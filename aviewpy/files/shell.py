from itertools import product
from pathlib import Path
from typing import List, Tuple
import pickle as pkl

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import stl
from mpl_toolkits import mplot3d
from scipy.spatial import KDTree


CACH_SUFFIX = '.bshl'


def write_shell_file(points: List[Tuple[float, float, float]],
                     facets: List[Tuple[int, int, int]],
                     file_name: Path,
                     scale: float):
    """Writes a shell (.shl) file

    Parameters
    ----------
    points : List[Tuple[float, float, float]]
        Shell points
    facets : List[Tuple[int, int, int]]
        Shell facets (index 0)
    file_name : Path
        Full path of shell file
    scale : float
        Shell scale
    """
    points, facets = drop_duplicates(points, facets)
    n_points = len(points)
    n_facets = len(facets)

    lines = [f'{n_points} {n_facets} {scale:.6f}']
    for point in points:
        lines.append(' '.join([f'{v:.8f}' for v in point]))

    for facet in facets:
        lines.append(' '.join([str(len(facet))] + [f'{p+1:d}' for p in facet]))

    Path(file_name).write_text('\n'.join(lines))


def drop_duplicates(points: List[Tuple[float, float, float]],
                    facets: List[Tuple[int, int, int]]):

    df_points = pd.DataFrame(points, columns=['x', 'y', 'z'])
    df_points['duplicated'] = df_points.duplicated()

    if df_points['duplicated'].any():
        df_facets = pd.DataFrame(facets)
        df_facets_new = df_facets.copy(deep=True)
        for idx, facet in df_facets.iterrows():
            for jdx, i_pt in enumerate(facet):
                if df_points['duplicated'].loc[i_pt]:

                    new_i_pt = df_points[(df_points['x'] == df_points['x'].loc[i_pt])
                                         & (df_points['y'] == df_points['y'].loc[i_pt])
                                         & (df_points['z'] == df_points['z'].loc[i_pt])].iloc[0].name

                    df_facets_new.at[idx, jdx] = new_i_pt

        df_points_new = df_points.copy(deep=True).drop_duplicates()
        df_points_new['new_index'] = np.arange(len(df_points_new))
        df_facets_new = df_facets_new.applymap(lambda ipt: df_points_new.loc[ipt]['new_index'].astype(int))

        new_points = df_points_new[['x', 'y', 'z']].to_numpy()
        new_facets = df_facets_new.to_numpy()

    else:
        new_points, new_facets = points, facets

    return new_points, new_facets

# @lru_cache(maxsize=1)


def read_shell_file(file_name: Path, use_cache=True):
    """Reads a shell (.shl) file

    Parameters
    ----------
    file_name : Path
        Full path of shell file
    use_cache : bool, optional
        Use cached version of file, by default True

    Returns
    -------
    List[Tuple[float, float, float]]
        Shell points
    List[Tuple[int, int, int]]
        Shell facets
    """
    file_name = Path(file_name)
    cache_file_name = file_name.with_suffix(CACH_SUFFIX)
    if (use_cache
        and cache_file_name.exists()
            and file_name.stat().st_mtime < cache_file_name.stat().st_mtime):
        with open(file_name.with_suffix(CACH_SUFFIX), 'rb') as fid:
            points, facets = pkl.load(fid)
    else:
        def _parse_lines(lines):
            n_points, n_facets, *_ = [float(v) for v in lines[0].split()]
            points = [tuple(float(v) for v in line.split())
                      for line in lines[1:int(n_points) + 1]]
            facets = [tuple(int(v) - 1 for v in line.split()[1:])
                      for line in lines[int(n_points) + 1:int(n_points + n_facets) + 1]
                      if len(line.split()[1:]) > 2]

            return points, facets
        lines = Path(file_name).read_text().splitlines()

        try:
            points, facets = _parse_lines(lines)
        except Exception:                                                                               # pylint: disable=broad-except
            lines = [l for l in lines if all(is_number(v) for v in l.split())]
            points, facets = _parse_lines(lines)

        # Remove duplicate points
        points, facets = drop_duplicates(points, facets)

        # Cache file
        with open(file_name.with_suffix(CACH_SUFFIX), 'wb') as fid:
            pkl.dump((points, facets), fid)

    return points, facets


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def get_shell_diff_vectors(file_1: Path, file_2: Path):
    """Get a vector of the differences between two (.shl) files

    Parameters
    ----------
    file_1 : Path
        Full path of shell file 1
    file_2 : Path
        Full path of shell file 2

    Returns
    -------
    bool
        True if the two files are the same
    """
    points_1, _ = read_shell_file(file_1)
    points_2, _ = read_shell_file(file_2)

    # Match each point in points_1 to the closest point in points_2 and create a dataframe of the distance components
    df = pd.DataFrame(points_1, columns=['x_1', 'y_1', 'z_1'])

    df['idx_pt_2'] = KDTree(points_2).query(points_1)[1]
    df[['x_2', 'y_2', 'z_2']] = df['idx_pt_2'].apply(lambda idx: points_2[idx]).tolist()

    df[['d_x', 'd_y', 'd_z']] = df[['x_1', 'y_1', 'z_1']].to_numpy() - df[['x_2', 'y_2', 'z_2']].to_numpy()

    return df


def get_shell_volume(points: List[Tuple[float, float, float]], facets: List[Tuple[int, int, int]]):
    """Get the volume of a shell

    Parameters
    ----------
    points : List[Tuple[float, float, float]]
        xyz coordinates of shell points
    facets : List[Tuple[int, int, int]]
        Shell facets

    Returns
    -------
    float
        Shell volume
    """
    mesh = to_stl_mesh(points, facets)
    volume, *_ = mesh.get_mass_properties()
    return abs(volume)


def to_stl_mesh(points, facets):
    """Converts a shell to an stl mesh

    Parameters
    ----------
    points : List[Tuple[float, float, float]]
        Shell points
    facets : List[Tuple[int, int, int]]
        Shell facets (index 0)

    Returns
    -------
    stl.mesh.Mesh
        Mesh
    """
    points = np.array(points)
    facets = np.array(facets)

    mesh = stl.mesh.Mesh(np.zeros(facets.shape[0], dtype=stl.mesh.Mesh.dtype))
    for (i, facet), j in product(enumerate(facets), range(3)):
        mesh.vectors[i][j] = points[facet[j], :]

    mesh.update_centroids()
    mesh.update_normals()
    mesh.update_areas()
    mesh.update_max()
    mesh.update_min()
    mesh.update_units()

    return mesh


def plot_shell(points, facets):

    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    mesh = to_stl_mesh(points=points, facets=facets)
    mesh.update_normals()
    mesh.update_centroids()

    ax.add_collection3d(mplot3d.art3d.Poly3DCollection(mesh.vectors, alpha=.75, edgecolor='k'))
    scale = mesh.points.flatten()
    ax.auto_scale_xyz(scale, scale, scale)

    for centroid, normal in zip(mesh.centroids, mesh.normals):
        ax.plot(*np.array([centroid, (centroid + normal * 2)]).T, c='r')

    return ax
