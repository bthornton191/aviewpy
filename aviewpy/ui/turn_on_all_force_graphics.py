
import logging
from typing import Union

import Adams  # type: ignore
from Constraint import Constraint  # type: ignore
from Contact import Contact  # type: ignore
from Force import Force, ForceVector, GeneralForce, SingleComponentForce  # type: ignore
from Model import Model  # type: ignore
from Geometry import GeometryForce, GeometryGContact  # type: ignore
from ..objects import get_parent_model

LOG = logging.getLogger(__name__)


def turn_on_all_force_graphics(mod: Model = None):
    mod = mod or Adams.getCurrentModel()
    for obj in [*mod.Constraints.values(), *mod.Forces.values(), *mod.Contacts.values()]:
        turn_on_force_graphic(obj)


def turn_on_force_graphic(obj: Union[Force, Constraint, Contact], show_on_ipart=True):
    if isinstance(obj, (SingleComponentForce, ForceVector, GeneralForce, Constraint)):
        Adams.execute_cmd(f'mdi graphic_force object = {obj.full_name} type = '
                          + ('1' if show_on_ipart else '2'))

    elif isinstance(obj, Contact):
        if Adams.evaluate_exp(f'db_exists("{obj.full_name}_graphic")'):
            Adams.execute_cmd(f'geometry delete geometry_name = {obj.full_name}_graphic')

        Adams.execute_cmd(f'geometry create shape gcontact '
                          f'    contact_force_name = {obj.full_name}_graphic '
                          f'    contact_element_name = {obj.full_name} '
                          f'    force_display = components')

    else:
        LOG.warning(f'`turn_on_force_graphic` does not support {obj.className()} objects.')

    return get_graphic(obj)


def get_graphic(obj: Union[Force, Constraint, Contact]):
    mod = get_parent_model(obj)
    return next((g for g in mod.Geometries.values()
                 if (isinstance(g, GeometryForce) and g.force_element == obj)
                 or (isinstance(g, GeometryGContact) and g.contact_element == obj)),
                None)
