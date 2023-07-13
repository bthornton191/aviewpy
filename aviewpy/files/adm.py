
from pathlib import Path
from Model import Model  # type: ignore

import Adams  # type: ignore

def write_adm(mod: Model, file_name: Path):
    Adams.execute_cmd('file adams_data_set write '
                      f'model_name = {mod.full_name} '
                      f'file_name = "{file_name}"')
