# -*- coding: utf-8 -*-
"""
Created on Sun May 24 22:08:53 2015

Metronome widget

@author: Ian Spielman

Provides metronome widget
"""

import struct
import numpy as np

from guitartools.Support import UiLoader, LocalPath, MakeAutoConfig

from PyQt5 import QtGui, QtCore, QtWidgets, QtMultimedia

class _QStyledItemDelegateMetronome(QtWidgets.QStyledItemDelegate):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def eventFilter(self, obj, event):
        """
        we will not pass on tab key presses to the cell
        """
        
        if type(event) == QtGui.QKeyEvent and event.key() == QtCore.Qt.Key_Tab:
            return False

        return super().eventFilter(obj, event)
        

class QTableWidgetMetronome(QtWidgets.QTableWidget):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Link right click action to context menu
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(
                self._clicked
                )

        # Link double click action to new item if clicked in no-mans land
        self.itemChanged.connect(self._validItem)

        self.delegate = _QStyledItemDelegateMetronome(self)
        self.setItemDelegate(self.delegate)

        

    def _clicked(self, point):
        row = self.row(self.itemAt(point))
        
        menu = QtWidgets.QMenu(self)
        menu.addAction(self._actionCreate(row))
        menu.addAction(self._actionRemove(row))
        menu.exec_(QtGui.QCursor.pos())
    
    def _actionCreate(self, row):
        """
        return an action to create at the specified row
        """
    
        actionCreate = QtWidgets.QAction("Create new item below...", self)
    
        def _createItem():
            self.newItem(row)
                
        actionCreate.triggered.connect(_createItem)
        
        return actionCreate

    def _actionRemove(self, row):
        """
        return an action to create at the specified row
        """
    
        actionRemove = QtWidgets.QAction("Remove current item...", self)
    
        def _removeItem():
            self.removeRow(row)
            
        actionRemove.triggered.connect(_removeItem)
        
        return actionRemove

    def newItem(self, row, BPM="100", Duration="60", Skipped="0%"):
        if row == -1 or row > self.rowCount():
            new_row = self.rowCount()
        else:
            new_row = row+1
            
        self.insertRow(new_row)
                
        tableWidgetItem_Bpm = QtWidgets.QTableWidgetItem(BPM)
        tableWidgetItem_Bpm.min = "1"
        tableWidgetItem_Bpm.default = "100"
        tableWidgetItem_Bpm.max = "240"

        tableWidgetItem_Duration = QtWidgets.QTableWidgetItem(Duration)
        tableWidgetItem_Duration.min = "1"
        tableWidgetItem_Duration.default = "60"
        tableWidgetItem_Duration.max = "3600"
        
        tableWidgetItem_Skipped = QtWidgets.QTableWidgetItem(Skipped)
        tableWidgetItem_Skipped.min = "0"
        tableWidgetItem_Skipped.default = "0"
        tableWidgetItem_Skipped.max = "99"


        self.setItem(new_row, 0, tableWidgetItem_Bpm)
        self.setItem(new_row, 1, tableWidgetItem_Duration)
        self.setItem(new_row, 2, tableWidgetItem_Skipped)

        self.resizeColumnsToContents()
        
    def _validItem(self, item):
        
        value = item.text()
        min_value = item.min
        max_value = item.max
        
        try:
            x = int(value)
            x = max(x, int(min_value))
            x = min(x, int(max_value))
            x = str(x)
        except:
            x = str(item.default)
                        
        item.setText(x)
        
    def keyPressEvent(self, event):
        """
        If we are at the last row, create a new one on tab
        """
        
        if event.key() == QtCore.Qt.Key_Tab:
            row = self.currentRow()
            column = self.currentColumn()
                                    
            if (row == self.rowCount()-1) and (column == self.columnCount()-1):
                self.newItem(row)
            
            super().keyPressEvent(event)
        else:
            super().keyPressEvent(event)

    def mouseDoubleClickEvent(self, event):
        """
        Make a new item when double clicking on empty table
        """
        
        if event.button() == QtCore.Qt.LeftButton:
            rows = self.rowCount()
                        
            if (rows == 0):
                self.newItem(-1)
            else:
                super().mouseDoubleClickEvent(event)
        else:
            super().mouseDoubleClickEvent(event)



AutoConfig = MakeAutoConfig()
class Metronome(QtWidgets.QWidget, AutoConfig):

    #
    # signals
    #
    timerSettings = QtCore.pyqtSignal(object)
    timerSettingsGo = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        
        # Setup widget
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        loader = UiLoader()
        loader.registerCustomWidget(QTableWidgetMetronome)
        loader.load(LocalPath('metronome.ui'), self)
        
        #
        # Setup initial values
        #

        self._externalTimerIndex = -1
        self._MetronomeIndex = 0
        self._MetronomeLoud = True
        self._TimerConnected = False

        # Perform autoconfig
        AutoConfig.__init__(self, autoconfig_name_key='metronome')
        
        #
        # Connect widgets!
        #

        # Metronome sound
        AudioFormat = QtMultimedia.QAudioFormat()
        AudioFormat.setChannelCount(1)
        AudioFormat.setSampleRate(44100)
        AudioFormat.setSampleSize(16)
        AudioFormat.setCodec("audio/pcm")
        AudioFormat.setByteOrder(QtMultimedia.QAudioFormat.LittleEndian)
        AudioFormat.setSampleType(QtMultimedia.QAudioFormat.SignedInt)
        
        self.MetronomeOutput = QtMultimedia.QAudioOutput(AudioFormat)
        self.MetronomeOutput.setVolume(1.0)
        self.MetronomeBuffer = QtCore.QBuffer()
        self.MetronomeDataQuiet = QtCore.QByteArray()
        self.MetronomeDataLoud = QtCore.QByteArray()

        self._make_click()
        
        # Metronome Flash timer
        self.MetronomeTimer = QtCore.QTimer()
        
        # Metronome MetronomeUnFlash timer
        self.MetronomeUnFlashTimer = QtCore.QTimer()

        # Start / stop metronome
        self.comboBox_Metronome.currentIndexChanged.connect(self.MetronomeStartStop)
        
        # Spinboxes: if metronome is running, change speed / emphasis based on changes
        self.BPM_spinBox.setKeyboardTracking(False)
        self.BPM_spinBox.valueChanged.connect(self.MetronomeUpdate)

        self.Emph_spinBox.setKeyboardTracking(False)
        self.Emph_spinBox.valueChanged.connect(self.MetronomeUpdate)
        
        # Table mode
        self.tableWidgetMetronome.setColumnCount(3)
        self.tableWidgetMetronome.setRowCount(0)
        self.tableWidgetMetronome.setHorizontalHeaderLabels(["BPM", "Duration", "Skipped"])
        self.tableWidgetMetronome.resizeColumnsToContents()
        self.tableWidgetMetronome.resizeRowsToContents()


    #    
    # TODO: Table needs to be populated from the ini file
    #

    @property
    def dynamicValues(self):
        rows = self.tableWidgetMetronome.rowCount()
        
        BPM = []
        Duration = []
        for row in range(rows):
            
            BPM.append(int(self.tableWidgetMetronome.item(row, 0).text()))
            Duration.append(int(self.tableWidgetMetronome.item(row, 1).text()))
            
        return {'BPM':BPM, 'Duration':Duration}

    
    #
    # Metronome Methods
    #

    def MetronomeUnFlash(self):
        self.pushButton_Click.setDown(False)

    def MetronomeFlash(self):
        
        # First start the current output
        self._play(self._MetronomeLoud)
        
        # Flash the strobe button.
        self.pushButton_Click.setDown(True)
        self.MetronomeUnFlashTimer.singleShot(100, self.MetronomeUnFlash)

        # Now get ready for the next shot
        self._MetronomeIndex += 1
        emphasis = self.Emph_spinBox.value()
        
        if self._MetronomeIndex % emphasis == 0:
            self._MetronomeLoud = True
        else:
            self._MetronomeLoud = False

    def MetronomeUpdate(self):
        if self.MetronomeTimer.isActive():
            BPM = self.BPM_spinBox.value()
            self.MetronomeTimer.start(60 / BPM * 1000) # BPM to ms

    def MetronomeStartStop(self, state):
                
        if state == 0:
            # Stopped state
            self.MetronomeTimer.stop()
            self._connect_timer(False)
            return
        
        # All remaining states are "Started states"
        
        self._MetronomeIndex = 0
        self._MetronomeVolume = 1.0
        BPM = self.BPM_spinBox.value()
        
        self.MetronomeTimer.start(60 / BPM * 1000) # BPM to ms

        if state == 1: # Started state
            self._connect_timer(True)
        elif state == 2: # External control state
            if self._externalTimerIndex >= 0:
                self._connect_timer(True)
            else:
                self._connect_timer(False)
        elif state == 3:# Table control state

            # Send update signal to timer widget with
            # expected durations

            self.timerSettings.emit(self.dynamicValues['Duration'])
            self.timerSettingsGo.emit()
        
            if self._externalTimerIndex >= 0:
                self._connect_timer(True)
            else:
                self._connect_timer(False)
    
    #
    # External control 
    #
    
    def _connect_timer(self, connect):
        """
        Connect or disconnect timer to flasher, but don't reconnect if already
        connected
        """
        
        if connect:
            # connect if needed
            if not self._TimerConnected:
                self.MetronomeTimer.timeout.connect(self.MetronomeFlash)
            
            self._TimerConnected = True
        else:
            # Disconnect if needed
            if self._TimerConnected:
                self.MetronomeTimer.timeout.disconnect()
                
            self._TimerConnected = False
            
    def externalTimerIndex(self, index):
        """
        a slot for the index of the external timer.  This allows the external
        timer to direct the metronome to click or not
        """
    
        self._externalTimerIndex = int(index)
        
        state = self.comboBox_Metronome.currentIndex()
        if state == 2:
            self._connect_timer(index != -1)        
        elif state == 3:
            # Update metronome settings from table based on current index
            # note that index is reversed indexed

            if index != -1:
                self.BPM_spinBox.setValue(self.dynamicValues['BPM'][-(index+1)])
            
            
            self._connect_timer(index != -1)
        
    #
    # Support Functions
    #

    def _play(self, Loud=True):
    
        if self.MetronomeOutput.state() == QtMultimedia.QAudio.ActiveState:
            self.MetronomeOutput.stop()
        
        if self.MetronomeBuffer.isOpen():
            self.MetronomeBuffer.close()
        
        if Loud:
            self.MetronomeBuffer.setData(self.MetronomeDataLoud)
        else:
            self.MetronomeBuffer.setData(self.MetronomeDataQuiet)

        self.MetronomeBuffer.open(QtCore.QIODevice.ReadOnly)
        self.MetronomeBuffer.seek(0)
        
        self.MetronomeOutput.reset()
        self.MetronomeOutput.start(self.MetronomeBuffer)

    def _make_click(self):

        # make a 0.01 s click
        sample_rate = 44100
        duration = 0.025
        frequency = 400
        sharpness = 0.5
        
        samples = int(sample_rate*duration)
        
        time_array = np.linspace(0, duration, samples)
        
        #sound_array = 2**15 * (np.sin(5*2*np.pi*time_array / duration) * 
        #               np.sin(np.pi*time_array / duration)**2 )

        sound_array = 2**15 * (np.sin(2*np.pi*time_array*frequency) * 
                       np.abs(np.sin(np.pi*time_array / duration))**sharpness )

                                    
        self._click_array = sound_array.astype(np.int16)

        self.MetronomeDataQuiet.clear()
        self.MetronomeDataLoud.clear()
        for value in self._click_array:
            self.MetronomeDataQuiet.append(struct.pack("<h", value//4))
            self.MetronomeDataLoud.append(struct.pack("<h", value))
        
        # Zero pad
        for value in self._click_array:
            self.MetronomeDataQuiet.append(struct.pack("<h", 0))
            self.MetronomeDataLoud.append(struct.pack("<h", 0))
  