import os
from pathlib import Path

from .bin import get_bin_version, read_bin_file, write_bin_file

import Adams # type: ignore # isort: skip # pylint: disable=wrong-import-order

def cached_model_import(cmd_file: Path):
    """Imports a model from a cmd file and caches it in a binary file. Imports from the binary
    file if it already exists and is newer than the cmd file.

    Parameters
    ----------
    cmd_file : Path
        Adams View Command (.cmd) file containing a single model.
    """
    cmd_file = Path(cmd_file)
    cached_file = cmd_file.with_suffix('.cached')

    existing_models = Adams.Models.values()

    # Check
    if (cached_file.exists()
            and cached_file.stat().st_mtime > cmd_file.stat().st_mtime
            and get_bin_version(cached_file) == os.environ['VERSION']):

        # If the cache file exists and it is newer than the cmd file and uses the same version,
        # Read in the cached file
        read_bin_file(cached_file)
    
    else:

        # If the cached file does not exist or it is older than the cmd file
        # Read in the cmd file
        Adams.read_command_file(cmd_file)
        
        # Write the cached file
        mod = next(m for m in Adams.Models.values() if m not in existing_models)
        write_bin_file(cached_file, mod)
    
