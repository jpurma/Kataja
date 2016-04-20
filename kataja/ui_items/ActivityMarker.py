# coding=utf-8

from PyQt5 import QtWidgets
from kataja.singletons import qt_prefs, ctrl
from kataja.UIItem import UIItem


class ActivityMarker(UIItem, QtWidgets.QGraphicsRectItem):
    """ Blinky thing to announce that computing is going on. """

    def __init__(self, role, ui_key):
        UIItem.__init__(self, ui_key, None)
        QtWidgets.QGraphicsRectItem.__init__(self, 0, 0, 4, 4)  # , scene = parent)
        self.role = role
        self.setZValue(100)
        self.setBrush(ctrl.cm.get('accent%s' % str(self.role + 1)))
        self.setPen(qt_prefs.no_pen)  # QtCore.Qt.NoPen
        self.setPos(5 + self.role * 10, 5)

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. List of types is kept as comments in globals.py,
        but for performance reasons just hardcode it here.
        :return:
        """
        return 65650

    def update_position(self):
        """ stay always in initial position """
        pass

    def update_colors(self):
        """ Uses available accent colors """
        self.setBrush(ctrl.cm.get('accent%s' % str(self.role + 1)))


