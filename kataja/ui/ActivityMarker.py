# coding=utf-8

from PyQt5 import QtWidgets
from kataja.singletons import qt_prefs, ctrl


class ActivityMarker(QtWidgets.QGraphicsRectItem):
    """ Blinky thing to announce that computing is going on. """

    def __init__(self, role, ui_key):
        QtWidgets.QGraphicsRectItem.__init__(self, 0, 0, 4, 4)  # , scene = parent)
        self.ui_key = ui_key
        self.host = None
        self.role = role
        self.setZValue(100)
        self.setBrush(ctrl.cm.get('accent%s' % str(self.role + 1)))
        self.setPen(qt_prefs.no_pen)  # QtCore.Qt.NoPen
        self.setPos(5 + self.role * 10, 5)

    def update_position(self):
        """ stay always in initial position """
        pass

    def update_colors(self):
        """ Uses available accent colors """
        self.setBrush(ctrl.cm.get('accent%s' % str(self.role + 1)))



