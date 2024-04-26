
from numbers import Number
from typing import List, Tuple, TypeVar, Union, overload

import Adams  # type: ignore
from Object import ObjectBase  # type: ignore
from Object import ObjectComment  # type: ignore
from DesignVariable import DesignVariable  # type: ignore


@overload
def set_dv(parent: str,
           name: str,
           value: Union[Number, str, ObjectBase],
           append=False,
           **kwargs) -> None:
    ...


@overload
def set_dv(parent:  Union[ObjectComment, ObjectBase],
           name: str,
           value: Union[Number, str, ObjectBase],
           append=False,
           **kwargs) -> DesignVariable:
    ...


def set_dv(parent: Union[str, ObjectComment, ObjectBase],
           name: str,
           value,
           append=False,
           **kwargs) -> Union[DesignVariable, None]:
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
    value = make_list(value)

    if len(value) == 0:
        raise ValueError('Value cannot be an empty list!')

    if isinstance(parent, str):
        _set_dv_str(parent, name, value, append)
        dv = None

    elif isinstance(parent, ObjectComment):
        dv = _set_dv_obj(parent, name, value, append, **kwargs)

    elif isinstance(parent, ObjectBase):
        # Must treat `ObjectBase`s that aren't `ObjectComment`s (e.g. `Analysis`) different because the
        # python API doesn't support setting desisgn variables for analyses, but the cmd API does...
        _set_dv_str(parent.full_name, name, value, append)
        dv = None

    else:
        raise TypeError(f'The parent must be an ObjectComment or str, not {type(parent)}')

    return dv


def _set_dv_obj(parent: ObjectComment, name: str, value: List[Union[Number, str, ObjectBase]], append=False, **kwargs):
    """Function to handle setting a design variable when the parent is an ObjectBase"""
    if name in parent.DesignVariables:
        # If the design variable already exists
        dv = parent.DesignVariables[name]

        if append:
            try:
                orig_val = dv.value
            except OSError:
                orig_val = make_list(Adams.evaluate_exp(f'{dv.full_name}'))

            value = orig_val + value

        dv.update(value=value, **kwargs)

    else:
        dv = _create_dv(value, parent, name, **kwargs)

    return dv


def _set_dv_str(parent: str, name: str, value: List[Union[Number, str, ObjectBase]], append=False) -> None:
    """Function to handle setting a design variable when the parent is a string"""
    if Adams.evaluate_exp(f'db_exists("{parent}.{name}")') and append:
        value = make_list(Adams.evaluate_exp(f'{parent}.{name}')) + value

    _cmd_set_dv(value, parent, name)


def _create_dv(value: list, parent: ObjectComment, name: str, **kwargs):
    """Creates a design variable with the given value.

    Parameters
    ----------
    value : List of Number, str, or ObjectBase
        Value(s) to set the design variable to
    parent : ObjectComment
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
        val_text = ', '.join([f'{v.full_name}' for v in value])
        Adams.execute_cmd(f'var set var={parent}.{name} obj={val_text}')

    else:
        raise TypeError(f'Invalid type for value: {type(value)}')


class NO_DEFAULT:
    pass


def get_dv(parent: Union[ObjectBase, str],
           name: str,
           default: List[Union[Number, str, ObjectComment]] = NO_DEFAULT) -> List[Union[Number, str, ObjectComment]]:
    """Returns the value of the design variable `name` from the object `parent`.

    Parameters
    ----------
    parent : ObjectBase or str
        Parent object of the design variable
    name : str
        Name of the design variable

    Returns
    -------
    List[Number, str, or ObjectComment]
        Value(s) of the design variable
    """
    if isinstance(parent, ObjectBase):
        parent = parent.full_name
    elif not isinstance(parent, str):
        raise TypeError(f'Invalid type for parent: {type(parent)}')

    dvs = make_list(Adams.evaluate_exp(f'db_children({parent}, "variable")'))

    if f'{parent}.{name}'.lower() in [n.lower() for n in dvs]:
        value = Adams.evaluate_exp(f'{parent}.{name}')
    elif default is NO_DEFAULT:
        raise ValueError(f'No design variable named "{name}" exists for object "{parent}"')
    else:
        value = default

    # Make sure the value is a list
    value = make_list(value)

    return value


Input = TypeVar('Input')


@overload
def make_list(value: str) -> List[str]:
    ...


@overload
def make_list(value: List[Input]) -> List[Input]:
    ...


@overload
def make_list(value: Tuple[Input]) -> List[Input]:
    ...


@overload
def make_list(value: Input) -> List[Input]:
    ...


def make_list(value: str) -> List[str]:
    return list(value) if isinstance(value, (list, tuple)) else [value]
