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

from PyQt5 import QtCore
from PyQt5 import QtMultimedia

AutoConfig = MakeAutoConfig()
class Metronome(AutoConfig):
    def __init__(self, GuitarTools, **kwargs):
        super().__init__(**kwargs)
        
        self.GuitarTools = GuitarTools
        
        loader = UiLoader()

        self.ui = loader.load(LocalPath('metronome.ui'))
        
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
        self.ui.MetronomeTimer.timeout.connect(self.MetronomeFlash)
        
        # Metronome MetronomeUnFlash timer
        self.ui.MetronomeUnFlashTimer = QtCore.QTimer()

        # Start / stop metronome
        self.ui.MetronomeStartStopButton.clicked.connect(self.MetronomeStartStop)
        
        # Spinboxes: if metronome is running, change speed / emphasis based on changes
        self.ui.BPM_spinBox.setKeyboardTracking(False)
        self.ui.BPM_spinBox.valueChanged.connect(self.MetronomeUpdate)

        self.ui.Emph_spinBox.setKeyboardTracking(False)
        self.ui.Emph_spinBox.valueChanged.connect(self.MetronomeUpdate)

        self._MetronomeIndex = 0
        self._MetronomeLoud = True

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

    def MetronomeStartStop(self):
        
        if self.ui.MetronomeTimer.isActive():
            self.ui.MetronomeTimer.stop()
        else:
            self._MetronomeIndex = 0
            self._MetronomeVolume = 1.0
            BPM = self.ui.BPM_spinBox.value()
            
            self.ui.MetronomeTimer.start(60 / BPM * 1000) # BPM to ms

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
  