#!/usr/bin/env python

from os.path import join
from setuptools import setup

VERSION = (5,1,1)
__versionstr__ = '.'.join(map(str, VERSION))
setup(
    name='karp-backend',
    version=__versionstr__,
    description='Backend for Karp',
    author='Språkbanken at the University of Gothenburg',
    maintainer='Kristoffer Andersson',
    maintainer_email='kristoffer.andersson@gu.se',
    url='https://www.github.com/spraakbanken/karp-backend',
    # packages_dir={'':'.'}
    # py_modules=['offline.py'],
    # packages_dir={'karp_backend': 'src'},
    packages=[
        'karp_backend',
        'karp_backend.dbhandler',
        'karp_backend.offline',
        'karp_backend.server',
        'karp_backend.server.helper',
        'karp_backend.server.translator'
    ],
    install_requires=[
        'elasticsearch>=6.0.0',
        'elasticsearch-dsl>=6.0.0',
        'Flask>=0.12.3',
        'SQLAlchemy',
        'urllib3'
    ]

)
