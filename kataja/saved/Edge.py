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


import time
from PyQt5 import QtCore, QtGui, QtWidgets
from collections import ChainMap

import kataja.globals as g
from kataja.EdgeLabel import EdgeLabel
from kataja.SavedField import SavedField
from kataja.SavedObject import SavedObject
from kataja.singletons import ctrl, prefs
from kataja.uniqueness_generator import next_available_type_id
from kataja.utils import to_tuple, add_xy, time_me
from kataja.FadeInOut import FadeInOut
from kataja.EdgePath import EdgePath


class Edge(QtWidgets.QGraphicsObject, SavedObject, FadeInOut):
    """ Any connection between nodes: can be represented as curves, branches
    or arrows """

    __qt_type_id__ = next_available_type_id()

    def __init__(self, start=None, end=None, edge_type='', extra=None):
        """
        :param Node start:
        :param Node end:
        :param string edge_type:
        :param extra: optional data for e.g. referring to third object
        """
        FadeInOut.__init__(self)
        SavedObject.__init__(self)
        QtWidgets.QGraphicsObject.__init__(self)
        self.label_item = None
        self.edge_type = edge_type
        self.start = start
        self.end = end
        self.extra = extra
        self.fixed_start_point = (0, 0)
        self.fixed_end_point = (0, 0)
        self.curve_adjustment = None  # user's adjustments. contains (dist, angle) tuples.
        self.path = EdgePath(self)
        self.label_data = {}
        self.selected = False
        self._nodes_overlap = False
        self.k_tooltip = ''
        self.k_action = None
        self._is_moving = False
        self.shape_settings_chain = None

        self.in_projections = []

        self._local_drag_handle_position = None

        # ## Adjustable values, defaults to ForestSettings if None for this
        # element
        # based on the relation style

        # self.center_point = (0, 0, 0)

        # ## Derivative elements
        self._hovering = False
        self._start_node_moving = False
        self._end_node_moving = False
        self.setZValue(5)
        self.crossed_out_flag = False
        self._use_labels = None
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self._visible_by_logic = True

    def type(self) -> int:
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

    def after_init(self):
        """ After_init is called in 2nd step in process of creating objects:
            1st wave creates the objects and calls __init__, and then
            iterates through and sets the values.
            2nd wave calls after_inits for all created objects. Now they can
            properly refer to each other and know their
                values.
        :return: None
        """
        self.connect_end_points(self.start, self.end)
        self.setZValue(self.get_edge_setting('z_value'))
        #self.update_end_points()
        self.update_visibility()
        self.announce_creation()

    def after_model_update(self, updated_fields, transition_type):
        """ Compute derived effects of updated values in sensible order.
        :param updated_fields: field keys of updates
        :param transition_type: 0:edit, 1:CREATED, -1:DELETED
        :return: None
        """
        if transition_type == g.CREATED:
            ctrl.forest.store(self)
            ctrl.forest.add_to_scene(self)
            print(self.start, self.end)
        elif transition_type == g.DELETED:
            ctrl.free_drawing.delete_edge(self, fade=False)
            return
        self.connect_end_points(self.start, self.end)
        self.update_visibility()
        #self.update_end_points()

    def cut(self, others=None):
        """ If edge ends are not included, set them to None, otherwise cut the edge as it is.
        :param others:
        :return:
        """
        start = None
        end = None
        if self.start and self.start in others:
            start = self.start
        if self.end and self.end in others:
            end = self.end
        self.connect_end_points(start, end)
        ctrl.forest.remove_from_scene(self)
        return self

    @property
    def color_id(self) -> str:
        return self.get_edge_setting('color_id')

    @color_id.setter
    def color_id(self, value):
        self.path.changed = True
        ctrl.settings.set_edge_setting('color_id', value, edge=self)

    @property
    def shape_name(self) -> str:
        return self.get_edge_setting('shape_name')

    @shape_name.setter
    def shape_name(self, value):
        self.path.changed = True
        ctrl.settings.set_edge_setting('shape_name', value, edge=self)

    @property
    def pull(self) -> float:
        return self.get_edge_setting('pull')

    @pull.setter
    def pull(self, value):
        ctrl.settings.set_edge_setting('pull', value, edge=self)

    @property
    def start_point(self) -> tuple:
        """ Helper property: returns latest known (x, y, z) coords of
        starting point of the edge
        :return: tuple (x, y, z)
        """
        if self.start:
            return self.path.computed_start_point
        else:
            return self.fixed_start_point

    @property
    def end_point(self) -> tuple:
        """ Helper property: returns latest known (x, y, z) coords of ending
        point of the edge
        :return: tuple (x, y, z)
        """
        if self.end:
            return self.path.computed_end_point
        else:
            return self.fixed_end_point

    def show(self):
        if not self.isVisible():
            super().show()
        else:
            print('unnecessary show in edge')

    def update_visibility(self, fade_in=True, fade_out=True) -> bool:
        """ Hide or show according to various factors, which allow edge
        to exist but not be drawn.
        This is called logical visibility and can be checked with is_visible().
        Qt's isVisible() checks for scene visibility. Items that are e.g. fading away
        have False for logical visibility but True for scene visibility and items that are part
        of graph in a forest that is not currently drawn may have True for logical visibility but
        false for scene visibility.
        :return:
        """
        lv = True
        if self._nodes_overlap:
            lv = False
        elif self.start and not self.start.is_visible():
            lv = False
        else:
            start = self.start
            end = self.end
            delete = False
            if self.edge_type == g.CONSTITUENT_EDGE:
                if end and not end.is_visible():
                    lv = False
                elif start and ctrl.forest.visualization and not \
                        ctrl.forest.visualization.show_edges_for(start):
                    lv = False
                elif not (start and end):
                    ctrl.free_drawing.delete_edge(self)
                    return False
                elif end.locked_to_node:
                    lv = False
            elif self.edge_type == g.FEATURE_EDGE:
                if start and end:
                    if not (end.is_visible() and start.is_visible()):
                        lv = False
                    elif start.get_node_shape() == g.CARD and (
                                (not end.adjustment) or end.adjustment == (0, 0)):
                        lv = False
                    #elif end.locked_to_node is start and \
                    #        ((not end.adjustment) or end.adjustment == (0, 0)):
                    #    lv = False
                else:
                    delete = True
            elif self.edge_type == g.CHECKING_EDGE:
                if start and end:
                    if not (end.is_visible() and start.is_visible()):
                        lv = False
                    elif ctrl.settings.get('feature_check_display') == 0:
                        lv = False
                else:
                    delete = True

            if delete:
                ctrl.free_drawing.delete_edge(self)
                return False

        self._visible_by_logic = lv
        # Change visibility if necessary, with fade or instantly.
        # If forest is not drawn, only the logical visibility matters -- do nothing
        if self.scene():
            if lv:
                if self.is_fading_out:
                    if fade_in:
                        self.fade_in()
                        return True
                    else:
                        self.is_fading_out = False
                        self._fade_out_anim.stop()
                        self.setOpacity(1.0)
                        return True
                if not self.isVisible():
                    if fade_in:
                        self.fade_in()
                        return True
                    else:
                        self.show()
                        return True
            else:
                if self.isVisible():
                    if fade_out:
                        self.fade_out()
                        return True
                    else:
                        self.hide()
                        return True
        return False

    # Edge type - based settings that can be overridden

    @property
    def color(self) -> QtGui.QColor:
        """ Color for drawing the edge -- both the fill and pen color.
        Returns QColor, but what is stored is Kataja
        internal color_id.
        :return: QColor
        """
        return ctrl.cm.get(self.color_id)

    def if_changed_color_id(self, value):
        """ Set edge color, uses palette id strings as values.
        :param value: string
        """
        if self.label_item:
            self.label_item.setDefaultTextColor(ctrl.cm.get(value))

    # ## Label data and its shortcut properties

    def get_label_text(self) -> str:
        """ Label text is actually stored in model.label_data, but this is a
        shortcut for it.
        :return:
        """
        return self.label_data.get('text', '')

    def set_label_text(self, value):
        if self.label_item:
            old = self.get_label_text()
            if old != value:
                self.poke('label_data')
                self.label_data['text'] = value
                self.label_item.update_text(value)
        else:
            self.label_item = EdgeLabel(value, parent=self)
            self.poke('label_data')
            self.label_data['text'] = value

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

    def is_visible(self) -> bool:
        return self._visible_by_logic

    def connect_start_to(self, node):
        """

        :param node:
        """
        ctrl.free_drawing.set_edge_start(self, node)
        self.update_shape()

    def connect_end_to(self, node):
        """

        :param node:
        """
        ctrl.free_drawing.set_edge_end(self, node)
        self.update_shape()

    def is_broken(self) -> bool:
        """ If this edge should be a connection between two nodes and either
        node is missing, the edge
        is broken and should be displayed differently.
        :return: bool
        """
        if self.edge_type == g.ARROW:
            return False
        return not (self.start and self.end)

    def edge_start_index(self) -> tuple:
        """ Return tuple where first value is the order of this edge among similar type of edges
        for this parent (parent = edge.start) and the second is the total amount of siblings (
        edges of this type)
        :return:
        """
        if not self.start:
            return 0, 0
        count = 0
        found = 0
        for ed in self.start.edges_down:
            if ed.edge_type == self.edge_type:
                if ed is self:
                    found = count
                count += 1
        return found, count

    def edge_end_index(self) -> tuple:
        """ Return tuple where first value is the order of this edge among similar type of edges
        for this child (child = edge.end) and the second is the total amount of parents (
        edges of this type)
        :return:
        """
        if not self.end:
            return 0, 0
        count = 0
        found = 0
        for ed in self.end.edges_up:
            if ed.edge_type == self.edge_type:
                if ed is self:
                    found = count
                count += 1
        return found, count

    def direction(self) -> int:
        """ Coarse direction of this edge, either g.LEFT or g.RIGHT. Useful for knowing if
         to prepend or append the sibling node compared to this.
        :return:
        """
        en, ecount = self.edge_start_index()
        if en < ecount / 2:
            return g.LEFT
        else:
            return g.RIGHT

    # ### Color ############################################################

    def contextual_color(self) -> QtGui.QColor:
        """ Drawing color that is sensitive to edge's state
        :return: QColor
        """
        if self.in_projections and self.in_projections[0].style == g.COLORIZE_PROJECTIONS:
            base = ctrl.cm.get(self.in_projections[0].color_id)
        elif self.color_id:
            base = ctrl.cm.get(self.color_id)
        elif self.extra and hasattr(self.extra, 'get_color_id'):
            base = ctrl.cm.get(self.extra.get_color_id())
        elif self.end:
            base = ctrl.cm.get(self.end.get_color_id())
        else:
            base = ctrl.cm.get('content1')

        if ctrl.pressed == self:
            return ctrl.cm.active(base)
        elif self._hovering:
            return ctrl.cm.hovering(base)
        elif self.is_broken():
            return ctrl.cm.broken(base)
        else:
            return base

    def uses_labels(self) -> bool:
        """ Some edge types, e.g. arrows inherently suggest adding labels to
        them. For others, having ui_support
         textbox for adding label would be unwanted noise.
        :return: bool
        """
        return self.get_edge_setting('labeled')

    # ### Shape / pull / visibility
    # ###############################################################

    def drag(self, event):
        """ This is for dragging the whole edge in cases when edge is not
        connected to nodes at any point
        e.g. it is freely floating arrow or divider
        :param event: Drag event?
        """
        # self.draggable = not (self.start or self.end)

        scene_x, scene_y = to_tuple(event.scenePos())
        ex, ey = self.end_point
        sx, sy = self.start_point
        if not self._local_drag_handle_position:
            drag_x, drag_y = to_tuple(event.buttonDownScenePos(QtCore.Qt.LeftButton))
            self._local_drag_handle_position = drag_x - sx, drag_y - sy
        handle_x, handle_y = self._local_drag_handle_position
        start_x = scene_x - handle_x
        start_y = scene_y - handle_y
        if not self.start:
            self.fixed_start_point = start_x, start_y
        if not self.end:
            self.fixed_end_point = start_x + ex - sx, start_y + ey - sy

    # # Not used. What is this for?
    # def compute_pos_from_adjust(self, point_index) -> tuple:
    #     """ Works with 1 or 2 control points.
    #     :param point_index:
    #     :return:
    #     """
    #     cx, cy = self.control_points[point_index]
    #     rdist, rrad = self.curve_adjustment[point_index]
    #     sx, sy = self.start_point if point_index == 0 else self.end_point
    #     sx_to_cx = cx - sx
    #     sy_to_cy = cy - sy
    #     line_rad = math.atan2(sy_to_cy, sx_to_cx)
    #     line_dist = math.hypot(sx_to_cx, sy_to_cy)
    #     new_dist = rdist * line_dist
    #     new_x = cx + (new_dist * math.cos(rrad + line_rad))
    #     new_y = cy + (new_dist * math.sin(rrad + line_rad))
    #     return new_x, new_y

    # ### Derivative features ############################################

    def make_path(self):
        self.path.make()
        if self.label_item:
            self.label_item.update_position()
        if self.selected:
            ctrl.ui.update_position_for(self)
        # overlap detection is costly, so do checks for cases that make it unnecessary
        if self.edge_type == g.FEATURE_EDGE or self.edge_type == g.CHECKING_EDGE:
            self._nodes_overlap = False
        elif not ctrl.settings.get('hide_edges_if_nodes_overlap'):
            self._nodes_overlap = False
        elif self.start and self.end:
            if self.end.locked_to_node:
                self._nodes_overlap = False
            elif self.start.is_visible() and self.end.is_visible():
                self._nodes_overlap = self.start.overlap_rect().intersects(self.end.overlap_rect())
            else:
                self._nodes_overlap = False
        else:
            self._nodes_overlap = False
        self.update_visibility()
        if not self._is_moving:
            self.update_tooltip()

    # override
    def boundingRect(self):
        return self.path.boundingRect()

    # override
    def shape(self) -> QtGui.QPainterPath:
        """ Overrides the QGraphicsItem method.
        :return: QGraphicsPath
        """
        return self.path.shape()

    def reset_style(self):
        self.shape_name = None
        ctrl.settings.reset_edge_settings(edge=self)
        self.curve_adjustment = [(0, 0)] * len(self.control_points)
        self.update_shape()

    def update_shape(self):
        """ Reload shape and shape settings """
        cpl = len(self.path.control_points)
        self.make_path()
        # while len(self.curve_adjustment) < len(self.control_points):
        # self.curve_adjustment.append((0, 0, 0))
        if cpl != len(self.path.control_points):
            ctrl.ui.update_control_points()
        self.update()

    def connect_end_points(self, start, end):
        """

        :param start:
        :param end:
        """
        if start:
            self.path.computed_start_point = start.current_scene_position
            self.start = start
        else:
            self.start = None
        if end:
            self.path.computed_end_point = end.current_scene_position
            self.end = end
        else:
            self.end = None

    def update_tooltip(self):
        """

        :return:
        """
        if self.edge_type == g.CONSTITUENT_EDGE:
            tt_style = f'<tt style="background:{ctrl.cm.paper2().name()};">%s</tt>'

            s_uid = self.start.uid if self.start else ''
            e_uid = self.end.uid if self.end else ''
            sx, sy = self.start_point
            ex, ey = self.end_point
            self.k_tooltip = f"""<strong>Constituent relation</strong><br/>
            from {tt_style % s_uid} (x:{int(sx)}, y:{int(sy)})<br/>
             to {tt_style % e_uid} (x:{int(ex)}, y:{int(ey)}) <br/> 
            uid:{tt_style % self.uid}"""

    def description(self):
        """

        :return:
        """
        label = 'Arrow' if self.edge_type == g.ARROW else 'Edge'
        if self.start:
            s1 = f'"{self.start}"'
        elif self.fixed_start_point:
            s1 = f'({int(self.start_point[0])}, {int(self.start_point[1])})'
        else:
            s1 = 'undefined'
        if self.end:
            s2 = f'"{self.end}"'
        elif self.fixed_end_point:
            s2 = f'({int(self.end_point[0])}, {int(self.end_point[1])})'
        else:
            s2 = 'undefined'
        return f'{label} from {s1} to {s2}'

    def __repr__(self):
        return self.description()

    def delete_on_disconnect(self):
        """ Some edges are not real edges, but can have sensible existence without being
        connected to nodes. Some are better to destroy at that point.
        :return:
        """
        return self.allow_orphan_ends()

    def allow_orphan_ends(self):
        """

        :return:
        """
        return self.edge_type is g.ARROW or self.edge_type is g.DIVIDER

    def update_selection_status(self, selected):
        """ Switch

        :param selected:
        """
        self.selected = selected
        if selected:
            if self.uses_labels():
                if not self.label_item:
                    self.label_item = EdgeLabel('', self, placeholder=True)
                    self.label_item.update_position()
        else:
            if self.label_item:
                if self.label_item.placeholder:
                    scene = self.scene()
                    if scene:
                        scene.removeItem(self.label_item)
                    self.label_item = None
        self.update()


    # ### Mouse - Qt events ##################################################

    def mousePressEvent(self, event):
        ctrl.press(self)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if ctrl.pressed is self:
            if ctrl.dragged_set or (event.buttonDownScenePos(
                    QtCore.Qt.LeftButton) - event.scenePos()).manhattanLength() > 6:
                self.drag(event)
                ctrl.graph_scene.dragging_over(event.scenePos())

    def mouseReleaseEvent(self, event):
        if ctrl.pressed is self:
            ctrl.release(self)
            if ctrl.dragged_set:
                self._local_drag_handle_position = None
                ctrl.graph_scene.kill_dragging()
                ctrl.ui.update_selections()  # drag operation may have changed visible affordances
            else:  # This is regular click on 'pressed' object
                shift = event.modifiers() == QtCore.Qt.ShiftModifier
                self.select(adding=shift, select_area=False)
                self.update()
            return None  # this mouseRelease is now consumed
        super().mouseReleaseEvent(event)

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
            self.prepareGeometryChange()
            self.update()
        elif (not value) and self._hovering:
            self._hovering = False
            self.prepareGeometryChange()
            self.setZValue(self.get_edge_setting('z_value'))
            self.update()

    def hoverEnterEvent(self, event):
        """
        Overrides (and calls) QtWidgets.QGraphicsItem.hoverEnterEvent
        Toggles hovering state and necessary graphical effects.
        :param event:
        """
        if self._is_moving:
            return
        self.hovering = True
        ctrl.ui.show_help(self, event)
        event.accept()
        #QtWidgets.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverMoveEvent(self, event):
        if self._is_moving:
            return
        ctrl.ui.move_help(event)
        QtWidgets.QGraphicsObject.hoverMoveEvent(self, event)

    def hoverLeaveEvent(self, event):
        """

        :param event:
        """
        if self.hovering:
            self.hovering = False
            ctrl.ui.hide_help(self, event)
            QtWidgets.QGraphicsItem.hoverLeaveEvent(self, event)


    # ## Scene-managed call

    def select(self, adding=False, select_area=False):
        """ Scene has decided that this edge has been clicked
        :param adding: bool, we are adding to selection instead of starting a new selection
        :param select_area: bool, we are dragging a selection box, method only informs that
         this edge can be included
        :returns: int or str, uid of node if node is selectable
        """
        self.hovering = False
        # if we are selecting an area, select actions are not called here, but once for all
        # objects. In this case return only uid of this object.
        if select_area:
            return self.uid
        if adding:
            if self.selected:
                action = ctrl.ui.get_action('remove_from_selection')
            else:
                action = ctrl.ui.get_action('add_to_selection')
            action.run_command(self.uid, has_params=True)
        else:
            action = ctrl.ui.get_action('select')
            action.run_command(self.uid, has_params=True)
        return self.uid

    # ## Qt paint method override
    def paint(self, painter, option, widget=None):
        """

        :param painter:
        :param option:
        :param widget:
        :return:
        """
        c = self.contextual_color()
        sx, sy = self.start_point
        ex, ey = self.end_point
        if self.path.use_simple_path:
            p = QtGui.QPen()
            p.setColor(c)
            painter.setPen(p)
            painter.drawPath(self.path.true_path)
        else:
            dpath = self.path.draw_path
            if self.has_outline():
                thickness = self.get_shape_setting('thickness')
                p = QtGui.QPen()
                p.setColor(c)
                p.setCapStyle(QtCore.Qt.RoundCap)
                # Show many projections
                if self.in_projections and self.in_projections[0].style == g.COLORIZE_PROJECTIONS:
                    p.setWidthF(thickness)
                    left = sx > ex
                    for i, proj in enumerate(self.in_projections):
                        cp = QtGui.QPen(p)
                        cp.setColor(ctrl.cm.get(proj.color_id))
                        painter.setPen(cp)
                        if left:
                            painter.drawPath(dpath.translated(i, i))
                        else:
                            painter.drawPath(dpath.translated(-i, i))
                else:
                    p.setWidthF(thickness)
                    painter.setPen(p)
                    painter.drawPath(dpath)

            if self.is_filled():
                if self.in_projections and self.in_projections[0].style == g.COLORIZE_PROJECTIONS:
                    left = sx > ex
                    for i, proj in enumerate(self.in_projections):
                        cp = ctrl.cm.get(proj.color_id)
                        if left:
                            painter.fillPath(self._path.translated(i, i), cp)
                        else:
                            painter.fillPath(self._path.translated(-i, i), cp)
                else:
                    painter.fillPath(dpath, c)

            if self.path.arrowhead_start_path:
                painter.fillPath(self.path.arrowhead_start_path, c)
            if self.path.arrowhead_end_path:
                painter.fillPath(self.path.arrowhead_end_path, c)

        if self.selected:
            p = QtGui.QPen(ctrl.cm.ui_tr())
            self.path.draw_control_point_hints(painter, p, self.curve_adjustment)
        if self.crossed_out_flag:
            cx, cy = to_tuple(self._true_path.pointAtPercent(0.5))
            p = QtGui.QPen(ctrl.cm.ui())
            p.setWidthF(1.0)
            painter.setPen(p)
            painter.drawLine(cx - 20, cy - 10, cx + 20, cy + 10)
            painter.drawLine(cx - 20, cy + 10, cx + 20, cy - 10)

    def end_node_started_moving(self):
        """ Called if the end node has started moving.
        :return:
        """
        self._end_node_moving = True
        self.path.make_fat_path = False
        if not self._start_node_moving:
            self._start_moving()

    def start_node_started_moving(self):
        """ Called if the end node has started moving.
        :return:
        """
        self._start_node_moving = True
        self.path.make_fat_path = False
        if not self._end_node_moving:
            self._start_moving()

    def _start_moving(self):
        """ Low level toggle off things that slow drawing
        :return: None
        """
        self._is_moving = True
        #if prefs.move_effect:
        #    self._use_simple_path = True

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
        self._is_moving = False
        self.path.make_fat_path = True
        #if prefs.move_effect:
        #    self._use_simple_path = False

    def free_drawing_mode(self, *args, **kwargs):
        """ Utility method for checking conditions for editing operations
        :param args: ignored
        :param kwargs: ignored
        :return:
        """
        return ctrl.free_drawing_mode

    # Shape helpers #############################

    def get_shape_setting(self, key, missing=None):
        return ctrl.settings.get_shape_setting(key, edge=self) or missing

    def get_shape_property(self, key, missing=None):
        return getattr(self.path.my_shape, key)

    def get_edge_setting(self, key):
        return ctrl.settings.get_edge_setting(key, self.edge_type)

    def set_arrowhead_at_start(self, value):
        ctrl.settings.set_edge_setting('arrowhead_at_start', value, edge=self)

    def set_arrowhead_at_end(self, value):
        ctrl.settings.set_edge_setting('arrowhead_at_end', value, edge=self)

    def set_leaf_width(self, value):
        ctrl.settings.set_edge_setting('leaf_x', value, edge=self)
        self.update_shape()

    def set_leaf_height(self, value):
        ctrl.settings.set_edge_setting('leaf_y', value, edge=self)
        self.update_shape()

    def reset_leaf_shape(self):
        ctrl.settings.del_shape_setting('leaf_x', edge=self)
        ctrl.settings.del_shape_setting('leaf_y', edge=self)
        self.update_shape()

    def change_edge_relative_curvature_x(self, value):
        ctrl.settings.set_edge_setting('rel_dx', value * .01, edge=self)
        self.update_shape()

    def change_edge_relative_curvature_y(self, value):
        ctrl.settings.set_edge_setting('rel_dy', value * .01, edge=self)
        self.update_shape()

    def change_edge_fixed_curvature_x(self, value):
        ctrl.settings.set_edge_setting('fixed_dx', value, edge=self)
        self.update_shape()

    def change_edge_fixed_curvature_y(self, value):
        ctrl.settings.set_edge_setting('fixed_dy', value, edge=self)
        self.update_shape()

    def reset_edge_curvature(self):
        ctrl.settings.del_shape_setting('rel_dx', edge=self)
        ctrl.settings.del_shape_setting('rel_dy', edge=self)
        ctrl.settings.del_shape_setting('fixed_dx', edge=self)
        ctrl.settings.del_shape_setting('fixed_dy', edge=self)
        self.update_shape()

    def reset_thickness(self):
        ctrl.settings.del_shape_setting('thickness', edge=self)
        self.update_shape()

    def set_thickness(self, value):
        ctrl.settings.set_edge_setting('thickness', value, edge=self)
        self.update_shape()


    def is_filled(self) -> bool:
        return self.get_shape_property('fillable') and self.get_shape_setting('fill')

    def has_outline(self) -> int:
        fillable = self.get_shape_property('fillable')
        return (fillable and self.get_shape_setting('outline')) or not fillable

    def is_fillable(self):
        return self.get_shape_property('fillable')

    def set_fill(self, value):
        ctrl.settings.set_edge_setting('fill', value, edge=self)
        self.update_shape()

    def set_outline(self, value):
        ctrl.settings.set_edge_setting('outline', value, edge=self)
        self.update_shape()


    @staticmethod
    def is_active_fillable():
        return ctrl.settings.get_active_shape_property('fillable')

    @staticmethod
    def has_active_outline():
        fillable = ctrl.settings.get_active_shape_property('fillable')
        if fillable:
            return ctrl.settings.get_active_shape_setting('outline')
        return True

    @staticmethod
    def has_active_fill():
        fillable = ctrl.settings.get_active_shape_property('fillable')
        if fillable:
            return ctrl.settings.get_active_shape_setting('fill')
        return False

    @staticmethod
    def get_active_color():
        fillable = ctrl.settings.get_active_shape_property('fillable')
        if fillable:
            return ctrl.settings.get_active_shape_setting('outline')
        return True


    def prepare_adjust_array(self, index):
        """

        :param index:
        """
        if self.curve_adjustment is None:
            self.curve_adjustment = [(0, 0)]
        while index >= len(self.curve_adjustment):
            self.curve_adjustment.append((0, 0))

    def adjust_control_point(self, index, dist=None, rad=None):
        """ Called from UI, when dragging
        :param index:
        :param dist:
        :param rad:
        """
        self.poke('curve_adjustment')
        self.prepare_adjust_array(index)
        odist, orad = self.curve_adjustment[index]
        if dist is None:
            dist = odist
        if rad is None:
            rad = orad
        self.curve_adjustment[index] = dist, rad
        self.call_watchers('edge_adjustment', 'curve_adjustment', self.curve_adjustment)
        self.path.changed = True
        self.make_path()
        self.update()

    def reset_control_points(self):
        """
        Set adjustments back to zero
        :return:
        """

        n = self.get_shape_property('control_points_n')
        self.poke('curve_adjustment')
        self.curve_adjustment = [(0, 0)] * n
        self.make_path()
        self.update()

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    # Saved properties
    fixed_start_point = SavedField("fixed_start_point")
    fixed_end_point = SavedField("fixed_end_point")
    edge_type = SavedField("edge_type")
    curve_adjustment = SavedField("curve_adjustment", watcher="edge_adjustment")
    start = SavedField("start")
    end = SavedField("end")
    extra = SavedField("extra")
    forest = SavedField("forest")
    label_data = SavedField("label_data")
