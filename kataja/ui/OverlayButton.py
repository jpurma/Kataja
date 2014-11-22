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

from PyQt5 import QtWidgets, QtGui, QtCore
from kataja.singletons import ctrl


class OverlayButton(QtWidgets.QPushButton):
    """ Buttons that change their color according to widget where they are.
        Currently this is not doing anything special that can't be done by setting TwoColorIconEngine for normal button,
        but let's keep this in case we need to deliver palette updates to icon engines.
     """

    def __init__(self, pixmap, host, role, text=None, parent=None, size=16):
        QtWidgets.QPushButton.__init__(self, parent)
        if text:
            self.setToolTip(text)
            self.setStatusTip(text)
        self.host = host
        self.role = role
        self._action = None
        self.setContentsMargins(0, 0, 0, 0)
        self.setIconSize(QtCore.QSize(size, size))
        self.setFlat(True)
        self.setIcon(QtGui.QIcon(pixmap))
        self.effect = QtWidgets.QGraphicsColorizeEffect(self)
        self.effect.setColor(ctrl.cm.ui())
        self.effect.setStrength(0.6)
        self.setGraphicsEffect(self.effect)
        self.just_triggered = False
        #self.setCursor(Qt.PointingHandCursor)

    def update_color(self):
        self.effect.colorChanged(ctrl.cm.ui())

    def event(self, e):
        if e.type() == QtCore.QEvent.PaletteChange:
            self.effect.setColor(ctrl.cm.ui())
        return QtWidgets.QPushButton.event(self, e)

    #def paintEvent(self, *args, **kwargs):
    #    self.effect.colorChanged(ctrl.cm.ui())
    #    QtWidgets.QPushButton.paintEvent(self, *args, **kwargs)

    def update_position(self):
        if self.role == 'start_cut' or self.role == 'remove_merger':
            adjust = QtCore.QPointF(19, 12)
            p = self.parent().mapFromScene(QtCore.QPoint(self.host.start_point[0], self.host.start_point[1])) - adjust
            self.move(p.toPoint())
        if self.role == 'end_cut':
            adjust = QtCore.QPointF(19, 12)
            p = self.parent().mapFromScene(QtCore.QPoint(self.host.end_point[0], self.host.end_point[1])) - adjust
            self.move(p.toPoint())

    def enterEvent(self, event):
        self.effect.setStrength(1.0)

    def leaveEvent(self, event):
        self.effect.setStrength(0.5)

    def connect_to_action(self, action):
        self._action = action
        self.clicked.connect(self.click_delegate)

    def click_delegate(self):
        print('in click delegate')
        self.just_triggered = True
        self._action.trigger()