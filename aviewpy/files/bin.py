
from pathlib import Path

import Adams  # type: ignore # noqa
from Object import Object  # type: ignore # noqa


def write_bin_file(filename: Path, entity: Object = None, alert=False):
    cmd = 'file bin write file="{}" alert={}'.format(filename, 'yes' if alert else 'no')
    if entity is not None:
        cmd+= f' entity={entity.full_name}'
    
    Adams.execute_cmd(cmd)

def read_bin_file(filename: Path, entity: Object = None, alert=False):
    cmd = 'file bin read file="{}" alert={}'.format(filename, 'yes' if alert else 'no')
    if entity is not None:
        cmd+= f' entity={entity.full_name}'
    
    Adams.execute_cmd(cmd)
