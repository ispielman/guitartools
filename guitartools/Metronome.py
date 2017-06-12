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
        
        # Link double click action
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(
                self._clicked
                )

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

    def newItem(self, row, BPM="100", Duration="60"):
        if row == -1 or row > self.rowCount():
            new_row = self.rowCount()
        else:
            new_row = row+1
            
        self.insertRow(new_row)
                
        tableWidgetItem_Bpm = QtWidgets.QTableWidgetItem(BPM)
        tableWidgetItem_Bpm.default = "100"

        tableWidgetItem_Duration = QtWidgets.QTableWidgetItem(Duration)
        tableWidgetItem_Duration.default = "60"

        self.setItem(new_row, 0, tableWidgetItem_Bpm)
        self.setItem(new_row, 1, tableWidgetItem_Duration)

        self.resizeColumnsToContents()
        
    def _validItem(self, item):
        
        value = item.text()
        
        try:
            x = int(value)
            x = max(x, 1)
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

class QSignalLauncher(QtWidgets.QWidget):
    """
    This encapsulates a bunch of signals to allow non QWidget objects to emit
    signals
    """
    
    timerSettings = QtCore.pyqtSignal(object)
    timerSettingsGo = QtCore.pyqtSignal()


AutoConfig = MakeAutoConfig()
class Metronome(AutoConfig):

    #
    # signals
    #

    def __init__(self, GuitarTools, **kwargs):
        #
        # Setup initial values
        #

        self._externalTimerIndex = -1
        self._MetronomeIndex = 0
        self._MetronomeLoud = True
        self._TimerConnected = False

        super().__init__(**kwargs)
        
        self.GuitarTools = GuitarTools
        
        loader = UiLoader()
        loader.registerCustomWidget(QTableWidgetMetronome)

        self.ui = loader.load(LocalPath('metronome.ui'))
        self.ui.timerSettings = QtCore.pyqtSignal(object)
        self.ui.signalLauncher = QSignalLauncher(self.ui)
        
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
        self.ui.MetronomeOutput = QtMultimedia.QAudioOutput(AudioFormat)
        self.ui.MetronomeOutput.setVolume(1.0)
        self.ui.MetronomeBuffer = QtCore.QBuffer()
        self.ui.MetronomeDataQuiet = QtCore.QByteArray()
        self.ui.MetronomeDataLoud = QtCore.QByteArray()

        self._make_click()
        
        # Metronome Flash timer
        self.ui.MetronomeTimer = QtCore.QTimer()
        
        # Metronome MetronomeUnFlash timer
        self.ui.MetronomeUnFlashTimer = QtCore.QTimer()

        # Start / stop metronome
        self.ui.comboBox_Metronome.currentIndexChanged.connect(self.MetronomeStartStop)
        
        # Spinboxes: if metronome is running, change speed / emphasis based on changes
        self.ui.BPM_spinBox.setKeyboardTracking(False)
        self.ui.BPM_spinBox.valueChanged.connect(self.MetronomeUpdate)

        self.ui.Emph_spinBox.setKeyboardTracking(False)
        self.ui.Emph_spinBox.valueChanged.connect(self.MetronomeUpdate)
        
        # Table mode
        self.ui.tableWidgetMetronome.setColumnCount(2)
        self.ui.tableWidgetMetronome.setRowCount(0)
        self.ui.tableWidgetMetronome.setHorizontalHeaderLabels(["BPM", "Duration"])
        self.ui.tableWidgetMetronome.resizeColumnsToContents()
        self.ui.tableWidgetMetronome.resizeRowsToContents()


    #    
    # TODO: Table needs to be populated from the ini file
    #

    @property
    def dynamicValues(self):
        rows = self.ui.tableWidgetMetronome.rowCount()
        
        BPM = []
        Duration = []
        for row in range(rows):
            
            BPM.append(int(self.ui.tableWidgetMetronome.item(row, 0).text()))
            Duration.append(int(self.ui.tableWidgetMetronome.item(row, 1).text()))
            
        return {'BPM':BPM, 'Duration':Duration}

    
    #
    # Metronome Methods
    #

    def MetronomeUnFlash(self):
        self.ui.pushButton_Click.setDown(False)

    def MetronomeFlash(self):
        
        # First start the current output
        self._play(self._MetronomeLoud)
        
        # Flash the strobe button.
        self.ui.pushButton_Click.setDown(True)
        self.ui.MetronomeUnFlashTimer.singleShot(100, self.MetronomeUnFlash)

        # Now get ready for the next shot
        self._MetronomeIndex += 1
        emphasis = self.ui.Emph_spinBox.value()
        
        if self._MetronomeIndex % emphasis == 0:
            self._MetronomeLoud = True
        else:
            self._MetronomeLoud = False

    def MetronomeUpdate(self):
        if self.ui.MetronomeTimer.isActive():
            BPM = self.ui.BPM_spinBox.value()
            self.ui.MetronomeTimer.start(60 / BPM * 1000) # BPM to ms

    def MetronomeStartStop(self, state):
                
        if state == 0:
            # Stopped state
            self.ui.MetronomeTimer.stop()
            self._connect_timer(False)
            return
        
        # All remaining states are "Started states"
        
        self._MetronomeIndex = 0
        self._MetronomeVolume = 1.0
        BPM = self.ui.BPM_spinBox.value()
        
        self.ui.MetronomeTimer.start(60 / BPM * 1000) # BPM to ms

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

            self.ui.signalLauncher.timerSettings.emit(self.dynamicValues['Duration'])
            self.ui.signalLauncher.timerSettingsGo.emit()
        
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
                self.ui.MetronomeTimer.timeout.connect(self.MetronomeFlash)
            
            self._TimerConnected = True
        else:
            # Disconnect if needed
            if self._TimerConnected:
                self.ui.MetronomeTimer.timeout.disconnect()
                
            self._TimerConnected = False
            
    def externalTimerIndex(self, index):
        """
        a slot for the index of the external timer.  This allows the external
        timer to direct the metronome to click or not
        """
    
        self._externalTimerIndex = int(index)
        
        state = self.ui.comboBox_Metronome.currentIndex()
        if state == 2:
            self._connect_timer(index != -1)        
        elif state == 3:
            # Update metronome settings from table based on current index
            # note that index is reversed indexed

            if index != -1:
                self.ui.BPM_spinBox.setValue(self.dynamicValues['BPM'][-(index+1)])
            
            
            self._connect_timer(index != -1)
        
    #
    # Support Functions
    #

    def _play(self, Loud=True):
    
        if self.ui.MetronomeOutput.state() == QtMultimedia.QAudio.ActiveState:
            self.ui.MetronomeOutput.stop()
        
        if self.ui.MetronomeBuffer.isOpen():
            self.ui.MetronomeBuffer.close()
        
        if Loud:
            self.ui.MetronomeBuffer.setData(self.ui.MetronomeDataLoud)
        else:
            self.ui.MetronomeBuffer.setData(self.ui.MetronomeDataQuiet)

        self.ui.MetronomeBuffer.open(QtCore.QIODevice.ReadOnly)
        self.ui.MetronomeBuffer.seek(0)
        
        self.ui.MetronomeOutput.reset()
        self.ui.MetronomeOutput.start(self.ui.MetronomeBuffer)

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

        self.ui.MetronomeDataQuiet.clear()
        self.ui.MetronomeDataLoud.clear()
        for value in self._click_array:
            self.ui.MetronomeDataQuiet.append(struct.pack("<h", value//4))
            self.ui.MetronomeDataLoud.append(struct.pack("<h", value))
        
        # Zero pad
        for value in self._click_array:
            self.ui.MetronomeDataQuiet.append(struct.pack("<h", 0))
            self.ui.MetronomeDataLoud.append(struct.pack("<h", 0))
  