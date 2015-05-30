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

import math

from PyQt5 import QtCore, QtGui, QtWidgets

from PyQt5.QtCore import QPointF as Pf, Qt
from kataja.singletons import ctrl
import kataja.utils as utils


class EdgeLabel(QtWidgets.QGraphicsTextItem):
    def __init__(self, text, parent=None, placeholder=False):
        QtWidgets.QGraphicsTextItem.__init__(self, text, parent=parent)
        self.draggable = not placeholder
        self.selectable = True
        self.clickable = True
        self.placeholder = placeholder
        self.selected = False
        self._size = self.boundingRect().size()
        self._local_drag_handle_position = None
        self.setFont(self.parentItem().font)
        self.setDefaultTextColor(self.parentItem().color)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

    def magnet_positions(self):
        w = self._size.width() / 2.0
        h = self._size.height() / 2.0
        return [(0, 0), (w, 0), (w + w, 0), (0, h), (w + w, h), (0, h + h), (w, h + h), (w + w, h + h)]

    def drag(self, event):
        if self.placeholder:
            return
        if not self._local_drag_handle_position:
            self._local_drag_handle_position = self.mapFromScene(event.buttonDownScenePos(Qt.LeftButton))
        self.compute_angle_for_pos(event.scenePos(), self._local_drag_handle_position)
        self.update()

    def being_dragged(self):
        return self._local_drag_handle_position

    def drop_to(self, x, y, recipient=None):
        self._local_drag_handle_position = None

    def click(self, event):
        p = self.parentItem()
        if p and ctrl.is_selected(p):
            ctrl.ui.start_edge_label_editing(self.parentItem())
        else:
            p.select(event)

    def select(self, event, multi=False):
        self.click(event)

    def update_text(self, value):
        self.setPlainText(value)
        self._size = self.boundingRect().size()
        if value:
            self.placeholder = False
            self.draggable = True
        p = self.parentItem()
        if p:
            p.refresh_selection_status(ctrl.is_selected(p))

    def find_closest_magnet(self, top_left, start_pos):
        spx, spy = start_pos.x(), start_pos.y()
        tlx, tly = top_left.x(), top_left.y()
        smallest_d = 10000
        closest_magnet = None
        for x, y in self.magnet_positions():
            d = abs((tlx + x) - spx) + abs((tly + y) - spy)
            if d < smallest_d:
                smallest_d = d
                closest_magnet = (x, y)
        return closest_magnet

    def find_suitable_magnet(self, start_pos, end_pos):
        spx, spy = start_pos.x(), start_pos.y()
        epx, epy = end_pos.x(), end_pos.y()
        dx = spx - epx
        dy = spy - epy
        angle = math.degrees(math.atan2(dy, dx)) + 180
        if angle < 22.5 or angle >= 327.5:
            i = 3  # left middle
        elif 22.5 <= angle < 67.5:
            i = 0  # left top
        elif 67.5 <= angle < 112.5:
            i = 1  # center top
        elif 112.5 <= angle < 147.5:
            i = 2  #
        elif 147.5 <= angle < 202.5:
            i = 4
        elif 202.5 <= angle < 247.5:
            i = 7
        elif 247.5 <= angle < 292.5:
            i = 6
        elif 292.5 <= angle < 327.5:
            i = 5
        return self.magnet_positions()[i]

    def compute_magnet(self, rad_angle):
        s = self._size
        if self.being_dragged() or True:
            return Pf(0, 0)
        angle = math.degrees(rad_angle)
        if angle > 315 or angle <= 45:
            # left middle
            return Pf(0, s.height() / 2)
        elif 45 < angle <= 135:
            # center top
            return Pf(s.width() / 2, 0)
        elif 135 < angle <= 225:
            # right middle
            return Pf(s.width(), s.height() / 2)
        elif 225 < angle <= 315:
            # center bottom
            return Pf(s.width() / 2, s.height())

    def compute_angle_for_pos(self, event_pos, adjustment):
        """

        :param top_left:
        """
        edge = self.parentItem()
        start_pos, end_point = edge.get_label_line_positions()
        # closest_magnet = self.find_closest_magnet(top_left, start_pos)
        # line_x = top_left.x() + closest_magnet[0] - start_pos.x()
        # line_y = top_left.y() + closest_magnet[1] - start_pos.y()
        line_x = event_pos.x() - start_pos.x()
        line_y = event_pos.y() - start_pos.y()
        rad = math.atan2(line_y, line_x)
        edge_angle = (360 - edge.get_angle_at(edge.label_start))
        my_angle = math.degrees(rad)
        if my_angle < 0:
            my_angle += 360
        a1 = my_angle - edge_angle
        a2 = my_angle - edge_angle + 360
        if abs(a1) < abs(a2):
            new_angle = a1
        else:
            new_angle = a2
        edge.label_angle = new_angle
        edge.label_dist = math.hypot(line_x, line_y)
        ctrl.ui.update_control_point_positions()

    def paint(self, QPainter, QStyleOptionGraphicsItem, QWidget):
        if self.being_dragged():
            # p = QtGui.QPen(ctrl.cm.ui_tr())
            # p.setWidthF(0.5)
            # QPainter.setPen(p)
            pos = self.pos()
            sp, end_point = self.parentItem().get_label_line_positions()
            ex, ey = utils.to_tuple(self.mapFromScene(pos))
            epx, epy = utils.to_tuple(self.mapFromScene(end_point))
            sx, sy = utils.to_tuple(self.mapFromScene(sp))
            # for mx, my in self.magnet_positions():
            # QPainter.drawLine(sx, sy, ex + mx, ey + my)
            mx, my = self.find_closest_magnet(pos, sp)
            p = QtGui.QPen(ctrl.cm.ui_tr())
            p.setWidthF(0.5)
            QPainter.setPen(p)
            QPainter.drawLine(sx, sy, ex + mx, ey + my)
            QPainter.drawLine(sx, sy, epx, epy)
            p = QtGui.QPen(ctrl.cm.ui_tr())
            p.setWidthF(2.0)
            QPainter.setPen(p)
            QPainter.drawEllipse(self.mapFromScene(end_point), 4, 4)

        if self.selected:
            p = QtGui.QPen(ctrl.cm.ui_tr())
            p.setWidthF(0.5)
            QPainter.setPen(p)
            QPainter.drawRect(self.boundingRect())
        QtWidgets.QGraphicsTextItem.paint(self, QPainter, QStyleOptionGraphicsItem, QWidget)


