# ---------------------
version = '1.4.1'
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
install_requires = ['numpy>=1.20,<2', 'pandas>=1.5,<2.3', 'scipy>=1.6,<1.14', 'numpy-stl', 'matplotlib>=3.4', 'adamspy>=0.33.0']
