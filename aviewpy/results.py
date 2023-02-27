from typing import List

import Adams # type: ignore # noqa # isort:skip
from Analysis import Analysis # type: ignore # noqa # isort:skip

def create_result(ans: Analysis, res_name: str, comp_name: str, values: List[float], units: str):
    """Convenience function to create a result component.
    
    Parameters
    ----------
    ans : Analysis
        The analysis to create the result component in.
    res_name : str
        The name of the result set to create.
    comp_name : str
        The name of the result component to create.
    values : List[float]
        The values to set for the result component.
    units : str
        The units of the result component.
    """
    if len(values) == 0:
        raise ValueError('No values to create result component with.')
    
    value_str = ','.join([str(val) for val in values])
    cmd = f'numeric_results create values values = {value_str} units = {units} new_result_set_component_name = {ans.full_name}.{res_name}.{comp_name}'

    Adams.execute_cmd(cmd)
