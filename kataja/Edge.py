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

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPointF as Pf, Qt

from kataja.singletons import ctrl
import kataja.globals as g
from kataja.globals import LEFT, RIGHT, NO_ALIGN
from kataja.shapes import SHAPE_PRESETS, to_Pf, outline_stroker
from kataja import utils


# ('shaped_relative_linear',{'method':shapedRelativeLinearPath,'fill':True,'pen':'thin'}),


class Edge(QtWidgets.QGraphicsItem):
    """ Any connection between nodes: can be represented as curves, branches or arrows """

    z_value = 10
    saved_fields = ['forest', 'edge_type', 'adjust', 'start', 'end', '_color', '_shape_name', '_pull', '_shape_visible',
                    '_visible']

    receives_signals = [g.EDGE_SHAPES_CHANGED]

    def __init__(self, forest, start=None, end=None, edge_type='', direction=''):
        """

        :param Forest forest:
        :param Node start:
        :param Node end:
        :param string edge_type:
        :param string direction:
        :param string restoring:
        """
        QtWidgets.QGraphicsItem.__init__(self)
        self.forest = forest
        self.save_key = 'R%s' % id(self)

        self.start_point = (0, 0, 0)
        self.end_point = (0, 0, 0)
        self.setZValue(-1)
        self.edge_type = edge_type
        self.control_points = []
        self.middle_point = None
        self.adjust = []
        self.has_outline = False
        self.is_filled = None

        if isinstance(direction, str):
            if direction == 'left':
                self.align = LEFT
            elif direction == 'right':
                self.align = RIGHT
            else:
                self.align = NO_ALIGN
        elif isinstance(direction, int):
            self.align = direction
        self.start = start
        self.end = end

        # ## Adjustable values, defaults to ForestSettings if None for this element
        self._color = None
        self._pen = None
        self._pen_width = None
        self._brush = None
        self._shape_name = None
        self._pull = None
        self._shape_visible = None

        # self.center_point = (0, 0, 0)

        # ## Derivative elements
        self._shape_method = None
        self._shape_supports_control_points = 0
        self._path = None
        self._fat_path = None
        self._visible = None
        self.selectable = True
        self.draggable = False
        self.clickable = True
        self._hovering = False
        self.touch_areas = {}
        self.setZValue(10)
        self.status_tip = ""
        if start and end:
            self.connect_end_points(start, end)

        # self.setAcceptedMouseButtons(QtCore.Qt.NoButton)
        # self.setFlag(QtGui.QGraphicsItem.ItemIsMovable)
        # self.setFlag(QtGui.QGraphicsItem.ItemIsSelectable)
        self.setAcceptHoverEvents(True)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.effect = utils.create_shadow_effect(ctrl.cm.selection())
        self.setGraphicsEffect(self.effect)

        if not ctrl.loading:
            forest.store(self)

    def receive_signal(self, signal, *args):
        """

        :param signal:
        :param args:
        """
        if signal is g.EDGE_SHAPES_CHANGED:
            if (args and args[0] == self.edge_type) or not args:
                self.update_shape()

    def get_touch_area(self, place):
        """

        :param place:
        :return:
        """
        return self.touch_areas.get(place, None)

    def is_visible(self):
        # assert (self._visible == self.isVisible())
        # print 'edge is_visible asked, ', self._visible
        """


        :return:
        """
        return self._visible

    def add_touch_area(self, touch_area):
        """

        :param touch_area:
        :return: :raise:
        """
        if touch_area.type in self.touch_areas:
            print('Touch area already exists. Someone is confused.')
            raise Exception("Touch area exists already")
        self.touch_areas[touch_area.type] = touch_area
        return touch_area

    def remove_touch_area(self, touch_area):
        """
        Forget about given TouchArea. Does not do anything about its scene presence, only cuts the association between
        edge and TouchArea.
        :param touch_area: TouchArea
        """
        del self.touch_areas[touch_area.type]

    # ### Color ############################################################

    def color(self, value=None):
        """
        get color of the edge, or set it.
        :param value: QColor
        :return: QColor
        """
        if value is None:
            if self._color is None:
                c = self.forest.settings.edge_settings(self.edge_type, 'color')
                return ctrl.cm.get(c)
            else:
                return ctrl.cm.get(self._color)
        else:
            self._color = value

    def contextual_color(self):
        """ Drawing color that is sensitive to node's state
        :return: QColor
        """
        if ctrl.pressed == self:
            return ctrl.cm.active(ctrl.cm.selection())
        elif self._hovering:
            return ctrl.cm.hovering(ctrl.cm.selection())
        elif ctrl.is_selected(self):
            return ctrl.cm.selection()
            #return ctrl.cm.selected(self.color())
        else:
            return self.color()

    # ### Pen & Brush ###############################################################


    def pen(self):
        """


        :return:
        """
        return QtGui.QPen()

    def pen_width(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._pen_width is None:
                return self.forest.settings.edge_settings(self.edge_type, 'pen_width')
            else:
                return self._pen_width
        else:
            self._pen_width = value

    # ### Shape / pull / visibility ###############################################################

    def shape_name(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._shape_name is None:
                return self.forest.settings.edge_settings(self.edge_type, 'shape_name')
            else:
                return self._shape_name
        else:
            self._shape_name = value
            self._shape_method = SHAPE_PRESETS[value]['method']

    def shape_method(self):
        """


        :return:
        """
        return SHAPE_PRESETS[self.shape_name()]['method']

    def shape_control_point_support(self):
        """


        :return:
        """
        return SHAPE_PRESETS[self.shape_name()]['control_points']

    def pull(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._pull is None:
                return self.forest.settings.edge_settings(self.edge_type, 'pull')
            else:
                return self._pull
        else:
            self._pull = value

    def shape_visibility(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._shape_visible is None:
                return self.forest.settings.edge_settings(self.edge_type, 'visible')
            else:
                return self._shape_visible
        else:
            self._shape_visible = value

    # ### Derivative features ############################################

    def make_path(self):
        """


        """
        if not self._shape_method:
            self.update_shape()
        self._path = self._shape_method(self)
        if not self.is_filled:  # expensive with filled shapes
            self._fat_path = outline_stroker.createStroke(self._path).united(self._path)

    def shape(self):
        """


        :return:
        """
        if not self.is_filled:
            if not self._fat_path:
                self.make_path()
            return self._fat_path
        else:
            if not self._path:
                self.make_path()
            return self._path

    def update_shape(self):
        """


        """
        d = SHAPE_PRESETS[self.shape_name()]

        self._shape_method = d['method']
        self.make_path()
        while len(self.adjust) < len(self.control_points):
            self.adjust.append((0, 0, 0))
        ctrl.ui.reset_control_points(self)
        self.update()


    def is_structural(self):
        """


        :return:
        """
        return self.edge_type == self.start.default_edge_type

    def adjust_control_point(self, index, points):
        """ Called from UI, when dragging
        :param index:
        :param points:
        """
        x, y = points
        z = self.adjust[index][2]
        self.adjust[index] = (x, y, z)
        self.make_path()
        self.update()

    def update_end_points(self):
        """


        """
        if self.align == LEFT:
            self.start_point = self.start.left_magnet()
        elif self.align == RIGHT:
            self.start_point = self.start.right_magnet()
        else:
            self.start_point = self.start.bottom_magnet()
        self.end_point = self.end.top_magnet()
        # sx, sy, sz = self.start_point
        # ex, ey, ez = self.end_point
        # self.center_point = sx + ((ex - sx) / 2), sy + ((ey - sy) / 2)

    def connect_end_points(self, start, end):
        """

        :param start:
        :param end:
        """
        self.start_point = start.get_current_position()
        self.end_point = end.get_current_position()
        self.start = start
        self.end = end
        # sx, sy, sz = self.start_point
        # ex, ey, ez = self.end_point
        # self.center_point = sx + ((ex - sx) / 2), sy + ((ey - sy) / 2)
        self.update_status_tip()

    def update_status_tip(self):
        if self.edge_type == g.CONSTITUENT_EDGE:
            self.status_tip = 'Constituent relation: %s is part of %s' % (self.end, self.start)        

    def __repr__(self):
        if self.start and self.end:
            return '<%s %s-%s %s>' % (self.edge_type, self.start, self.end, self.align)
        else:
            return '<%s stub from %s to %s>' % (self.edge_type, self.start, self.end)

    def drop_to(self, x, y):
        """

        :param x:
        :param y:
        """
        pass

    def set_visible(self, visible):
        """ Hide or show, and also manage related UI objects. Note that the shape itself may be visible or not independent of this. It has to be visible in this level so that UI elements can be used.
        :param visible:
        """
        v = self.isVisible()
        # print 'set visible called with vis %s when isVisible is %s' % (visible, v)
        if v and not visible:
            self._visible = False
            self.hide()
            ctrl.main.ui_manager.remove_control_points(self)
            for touch_area in self.touch_areas.values():
                touch_area.hide()
        elif (not v) and visible:
            self._visible = True
            self.show()
            if ctrl.is_selected(self):
                ctrl.main.ui_manager.add_control_points(self)
            for touch_area in self.touch_areas.values():
                touch_area.show()
        else:
            self._visible = visible

    def refresh_selection_status(self, selected):
        """

        :param selected:
        """
        ui = ctrl.main.ui_manager  # @UndefinedVariable
        if selected:
            ui.add_control_points(self)
        else:
            ui.remove_control_points(self)
        self.update()

    def boundingRect(self):
        """


        :return:
        """
        if self._shape_name == 'linear':
            return QtCore.QRectF(to_Pf(self.start_point), to_Pf(self.end_point))
        else:  # include curve adjustments
            if not self._path:
                self.update_end_points()
                self.make_path()
            return self._path.controlPointRect()

    # ### Mouse - Qt events ##################################################

    def set_hovering(self, value):
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
            self.setZValue(self.__class__.z_value)
            self.update()
            ctrl.remove_status(self.status_tip)

    def hoverEnterEvent(self, event):
        """
        Overrides (and calls) QtWidgets.QGraphicsItem.hoverEnterEvent
        Toggles hovering state and necessary graphical effects.
        :param event:
        """
        self.set_hovering(True)
        QtWidgets.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """

        :param event:
        """
        self.set_hovering(False)
        QtWidgets.QGraphicsItem.hoverLeaveEvent(self, event)

    # ## Scene-managed call

    def click(self, event=None):
        """ Scene has decided that this node has been clicked
        :param event:
        """
        self.set_hovering(False)
        if event and event.modifiers() == Qt.ShiftModifier:  # multiple selection
            if ctrl.is_selected(self):
                ctrl.remove_from_selection(self)
            else:
                ctrl.add_to_selection(self)
            return
        if ctrl.is_selected(self):
            pass
            # ctrl.deselect_objects()
        else:
            ctrl.select(self)

    # ## Qt paint method override

    def paint(self, painter, option, widget=None):
        """

        :param painter:
        :param option:
        :param widget:
        :return:
        """
        if not self.start or not self.end:
            return
        c = self.contextual_color()
        if self.has_outline:
            p = self.pen()
            p.setColor(c)
            p.setWidth(self.pen_width())
            painter.setPen(p)
            painter.drawPath(self._path)
        if self.is_filled:
            painter.fillPath(self._path, c)

    def adjusted_control_point_list(self):
        """ List where control points and their adjustments are added up, and (x,y) tuples
        are break down into one big list x1, y1, x2, y2,... to be used in path construction
        :return: list
        """
        l = []
        la = len(self.adjust)
        for i, cp in enumerate(self.control_points):
            if la <= i:
                l.append(cp[0])
                l.append(cp[1])
            else:
                l.append(cp[0] + self.adjust[i][0])
                l.append(cp[1] + self.adjust[i][1])
        return l

    def get_path(self)-> QtGui.QPainterPath:
        """ Get drawing path of this edge
        :return: QPath
        """
        return self._path

    def get_point_at(self, d: int)-> Pf:
        """ Get coordinates at the percentage of the length of the path.
        :param d: int
        :return: QPoint
        """
        if self.is_filled:
            d /= 2.0
        if not self._path:
            self.update_end_points()
            self.make_path()
        return self._path.pointAtPercent(d)

    def get_angle_at(self, d) -> float:
        """ Get angle at the percentage of the length of the path.
        :param d: int
        :return: float
        """
        if self.is_filled:
            d /= 2.0
            # slopeAtPercent
        if not self._path:
            self.update_end_points()
            self.make_path()
        return self._path.angleAtPercent(d)

    # ### Event filter - be sensitive to changes in settings  ########################################################

    # def sceneEvent(self, event):
    # print 'Edge event received: ', event.type()
    # return QtWidgets.QGraphicsItem.sceneEvent(self, event)

    # ### Restoring after load / undo #########################################

    def after_restore(self, changes):
        """ Fix derived attributes
        :param changes:
        """
        self.update_end_points()
        self.set_visible(self._visible)
