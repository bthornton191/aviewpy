
from numbers import Number
from typing import Iterable, List, Union

import Adams  # type: ignore # noqa # isort: skip
from Object import Object  # type: ignore # noqa # isort: skip


def set_dv(parent, name: str, value, append=False, **kwargs):
    """Sets the value of a design variable. If the design variable does not exist, it is created.
    
    Parameters
    ----------
    parent : Object or str
        Parent object of the design variable
    name : str
        Name of the design variable
    value : Number, str, or Object (or list of any of these)
        Value(s) to set the design variable to
    append : bool, optional
        If True, appends the given value to the existing value of the design variable, by default False
    **kwargs
        Additional keyword arguments to pass to the DesignVariable.create* methods.
    """
    # Make sure the value is a list
    value = [value] if not isinstance(value, Iterable) or isinstance(value, str) else value

    if isinstance(parent, Object):
        dv = _set_dv_obj(parent, name, value, append, **kwargs)
    elif isinstance(parent, str):
        dv = _set_dv_str(parent, name, value, append)                                               # pylint: disable=assignment-from-no-return
    else:
        raise TypeError(f'Invalid type for value: {type(parent)}')

    return dv


def _set_dv_obj(parent: Object, name: str, value: List[Union[Number, str, Object]], append=False, **kwargs):
    """Function to handle setting a design variable when the parent is an Object"""
    if name in parent.DesignVariables:
        # If the design variable already exists
        dv = parent.DesignVariables[name]

        if append:
            value = dv.value + value

        dv.update(value=value, **kwargs)

    else:
        dv = _create_dv(value, parent, name, **kwargs)

    return dv


def _set_dv_str(parent: str, name: str, value: List[Union[Number, str, Object]], append=False):
    """Function to handle setting a design variable when the parent is a string"""
    if Adams.evaluate_exp(f'db_exists("{parent}.{name}")') and append:
        value_ = Adams.evaluate_exp(f'{parent}.{name}')
        value_ = [value_] if not isinstance(value_, (tuple, list)) else value_
        value = value_ + value

    _cmd_set_dv(value, parent, name)


def _create_dv(value: list, parent: Object, name: str, **kwargs):
    """Creates a design variable with the given value.
    
    Parameters
    ----------
    value : List of Number, str, or Object
        Value(s) to set the design variable to
    parent : Object
        Parent object of the design variable
    name : str
        Name of the design variable
    **kwargs
        Additional keyword arguments to pass to the DesignVariable.create* methods.
    """
    if isinstance(value, List[str]):
        dv = parent.DesignVariables.createString(name=name, value=value, **kwargs)

    elif isinstance(value, List[Number]):
        dv = parent.DesignVariables.createReal(name=name, value=value, **kwargs)

    elif isinstance(value, List[int]):
        dv = parent.DesignVariables.createInteger(name=name, value=value, **kwargs)

    elif isinstance(value, List[Object]):
        dv = parent.DesignVariables.createObject(name=name, value=value, **kwargs)
    else:
        raise TypeError(f'Invalid type for value: {type(value)}')

    return dv


def _cmd_set_dv(value: list, parent: str, name: str):
    """Sets the value of a design variable. If the design variable does not exist, it is created.
    
    Parameters
    ----------
    value : Number, str, or Object (or list of any of these)
        Value(s) to set the design variable to
    parent : str
        Parent object of the design variable
    name : str
        Name of the design variable
    """
    if isinstance(value, List[str]):
        val_text = ', '.join([f'"{v}"' for v in value])
        Adams.execute_cmd(f'var set var={parent}.{name} str={val_text}')

    elif isinstance(value, List[Number]):
        val_text = ', '.join(value)
        Adams.execute_cmd(f'var set var={parent}.{name} real={val_text}')

    elif isinstance(value, List[int]):
        val_text = ', '.join(value)
        Adams.execute_cmd(f'var set var={parent}.{name} int={val_text}')

    elif isinstance(value, List[Object]):
        val_text = ', '.join(value)
        Adams.execute_cmd(f'var set var={parent}.{name} obj={val_text}')

    else:
        raise TypeError(f'Invalid type for value: {type(parent)}')
