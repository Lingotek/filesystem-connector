from setuptools import setup, find_packages
from lib import __version__

setup(
    name='ltk',
    version=__version__,
    url='https://github.com/Lingotek/client',
    description='Command line tool that connects your content to the Lingotek Translation Network',
    license='MIT',
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
