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

from PyQt5 import QtCore
from PyQt5.QtCore import QPointF as Pf
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
from kataja.Edge import Edge
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.utils import to_tuple
import kataja.globals as g


end_spot_size = 7


class TouchArea(QtWidgets.QGraphicsItem):
    """ Mouse sensitive areas connected to either nodes or edges between them. """

    @staticmethod
    def create_key(host, type):
        """

        :param host:
        :param type:
        :return:
        """
        return 'touch_area_%s_%s' % (type, host.save_key)

    def __init__(self, host, type):
        """

        :param ConstituentNode host:
        :param boolean left:
        :param boolean top:
        """

        QtWidgets.QGraphicsItem.__init__(self)
        self._dragging = False
        self.host = host
        self._path = None
        self.start_point = None
        self.end_point = None
        self.setZValue(200)
        self.type = type
        # Drawing flags defaults
        self._align_left = False
        self._has_tail = True
        self._shape_has_joint = False
        # Drawing flags for each touch area type
        if self.type is g.LEFT_ADD_ROOT:
            self.status_tip = "Add new constituent to left of %s" % self.host
            self._align_left = True
            self._shape_has_joint = True
        elif self.type is g.RIGHT_ADD_ROOT:
            self.status_tip = "Add new constituent to right of %s" % self.host
            self._shape_has_joint = True
        elif self.type is g.LEFT_ADD_SIBLING:
            self.status_tip = "Add new sibling to left of %s" % self.host.end
            self._align_left = True
        elif self.type is g.RIGHT_ADD_SIBLING:
            self.status_tip = "Add new sibling to right of %s" % self.host.end
        elif self.type is g.TOUCH_ADD_CONSTITUENT:
            self.status_tip = "Add a constituent here"
            self._has_tail = False
        else:
            self.status_tip = "Unknown touch area???"
        self.selectable = False
        self.focusable = True
        self.draggable = True
        self.clickable = True
        self._visible = True
        self._hovering = False
        self._drag_hint = False
        self.key = TouchArea.create_key(host, type)
        self.update_end_points()
        self.setCursor(QtCore.Qt.PointingHandCursor)
        self.setAcceptHoverEvents(True)
        self._fill_path = False
        self.setToolTip(self.status_tip)


    def is_visible(self):
        """


        :return:
        """
        return self._visible

    def boundingRect(self):
        """


        :return:
        """
        if self._has_tail:
            # Bounding rect that includes the tail and end spot ellipse
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
            if self._shape_has_joint:
                return r.united(self._path.controlPointRect())
            else:
                return r
        else:
            # Just the bounding rect of end spot ellipse
            ex, ey = self.end_point
            return QtCore.QRectF(ex - end_spot_size, ey - end_spot_size, end_spot_size + end_spot_size, end_spot_size + end_spot_size)

    def sensitive_area(self):
        """


        :return:
        """
        return self.boundingRect()

    def update_position(self):
        """


        """
        pass
        #if not self in ctrl.dragged:
        #    self.update_end_points()

    def drag(self, event):
        self._dragging = True
        self.update_end_points(end_point=to_tuple(event.scenePos()))

    def drop_to(self, x, y, recipient=None):
        self._dragging = False
        print(x,y, recipient)

    # edge.py
    def update_end_points(self, end_point=None):
        # start
        """

        :param end_point: End point can be given or it can be calculated.
        """
        if not self._has_tail:
            if end_point:
                self.end_point = end_point
            elif isinstance(self.host, Edge):
                self.end_point = (self.host.end_point[0], self.host.end_point[1])
            elif hasattr(self.host, 'get_current_position'):
                self.end_point = (self.host.get_current_position()[0], self.host.get_current_position()[1])
            self.start_point = self.end_point
            self._path = None
            return
        use_middle_point = False
        line_middle_point = None
        path_settings = None
        if isinstance(self.host, Edge): # Touch area starts from relation between nodes
            rel = self.host
            path_settings = ctrl.forest.settings.edge_shape_settings(rel.edge_type)
            sx, sy = to_tuple(rel.get_point_at(0.5))
            self.start_point = sx, sy
            if end_point:
                self.end_point = end_point
            else:
                d = rel.get_angle_at(0.5)
                if self._align_left:
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
        elif self._shape_has_joint:
            path_settings = ctrl.forest.settings.edge_shape_settings(g.CONSTITUENT_EDGE)
            sx, sy, dummy = self.host.magnet(2)
            self.start_point = sx, sy
            if end_point:
                self.end_point = end_point
            else:
                if self._align_left:
                    self.end_point = sx - max((prefs.edge_width * 2, self.host.width)), sy
                else:
                    self.end_point = sx + max((prefs.edge_width * 2, self.host.width)), sy
            use_middle_point = True
            line_middle_point = sx - (0.5 * (sx - self.end_point[0])), sy - 10
        else:
            print("What is this toucharea?", self, " connected to ", self.host)
        shape_method = path_settings['method']
        self._fill_path = path_settings.get('fill', False)

        if use_middle_point:
            mp = line_middle_point[0], line_middle_point[1], 0
            adjust = []
            if self._align_left:
                sp = self.start_point[0], self.start_point[1], 0
                ep = self.end_point[0], self.end_point[1], 0
            else:
                ep = self.start_point[0], self.start_point[1], 0
                sp = self.end_point[0], self.end_point[1], 0

            self._path, true_path, control_points = shape_method(mp, sp, align=g.RIGHT, adjust=adjust, **path_settings)
            self._path.moveTo(sp[0], sp[1])
            path2, true_path, control_points = shape_method(mp, ep, align=g.LEFT, adjust=adjust, **path_settings)
            self._path = self._path.united(path2)

        else:
            sp = self.start_point[0], self.start_point[1], 0
            ep = self.end_point[0], self.end_point[1], 0
            adjust = []
            if self._align_left:
                align = g.LEFT
            else:
                align = g.RIGHT
            self._path, true_path, control_points = shape_method(sp, ep, align=align, adjust=adjust, **path_settings)


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
        print('---- dropped node to touch area -----')
        # if not isinstance(dropped_node, ConstituentNode):
        # return False
        f.undo_manager.record('re-merge constituent')
        if isinstance(self.host, Edge):
            print('calling replace_node_with_merged_node from edge')
            f.replace_node_with_merged_node(self.host.end, dropped_node, edge=self.host, merge_to_left=self._align_left,
                                            merger_node_pos=None)
        else:
            print('calling replace_node_with_merged_node')
            f.replace_node_with_merged_node(self.host, dropped_node, None, merge_to_left=self._align_left,
                                            merger_node_pos=self.start_point)


    def click(self, event=None):
        """
        :type event: QMouseEvent
        :type forest: Forest
        Creates a new node, edge to host depends on which merge area was clicked
         """
        f = self.host.forest
        self._dragging = False
        if self._drag_hint:
            return False
        f.undo_manager.record('add constituent')
        edge = None
        node = self.host
        if hasattr(self.host, 'end'):
            edge = self.host
            node = self.host.end
        if self.type is g.TOUCH_ADD_CONSTITUENT:
            node.open_embed()
        else:
            f.replace_node_with_merged_empty_node(node=node, edge=edge, merge_to_left=self._align_left,
                                              new_node_pos=self.end_point, merger_node_pos=self.start_point)
            ctrl.deselect_objects()
        return True

    # self, N, R, merge_to_left, new_node_pos, merger_node_pos):

    def calculate_if_can_merge(self, dragged, root, node_list):
        """

        :param dragged:
        :param root:
        :param node_list:
        :return:
        """
        host = self.host
        if host == dragged:
            return False
        elif host in ctrl.dragged:
            return False
        elif host is ctrl.pressed:
            return False
        return True


    def dragged_over_by(self, dragged):
        if not self._hovering and self.accepts_drops(dragged):
            if ctrl.latest_hover and not ctrl.latest_hover is self:
                ctrl.latest_hover.set_hovering(False)
            ctrl.latest_hover = self
            self.set_hovering(True)


    def accepts_drops(self, dragged):
        return self.calculate_if_can_merge(dragged, None, None)


    def set_hovering(self, value):
        """

        :param value:
        """
        if value and not self._hovering:
            self._hovering = True
            ctrl.set_status(self.status_tip)

        elif (not value) and self._hovering:
            self._hovering = False
            ctrl.remove_status(self.status_tip)
        self.update()

    def hoverEnterEvent(self, event):
        """

        :param event:
        """
        if (not self._hovering) and not ctrl.pressed:
            self.set_hovering(True)
        QtWidgets.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """

        :param event:
        """
        if self._hovering:
            self.set_hovering(False)
        QtWidgets.QGraphicsItem.hoverLeaveEvent(self, event)


    def paint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        :raise:
        """
        if ctrl.pressed == self:
            pass

        if self._hovering:
            c = ctrl.cm.hovering(ctrl.cm.ui())
        elif ctrl.is_selected(self):  # wrong colors, just testing
            print('cant select ui toucharea')
            c = ctrl.cm.selection()
        else:
            c = ctrl.cm.ui_tr()
        painter.setPen(c)
        if self._has_tail:
            if self._fill_path:
                painter.fillPath(self._path, c)
            else:
                painter.drawPath(self._path)
            if self._hovering:
                painter.setBrush(ctrl.cm.paper())
                painter.drawEllipse(self.end_point[0] - end_spot_size + 1, self.end_point[1] - end_spot_size + 1,
                                    2 * end_spot_size, 2 * end_spot_size)
                painter.drawLine(self.end_point[0] - 1, self.end_point[1] + 1, self.end_point[0] + 3, self.end_point[1] + 1)
                painter.drawLine(self.end_point[0] + 1, self.end_point[1] - 1, self.end_point[0] + 1, self.end_point[1] + 3)
        else:
            painter.setBrush(ctrl.cm.paper())
            painter.drawEllipse(self.end_point[0] - end_spot_size + 1, self.end_point[1] - end_spot_size + 1,
                                2 * end_spot_size, 2 * end_spot_size)
            if self._hovering:
                painter.drawLine(self.end_point[0] - 1, self.end_point[1] + 1, self.end_point[0] + 3, self.end_point[1] + 1)
                painter.drawLine(self.end_point[0] + 1, self.end_point[1] - 1, self.end_point[0] + 1, self.end_point[1] + 3)

