# ---------------------
version = '1.3.6'
version_notes = (
    'Add ignore_parse parameter to get_sim_errors function\n'
    'Add logging and modify submit function\n'
    'Add turn_on_all_force_graphics module\n'
    'Add show_fbd function to display Free Body Diagram\n'
    'Formatting and changed "aview_main" to "__main__"\n'
    'Fix comparison operators in res_to_csv.py\n'
    'Add show_fbd function to create animation in Adams post processor\n'
    'Replaced Object class with ObjectComment class in variables.py. Added an adams_warning_suppressed context manager to alerts.py\n'
)
date = 'April 26th, 2024'
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
