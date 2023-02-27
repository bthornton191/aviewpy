import importlib
import sys
import unittest
from pathlib import Path

if '.' not in sys.path:
    sys.path.insert(0, '.')

# Reload Modules
modules = tuple(sys.modules.values())
for mod in modules:
    if (
        hasattr(mod, '__file__')
        and bool(mod.__file__)
        and bool(Path(mod.__file__).parents)
        and Path() in Path(mod.__file__).parents
    ):
        importlib.reload(mod)

tes_mod_names = [f'test.{file.stem}' for file in Path('test').glob('test_*.py')]
for mod_name in tes_mod_names:
    if mod_name in sys.modules:
        importlib.reload(sys.modules[mod_name])
    else:
        importlib.import_module(mod_name)
    
    unittest.main(mod_name, verbosity=2)
