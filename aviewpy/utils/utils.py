import re
from typing import List

RE_MACRO_PARAM = re.compile(r'\$(?P<name>\w+)'
                            r'(?:'
                            r'(?::t=(?P<type_>\w+)(?:\((?P<options>.*)\))?)|'
                            r'(?::c=(?P<count>\d+))|'
                            r'(?::d=(?P<default>.*))'
                            r')*'
                            r'', flags=re.IGNORECASE | re.MULTILINE)

class Param():
    def __init__(self, name, type_=None, count=1, options=None, default=None):
        self.name: str = name
        self.type: str  = type_
        self.count: int = int(count) if count is not None else 1
        self.options = options

        if default is not None and type_ == 'real':
            self.default = float(default)
        elif default is not None and type_ == 'integer':
            self.default = int(default)
        else:
            self.default = default

def get_macro_params(macro_text: str) -> List[Param]:
    """Gets all parameters from a macro

    Parameters
    ----------
    macro : str
        Text of the macro

    Example
    -------
    >>> macro_text = Path('macros/macro.mac').read_text()
    >>> params = get_macro_params(macro_text)

    Returns
    -------
    List[Param]
        Prams of the macro
    """
    params = []
    for line in macro_text.splitlines(keepends=False):
        if 'END_OF_PARAMETERS' in line:
            break
        
        for match in RE_MACRO_PARAM.finditer(line):
            param = Param(**match.groupdict())
            params.append(param)
    
    return params        
