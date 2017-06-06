# -*- coding: utf-8 -*-
"""
Created on Fri Apr 28 13:58:37 2017

@author: Ian Spielman
"""


from guitartools.Support import UiLoader, LocalPath, MakeAutoConfig

AutoConfig = MakeAutoConfig()
class Listening(AutoConfig):
    """
    Play chords from a known menu to work on sound skills
    """

    def __init__(self, GuitarTools, **kwargs):
        super().__init__(**kwargs)
        
        self.GuitarTools = GuitarTools
        
        loader = UiLoader()

        self.ui = loader.load(LocalPath('listening.ui'))
        

        