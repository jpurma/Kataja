import random

from PyQt5 import QtGui, QtWidgets

from kataja.Controller import qt_prefs


class ActivityMarker(QtWidgets.QGraphicsRectItem):
    def __init__(self, parent=None):
        QtWidgets.QGraphicsRectItem.__init__(self, 0, 0, 10, 10)  # , scene = parent)
        self.setBrush(QtGui.QColor(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
        self.setPen(qt_prefs.no_pen)  # QtCore.Qt.NoPen
        self.setZValue(100)

    def show(self):
        QtWidgets.QGraphicsRectItem.show(self)


