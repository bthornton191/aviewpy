from pathlib import Path
from typing import List
from adamspy.postprocess.msg import get_errors
import Adams # type: ignore # noqa # isort:skip
from Analysis import Analysis # type: ignore # noqa # isort:skip

SIM_STAT_ERROR_MSG = 'static equilibrium analysis has not been successful'

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


def get_sim_errors(msg_file: Path, ignore_static: bool = False):
    """Get the simulation errors from a .msg file.
    
    Parameters
    ----------
    msg_file : Path
        The .msg file to get the errors from.
    
    Returns
    -------
    List[str]
        The list of errors.
    """
    errors: List[str] = get_errors(msg_file)
    
    if ignore_static:
        errors = [e for e in errors if SIM_STAT_ERROR_MSG.lower() not in e.lower()]
    
    return errors

def write_results(ans: Analysis, file_name: Path, binary=False):
    """Write the results of an analysis.
    
    Parameters
    ----------
    ans : Analysis
        The analysis to write the results of.
    binary : bool, optional
        Whether to write the results in binary format, by default False
    """
    
    if binary and ans.parent is not None:
        xrf = Adams.evaluate_exp(f'user_string("{ans.parent.full_name}.analysis_flags.results_xrf")')
        Adams.evaluate_exp(f'output set results model = {ans.parent.full_name} xrf = off')
    
    try:
        
        Adams.execute_cmd(f'file analysis write analysis={ans.full_name} file="{file_name}"')
        
    finally:
        if binary and ans.parent is not None:
            Adams.evaluate_exp(f'output set results model = {ans.parent.full_name} xrf = {xrf}')
