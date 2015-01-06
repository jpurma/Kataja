#! /usr/bin/env python3.4
# coding=utf-8
"""
Created on 28.8.2013

@author: purma
"""
from PyQt5 import QtWidgets
from kataja.KatajaMain import KatajaMain
import sys


# building with pyinstaller:
# PyInstaller-2.1/pyinstaller.py Kataja.py --clean -n Kataja -i kataja.icns --windowed

# noinspection PyCallByClass,PyTypeChecker
QtWidgets.QApplication.setStyle('Fusion')

app = QtWidgets.QApplication(sys.argv)
print("Launching Kataja with Python %s.%s" % (sys.version_info.major, sys.version_info.minor))
window = KatajaMain(app, sys.argv)
window.show()
app.exec_()