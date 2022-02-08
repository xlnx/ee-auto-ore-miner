import os
import sys
import pathlib
import subprocess
from setuptools import setup
from setuptools.command.build_py import build_py


class BuildPyCommand(build_py):

    def run(self):
        cwd = pathlib.Path().absolute()
        js = os.path.join(str(cwd), 'echoes/admind')
        cmds = [
            'yarn install',
            'yarn run build',
        ]
        for cmd in cmds:
            _, err = subprocess.Popen(
                cmd.split(' '),
                cwd=js,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT).communicate()
            if err:
                sys.exit(-1)
        build_py.run(self)


setup(
    name='echoes-admind',
    version='1.2.0',
    packages=['echoes', 'echoes.admind'],
    include_package_data=True,
    cmdclass={
        'build_py': BuildPyCommand,
    },
    install_requires=[
        'PyYAML>=6.0',
        'aiohttp>=3.8.1',
        'aiohttp-session>=2.10.0',
        'python-socketio>=5.5.1',
    ],
)
