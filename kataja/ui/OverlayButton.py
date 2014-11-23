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
from kataja.Forest import ForestError
from kataja.singletons import ctrl
import kataja.globals as g


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
        self.edge = None # kind of secondary host, required for some buttons that apply both to node (=host) and edge
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
        if self.role == 'remove_merger':
            adjust = QtCore.QPointF(19, self.host.height/2)
            if not self.edge:
                edges = [x for x in self.host.edges_down if x.edge_type is g.CONSTITUENT_EDGE and x.end.is_placeholder()]
                if not edges:
                    raise ForestError("How did I get here? Remove merger suggested for merger with no children")
                else:
                    self.edge = edges[0]
            p = ctrl.main.graph_view.mapFromScene(QtCore.QPointF(self.edge.start_point[0], self.edge.start_point[1])) - adjust
            p = p.toPoint()
        elif self.role == 'start_cut':
            adjust = QtCore.QPointF(self.host.end.width/2, self.host.end.height/2)
            p = ctrl.main.graph_view.mapFromScene(QtCore.QPointF(self.host.start_point[0], self.host.start_point[1]) + adjust)
        elif self.role == 'end_cut':
            if self.host.align == g.LEFT:
                adjust = QtCore.QPointF(-self.host.end.width/2, -self.host.end.height/2)
            else:
                adjust = QtCore.QPointF(self.host.end.width/2, -self.host.end.height/2)
            p = ctrl.main.graph_view.mapFromScene(QtCore.QPointF(self.host.start_point[0], self.host.start_point[1]) + adjust)
        self.move(p)

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