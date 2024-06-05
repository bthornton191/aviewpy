# ---------------------
version = '1.3.8'
commit_message = (
    'Improved typing\n'
    'added an optional `callback` argument to `sim.submit()` allowing a Callable to be passed to `sim.submit()` that is called after the simulation files are written.\n'
)
date = 'June 5th, 2024'
# ---------------------
author = 'Ben Thornton'
author_email = 'ben.thornton@hexagon.com'
name = 'aviewpy'
description = 'Python tools for working with in the Adams View python environment'
install_requires = ['numpy',
                    'pandas',
                    'scipy',
                    'numpy-stl',
                    'adamspy']
