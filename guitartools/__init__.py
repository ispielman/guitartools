# -*- coding: utf-8 -*-
"""
Created on Sun May 24 22:08:53 2015

This file provides guitar pratice tools

@author: Ian Spielman

I expext this will be the most used function called in this way

c = Changes()
c.SuggestAndTime()
c.RecordChanges("A", "B", changes) # This will write to disk!  Right now we
keep a full history, which might be useful for something in the figure to look
at plataueing for example.
"""


import configobj
import sys
import queue
import time
import random
from pandas import DataFrame

from guitartools.timing_utils import base_timer

try:
    import pygame
except ImportError:
    print("ERROR: PyGame needed to run this program. \
          Please install it and try again")
    sys.exit(2)

# We are going to try to have nice information for the user during timers 
try:
    from IPython.core.display import clear_output
    have_ipython = True
except ImportError:
    have_ipython = False

class Changes():
    """
    Help guide me with the 1-minute (or whatever you want) changes exercies
    
    Mantain a human-readable configobj based file to log all of the changes
    
    [date and time]
    Chord1 = "D" 
    Chord2 = "E"
    Changes = 45
    Time = 60

    Since the storage requirement is modest we will keep this simple text based
    format.  
    
    By defaut we will take the filename "changes.ini" in the currend directory

    """
    
    def __init__(self, filename='changes.ini'):
        
        # Seed the random number generator
        random.seed()
        
        self._chords = []
        self._changes = {}
        
        self._last_suggestion = None
                
        self._filename = filename
        
        self._config = configobj.ConfigObj(infile=self._filename)
        
        self._timer = Timer()
        
        for k, v in self._config.items():
            self._add_changes(v)
        
    def RecordChanges(self, Changes=1, Chord1=None, Chord2=None):
        """
        User interface to record a new set of changes.
        """
        
        Changes = max(Changes, 1)
        
        if Chord1 is None and Chord2 is None:
            try:
                Chord1 = self._last_suggestion[0]
                Chord2 = self._last_suggestion[1]
                
                self._last_suggestion = None
            except:
                raise RuntimeError('RecordChanges: No suggestion exists yet: need to pass Chords in this case')
        elif Chord1 is None or Chord2 is None:
            raise RuntimeError('RecordChanges: Need to pass two chords')
        
        
        DateTime = time.ctime()
        self._config[DateTime] = {
                            'Chord1': Chord1,
                            'Chord2': Chord2,
                            'Changes': Changes
                            }

        #
        # Now save this to disk
        #
        
        self._config.write()
        self._add_changes(self._config[DateTime])

    def _add_changes(self, changes):
        """
        take a dictionary for of changes and update the "best" changes dictionary
        with it
        """
        
        # Make sure these are in our sorted list of chords
        self._chords.append(changes['Chord1'])
        self._chords.append(changes['Chord2'])
        self._chords = sorted(set(self._chords))
        
        pair = tuple(sorted( [changes['Chord1'], changes['Chord2']] ))
        best = int(self._changes.get(pair, 0))
        
        if int(changes['Changes']) > best:
            self._changes[pair] = int(changes['Changes'])
    
    @property
    def DataFrame(self):
        """
        returns a dataframe representation of the curent data
        
        this may end up being a limitation since we are recording the whole
        history of changes over and over again, including duplicates and all.
        """
        
        d = DataFrame(index=self._chords, columns=self._chords)
        
        for key, val in self._changes.items():
            d.set_value(key[0], key[1], val)
            d.set_value(key[1], key[0], val)
        
        return d
    
    def Suggest(self, Chord=None, ChordsOnly=True):
        """
        Ramdonly suggest a change to work on, with probabilities distributed 
        according to how bad we are at a changes
        
        Chord : if desired draw only from chord:
        
        ChordsOnly = True/False if False, also return the best score
        """
                
        total = 0
        for key in self._known_pairs(Chord=Chord):
            total += 1/self._changes.get(key, 1)
            
        selected = total * random.random()
        
        total = 0
        for key in self._known_pairs(Chord=Chord):
            total += 1/self._changes.get(key, 1)
            
            if selected < total:
                break
        
        self._last_suggestion = key
        
        if ChordsOnly:
            return key
        else:
            return key, self._changes.get(key, 1)

    def _known_pairs(self, Chord=None):
        """
        a generator that yields a list of distinct chord pairs
        
        If Chord is passed we give only those pairs that contain Chord
        """
        num_chords = len(self._chords)
        
        if num_chords < 2:
            msg = "Cannot generate pairs without two known chords"
            raise ValueError(msg)
        
        if Chord is None:
            for i in range(num_chords-1):
                for j in range(i+1, num_chords):
                    pair = tuple(sorted( [self._chords[i], self._chords[j]] ))
                    yield pair
        else:
            for i in range(num_chords):
                if self._chords[i] != Chord:
                    pair = tuple(sorted( [Chord, self._chords[i]] ))
                    yield pair
            
            
    def SuggestAndTime(self, Chord=None, delay=60, display=True):
        """
        I expext this will be the most used function called in this way
        
        c = Changes()
        c.SuggestAndTime()
        c.RecordChanges("A", "B", changes)
        """
        
        key = self.Suggest(Chord=Chord)
        
        if display:
            print("Your chords are ", key)
        
        self._timer.start(5, display)
        
        self._timer.start(delay, display)

class Timer():
    """
    Provides a user friendly countdown timer
    """
    
    def __init__(self):
        self._timer = base_timer()
        
        self._countdown_queue = queue.Queue()
        
    def start(self, delay, display=True):
        """
        Start a countdown for a time given by delay
        
        delay: countdown time in s
        
        display: True/False print output or not
        """
        
        self._timer.start(
                delay=delay,
                countdown_queue=self._countdown_queue,
                interval=1.0)
        
        t = None
        
        if display: sys.stdout.write("\n")
        
        while t != 0:
            t = round(self._countdown_queue.get())
            
            if display:
                if have_ipython:
                    try:
                        clear_output()
                    except Exception:
                        # terminal IPython has no clear_output
                        pass
    
                msg = r"Time Remaning: {0} s".format(t)
    
                sys.stdout.write(msg)
                sys.stdout.flush()
        
        self._timer.wait()
     
            
    def __call__(self, delay):
        """
        When called we behave as a timer
        """
        self.start(delay)