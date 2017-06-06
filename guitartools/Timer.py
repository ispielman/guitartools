#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets

from guitartools.Support import UiLoader, LocalPath, MakeAutoConfig

class QProgressBarNumber(QtWidgets.QWidget):
    """
    A progress bar with a number display as well
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.ProgressBar = QtWidgets.QProgressBar()

        self.Number = QtWidgets.QSpinBox()
        self.Number.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.Number.setReadOnly(True)
        font = self.Number.font()
        font.setBold(True)
        
        self.Number.setFont(font)
        
        self.grid = QtWidgets.QGridLayout()
        self.grid.setContentsMargins(0,0,0,0)
        self.grid.addWidget(self.ProgressBar, 0, 0, 1, 2)
        self.grid.addWidget(self.Number, 0, 2, 1, 1)

        self.setLayout(self.grid)

    def setRange(self, *args, **kwargs):
        self.ProgressBar.setRange(*args, **kwargs)
            
    def setValue(self, value):
        self.ProgressBar.setValue(value)
        self.Number.setValue(value)
            
    def value(self):
        return self.ProgressBar.value()
        
    def increment(self):
        self.setValue(self.value() + 1)


AutoConfig = MakeAutoConfig()
class Timer(AutoConfig):
    
    AutoConfig.Add("repeats", 5)
    AutoConfig.Add("starttime", 60)
    
    def __init__(self, GuitarTools, **kwargs):

        # Must load UI first!
        loader = UiLoader()
        loader.registerCustomWidget(QProgressBarNumber)
        
        self.ui = loader.load(LocalPath('timer.ui'))
        
        self.GuitarTools = GuitarTools

        # set all autoconfig items
        super().__init__(**kwargs)

        #
        # Basic timer functionality
        #

        self.ui.timer = QtCore.QTimer()
        self.ui.timer.timeout.connect(self.TimerUpdate)

        self.ui.pushButton_StartStop.clicked.connect(self.TimerStartStop)
        self.ui.pushButton_Reset.clicked.connect(self.TimerReset)

        #
        # Set defaults
        #
        
        self._TimerReset()
     
    #
    # Direct access to UI constructs to avoid duplicate of data as python
    # variables.
    #
    
    @property
    def repeats(self):
        return self.ui.spinBox_Repeats.value()
    
    @repeats.setter
    def repeats(self, value):
        value = max(int(value), 1)
        
        self.ui.spinBox_Repeats.setValue(value)

    @property
    def starttime(self):
        return self.ui.spinBox_StartTime.value()
    
    @starttime.setter
    def starttime(self, value):
        value = max(int(value), 1)

        self.ui.spinBox_StartTime.setValue(value)
        
    #
    # Timer methods
    #

    def _TimerReset(self):
        start_time = self.ui.spinBox_StartTime.value()
        self.ui.progressBarNumber_Countdown.setRange(0, start_time)
        self.ui.progressBarNumber_Countdown.setValue(0)

        self.ui.spinBox_RepeatsRemaining.setValue(self.repeats)

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
        self.ui.progressBarNumber_Countdown.increment()        
        
        if self.ui.progressBarNumber_Countdown.value() >= self.starttime:
            self.GuitarTools.qt_application.beep()
            self.ui.spinBox_RepeatsRemaining.setValue(self.ui.spinBox_RepeatsRemaining.value() - 1)
            
            # Check to see if we should do a repeat or not
            if self.ui.spinBox_RepeatsRemaining.value() <= 0:
                self.TimerStop()
                self._TimerReset()
            else:
                self.ui.progressBarNumber_Countdown.setValue(0)