from pathlib import Path
from typing import List, Tuple
import pandas as pd
from numpy import arange
from scipy.spatial import KDTree

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
        Shell facets
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
        lines.append(' '.join([str(len(facet))] + [str(p) for p in facet]))

    Path(file_name).write_text('\n'.join(lines))


def drop_duplicates(points: List[Tuple[float, float, float]],
                    facets: List[Tuple[int, int, int]]):
    
    df_facets = pd.DataFrame(facets)

    df_points = pd.DataFrame(points, columns=['x', 'y', 'z'])

    df_facets_new = df_facets.copy(deep=True)
    for idx, facet in df_facets.iterrows():
        for jdx, i_pt in enumerate(facet):
            if df_points.duplicated().loc[i_pt]:

                new_i_pt = df_points[(df_points['x'] == df_points['x'].loc[i_pt])
                                        & (df_points['y'] == df_points['y'].loc[i_pt])
                                        & (df_points['z'] == df_points['z'].loc[i_pt])].iloc[0].name
                
                df_facets_new.at[idx, jdx] = new_i_pt
                # print(f'replaced {i_pt} with {new_i_pt}')

    df_points_new = df_points.copy(deep=True).drop_duplicates()
    df_points_new['new_index'] = arange(1, len(df_points_new)+1)
    df_facets_new = df_facets_new.applymap(lambda ipt: df_points_new.loc[ipt]['new_index'].astype(int))

    return ([tuple(r) for _, r in df_points_new[['x', 'y', 'z']].iterrows()],
            [tuple(r) for _, r in df_facets_new.iterrows()])

def read_shell_file(file_name: Path):
    """Reads a shell (.shl) file

    Parameters
    ----------
    file_name : Path
        Full path of shell file

    Returns
    -------
    List[Tuple[float, float, float]]
        Shell points
    List[Tuple[int, int, int]]
        Shell facets
    """
    lines = Path(file_name).read_text().splitlines()
    n_points, n_facets, scale = [float(v) for v in lines[0].split()]
    points = [tuple([float(v) for v in line.split()]) for line in lines[1:int(n_points)+1]]
    facets = [tuple([int(v) for v in line.split()[1:]]) for line in lines[int(n_points)+1:]]
    
    return points, facets

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
