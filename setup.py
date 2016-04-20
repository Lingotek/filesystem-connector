from setuptools import setup, find_packages
from ltk import __version__

try:
    import pypandoc

    long_description = pypandoc.convert('README.md', 'rst')
    long_description = long_description.replace("\r", "")
except (IOError, ImportError, OSError):
    long_description = open('README.md').read()

setup(
    name='ltk',
    version=__version__,
    url='https://github.com/Lingotek/client',
    description='Command line tool that connects your content to the Lingotek Translation Network',
    long_description=long_description,
    author='Lingotek',
    author_email='integrations@lingotek.com',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'requests[security]',
        'tinydb',
        'watchdog',
    ],
    extras_require={
        'security': ['pyOpenSSL', 'ndg-httpsclient', 'pyasn1'],
    },
    entry_points='''
        [console_scripts]
        ltk=ltk.commands:ltk
    ''',
)
