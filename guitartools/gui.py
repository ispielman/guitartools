#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import types

import signal

# Quit on ctrl-c
signal.signal(signal.SIGINT, signal.SIG_DFL)

from PyQt5.QtCore import pyqtSlot as Slot
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import uic
    
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

from guitartools.Metronome import Metronome

class GuitarToolsWindow(QtWidgets.QMainWindow):
    pass

class MainWindow():
    def __init__(self, application):
        
        self.Metronome = Metronome()
        
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

        #
        # Connect widgets!
        #

        # Select log file.    
        self.ui.actionSelect_Log_File.triggered.connect(self.SetLogFile)
        
        # Quit
        self.ui.actionQuit.triggered.connect(self.Quit)

        #
        # Metronome
        #
        
        # Start / stop metronome
        self.ui.MetronomeStartButton.clicked.connect(self.MetronomeStart)
        self.ui.MetronomeStopButton.clicked.connect(self.MetronomeStop)
        
        # Spinboxes: if metronome is running, change speed / emphasis based on changes
        self.ui.BPM_spinBox.valueChanged.connect(self.MetronomeUpdate)
        self.ui.Emph_spinBox.valueChanged.connect(self.MetronomeUpdate)
    
        # Start "one-minute changes" timer
        
        # Record "one-minute changes" result
        
        # Suggest changes given "source" and "destination"

       
        #
        # Display the main window
        #

        self.ui.show()

    def Quit(self):
        self.qt_application.quit()

    def SetLogFile(self):
        # self.ui.fileDialog = QtWidgets.QFileDialog()

        fileName, _ = QtWidgets.QFileDialog.getOpenFileName(self.ui,
                                                  "QFileDialog.getOpenFileName()", 
                                                  "",
                                                  "Config files (*.ini);;All Files (*)"
                                                  )
        if fileName:
            print(fileName)
        
        pass

    def MetronomeUpdate(self):
        BPM = self.ui.BPM_spinBox.value()
        emphasis = self.ui.Emph_spinBox.value()

        self.Metronome.update(BPM, emphasis=emphasis)

    def MetronomeStart(self):
        BPM = self.ui.BPM_spinBox.value()
        emphasis = self.ui.Emph_spinBox.value()

        self.Metronome.start(BPM, emphasis=emphasis)

    def MetronomeStop(self):
        self.Metronome.stop()
    

if __name__ == '__main__':
    qapplication = QtWidgets.QApplication(sys.argv)

    app = MainWindow(qapplication)

    def execute_program():
        qapplication.exec_()

    sys.exit(execute_program())
