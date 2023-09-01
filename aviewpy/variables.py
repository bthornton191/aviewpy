
from functools import singledispatch
from numbers import Number
from typing import Iterable, List, Union

import Adams  # type: ignore
from Object import ObjectBase  # type: ignore
from Object import Object  # type: ignore
from Analysis import Analysis  # type: ignore
from DesignVariable import DesignVariable  # type: ignore

def set_dv(parent, name: str, value, append=False, **kwargs)->Union[DesignVariable, None]:
    """Sets the value of a design variable. If the design variable does not exist, it is created.
    
    Note
    ----
    Return value is `None` if `parent' is a string.

    Parameters
    ----------
    parent : ObjectBase or str
        Parent object of the design variable
    name : str
        Name of the design variable
    value : Number, str, or ObjectBase (or list of any of these)
        Value(s) to set the design variable to
    append : bool, optional
        If True, appends the given value to the existing value of the design variable, by default False
    **kwargs
        Additional keyword arguments to pass to the DesignVariable.create* methods.
    """
    # Make sure the value is a list
    value = [value] if not isinstance(value, Iterable) or isinstance(value, str) else value

    if isinstance(parent, str):
        _set_dv_str(parent, name, value, append)
        dv = None

    elif isinstance(parent, Object):
        dv = _set_dv_obj(parent, name, value, append, **kwargs)
    
    elif isinstance(parent, ObjectBase):
        # Must treat `ObjectBase`s that aren't `Object`s (e.g. `Analysis`) different because the 
        # python API doesn't support setting desisgn variables for analyses, but the cmd API does...
        _set_dv_str(parent.full_name, name, value, append)
        dv = None
        
    else:
        raise TypeError(f'Invalid type for value: {type(value)}')

    return dv


def _set_dv_obj(parent: Object, name: str, value: List[Union[Number, str, ObjectBase]], append=False, **kwargs):
    """Function to handle setting a design variable when the parent is an ObjectBase"""
    if name in parent.DesignVariables:
        # If the design variable already exists
        dv = parent.DesignVariables[name]

        if append:
            value = dv.value + value

        dv.update(value=value, **kwargs)

    else:
        dv = _create_dv(value, parent, name, **kwargs)

    return dv


def _set_dv_str(parent: str, name: str, value: List[Union[Number, str, ObjectBase]], append=False)->None:
    """Function to handle setting a design variable when the parent is a string"""
    if Adams.evaluate_exp(f'db_exists("{parent}.{name}")') and append:
        value_ = Adams.evaluate_exp(f'{parent}.{name}')
        value_ = [value_] if not isinstance(value_, (tuple, list)) else list(value_)
        value = value_ + value

    _cmd_set_dv(value, parent, name)


def _create_dv(value: list, parent: Object, name: str, **kwargs):
    """Creates a design variable with the given value.
    
    Parameters
    ----------
    value : List of Number, str, or ObjectBase
        Value(s) to set the design variable to
    parent : Object
        Parent object of the design variable
    name : str
        Name of the design variable
    **kwargs
        Additional keyword arguments to pass to the DesignVariable.create* methods.
    """
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        dv = parent.DesignVariables.createString(name=name, value=value, **kwargs)

    elif isinstance(value, list) and all(isinstance(v, Number) for v in value):
        dv = parent.DesignVariables.createReal(name=name, value=value, **kwargs)

    elif isinstance(value, list) and all(isinstance(v, int) for v in value):
        dv = parent.DesignVariables.createInteger(name=name, value=value, **kwargs)

    elif isinstance(value, list) and all(isinstance(v, ObjectBase) for v in value):
        dv = parent.DesignVariables.createObject(name=name, value=value, **kwargs)
    else:
        raise TypeError(f'Invalid type for value: {type(value)}')

    return dv


def _cmd_set_dv(value: list, parent: str, name: str):
    """Sets the value of a design variable. If the design variable does not exist, it is created.
    
    Parameters
    ----------
    value : Number, str, or ObjectBase (or list of any of these)
        Value(s) to set the design variable to
    parent : str
        Parent object of the design variable
    name : str
        Name of the design variable
    """
    
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        val_text = ', '.join([f'\'{v}\'' for v in value])
        Adams.execute_cmd(f'var set var={parent}.{name} str={val_text}')

    elif isinstance(value, list) and all(isinstance(v, Number) for v in value):
        val_text = ', '.join([f'{v}' for v in value])
        Adams.execute_cmd(f'var set var={parent}.{name} real={val_text}')

    elif isinstance(value, list) and all(isinstance(v, int) for v in value):
        val_text = ', '.join([f'{v}' for v in value])
        Adams.execute_cmd(f'var set var={parent}.{name} int={val_text}')

    elif isinstance(value, list) and all(isinstance(v, ObjectBase) for v in value):
        val_text = ', '.join([f'{v}' for v in value])
        Adams.execute_cmd(f'var set var={parent}.{name} obj={val_text}')

    else:
        raise TypeError(f'Invalid type for value: {type(value)}')


def get_dv(parent: Union[ObjectBase, str], name: str)->List[Union[Number, str, Object]]:
    """Returns the value of the design variable `name` from the object `parent`.

    Parameters
    ----------
    parent : ObjectBase or str
        Parent object of the design variable
    name : str
        Name of the design variable

    Returns
    -------
    List[Number, str, or Object]
        Value(s) of the design variable
    """
    if isinstance(parent, ObjectBase):
        parent=parent.full_name
    elif not isinstance(parent, str):
        raise TypeError(f'Invalid type for parent: {type(parent)}')

    value = Adams.evaluate_exp(f'{parent}.{name}')

    # Make sure the value is a list
    value = [value] if not isinstance(value, Iterable) or isinstance(value, str) else value
    
    return value
