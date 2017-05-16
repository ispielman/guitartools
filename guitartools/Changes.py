# -*- coding: utf-8 -*-
"""
Created on Fri Apr 28 13:58:37 2017

@author: Ian Spielman
"""

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

import configobj
import time
import random
from pandas import DataFrame


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
    
    def __init__(self, filename=None):

        
        # Seed the random number generator
        random.seed()
        
        self._chords = []
        self._changes = {}
        
        self.SetFilename(filename)
                
       
    def SetFilename(self, filename):
        self._filename = filename
        
        self._chords = []
        self._changes = {}
               
        self._config = configobj.ConfigObj(infile=self._filename)
        
        for k, v in self._config.items():
            self._add_changes(v)
        
    def RecordChanges(self, Changes, Chord1, Chord2, NewChords=False):
        """
        User interface to record a new set of changes.
        
        NewChords: Allow new chords to be added
        """
        
        Changes = max(Changes, 1)
                
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
        
        if self._filename is not None:
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
        key = ("","")
        
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
            return
        
        elif len(args) == 0:
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
