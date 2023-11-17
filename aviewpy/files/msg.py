import re
from pathlib import Path

PROCESS_ID_PATTERN = re.compile('^[^\\w]*Process ID:\\s*(\\d+)[^\\w]*$', flags=re.MULTILINE | re.IGNORECASE)


def get_process_id(filename: Path):
    """Returns the process ID of the Adams job that generated the given message file.

    Parameters
    ----------
    filename : Path
        Path to the message file.

    Returns
    -------
    int
        Process ID of the Adams job that generated the given message file.

    """
    return next(int(p) for p in PROCESS_ID_PATTERN.findall(Path(filename).read_text()))
