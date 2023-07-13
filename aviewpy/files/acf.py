
from pathlib import Path
from Simulation import Simulation  # type: ignore

import Adams  # type: ignore

def write_acf(sim: Simulation, file_name: Path):
    Adams.execute_cmd('simulation script write_acf '
                      f'sim_script_name = {sim.full_name} '
                      f'file_name = "{file_name}"')
