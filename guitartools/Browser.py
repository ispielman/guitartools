# -*- coding: utf-8 -*-
"""
Created on Sun May 24 22:08:53 2015

Metronome widget

@author: Ian Spielman

Provides metronome widget
"""

from guitartools.Support import UiLoader, LocalPath, MakeAutoConfig

from PyQt5 import QtGui, QtCore, QtWidgets, QtWebEngineWidgets

class QWebEngineViewBrowser(QtWebEngineWidgets.QWebEngineView):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

AutoConfig = MakeAutoConfig()
class Browser(QtWidgets.QWidget, AutoConfig):

    AutoConfig.Add('urlText', 'https://www.google.com')
    
    @property
    def urlText(self):
        return self.url.url()
    
    @urlText.setter
    def urlText(self, address):
        self.url.setUrl(address)

        # Make sure that the http(s) part has been specified
        if self.url.scheme() == '':
            self.url.setScheme('http')
        
        if self.url.isValid():
        
            # It is possible that this will be called by super before the 
            # webEngineViewBrowser_Browser object has been initized
            try:
                self.webEngineViewBrowser_Browser.load(self.url)     
            except:
                pass
    
    def __init__(self, *args, **kwargs):

        self.url = QtCore.QUrl()        
        super().__init__(*args, **kwargs)
                
        loader = UiLoader()
        loader.registerCustomWidget(QWebEngineViewBrowser)
        loader.load(LocalPath('browser.ui'), self)

        #
        # Setup browser
        #

        # wow, I segfault python:
        # self.webEngineViewBrowser_Browser.page().profile().cookieStore().deleteAllCookies()

        
        webEngineProfile = QtWebEngineWidgets.QWebEngineProfile.defaultProfile()

        webEngineProfile.setPersistentCookiesPolicy(
                QtWebEngineWidgets.QWebEngineProfile.NoPersistentCookies
                )
        
        webEngineProfile.cookieStore().deleteAllCookies()

        #
        # Link Browser and address display
        #
        
        self.lineEdit_address.editingFinished.connect(self.load)
        self.webEngineViewBrowser_Browser.urlChanged.connect(self.urlChanged)
        
        #
        # Direct Browser to first site
        #
        
        self.webEngineViewBrowser_Browser.load(self.url)

    def load(self):
        self.urlText = self.lineEdit_address.text()
                
        self.lineEdit_address.setText(self.urlText)
        
    def urlChanged(self):
        self.url = self.webEngineViewBrowser_Browser.url()
        self.lineEdit_address.setText(self.urlText)
    