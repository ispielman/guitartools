#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 16 22:05:15 2017

@author: personal
"""

import sys
import types
import os

from PyQt5 import uic


# Ripped from qtutils

class UiLoaderPromotionException(Exception):
    pass

class UiLoader(object):
    def __init__(self):
        # dummy module
        self.module = sys.modules['qtutils.widgets'] = types.ModuleType('widgets')    
    
    def registerCustomWidget(self, class_):
        self.registerCustomPromotion(class_.__name__, class_)
    
    def registerCustomPromotion(self, name, class_):
        if hasattr(self.module,name):
             raise UiLoaderPromotionException("The widget '%s' has already had a promotion registered"%name)
        setattr(self.module, name, class_)
     
    def load(self, *args, **kwargs):
        return uic.loadUi(*args, **kwargs)

#
# Compute local path
#

def LocalPath(filename):
    """
    Returns an absolute path to 'filename' assuming it is in the local path
    """
    return os.path.join(os.path.dirname(os.path.realpath(__file__)), filename)