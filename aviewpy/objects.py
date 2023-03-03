from typing import Generator, Iterable, List, Union

import Adams  # type: ignore # noqa
from DataElement import DataElement  # type: ignore # noqa
from DBAccess import find_by_full_name  # type: ignore # noqa
from Manager import AdamsManager  # type: ignore # noqa
from Model import Model  # type: ignore # noqa
from Object import DuplicateAttributeError  # type: ignore # noqa
from Object import ObjectBase as Object  # type: ignore # noqa


def get_object(full_name: str, mod: Model):
    """Returns the object with the given full name in the given model.

    Parameters
    ----------
    full_name : str
        Full name of the object to return
    mod : Model
        Model to search for the object

    Returns
    -------
    Object, None
        Object with the given full name in the given model, or None if no object with the given
        full name is found.
    """
    for obj in all_descendants(mod):
        if obj.full_name.lower() == full_name.lower():
            return obj
    return None


def delete_objects(objects: Union[str, Object, List[str], List[Object]]):
    """Deletes object(s) from Adams View database. Can pass iterable or scalar, objects or names.

    Parameters
    ----------
    objects : Union[str, Object, List[str], List[Object]]
        Object(s) to delete. Can be a single value or an iterable. Can be of type `Object` or str.
    """
    if not isinstance(objects, Iterable) or isinstance(objects, str):
        objects = [objects]

    names = [obj.full_name if isinstance(obj, Object) else str(obj) for obj in objects]
    cmds = ['group empty group=SELECT_LIST',
            *[f'group object add group=select_list objects = {name}' for name in names],
            'mdi delete_macro']

    for cmd in cmds:
        Adams.execute_cmd(cmd)


def all_descendants(obj: Object) -> Generator[Object, None, None]:
    for mgr in get_managers(obj):
        for descendant in mgr.values():
            yield descendant
            yield from all_descendants(descendant)

            if hasattr(descendant, 'objects'):
                yield from (obj for obj in descendant.objects if obj is not None)


def get_managers(parent: Object):
    return [mgr for mgr in parent.__dict__.values() if isinstance(mgr, AdamsManager)]


def get_parent_model(entity: Object)->Model:
    """Returns the parent model of `entity`.

    Parameters
    ----------
    entity : Object
        Adams Object

    Returns
    -------
    Model
        Parent `Model` of `entity`
    """
    if isinstance(entity.parent, Model):
        return entity.parent
    else:
        return get_parent_model(entity.parent)


def set_unique_adams_id(entity):
    if isinstance(entity, DataElement):

        # Get the model object
        mod = Adams.Models[Adams.evaluate_exp(f'db_ancestor({entity.full_name}, "model")')]
        adams_id = entity.adams_id

        # Get an available adams id
        ents = [ent for ent in mod.DataElements.values() if entity != ent]
        while adams_id == 0 or adams_id in [ent.adams_id for ent in ents]:
            adams_id += 1

    else:
        raise NotImplementedError(f'This function is not implemented for type {type(entity)}')

    try:
        entity.adams_id = adams_id
    except DuplicateAttributeError as err:
        ents = [e for e in mod.DataElements.values() if e.adams_id == adams_id if e != entity]
        if ents != []:
            custom_err = DuplicateAttributeError(f'An adams id of {adams_id} was found while '
                                                 f'looking for a unique id for {entity.name} '
                                                 'However, this id is already taken by '
                                                 '{}!'.format(','.join([e.name for e in ents])))
            raise custom_err from err

    return adams_id



def unique_object_name(full_name: str) -> str:
    """Returns a unique name for an object in a model

    Parameters
    ----------
    full_name : str
        Full name of object
    model : Model
        Adams model

    Returns
    -------
    str
        Unique name
    """
    if not find_by_full_name(full_name):
        return full_name

    unique_name = full_name
    
    if full_name.split('_')[-1].isdigit():
        idx = int(full_name.split('_')[-1])+1
        full_name = '_'.join(full_name.split('_')[:-1])
        unique_name = full_name + f'_{idx}'
    else:
        idx = 1
        unique_name = full_name + f'_{idx}'

    while find_by_full_name(unique_name):
        idx += 1
        unique_name = f'{full_name}_{idx}'
        
    return unique_name


def all_objects(obj_type: str = 'all') -> Generator[Object, None, None]:
    if obj_type.lower() == 'model':
        yield from (mod for mod in Adams.Models.values())

    else:
        for mod in Adams.Models.values():
            objects = Adams.evaluate_exp(f'DB_DESCENDANTS({mod.full_name} , "{obj_type}" , 0 , 2 )')
            if isinstance(objects, str):
                objects = [objects]

            yield from (get_object(name, mod) for name in objects)
