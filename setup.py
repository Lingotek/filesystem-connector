from setuptools import setup, find_packages

setup(
    name='',
    version='',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'click',
        'requests',
    ],
    entry_points='''
        [console_scripts]
        ltk=lib.commands:ltk
    ''',
)