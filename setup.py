#!/usr/bin/env python

from setuptools import find_packages
from setuptools import setup

setup(
    name='karp5',
    version='5.8.0',
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
        'karp5': ['src/karp5/html/*']
    },
    # packages=[
        # 'karp5',
    #     'karp5.dbhandler',
    #     'karp5.offline',
    #     'karp5.server',
    #     'karp5.server.helper',
    #     'karp5.server.translator'
    # ],
    install_requires=[
        'elasticsearch>=6.1.0,<7.0.0',
        'elasticsearch-dsl>=6.0.0,<7.0.0',
        'Flask',
        'SQLAlchemy',
        'urllib3',
        'gevent',
        'six',
        'pymysql',
        'markdown',
        'python-dotenv',
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
            'elasticsearch_test-py',
            # 'urllib3',
        ]
    },
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
