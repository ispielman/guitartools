#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import signal

# Quit on ctrl-c
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt5 import QtWidgets

#
# Metronome widget
#

from guitartools.Metronome import Metronome
from guitartools.Timer import Timer
from guitartools.Changes import Changes

from guitartools.Support import UiLoader, LocalPath


class GuitarToolsWindow(QtWidgets.QMainWindow):
    pass

class GuitarToolsMainWindow():
    def __init__(self, application):
                
        self.qt_application = application

        loader = UiLoader()

        self.ui = loader.load(LocalPath('mainwindow.ui'), GuitarToolsWindow())
        
        #
        # Custom widgets
        # 

        # Basic timer functionality
        self.Timer = Timer(self)
        self.ui.verticalLayout_Timer.addWidget(self.Timer.ui)
                
        # Metronome
        self.Metronome = Metronome(self)
        self.ui.verticalLayout_Metronome.addWidget(self.Metronome.ui)

        # Chord changes
        self.Changes = Changes(self)
        self.ui.verticalLayout_Changes.addWidget(self.Changes.ui)
        
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
            self.Changes.SetFilename(fileName)
            
        self._SetWindowTitle()
            
    def _SetWindowTitle(self):
        if self.Changes._filename is None:
            self.ui.setWindowTitle("guitartools - ")
        else:
            self.ui.setWindowTitle("guitartools - {}".format(self.Changes._filename))
                
if __name__ == '__main__':
    qapplication = QtWidgets.QApplication(sys.argv)

    app = GuitarToolsMainWindow(qapplication)

    def execute_program():
        qapplication.exec_()

    sys.exit(execute_program())
