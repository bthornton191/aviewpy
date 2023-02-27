from typing import Iterable, List

import Adams  # type: ignore # noqa # isort: skip
from Object import Object # type: ignore # noqa # isort: skip
from Group import Group # type: ignore # noqa # isort: skip

def translate(objects: List[Object], vector: List[float], csentity: Object = None):
    """Move objects by a vector.

    Parameters
    ----------
    objects : List[Object]
        List of objects to move
    vector : List[float]
        Vector to move objects by
    csentity : Object, optional
        Coordinate system entity to move objects in, by default None
    """
    if not isinstance(objects, Iterable):
        objects = [objects]
        
    select_list: Group = Adams.Groups['SELECT_LIST']
    select_list.empty()
    
    for obj in objects:
        select_list.append(obj)

    vec_str = ' '.join([f'c{i+1}={v}' for i, v in enumerate(vector)])

    cmd = f'move translation {vec_str} group=SELECT_LIST'
    if csentity is not None:
        cmd += f' csentity_name={csentity.full_name}'

    Adams.execute_cmd(cmd)

    select_list.empty()
