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

from kataja.singletons import ctrl, qt_prefs
import kataja.utils as utils
import kataja.globals as g
from kataja.uniqueness_generator import next_available_type_id


class ArrowLabel(QtWidgets.QGraphicsTextItem):
    __qt_type_id__ = next_available_type_id()

    def __init__(self, text, parent=None, placeholder=False):
        """ ArrowLabel takes care of (optional) label for the edge and related UI. All of the data
        required is stored at label_data -dict of host. This dict is saved with Edge,
        but ArrowLabels are always created anew.

        :param text:
        :param parent:
        :param placeholder:
        """
        QtWidgets.QGraphicsTextItem.__init__(self, text, parent=parent)
        self._host = self.parentItem()
        self.placeholder = placeholder
        w = self.document().idealWidth()
        if w > 200:
            self.setTextWidth(200)
        else:
            self.setTextWidth(-1)
        self._size = self.boundingRect().size()
        self._local_drag_handle_position = None
        self._label_start_pos = None
        self.setFont(self.get_font())
        self.setDefaultTextColor(self.parentItem().color)
        self.setFlag(QtWidgets.QGraphicsObject.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsObject.ItemIsSelectable)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

    @property
    def label_text(self):
        return self._host.get_label_text()

    @label_text.setter
    def label_text(self, value):
        self._host.set_label_text(value)

    def get_font(self):
        """ Font is the font used for label. What is stored is the kataja internal font name,
        but what is returned here is the actual QFont.
        :return: QFont instance
        """
        font_id = ctrl.settings.get_node_setting('font_id', node_type=g.COMMENT_NODE)
        return qt_prefs.get_font(font_id or g.MAIN_FONT)

    @property
    def font_name(self):
        """ Font is the font used for label. This returns the kataja internal font name.
        :return:
        """
        return ctrl.settings.get_node_setting('font_id', node_type=g.COMMENT_NODE) or g.MAIN_FONT

    @font_name.setter
    def font_name(self, value=None):
        """ Font is the font used for label. This sets the font name to be used.
        :param value: string (font name).
        """
        # This shouldn't be used
        pass

    @property
    def label_start(self):
        """
        label's startpoint in length of an edge (from 0 to 1.0)
        """
        return self._host.label_data.get('start_at', 0.2)

    @label_start.setter
    def label_start(self, value):
        """ label's startpoint in length of an edge (from 0 to 1.0)
        :param value: float (0 - 1.0)
        """
        self._host.poke('label_data')
        self._host.label_data['start_at'] = value
        self.update_position()
        self._host.call_watchers('edge_label_adjust', 'start_at', value)

    def update_position(self):
        """ Compute and set position for edge label. Make sure that path is
        up to date before doing this.
        :return:
        """
        start, end = self.get_label_line_positions()
        mx, my = self.find_suitable_magnet(start, end)
        label_pos = end - QtCore.QPointF(mx, my)
        self._label_start_pos = start
        self.setPos(label_pos)

    def get_label_start_pos(self):
        if not self._label_start_pos:
            self.update_position()
        return self._label_start_pos

    @property
    def label_angle(self):
        """
        label's angle relative to edge where it is attached
        """
        return self._host.label_data.get('angle', 90)

    @label_angle.setter
    def label_angle(self, value):
        """
        label's angle relative to edge where it is attached
        :param value:
        """
        self._host.poke('label_data')
        self._host.label_data['angle'] = value
        self.update_position()
        self._host.call_watchers('edge_label_adjust', 'angle', value)

    @property
    def label_dist(self):
        """
        label's distance from edge
        """
        return self._host.label_data.get('dist', 12)

    @label_dist.setter
    def label_dist(self, value):
        """
        label's distance from edge
        :param value:
        """
        self._host.poke('label_data')
        self._host.label_data['dist'] = value
        self.update_position()
        self._host.call_watchers('edge_label_adjust', 'dist', value)

    def magnet_positions(self):
        w = self._size.width() / 2.0
        h = self._size.height() / 2.0
        return [(0, 0), (w, 0), (w + w, 0), (0, h), (w + w, h), (0, h + h), (w, h + h),
                (w + w, h + h)]

    def drag(self, event):
        """
        :param event:
        :return:
        """
        if self.placeholder:
            return
        if not self._local_drag_handle_position:
            self._local_drag_handle_position = self.mapFromScene(
                event.buttonDownScenePos(Qt.LeftButton))
        self.compute_angle_for_pos(event.scenePos(), self._local_drag_handle_position)
        self.update()

    def kill_dragging(self):
        self._local_drag_handle_position = None

    def being_dragged(self):
        return self._local_drag_handle_position

    def drop_to(self, x, y, recipient=None, shift_down=False):
        self._local_drag_handle_position = None

    def mousePressEvent(self, event):
        ctrl.press(self)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if ctrl.pressed is self:
            if self.being_dragged() or (event.buttonDownScenePos(
                    QtCore.Qt.LeftButton) - event.scenePos()).manhattanLength() > 6:
                self.drag(event)
                ctrl.graph_scene.dragging_over(event.scenePos())

    def mouseReleaseEvent(self, event):
        if ctrl.pressed is self:
            ctrl.release(self)
            if self.being_dragged():
                self.kill_dragging()
            else:  # This is regular click on 'pressed' object
                self.click(event)
                self.update()
            return None  # this mouseRelease is now consumed
        super().mouseReleaseEvent(event)

    def click(self, event):
        if self._host and self._host.selected:
            ctrl.ui.start_arrow_label_editing(self._host)
        else:
            adding = event.modifiers() == Qt.ShiftModifier
            self._host.select(adding=adding, select_area=False)

    def select(self, adding=False, select_area=False):
        if self._host and self._host.selected:
            ctrl.ui.start_arrow_label_editing(self._host)
        else:
            return self._host.select(adding=adding, select_area=select_area)

    def get_label_line_positions(self):
        """ When editing edge labels, there is a line connecting the edge to
        label. This one provides the
        end- and start points for such line.
        :return: None
        """
        start = self._host.path.get_point_at(self.label_start)
        angle = (360 - self._host.path.get_angle_at(self.label_start)) + self.label_angle
        if angle > 360:
            angle -= 360
        if angle < 0:
            angle += 360
        angle = math.radians(angle)
        end_x = start.x() + (self.label_dist * math.cos(angle))
        end_y = start.y() + (self.label_dist * math.sin(angle))
        end = QtCore.QPointF(end_x, end_y)
        return start, end

    def update_text(self, value):
        self.setPlainText(value)
        w = self.document().idealWidth()
        if w > 200:
            self.setTextWidth(200)
        else:
            self.setTextWidth(-1)
        self._size = self.boundingRect().size()
        if value:
            self.placeholder = False

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
        edge = self._host
        start_pos, end_point = self.get_label_line_positions()
        # closest_magnet = self.find_closest_magnet(top_left, start_pos)
        # line_x = top_left.x() + closest_magnet[0] - start_pos.x()
        # line_y = top_left.y() + closest_magnet[1] - start_pos.y()
        line_x = event_pos.x() - start_pos.x()
        line_y = event_pos.y() - start_pos.y()
        rad = math.atan2(line_y, line_x)
        edge_angle = (360 - edge.path.get_angle_at(self.label_start))
        my_angle = math.degrees(rad)
        if my_angle < 0:
            my_angle += 360
        a1 = my_angle - edge_angle
        a2 = my_angle - edge_angle + 360
        if abs(a1) < abs(a2):
            new_angle = a1
        else:
            new_angle = a2
        self.label_angle = new_angle
        self.label_dist = math.hypot(line_x, line_y)
        ctrl.call_watchers(edge, 'edge_label_adjust', 'adjustment', adjustment)

    def paint(self, QPainter, QStyleOptionGraphicsItem, QWidget):
        if self.being_dragged():
            # p = QtGui.QPen(ctrl.cm.ui_tr())
            # p.setWidthF(0.5)
            # QPainter.setPen(p)
            pos = self.pos()
            sp, end_point = self.get_label_line_positions()
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

        if self._host.selected:
            p = QtGui.QPen(ctrl.cm.ui_tr())
            p.setWidthF(0.5)
            QPainter.setPen(p)
            QPainter.drawRect(self.boundingRect())
        self.setDefaultTextColor(self.parentItem().color)
        QtWidgets.QGraphicsTextItem.paint(self, QPainter, QStyleOptionGraphicsItem, QWidget)
