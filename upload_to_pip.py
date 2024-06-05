#! env\Scripts\Python.exe
import os
import re
from subprocess import check_output
import sys

import pkg

RE_PIP_VERSION = re.compile('^available versions: ([\\d\\.]+),', flags=re.I | re.MULTILINE)
PIP_VERSION_CMD = 'pip index versions aviewpy'

if __name__ == '__main__':

    latest_version = RE_PIP_VERSION.search(check_output(PIP_VERSION_CMD).decode()).groups()[0]
    if pkg.version == latest_version:
        print(f'The current version ({pkg.version}) is already the latest version on PyPI')
        sys.exit()

    q1 = 'Have you staged your changes? (y/n)'
    q2 = (f'This version ({pkg.version}) will succed the latest version on PyPi ({latest_version}).'
          ' Is that correct? (y/n)')

    if (input(q1).lower().startswith('y') and input(q2).lower().startswith('y')):
        # os.system('pip freeze > requirements.txt')
        # os.system('git add -u requirements.txt')
        os.system('rmdir /S /Q dist')
        os.system('rmdir /S /Q build')
        os.system('rmdir /S /Q aviewpy.egg-info')
        os.system('python setup.py sdist bdist_wheel')
        os.system('twine upload dist/*')

        # Uncomment this when you have a _update_docs.bat file
        # os.system('call _update_docs.bat')
        # os.system('git add -u docs/* rst/*')

        os.system('git commit -m "{}"'.format(pkg.commit_message))
        os.system('git push --all origin')
        os.system('git tag v{}'.format(pkg.version))
        os.system('git push origin v{}'.format(pkg.version))
