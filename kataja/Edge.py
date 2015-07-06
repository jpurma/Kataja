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
from kataja.globals import LEFT, RIGHT
from kataja.shapes import SHAPE_PRESETS, outline_stroker
from kataja.EdgeLabel import EdgeLabel
import kataja.utils as utils
from kataja.BaseModel import BaseModel, SavedAndGetter, Saved

# ('shaped_relative_linear',{'method':shapedRelativeLinearPath,'fill':True,'pen':'thin'}),

angle_magnet_map = {0: 6, 1: 6, 2: 4, 3: 3, 4: 2, 5: 1, 6: 0, 7: 5, 8: 5, 9: 5, 10: 7, 11: 8, 12: 9, 13: 10, 14: 11,
                    15: 6, 16: 6}

atan_magnet_map = {-8: 5, -7: 5, -6: 0, -5: 1, -4: 2, -3: 3, -2: 4, -1: 6, 0: 6, 1: 6, 2: 11, 3: 10, 4: 9, 5: 8, 6: 7,
                   7: 5, 8: 5}


class Edge(QtWidgets.QGraphicsItem, BaseModel):
    """ Any connection between nodes: can be represented as curves, branches or arrows """

    short_name = "E"

    def __init__(self, start=None, end=None, edge_type='', direction=''):
        """
        :param Node start:
        :param Node end:
        :param string edge_type:
        :param string direction:
        """
        BaseModel.__init__(self)
        QtWidgets.QGraphicsItem.__init__(self)

        self.label_item = None
        self._shape_method = None

        self.edge_type = edge_type
        self.alignment = direction or g.NO_ALIGN
        self.start = start
        self.end = end
        self.fixed_start_point = None
        self.fixed_end_point = None
        self.curve_adjustment = None
        self.label_data = {}
        self.local_shape_args = {}
        self.color_id = None
        self.shape_name = None
        self.pull = None
        self.visible = True

        self._computed_start_point = None
        self._computed_end_point = None

        self.control_points = []
        self._local_drag_handle_position = None

        # ## Adjustable values, defaults to ForestSettings if None for this element
        # based on the relation style

        # self.center_point = (0, 0, 0)

        # ## Derivative elements
        self._path = None
        self._true_path = None  # inner arc or line without the leaf effect
        self._fat_path = None
        self._use_simple_path = False
        self.selectable = True
        self.draggable = not (self.start or self.end)
        self.clickable = False
        self._hovering = False
        self._start_node_moving = False
        self._end_node_moving = False
        self._make_fat_path = False
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
        self._cached_cp_rect = None
        self._use_labels = None
        self._label_text = None
        self._label_rect = None
        self._relative_vector = None
        self._label_font = None  # inherited from settings
        self._cached_label_start = None
        # self.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        # self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        # self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.effect = None
        self.move_effect = None

    def after_init(self):
        """ After_init is called in 2nd step in process of creating objects:
            1st wave creates the objects and calls __init__, and then iterates through and sets the values.
            2nd wave calls after_inits for all created objects. Now they can properly refer to each other and know their
                values.
        :return: None
        """
        # print("after-initing edge ", self)
        self.connect_end_points(self.start, self.end)
        self.make_relative_vector()
        self.effect = utils.create_shadow_effect(self.color)
        self.move_effect = utils.create_blur_effect()
        self.setGraphicsEffect(self.effect)
        self.update_visibility()
        self.announce_creation()

    def after_model_update(self, updated_fields, update_type):
        """ Compute derived effects of updated values in sensible order.
        :param updated_fields: field keys of updates
        :param update_type: 0:edit, 1:CREATED, 2:DELETED
        :return: None
        """
        if 'visible' in updated_fields:
            self.update_visibility()
        self.connect_end_points(self.start, self.end)
        self.make_relative_vector()


    @property
    def start_point(self):
        """ Helper property: returns latest known (x, y, z) coords of starting point of the edge
        :return: tuple (x, y, z)
        """
        if self.start:
            return self._computed_start_point
        else:
            return self.fixed_start_point

    @property
    def end_point(self):
        """ Helper property: returns latest known (x, y, z) coords of ending point of the edge
        :return: tuple (x, y, z)
        """
        if self.end:
            return self._computed_end_point
        else:
            return self.fixed_end_point

    def if_changed_visible(self, value):
        """ Edges may be filtered out of view without destroying them, e.g. comment edges and arrows.
        Setting edge hidden makes it invisible for many ways of manipulating and updating edges, so care must
         be taken.  Note that the edge can be invisible because it has shape 'not drawn', but such edge is still visible
         for these purposes: it will have its UI buttons, it is selectable etc.
        :param value: bool
        """
        self.update_visibility()

    def update_visibility(self):
        """ Hide or show according to model.visible flag, which allows edge to exist but not be drawn.
        :return:
        """
        v = self.isVisible()
        if v and not self.visible:
            self.hide()
            ctrl.ui.remove_ui_for(self)

        elif self.visible and not v:
            self.show()
            if ctrl.is_selected(self):
                ctrl.ui.add_control_points(self)

    # Edge type - based settings that can be overridden

    @property
    def color(self):
        """ Color for drawing the edge -- both the fill and pen color. Returns QColor, but what is stored is Kataja
        internal color_id.
        :return: QColor
        """
        return ctrl.cm.get(self.color_id)

    def after_get_color_id(self, value):
        """ Get palette id of the edge color.
        :return: str
        """
        return value or ctrl.forest.settings.edge_type_settings(self.edge_type, 'color')

    def if_changed_color_id(self, value):
        """ Set edge color, uses palette id strings as values.
        :param value: string
        """
        if self.label_item:
            self.label_item.setDefaultTextColor(ctrl.cm.get(value))

    def after_get_shape_name(self, value):
        """ Get the shape name key for this edge. These keys are used to get the shape drawing settings, amount of
        control points, whether the shape is filled etc.
        :return:
        """
        return value or ctrl.forest.settings.edge_type_settings(self.edge_type, 'shape_name')

    def if_changed_shape_name(self, value):
        """ Set the shape name key for this edge. These keys are used to get the shape drawing settings, amount of
        control points, whether the shape is filled etc. Also updates the _shape_method according to new shape_name.
        :param value: str
        """
        if value:
            self._shape_method = SHAPE_PRESETS[value]['method']

    def after_get_pull(self, value):
        """ The strength of connection between nodes. Think of edge as a rubber band between nodes, and this is how
        strongly it pulls the nodes together. Pull is typically between 0 - 1.0
        :return: float
        """
        return value or ctrl.forest.settings.edge_type_settings(self.edge_type, 'pull')

    # ## Label data and its shortcut properties

    @property
    def label_text(self):
        """ Label text is actually stored in model.label_data, but this is a shortcut for it.
        :return:
        """
        return self.label_data.get('text', '')

    @label_text.setter
    def label_text(self, value=None):
        """ Label text is actually stored in label_data, but this is a shortcut for setting it.
        :param value:
        :return:
        """
        old = self.label_text
        if value != old:
            self.poke('label_data')
            self.label_data['text'] = value
            if not self.label_item:
                self.label_item = EdgeLabel(value, parent=self)
            else:
                self.label_item.update_text(value)

    @property
    def font(self):
        """ Font is the font used for label. What is stored is the kataja internal font name, but what is
        returned here is the actual QFont.
        :return: QFont instance
        """
        f_name = self.label_data.get('font', None)
        if f_name:
            return qt_prefs.font(f_name)
        else:
            return qt_prefs.font(ctrl.forest.settings.edge_type_settings(self.edge_type, 'font'))

    @property
    def font_name(self):
        """ Font is the font used for label. This returns the kataja internal font name.
        :return:
        """
        f_name = self.label_data.get('font', None)
        if f_name:
            return f_name
        else:
            return ctrl.forest.settings.edge_type_settings(self.edge_type, 'font')

    @font_name.setter
    def font_name(self, value=None):
        """ Font is the font used for label. This sets the font name to be used.
        :param value: string (font name).
        """
        f = self.font_name
        if value != f:
            self.poke('label_data')
            self.label_data['font'] = value

    @property
    def label_start(self):
        """
        label's startpoint in length of an edge (from 0 to 1.0)
        """
        return self.label_data.get('start_at', 0.2)

    @label_start.setter
    def label_start(self, value):
        """ label's startpoint in length of an edge (from 0 to 1.0)
        :param value: float (0 - 1.0)
        """
        v = self.label_start
        if v != value:
            self.poke('label_data')
            self.label_data['start_at'] = value
            self.update_label_pos()
            self.call_watchers('edge_label_adjust', 'start_at', value)


    @property
    def label_angle(self):
        """
        label's angle relative to edge where it is attached
        """
        return self.label_data.get('angle', 90)

    @label_angle.setter
    def label_angle(self, value):
        """
        label's angle relative to edge where it is attached
        :param value:
        """
        v = self.label_angle
        if v != value:
            self.poke('label_data')
            self.label_data['angle'] = value
            self.update_label_pos()
            self.call_watchers('edge_label_adjust', 'angle', value)

    @property
    def label_dist(self):
        """
        label's distance from edge
        """
        return self.label_data.get('dist', 12)

    @label_dist.setter
    def label_dist(self, value):
        """
        label's distance from edge
        :param value:
        """
        v = self.label_dist
        if v != value:
            self.poke('label_data')
            self.label_data['dist'] = value
            self.update_label_pos()
            self.call_watchers('edge_label_adjust', 'dist', value)

    ### Local shape settings and its shortcut properties #################

    @property
    def arrowhead_at_start(self):
        """ Should there be an arrowhead drawn at the start of the edge. If the value is set, it is stored in
        local_shape_args, but otherwise it is get from settings for this type of edge.
        :return: bool
        """
        a = self.local_shape_args.get('arrowhead_at_start', None)
        if a is None:
            return ctrl.forest.settings.edge_type_settings(self.edge_type, 'arrowhead_at_start')
        else:
            return a

    @arrowhead_at_start.setter
    def arrowhead_at_start(self, value):
        """ Should there be an arrowhead drawn at the start of the edge. If the value is set, it is stored in
        local_shape_args, but otherwise it is get from settings for this type of edge.
        :param value: bool
        """
        self.poke('local_shape_args')
        self.local_shape_args['arrowhead_at_start'] = value

    @property
    def arrowhead_at_end(self):
        """ Should there be an arrowhead drawn at the start of the edge. If the value is set, it is stored in
        local_shape_args, but otherwise it is get from settings for this type of edge.
        :return: bool
        """
        a = self.local_shape_args.get('arrowhead_at_end', None)
        if a is None:
            return ctrl.forest.settings.edge_type_settings(self.edge_type, 'arrowhead_at_end')
        else:
            return a

    @arrowhead_at_end.setter
    def arrowhead_at_end(self, value):
        """ Should there be an arrowhead drawn at the start of the edge. If the value is set, it is stored in
        local_shape_args, but otherwise it is get from settings for this type of edge.
        :param value: bool
        """
        self.poke('local_shape_args')
        self.local_shape_args['arrowhead_at_end'] = value

    # ## Signal handling ####

    def receive_signal(self, signal, *args):
        """

        :param signal:
        :param args:
        """
        if signal is g.EDGE_SHAPES_CHANGED:
            if (args and args[0] == self.edge_type) or not args:
                self.update_shape()

    # Helper methods for derived properties

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
        """ Relative vector helps to keep the shape of a line when another, attached end moves.
         It applies only to lines where the other end is attached to node.
        :return:
        """
        #print(id(self), self.start_point, self.end_point, self.start, self.end)
        if self.start and not self.end:
            sx, sy, sz = self.start.current_position
            ex, ey, ez = self.end_point
            self._relative_vector = ex - sx, ey - sy, ez - sz
        elif self.end and not self.start:
            sx, sy, sz = self.start_point
            ex, ey, ez = self.end.current_position
            self._relative_vector = ex - sx, ey - sy, ez - sz
        #print(id(self), self.start_point, self.end_point, self.start, self.end)

    def connect_start_to(self, node):
        """

        :param node:
        """
        ctrl.forest.set_edge_start(self, node)
        self.make_relative_vector()
        self.update_shape()
        # self.update()

    def connect_end_to(self, node):
        """

        :param node:
        """
        ctrl.forest.set_edge_end(self, node)
        self.make_relative_vector()
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
        """ When editing edge labels, there is a line connecting the edge to label. This one provides the
        end- and start points for such line.
        :return: None
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
        """ Compute and set position for edge label. Make sure that path is up to date before doing this.
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

    @property
    def cached_label_start(self):
        """ Get the cached (absolute) label starting position. This has to be visible outside, because
        control points may need it.
        :return: QPos
        """
        if not self._cached_label_start:
            self.update_label_pos()
        return self._cached_label_start

    def is_broken(self):
        """ If this edge should be a connection between two nodes and either node is missing, the edge
        is broken and should be displayed differently.
        :return: bool
        """
        if self.edge_type == g.ARROW:
            return False
        if not (self.start and self.end):
            return True
        return self.start.is_placeholder() or self.end.is_placeholder()

    # ### Color ############################################################

    @property
    def contextual_color(self):
        """ Drawing color that is sensitive to edge's state
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

    @property
    def uses_labels(self):
        """ Some edge types, e.g. arrows inherently suggest adding labels to them. For others, having ui
         textbox for adding label would be unwanted noise.
        :return: bool
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
        """ This is for dragging the whole edge in cases when edge is not connected to nodes at any point
        e.g. it is freely floating arrow or divider
        :param event: Drag event?
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
                    self.poke('local_shape_args')
                    del self.local_shape_args[key]
            else:
                self.poke('local_shape_args')
                self.local_shape_args[key] = value

    # ### Derivative features ############################################
    #@utils.time_me
    def make_path(self):
        """ Draws the shape as a path """
        self.update_end_points()
        if not self._shape_method:
            self.update_shape()
        c = self._cached_shape_args
        c['start_point'] = self.start_point
        c['end_point'] = self.end_point
        c['curve_adjustment'] = self.curve_adjustment
        c['alignment'] = self.alignment
        c['start'] = self.start
        c['end'] = self.end
        c['inner_only'] = self._use_simple_path
        self._path, self._true_path, self.control_points = self._shape_method(**c)

        if self._use_simple_path:
            self._path = self._true_path

        if self.arrowhead_at_start:
            self._arrowhead_start_path = self.make_arrowhead_path('start')
        else:
            self._arrowhead_start_path = None

        if self.arrowhead_at_end:
            self._arrowhead_end_path = self.make_arrowhead_path('end')
        else:
            self._arrowhead_end_path = None
        if self._make_fat_path and not self._use_simple_path:
            # Fat path is the shape of the path with some extra margin to make it easier to click/touch
            self._fat_path = outline_stroker.createStroke(self._path)
        else:
            self._fat_path = self._path
        self._cached_cp_rect = self._path.controlPointRect()
        #
        self.update_label_pos()
        if ctrl.is_selected(self):
            ctrl.ui.update_position_for(self)

    def shape(self):
        """ Override of the QGraphicsItem method. Should returns the real shape of item to
        allow exact hit detection.
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
        # while len(self.curve_adjustment) < len(self.control_points):
        # self.curve_adjustment.append((0, 0, 0))
        if cpl != len(self.control_points):
            ctrl.ui.update_control_points()
        self.update()

    def prepare_adjust_array(self, index):
        """

        :param index:
        """
        if self.curve_adjustment is None:
            self.curve_adjustment = [(0, 0, 0)] * (index + 1)
        elif index >= len(self.curve_adjustment):
            self.curve_adjustment += [(0, 0, 0)] * (index - len(self.curve_adjustment) + 1)


    def adjust_control_point(self, index, points, cp=True):
        """ Called from UI, when dragging
        :param index:
        :param points:
        :param cp:
        """
        x, y = points
        self.poke('curve_adjustment')
        self.prepare_adjust_array(index)
        z = self.curve_adjustment[index][2]
        self.curve_adjustment[index] = (x, y, z)
        self.call_watchers('edge_adjustment', 'curve_adjustment', self.curve_adjustment)
        self.make_path()
        self.update()

    def adjust_control_point_xy(self, index, dim, value):
        """ Called when modifying control point settings directly
        :param index:
        :param dim:
        :param value:
        :return:
        """
        self.poke('curve_adjustment')
        self.prepare_adjust_array(index)
        x, y, z = self.curve_adjustment[index]
        if dim == 'x':
            self.curve_adjustment[index] = value, y, z
        elif dim == 'y':
            self.curve_adjustment[index] = x, value, z
        elif dim == 'z':
            self.curve_adjustment[index] = x, y, value
        self.call_watchers('edge_adjustment', 'curve_adjustment', self.curve_adjustment)
        self.make_path()
        self.update()

    def reset_control_point(self, index):
        """
        Set adjustments back to zero
        :param index:
        :return:
        """
        self.poke('curve_adjustment')
        if self.curve_adjustment and len(self.curve_adjustment) > index:
            self.curve_adjustment[index] = (0, 0, 0)
            self.call_watchers('edge_adjustment', 'curve_adjustment', self.curve_adjustment)
        can_delete = True
        for (x, y, z) in self.curve_adjustment:
            if x != 0 or y != 0:
                can_delete = False
        if can_delete:
            self.curve_adjustment = None
        self.make_path()
        self.update()

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
                    self._computed_start_point = self.start.magnet(angle_magnet_map[i])
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
                    self._computed_end_point = self.end.magnet(angle_magnet_map[i])
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
                if self.alignment == LEFT:
                    self._computed_start_point = self.start.magnet(8)
                elif self.alignment == RIGHT:
                    self._computed_start_point = self.start.magnet(10)
                else:
                    self._computed_start_point = self.start.magnet(9)
            if self.end:
                self._computed_end_point = self.end.magnet(2)
            assert self._computed_start_point or self._computed_end_point

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

    def update_selection_status(self, selected):
        """

        :param selected:
        """
        if selected:
            if self.allow_orphan_ends() or not self.has_orphan_ends():
                if self.uses_labels:
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
        """ BoundingRect that includes the control points of the arc

        :return:
        """
        if not self._path:
            self.make_path()
        return self._cached_cp_rect

    # ### Mouse - Qt events ##################################################


    @property
    def hovering(self):
        """


        :return:
        """
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
            #if ctrl.cm.use_glow():
            #    self.effect.setColor(ctrl.cm.selection())
            #    self.effect.setEnabled(True)
            self.prepareGeometryChange()
            self.update()
            ctrl.set_status(self.status_tip)
        elif (not value) and self._hovering:
            #if ctrl.cm.use_glow():
            #    self.effect.setEnabled(False)
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

    def select(self, event=None, multi=False):
        """ Scene has decided that this node has been selected
        (update
        :param event:
        :param multi: force multiple selection (append, not replace)
        """
        self.hovering = False
        if (event and event.modifiers() == Qt.ShiftModifier) or multi:  # multiple selection
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
        # fixme -- please
        return True

    # ## Qt paint method override

    def paint(self, painter, option, widget=None):
        """

        :param painter:
        :param option:
        :param widget:
        :return:
        """
        c = self.contextual_color
        if self._use_simple_path:
            p = QtGui.QPen()
            p.setColor(c)
            painter.setPen(p)
            painter.drawPath(self._true_path)
        else:
            width = self.has_outline()
            if width:
                p = QtGui.QPen()
                p.setColor(c)
                if self.asymmetric() and self.alignment is g.RIGHT:
                    width *= 2
                p.setWidthF(width)
                painter.setPen(p)
                painter.drawPath(self._path)
            elif self.asymmetric() and self.alignment is g.RIGHT:
                p = QtGui.QPen()
                p.setColor(c)
                painter.setPen(p)
                painter.drawPath(self._path)

            if self.is_filled():
                painter.fillPath(self._path, c)
            if self.arrowhead_at_start:
                painter.fillPath(self._arrowhead_start_path, c)
            if self.arrowhead_at_end:
                painter.fillPath(self._arrowhead_end_path, c)
        if ctrl.is_selected(self):
            p = QtGui.QPen(ctrl.cm.ui_tr())
            painter.setPen(p)
            painter.drawPath(self._true_path)

    def get_point_at(self, d: float) -> Pf:
        """ Get coordinates at the percentage of the length of the path.
        :param d: int
        :return: QPoint
        """
        if not self._true_path:
            self.make_path()
        return self._true_path.pointAtPercent(d)

    def get_angle_at(self, d: float) -> float:
        """ Get angle at the percentage of the length of the path.
        :param d: int
        :return: float
        """
        if not self._true_path:
            self.make_path()
        return self._true_path.angleAtPercent(d)

    def get_closest_path_point(self, pos):
        """ When dragging object along path, gives the coordinates to closest point in path corresponding to
        given position. There is no exact way of doing this, what we do is to take 100 points along the line and
        find the closest point from there.
        :param pos: position looking for closest path position
        :return: (float:pointAtPercent, QPos:path position)
        """
        if not self._true_path:
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

    def make_arrowhead_path(self, pos='end'):
        """ Assumes that the path exists already, creates arrowhead path to either at the end or at start,
        but doesn't yet combine these paths.
        :param pos: 'end' or 'start'
        :return: QPainterPath for arrowhead
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

    def end_node_started_moving(self):
        """ Called if the end node has started moving.
        :return:
        """
        self._end_node_moving = True
        self._make_fat_path = False
        if not self._start_node_moving:
            self._start_moving()


    def start_node_started_moving(self):
        """ Called if the end node has started moving.
        :return:
        """
        self._start_node_moving = True
        self._make_fat_path = False
        if not self._end_node_moving:
            self._start_moving()

    def _start_moving(self):
        """ Low level toggle off things that slow drawing
        :return: None
        """
        if prefs.move_effect:
            self.setGraphicsEffect(self.move_effect)
            self._use_simple_path = True
            self.move_effect.setEnabled(True)

    def start_node_stopped_moving(self):
        """ Called if the end node has started moving.
        :return:
        """
        self._start_node_moving = False
        if not self._end_node_moving:
            self._stop_moving()

    def end_node_stopped_moving(self):
        """ Called if the end node has started moving.
        :return:
        """
        self._end_node_moving = False
        if not self._start_node_moving:
            self._stop_moving()

    def _stop_moving(self):
        """ Low level toggle back complex drawing
        :return: None
        """
        self._make_fat_path = True
        if prefs.move_effect:
            self._use_simple_path = False
            self.move_effect.setEnabled(False)

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    # Saved properties
    fixed_start_point = Saved("fixed_start_point")
    fixed_end_point = Saved("fixed_end_point")
    edge_type = Saved("edge_type")
    curve_adjustment = Saved("curve_adjustment", watcher="edge_adjustment")
    alignment = Saved("alignment")
    start = Saved("start")
    end = Saved("end")
    label_data = Saved("label_data", watcher="edge_label")
    local_shape_args = Saved("local_shape_args", watcher="edge_shape")
    color_id = SavedAndGetter("color_id", after_get=after_get_color_id, if_changed=if_changed_color_id)
    shape_name = SavedAndGetter("shape_name", after_get=after_get_shape_name,
                                if_changed=if_changed_shape_name)
    pull = SavedAndGetter("pull", after_get=after_get_pull)
    visible = Saved("visible", if_changed=if_changed_visible)


