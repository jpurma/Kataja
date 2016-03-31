# coding=utf-8
"""
Created on 28.8.2013

@author: purma
"""
from PyQt5 import QtGui, QtCore, QtWidgets

from kataja.singletons import ctrl


class GlowRing(QtWidgets.QGraphicsEllipseItem):
    """ Decoration for radial menus """

    def __init__(self, parent, radius=40):
        QtWidgets.QGraphicsEllipseItem.__init__(self, QtCore.QRectF(0, 0, 0, 0), parent)
        pen = QtGui.QPen(ctrl.cm.ui())
        pen.setWidth(4)
        self.setPen(pen)
        glow = QtWidgets.QGraphicsBlurEffect(parent)
        glow.setBlurRadius(7)
        glow.setEnabled(True)
        self.setGraphicsEffect(glow)
        self._radius = 0
        self._max_radius = radius
        self._step_size = radius / 6.0

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. List of types is kept as comments in globals.py,
        but for performance reasons just hardcode it here.
        :return:
        """
        return 65653

    def grow(self):
        """


        """
        self._radius += self._step_size
        self.setRect(-self._radius, -self._radius, 2 * self._radius, 2 * self._radius)

    def shrink(self):
        """


        """
        self.radius -= self.step_size
        self.setRect(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)

