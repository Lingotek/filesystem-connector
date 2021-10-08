# coding: utf-8
from setuptools import setup, find_packages
import sys

if sys.version_info[0] == 2:
    base_dir = 'python2'
elif sys.version_info[0] == 3:
    base_dir = 'python3'

try:
    import pypandoc

    long_description = pypandoc.convert('README.md', 'rst')
    long_description = long_description.replace("\r", "")
except (IOError, ImportError, OSError):
    long_description = open('README.md').read()

setup(
    name='ltk',
    version='1.3.13',
    url='https://github.com/Lingotek/filesystem-connector',
    description='The Lingotek Filesystem Connector (ltk) links your files and folders to the Translation Network™',
    long_description=long_description,
    author='Lingotek',
    author_email='integrations@lingotek.com',
    license='MIT',
    packages=[ 'ltk',],
    package_dir={
        'ltk' : base_dir + '/ltk',
    },
    include_package_data=True,
    install_requires=[
        'click',
        'requests[security]',
        'tinydb',
        'watchdog',
        'gitpython',
        'pexpect',
        'blessings',
        'tabulate'
    ],
    extras_require={
        'security': ['pyOpenSSL', 'ndg-httpsclient', 'pyasn1'],
    },
    entry_points='''
        [console_scripts]
        ltk=ltk.commands:ltk
    ''',
)
