from pathlib import Path
from typing import List

import Adams  # type: ignore
from adamspy.postprocess.msg import get_errors
from Analysis import Analysis  # type: ignore

from aviewpy.objects import get_parent_model  # type: ignore

SIM_STAT_ERROR_MSG = 'static equilibrium analysis has not been successful'
PARSE_ERROR_MSG = 'errors found parsing command. command ignored.'


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

    Returns
    -------
    Analysis
        The analysis that the result component was created in. This is returned because the `ans` 
        argument is not updated in place.
    """
    if len(values) == 0:
        raise ValueError('No values to create result component with.')

    if res_name in ans.results and comp_name in ans.results[res_name]:
        raise ValueError(f'Result component {ans.name}.{res_name}.{comp_name} already exists!')

    value_str = ','.join([str(val) for val in values])
    Adams.execute_cmd(f'numeric_results create values '
                      f'units = {units} '
                      f'new_result_set_component_name = {ans.full_name}.{res_name}.{comp_name} '
                      f'values = {value_str}')

    return get_parent_model(ans).Analyses[ans.name]


def get_sim_errors(msg_file: Path, ignore_static: bool = False, ignore_parse: bool = False):
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

    if ignore_parse:
        errors = [e for e in errors if PARSE_ERROR_MSG.lower() not in e.lower()]

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
