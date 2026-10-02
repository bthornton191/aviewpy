"""Platform-portable tests for `aviewpy.sim` (launcher discovery + prefs).

These run WITHOUT Adams: everything Adams-touching is mocked. The target
behaviours are the Linux-port fixes tracked downstream as CDM WP3
(linux-port-audit findings B3/B4):

* ``solve()`` must locate the mdi launcher from ``TOPDIR`` **or** the
  lowercase ``topdir`` (only the lowercase form exists on Linux), honour
  ``ADAMS_LAUNCH_COMMAND`` when set, and build the POSIX argv as
  ``[mdi, '-c', 'ru-standard', 'i', <acf>, 'exit']`` with stdin closed.
* ``temp_sim_prefs`` must rewrite ``file_prefix`` separators to backslashes
  ONLY on Windows -- on POSIX a directory-bearing prefix must survive
  verbatim.
"""
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ``aviewpy.sim`` imports the in-Aview ``Adams``/``Simulation`` modules at
# import time, and ``aviewpy.files.bin`` (imported by sim for write_bin_file)
# additionally imports ``Object``; the portable tests never touch those, so
# provide placeholders before import.
sys.modules.setdefault('Adams', MagicMock())
sys.modules.setdefault('Simulation', MagicMock())
sys.modules.setdefault('Object', MagicMock())

from aviewpy import sim  # noqa: E402


class _FakeAdams:
    """Stand-in for the in-Aview ``Adams`` module."""

    def __init__(self, file_prefix):
        self._file_prefix = file_prefix
        self.commands = []

    def evaluate_exp(self, expression):
        if expression == '.sim_preferences.file_prefix':
            return self._file_prefix
        raise AssertionError(f'unexpected expression: {expression}')

    def execute_cmd(self, cmd):
        self.commands.append(cmd)


def _run_solve(platform, env, acf_name='model.acf'):
    """Call ``sim.solve`` with Adams/PATH mocks; return the Popen kwargs."""
    acf = Path('C:/work' if platform == 'Windows' else '/tmp/work') / acf_name
    popen_kwargs = {}

    def fake_popen(command, **kwargs):
        popen_kwargs['command'] = command
        popen_kwargs.update(kwargs)
        return MagicMock(pid=1234)

    with patch.object(sim.platform, 'system', lambda: platform), \
            patch.dict('os.environ', env, clear=True), \
            patch.object(subprocess, 'Popen', fake_popen):
        proc = sim.solve(acf)
    assert proc is not None
    return popen_kwargs


class TestSolveLauncherDiscovery(unittest.TestCase):

    def test_windows_topdir_builds_mdi_bat(self):
        kwargs = _run_solve('Windows', {'TOPDIR': 'C:/Program Files/MSC.Software/Adams/2023_4_1'})
        command = kwargs['command']
        self.assertIsInstance(command, str)
        self.assertIn('mdi.bat', command)
        self.assertIn('ru-s', command)

    def test_linux_lowercase_topdir_builds_mdi(self):
        kwargs = _run_solve('Linux', {'topdir': '/home/thornton/adams/2023_4_1'})
        command = kwargs['command']
        # The launcher element is built with pathlib, which renders with the
        # HOST's separator -- these tests run on Windows too, so compare it as
        # a path rather than as a string. The argv shape around it is what the
        # POSIX fix is about and is compared literally.
        self.assertEqual(Path(command[0]), Path('/home/thornton/adams/2023_4_1/mdi'))
        self.assertEqual(command[1:], ['-c', 'ru-standard', 'i', 'model.acf', 'exit'])

    def test_adams_launch_command_wins_on_linux(self):
        kwargs = _run_solve('Linux', {
            'topdir': '/home/thornton/adams/2023_4_1',
            'ADAMS_LAUNCH_COMMAND': '/opt/adams/2023_4_1/mdi'})
        self.assertEqual(Path(kwargs['command'][0]), Path('/opt/adams/2023_4_1/mdi'))

    def test_linux_adams_car_form(self):
        acf = Path('/tmp/work/model.acf')
        popen_kwargs = {}

        def fake_popen(command, **kwargs):
            popen_kwargs['command'] = command
            popen_kwargs.update(kwargs)
            return MagicMock(pid=1234)

        with patch.object(sim.platform, 'system', lambda: 'Linux'), \
                patch.dict('os.environ', {'topdir': '/home/a/2023_4_1'}, clear=True), \
                patch.object(subprocess, 'Popen', fake_popen):
            sim.solve(acf, use_adams_car=True)
        command = popen_kwargs['command']
        self.assertEqual(Path(command[0]), Path('/home/a/2023_4_1/mdi'))
        self.assertEqual(command[1:],
                         ['-c', 'acar', 'ru-solver', 'i', 'model.acf', 'exit'])

    def test_missing_launcher_env_raises_runtime_error(self):
        acf = Path('/tmp/work/model.acf')
        with patch.object(sim.platform, 'system', lambda: 'Linux'), \
                patch.dict('os.environ', {}, clear=True):
            with self.assertRaises(RuntimeError):
                sim.solve(acf)

    def test_linux_launcher_has_no_common_mdi_bat(self):
        """The historic Windows-only shape must not appear on POSIX."""
        kwargs = _run_solve('Linux', {'topdir': '/home/a/2023_4_1'})
        launcher = Path(kwargs['command'][0])
        self.assertEqual(launcher.name, 'mdi')
        self.assertNotIn('common', launcher.parts)

    def test_posix_stdin_is_devnull(self):
        kwargs = _run_solve('Linux', {'topdir': '/home/a/2023_4_1'})
        self.assertIs(kwargs.get('stdin'), subprocess.DEVNULL)


class TestTempSimPrefsSeparators(unittest.TestCase):

    def _run_prefs(self, platform, value):
        adams = _FakeAdams('C:/old/prefix')
        commands = []
        with patch.object(sim.platform, 'system', lambda: platform), \
                patch.object(sim, 'Adams', adams), \
                patch.object(sim.LOG, 'debug', commands.append):
            with sim.temp_sim_prefs(file_prefix=value):
                pass
        return commands

    def test_windows_rewrites_separators_to_backslashes(self):
        commands = self._run_prefs('Windows', 'C:/new/prefix')
        set_new = [c for c in commands if 'new' in c][0]
        self.assertIn('file_prefix = "C:\\\\new\\\\prefix"', set_new)
        # ...and the ORIGINAL is restored with backslashes too (historic shape)
        restore = [c for c in commands if 'old' in c][0]
        self.assertIn('file_prefix = "C:\\\\old\\\\prefix"', restore)

    def test_posix_keeps_posix_separators_verbatim(self):
        commands = self._run_prefs('Linux', '/tmp/set42/prefix')
        set_new = [c for c in commands if 'set42' in c][0]
        self.assertIn('file_prefix = "/tmp/set42/prefix"', set_new)
        self.assertNotIn(chr(92), set_new)

    def test_posix_restore_keeps_posix_separators(self):
        commands = self._run_prefs('Linux', '/tmp/set42/prefix')
        restore = [c for c in commands if 'old' in c][0]
        self.assertIn('file_prefix = "C:/old/prefix"', restore)
        self.assertNotIn(chr(92), restore)


if __name__ == '__main__':
    unittest.main()
