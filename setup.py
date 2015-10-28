from setuptools import setup, find_packages
from lib import __version__

setup(
    name='',
    version=__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'requests[security]',
        'tinydb',
    ],
    extras_require={
        'security': ['pyOpenSSL', 'ndg-httpsclient', 'pyasn1'],
    },
    entry_points='''
        [console_scripts]
        ltk=lib.commands:ltk
    ''',
)
