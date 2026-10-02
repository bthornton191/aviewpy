# ---------------------
version = '1.4.0'
commit_message = (
    'Linux support: solve() finds the mdi launcher from lowercase topdir / '
    'ADAMS_LAUNCH_COMMAND (no common/mdi.bat on Linux), closes stdin on the '
    'POSIX launcher, and temp_sim_prefs only rewrites file_prefix separators '
    'to backslashes on Windows'
)
date = 'October 2nd, 2026'
# ---------------------
author = 'Ben Thornton'
author_email = 'ben.thornton@hexagon.com'
name = 'aviewpy'
description = 'Python tools for working with in the Adams View python environment'
install_requires = ['numpy>=1.20.0',
                    'pandas',
                    'scipy',
                    'numpy-stl',
                    'matplotlib>=3.5',
                    'adamspy']
