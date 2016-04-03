# coding=utf-8
from PyQt5 import QtCore, QtGui, QtWidgets
from kataja.UIItem import UIItem

class ModeLabel(UIItem, QtWidgets.QLabel):
    def __init__(self, text, ui_key, parent=None):
        UIItem.__init__(self, ui_key, None)
        QtWidgets.QLabel.__init__(self, text, parent=parent)




