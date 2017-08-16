from PyQt5 import QtWidgets, QtGui, QtCore

from kataja.UIItem import UIWidget
from kataja.singletons import ctrl


__author__ = 'purma'


class PushButtonBase(QtWidgets.QPushButton, UIWidget):
    """
        PushButton that inherits UIWidget so it can be recognized by kataja ui machinery. Tries
        to do all setup a typical text button will need. There will be classes above to deal with
        special buttons and buttons with icons.
    """
    permanent_ui = True

    def __init__(self, parent=None, text=None, size=None, **kwargs):
        QtWidgets.QPushButton.__init__(self, parent=parent)
        UIWidget.__init__(self, **kwargs)
        if text:
            self.setText(text)
        if size:
            if isinstance(size, QtCore.QSize):
                width = size.width()
                height = size.height()
            elif isinstance(size, tuple):
                width = size[0]
                height = size[1]
            else:
                width = size
                height = size
            size = QtCore.QSize(width, height)
            self.setIconSize(size)
        ctrl.ui.add_ui(self)

    def enterEvent(self, event):
        UIWidget.enterEvent(self, event)
        return QtWidgets.QPushButton.enterEvent(self, event)

    def leaveEvent(self, event):
        UIWidget.leaveEvent(self, event)
        return QtWidgets.QPushButton.leaveEvent(self, event)

