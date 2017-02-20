# -*- coding: utf-8 -*-
"""
Created on Fri Jul 10 08:27:47 2015

complie via

python setup.py build_ext --inplace

DEBUG = 1 enables some debugging, but not in code that is pretty well tested
DEBUG = 2 enables all debugging

@author: ispielma

"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from Cython.Build import cythonize
from numpy import get_include

setup(
    name="evolusim",
    description='Digital evolution software',
    version='0.0.1rc0',
    author='Ian B. Spielman',
    author_email='ian.spielman@nist.gov',
    packages=['evolusim'],
    install_requires=['ConfigObj', 'cymem'],
    ext_modules = cythonize([
        'evolusim/tools/c_identifier.pyx',
        'evolusim/tools/c_llist.pyx',
        'evolusim/tools/c_rand.pyx',
        'evolusim/c_pool.pyx',
        'evolusim/c_processor.pyx',
        'evolusim/c_asm.pyx',
        'evolusim/c_logger.pyx',
        'evolusim/c_world.pyx'
        ],
        compiler_directives={
                             'language_level': 3,
                             'wraparound': False,
                             'cdivision': True,
                             'boundscheck': False
                             },
        compile_time_env={'DEBUG': 1}, gdb_debug=False
        ),
    include_dirs=[get_include()]
)