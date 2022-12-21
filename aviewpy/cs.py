from __future__ import annotations
from typing import Tuple

from scipy.spatial.transform import Rotation as R
import numpy as np

import Adams  # type: ignore # noqa # isort: skip
from Analysis import Analysis # type: ignore # noqa
from Marker import Marker # type: ignore # noqa
from Part import Part # type: ignore # noqa

from numpy.typing import ArrayLike, NDArray

class CS():
    def __init__(self, loc, ori=None, design_loc=None, design_ori=None):
        self.loc = loc
        self.ori = ori
        self.design_loc = design_loc if design_loc is not None else self.loc[0]
        self.design_ori = design_ori if design_ori is not None else (self.ori[0] if ori is not None else None)

    def __add__(self, other: CS) -> CS:
        rot = self.rot * other.rot
        design_rot = self.design_rot * other.design_rot
        return CS(
            loc=self.loc + other.loc,
            ori=rot.as_euler('ZXZ', degrees=True),
            design_loc=self.design_loc + other.design_loc,
            design_ori=design_rot.as_euler('ZXZ', degrees=True),
        )

    def __sub__(self, other: CS) -> CS:

        if other.rot is not None and self.rot is not None:
            rot: R = other.rot.inv() * self.rot
            ori=rot.as_euler('ZXZ', degrees=True)
            design_rot: R = (self.design_rot * other.design_rot.inv())
            design_ori=design_rot.as_euler('ZXZ', degrees=True)
        
        else:
            ori = None
            design_ori = None
        
        return CS(
            loc=self.loc - other.loc,       
            ori=ori,
            design_loc=self.design_loc - other.design_loc,
            design_ori=design_ori,
        )

    @property
    def rot(self) -> R:
        return R.from_euler('ZXZ', self.ori, degrees=True) if self.ori is not None else None

    @property
    def design_rot(self) -> R:
        return R.from_euler('ZXZ', self.design_ori, degrees=True) if self.design_ori is not None else None


class PartCS(CS):

    def __init__(self, part: Part, ans: Analysis=None):
        design_loc = np.array(Adams.evaluate_exp(f'loc_global({{0,0,0}}, {part.full_name})'))
        design_ori = np.array(Adams.evaluate_exp(f'ori_global({{0,0,0}}, {part.full_name})'))
        
        if ans is not None:
            loc = np.array([Adams.evaluate_exp(f'{ans.full_name}.{part.name}_XFORM.{direc}.values')
                            for direc in ('X', 'Y', 'Z')]).T
            ori = np.array([Adams.evaluate_exp(f'{ans.full_name}.{part.name}_XFORM.{direc}.values')
                            for direc in ('PSI', 'THETA', 'PHI')]).T
        else:
            loc = design_loc
            ori = design_ori

        super().__init__(loc, ori, design_loc, design_ori)


class MarkerCS(CS):

    def __init__(self, mkr: Marker, ans: Analysis=None):
        design_loc = np.array(Adams.evaluate_exp(f'loc_global({{0,0,0}}, {mkr.full_name})'))
        design_ori = np.array(Adams.evaluate_exp(f'ori_global({{0,0,0}}, {mkr.full_name})'))

        part_gcs = PartCS(mkr.parent, ans)

        rel_loc = design_loc-part_gcs.design_loc
        loc = part_gcs.loc+rel_loc
        rot: R = part_gcs.rot * R.from_euler('ZXZ', mkr.orientation, degrees=True)
        ori = rot.as_euler('ZXZ', degrees=True)

        super().__init__(loc, ori, design_loc, design_ori)


def cart_to_cyl(x: ArrayLike, y: ArrayLike, z: ArrayLike) -> Tuple[NDArray, NDArray, NDArray]:
    return (
        np.sqrt(x**2 + y**2),
        np.arctan2(y, x),
        z
    )


def cyl_to_cart(r: ArrayLike, phi: ArrayLike, z: ArrayLike) -> Tuple[NDArray, NDArray, NDArray]:
    return (
        r*np.cos(phi),
        r*np.sin(phi),
        z
    )