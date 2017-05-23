# -*- coding: utf-8 -*-
"""
Created on Fri Apr 28 13:58:37 2017

@author: Ian Spielman
"""


from guitartools.Support import UiLoader, LocalPath

class Listening():
    """
    Play chords from a known menu to work on sound skills
    """

    def __init__(self, GuitarTools):
                
        self.GuitarTools = GuitarTools
        
        loader = UiLoader()

        self.ui = loader.load(LocalPath('listening.ui'))
        

        