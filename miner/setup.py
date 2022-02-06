from setuptools import setup

setup(
    name='ee-miner',
    version='1.0.0',
    packages=['ee-miner', 'ee-miner.client', 'ee-miner.miner'],
    include_package_data=True,
    install_requires=[
        'PyYAML>=6.0',
        'cnocr>=2.1.0',
        'opencv-python>=4.5.5.62',
        'python-socketio>=5.5.1',
    ],
)
