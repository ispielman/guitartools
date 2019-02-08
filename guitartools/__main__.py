#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import signal
import configobj

# Quit on ctrl-c
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt5 import QtWidgets

#
# Metronome widget
#

from guitartools.Metronome import Metronome
from guitartools.Timer import Timer
from guitartools.Changes import Changes
from guitartools.Listening import Listening
from guitartools.Songs import Songs

from guitartools.Support import UiLoader, LocalPath, MakeAutoConfig


class GuitarToolsWindow(QtWidgets.QMainWindow):
    pass

AutoConfig = MakeAutoConfig()
class GuitarToolsMainWindow(AutoConfig):

    AutoConfig.Add('_filename', None)
    AutoConfig.Add('volume', 100)
    _autoconfig_on_init = False
    
    def __init__(self, application, **kwargs):
        super().__init__(**kwargs)
                
        self.qt_application = application

        loader = UiLoader()

        self.ui = loader.load(LocalPath('mainwindow.ui'), GuitarToolsWindow())

        # set all autoconfig items
        self.set_state(**kwargs)
        
        # #####################################################################
        #
        # Custom widgets
        # 
        # #####################################################################



        #
        # Timer
        #
        self.Timer = Timer(self, autoconfig_name_key='timer')
        self.ui.verticalLayout_Timer.addWidget(self.Timer.ui)
        self.Timer.ui.progressBarNumber_Countdown.beep.connect(
                self.qt_application.beep
                )

        #
        # Metronome
        #
        self.Metronome = Metronome(autoconfig_name_key='metronome')
        self.ui.verticalLayout_Metronome.addWidget(self.Metronome)
        
        # Now link the metronome to the timer
        self.Timer.ui.progressBarNumber_Countdown.repeatTimeout.connect(
                self.Metronome.externalTimerIndex
                )

        self.Metronome.timerSettings.connect(
                self.Timer.ui.progressBarNumber_Countdown.setTimes)

        self.Metronome.timerSettingsGo.connect(
                self.Timer.ui.progressBarNumber_Countdown.stop)

        self.Metronome.timerSettingsGo.connect(
                self.Timer.ui.progressBarNumber_Countdown.start)
        
        self.ui.verticalSlider_Volume.valueChanged.connect(self.Metronome.setVolume)
        self.ui.verticalSlider_Volume.valueChanged.emit(self.ui.verticalSlider_Volume.value() )

        
        #
        # Chord changes
        #
        self.Changes = Changes(self, autoconfig_name_key='changes')
        self.ui.verticalLayout_Changes.addWidget(self.Changes.ui)

        #
        # Songs Suggestor
        #
        self.Songs = Songs(self, autoconfig_name_key='songs')
        self.ui.verticalLayout_Songs.addWidget(self.Songs.ui)

        #
        # Listening
        #
        self.Listening = Listening(self, autoconfig_name_key='listening')
        self.ui.verticalLayout_Listening.addWidget(self.Listening.ui)
        
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
        
        self.ui.actionSave_Log_File.triggered.connect(self.SaveChanges)
        
        self.SetFilename(None)

        # Quit
        self.ui.actionQuit.triggered.connect(self.Quit)

        self.qt_application.aboutToQuit.connect(self.GracefulShutdown)

        #
        # Setup complete.  Show the user interface
        #
                
        self.ui.show()
        
        # Now load the default settings
        
        scriptDir = os.path.dirname(os.path.realpath(__file__)) + os.path.sep + 'examples'
        ConfigFile = scriptDir + os.path.sep + 'changes.ini'
        self.SetFilename(ConfigFile)
        self._SetWindowTitle()

    @property
    def volume(self):
        return self.ui.verticalSlider_Volume.value()
    
    @volume.setter
    def volume(self, value):
        value = max(int(value), 0)
        value = min(int(value), 100)
        
        self.ui.verticalSlider_Volume.setValue(value)

    def Quit(self):
        self.qt_application.quit()

    def GracefulShutdown(self):
        self.SaveChanges()

    def SetLogFile(self):

        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self.ui,
                                                  "QFileDialog.getOpenFileName()", 
                                                  "",
                                                  "Config files (*.ini);;All Files (*)"
                                                  )
        if fileName:            
            self.SetFilename(fileName)
            
        self._SetWindowTitle()
            
    def _SetWindowTitle(self):
        if self._filename is None:
            self.ui.setWindowTitle("guitartools - ")
        else:
            self.ui.setWindowTitle("guitartools - {}".format(self._filename))

    #
    # Load and save from configobj files
    #

    def SetFilename(self, filename):
                
        if filename is not None:
            try:
                state = configobj.ConfigObj(infile=filename)
                
            except:
                self.ui.statusbar.showMessage("Invalid file: " + filename, 10000)
                
                state = configobj.ConfigObj()


        else:
            state = configobj.ConfigObj()

        # Now for every subwidget distributed the config
        self.set_state(**state)
        self._filename = filename        

        self.Timer.set_state(**state)
        self.Metronome.set_state(**state)
        self.Changes.set_state(**state)
        self.Songs.set_state(**state)
        self.Listening.set_state(**state)

    
    def SaveChanges(self):
        """
        Save to disk
        """
        
        state = configobj.ConfigObj()
        state.update(self.get_state())
        state.update(self.Timer.get_state())
        state.update(self.Metronome.get_state())
        state.update(self.Changes.get_state())
        state.update(self.Songs.get_state())
        state.update(self.Listening.get_state())

        
        if self._filename is not None:
            state.filename = self._filename
            state.write()

        self._unsaved_changes = False


if __name__ == '__main__':
    qapplication = QtWidgets.QApplication(sys.argv)

    app = GuitarToolsMainWindow(qapplication, autoconfig_name_key='guitartools')

    def execute_program():
        qapplication.exec_()    

    sys.exit(execute_program())
