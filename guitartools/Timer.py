#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5 import QtCore

from guitartools.Support import UiLoader, LocalPath


class Timer():
    def __init__(self, GuitarTools):

        self.GuitarTools = GuitarTools

                
        loader = UiLoader()

        self.ui = loader.load(LocalPath('timer.ui'))

        #
        # Basic timer functionality
        #

        self.ui.timer = QtCore.QTimer()
        self.ui.timer.timeout.connect(self.TimerUpdate)

        self.ui.pushButton_TimerStartStop.clicked.connect(self.TimerStartStop)
        self.ui.pushButton_TimerReset.clicked.connect(self.TimerReset)

        self._TimerReset()
                
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
            self._TimerPaused = True
        else:
            if not self._TimerPaused:
                self._TimerReset()
            
            self._TimerPaused = False
            self.ui.timer.start(1000)

    def TimerStop(self):
        """
        Start the timer
        """        
        if self.ui.timer.isActive():
            self.ui.timer.stop()
            self._TimerPaused = True
    
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
            self.GuitarTools.qt_application.beep()
            self.ui.lcdNumber_TimerRepeats.value -=1
            self.ui.lcdNumber_TimerRepeats.display(self.ui.lcdNumber_TimerRepeats.value)
            
            # Check to see if we should do a repeat or not
            if self.ui.lcdNumber_TimerRepeats.value <= 0:
                self.TimerStop()
                self._TimerReset()
            else:
                self.ui.progressBar_Timer.setValue(0)
                
                self.ui.lcdNumber_Timer.value = self.ui.spinBox_Timer_Time.value()