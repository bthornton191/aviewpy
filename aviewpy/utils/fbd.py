"""This module contains a function `show_fbd` which creates an animation in the Adams post processor 
with only one part visible, and all force vectors on that part displayed.
"""
from typing import List
from Analysis import Analysis  # type: ignore
from Part import Part  # type: ignore
from Contact import Contact  # type: ignore
from Object import ObjectSubBase, Object  # type: ignore
import Adams  # type: ignore
from aviewpy.ui.turn_on_all_force_graphics import get_graphic, turn_on_force_graphic
from aviewpy.objects import get_parent_model

IPART_ATTRS = ['i_part']

PART_ATTRS = [*IPART_ATTRS,
              'j_part']

ICHILD_ATTRS = ['i_marker',
                'i_geometry']
CHILD_ATTRS = [*ICHILD_ATTRS,
               'j_marker',
               'ref_marker',
               'j_floating_marker',
               'j_geometry']


def show_fbd(ans: Analysis, part: Part):
    """Creates an animation in the Adams post processor with only one part visible, and all force 
    vectors on that part displayed.

    Parameters
    ----------
    ans : Analysis
        The analysis object
    part : Part
        The part for which the fbd animation is to be created
    """
    mod = get_parent_model(part)

    # Hide all other parts
    for p in [p for p in mod.Parts.values() if p != part]:
        p.visibility = 'off'

    # Get all the constraints, forces, and contacts that attach to the part
    constraints = [c for c in mod.Constraints.values() if is_attached(part, c)]
    forces = [f for f in mod.Forces.values() if is_attached(part, f)]
    contacts = [c for c in mod.Contacts.values() if is_attached(part, c)]

    # Show only these constraints, forces, and contacts
    for obj in [*mod.Constraints.values(), *mod.Forces.values(), *mod.Contacts.values()]:
        obj: Object

        if obj in constraints+forces+contacts:
            # --------------
            # If attached...
            # --------------

            # Show the object
            obj.visibility = 'on'

            # Show the graphics for the forces
            if isinstance(obj, Contact):
                graphic = get_graphic(obj) or turn_on_force_graphic(obj)
            else:
                graphic = turn_on_force_graphic(obj, show_on_ipart=is_ipart(part, obj))

        else:
            # ------------------
            # If not attached...
            # ------------------

            # Hide the object
            obj.visibility = 'off'

            # Hide the graphics for the forces
            graphic = get_graphic(obj)
            if graphic:
                graphic.visibility = 'off'
    page_name: str = Adams.evaluate_exp(f'unique_name_in_hierarchy(".gui.ppt_main.sash1.sash2.gfx.{part.name}_FBD")')

    # Create a new page in the post processor
    Adams.execute_cmd(f'interface page create'
                      f' page_name = "{page_name.split(".")[-1]}"'
                      f' layout = page2x2'
                      f' set_contents = yes')

    # ----------------------------------------------------------------------------------------------
    # Plotting
    # ----------------------------------------------------------------------------------------------

    for idx, direc in enumerate(['X', 'Y', 'Z'], start=2):

        Adams.execute_cmd(f'view activate view=(eval({page_name}.views[{idx}]))')
        Adams.execute_cmd('interface plot window set_mode mode=plotting')
        for obf in constraints + forces + contacts:
            Adams.execute_cmd('xy_plot curve create'
                              f' curve=(eval(unique_name_in_hierarchy({page_name}.views[{idx}].contents // ".{obf.name}")))'
                              f' ddata={obf.full_name.replace(mod.full_name, ans.full_name)}.F{direc}'
                              f' run={ans.full_name}'
                              f' auto_axis=UNITS')
        Adams.execute_cmd(f'xy_plots template auto_zoom'
                          f' plot_name=(eval({page_name}.views[{idx}].contents))')
        Adams.execute_cmd(f'xy_plot template calculate_axis_limits'
                          f' plot_name=(eval({page_name}.views[{idx}].contents))')
        Adams.execute_cmd(f'xy template modify'
                          f' plot=(eval({page_name}.views[{idx}].contents))'
                          f' title="{direc} Forces"')

    # ----------------------------------------------------------------------------------------------
    # Animation
    # ----------------------------------------------------------------------------------------------
    ani_name = Adams.evaluate_exp(f'unique_name("ani_{part.name}_FBD")')
    Adams.execute_cmd(f'view activate view_name = (eval({page_name}.views[1]))')
    Adams.execute_cmd('interface plot window set_mode mode = animation')
    Adams.execute_cmd(f'animation create '
                      f' analysis_name = {ans.full_name} '
                      f' view = (eval({page_name}.views[1]))'
                      f' animation_name = {ani_name}')
    Adams.execute_cmd(f'view center'
                      f' view = (eval({page_name}.views[1]))'
                      f' object = (eval(loc_global({{0,0,0}}, {part.cm.full_name})))')
    Adams.execute_cmd(f'animation modify'
                      f' base = {part.full_name}'
                      f' animation_name = {ani_name}')
    Adams.execute_cmd(f'animation modify animation_name = {ani_name} lock_rotation = on')
    Adams.execute_cmd(f'interface plot window page_display page={page_name}')


def is_attached(part: Part, obj: ObjectSubBase):

    for dep_obj in (getattr(obj, a) for a in PART_ATTRS if getattr(obj, a, None) is not None):
        if dep_obj == part:
            return True

    for dep_obj in (getattr(obj, a) for a in CHILD_ATTRS
                    if getattr(obj, a, None) is not None
                    and getattr(obj, a) is not None
                    and not isinstance(getattr(obj, a), (list, tuple))):
        dep_obj: ObjectSubBase
        if dep_obj.parent == part:
            return True

    for dep_objs in (getattr(obj, a) for a in CHILD_ATTRS
                     if getattr(obj, a, None) is not None
                     and isinstance(getattr(obj, a), (list, tuple))):
        dep_objs: List[ObjectSubBase]
        if any(o.parent == part for o in dep_objs):
            return True

    return False


def is_ipart(part: Part, obj: ObjectSubBase):
    for dep_obj in (getattr(obj, a) for a in IPART_ATTRS if getattr(obj, a, None) is not None):
        if dep_obj == part:
            return True

    for dep_obj in (getattr(obj, a) for a in ICHILD_ATTRS
                    if getattr(obj, a, None) is not None
                    and getattr(obj, a) is not None
                    and not isinstance(getattr(obj, a), (list, tuple))):
        dep_obj: ObjectSubBase
        if dep_obj.parent == part:
            return True

    for dep_objs in (getattr(obj, a) for a in ICHILD_ATTRS
                     if getattr(obj, a, None) is not None
                     and isinstance(getattr(obj, a), (list, tuple))):
        dep_objs: List[ObjectSubBase]
        if any(o.parent == part for o in dep_objs):
            return True

    return False
