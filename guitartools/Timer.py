#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtWidgets

from guitartools.Support import UiLoader, LocalPath, MakeAutoConfig

class QProgressBarNumber(QtWidgets.QWidget):
    """
    A progress bar with a number display as well, along with a display of the
    remaining repeats
    """
    
    RUNNING = 0
    STOPPED = 1
    PAUSED = 2

    #
    # signals: beep, timer update and repeats deincremented
    #

    beep = QtCore.pyqtSignal()

    timeout = QtCore.pyqtSignal()
    
    repeatTimeout = QtCore.pyqtSignal(int)

    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #
        # Init Local Variables
        #

        self.setTimes([0,])
        self._active_times = self._times.copy()

        self.setLeadIn(3)

        self._state = QProgressBarNumber.STOPPED

        #
        # Basic timer functionality
        #

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._timerUpdate)

        #
        # GUI elements
        #
        
        self.ProgressBar = QtWidgets.QProgressBar()

        self.label_Time = QtWidgets.QLabel("Time")
        self.Time = QtWidgets.QSpinBox()
        self.Time.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.Time.setReadOnly(True)
        font = self.Time.font()
        font.setBold(True)
        
        self.Time.setFont(font)
        
        self.label_Repeats = QtWidgets.QLabel("Repeats")
        self.Repeats = QtWidgets.QSpinBox()
        self.Repeats.setButtonSymbols(QtWidgets.QAbstractSpinBox.NoButtons)
        self.Repeats.setReadOnly(True)
        font = self.Repeats.font()
        font.setBold(True)
        
        self.Repeats.setFont(font)
        
        self.grid = QtWidgets.QHBoxLayout()
        self.grid.setContentsMargins(0,0,0,0)
        self.grid.addWidget(self.ProgressBar)
        self.grid.addWidget(self.label_Time)
        self.grid.addWidget(self.Time)
        self.grid.addWidget(self.label_Repeats)
        self.grid.addWidget(self.Repeats)

        self.setLayout(self.grid)
        
        self.timerReset()
    
    @property
    def state(self):
        return self._state
    
    @property
    def _times_with_leadin(self):
        """
        Gives us the list of times including the leadin at the start
        """
        return self._leadin + self._active_times
        
    def setTimes(self, val):
        """
        Set the durations of each timer as a list
        """
                
        self._times = val            
               
    def setValue(self, time, repeats):
        self.ProgressBar.setValue(time)
        self.Time.setValue(time)
        self.Repeats.setValue(repeats)

    def value(self):
        return ( self.Time.value(), self.Repeats.value() )

    def timerReset(self):
        """
        Reset the timer to a state specified by self._times
        """
        
        self._active_times = self._times.copy()
        
        self.ProgressBar.setRange(0, self._times_with_leadin[0])
        self.setValue(self._times_with_leadin[0], len(self._times))
        
    def setLeadIn(self, val):
        """
        Add an initial leadin countdown
        """
        
        if val:
            self._leadin = [int(val)]
        else:
            self._leadin = []
                
    #
    # Methods from timer (slots and emitted signal)
    #
    
    def stop(self, *args, **kwargs):
        """
        This stops the timer and resets it to its defaults
        """
        self._emit_repeatTimeout(-1)
        self._state = QProgressBarNumber.STOPPED
        ans = self.timer.stop(*args, **kwargs)
        self.timerReset()

        return ans
    
    def start(self, *args, **kwargs):
        """
        Sending start either continues from being paused OR starts fresh.
        """
        # send a signal indicating the current location in the repeats list
        self._emit_repeatTimeout(self.value()[1])
        self._state = QProgressBarNumber.RUNNING

        return self.timer.start(1000)

    def pause(self, *args, **kwargs):
        self._state = QProgressBarNumber.PAUSED
        
        return self.timer.stop(*args, **kwargs)

    def _timerUpdate(self):
        """
        slot sending a single tick to the timer
        """
        
        time, repeats = self.value()

        if time <= 0:
            # Send beep signal!!
            self.beep.emit()
            
            # Check to see if we should do a repeat or not
            if repeats <= 0:
                self.stop()
            else:
                next_time = self._times_with_leadin[-repeats]
                repeats -= 1
                self.ProgressBar.setRange(0, next_time)
                self.setValue(
                        next_time, 
                        repeats)
                
                # Send repeatTimeout and timeout signals
                self._emit_repeatTimeout(repeats)
                self.timeout.emit()

        else:
            self.setValue(time-1, repeats)     
            # send timeout signal
            self.timeout.emit()
    
    def _emit_repeatTimeout(self, val):
        """
        emit the signal indicating the current number of repeats but external
        widgets don't know that we added the leadin, so this info is hidden
        """
        
        # paused condition
        if val < 0:
            self.repeatTimeout.emit(val)
        elif len(self._leadin) == 0:
            self.repeatTimeout.emit(val)
        else:
            # OK there is a leadin and we want to igore it
            # Remember we count down
            if val == len(self._times):
                self.repeatTimeout.emit(val-1)
            else:
                self.repeatTimeout.emit(val)
    
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

        self.ui.pushButton_StartPause.clicked.connect(self.timerStartPause)
        self.ui.pushButton_Reset.clicked.connect(self.timerReset)

        #
        # Set defaults
        #
        
        self.timerReset()
        
     
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


    def timerStartPause(self):
        """
        Start/Pause button of a typical timer
        """

        if self.ui.progressBarNumber_Countdown.state == QProgressBarNumber.RUNNING:
            self.ui.progressBarNumber_Countdown.pause()
        elif self.ui.progressBarNumber_Countdown.state == QProgressBarNumber.PAUSED:
            # if we are paused then just start
            self.ui.progressBarNumber_Countdown.start()
        else:
            # otherwise we will reset send new values as well
            self.timerReset()
            
            self.ui.progressBarNumber_Countdown.start()
            
    def timerReset(self):
        """
        Reset the timer, but only if the timer is in the paused state
        """        
        if self.ui.progressBarNumber_Countdown.state == QProgressBarNumber.PAUSED:
            # This will stop and rest the timer
            self.ui.progressBarNumber_Countdown.stop()
        elif self.ui.progressBarNumber_Countdown.state == QProgressBarNumber.STOPPED:
            # Just reset the timer 
            self.ui.progressBarNumber_Countdown.setTimes(
                    [self.starttime]*self.repeats
                    )

            self.ui.progressBarNumber_Countdown.timerReset()        
        