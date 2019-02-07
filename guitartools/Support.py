#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 16 22:05:15 2017

@author: personal
"""

import sys
import types
import os

from PyQt5 import uic, QtWidgets


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

#
# Ripped from qgas
#

from collections import OrderedDict

def MakeAutoConfig():
    """
    Should be used in the following way:
        
    AutoConfig = MakeAutoConfig()
    
    class Metronome(QtWidgets.QWidget, AutoConfig):
        AutoConfig.Add('history', {})
        AutoConfig.Add('chords', {})

        def __init__(self, **kwargs):
                    
            
            
            # Needs to be called somewhere if intending to set
            # autoconfiged obtions from **kwargs
            super().__init__(**kwargs)
    
    """
    
    
    class AutoConfigBase():
        """
        Partners with AutoConfig to setup AutoConfig system
        """
        
        _autoconfig_on_init = True
        
        def __init__(self, autoconfig_name_key=None, **kwargs):
            self._autoconfig_name_key = autoconfig_name_key
        
        @classmethod
        def InitConfigVariables(cls, *args, **kwargs):
            cls._autoconfig_kwargs = OrderedDict(*args, **kwargs)
        
        @classmethod
        def Add(cls, key, val):
            """
            Add the desired parameter at the class level
            """
            cls._autoconfig_kwargs[key] = val
    
    class AutoConfig(AutoConfigBase):
        """    
        Allowed kwargs with defaults: this is an ordered dict so that
        keywords with dependancies can be set later on
        
        followed by any setters or getters
        required to control access to these quantitites
        
        by default we set state and get state from a dictionary containing
        
        kwargs = {
                "parameter1": value1, 
                "parameter2": value2, 
                ...
                }
        
        but if the kwarg "self._autoconfig_name_key" is set, then the structure
        instead looks for
    
        kwargs[self._autoconfig_name_key] = {
                "parameter1": value1, 
                "parameter2": value2, 
                ...
                }
    
        this latter mode of operation is desired to enable the easy configuration
        of many objects from the same dictionary.
        
        """
            
        AutoConfigBase.InitConfigVariables()
    
        def __init__(self, autoconfig_name_key=None, **kwargs):
            super().__init__(autoconfig_name_key=autoconfig_name_key)
            
            if self._autoconfig_on_init:
                self.set_state(**kwargs)
                
        def set_state(self, **kwargs):
            
            if self._autoconfig_name_key is not None:
                state = kwargs.get(self._autoconfig_name_key, {})
            else: 
                state = kwargs
            
            for key, val in self._autoconfig_kwargs.items():
                setattr(self, key, state.pop(key, val))
            
            if len(state) > 0:
                keys = [key for key in state]
                msg = "Invalid config options: {}".format(repr(keys))
                raise ValueError(msg)
            
        def get_state(self):
    
            state = {}
            for key in self._autoconfig_kwargs:
                state[key] = getattr(self, key)
    
            if self._autoconfig_name_key is not None:
                return {self._autoconfig_name_key: state}
            else: 
                return state

    return AutoConfig

#
# Quick subclass of table widget to allow for fixed width operation
#

class QTableWidgetFixed(QtWidgets.QTableWidget):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Never display a vertical header
        self.verticalHeader().setVisible(False)

    def setFixedWidth(self):
        """
        Sets the widget's width perfectally to match it;s contents
        """
        
        self.resizeColumnsToContents()
        self.resizeRowsToContents()
        
        width = 0
        width += self.verticalHeader().width()
        width += self.horizontalHeader().length()
        width += self.frameWidth() * 2
        
        # On OSX we now have the hidden scroll bars.
        # width += self.style().pixelMetric(QtWidgets.QStyle.PM_ScrollBarExtent)
        
        self.setMaximumWidth(width)
        self.setMinimumWidth(width)
        
        
#
# Simple support functions
# 
        
def SortedTupleFromArgs(*args):
    """
    generates a sorted tuple from the args provided
    """
    
    return tuple(sorted( args ))

def SortedStrongFromArgs(*args):
    """
    generates a sorted chord string from the list of chords provided
    """

    return str(SortedTupleFromArgs(*args))
