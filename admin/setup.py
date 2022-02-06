from setuptools import setup

setup(
    name='ee-admind',
    version='1.0.0',
    packages=['ee-admind'],
    include_package_data=True,
    install_requires=[
        'PyYAML>=6.0',
        'aiohttp>=3.8.1',
        'aiohttp-session>=2.10.0',
        'python-socketio>=5.5.1',
    ],
)
