
import os
from pathlib import Path
import re
from typing import Union
import unicodedata

import Adams  # type: ignore # noqa
from Object import Object  # type: ignore # noqa


def write_bin_file(filename: Path, entity: Object = None, alert=False):
    cmd = 'file bin write file="{}" alert={}'.format(filename, 'yes' if alert else 'no')
    if entity is not None:
        cmd += f' entity={entity.full_name}'

    Adams.execute_cmd(cmd)


def read_bin_file(filename: Path, entity_name: str = None, alert=False):
    cmd = 'file bin read file="{}" alert={}'.format(filename, 'yes' if alert else 'no')
    if entity_name is not None:
        cmd += f' entity={entity_name}'

    Adams.execute_cmd(cmd)


def get_bin_version(filename: Union[Path, str]):
    with Path(filename).open('rb') as fid:
        line = fid.readline()

    text = ''.join([ch for ch in line.decode('ascii', errors='ignore')
                    if unicodedata.category(ch)[0] != "C"])
    comps = re.findall('version\\s([\\d\\.]*)', text, flags=re.IGNORECASE)[0].split('.')
    year = int(comps[0])

    # If there is a release
    if len(comps) > 1 and len(comps[1]) <= 2:
        release = int(comps[1])
    else:
        release = 0

    # If there is an update
    if len(comps) > 2 and len(comps[2]) <= 2:
        update = int(comps[2])
    else:
        update = 0

    # If there is a build number at the and it would be longer than 2 digits
    if len(comps[-1]) > 4:
        build = int(comps[-1])
    else:
        build = 0

    # Store any other components in a list
    if len(comps) > 3:
        other = (int(comp) for comp in comps[3:] if len(comp) <= 2)
    else:
        other = ()

    return '_'.join(str(val) for val in (year, release, update, build) + other
                    if isinstance(val, int) and val != 0)

def is_compatible(filename: Union[Path, str]):
    bin_ver = get_bin_version(filename)
    adams_ver =  os.environ['VERSION']

    for bv, av in zip(bin_ver.split('_'), adams_ver.split('_')):
        if bv > av:
            return False
    
    return True
