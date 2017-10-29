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

from kataja.singletons import ctrl, qt_prefs, prefs
import kataja.globals as g
import kataja.utils as utils
from kataja.uniqueness_generator import next_available_type_id


class GroupLabel(QtWidgets.QGraphicsTextItem):
    __qt_type_id__ = next_available_type_id()

    def __init__(self, text, parent=None):
        """ GroupLabel takes care of (optional) label for groups and related UI. All of the data
        required is stored at label_data -dict of host. This dict is saved with Group,
        but GroupLabels are always created anew.

        :param text:
        :param parent:
        """
        QtWidgets.QGraphicsTextItem.__init__(self, text, parent=parent)
        self._host = self.parentItem()
        self.selected = False
        self.automatic_position = True
        w = self.document().idealWidth()
        if w > 200:
            self.setTextWidth(200)
        else:
            self.setTextWidth(-1)
        self._size = self.boundingRect().size()
        self._w2 = self._size.width() / 2
        self._h2 = self._size.height() / 2
        self._local_drag_handle_position = None
        self._label_start_pos = None
        self.setFont(self.get_font())
        self.setFlag(QtWidgets.QGraphicsObject.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsObject.ItemIsSelectable)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.update_color()

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

    def set_label_data(self, key, value):
        self._host.poke('label_data')
        self._host.label_data[key] = value

    def get_label_data(self, key):
        self._host.label_data.get(key, None)

    @property
    def label_text(self):
        return self._host.get_label_text()

    @label_text.setter
    def label_text(self, value):
        self._host.set_label_text(value)

    def get_font(self):
        """ Font is the font used for label. What is stored is the kataja
        internal font name, but what is returned here is the actual QFont.
        :return: QFont instance
        """
        return qt_prefs.get_font(self.get_label_data('font') or g.MAIN_FONT)

    @property
    def font_name(self):
        """ Font is the font used for label. This returns the kataja internal font name.
        :return:
        """
        return self.get_label_data('font') or g.MAIN_FONT

    @font_name.setter
    def font_name(self, value=None):
        """ Font is the font used for label. This sets the font name to be used.
        :param value: string (font name).
        """
        self.set_label_data('font', value)

    def update_position(self):
        """ Compute and set position for group label. Make sure that path is
        up to date before doing this.
        :return:
        """
        start, end = self.get_label_line_positions()
        self._label_start_pos = start
        self.setPos(end - QtCore.QPointF(self._w2, self._h2))

    def update_color(self):
        self.setDefaultTextColor(self.parentItem().color)

    def get_label_start_pos(self):
        if not self._label_start_pos:
            self.update_position()
        return self._label_start_pos

    @property
    def label_angle(self):
        """
        label's angle to group blob
        """
        return self._host.label_data.get('angle', 90)

    @label_angle.setter
    def label_angle(self, value):
        """
        label's angle to group blob
        :param value:
        """

        if self.set_label_data('angle', value):
            self.update_position()

    @property
    def label_dist(self):
        """
        label's distance from group
        """
        return self._host.label_data.get('dist', 12)

    @label_dist.setter
    def label_dist(self, value):
        """
        label's distance from group
        :param value:
        """
        if self.set_label_data('dist', value):
            self.update_position()

    @property
    def automatic_position(self):
        """ Try to find the best suitable position for label.
        If false, user has dragged this to place.

        :return:
        """
        return self._host.label_data.get('automatic_position', False)

    @automatic_position.setter
    def automatic_position(self, value):
        """ Try to find the best suitable position for label.
        If false, user has dragged this to place.

        :return:
        """
        self.set_label_data('automatic_position', value)

    def drag(self, event):
        """
        :param event:
        :return:
        """
        if not self._local_drag_handle_position:
            self._local_drag_handle_position = self.mapFromScene(
                event.buttonDownScenePos(Qt.LeftButton))
        self.compute_angle_for_pos(event.scenePos(), self._local_drag_handle_position)
        self.update_position()

    def being_dragged(self):
        return self._local_drag_handle_position

    def kill_dragging(self):
        self.automatic_position = False
        self._local_drag_handle_position = None

    def drop_to(self, x, y, recipient=None, shift_down=False):
        self.automatic_position = False
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
        if self._host and ctrl.is_selected(self._host):
            ctrl.ui.start_group_label_editing(self._host)
        else:
            adding = event.modifiers() == Qt.ShiftModifier
            self._host.select(adding=adding, select_area=False)

    def select(self, adding=False, select_area=False):
        if self._host and ctrl.is_selected(self._host):
            ctrl.ui.start_group_label_editing(self._host)
        else:
            return self._host.select(adding=adding, select_area=select_area)

    def get_label_line_positions(self):
        """ When editing group labels, there is a line connecting the group to
        label. This one provides the
        end- and start points for such line.
        :return: None
        """
        start_x, start_y = self._host.center_point
        angle = math.radians(self.label_angle)
        end_x = start_x + (self.label_dist * math.cos(angle))
        end_y = start_y + (self.label_dist * math.sin(angle))
        end = QtCore.QPointF(end_x, end_y)
        return QtCore.QPointF(start_x, start_y), end

    def update_text(self, value):
        self.setPlainText(value)
        w = self.document().idealWidth()
        if w > 200:
            self.setTextWidth(200)
        else:
            self.setTextWidth(-1)
        self._size = self.boundingRect().size()
        self._w2 = self._size.width() / 2
        self._h2 = self._size.height() / 2
        if self._host:
            self._host.update_selection_status(ctrl.is_selected(self._host))

    def compute_angle_for_pos(self, event_pos, adjustment=None):
        """

        :param top_left:
        """
        if adjustment:
            epos = event_pos - adjustment + QtCore.QPointF(self._w2, self._h2)
        else:
            epos = event_pos + QtCore.QPointF(self._w2, self._h2)
        start_pos, end_point = self.get_label_line_positions()
        line_x = epos.x() - start_pos.x()
        line_y = epos.y() - start_pos.y()
        rad = math.atan2(line_y, line_x)
        my_angle = math.degrees(rad)
        if my_angle < 0:
            my_angle += 360
        self.set_label_data('angle', my_angle)
        self.set_label_data('dist', math.hypot(line_x, line_y))

    def position_at_bottom(self):
        cx, cy = self._host.center_point
        br = self._host.boundingRect()
        best_x = cx
        best_y = br.bottom() + 4
        self.prepareGeometryChange()
        self.setPos(best_x, best_y)
        self.compute_angle_for_pos(QtCore.QPointF(best_x, best_y))

    def compute_best_position_along_route(self, route):
        label_width = self._size.width()
        label_height = self._size.height()
        cx, cy = self._host.center_point

        min_dist = 100000
        prev_x, prev_y = route[-1]
        best_x, best_y = 0, 0
        for x, y in route:
            mx = (prev_x + x) / 2
            my = (prev_y + y) / 2
            d = (cx - mx) ** 2 + (cy - my) ** 2
            if d < min_dist:
                if mx < cx:
                    mx -= label_width + 2
                else:
                    mx += 2
                if my < cy:
                    my -= label_height + 2
                else:
                    my += 2
                items = ctrl.graph_scene.items(QtCore.QRectF(mx, my, label_width, label_height))
                if not items:
                    min_dist = d
                    best_x, best_y = mx, my
            prev_x, prev_y = x, y
        self.prepareGeometryChange()
        self.setPos(best_x, best_y)
        self.compute_angle_for_pos(QtCore.QPointF(best_x, best_y))

    def paint(self, QPainter, QStyleOptionGraphicsItem, QWidget):
        if self.being_dragged():
            sp, end_point = self.get_label_line_positions()
            ex, ey = utils.to_tuple(self.mapFromScene(end_point))
            sx, sy = utils.to_tuple(self.mapFromScene(sp))
            p = QtGui.QPen(ctrl.cm.ui_tr())
            p.setWidthF(0.5)
            QPainter.setPen(p)
            QPainter.drawLine(sx, sy, ex, ey)
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
