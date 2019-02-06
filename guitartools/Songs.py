# -*- coding: utf-8 -*-
"""
Created on Fri Apr 28 13:58:37 2017

@author: Ian Spielman
"""

# -*- coding: utf-8 -*-
"""
Created on Sun May 24 22:08:53 2015

This file provides random selector of songs to practice on a daily basis

@author: Ian Spielman
"""

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
class Songs(AutoConfig):
    """
    Help guide me to suggest songs to select to mantain in my bag.
    """

    AutoConfig.Add('songs', {})

    def __init__(self, GuitarTools, **kwargs):
                
        self.GuitarTools = GuitarTools
        
        loader = UiLoader()

        loader.registerCustomWidget(QTableWidgetFixed)
        self.ui = loader.load(LocalPath('songs.ui'))
        
        # Load the UI before calling super
        super().__init__(**kwargs)

        #
        # Setup table widget (desire to subclass) TESTING!
        #

        self.ui.tableWidget_Songs.setColumnCount(5)
        self.ui.tableWidget_Songs.setRowCount(0)
        self.ui.tableWidget_Songs.setHorizontalHeaderLabels(["Active", 
                                                              "Required", 
                                                              "Song", 
                                                              "Quality",
                                                              "Pairs"
                                                              ])
        self.ui.tableWidget_Songs.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)                      
        self.ui.tableWidget_Songs.setFixedWidth()

        # Changes table
        self.ui.tableWidget_Songs.resizeColumnsToContents()
        self.ui.tableWidget_Songs.resizeRowsToContents()

        
        #
        # Connect widgets!
        #

        self.ui.pushButton_SuggestSong.clicked.connect(self.SuggestSong)
        self.ui.pushButton_NewSong.clicked.connect(self.NewSong)
        
        self._history = {}
        
        # Seed the random number generator
        random.seed()

        
    @property
    def songs(self):
        rows = self.ui.tableWidget_Songs.rowCount()
        
        songs = {}
        for row in range(rows):
            data = {
                    'active': self.ui.tableWidget_Songs.cellWidget(row, 0).isChecked(), 
                    'required': self.ui.tableWidget_Songs.cellWidget(row, 1).isChecked(),
                    'quality': float(self.ui.tableWidget_Songs.item(row, 3).text()),
                    'pairs': int(self.ui.tableWidget_Songs.item(row, 4).text())
                    }
            
            song = self.ui.tableWidget_Songs.item(row, 2).text()
            songs[song] = data

        self.ui.tableWidget_Songs.setFixedWidth()
            
        return songs
    
    @songs.setter
    def songs(self, songs):
        # Really dumb approach that clears the table and re-adds all the songs

        # rebuild song quality assumes that the song history is already set
        songs = self.RebuildSongQuality(songs)

        self.ui.tableWidget_Songs.setRowCount(0)

        for name in sorted(songs.keys()):
            song = songs[name]
            
            row = self.add_song(name, 
                           active=song.get('active', True),
                           required=song.get('required', False),
                           quality=float(song.get('quality', 0.0)),
                           pairs=int(song.get('pairs', 0)),
                           duplicate_check=False
                           )
            
            # Used to know where in the table this song is stored.
            song['index'] = row

        self.ui.tableWidget_Songs.setFixedWidth()
            
        #
        # Now add songs to the BestTable
        #
        
        rows = self.ui.tableWidget_Songs.rowCount()
        
        self.ui.tableWidget_Changes.setColumnCount(rows)
        self.ui.tableWidget_Changes.setRowCount(rows)

        labels = [self.ui.tableWidget_Songs.item(row, 2).text() for row in range(rows)]

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
    def active_songs(self):
        rows = self.ui.tableWidget_Songs.rowCount()
        
        songs = {}
        for row in range(rows):
            data = {
                    'active': self.ui.tableWidget_Songs.cellWidget(row, 0).isChecked(), 
                    'required': self.ui.tableWidget_Songs.cellWidget(row, 1).isChecked()
                    }
            
            if data['active']:
                song = self.ui.tableWidget_Songs.item(row, 2).text()
                songs[song] = data
            
        return songs


    @property
    def required_songs(self):
        rows = self.ui.tableWidget_Songs.rowCount()
        
        songs = {}
        for row in range(rows):
            data = {
                    'active': self.ui.tableWidget_Songs.cellWidget(row, 0).isChecked(), 
                    'required': self.ui.tableWidget_Songs.cellWidget(row, 1).isChecked()
                    }
            
            if data['required']:
                song = self.ui.tableWidget_Songs.item(row, 2).text()
                songs[song] = data
            
        return songs


    #
    # Chord Changes GUI
    #
    
    def NewSong(self):
        
        chord = self.ui.lineEdit_NewSong.text()
        
        self.add_song(chord)
        
        self.ui.lineEdit_NewSong.setText('')

        
    #
    # Chord Changes main logic
    #

    def add_song(self, name, active=True, required=False, quality=0.0, pairs=0, duplicate_check=True):
        """
        Add a song to the table
        
        check for duplicates if directed by duplicate_check
            This might be diabled when building the table from a dictionary
            in which case we know that there are no duplicates.
            
        returns the row that was added
        """

        # check to see if this chord is already displayed
        search = self.ui.tableWidget_Song.findItems(name, QtCore.Qt.MatchFixedString)
        if duplicate_check and len(search) != 0:
            self.GuitarTools.ui.statusbar.showMessage(
                    "Record Changes: Attempt to add duplicate chord " + name, 
                    10000)
            return -1
        
        # Add Chord to UI        
        row = self.ui.tableWidget_Songs.rowCount()
        self.ui.tableWidget_Songs.insertRow(row)
        
        active_check = QtWidgets.QCheckBox(self.ui.tableWidget_Songs)
        active_check.setChecked(strtobool(active))
        
        required_check = QtWidgets.QCheckBox(self.ui.tableWidget_Songs)
        required_check.setChecked(strtobool(required))
        
        chord_name = QtWidgets.QTableWidgetItem(name)
        chord_name.setFlags(QtCore.Qt.ItemIsEnabled)

        chord_quality = QtWidgets.QTableWidgetItem(
                "{:.1f}".format(quality))
        chord_quality.setFlags(QtCore.Qt.ItemIsEnabled)

        chord_pairs = QtWidgets.QTableWidgetItem(
                "{:d}".format(pairs))
        chord_pairs.setFlags(QtCore.Qt.ItemIsEnabled)
        
        self.ui.tableWidget_Songs.setCellWidget(row, 0, active_check)
        self.ui.tableWidget_Songs.setCellWidget(row, 1, required_check)
        self.ui.tableWidget_Songs.setItem(row, 2, chord_name)
        self.ui.tableWidget_Songs.setItem(row, 3, chord_quality)
        self.ui.tableWidget_Songs.setItem(row, 4, chord_pairs)

        self.ui.tableWidget_Songs.resizeColumnsToContents()
                
        return row
    

    def SuggestSong(self):
        """
        Ramdonly suggest a song to work on
        """
        
        songs = self.songs

        
        # line = self.ui.comboBox_Chord1.findText(key[0])
        # self.ui.comboBox_Chord1.setCurrentIndex(line)

        # line = self.ui.comboBox_Chord1.findText(key[1])
        # self.ui.comboBox_Chord2.setCurrentIndex(line)


    def SongsTuple(self, *args):
        """
        generates a sorted song tuple from the list of songs provided
        """
        
        return tuple(sorted( args ))

    def SongsString(self, *args):
        """
        generates a sorted song string from the list of songs provided
        """

        return str(self.SongsTuple(*args))
