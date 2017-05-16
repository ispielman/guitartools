#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import types
import struct
import numpy as np

import signal

# Quit on ctrl-c
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic
from PyQt5 import QtMultimedia

# Ripped from qtutils

class UiLoaderPromotionException(Exception):
    pass

class UiLoader(object):
    def __init__(self):
        # dummy module
        self.module = sys.modules['qtutils.widgets'] = types.ModuleType('widgets')    
    
    def registerCustomWidget(self, class_):
        self.registerCustomPromotion(class_.__name__, class_)
    
    def registerCustomPromotion(self, name, class_):
        if hasattr(self.module,name):
             raise UiLoaderPromotionException("The widget '%s' has already had a promotion registered"%name)
        setattr(self.module, name, class_)
     
    def load(self, *args, **kwargs):
        return uic.loadUi(*args, **kwargs)

#
# guitartools material
#

from guitartools.Changes import Changes

class GuitarToolsWindow(QtWidgets.QMainWindow):
    pass

class GuitarToolsMainWindow():
    def __init__(self, application):
        
        self.Changes = Changes()
        
        self.qt_application = application

        loader = UiLoader()

        self.ui = loader.load(
                os.path.join(os.path.dirname(os.path.realpath(__file__)), 'mainwindow.ui'), 
                GuitarToolsWindow())
        
        self.ui.guitartools = self
        
        #
        # Render menubar: work around a bug in osx where menubar is not active.
        #
        if sys.platform=="darwin": 
            self.ui.menubar.setNativeMenuBar(False)

        # Window Title
        self._SetWindowTitle()


        #
        # Connect widgets!
        #

        # Select log file.    
        self.ui.actionSelect_Log_File.triggered.connect(self.SetLogFile)
        self._logfile = None
        
        
        # Quit
        self.ui.actionQuit.triggered.connect(self.Quit)

        #
        # Basic timer functionality
        #

        self.ui.timer = QtCore.QTimer()
        self.ui.timer.timeout.connect(self.TimerUpdate)

        self.ui.pushButton_TimerStartStop.clicked.connect(self.TimerStartStop)
        self.ui.pushButton_TimerReset.clicked.connect(self.TimerReset)

        self._TimerReset()
                
        #
        # Metronome
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
        self.ui.MetronomeBuffer = QtCore.QBuffer()
        self.ui.MetronomeData = QtCore.QByteArray()

        self._make_click()
        
        self.ui.MetronomeBuffer.setData(self.ui.MetronomeData)

        # Metronome Flash timer
        self.ui.MetronomeTimer = QtCore.QTimer()
        self.ui.MetronomeTimer.timeout.connect(self.MetronomeFlash)
        
        # Metronome MetronomeUnFlash timer
        self.ui.MetronomeUnFlashTimer = QtCore.QTimer()

        # Start / stop metronome
        self.ui.MetronomeStartStopButton.clicked.connect(self.MetronomeStartStop)
        
        # Spinboxes: if metronome is running, change speed / emphasis based on changes
        self.ui.BPM_spinBox.valueChanged.connect(self.MetronomeUpdate)
        self.ui.Emph_spinBox.valueChanged.connect(self.MetronomeUpdate)

        self._MetronomeIndex = 0
        self._MetronomeVolume = 1.0

        #
        # Chord changes
        #
        self.ui.pushButton_SuggestChanges.clicked.connect(self.SuggestChordChanges)

       
        #
        # Display the main window
        #

        self.ui.show()

    def Quit(self):
        self.qt_application.quit()

    def SetLogFile(self):

        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self.ui,
                                                  "QFileDialog.getOpenFileName()", 
                                                  "",
                                                  "Config files (*.ini);;All Files (*)"
                                                  )
        if fileName:            
            self.Changes.SetFilename(fileName)
            
        self._SetWindowTitle()
            
    def _SetWindowTitle(self):
        if self.Changes._filename is None:
            self.ui.setWindowTitle("guitartools - ")
        else:
            self.ui.setWindowTitle("guitartools - {}".format(self.Changes._filename))
            
        
    #
    # Timer methods
    #

    def _TimerReset(self):
        start_time = self.ui.spinBox_Timer_Time.value()
        self.ui.progressBar_Timer.setRange(0, start_time)
        self.ui.progressBar_Timer.setValue(0)

        self.ui.lcdNumber_Timer.value = start_time
        self.ui.lcdNumber_Timer.display(self.ui.lcdNumber_Timer.value)

        self.ui.lcdNumber_TimerRepeats.value = self.ui.spinBox_Timer_Repeats.value()
        self.ui.lcdNumber_TimerRepeats.display(self.ui.lcdNumber_TimerRepeats.value)

        self._TimerPaused = False


    def TimerStartStop(self):
        """
        Start Stop button of a typical timer
        """        
        if  self.ui.timer.isActive():
            self.ui.timer.stop()
        else:            

            self.ui.timer.start(1000)

    
    def TimerReset(self):
        """
        Performs stop / reset action
        """
        
        if not self.ui.timer.isActive():
            # Reset Behavior
            self._TimerReset()
    
    def TimerUpdate(self):
        self.ui.progressBar_Timer.setValue(self.ui.progressBar_Timer.value() + 1)

        self.ui.lcdNumber_Timer.value -= 1
        self.ui.lcdNumber_Timer.display(self.ui.lcdNumber_Timer.value)
        
        
        if self.ui.lcdNumber_Timer.value <= 0:
            self.qt_application.beep()
            self.ui.lcdNumber_TimerRepeats.value -=1
            self.ui.lcdNumber_TimerRepeats.display(self.ui.lcdNumber_TimerRepeats.value)
            
            # Check to see if we should do a repeat or not
            if self.ui.lcdNumber_TimerRepeats.value <= 0:
                self.TimerStop()
                self._TimerReset()
            else:
                self.ui.progressBar_Timer.setValue(0)
                
                self.ui.lcdNumber_Timer.value = self.ui.spinBox_Timer_Time.value()

        

    #
    # Metronome Methods
    #

    def MetronomeUnFlash(self):
        self.ui.pushButton_Click.setDown(False)

    def MetronomeFlash(self):
        
        # First start the current output
        self._play()
        
        # Flash the strobe button.
        self.ui.pushButton_Click.setDown(True)
        self.ui.MetronomeUnFlashTimer.singleShot(100, self.MetronomeUnFlash)

        # Now get ready for the next shot
        self._MetronomeIndex += 1
        emphasis = self.ui.Emph_spinBox.value()
        
        if self._MetronomeIndex % emphasis == 0:
            self._MetronomeVolume = 1.0
        else:
            self._MetronomeVolume = 0.25

    def MetronomeUpdate(self):
        if self.ui.MetronomeTimer.isActive():
            BPM = self.ui.BPM_spinBox.value()
            self.ui.MetronomeTimer.start(60 / BPM * 1000) # BPM to ms

    def MetronomeStartStop(self):
        
        if self.ui.MetronomeTimer.isActive():
            self.ui.MetronomeTimer.stop()
        else:
            self._MetronomeIndex = 0
            self._MetronomeVolume = 1.0
            BPM = self.ui.BPM_spinBox.value()
            
            self.ui.MetronomeTimer.start(60 / BPM * 1000) # BPM to ms

    def _play(self):
    
        if self.ui.MetronomeOutput.state() == QtMultimedia.QAudio.ActiveState:
            self.ui.MetronomeOutput.stop()
        
        if self.ui.MetronomeBuffer.isOpen():
            self.ui.MetronomeBuffer.close()
        
        # This was important!

        self.ui.MetronomeBuffer.open(QtCore.QIODevice.ReadOnly)
        self.ui.MetronomeBuffer.seek(0)
        
        self.ui.MetronomeOutput.reset()
        self.ui.MetronomeOutput.setVolume(self._MetronomeVolume)
        self.ui.MetronomeOutput.start(self.ui.MetronomeBuffer)

    def _make_click(self):

        # make a 0.01 s click
        sample_rate = 44100
        channels = 1
        duration = 0.025
        samples = int(sample_rate*duration)
        
        time_array = np.linspace(0, duration, samples)
        channels_array = np.zeros(channels)
        time_array = np.meshgrid(channels_array, time_array)[1]
        
        #sound_array = 2**15 * (np.sin(5*2*np.pi*time_array / duration) * 
        #               np.sin(np.pi*time_array / duration)**2 )

        sound_array = 2**15 * (np.sin(2*np.pi*time_array*440) * 
                       np.sin(np.pi*time_array / duration)**2 )

                                    
        self._click_array = sound_array.astype(np.int16)

        self.ui.MetronomeData.clear()
        for value in self._click_array:
            self.ui.MetronomeData.append(struct.pack("<h", value[0]))

                
    #
    # Chord Changes
    #
    
    def SuggestChordChanges(self):
        Chords = self.Changes.Suggest()
        
        self.ui.lineEdit_Chord1.setText(Chords[0])
        self.ui.lineEdit_Chord2.setText(Chords[1])

if __name__ == '__main__':
    qapplication = QtWidgets.QApplication(sys.argv)

    app = GuitarToolsMainWindow(qapplication)

    def execute_program():
        qapplication.exec_()

    sys.exit(execute_program())
