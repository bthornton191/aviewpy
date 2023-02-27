from collections import namedtuple
from itertools import product
from typing import List

import numpy as np
from numpy.typing import NDArray
import pandas as pd

import Adams  # type: ignore # noqa
from Analysis import Analysis  # type: ignore # noqa
from Contact import Contact  # type: ignore # noqa
from Geometry import Geometry  # type: ignore # noqa
from Marker import Marker  # type: ignore # noqa
from Model import Model  # type: ignore # noqa
from Part import Part  # type: ignore # noqa

from .cs import CS, MarkerCS
from .objects import get_parent_model
from .ui.progressbar import progress_bar

TESTING = False


TrackData = namedtuple('TrackData', ['normal',
                                     'normal_unit',
                                     'friction',
                                     'slip',
                                     'time',
                                     'loc',
                                     'penetration'])


class Track():
    """Class for managing contact track data"""

    COLS = ['time', 'normal', 'normal_unit', 'friction', 'slip', 'loc', 'penetration']
    COLS_WITH_COMPS = ['normal', 'normal_unit', 'friction', 'slip', 'loc']

    def __init__(self, ans: Analysis, cont: Contact, name: str) -> None:
        """Class for managing contact track data

        Parameters
        ----------
        ans : Analysis
            Adams analysis
        cont : Contact
            Parent Adams `Contact` object
        name : str
            Full name of contact track
        """
        self.ans = ans
        self.cont = cont
        self.name = name

    def get_data(self, mkr: Marker, i_part=True) -> TrackData:
        """Returns track data in a local CS

        Parameters
        ----------
        ans : Analysis
            Adams analysis
        ref_part : Part, optional
            Part to transform coordinates into, (overridden by `ref_mkr`), by default None
        ref_mkr : Marker, optional
            Marker to transform coordinates into, by default None

        Returns
        -------
        _type_
            _description_
        """
        part: Part = mkr.parent
        time = np.array(self.ans.results['TIME'].values)
        I_or_J = 'I' if i_part else 'J'

        track_gcs = CS(np.array([Adams.evaluate_exp(f'{self.name}.{I_or_J}_Point.{d}.values')
                                 for d in ('X', 'Y', 'Z')]).T)
        mkr_gcs = MarkerCS(mkr, self.ans)
        normal_gcs = CS(np.array([Adams.evaluate_exp(f'{self.name}.{I_or_J}_Normal_Force.{d}.values')
                        for d in ('X', 'Y', 'Z')]).T)
        normal_unit_gcs = CS(np.array([Adams.evaluate_exp(f'{self.name}.{I_or_J}_Normal_Unit_Vector.{d}.values')
                                       for d in ('X', 'Y', 'Z')]).T)
        friction_gcs = CS(np.array([Adams.evaluate_exp(f'{self.name}.{I_or_J}_Friction_Force.{d}.values')
                                    for d in ('X', 'Y', 'Z')]).T)
        slip_gcs = CS(np.array([Adams.evaluate_exp(f'{self.name}.Slip_Velocity.{d}.values')
                                for d in ('X', 'Y', 'Z')]).T)
        penetration = Adams.evaluate_exp(f'{self.name}.Penetration.Depth.values')
        normal_lcs: NDArray = mkr_gcs.rot.apply(normal_gcs.loc, inverse=True)
        normal_unit_lcs: NDArray = mkr_gcs.rot.apply(normal_unit_gcs.loc, inverse=True)
        friction_lcs: NDArray = mkr_gcs.rot.apply(friction_gcs.loc, inverse=True)
        slip_lcs: NDArray = mkr_gcs.rot.apply(slip_gcs.loc, inverse=True)
        track_pos_lcs: NDArray = mkr_gcs.rot.apply((track_gcs-mkr_gcs).loc, inverse=True)

        if False:
            mod = get_parent_model(part)
            for (idx, loc_gcs), loc_lcs in zip(enumerate(track_gcs.loc), track_pos_lcs):
                mkr_g = mod.ground_part.Markers.create(
                    location=list(loc_gcs),
                    relative_to=mod.ground_part,
                )
                mkr_g.color_name = 'violet'
                mkr_g.size_of_icons = 0.01

                mkr_l = part.Markers.create(
                    location=list(loc_lcs),
                    relative_to=mkr,
                )
                mkr_l.color_name = 'cyan'
                mkr_l.size_of_icons = 0.02
                # assert all(np.round(mkr_g.location_global, 5) == np.round(mkr_l.location_global, 5))

        return TrackData(normal_lcs,
                         normal_unit_lcs,
                         friction_lcs,
                         slip_lcs,
                         time,
                         track_pos_lcs,
                         np.array(penetration))


def all_tracks_on_geometry(geom: Geometry, ans: Analysis) -> List[Track]:
    """Returns a list of all the `Tracks` on a given `Geometry`.

    Parameters
    ----------
    geom : Geometry
        An Adams Geometry object to return tracks for
    ans : Analysis
        An Adams Analysis object 

    Returns
    -------
    List[Track]
        List of Tracks that involve `geom`
    """
    mod: Model = ans.parent
    tracks: List[Track] = []
    for cont in (c for c in mod.Contacts.values()
                 if geom in c.i_geometry + c.j_geometry
                 and c.name in ans.results):
        Adams.execute_cmd(
            f'analysis collate_contacts analysis={ans.full_name} contact={cont.full_name}'
        )
        names = Adams.evaluate_exp(
            f'db_filter_name(db_immediate_children({ans.full_name}.{cont.name}, "result_set"), "track_*")'
        )

        if isinstance(names, str):
            names = [names]

        tracks.extend([Track(ans, cont, name) for name in names])

    return tracks


def get_track_data(ans: Analysis, track_name: str, mkr: Marker, I_part=True) -> TrackData:
    """Returns track data in a local CS

    Parameters
    ----------
    ans : Analysis
        Adams analysis to
    track_name : str
        Full name of contact track
    ref_part : Part, optional
        Part to transform coordinates into, (overridden by `ref_mkr`), by default None
    ref_mkr : Marker, optional
        Marker to transform coordinates into, by default None

    Returns
    -------
    _type_
        _description_
    """
    part: Part = mkr.parent
    time = np.array(ans.results['TIME'].values)
    I_or_J = 'I' if I_part else 'J'

    track_gcs = CS(np.array([Adams.evaluate_exp(f'{track_name}.{I_or_J}_Point.{d}.values')
                             for d in ('X', 'Y', 'Z')]).T)
    mkr_gcs = MarkerCS(mkr, ans)
    normal_gcs = CS(np.array([Adams.evaluate_exp(f'{track_name}.{I_or_J}_Normal_Force.{d}.values')
                              for d in ('X', 'Y', 'Z')]).T)
    normal_unit_gcs = CS(np.array([Adams.evaluate_exp(f'{track_name}.{I_or_J}_Normal_Unit_Vector.{d}.values')
                                   for d in ('X', 'Y', 'Z')]).T)
    friction_gcs = CS(np.array([Adams.evaluate_exp(f'{track_name}.{I_or_J}_Friction_Force.{d}.values')
                                for d in ('X', 'Y', 'Z')]).T)
    slip_gcs = CS(np.array([Adams.evaluate_exp(f'{track_name}.Slip_Velocity.{d}.values')
                            for d in ('X', 'Y', 'Z')]).T)
    penetration = Adams.evaluate_exp(f'{track_name}.Penetration.Depth.values')
    normal_lcs: NDArray = mkr_gcs.rot.apply(normal_gcs.loc, inverse=True)
    normal_unit_lcs: NDArray = mkr_gcs.rot.apply(normal_unit_gcs.loc, inverse=True)
    friction_lcs: NDArray = mkr_gcs.rot.apply(friction_gcs.loc, inverse=True)
    slip_lcs: NDArray = mkr_gcs.rot.apply(slip_gcs.loc, inverse=True)
    track_pos_lcs: NDArray = mkr_gcs.rot.apply((track_gcs-mkr_gcs).loc, inverse=True)

    if TESTING:
        mod = get_parent_model(part)
        for (idx, loc_gcs), loc_lcs in zip(enumerate(track_gcs.loc), track_pos_lcs):
            mkr_g = mod.ground_part.Markers.create(
                location=list(loc_gcs),
                relative_to=mod.ground_part,
            )
            mkr_g.color_name = 'violet'
            mkr_g.size_of_icons = 0.01

            mkr_l = part.Markers.create(
                location=list(loc_lcs),
                relative_to=mkr,
            )
            mkr_l.color_name = 'cyan'
            mkr_l.size_of_icons = 0.02
            # assert all(np.round(mkr_g.location_global, 5) == np.round(mkr_l.location_global, 5))

    return TrackData(normal_lcs,
                     normal_unit_lcs,
                     friction_lcs,
                     slip_lcs,
                     time,
                     track_pos_lcs,
                     np.array(penetration))


def get_contact_data(geom: Geometry, ans: Analysis, ref_mkr: Marker) -> pd.DataFrame:
    """Gets a DataFrame of contact data needed for calculating wear.

    Parameters
    ----------
    geom : Geometry
        The Adams geometry for which contact data will be returned
    ans : Analysis
        The Adams analysis for which contact data will be returned
    ref_mkr : Marker
        The marker to transform coordinates into

    Returns
    -------
    pd.DataFrame
        A DataFrame of contact data needed for calculating wear
    """
    tracks = all_tracks_on_geometry(geom, ans)

    dfs = [pd.DataFrame({
        **{k: [] for k in Track.COLS},
        **{f'{k}_{d}': [] for d, k in product(['x', 'y', 'z'], Track.COLS_WITH_COMPS)},
        'step': [],
        'contact': [],
        'track': []
    }).set_index('time', drop=True)]

    inc = 100 / len(tracks) if len(tracks) > 0 else 0
    with progress_bar(f'Processing {geom.parent.name}.{geom.name} contacts...') as pbar:
        for track in tracks:

            track_data = track.get_data(mkr=ref_mkr,
                                        i_part=geom in track.cont.i_geometry)

            # Organize the data into a dictionary
            data = {}
            for key, values in track_data._asdict().items():

                # Check if `values` has multiple components
                if isinstance(values, np.ndarray) and len(values.shape) > 1:

                    # If `values` has multiple components,
                    # split the components (x,y,z) and get magnitudes
                    data = {
                        **data,
                        **{f'{key}_{d}': values[:, i] for i, d in enumerate(['x', 'y', 'z'])},
                        key: np.sqrt(np.apply_along_axis(np.sum, 1, values**2))
                    }

                else:
                    data[key] = values

            # Create DataFrame and append to list
            dfs.append(pd.DataFrame({**data,
                                    'step': pd.Series(track_data.time).diff(-1).fillna(0)*-1,
                                    'contact': track.cont.name,
                                    'track': track.name})
                    .set_index('time', drop=True)
                    .sort_index())

            pbar.progress += inc

    return pd.concat(dfs)
