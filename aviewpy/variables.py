
from numbers import Number
from typing import Iterable, List, Union


import Adams  # type: ignore # noqa # isort: skip
from Object import Object  # type: ignore # noqa # isort: skip


def set_dv(parent: Object, name: str,
           value: List[Union[Number, str, Object]], append=False, **kwargs):
    # Make sure the value is a list
    value = [value] if not isinstance(value, Iterable) or isinstance(value, str) else value

    if name in parent.DesignVariables:
        # And the design variable already exists
        dv = parent.DesignVariables[name]

        if append:
            value = dv.value + value

        dv.update(value=value, **kwargs)

    elif isinstance(value[0], int):
        # And the design variable does not exist and it's an **Integer**
        dv = parent.DesignVariables.createInteger(name=name, value=value, **kwargs)

    elif isinstance(value[0], Number):
        # And the design variable does not exist and it's a **Float**
        dv = parent.DesignVariables.createReal(name=name, value=value, **kwargs)

    elif isinstance(value[0], Object):
        # And the design variable does not exist and it's an **Object**
        dv = parent.DesignVariables.createObject(name=name, value=value, **kwargs)

    else:
        try:
            value = [str(v) for v in value]
        except Exception as err:
            raise ValueError('Unrecognized value type!') from err

        dv = parent.DesignVariables.createString(name=name, value=value, **kwargs)

    return dv
