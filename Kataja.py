#! /usr/bin/env python3.4
# coding=utf-8
"""
Created on 28.8.2013

@author: purma
"""
from PyQt5 import QtCore
import os
import sys
from kataja.environment import resources_path, running_environment

if running_environment == 'mac app':
    filePath = os.path.dirname(os.path.abspath(__file__))
    QtCore.QCoreApplication.setLibraryPaths([filePath + '/../plugins'])
print("Launching Kataja with Python %s.%s" % (sys.version_info.major, sys.version_info.minor))


from PyQt5 import QtWidgets, QtPrintSupport, QtGui
from kataja.KatajaMain import KatajaMain

# QtPrintSupport is imported here only because py2app then knows to add it as a framework.
# libqcocoa.dynlib requires QtPrintSupport.
ok = QtPrintSupport
app = QtWidgets.QApplication(sys.argv)
font = QtGui.QFont('Helvetica', 10)
app.setFont(font)
app.setApplicationName('Kataja')
app.setOrganizationName('JPurma-Aalto')
app.setOrganizationDomain('jpurma.aalto.fi')
app.setStyle('Fusion')
splash = QtWidgets.QSplashScreen(QtGui.QPixmap(resources_path+'katajalogo.png'))
splash.showMessage('Jukka Purma | 2015 | Fetching version...', QtCore.Qt.AlignBottom | QtCore.Qt.AlignHCenter, QtGui.QColor(181, 137, 0))
app.processEvents()
splash.show()
window = KatajaMain(app, splash, sys.argv)
splash.finish(window)
window.show()
app.exec_()
