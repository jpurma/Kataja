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
from kataja.SavedField import SavedField
from kataja.SavedObject import SavedObject
from kataja.singletons import ctrl, prefs
from kataja.settings.EdgeSettings import EdgeSettings
from kataja.uniqueness_generator import next_available_type_id
from kataja.utils import to_tuple, add_xy, time_me
from kataja.FadeInOut import FadeInOut
from kataja.EdgePath import EdgePath
from kataja.Shapes import SHAPE_PRESETS
from kataja.edge_styles import names


class Edge(QtWidgets.QGraphicsObject, SavedObject, FadeInOut):
    """ Connections between 2 nodes """

    __qt_type_id__ = next_available_type_id()

    def __init__(self, forest=None, start=None, end=None, edge_type='', alpha=None):
        """
        :param Node start:
        :param Node end:
        :param string edge_type:
        :param alpha: optional data for e.g. referring to third object
        """
        FadeInOut.__init__(self)
        SavedObject.__init__(self)
        QtWidgets.QGraphicsObject.__init__(self)
        self.forest = forest
        self.settings = EdgeSettings(self)
        self.edge_type = edge_type
        self.start = start
        self.start_links_to = None
        self.end_links_to = None
        self.end = end
        self.alpha = alpha
        self.start_symbol = 0
        self.curve_adjustment = None  # user's adjustments. contains (dist, angle) tuples.
        self.path = EdgePath(self)
        self.selected = False
        self._nodes_overlap = False
        self.k_tooltip = ''
        self.k_action = None
        self._is_moving = False

        self._local_drag_handle_position = None

        # ## Adjustable values, defaults to ForestSettings if None for this
        # element
        # based on the relation style

        # self.center_point = (0, 0, 0)

        # ## Derivative elements
        self._indirect_hovering = False
        self._direct_hovering = False
        self._start_node_moving = False
        self._end_node_moving = False
        self.setZValue(15)
        self.crossed_out_flag = False
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self._visible_by_logic = False
        self.cached_edge_start_index = (0, 1)
        self.cached_edge_end_index = (0, 1)
        self.hide()

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
        self.setZValue(self.settings.get('z_value'))
        # self.update_end_points()
        self.update_visibility()
        self.announce_creation()

    @property
    def forest(self):
        if self.start:
            return self.start.forest
        elif self.end:
            return self.end.forest

    def after_model_update(self, updated_fields, transition_type):
        """ Compute derived effects of updated values in sensible order.
        :param updated_fields: field keys of updates
        :param transition_type: 0:edit, 1:CREATED, -1:DELETED
        :return: None
        """
        if transition_type == g.CREATED:
            self.forest.store(self)
            self.forest.add_to_scene(self)
        elif transition_type == g.DELETED:
            ctrl.free_drawing.delete_edge(self, fade=False)
            return
        self.connect_end_points(self.start, self.end)
        self.update_visibility()
        # self.update_end_points()

    def cut(self, others=None):
        """ If edge ends are not included, set them to None, otherwise cut the edge as it is.
        :param others:
        :return:
        """
        self.connect_end_points(self.start if self.start in others else None,
                                self.end if self.end in others else None)
        self.forest.remove_from_scene(self)
        return self

    @property
    def color_key(self) -> str:
        return self.settings.get('color_key')

    @color_key.setter
    def color_key(self, value):
        self.path.changed = True
        self.settings.set('color_key', value)

    @property
    def shape_name(self) -> str:
        return self.settings.get('shape_name')

    @shape_name.setter
    def shape_name(self, value):
        self.path.changed = True
        self.settings.set('shape_name', value)

    @property
    def pull(self) -> float:
        return self.settings.get('pull')

    @pull.setter
    def pull(self, value):
        self.settings.set('pull', value)

    @property
    def start_point(self) -> tuple:
        """ Helper property: returns latest known (x, y, z) coords of
        starting point of the edge
        :return: tuple (x, y, z)
        """
        return self.path.computed_start_point if self.path else (0, 0)

    @property
    def end_point(self) -> tuple:
        """ Helper property: returns latest known (x, y, z) coords of ending
        point of the edge
        :return: tuple (x, y, z)
        """
        return self.path.computed_end_point if self.path else (0, 0)

    def show(self):
        if not self.isVisible():
            super().show()
        else:
            print('unnecessary show in edge')

    def final_start_node(self):
        if not self.start_links_to:
            return self.start
        else:
            return self.start_links_to.final_start_node()

    def chain_up(self, chain):
        if self.start_links_to:
            chain.append(self.start_links_to)
            return self.start_links_to.chain_up(chain)
        return chain

    def chain_down(self, chain):
        if self.end_links_to:
            chain.append(self)
            return self.end_links_to.chain_down(chain)
        return chain

    def final_end_node(self):
        if not self.end_links_to:
            return self.end
        else:
            return self.end_links_to.final_end_node()

    def update_start_symbol(self):
        if self.start_links_to:
            self.start_symbol = 0
        elif self.alpha:
            self.start_symbol = self.alpha.get_edge_start_symbol()
        else:
            self.start_symbol = 0

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
        start = self.start
        end = self.end
        if not (start and end):
            ctrl.free_drawing.delete_edge(self)
            return False
        lv = True
        if self._nodes_overlap:
            lv = False
        elif not start.is_visible():
            lv = False
        elif not end.is_visible():
            lv = False
        elif self.alpha and not self.alpha.is_visible():
            lv = False
        elif not self.settings.get('visible'):
            lv = False
        else:
            if self.edge_type == g.CONSTITUENT_EDGE:
                if end.locked_to_node:
                    lv = False
                elif (self.forest.visualization and
                      not self.forest.visualization.show_edges_for(start)):
                    lv = False
            elif self.edge_type == g.FEATURE_EDGE:
                if (start.node_type == g.CONSTITUENT_NODE and
                   start.is_card() and
                   ((not end.adjustment) or end.adjustment == (0, 0))):
                    lv = False
                    # elif end.locked_to_node is start and \
                    #        ((not end.adjustment) or end.adjustment == (0, 0)):
                    #    lv = False
            elif self.edge_type == g.CHECKING_EDGE:
                if self.forest.settings.get('feature_check_display') == 0:
                    lv = False

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
        internal color_key.
        :return: QColor
        """
        return ctrl.cm.get(self.color_key)


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

    def __lt__(self, other):
        return self.edge_start_index()[0] < other.edge_start_index()[0]

    def __gt__(self, other):
        return self.edge_start_index()[0] > other.edge_start_index()[0]

    def edge_start_index(self, from_cache=True) -> tuple:
        """ Return tuple where first value is the order of this edge among similar type of edges
        for this parent (parent = edge.start) and the second is the total amount of siblings (
        edges of this type)
        :return:
        """
        if from_cache:
            return self.cached_edge_start_index
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

    def edge_end_index(self, from_cache=True) -> tuple:
        """ Return tuple where first value is the order of this edge among similar type of edges
        for this child (child = edge.end) and the second is the total amount of parents (
        edges of this type)
        :return:
        """
        if from_cache:
            return self.cached_edge_end_index
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
        if self.color_key:
            base = ctrl.cm.get(self.color_key)
        elif self.alpha and hasattr(self.alpha, 'color'): #hasattr(self.alpha, 'get_color_key'):
            base = self.alpha.color # ctrl.cm.get(self.alpha.get_color_key())
        elif self.end:
            base = self.end.color # get_color_key())
        else:
            base = ctrl.cm.get('content1')

        if ctrl.pressed == self:
            return ctrl.cm.active(base)
        elif self.hovering:
            return ctrl.cm.hovering(base)
        else:
            return base


    # ### Derivative features ############################################

    def make_path(self):
        self.path.make()
        if self.selected:
            ctrl.ui.update_position_for(self)
        # overlap detection is costly, so do checks for cases that make it unnecessary
        if self.edge_type == g.FEATURE_EDGE or self.edge_type == g.CHECKING_EDGE:
            self._nodes_overlap = False
        elif self.forest.visualization and not self.forest.visualization.hide_edges_if_nodes_overlap:
            self._nodes_overlap = False
        elif self.start and self.end and False:
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

    def reset_settings(self):
        self._settings = {}
        self.path.my_shape = SHAPE_PRESETS[self.shape_name]()
        self.curve_adjustment = [(0, 0)] * len(self.path.control_points)
        self.update_shape()

    def update_shape(self):
        """ Reload shape and shape settings """
        cpl = len(self.path.control_points)
        self.make_path()
        if cpl != len(self.path.control_points):
            ctrl.ui.update_control_points()
        self.update()

    def connect_end_points(self, start, end):
        """

        :param start:
        :param end:
        """
        self.start = start
        self.end = end
        self.path.computed_start_point = start.current_scene_position if start else (0, 0)
        self.path.computed_end_point = end.current_scene_position if end else (0, 0)

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

    def __repr__(self):
        return f'{names[self.edge_type][0]} from {self.start} to {self.end}'

    def update_selection_status(self, selected):
        """ Switch

        :param selected:
        """
        self.selected = selected
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

    def start_hovering(self):
        self._direct_hovering = True
        self.hovering = True
        self.final_start_node().hovering = True
        self.final_end_node().hovering = True

    def stop_hovering(self):
        self._direct_hovering = False
        self.hovering = False
        self.final_start_node().hovering = False
        self.final_end_node().hovering = False

    @property
    def hovering(self):
        return self._indirect_hovering or self._direct_hovering

    @hovering.setter
    def hovering(self, value):
        if value and not self._indirect_hovering:
            self._indirect_hovering = True
            self.prepareGeometryChange()
            self.update()
        elif (not value) and self._indirect_hovering:
            self._indirect_hovering = False
            self.prepareGeometryChange()
            self.setZValue(self.settings.get('z_value'))
            self.update()

    def hoverEnterEvent(self, event):
        if not self._direct_hovering:
            self.start_hovering()
            if not ctrl.scene_moving:
                ctrl.ui.show_help(self, event)
        event.accept()
        # QtWidgets.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverMoveEvent(self, event):
        if not ctrl.scene_moving:
            ctrl.ui.move_help(event)

    def hoverLeaveEvent(self, event):
        if self._direct_hovering:
            self.stop_hovering()
            ctrl.ui.hide_help(self, event)
        self.hovering = False

    # ## Scene-managed call

    def select(self, adding=False, select_area=False):
        """ Scene has decided that this edge has been clicked
        :param adding: bool, we are adding to selection instead of starting a new selection
        :param select_area: bool, we are dragging a selection box, method only informs that
         this edge can be included
        :returns: self if item is selectable
        """
        self.hovering = False
        # if we are selecting an area, select actions are not called here, but once for all
        # objects. In this case return only uid of this object.
        if select_area:
            return self
        if adding:
            if self.selected:
                action = ctrl.ui.get_action('remove_from_selection')
            else:
                action = ctrl.ui.get_action('add_to_selection')
            action.run_command(self.uid, has_params=True)
        else:
            action = ctrl.ui.get_action('select')
            action.run_command(self.uid, has_params=True)
        return self

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
                thickness = self.settings.get_shape('thickness')
                p = QtGui.QPen()
                p.setColor(c)
                p.setCapStyle(QtCore.Qt.RoundCap)
                p.setWidthF(thickness)
                painter.setPen(p)
                painter.drawPath(dpath)

            if self.is_filled():
                painter.fillPath(dpath, c)

            if self.path.arrowhead_start_path:
                painter.fillPath(self.path.arrowhead_start_path, c)
            if self.path.arrowhead_end_path:
                painter.fillPath(self.path.arrowhead_end_path, c)

        if self.selected and not ctrl.multiple_selection():
            p = QtGui.QPen(ctrl.cm.ui_tr())
            self.path.draw_control_point_hints(painter, p, self.curve_adjustment)
        if self.crossed_out_flag:
            cx, cy = to_tuple(self._true_path.pointAtPercent(0.5))
            p = QtGui.QPen(ctrl.cm.ui())
            p.setWidthF(1.0)
            painter.setPen(p)
            painter.drawLine(QtCore.QLineF(cx - 20, cy - 10, cx + 20, cy + 10))
            painter.drawLine(QtCore.QLineF(cx - 20, cy + 10, cx + 20, cy - 10))

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
        self.setAcceptHoverEvents(False)
        # if prefs.move_effect:
        self._use_simple_path = True

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
        self.setAcceptHoverEvents(True)
        # if prefs.move_effect:
        #    self._use_simple_path = False

    # Shape helpers #############################

    def get_shape_property(self, key, missing=None):
        return getattr(self.path.my_shape, key)

    def set_leaf_width(self, value):
        self.settings.set('leaf_x', value)
        self.path.changed = True
        self.update_shape()

    def set_leaf_height(self, value):
        self.settings.set('leaf_y', value)
        self.path.changed = True
        self.update_shape()

    def change_edge_relative_curvature_x(self, value):
        self.settings.set('rel_dx', value * .01)
        self.path.changed = True
        self.update_shape()

    def change_edge_relative_curvature_y(self, value):
        self.settings.set('rel_dy', value * .01)
        self.path.changed = True
        self.update_shape()

    def change_edge_fixed_curvature_x(self, value):
        self.settings.set('fixed_dx', value)
        self.path.changed = True
        self.update_shape()

    def change_edge_fixed_curvature_y(self, value):
        self.settings.set('fixed_dy', value)
        self.path.changed = True
        self.update_shape()

    def set_thickness(self, value):
        self.settings.set('thickness', value)
        self.path.changed = True
        self.update_shape()

    def is_filled(self) -> bool:
        return self.get_shape_property('fillable') and self.settings.get_shape('fill')

    def has_outline(self) -> int:
        return self.settings.get_shape('outline')

    def is_fillable(self):
        return self.get_shape_property('fillable')

    def set_fill(self, value):
        self.settings.set('fill', value)
        self.path.changed = True
        self.update_shape()

    def set_outline(self, value):
        self.settings.set('outline', value)
        self.path.changed = True
        self.update_shape()

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
    edge_type = SavedField("edge_type")
    curve_adjustment = SavedField("curve_adjustment")
    start = SavedField("start")
    end = SavedField("end")
    alpha = SavedField("alpha")
    forest = SavedField("forest")
