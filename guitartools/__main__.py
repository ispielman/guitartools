#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
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

from guitartools.Support import UiLoader, LocalPath, MakeAutoConfig


class GuitarToolsWindow(QtWidgets.QMainWindow):
    pass

AutoConfig = MakeAutoConfig()
class GuitarToolsMainWindow(AutoConfig):

    AutoConfig.Add('_filename', None)
        
    def __init__(self, application, **kwargs):
        super().__init__(**kwargs)
                
        self.qt_application = application

        loader = UiLoader()

        self.ui = loader.load(LocalPath('mainwindow.ui'), GuitarToolsWindow())
        
        #
        # Custom widgets
        # 

        # Basic timer functionality
        self.Timer = Timer(self, autoconfig_name_key='timer')
        self.ui.verticalLayout_Timer.addWidget(self.Timer.ui)
                
        # Metronome
        self.Metronome = Metronome(self, autoconfig_name_key='metronome')
        self.ui.verticalLayout_Metronome.addWidget(self.Metronome.ui)

        # Chord changes
        self.Changes = Changes(self, autoconfig_name_key='changes')
        self.ui.verticalLayout_Changes.addWidget(self.Changes.ui)

        # Listening
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

        #
        # Setup complete.  Show the user interface
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