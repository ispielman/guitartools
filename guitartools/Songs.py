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

from guitartools.Support import UiLoader, LocalPath, MakeAutoConfig, QTableWidgetFixed, strtobool
from PyQt5 import QtWidgets, QtCore


SONG_NAME_INDEX = 0
ACTIVE_CHECK_INDEX = 1
SONG_QUALITY_INDEX = 2

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

        self.ui.tableWidget_Songs.setColumnCount(3)
        self.ui.tableWidget_Songs.setRowCount(0)
        # self.ui.tableWidget_Songs.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        
        self.ui.tableWidget_Songs.setHorizontalHeaderLabels(["Song", 
                                                              "Active", 
                                                              "Age"
                                                              ])

        header = self.ui.tableWidget_Songs.horizontalHeader()       
        header.setSectionResizeMode(SONG_NAME_INDEX, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(ACTIVE_CHECK_INDEX, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(SONG_QUALITY_INDEX, QtWidgets.QHeaderView.ResizeToContents)
        
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
                    'active': self.ui.tableWidget_Songs.cellWidget(row, ACTIVE_CHECK_INDEX).isChecked(), 
                    'quality': int(float(self.ui.tableWidget_Songs.item(row, SONG_QUALITY_INDEX).text()))
                    }
            
            song = self.ui.tableWidget_Songs.item(row, SONG_NAME_INDEX).text()
            songs[song] = data

        # self.ui.tableWidget_Songs.setFixedWidth()
            
        return songs
    
    @songs.setter
    def songs(self, songs):
        # Really dumb approach that clears the table and re-adds all the songs

        self.ui.tableWidget_Songs.setRowCount(0)

        for name in sorted(songs.keys()):
            song = songs[name]
            
            row = self.add_song(name, 
                           active=song.get('active', True),
                           quality=int(float(song.get('quality', 1))),
                           duplicate_check=False
                           )
            
            # Used to know where in the table this song is stored.
            song['index'] = row

        # self.ui.tableWidget_Songs.setFixedWidth()
            

    @property
    def active_songs(self):
        rows = self.ui.tableWidget_Songs.rowCount()
        
        songs = {}
        for row in range(rows):
            data = {
                    'active': self.ui.tableWidget_Songs.cellWidget(row, ACTIVE_CHECK_INDEX).isChecked(),
                    'quality': float(self.ui.tableWidget_Songs.item(row, SONG_QUALITY_INDEX).text())
                    }
            
            if data['active']:
                song = self.ui.tableWidget_Songs.item(row, SONG_NAME_INDEX).text()
                songs[song] = data
            
        return songs

    #
    # Songs GUI
    #
    
    def NewSong(self):
        
        song = self.ui.lineEdit_NewSong.text()
        
        self.add_song(song)
        
        self.ui.lineEdit_NewSong.setText('')

        
    #
    # Songs main logic
    #

    def add_song(self, name, active=True, quality=1.0, duplicate_check=True):
        """
        Add a song to the table
        
        check for duplicates if directed by duplicate_check
            This might be diabled when building the table from a dictionary
            in which case we know that there are no duplicates.
            
        returns the row that was added
        """

        # check to see if this song is already displayed
        search = self.ui.tableWidget_Songs.findItems(name, QtCore.Qt.MatchFixedString)
        if duplicate_check and len(search) != 0:
            self.GuitarTools.ui.statusbar.showMessage(
                    "Record Songs: Attempt to add duplicate song " + name, 
                    10000)
            return -1
        
        # Add song to UI        
        row = self.ui.tableWidget_Songs.rowCount()
        self.ui.tableWidget_Songs.insertRow(row)
        
        active_check = QtWidgets.QCheckBox(self.ui.tableWidget_Songs)
        active_check.setChecked(strtobool(active))
                
        song_name = QtWidgets.QTableWidgetItem(name)
        song_name.setFlags(QtCore.Qt.ItemIsEnabled)
        song_name.setFlags(QtCore.Qt.ItemIsSelectable)
        

        song_quality = QtWidgets.QTableWidgetItem(
                "{:.1f}".format(quality))
        song_quality.setFlags(QtCore.Qt.ItemIsEnabled)
        song_quality.setFlags(QtCore.Qt.ItemIsSelectable)

       
        self.ui.tableWidget_Songs.setCellWidget(row, ACTIVE_CHECK_INDEX, active_check)
        self.ui.tableWidget_Songs.setItem(row, SONG_NAME_INDEX, song_name)
        self.ui.tableWidget_Songs.setItem(row, SONG_QUALITY_INDEX, song_quality)

        # self.ui.tableWidget_Songs.resizeColumnsToContents()
        
        return row
    

    def SuggestSong(self):
        """
        Ramdonly suggest a song to work on
        """
        
        active_songs = self.active_songs
        songs = self.songs
        
        if len(active_songs) == 0:
            song = ''
        else:
            # Randomize, but weighted by delay since last performance
            interval = 0
            for k in active_songs:
                 interval += songs[k]['quality']
                 
            selection = random.randrange(interval)
            for index, song in enumerate(active_songs):
                 selection -= active_songs[song]['quality']
                 if selection < 0:
                     break
            
            # update time since last play for all other active songs
            for i, k in enumerate(active_songs):
                if k != song:
                    songs[k]['quality'] += 1
                else:
                    index = i 
                    songs[k]['quality'] = 1
            
            self.songs = songs
            
        self.ui.tableWidget_Songs.selectRow(index)
        
        self.GuitarTools.qt_application.clipboard().setText(song)
        # clipboard.setText(song)
        
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
