#! /usr/bin/env python3.4
# coding=utf-8
"""
Created on 28.8.2013

@author: purma
"""
import datetime
import os
import sys
from kataja.environment import resources_path, running_environment
from PyQt5 import QtWidgets, QtPrintSupport, QtGui, QtCore

# QtPrintSupport is imported here only because py2app then knows to add it as a framework.
# libqcocoa.dynlib requires QtPrintSupport.
ok = QtPrintSupport


dir_path = os.path.dirname(os.path.abspath(__file__))
if running_environment == 'mac app':
    QtCore.QCoreApplication.setLibraryPaths([dir_path + '/../plugins'])
print("Launching Kataja with Python %s.%s" % (sys.version_info.major, sys.version_info.minor))
print('launch path: ', dir_path)

app = QtWidgets.QApplication(sys.argv)
font = QtGui.QFont('Helvetica', 10)
app.setFont(font)
author = 'Jukka Purma'
app.setApplicationName('Kataja')
app.setOrganizationName('JPurma-Aalto')
app.setOrganizationDomain('jpurma.aalto.fi')
app.setStyle('Fusion')
splash = QtWidgets.QSplashScreen(QtGui.QPixmap(resources_path+'katajalogo.png'))
#nice_yellow = QtGui.QColor(181, 137, 0)
nice_yellow = QtGui.QColor(238, 232, 213)
splash.showMessage('%s | Fetching version...' % author, QtCore.Qt.AlignBottom | QtCore.Qt.AlignHCenter, nice_yellow)
app.processEvents()
splash.show()

try:
    version_file = open(resources_path+'version.txt', 'r')
    version = version_file.readlines()
    version_file.close()
except FileNotFoundError:
    version = []


if version:
    date, running_number, version_name = version[0].split(' | ', 2)
    running_number = int(running_number[2:])
    if running_environment.endswith('python'):
        date = str(datetime.datetime.now())
        running_number += 1
else:
    date = str(datetime.datetime.now())
    running_number = 1
    version_name = ''

if running_environment.endswith('python'):
    try:
        version_file = open(resources_path+'version.txt', 'w')
        version_file.write('%s | v. %s | %s' % (date, running_number, version_name))
        version_file.close()
    except IOError:
        print('write failed')
        pass

splash.showMessage('%s | %s | v. %s | %s' % (author, date, running_number, version_name),
                   QtCore.Qt.AlignBottom | QtCore.Qt.AlignHCenter, nice_yellow)

from kataja.KatajaMain import KatajaMain

window = KatajaMain(app, splash, sys.argv)
splash.finish(window)
app.setActiveWindow(window)
app.processEvents()
app.exec_()
