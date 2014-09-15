# coding=utf-8
# ############################################################################
#
# *** Kataja - Biolinguistic Visualization tool ***
#
# Copyright 2013 Jukka Purma
#
# This file is part of Kataja.
#
# Kataja is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Kataja is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kataja.  If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################

from PyQt5 import QtGui, QtCore
from PyQt5.QtGui import QPixmap

from kataja.singletons import ctrl

class TwoColorIconEngine(QtGui.QIconEngine):
    """

    """

    def __init__(self, bitmaps=None, paint_method=None, owner=None):
        QtGui.QIconEngine.__init__(self)
        self.mono = True
        self.bitmap = None
        self.filter1 = None
        self.filter2 = None
        self.mask = None
        self.paint_method = paint_method
        self.owner = owner

        if bitmaps:
            self.addPixmap(bitmaps)

    def pixmap(self, QSize, QIcon_Mode=None, QIcon_State=None):
        pm = QtGui.QIconEngine.pixmap(self, QSize, QIcon_Mode, QIcon_State)
        if self.mask:
            pm.setMask(QtGui.QBitmap(self.mask.scaled(QSize, QtCore.Qt.KeepAspectRatio)))
        return pm


    def addPixmap(self, bitmaps):
        """

        :type bitmaps:
        """
        if isinstance(bitmaps, str):
            bitmaps = QtGui.QPixmap(bitmaps)

        if isinstance(bitmaps, tuple):
            self.mono = False
            self.bitmap = bitmaps[0]
            self.filter1 = bitmaps[1]
            self.filter2 = bitmaps[2]
            self.mask = self.bitmap.mask()

        elif isinstance(bitmaps, QtGui.QPixmap):
            self.mono = True
            self.bitmap = bitmaps
            self.filter1 = None
            self.filter2 = None
            self.mask = self.bitmap.mask()


    #@caller
    def paint(self, painter, rect, mode, state):
        """

        :param painter:
        :param rect:
        :param mode:
        :param state:
        """
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        c = ctrl.cm.ui()
        if mode == 0:  # normal
            painter.setPen(c)
        elif mode == 1:  # disabled
            painter.setPen(ctrl.cm.inactive(c))
        elif mode == 2:  # hovering
            painter.setPen(ctrl.cm.hovering(c))
        elif mode == 3:  # selected
            painter.setPen(ctrl.cm.active(c))
        else:
            painter.setPen(c)
            print('Weird button mode: ', mode)
        #
        #print(painter.backgroundMode(), painter.background(), QtCore.Qt.OpaqueMode, QtCore.Qt.TransparentMode)
        #

        if self.paint_method:
            #painter.setBackgroundMode(QtCore.Qt.OpaqueMode)
            #painter.setBackground(ctrl.cm.paper())
            painter.fillRect(rect, ctrl.cm.paper2())
            #b = painter.background()
            self.paint_method(painter, rect, self.owner.pen(), self.owner.brush())
        else:
            if self.mono:
                painter.drawPixmap(rect, self.mask)
            else:
                painter.drawPixmap(rect, self.filter1)
                painter.setPen(c.darker())
                painter.drawPixmap(rect, self.filter2)


