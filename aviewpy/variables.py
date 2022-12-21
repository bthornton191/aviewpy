
from numbers import Number
from typing import Iterable, List, Union

from Object import Object  # type: ignore # noqa


def set_dv(parent: Object, name: str, value: List[Union[Number, str, Object]], **kwargs):
    # Make sure the value is a list
    value = [value] if not isinstance(value, Iterable) else value

    if name in parent.DesignVariables:

        # If the design variable already exists
        dv = parent.DesignVariables[name]
        dv.update(value=value, **kwargs)

    elif isinstance(value[0], int):

        # If the design variable does not exist and it's an **Integer**
        dv = parent.DesignVariables.createInteger(name=name, value=value, **kwargs)

    elif isinstance(value[0], Number):
        # If the design variable does not exist and it's a **Float**
        dv = parent.DesignVariables.createReal(name=name, value=value, **kwargs)

    elif isinstance(value[0], Object):
        # If the design variable does not exist and it's an **Object**
        dv = parent.DesignVariables.createObject(name=name, value=value, **kwargs)

    else:
        try:
            value = [str(v) for v in value]
        except Exception as err:
            raise ValueError('Unrecognized value type!') from err

        dv = parent.DesignVariables.createString(name=name, value=value, **kwargs)

    return dv
