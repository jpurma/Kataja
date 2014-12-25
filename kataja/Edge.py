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
import kataja.globals as g
from kataja.globals import LEFT, RIGHT, NO_ALIGN
from kataja.shapes import SHAPE_PRESETS, to_Pf, outline_stroker
from kataja.EdgeLabel import EdgeLabel
import kataja.utils as utils
from kataja.Saved import Savable

# ('shaped_relative_linear',{'method':shapedRelativeLinearPath,'fill':True,'pen':'thin'}),

angle_magnet_map = {0: 6, 1: 6, 2: 4, 3: 3, 4: 2, 5: 1, 6: 0, 7: 5, 8: 5, 9: 5, 10: 7, 11: 8, 12: 9, 13: 10, 14: 11,
                    15: 6, 16: 6}

atan_magnet_map = {-8: 5, -7: 5, -6: 0, -5: 1, -4: 2, -3: 3, -2: 4, -1: 6, 0: 6, 1: 6, 2: 11, 3: 10, 4: 9, 5: 8, 6: 7,
                   7: 5, 8: 5}


class Edge(Savable, QtWidgets.QGraphicsItem):
    """ Any connection between nodes: can be represented as curves, branches or arrows """

    receives_signals = [g.EDGE_SHAPES_CHANGED]

    def __init__(self, start=None, end=None, edge_type='', direction=''):
        """
        :param Node start:
        :param Node end:
        :param string edge_type:
        :param string direction:
        :param string restoring:
        """
        Savable.__init__(self)
        QtWidgets.QGraphicsItem.__init__(self)
        self.saved.fixed_start_point = None
        self.saved.fixed_end_point = None
        self.saved.edge_type = edge_type
        self.saved.adjust = None
        self.saved.align = direction #or NO_ALIGN
        self.saved.start = start
        self.saved.end = end
        self.saved.use_arrowheads = None
        self.saved.label_data = {}
        self.saved.local_shape_args = {}
        self.saved.color = None
        self.saved.shape_name = None
        self.saved.pull = None
        self.saved.visible = None

        self._computed_start_point = None
        self._computed_end_point = None

        self.control_points = []
        self._local_drag_handle_position = None
        self._arrowhead_at_start = None
        self._arrowhead_at_end = None

        # ## Adjustable values, defaults to ForestSettings if None for this element
        # based on the relation style

        # self.center_point = (0, 0, 0)

        # ## Derivative elements
        self._shape_method = None
        self._path = None
        self._true_path = None  # inner arc or line without the leaf effect
        self._fat_path = None
        self.selectable = True
        self.draggable = not (self.start or self.end)
        self.clickable = False
        self._hovering = False
        self.setZValue(10)
        self.status_tip = ""
        self._cached_shape_args = {}
        self.connect_end_points(start, end)
        self.arrowhead_size_at_start = 6
        self.arrowhead_size_at_end = 6
        self._arrow_cut_point_start = None
        self._arrow_cut_point_end = None
        self._arrowhead_start_path = None
        self._arrowhead_end_path = None

        self._use_labels = None
        self._label_text = None
        self.label_item = None
        self._label_rect = None
        self._relative_vector = None
        self._label_font = None  # inherited from settings
        self._cached_label_start = None
        # self.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        # self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        # self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.effect = utils.create_shadow_effect(ctrl.cm.selection())
        self.setGraphicsEffect(self.effect)

    def after_init(self):
        #print("after-initing edge ", self)
        self.update_end_points()

    @property
    def fixed_start_point(self):
        """
        :return:
        """
        return self.saved.fixed_start_point

    @fixed_start_point.setter
    def fixed_start_point(self, value):
        """
        :param value:
        """
        self.saved.fixed_start_point = value

    @property
    def fixed_end_point(self):
        """
        :return:
        """
        return self.saved.fixed_end_point

    @fixed_end_point.setter
    def fixed_end_point(self, value):
        """
        :param value:
        """
        self.saved.fixed_end_point = value


    @property
    def start_point(self):
        """
        :return:
        """
        if self.saved.start:
            return self._computed_start_point
        else:
            return self.saved.fixed_start_point

    @property
    def end_point(self):
        """
        :return:
        """
        if self.saved.end:
            return self._computed_end_point
        else:
            return self.saved.fixed_end_point

    @property
    def edge_type(self):
        """
        :return:
        """
        return self.saved.edge_type

    @edge_type.setter
    def edge_type(self, value):
        """
        :param value:
        """
        self.saved.edge_type = value

    @property
    def adjust(self):
        """
        :return:
        """
        return self.saved.adjust

    @adjust.setter
    def adjust(self, value):
        """
        :param value:
        """
        self.saved.adjust = value

    @property
    def align(self):
        """
        :return:
        """
        return self.saved.align

    @align.setter
    def align(self, value):
        """
        :param value:
        """
        self.saved.align = value

    @property
    def start(self):
        """
        :return:
        """
        return self.saved.start

    @start.setter
    def start(self, value):
        """
        :param value:
        """
        self.saved.start = value

    @property
    def end(self):
        """
        :return:
        """
        return self.saved.end

    @end.setter
    def end(self, value):
        """
        :param value:
        """
        self.saved.end = value

    @property
    def use_arrowheads(self):
        """
        :return:
        """
        return self.saved.use_arrowheads

    @use_arrowheads.setter
    def use_arrowheads(self, value):
        """
        :param value:
        """
        self.saved.use_arrowheads = value

    @property
    def label_data(self):
        """
        :return:
        """
        return self.saved.label_data

    @label_data.setter
    def label_data(self, value):
        """
        :param value:
        """
        if value is None:
            value = {}
        self.saved.label_data = value

    @property
    def label_text(self):
        """
        :return:
        """
        return self.saved.label_data.get('text', '')

    @label_text.setter
    def label_text(self, value=None):
        """
        :param value:
        :return:
        """
        self.saved.label_data['text'] = value
        if not self.label_item:
            self.label_item = EdgeLabel(value, parent=self)
        else:
            self.label_item.update_text(value)

    @property
    def font(self):
        """
        :return:
        """
        f_name = self.saved.label_data.get('font', None)
        if f_name:
            return qt_prefs.font(f_name)
        else:
            return qt_prefs.font(ctrl.forest.settings.edge_type_settings(self.edge_type, 'font'))

    @font.setter
    def font(self, value=None):
        """
        :param value:
        :return:
        """
        if isinstance(value, QtGui.QFont):
            self.saved.label_data['font'] = qt_prefs.get_key_for_font(value)
        else:
            self.saved.label_data['font'] = value

    @property
    def local_shape_args(self):
        """
        :return:
        """
        return self.saved.local_shape_args

    @local_shape_args.setter
    def local_shape_args(self, value):
        """
        :param value:
        """
        if value is None:
            value = {}
        self.saved.local_shape_args = value

    @property
    def color(self):
        """
        :return:
        """
        if self.saved.color is None:
            c = ctrl.forest.settings.edge_type_settings(self.edge_type, 'color')
            return ctrl.cm.get(c)
        else:
            return ctrl.cm.get(self.saved.color)

    @color.setter
    def color(self, value):
        """
        :param value:
        """
        self.saved.color = value
        if self.label_item:
            self.label_item.setDefaultTextColor(ctrl.cm.get(value))

    @property
    def color_id(self):
        """  get palette id of the edge color.
        :return: str
        """
        if self.saved.color is None:
            return ctrl.forest.settings.edge_type_settings(self.edge_type, 'color')
        else:
            return self.saved.color

    @property
    def shape_name(self):
        """
        :return:
        """
        if self.saved.shape_name is None:
            return ctrl.forest.settings.edge_type_settings(self.edge_type, 'shape_name')
        else:
            return self.saved.shape_name

    @shape_name.setter
    def shape_name(self, value):
        """
        :param value:
        """
        self.saved.shape_name = value
        self._shape_method = SHAPE_PRESETS[value]['method']

    @property
    def pull(self):
        """
        :return:
        """
        if self.saved.pull is None:
            return ctrl.forest.settings.edge_type_settings(self.edge_type, 'pull')
        else:
            return self.saved.pull

    @pull.setter
    def pull(self, value):
        """
        :param value:
        """
        self.saved.pull = value

    @property
    def visible(self):
        """
        :return:
        """
        return self.saved.visible

    @visible.setter
    def visible(self, value):
        """ Hide or show, and also manage related UI objects. Note that the shape itself may be visible or
        not independent of this. It has to be visible in this level so that UI elements can be used.
        :param visible:
        """
        v = self.isVisible()
        if v and not value:
            self.saved.visible = False
            self.hide()
            ctrl.main.ui_manager.remove_control_points(self)
        elif (not v) and value:
            self.saved.visible = True
            self.show()
            if ctrl.is_selected(self):
                ctrl.main.ui_manager.add_control_points(self)
        else:
            self.saved.visible = value

    @property
    def label_start(self):
        """
        label's startpoint in length of an edge (from 0 to 1.0)
        """
        return self.label_data.get('start_at', 0.2)

    @label_start.setter
    def label_start(self, value):
        """
        :param value:
        """
        self.label_data['start_at'] = value
        self.update_label_pos()


    @property
    def label_angle(self):
        """
        label's angle relative to edge where it is attached
        """
        return self.label_data.get('angle', 90)

    @label_angle.setter
    def label_angle(self, value):
        """
        :param value:
        """
        self.label_data['angle'] = value
        self.update_label_pos()

    @property
    def label_dist(self):
        """
        label's distance from edge
        """
        return self.label_data.get('dist', 12)

    @label_dist.setter
    def label_dist(self, value):
        """
        :param value:
        """
        self.label_data['dist'] = value
        self.update_label_pos()




    def receive_signal(self, signal, *args):
        """

        :param signal:
        :param args:
        """
        if signal is g.EDGE_SHAPES_CHANGED:
            if (args and args[0] == self.edge_type) or not args:
                self.update_shape()

    def is_filled(self):
        """


        :return:
        """
        return self._cached_shape_args['fill']

    def has_outline(self):
        """


        :return:
        """
        return self._cached_shape_args.get('thickness', 0)

    def is_visible(self):
        """


        :return:
        """
        return self.visible

    def make_relative_vector(self):
        """

        :return:
        """
        if self.start and not self.end:
            sx, sy, sz = self.start.current_position
            ex, ey, ez = self.end_point
            self._relative_vector = ex - sx, ey - sy, ez - sz
        elif self.end and not self.start:
            sx, sy, sz = self.start_point
            ex, ey, ez = self.end.current_position
            self._relative_vector = ex - sx, ey - sy, ez - sz

    def connect_start_to(self, node):
        """

        :param node:
        """
        ctrl.forest.set_edge_start(self, node)
        self.make_relative_vector()
        ctrl.ui.reset_control_points(self)
        self.update_shape()
        # self.update()

    def connect_end_to(self, node):
        """

        :param node:
        """
        ctrl.forest.set_edge_end(self, node)
        self.make_relative_vector()
        ctrl.ui.reset_control_points(self)
        self.update_shape()

    def set_start_point(self, p, y=None, z=None):
        """ Convenience method for setting start point: accepts QPoint(F)s, tuples and x,y coords.
        :param p: first argument, either QPoint, tuple or x coordinate if y is also given
        :param y: y coordinate
        :param z: z coordinate
        :return:
        """
        if z is None:
            if self.start_point:
                z = self.start_point[2]
            else:
                z = 0

        if y is not None:
            self.fixed_start_point = p, y, z
        elif isinstance(p, tuple):
            if len(p) == 3:
                self.fixed_start_point = p
            else:
                self.fixed_start_point = (p[0], p[1], z)
        if isinstance(p, (QtCore.QPoint, QtCore.QPointF)):
            self.fixed_start_point = (p.x(), p.y(), z)
        self.make_relative_vector()

    def set_end_point(self, p, y=None, z=None):
        """ Convenience method for setting end point: accepts QPoint(F)s, tuples and x,y coords.
        :param p: first argument, either QPoint, tuple or x coordinate if y is also given
        :param y: y coordinate
        :param z: z coordinate
        :return:
        """
        if z is None:
            if self.end_point:
                z = self.end_point[2]
            else:
                z = 0

        if y is not None:
            self.fixed_end_point = p, y, z
        elif isinstance(p, tuple):
            if len(p) == 3:
                self.fixed_end_point = p
            else:
                self.fixed_end_point = (p[0], p[1], z)
        if isinstance(p, (QtCore.QPoint, QtCore.QPointF)):
            self.fixed_end_point = (p.x(), p.y(), z)
        self.make_relative_vector()

    # Label for arrow etc. ##############################################


    def get_label_line_positions(self):
        """


        :return:
        """
        start = self.get_point_at(self.label_start)
        angle = (360 - self.get_angle_at(self.label_start)) + self.label_angle
        if angle > 360:
            angle -= 360
        if angle < 0:
            angle += 360
        angle = math.radians(angle)
        end_x = start.x() + (self.label_dist * math.cos(angle))
        end_y = start.y() + (self.label_dist * math.sin(angle))
        end = QtCore.QPointF(end_x, end_y)
        return start, end

    def update_label_pos(self):
        """


        :return:
        """
        if not self.label_item:
            return
        start, end = self.get_label_line_positions()
        mx, my = self.label_item.find_suitable_magnet(start, end)
        # mx, my = self._label_item.find_closest_magnet(start, end)
        label_pos = end - QtCore.QPointF(mx, my)
        self._cached_label_start = start
        self.label_item.setPos(label_pos)

    def get_cached_label_start(self):
        """


        :return:
        """
        if not self._cached_label_start:
            self.update_label_pos()
        return self._cached_label_start

    def is_broken(self):
        """


        :return:
        """
        if self.edge_type == g.ARROW:
            return False
        if not (self.start and self.end):
            return True
        return self.start.is_placeholder() or self.end.is_placeholder()

    # ### Color ############################################################

    def contextual_color(self):
        """ Drawing color that is sensitive to node's state
        :return: QColor
        """
        if ctrl.pressed == self:
            return ctrl.cm.active(ctrl.cm.selection())
        elif self._hovering:
            return ctrl.cm.hovering(ctrl.cm.selection())
        elif self.is_broken():
            return ctrl.cm.broken(self.color)
        else:
            return self.color

    def use_labels(self):
        """


        :return:
        """
        if self._use_labels is None:
            return ctrl.forest.settings.edge_type_settings(self.edge_type, 'labeled')
        else:
            return self._use_labels

    # ### Shape / pull / visibility ###############################################################

    def shape_method(self):
        """


        :return:
        """
        return SHAPE_PRESETS[self.shape_name]['method']

    def shape_control_point_support(self):
        """


        :return:
        """
        return SHAPE_PRESETS[self.shape_name]['control_points']

    def drag(self, event):
        """

        :param event:
        """
        sx, sy, z = self.start_point
        dx, dy = self.end_point[0] - sx, self.end_point[1] - sy
        if not self._local_drag_handle_position:
            drag_x = event.buttonDownScenePos(QtCore.Qt.LeftButton).x()
            drag_y = event.buttonDownScenePos(QtCore.Qt.LeftButton).y()
            self._local_drag_handle_position = drag_x - sx, drag_y - sy
        scx, scy = utils.to_tuple(event.scenePos())
        lx, ly = self._local_drag_handle_position
        sx, sy = scx - lx, scy - ly
        if not self.start:
            self.set_start_point(sx, sy)
        if not self.end:
            self.set_end_point(sx + dx, sy + dy)

    def change_leaf_shape(self, dim, value):
        """

        :param dim:
        :param value:
        """
        if dim == 'w':
            self.shape_args('leaf_x', value)
        elif dim == 'h':
            self.shape_args('leaf_y', value)
        elif dim == 'r':
            self.shape_args('leaf_x', g.DELETE)
            self.shape_args('leaf_y', g.DELETE)
        self.update_shape()

    def change_curvature(self, dim, value):
        """

        :param dim:
        :param value:
        """
        relative = self.shape_args('relative')
        if dim == 'x':
            if relative:
                self.shape_args('rel_dx', value * .01)
            else:
                self.shape_args('fixed_dx', value)
        elif dim == 'y':
            if relative:
                self.shape_args('rel_dy', value * .01)
            else:
                self.shape_args('fixed_dy', value)
        elif dim == 'r':
            self.shape_args('rel_dx', g.DELETE)
            self.shape_args('rel_dy', g.DELETE)
            self.shape_args('fixed_dx', g.DELETE)
            self.shape_args('fixed_dy', g.DELETE)
            self.shape_args('relative', g.DELETE)
        elif dim == 's':
            if value == 'fixed':
                self.shape_args('relative', False)
            else:
                self.shape_args('relative', True)
        self.update_shape()

    def change_thickness(self, dim, value):
        """

        :param dim:
        :param value:
        """
        if dim == 'r':
            self.shape_args('thickness', g.DELETE)
        else:
            self.shape_args('thickness', value)
        self.update_shape()

    def shape_args(self, key=None, value=None):
        """ Without key, return a dict of shape drawing arguments that should be used with shape drawing method.
        With key, give a certain shape_arg.
        With key and value, set the key.
        :param key:
        :param value:
        :return:
        """
        if key is None:
            # print('getting shape_args for edge ', self)
            shape_args = ctrl.forest.settings.edge_shape_settings(self.edge_type, shape_name=self.shape_name)
            if self.local_shape_args:
                sa = shape_args.copy()
                sa.update(self.local_shape_args)
                return sa
            else:
                return shape_args.copy()
        else:
            if value is None:
                local = self.local_shape_args.get(key, None)
                if local is not None:
                    return local
                else:
                    ctrl.forest.settings.edge_shape_settings(self.edge_type, key=key, shape_name=self.shape_name)
            elif value == g.DELETE:
                if key in self.local_shape_args:
                    del self.local_shape_args[key]
            else:
                self.local_shape_args[key] = value

    # ### Derivative features ############################################
    # @time_me
    def make_path(self):
        """ Draws the shape as a path """
        if not self._shape_method:
            self.update_shape()
        c = self._cached_shape_args
        c['start_point'] = self.start_point
        c['end_point'] = self.end_point
        c['adjust'] = self.adjust
        c['align'] = self.align
        c['start'] = self.start
        c['end'] = self.end
        self._path, self._true_path, self.control_points = self._shape_method(**c)
        if self.ending('start'):
            self._arrowhead_start_path = self.make_arrowhead_path('start')
        else:
            self._arrowhead_start_path = None
        if self.ending('end'):
            self._arrowhead_end_path = self.make_arrowhead_path('end')
        else:
            self._arrowhead_end_path = None

        sn = self.shape_name
        if sn == 'blob' or sn == 'directional_blob':
            self._fat_path = self._path
        elif c.get('thickness', 0):
            if self.ending('start'):
                self._path = self.clip_ending('start', self._path)
            if self.ending('end'):
                self._path = self.clip_ending('end', self._path)
            bi = QtGui.QPainterPath(self._path)
            bi.addPath(self._path.toReversed())
            self._fat_path = outline_stroker.createStroke(self._path).united(bi)
        else:
            self._fat_path = outline_stroker.createStroke(self._path).united(self._path)
        if self._arrowhead_start_path:
            self._fat_path = self._fat_path.united(self._arrowhead_start_path)
        if self._arrowhead_end_path:
            self._fat_path = self._fat_path.united(self._arrowhead_end_path)
        self.update_label_pos()
        ctrl.ui.update_control_point_positions()
        if ctrl.is_selected(self):
            ctrl.ui.update_edge_button_positions(self)

    def shape(self):
        """ Override of the QGraphicsItem method. Should returns the real shape of item to allow exact hit detection.
        In our case we should have special '_fat_path' for those shapes that are just narrow lines.
        :return: QGraphicsPath
        """
        if not self._fat_path:
            self.make_path()
        return self._fat_path

    def update_shape(self):
        """ Reload shape and shape settings """
        self._shape_method = SHAPE_PRESETS[self.shape_name]['method']
        self._cached_shape_args = self.shape_args()
        cpl = len(self.control_points)
        self.make_path()
        #while len(self.adjust) < len(self.control_points):
        #    self.adjust.append((0, 0, 0))
        if cpl != len(self.control_points):
            ctrl.ui.reset_control_points(self)
        ctrl.ui.update_control_point_positions()
        self.update()

    def prepare_adjust_array(self, index):
        if self.adjust is None:
            self.adjust = [(0, 0, 0)] * (index + 1)
        elif index >= len(self.adjust):
            self.adjust += [(0, 0, 0)] * (index - len(self.adjust) + 1)


    def adjust_control_point(self, index, points, cp=True):
        """ Called from UI, when dragging
        :param index:
        :param points:
        :param cp:
        """
        x, y = points
        self.prepare_adjust_array(index)
        z = self.adjust[index][2]
        self.adjust[index] = (x, y, z)
        self.make_path()
        self.update()
        if cp:
            panel = ctrl.ui.get_panel(g.LINE_OPTIONS)
            if panel:
                panel.update_control_point_spinboxes()

    def adjust_control_point_xy(self, index, dim, value):
        """ Called when modifying control point settings directly
        :param index:
        :param dim:
        :param value:
        :return:
        """
        self.prepare_adjust_array(index)
        x, y, z = self.adjust[index]
        if dim == 'x':
            self.adjust[index] = value, y, z
        elif dim == 'y':
            self.adjust[index] = x, value, z
        elif dim == 'z':
            self.adjust[index] = x, y, value
        self.make_path()
        ctrl.ui.update_control_point_positions()
        self.update()

    def reset_control_point(self, index):
        """
        Set adjustments back to zero
        :param index:
        :return:
        """
        if self.adjust and len(self.adjust) > index:
            self.adjust[index] = (0, 0, 0)
        can_delete = True
        for (x, y, z) in self.adjust:
            if x != 0 or y != 0:
                can_delete = False
        if can_delete:
            self.adjust = None
        self.make_path()
        ctrl.ui.update_control_point_positions()
        self.update()
        panel = ctrl.ui.get_panel(g.LINE_OPTIONS)
        panel.update_control_point_spinboxes()

    def update_end_points(self):
        """

        :return:
        """
        if self.start and not self.end:
            sp_x, sp_y, sp_z = self.start.current_position
            r_x, r_y, r_z = self._relative_vector
            self._computed_end_point = sp_x + r_x, sp_y + r_y, sp_z + r_z
        elif self.end and not self.start:
            ep_x, ep_y, ep_z = self.end.current_position
            r_x, r_y, r_z = self._relative_vector
            self._computed_start_point = ep_x - r_x, ep_y - r_y, ep_z - r_z

        if self.edge_type == g.ARROW:

            if self.start:
                if self._true_path:
                    a = self.get_angle_at(0)
                    i = round(a / 22.5)
                    self._computed_start_point  = self.start.magnet(angle_magnet_map[i])
                else:
                    sx, sy, sz = self.start_point
                    ex, ey, ez = self.end_point
                    dx = ex - sx
                    dy = ey - sy
                    i = round(math.degrees(math.atan2(dy, dx)) / 22.5)
                    self._computed_start_point = self.start.magnet(atan_magnet_map[i])
            if self.end:
                if self._true_path:
                    a = self.get_angle_at(1.0)
                    if a >= 180:
                        a -= 180
                    elif a < 180:
                        a += 180
                    i = round(a / 22.5)
                    self._computed_end_point  = self.end.magnet(angle_magnet_map[i])
                else:
                    sx, sy, sz = self.start_point
                    ex, ey, ez = self.end_point
                    dx = sx - ex
                    dy = sy - ey
                    i = round(math.degrees(math.atan2(dy, dx)) / 22.5)
                    self._computed_end_point = self.end.magnet(atan_magnet_map[i])
        elif self.edge_type == g.DIVIDER:
            pass

        else:
            if self.start:
                if self.align == LEFT:
                    self._computed_start_point = self.start.magnet(8)
                elif self.align == RIGHT:
                    self._computed_start_point = self.start.magnet(10)
                else:
                    self._computed_start_point = self.start.magnet(9)
            if self.end:
                self._computed_end_point = self.end.magnet(2)

    def connect_end_points(self, start, end):
        """

        :param start:
        :param end:
        """
        if start:
            self._computed_start_point = start.current_position
            self.start = start
        else:
            self.start = None
        if end:
            self._computed_end_point = end.current_position
            self.end = end
        else:
            self.end = None
        self.make_relative_vector()
        self.update_status_tip()

    def update_status_tip(self):
        """

        :return:
        """
        if self.edge_type == g.CONSTITUENT_EDGE:
            self.status_tip = 'Constituent relation: %s is part of %s' % (self.end, self.start)

    def description(self):
        """

        :return:
        """
        if self.edge_type == g.ARROW:
            label = 'Arrow'
        else:
            label = 'Edge'
        if self.start:
            s1 = self.start
        elif self.fixed_start_point:
            s1 = '(%s, %s)' % (int(self.start_point[0]), int(self.start_point[1]))
        else:
            s1 = 'undefined'
        if self.end:
            s2 = self.end
        elif self.fixed_end_point:
            s2 = '(%s, %s)' % (int(self.end_point[0]), int(self.end_point[1]))
        else:
            s2 = 'undefined'
        return '%s from %s to %s' % (label, s1, s2)

    def __repr__(self):
        return self.description()

    def drop_to(self, x, y, recipient=None):
        """ This happens only when dragging the whole edge. Just reset the drag handle position so that the next
         drag attempt will take new handle.
        :param x: not used
        :param y: not used
        :param recipient: not used
        """
        self._local_drag_handle_position = None


    def can_be_disconnected(self):
        """
        :return:
        """
        return True

    def allow_orphan_ends(self):
        """

        :return:
        """
        return self.edge_type is g.ARROW or self.edge_type is g.DIVIDER

    def has_orphan_ends(self):
        """

        :return:
        """
        return (self.end and (self.end.is_placeholder())) or (self.start and (self.start.is_placeholder()))

    def refresh_selection_status(self, selected):
        """

        :param selected:
        """
        if selected:
            if self.allow_orphan_ends() or not self.has_orphan_ends():
                if self.use_labels():
                    if not self.label_item:
                        self.label_item = EdgeLabel('', self, placeholder=True)
                        self.update_label_pos()
                    self.label_item.selected = True
        else:
            if self.label_item:
                if self.label_item.placeholder:
                    scene = self.scene()
                    if scene:
                        scene.removeItem(self.label_item)
                    self.label_item = None
                else:
                    self.label_item.selected = False
        self.update()

    def boundingRect(self):
        """

        :return:
        """
        if not self._path:
            self.update_end_points()
            self.make_path()
        return self._path.controlPointRect()

    # ### Mouse - Qt events ##################################################


    @property
    def hovering(self):
        return self._hovering

    @hovering.setter
    def hovering(self, value):
        """ Toggle hovering effects and internal bookkeeping
        :param value: bool
        :return:
        """
        if value and not self._hovering:
            self._hovering = True
            self.setZValue(100)
            if ctrl.cm.use_glow():
                self.effect.setColor(ctrl.cm.selection())
                self.effect.setEnabled(True)
            self.prepareGeometryChange()
            self.update()
            ctrl.set_status(self.status_tip)
        elif (not value) and self._hovering:
            if ctrl.cm.use_glow():
                self.effect.setEnabled(False)
            self._hovering = False
            self.prepareGeometryChange()
            self.setZValue(10)
            self.update()
            ctrl.remove_status(self.status_tip)

    def hoverEnterEvent(self, event):
        """
        Overrides (and calls) QtWidgets.QGraphicsItem.hoverEnterEvent
        Toggles hovering state and necessary graphical effects.
        :param event:
        """
        self.hovering = True
        QtWidgets.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """

        :param event:
        """
        self.hovering = False
        QtWidgets.QGraphicsItem.hoverLeaveEvent(self, event)

    # ## Scene-managed call

    def select(self, event=None):
        """ Scene has decided that this node has been selected
        (update
        :param event:
        """
        self.hovering = False
        if event and event.modifiers() == Qt.ShiftModifier:  # multiple selection
            if ctrl.is_selected(self):
                ctrl.remove_from_selection(self)
            else:
                ctrl.add_to_selection(self)
            return
        if not ctrl.is_selected(self):
            ctrl.select(self)

    def asymmetric(self):
        """

        :return:
        """
        return True

    # ## Qt paint method override

    def paint(self, painter, option, widget=None):
        """

        :param painter:
        :param option:
        :param widget:
        :return:
        """
        c = self.contextual_color()
        width = self.has_outline()
        if width:
            p = QtGui.QPen()
            p.setColor(c)
            if self.asymmetric() and self.align is g.RIGHT:
                width *= 2
            p.setWidthF(width)
            painter.setPen(p)
            painter.drawPath(self._path)
        elif self.asymmetric() and self.align is g.RIGHT:
            p = QtGui.QPen()
            p.setColor(c)
            painter.setPen(p)
            painter.drawPath(self._path)

        if self.is_filled():
            painter.fillPath(self._path, c)
        if self.ending('start'):
            painter.fillPath(self._arrowhead_start_path, c)
        if self.ending('end'):
            painter.fillPath(self._arrowhead_end_path, c)
        if ctrl.is_selected(self):
            p = QtGui.QPen(ctrl.cm.ui_tr())
            painter.setPen(p)
            painter.drawPath(self._true_path)

            # painter.setPen(ctrl.cm.d['accent6'])
            # painter.drawPath(self._fat_path)
            # painter.fillPath(self._fat_path, ctrl.cm.d['accent7'])

    def get_path(self) -> QtGui.QPainterPath:
        """ Get drawing path of this edge
        :return: QPath
        """
        return self._path

    def get_point_at(self, d: float) -> Pf:
        """ Get coordinates at the percentage of the length of the path.
        :param d: int
        :return: QPoint
        """
        if not self._true_path:
            self.update_end_points()
            self.make_path()
        return self._true_path.pointAtPercent(d)

    def get_angle_at(self, d: float) -> float:
        """ Get angle at the percentage of the length of the path.
        :param d: int
        :return: float
        """
        if not self._true_path:
            self.update_end_points()
            self.make_path()
        return self._true_path.angleAtPercent(d)

    def get_closest_path_point(self, pos):
        """

        :param pos:
        :return:
        """
        if not self._true_path:
            self.update_end_points()
            self.make_path()
        min_d = 1000
        min_i = -1
        min_pos = None
        for i in range(0, 100, 2):
            p2 = self._true_path.pointAtPercent(i / 100.0)
            d = (pos - p2).manhattanLength()
            if d < min_d:
                min_d = d
                min_i = i
                min_pos = p2
        return min_i / 100.0, min_pos

    # ### Event filter - be sensitive to changes in settings  ########################################################

    # def sceneEvent(self, event):
    # print 'Edge event received: ', event.type()
    # return QtWidgets.QGraphicsItem.sceneEvent(self, event)

    # ### Restoring after load / undo #########################################

    def ending(self, which_end, value=None):
        """
        get ending to be used in the edge, or set it.
        :param which_end:
        :param value: string or boolean
        :return: string or boolean
        """
        if value is None:
            if which_end == 'start':
                if self._arrowhead_at_start is None:
                    return ctrl.forest.settings.edge_type_settings(self.edge_type, 'arrowhead_at_start')
                else:
                    return self._arrowhead_at_start
            elif which_end == 'end':
                if self._arrowhead_at_end is None:
                    return ctrl.forest.settings.edge_type_settings(self.edge_type, 'arrowhead_at_end')
                else:
                    return self._arrowhead_at_end

        else:
            if which_end == 'start':
                self._arrowhead_at_start = value
            elif which_end == 'end':
                self._arrowhead_at_end = value

    def clip_ending(self, which_end, path):
        """

        :param which_end:
        :param path:
        :return:
        """
        if which_end == 'start':
            i = 0
            if self._arrow_cut_point_start:
                x, y = self._arrow_cut_point_start
            else:
                return path
        else:
            i = path.elementCount() - 1
            if self._arrow_cut_point_end:
                x, y = self._arrow_cut_point_end
            else:
                return path
        path.setElementPositionAt(i, x, y)
        return path

    def make_arrowhead_path(self, pos='end'):
        """

        :param pos:
        """
        ad = 0.5
        x = y = size = a = 0
        t = self._cached_shape_args.get('thickness', 0)
        if pos == 'start':
            size = self.arrowhead_size_at_start
            if t:
                size *= t
            x, y, z = self.start_point
            a = math.radians(-self.get_angle_at(0) + 180)
        elif pos == 'end':
            size = self.arrowhead_size_at_end
            if t:
                size *= t
            x, y, z = self.end_point
            a = math.radians(-self.get_angle_at(.95))
        p = QtGui.QPainterPath()
        p.moveTo(x, y)
        x1, y1 = x - (math.cos(a + ad) * size), y - (math.sin(a + ad) * size)
        xm, ym = x - (math.cos(a) * size * 0.5), y - (math.sin(a) * size * 0.5)
        x2, y2 = x - (math.cos(a - ad) * size), y - (math.sin(a - ad) * size)
        p.lineTo(x1, y1)
        p.lineTo(xm, ym)
        p.lineTo(x2, y2)
        p.lineTo(x, y)
        if pos == 'start':
            self._arrow_cut_point_start = xm, ym
        elif pos == 'end':
            self._arrow_cut_point_end = xm, ym
        return p

