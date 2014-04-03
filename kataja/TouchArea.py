#############################################################################
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
#############################################################################

import math

from PyQt5 import QtCore

from kataja.Controller import ctrl, prefs, qt_prefs, colors
from kataja.utils import to_tuple
from PyQt5.QtCore import QPointF as Pf
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets


end_spot_size = 7


class TouchArea(QtWidgets.QGraphicsItem):
    """ Mouse sensitive areas connected to either nodes or edges between them. """

    @staticmethod
    def create_key(host, place):
        return 'touch_area_%s_%s' % (place, host.save_key)

    def __init__(self, host, place, drag_mode=False):
        """

        :param ConstituentNode host:
        :param boolean left:
        :param boolean top:
        """

        QtWidgets.QGraphicsItem.__init__(self)
        self.host = host
        self._path = None
        self.start_point = 0, 0
        self.end_point = 0, 0
        self.setZValue(20)
        self.place = place
        self.left = 'left' in place
        self._shape_is_arc = 'top' in place
        self.selectable = False
        self.focusable = True
        self.draggable = False
        self.clickable = True
        self._visible = True
        self._hovering = False
        self._drag_hint = False
        self.drag_mode = drag_mode
        self.update_end_points()
        self.key = TouchArea.create_key(host, place)
        intern(self.key)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.setAcceptHoverEvents(True)


    def is_visible(self):
        return self._visible

    def boundingRect(self):
        ex, ey = self.end_point
        sx, sy = self.start_point
        e2 = end_spot_size * 2
        if sx < ex:
            w = max((ex - sx + end_spot_size, e2))
            x = min((sx, ex - end_spot_size))
        else:
            w = max((sx - ex + end_spot_size, e2))
            x = ex - end_spot_size
        if sy < ey:
            h = max((ey - sy + end_spot_size, e2))
            y = min((sy, ey - end_spot_size))
        else:
            h = max((sy - ey + end_spot_size, e2))
            y = ey - end_spot_size
        r = QtCore.QRectF(x, y, w, h)
        if self._shape_is_arc:
            return r.united(self._path.controlPointRect())
        else:
            return r

    def sensitive_area(self):
        return self.boundingRect()

    def update_position(self):
        self.update_end_points()

    # edge.py
    def update_end_points(self):
        # start
        if self.host.__class__.__name__ == 'Edge':
            rel = self.host
            # rel.get_path()
            # sx, sy = to_tuple(rel.get_point_at(0.5))
            sx, sy = to_tuple(rel.middle_point)
            self.start_point = sx, sy
            d = rel.get_angle_at(0.5)
            if self.left:
                d -= 75
            else:
                d += 75
            angle = math.radians(-d)
            dx = math.cos(angle)
            dy = math.sin(angle)
            l = 30
            x = sx + dx * l
            y = sy + dy * l
            self.end_point = x, y
            line_end_point = sx + dx * (l - 4), sy + dy * (l - 4)
            plus_point = x + dx * 2, y + dy * 2
            use_middle_point = False

        elif self._shape_is_arc:
            sx, sy, dummy = self.host.top_magnet()
            self.start_point = sx, sy
            if self.left:
                self.end_point = sx - max((prefs.edge_width * 2, self.host.width)), sy
                line_end_point = self.end_point[0] + 5, sy - 2
                plus_point = self.end_point[0] - 2, self.end_point[1]
            else:
                self.end_point = sx + max((prefs.edge_width * 2, self.host.width)), sy
                line_end_point = self.end_point[0] - 5, sy - 2
                plus_point = self.end_point[0] + 2, self.end_point[1]
            use_middle_point = True
            line_middle_point = sx - (0.5 * (sx - self.end_point[0])), sy - 10

        self._path = QtGui.QPainterPath(Pf(self.start_point[0], self.start_point[1]))
        if use_middle_point:
            self._path.lineTo(line_middle_point[0], line_middle_point[1])
        self._path.lineTo(line_end_point[0], line_end_point[1])
        #self._path.addEllipse(self.end_point[0] - end_spot_size, self.end_point[1] - end_spot_size, 2 * end_spot_size,
        #                      2 * end_spot_size)
        if self.drag_mode:
            self._path.addEllipse(plus_point[0] - 2, plus_point[1] - 2, 4, 4)
        else:
            self._path.moveTo(plus_point[0] - 2, plus_point[1])
            self._path.lineTo(plus_point[0] + 2, plus_point[1])
            self._path.moveTo(plus_point[0], plus_point[1] - 2)
            self._path.lineTo(plus_point[0], plus_point[1] + 2)

    def update_colors(self):
        self.setBrush(self.host.color)

    def __repr__(self):
        return '<toucharea %s>' % self.key

    def remove(self):
        """ remove item from the scene but otherwise keep it intact """
        sc = self.scene()
        if sc:
            sc.removeItem(self)


    def drop(self, dropped_node):
        """
        Connect dropped node to host of this TouchArea.
        Connection depends on which merge area this is:
        top left, top right, left, right
        :param dropped_node:
        """
        f = self.host.forest
        print '---- dropped node to touch area -----'
        # if not isinstance(dropped_node, ConstituentNode):
        #    return False
        f.undo_manager.record('re-merge constituent')
        if self.host.__class__.__name__ == 'Edge':
            print 'calling replace_node_with_merged_node from edge'
            f.replace_node_with_merged_node(self.host.end, dropped_node, left=self.left)
        else:
            print 'calling replace_node_with_merged_node'
            f.replace_node_with_merged_node(self.host, dropped_node, None, merge_to_left=self.left,
                                            merger_node_pos=self.start_point)


    def click(self, event=None):
        """
        :type event: QMouseEvent
        :type forest: Forest
        Creates a new node, edge to host depends on which merge area was clicked
         """
        f = self.host.forest
        if self._drag_hint:
            return False
        f.undo_manager.record('add constituent')
        if event:
            x, y = to_tuple(event.scenePos())
        else:
            x, y = to_tuple(self.boundingRect().center())
            ox, oy = to_tuple(self.pos())
            x, y = x + ox, y + oy
        if self.host.__class__.__name__ == 'Edge':
            print 'click on edge %s, end node: %s' % (self.host, self.host.end)
            f.replace_node_with_merged_empty_node(N=self.host.end, R=self.host, merge_to_left=self.left,
                                                  new_node_pos=self.end_point, merger_node_pos=self.start_point)
        else:
            f.replace_node_with_merged_empty_node(N=self.host, R=None, merge_to_left=self.left,
                                                  new_node_pos=self.end_point, merger_node_pos=self.start_point)
        ctrl.deselect_objects()
        return True

    # self, N, R, merge_to_left, new_node_pos, merger_node_pos):

    def calculate_if_can_merge(self, dragged, root, node_list):
        host = self.host
        if host == dragged:
            return False
        elif host in ctrl.dragged:
            return False
        elif host in ctrl.pressed:
            return False
        return True


    def toggle_hovering(self, value):
        if value and not self._hovering:
            self._hovering = True
        elif (not value) and self._hovering:
            self._hovering = False

    def hoverEnterEvent(self, event):
        if (not self._hovering) and not ctrl.pressed:
            self.toggle_hovering(True)
        QtWidgets.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        if self._hovering:
            self.toggle_hovering(False)
        QtWidgets.QGraphicsItem.hoverLeaveEvent(self, event)


    def paint(self, painter, option, widget):
        if ctrl.pressed == self:
            pass

        if self._hovering:
            painter.setBrush(colors.ui_hover)
            painter.setPen(qt_prefs.no_pen)
            painter.drawEllipse(self.end_point[0] - end_spot_size + 1, self.end_point[1] - end_spot_size + 1,
                                2 * end_spot_size, 2 * end_spot_size)
            painter.setBrush(qt_prefs.no_brush)
            painter.setPen(colors.ui)

        elif ctrl.is_selected(self):  # wrong colors, just testing
            print 'cant select ui toucharea'
            raise
            painter.setPen(colors.ui)
        self.update_end_points()
        # painter.drawRect(self.boundingRect()) # debug
        painter.drawPath(self._path)
        if self._hovering and ctrl.dragged:
            painter.setPen(colors.ui_hover)
            ex, ey = self.end_point
            painter.drawLine(ex, ey - 30, ex, ey + 30)
            painter.drawLine(ex - 30, ey, ex + 30, ey)

