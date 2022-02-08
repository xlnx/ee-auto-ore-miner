from setuptools import setup

setup(
    name='echoes-miner',
    version='1.2.0',
    packages=['echoes', 'echoes.miner', 'echoes.client'],
    include_package_data=True,
    install_requires=[
        'PyYAML>=6.0',
        'cnocr>=2.1.0',
        'opencv-python>=4.5.5.62',
        'python-socketio>=5.5.1',
    ],
)
