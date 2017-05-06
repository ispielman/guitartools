#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

import signal
# Quit on ctrl-c
signal.signal(signal.SIGINT, signal.SIG_DFL)

try:
    from PySide import QtCore
    from PySide import QtWidgets
    from PySide import QtQuick
except:
    from PyQt4.QtCore import pyqtSlot as Slot
    from PyQt4 import QtCore
    from PyQt4 import QtGui

import qtutils

#
# guitartools material
#

from guitartools.Metronome import Metronome

class GuitarToolsWindow(QtGui.QMainWindow):
    pass

class MainWindow():
    def __init__(self, application):
        
        self.Metronome = Metronome()
        
        self.qt_application = application

        loader = qtutils.UiLoader()

        self.ui = loader.load(
                os.path.join(os.path.dirname(os.path.realpath(__file__)), 'mainwindow.ui'), 
                GuitarToolsWindow())
        
        self.ui.guitartools = self

        #
        # Connect widgets!
        #

        # Start / stop metronome
        self.ui.MetronomeStartButton.clicked.connect(self.MetronomeStart)
        self.ui.MetronomeStopButton.clicked.connect(self.MetronomeStop)
 
        # Start "one-minute changes" timer
        
        # Record "one-minute changes" result
        
        # Suggest changes given "source" and "destination"

        # Select log file.    
       
        #
        # Display the main window
        #

        self.ui.show()

    def MetronomeStart(self):
        BPM = self.ui.BPM_spinBox.value()
        emphasis = self.ui.Emph_spinBox.value()

        self.Metronome.start(BPM, emphasis=emphasis)

    def MetronomeStop(self):
        self.Metronome.stop()
    

if __name__ == '__main__':
    qapplication = QtGui.QApplication(sys.argv)

    app = MainWindow(qapplication)

    def execute_program():
        qapplication.exec_()

    sys.exit(execute_program())
