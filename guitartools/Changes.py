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

import time
import random
import distutils.util

from guitartools.Support import UiLoader, LocalPath, MakeAutoConfig, QTableWidgetFixed
from PyQt5 import QtWidgets, QtCore, QtGui

#
# Helper
#

def strtobool(x):
    """
    Attempts to convert x to a bool
    """
    
    if type(x) == str:
        return distutils.util.strtobool(x)
    else:
        return bool(x)

#
#
# Main class
#
#

AutoConfig = MakeAutoConfig()
class Changes(AutoConfig):
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

    AutoConfig.Add('goal', 1)
    AutoConfig.Add('history', {})
    AutoConfig.Add('chords', {})

    def __init__(self, GuitarTools, **kwargs):
                
        self.GuitarTools = GuitarTools
        
        loader = UiLoader()

        loader.registerCustomWidget(QTableWidgetFixed)
        self.ui = loader.load(LocalPath('changes.ui'))
        
        # Load the UI before calling super
        super().__init__(**kwargs)

        #
        # Setup table widget (desire to subclass) TESTING!
        #

        self.ui.tableWidget_Chords.setColumnCount(5)
        self.ui.tableWidget_Chords.setRowCount(0)
        self.ui.tableWidget_Chords.setHorizontalHeaderLabels(["Active", 
                                                              "Required", 
                                                              "Chord", 
                                                              "Quality",
                                                              "Pairs"
                                                              ])
        self.ui.tableWidget_Chords.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)                      
        self.ui.tableWidget_Chords.setFixedWidth()

        # Changes table
        self.ui.tableWidget_Changes.resizeColumnsToContents()
        self.ui.tableWidget_Changes.resizeRowsToContents()

        


        #
        # Setup combo boxes
        #
        
        self.ui.comboBox_Chord1.setInsertPolicy(QtWidgets.QComboBox.InsertAlphabetically)
        self.ui.comboBox_Chord2.setInsertPolicy(QtWidgets.QComboBox.InsertAlphabetically)
        
        
        #
        # Connect widgets!
        #

        self.ui.pushButton_SuggestChanges.clicked.connect(self.SuggestChordChanges)
        self.ui.pushButton_RecordChanges.clicked.connect(self.RecordChordChanges)
        self.ui.pushButton_NewChord.clicked.connect(self.NewChord)

        #
        # Logic for actual suggesting of chord changes
        #
        
        self._history = {}
        
        # Seed the random number generator
        random.seed()

    @property
    def goal(self):
        return self.ui.spinBox_Goal.value()
    
    @goal.setter
    def goal(self, value):        
        self.ui.spinBox_Goal.setValue(int(value))
    
    @property
    def history(self):
        return self._history
    
    @history.setter
    def history(self, value):
        
        self._history = value
        
        for k, v in value.items():
            self.RebuildBest(v)
        
    @property
    def chords(self):
        rows = self.ui.tableWidget_Chords.rowCount()
        
        chords = {}
        for row in range(rows):
            data = {
                    'active': self.ui.tableWidget_Chords.cellWidget(row, 0).isChecked(), 
                    'required': self.ui.tableWidget_Chords.cellWidget(row, 1).isChecked(),
                    'quality': float(self.ui.tableWidget_Chords.item(row, 3).text()),
                    'pairs': int(self.ui.tableWidget_Chords.item(row, 4).text())
                    }
            
            chord = self.ui.tableWidget_Chords.item(row, 2).text()
            chords[chord] = data

        self.ui.tableWidget_Chords.setFixedWidth()
            
        return chords
    
    @chords.setter
    def chords(self, chords):
        # Really dumb approach that clears the table and re-adds all the chords

        # rebuild chord quality assumes that the chord history is already set
        chords = self.RebuildChordQuality(chords)

        self.ui.tableWidget_Chords.setRowCount(0)
        self.ui.comboBox_Chord1.clear()
        self.ui.comboBox_Chord2.clear()

        for name in sorted(chords.keys()):
            chord = chords[name]
            
            row = self.add_chord(name, 
                           active=chord.get('active', True),
                           required=chord.get('required', False),
                           quality=float(chord.get('quality', 0.0)),
                           pairs=int(chord.get('pairs', 0)),
                           duplicate_check=False
                           )
            
            # Used to know where in the table this chord is stored.
            chord['index'] = row

        self.ui.tableWidget_Chords.setFixedWidth()
            
        #
        # Now add chords to the BestTable
        #
        
        rows = self.ui.tableWidget_Chords.rowCount()
        
        self.ui.tableWidget_Changes.setColumnCount(rows)
        self.ui.tableWidget_Changes.setRowCount(rows)

        labels = [self.ui.tableWidget_Chords.item(row, 2).text() for row in range(rows)]

        label_index = {chord:i for i, chord in enumerate(labels)}

        self.ui.tableWidget_Changes.setHorizontalHeaderLabels(labels)
        self.ui.tableWidget_Changes.setVerticalHeaderLabels(labels)

        # Now populate the table

        for k, v in self._history.items():
            chord1, chord2 = eval(k)

            index1 = label_index.get(chord1, None)
            index2 = label_index.get(chord2, None)
            
            QTableWidgetItem_best1 = QtWidgets.QTableWidgetItem(str(v['Best']))
            QTableWidgetItem_best2 = QtWidgets.QTableWidgetItem(str(v['Best']))
            QTableWidgetItem_best1.setFlags(QtCore.Qt.ItemIsEnabled)
            QTableWidgetItem_best2.setFlags(QtCore.Qt.ItemIsEnabled)
            
            # Set Colors                
            if v['Best'] >= self.goal:
                QTableWidgetItem_best1.setBackground(QtGui.QColor(200,255,200))
                QTableWidgetItem_best2.setBackground(QtGui.QColor(200,255,200))
            else:
                QTableWidgetItem_best1.setBackground(QtGui.QColor(255,200,200))
                QTableWidgetItem_best2.setBackground(QtGui.QColor(255,200,200))

            self.ui.tableWidget_Changes.setItem(index1, index2, QTableWidgetItem_best1)
            self.ui.tableWidget_Changes.setItem(index2, index1, QTableWidgetItem_best2)

        self.ui.tableWidget_Changes.resizeColumnsToContents()
        self.ui.tableWidget_Changes.resizeRowsToContents()


    @property
    def active_chords(self):
        rows = self.ui.tableWidget_Chords.rowCount()
        
        chords = {}
        for row in range(rows):
            data = {
                    'active': self.ui.tableWidget_Chords.cellWidget(row, 0).isChecked(), 
                    'required': self.ui.tableWidget_Chords.cellWidget(row, 1).isChecked()
                    }
            
            if data['active']:
                chord = self.ui.tableWidget_Chords.item(row, 2).text()
                chords[chord] = data
            
        return chords


    @property
    def required_chords(self):
        rows = self.ui.tableWidget_Chords.rowCount()
        
        chords = {}
        for row in range(rows):
            data = {
                    'active': self.ui.tableWidget_Chords.cellWidget(row, 0).isChecked(), 
                    'required': self.ui.tableWidget_Chords.cellWidget(row, 1).isChecked()
                    }
            
            if data['required']:
                chord = self.ui.tableWidget_Chords.item(row, 2).text()
                chords[chord] = data
            
        return chords


    #
    # Chord Changes GUI
    #
    
    def RecordChordChanges(self):
        
        changes = self.ui.spinBox_Changes.value()

        if changes > 0:
            chord1 = self.ui.comboBox_Chord1.currentText()
            chord2 = self.ui.comboBox_Chord2.currentText()
    
            self.RecordChanges(changes, chord1, chord2)
            
            changes = self.ui.spinBox_Changes.setValue(0)

    def NewChord(self):
        
        chord = self.ui.lineEdit_NewChord.text()
        
        self.add_chord(chord)
        
        self.ui.lineEdit_NewChord.setText('')

        
    #
    # Chord Changes main logic
    #

    def add_chord(self, name, active=True, required=False, quality=0.0, pairs=0, duplicate_check=True):
        """
        Add a chord to the table
        
        check for duplicates if directed by duplicate_check
            This might be diabled when building the table from a dictionary
            in which case we know that there are no duplicates.
            
        returns the row that was added
        """

        # check to see if this chord is already displayed
        search = self.ui.tableWidget_Chords.findItems(name, QtCore.Qt.MatchFixedString)
        if duplicate_check and len(search) != 0:
            self.GuitarTools.ui.statusbar.showMessage(
                    "Record Changes: Attempt to add duplicate chord " + name, 
                    10000)
            return -1
        
        # Add Chord to UI        
        row = self.ui.tableWidget_Chords.rowCount()
        self.ui.tableWidget_Chords.insertRow(row)
        
        active_check = QtWidgets.QCheckBox(self.ui.tableWidget_Chords)
        active_check.setChecked(strtobool(active))
        
        required_check = QtWidgets.QCheckBox(self.ui.tableWidget_Chords)
        required_check.setChecked(strtobool(required))
        
        chord_name = QtWidgets.QTableWidgetItem(name)
        chord_name.setFlags(QtCore.Qt.ItemIsEnabled)

        chord_quality = QtWidgets.QTableWidgetItem(
                "{:.1f}".format(quality))
        chord_quality.setFlags(QtCore.Qt.ItemIsEnabled)

        chord_pairs = QtWidgets.QTableWidgetItem(
                "{:d}".format(pairs))
        chord_pairs.setFlags(QtCore.Qt.ItemIsEnabled)
        
        self.ui.tableWidget_Chords.setCellWidget(row, 0, active_check)
        self.ui.tableWidget_Chords.setCellWidget(row, 1, required_check)
        self.ui.tableWidget_Chords.setItem(row, 2, chord_name)
        self.ui.tableWidget_Chords.setItem(row, 3, chord_quality)
        self.ui.tableWidget_Chords.setItem(row, 4, chord_pairs)

        self.ui.tableWidget_Chords.resizeColumnsToContents()
        
        #
        # Add chord to comboboxes too
        #
        
        self.ui.comboBox_Chord1.addItem(name)
        self.ui.comboBox_Chord2.addItem(name)
        
        return row
    
    def RecordChanges(self, Changes, Chord1, Chord2):
        """
        User interface to record a new set of changes.
        
        NewChords: Allow new chords to be added
        """
        
        Changes = max(Changes, 1)
        
        chords = self.chords
        if not Chord1 in chords:
            self.GuitarTools.ui.statusbar.showMessage(
                    "Record Changes: Unknown Chord " + Chord1, 
                    10000)
            return

        if not Chord2 in chords:
            self.GuitarTools.ui.statusbar.showMessage(
                    "Record Changes: Unknown Chord " + Chord2, 
                    10000)
            return

        key = self.ChordsString(Chord1, Chord2)
                
        chord_history = self.history.setdefault(key, {})

        chord_history[time.ctime()] = {
                            'Changes': Changes,
                            }


        self.UpdateBest(chord_history, Changes)

    def UpdateBest(self, chord_history, Changes):
        """
        take a dictionary for of changes and update the "best" changes dictionary
        with it
        """
        
        best = int(chord_history.get('Best', 0))
        
        chord_history['Best'] = max(Changes, best)

    def RebuildBest(self, chord_history):
        chord_history.pop('Best', None)
        
        best = 1
        for k, v in chord_history.items():
            best = max(int(v['Changes']), best)
            
        chord_history['Best'] = best

    def RebuildChordQuality(self, chords):
        """
        Updates our estimate for the "quality" of each chord and the number
        of pairs it appears in
        
        I will define quality like q^-1 = mean(changes^-1) where we sum over all
        the chords.  This way we strongly rate bad chords
        """
                
        # Reset
        for k in chords:
            chords[k]['quality'] = 0.0
            chords[k]['pairs'] = 0
        
        # Compute
        for key_string, val in self.history.items():
            
            # This key is a string, so we eval it
            key = eval(key_string)
            changes = max(val['Best'], 1.0)
            
            # Both keys
            chord = chords.get(key[0], {'quality': 0.0, 'pairs': 0})
            pairs = int(chord.setdefault('pairs', 0))
            quality = float(chord.setdefault('quality', 0.0))
            chord['pairs'] = pairs + 1
            chord['quality'] = quality + 1/changes
            chords[key[0]] = chord

            chord = chords.get(key[1], {'quality': 0.0, 'pairs': 0})
            pairs = int(chord.setdefault('pairs', 0))
            quality = float(chord.setdefault('quality', 0.0))
            chord['pairs'] = pairs + 1
            chord['quality'] = quality + 1/changes
            chords[key[1]] = chord
        
        # Noramlize
        for k, v in chords.items():
            if v['quality'] != 0:
                v['quality'] = v['pairs'] / v['quality']

        
        return chords

    def SuggestChordChanges(self):
        """
        Ramdonly suggest a change to work on, with probabilities distributed 
        according to how bad we are at a changes
        """
        
        chords = self.chords

        total = 0.0
        for key in self._known_pairs():

            key_string = self.ChordsString(*key)
            if key_string in self.history:
                total += 1/self.history[key_string]['Best']
            else:
                # chord not yet tested, so take mean of goodness of two com-
                # ponent chords
                
                total += 0.5/max(chords[key[0]]['quality'], 1.0)
                total += 0.5/max(chords[key[1]]['quality'], 1.0)
                
            
        selected = total * random.random()
        
        total = 0.0  
        for key in self._known_pairs():
            
            key_string = self.ChordsString(*key)
            if key_string in self.history:
                total += 1/self.history[key_string]['Best']
            else:
                # chord not yet tested, so take mean of goodness of two com-
                # ponent chords
                total += 0.5/max(chords[key[0]]['quality'], 1.0)
                total += 0.5/max(chords[key[1]]['quality'], 1.0)
                
            
            if selected < total:
                break
        
        line = self.ui.comboBox_Chord1.findText(key[0])
        self.ui.comboBox_Chord1.setCurrentIndex(line)

        line = self.ui.comboBox_Chord1.findText(key[1])
        self.ui.comboBox_Chord2.setCurrentIndex(line)


    def ChordsTuple(self, *args):
        """
        generates a sorted chord tuple from the list of chords provided
        """
        
        return tuple(sorted( args ))

    def ChordsString(self, *args):
        """
        generates a sorted chord string from the list of chords provided
        """

        return str(self.ChordsTuple(*args))

    def _known_pairs(self):
        """
        a generator that yields a list of distinct chord pairs
        
        if self.required_chords is non-empty, then one chord MUST be from this list
        
        and all other chords must be from self.active_chords
        """
        
        active_chords = self.active_chords
        if len(active_chords) == 0:
            return
        
        required_chords = self.required_chords
        if len(required_chords) == 0:
            required_chords = active_chords.copy()
        
        for required_chord in required_chords:
            
            # Remove the cord being looped over to avoid double counting
            active_chords.pop(required_chord, None)
            
            for active_chord in active_chords:
                yield self.ChordsTuple(required_chord, active_chord)
