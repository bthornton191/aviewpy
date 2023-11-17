import re
from typing import List
from Object import Object  # type: ignore
from ..files.mac import RE_MACRO_PARAM, get_macro_params  # for backwards compatibility

DEACTIVAETABLE_TYPES = {
    'beam': [],
    'bushing': [],
    'clearance': [],
    'contact': [],
    'coupler': [],
    'diff': ['differential_equation'],
    'fe_load': [],
    'field': [],
    'gcon': ['general_constraint'],
    'gforce': ['general_force'],
    'joint': ['curve_curve',
              'point_curve',
              'point_surface_follower',
              'fixed_joint',
              'translational_joint',
              'revolute_joint'],
    'jprim': ['primitive_joint'],
    'motion': [],
    'sensor': [],
    'sforce': ['single_component_force'],
    'springdamper': [],
    'vforce': ['force_vector'],
    'vtorque': ['torque_vector'],
}
"""Type of parameters that can be deactivated using the `DEACTIVATE` solver command.

The keys are the argument that should be passed to the `DEACTIVATE` command.
The values are the types returned by an objects `className()` method."""


class Param():
    def __init__(self, name, type_=None, count=1, options=None, default=None):
        self.name: str = name
        self.type: str = type_
        self.count: int = int(count) if count is not None else 1
        self.options = options

        if default is not None and type_ == 'real':
            self.default = float(default)
        elif default is not None and type_ == 'integer':
            self.default = int(default)
        else:
            self.default = default


def is_deactivatable(obj: Object) -> bool:
    """Checks if an object is deactivatable

    Parameters
    ----------
    obj : Object
        Object to check

    Returns
    -------
    bool
        True if the object is deactivatable
    """
    try:
        get_deactivateable_type(obj)
    except ValueError:
        deactivatable = False
    else:
        deactivatable = True

    return deactivatable


def get_deactivateable_type(obj: Object):

    def remove_fmt(nm: str):
        return re.sub(r'[ _]+', '', nm.lower())

    if remove_fmt(obj.className()) in map(remove_fmt, DEACTIVAETABLE_TYPES):
        idx = [remove_fmt(dt) for dt in DEACTIVAETABLE_TYPES].index(remove_fmt(obj.className()))
        deac_type = list(DEACTIVAETABLE_TYPES)[idx]

    elif remove_fmt(obj.className()) in [remove_fmt(dt)
                                         for dts in DEACTIVAETABLE_TYPES.values()
                                         for dt in dts]:
        deac_type = next(dtype.upper() for dtype, otype in DEACTIVAETABLE_TYPES.items()
                         if remove_fmt(obj.className()) in map(remove_fmt, otype))

    else:
        raise ValueError(f'Object {obj.className()} is not deactivateable')

    return deac_type
