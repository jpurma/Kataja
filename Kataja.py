#! /usr/bin/env python3.4
# coding=utf-8
"""
Created on 28.8.2013

@author: purma
"""
from PyQt5 import QtCore
import os

filePath = os.path.dirname(os.path.abspath(__file__))
print(filePath)
if filePath.endswith('Resources'):
    QtCore.QCoreApplication.setLibraryPaths([filePath + '/../plugins'])
print('librarypath:', QtCore.QCoreApplication.libraryPaths())


from PyQt5 import QtWidgets, QtPrintSupport
from kataja.KatajaMain import KatajaMain
import sys

ok = QtPrintSupport

# building with pyinstaller:
# PyInstaller-2.1/pyinstaller.py Kataja.py --clean -n Kataja -i kataja.icns --windowed

# noinspection PyCallByClass,PyTypeChecker
#QtWidgets.QApplication.setStyle('Fusion')


app = QtWidgets.QApplication(sys.argv)
app.setApplicationName('Kataja')
app.setOrganizationName('JPurma-Aalto')
app.setOrganizationDomain('jpurma.aalto.fi')
app.setStyle('Fusion')
print("Launching Kataja with Python %s.%s" % (sys.version_info.major, sys.version_info.minor))
print(app.applicationFilePath())
window = KatajaMain(app, sys.argv)
window.show()
app.exec_()
