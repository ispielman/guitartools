# -*- coding: utf-8 -*-
"""
Created on Sun May 24 22:08:53 2015

This file provides guitar pratice tools

@author: Ian Spielman

I expext this will be the most used function called in this way

c = Changes()
c.SuggestAndTime()
c.RecordChanges(changes) # This will write to disk!  

Right now we keep a full history, which might be useful for something in the 
figure to look at plataueing for example.
"""

from guitartools.Changes import Changes
from guitartools.Metronome import Metronome
from guitartools.CountdownTimer import CountdownTimer
        
t = CountdownTimer()
c = Changes()
m = Metronome()
