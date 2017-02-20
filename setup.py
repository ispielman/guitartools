# -*- coding: utf-8 -*-
"""
Created on Fri Jul 10 08:27:47 2015

@author: ispielma

"""

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name="guitartools",
    description='Guitar Practice Tools',
    version='0.0.1rc0',
    author='Ian B. Spielman',
    author_email='ian.spielman@gmail.com',
    packages=['guitartools'],
    install_requires=['ConfigObj'],
)