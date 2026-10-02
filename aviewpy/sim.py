import logging
import os
import platform
import shutil
import subprocess
from contextlib import contextmanager
from math import log10
from numbers import Number
from pathlib import Path
from typing import Callable, List, Tuple, Union

import Adams  # type: ignore
from Simulation import Simulation  # type: ignore

from .files.bin import write_bin_file
from .files.msg import get_process_id

SIM_PREFERNCES = ['internal', 'external', 'write_files_only']
SIM_EXTS = ['.acf', '.adm', '.xmt_txt', '.req', '.res', '.msg', '.out', '.gra']


LOG = logging.getLogger(__name__)


def static_funnel(steps: int, **kwargs: Union[float, Tuple[float, float]]) -> List[str]:
    """Generate a list of acf commands to simulate a static equilibrium funnel.

    Parameters
    ----------
    steps : int
        The number of steps in the funnel
    **kwargs : float or Tuple[float, float]]
        The parameters to vary in the funnel. The value can be a single number, in which case
        the parameter is held constant, or a tuple of two numbers, in which case the parameter
        is varied linearly between the two values.
    """
    lines = []
    for step in range(1, steps + 1):
        params = []
        for key, value in kwargs.items():
            if isinstance(value, Number):
                val = value
            else:
                start_value, end_value = value

                if start_value > 0 and end_value > 0:

                    # If both values are positive (most likely), interpolate logarithmically
                    start_value = log10(start_value)
                    end_value = log10(end_value)
                    val = 10 ** (start_value + (end_value - start_value) * step / steps)

                else:

                    # If either value is negative, interpolate linearly
                    val = start_value + (end_value - start_value) * step / steps

            params.append(f'{key}={val:d}' if isinstance(val, int) else f'{key}={val:.2e}')

        lines.append('equilibrium/' + ', '.join(params))
        lines.append('simulate/static')

    return lines


def write_simulation_files(sim: Simulation,
                           file_prefix: str,
                           working_dir: Path = None,
                           aux_files: List[Path] = None,
                           write_cmd=False,
                           write_bin=False):

    if aux_files is not None and working_dir is not None:
        for aux_file in aux_files:
            shutil.copy(aux_file, working_dir)

        current_files = {f: os.stat(f).st_mtime for f in Path().iterdir()}

    if write_cmd:
        # Write the .cmd file. (NOTE: This file is for reference only)
        Adams.write_command_file(file_name=f'{file_prefix}_.cmd', model=sim.parent)

    if write_bin:
        write_bin_file(filename=f'{file_prefix}.bin', entity=sim.parent)

    # Write the analysis files
    with temp_sim_prefs(solver_preference='write_files_only', file_prefix=file_prefix):
        Adams.execute_cmd('simulation single_run scripted'
                          f'    model_name={sim.parent.full_name}'
                          f'    sim_script_name={sim.full_name}')

    if working_dir is not None:

        # Move all new files
        files = [f for f in Path().iterdir() if f not in current_files]

        # Move all files that have been modified
        files += [f for f, st_mtime in current_files.items()
                  if os.stat(f).st_mtime != st_mtime]

        for file in (f for f in files if f.suffix not in ['.log', '.tmp']):
            if (working_dir / file.name).is_file():
                (working_dir / file.name).unlink()
            shutil.move(file.name, working_dir)


def solve(acf_file: Path, wait=False, use_adams_car=False) -> subprocess.Popen:
    """Runs Adams Solver to solve the model specified in `acf_file`

    Parameters
    ----------
    acf_file : str
        Path to an Adams Command (.acf) File
    wait : bool, optional
        Whether to wait for the simulation to complete, by default False
    use_adams_car : bool, optional
        Whether to use Adams/Car to solve the simulation, by default False

    Returns
    -------
    subprocess.Popen
        The process running the Adams Solver
    """
    acf_file = Path(acf_file).absolute()
    cwd = str(acf_file.parent)
    # Cross-platform launcher discovery (Linux port, tracked downstream as
    # CDM WP3 / audit B3). On Windows the launcher is
    # <topdir>/common/mdi.bat and TOPDIR is exported; on Linux the install
    # exports only the lowercase ``topdir`` and the launcher is
    # <topdir>/mdi -- there is no common/ directory and no mdi.bat, so the
    # historic os.environ['TOPDIR'] raised KeyError there. An explicit
    # ADAMS_LAUNCH_COMMAND wins on both platforms: callers that drive a
    # specific Adams install (the CDM qualification harness does) set it,
    # and it must not be overridden by whatever topdir the ambient session
    # happens to carry.
    launch_cmd = os.environ.get('ADAMS_LAUNCH_COMMAND')
    topdir = os.environ.get('TOPDIR') or os.environ.get('topdir')
    if launch_cmd:
        mdi_cmd = Path(launch_cmd)
    elif topdir and platform.system() == 'Windows':
        mdi_cmd = Path(topdir) / 'common' / 'mdi.bat'
    elif topdir:
        mdi_cmd = Path(topdir) / 'mdi'
    else:
        raise RuntimeError(
            'Neither ADAMS_LAUNCH_COMMAND nor TOPDIR/topdir is set; cannot '
            'locate the Adams mdi launcher to solve ' + str(acf_file))

    if platform.system() == 'Windows':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        if use_adams_car is False:
            command = f'"{mdi_cmd}" ru-s "{acf_file.name}"'
        else:
            command = f'"{mdi_cmd}" acar ru-solver "{acf_file.name}"'

        proc = subprocess.Popen(command, cwd=cwd, startupinfo=startupinfo)

    else:
        # POSIX mdi is a csh wrapper: '-c' selects the product run and the
        # trailing 'exit' stops the wrapper from spinning at its menu
        # prompt once the solver returns. stdin is closed for the same
        # reason -- a live stdin keeps the menu alive.
        if use_adams_car is False:
            command = [str(mdi_cmd), '-c', 'ru-standard', 'i', acf_file.name, 'exit']
        else:
            command = [str(mdi_cmd), '-c', 'acar', 'ru-solver', 'i', acf_file.name, 'exit']

        proc = subprocess.Popen(command, cwd=cwd, stdin=subprocess.DEVNULL)

    if wait:
        proc.wait()

    return proc


def submit(sim: Simulation,
           file_prefix: str,
           use_adams_car=False,
           wait=False,
           write_cmd=False,
           write_bin=False,
           just_write_files=False,
           callback: Callable = None):
    """Run a simulation externally and import results on completion.

    Parameters
    ----------
    sim : Simulation
        The simulation to submit
    file_prefix : str
        The prefix for the simulation files
    use_adams_car : bool, optional
        Whether to use Adams/Car to solve the simulation, by default False
    wait : bool, optional
        Whether to wait for the simulation to complete, by default False
    write_cmd : bool, optional
        Whether to write a .cmd file of the current model (for reference only), by default False
    write_bin : bool, optional
        Whether to write a .bin file of the current model (for reference only), by default False
    just_write_files : bool, optional
        Whether to just write the simulation files and not run the simulation, by default False
    callback : Callable, optional
        A function to run before the simulation is submitted, by default None
    Returns
    -------
    subprocess.Popen
        The process running the Adams Solver
    """
    acf_file = Path.cwd() / f'{file_prefix}.acf'

    write_simulation_files(sim, file_prefix, write_cmd=write_cmd, write_bin=write_bin)

    if callback is not None:
        callback()

    if not just_write_files:
        proc = solve(acf_file, wait=wait, use_adams_car=use_adams_car)
    else:
        proc = None

    return proc


@contextmanager
def temp_sim_prefs(**kwargs):
    """Context manager to temporarily change simulation preferences.


    Parameters
    ----------
    **kwargs : dict
        The simulation preferences to change. The keys should be the names of the preferences
        and the values should be the new values.

    Examples
    --------
    To temporarily change the solver preference to external:
    ```python
    with temporary_sim_preferences(solver_preference='external'):
        sim.simulate()
    ```

    To temporarily write files and set the file prefix
    ```python
    with temporary_sim_preferences(file_prefix='my_sim', save_files=True):
        sim.simulate()
    ```
    """
    current_settings = {}
    for key, value in kwargs.items():
        if key == 'solver_preference':
            current_settings[key] = SIM_PREFERNCES[Adams.evaluate_exp('.sim_preferences.solver_preference')]
        elif key == 'file_prefix':
            file_prefix = Adams.evaluate_exp('.sim_preferences.file_prefix')
            if platform.system() == 'Windows':
                # Windows separators only (Linux port / audit B4): the
                # historic unconditional rewrite mangled directory-bearing
                # prefixes on POSIX, where the separator must stay '/'.
                current_settings[key] = '"{}"'.format(Path(file_prefix).as_posix().replace('/', r'\\'))
                value = '"{}"'.format(Path(value).as_posix().replace('/', r'\\'))
            else:
                current_settings[key] = '"{}"'.format(Path(file_prefix).as_posix())
                value = '"{}"'.format(Path(value).as_posix())
        else:
            current_settings[key] = Adams.evaluate_exp(f'.sim_preferences.{key}')

        # Convert bools to yes/no
        if isinstance(value, bool):
            value = 'yes' if value else 'no'

        cmd = f'simulation set {key} = {value}'
        LOG.debug(f'Running command: {cmd}')
        Adams.execute_cmd(cmd)

    yield

    for key, value in current_settings.items():
        cmd = f'simulation set {key} = {value}'
        LOG.debug(f'Running command: {cmd}')
        Adams.execute_cmd(cmd)


def solve_internal(sim: Simulation, reset=False):
    """Solve a simulation internally.

    Parameters
    ----------
    sim : Simulation
        The simulation to solve
    reset : bool, optional
        Whether to reset the simulation before solving, by default False
    """
    Adams.execute_cmd('simulation single_run scripted '
                      f'model_name={sim.parent.full_name} '
                      f'sim_script_name={sim.full_name} '
                      f'reset={"yes" if reset else "no"}')
