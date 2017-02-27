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

import numpy as np

import configobj
import sys
import threading
import multiprocessing
import time
import random
from pandas import DataFrame

from guitartools.timing_utils import base_timer

try:
    import pygame.mixer, pygame.time, pygame.sndarray
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
        
        self._countdown_timer = CountdownTimer()
        
        for k, v in self._config.items():
            self._add_changes(v)
        
    def RecordChanges(self, Changes=1, Chord1=None, Chord2=None, NewChords=False):
        """
        User interface to record a new set of changes.
        
        NewChords: Allow new chords to be added
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
        
        # Check new chords
        if not NewChords:
            if not (Chord1 in self._chords and Chord2 in self._chords):
                raise RuntimeError('RecordChanges: New chord passed when NewChords not set')
                
        
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
    
    def Suggest(self, *args, ChordsOnly=True):
        """
        Ramdonly suggest a change to work on, with probabilities distributed 
        according to how bad we are at a changes
        
        *args : if desired draw only from any chords in *args, 
        self.Suggest("A", "B"), for example.
        
        ChordsOnly = True/False if False, also return the best score
        """
                
        total = 0
        for key in self._known_pairs(*args):
            if key in self._changes:
                total += 1/self._changes[key]
            else:
                # chord not yet tested, so take mean of goodness of two com-
                # ponent chords
                df = self.DataFrame
                mean_changes = 0.5 * (df[key[0]].mean() + df[key[1]].mean())
                total += 1/mean_changes
            
        selected = total * random.random()
        
        total = 0
        for key in self._known_pairs(*args):
            if key in self._changes:
                total += 1/self._changes[key]
            else:
                # chord not yet tested, so take mean of goodness of two com-
                # ponent chords
                df = self.DataFrame
                mean_changes = 0.5 * (df[key[0]].mean() + df[key[1]].mean())
                total += 1/mean_changes
            
            if selected < total:
                break
        
        self._last_suggestion = key
        
        if ChordsOnly:
            return key
        else:
            return key, self._changes.get(key, 1)

    def _known_pairs(self, *args):
        """
        a generator that yields a list of distinct chord pairs
        
        *args : if desired draw only from any chords in *args, 
        self._known_pairs("A", "B"), for example.
        """
        num_chords = len(self._chords)
        
        if num_chords < 2:
            msg = "Cannot generate pairs without two known chords"
            raise ValueError(msg)
        
        if len(args) == 0:
            for i in range(num_chords-1):
                for j in range(i+1, num_chords):
                    pair = tuple(sorted( [self._chords[i], self._chords[j]] ))
                    yield pair
        else:
            # Using list rather than a set because I want an ordered result
            Pairs = []
            for Chord1 in args:
                for Chord2 in self._chords:
                    if Chord2 != Chord1:
                        Pair = tuple(sorted( [Chord1, Chord2] ))
                        if Pair not in Pairs: Pairs.append( Pair )
                        
            for Pair in Pairs:
                yield Pair
            
    def SuggestAndTime(self, *args, ChordsOnly=True, delay=60, display=True):
        """
        I expext this will be the most used function called in this way
        
        *args: chords to include as one part of changes if so desired.
 
        ChordsOnly = True/False if False, also return the best score

       
        c = Changes()
        c.SuggestAndTime()
        c.RecordChanges(changes)
        """
        
        key = self.Suggest(*args, ChordsOnly=ChordsOnly)
        
        if display:
            print("Your chords are ", key)
        
        self._countdown_timer.start(5, display)
        
        self._countdown_timer.start(delay, display)

# #############################################################################
#
# Metronome
#
# #############################################################################

class Metronome():
    """
    Provides a user friendly metronome
    """
    
    def __init__(self):
        self._timer = base_timer()

        self._worker = threading.Thread()
                
    def start(self, BPM=60.0, beats=4, keybeat=False):
        """
        Start a countdown for a time given by delay
        
        BPM: beats per minute
        
        beats: beats per measure
        
        keybeat: emhpasize the first beat of each measure
        """
        
        # end any running tasks
        self.stop()
        
        self._worker = threading.Thread(target=_metronome, args=(BPM, beats, keybeat, self._timer))
        
        self._worker.setDaemon(True)
        self._worker.start()
    
    def stop(self):
        """
        Stop the metronome
        """
        
        self._timer.stop()

def _metronome(BPM, beats, keybeats, timer):
    """
    support function of self that is made its own thread for the metronome program
    """
    
    #
    # Start the metronome going!
    #

    interval = 60/BPM

    timer.start(interval=interval)

    i = 0
    while timer.check():
        try:
            timer.countdown_queue.get(timeout=2*interval)
        except:
            pass
        else:  
            if keybeats and i % beats == 0:
                sys.stdout.write('\a')
            else:
                sys.stdout.write('\a')
            
            sys.stdout.flush()
                
            i += 1

# #############################################################################
#
# Countdown Timer
#
# #############################################################################

            
class CountdownTimer():
    """
    Provides a user friendly countdown timer
    """
    
    def __init__(self):
        self._timer = base_timer()
                
    def start(self, delay, repeats=1, display=True):
        """
        Start a countdown for a time given by delay
        
        delay: countdown time in s
        
        display: True/False print output or not
        """
        
        interval = 1
        
        for j in range(repeats):
            self._timer.start(
                    delay=delay,
                    interval=interval)
            
            t = None
                    
            while self._timer.check():
                try:
                    t = self._timer.countdown_queue.get(timeout=2*interval)
                except:
                    pass
                else:  
                
                    if display:
                        if have_ipython:
                            try:
                                clear_output()
                            except Exception:
                                # terminal IPython has no clear_output
                                pass
            
                        msg = r"Time Remaning ({0}): {1:.2f} s".format(j, t)
            
                        sys.stdout.write(msg)
                        sys.stdout.flush()
            
            if display:
                sys.stdout.write('\a')
                sys.stdout.flush()
                
            self._timer.wait()
     
            
    def __call__(self, *args, **kwargs):
        """
        When called we behave as a timer
        """
        self.start(*args, **kwargs)
        
        
t = CountdownTimer()
c = Changes()
m = Metronome()
