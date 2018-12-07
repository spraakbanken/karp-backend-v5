#!/usr/bin/env python

from setuptools import find_packages
from setuptools import setup

setup(
    name='karp-backend',
    version='5.2.0',
    description='Backend for Karp',
    author='Språkbanken at the University of Gothenburg',
    maintainer='Språkbanken',
    maintainer_email='sb-info@svenska.gu.se',
    url='https://www.github.com/spraakbanken/karp-backend',
    # packages_dir={'':'.'}
    # py_modules=['offline.py'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    package_data={
        'karp-backend': ['src/karp_backend/html/*']
    },
    # packages=[
        # 'karp_backend',
    #     'karp_backend.dbhandler',
    #     'karp_backend.offline',
    #     'karp_backend.server',
    #     'karp_backend.server.helper',
    #     'karp_backend.server.translator'
    # ],
    install_requires=[
        'elasticsearch>=6.1.0,<6.2.0',
        'elasticsearch-dsl>=6.0.0,<7.0.0',
        'Flask>=0.12.3, <1.0.0',
        'SQLAlchemy',
        'urllib3',
        'gevent==1.2.2',
        'six',
        'pymsql',
        'markdown'
    ],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 2 - Pre-Alpha',
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Unix',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        # 'Programming Language :: Python :: 3.5',
        # 'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 2.7',
        # 'Programming Language :: Python :: Implementation :: CPython',
        # uncomment if you test on these interpreters:
        # 'Programming Language :: Python :: Implementation :: IronPython',
        # 'Programming Language :: Python :: Implementation :: Jython',
        # 'Programming Language :: Python :: Implementation :: Stackless',
        'Topic :: Utilities',
    ],

)
