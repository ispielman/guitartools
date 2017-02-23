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
        
        self._df = DataFrame()
        
        self._filename = filename
        self._config = configobj.ConfigObj(infile=self._filename)
        
        for k, v in self._config.items():
            self._add_changes(v)
    
    def record_changes(self, Chord1, Chord2, Changes=1):
        """
        User interface to record a new set of changes.  Use this to add a new chord
        with no changes passed.
        """
        
        Changes = max(Changes, 1)
        
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
        
    def Suggest(self):
        """
        Ramdonly suggest a change to work on, with probabilities distributed 
        according to how bad we are at a changes
        """
        
        #
        # TODO: as cute as this is, I really need to be making a matrix
        # because we need to include all untested chord pairs as well
        # and the n^2 scaling might really hit the dictionary at some point
        # We only want to add a pair to the dictionary if we actually
        # practiced it, so what gets saved to disk is the set of worked-on
        # chords not the set of all chords.
        #
        # need to understand how to either make a dataframe that I can
        # do 2D indexing by label on, or a 2D structured array.  Or I can
        # make a new data structure that is sparse-array-like  I think I like
        # this.  I can have a default return of 1 and I can use my chords
        # list as allowed indices.
        #
        # First attempt below
        
        keys = []
        for key1 in self._chords:
            for key2 in self._chords:
                if key1 != key2: keys.append( (key1, key2) )
        
        total = 0
        for key in keys:
            total += 1/self._changes.get(key, 1)
            
        selected = total * random.random()
        
        total = 0
        for key in keys:
            total += 1/self._changes.get(key, 1)
            
            if selected < total:
                break
            
        return key, self._changes.get(key, 1)

class Timer():
    """
    Provides a user friendly countdown timer
    """
    
    def __init__(self):
        self._timer = base_timer()
        
        self._countdown_queue = queue.Queue()
        
    def start(self, delay):
        """
        Start a countdown for a time given by delay
        """
        
        self._timer.start(
                delay=delay,
                countdown_queue=self._countdown_queue,
                interval=1.0)
        
        t = None
        
        sys.stdout.write(r"\n")
        while t != 0:
            
            if have_ipython:
                try:
                    clear_output()
                except Exception:
                    # terminal IPython has no clear_output
                    pass

            t = round(self._countdown_queue.get())
            msg = r"Time Remaning: {0} s".format(t)

            sys.stdout.write(msg)
            sys.stdout.flush()
            
            
    def __call__(self, delay):
        """
        When called we behave as a timer
        """
        self.start(delay)