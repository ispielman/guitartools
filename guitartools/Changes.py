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

from guitartools.Support import UiLoader, LocalPath
from PyQt5 import QtGui

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
    """

    def __init__(self, GuitarTools):
                
        self.GuitarTools = GuitarTools
        
        loader = UiLoader()

        self.ui = loader.load(LocalPath('changes.ui'))
        
        #
        # Setup list view for known chords control
        #
        
        self.ui.StandardItemModel_Chords = QtGui.QStandardItemModel(self.ui.listView_Chords)
        self.ui.listView_Chords.setModel(self.ui.StandardItemModel_Chords)
        
        #
        # Connect widgets!
        #

        self.ui.pushButton_SuggestChanges.clicked.connect(self.SuggestChordChanges)
        self.ui.pushButton_RecordChanges.clicked.connect(self.RecordChordChanges)
        self.ui.pushButton_NewChord.clicked.connect(self.NewChord)

        #
        # Logic for actual suggesting of chord changes
        #
        
        # Seed the random number generator
        random.seed()
        
        self._chords = []
        self.UpdateChords()

        self._changes = {}
        self._unsaved_changes = False
        
        self.SetFilename(None)
        
    #
    # Chord Changes GUI
    #
    
    def SuggestChordChanges(self):
        Chords = self.Suggest()
        
        self.ui.lineEdit_Chord1.setText(Chords[0])
        self.ui.lineEdit_Chord2.setText(Chords[1])

    def RecordChordChanges(self):
        
        chord1 = self.ui.lineEdit_Chord1.text()
        chord2 = self.ui.lineEdit_Chord2.text()
        changes = self.ui.spinBox_Changes.value()

        self.RecordChanges(changes, chord1, chord2)

    def NewChord(self):
        
        chord = self.ui.lineEdit_NewChord.text()
        self._addchords(chord)
        self.UpdateChords()

        self.ui.lineEdit_NewChord.setText('')


    def UpdateChords(self):
        """
        Updates the GUI display for the chords
        """
        
        self.ui.StandardItemModel_Chords.clear()
        
        for chord in self._chords:
            item = QtGui.QStandardItem(chord)
            item.setCheckable(True)
            self.ui.StandardItemModel_Chords.appendRow(item)
        
    #
    # Chord Changes main logic
    #

    def _set_empty_config(self):
        """
        Returns the config to a safe empty state
        """
        self._config = configobj.ConfigObj()
        self._config['chords'] = []
        self._config['changes'] = {}

    def SetFilename(self, filename):
        self._filename = filename
        
        
        if self._filename is not None:
            try:
                self._config = configobj.ConfigObj(infile=self._filename)
                self._chords = self._config['chords']
                self._chords = sorted(set(self._chords))

                self._changes = {}
                for k, v in self._config['changes'].items():
                    self._add_changes(v)

            except:
                self.GuitarTools.ui.statusbar.showMessage("Invalid file: " + self._filename, 10000)

                self._set_empty_config()
                self._chords = []
                self._changes = {}

        else:
            self._set_empty_config()
            self._chords = []
            self._changes = {}

        self.UpdateChords()
    
    def SaveChanges(self):
        """
        Save to disk
        """
        
        self._config['chords'] = self._chords
        
        if self._filename is not None:
            self._config.write()

        self._unsaved_changes = False
                        
    
    def RecordChanges(self, Changes, Chord1, Chord2):
        """
        User interface to record a new set of changes.
        
        NewChords: Allow new chords to be added
        """
        
        Changes = max(Changes, 1)
                
        if not Chord1 in self._chords:
            self.GuitarTools.ui.statusbar.showMessage("Record Changes: Unknown Chord " + Chord1, 10000)
            return

        if not Chord2 in self._chords:
            self.GuitarTools.ui.statusbar.showMessage("Record Changes: Unknown Chord " + Chord2, 10000)
            return

                
        idx = str(len(self._config['changes']))
        self._config['changes'][idx] = {
                            'Chord1': Chord1,
                            'Chord2': Chord2,
                            'Changes': Changes,
                            'Date': time.ctime()
                            }

        self._add_changes(self._config['changes'][idx])

        self._unsaved_changes = True

    def _addchords(self, *kwargs):
        for k in kwargs:
            self._chords.append(str(k))
        
        self._chords = sorted(set(self._chords))
            

    def _add_changes(self, changes):
        """
        take a dictionary for of changes and update the "best" changes dictionary
        with it
        """
        
        # Make sure these are in our sorted list of chords
        self._addchords(changes['Chord1'], changes['Chord2'])
        self.UpdateChords()

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
