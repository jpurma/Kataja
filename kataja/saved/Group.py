# coding=utf-8
import math

from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.SavedObject import SavedObject
from kataja.SavedField import SavedField
from kataja.singletons import ctrl, qt_prefs
from kataja.saved.movables.Node import Node
from kataja.GroupLabel import GroupLabel
from kataja.uniqueness_generator import next_available_type_id, next_available_ui_key

points = 36


class Group(SavedObject, QtWidgets.QGraphicsObject):
    __qt_type_id__ = next_available_type_id()
    permanent_ui = False
    unique = False
    can_fade = False
    scene_item = True
    is_widget = False

    def __init__(self, selection=None, persistent=True, color_key='accent1'):
        SavedObject.__init__(self)
        QtWidgets.QGraphicsObject.__init__(self)
        # -- Fake as UIItem to make selection groups part of UI:
        self.ui_key = next_available_ui_key()
        self.ui_type = self.__class__.__name__
        self.ui_manager = ctrl.ui
        self.role = None
        self.host = None
        self.is_fading_in = False
        self.is_fading_out = False
        # -- end faking as UIItem
        self.selection = []
        self.selection_with_children = []
        self.persistent = persistent
        self._skip_this = not persistent
        self._selected = False
        self.points = []
        self.center_point = None
        self.outline = False
        self.fill = True
        self.color_key = color_key
        self.color = None
        self.color_tr_tr = None
        self.purpose = None
        self.path = None
        self.label_item = None
        self.label_data = {}
        self.buttons = []
        self._br = None
        # self.setFlag(QtWidgets.QGraphicsObject.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsObject.ItemIsSelectable)
        if selection:
            self.update_selection(selection)
        self.update_shape()
        self.update_colors()

    def __contains__(self, item):
        return item in self.selection_with_children

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

    def after_init(self):
        self.update_selection(self.selection)
        self.update_shape()
        self.update_colors()

    def after_model_update(self, updated_fields, transition_type):
        """ Compute derived effects of updated values in sensible order.
        :param updated_fields: field keys of updates
        :param transition_type: 0:edit, 1:CREATED, -1:DELETED
        :return: None
        """
        if transition_type == g.CREATED:
            ctrl.forest.store(self)
            ctrl.forest.add_to_scene(self)
        elif transition_type == g.DELETED:
            ctrl.forest.remove_from_scene(self, fade_out=False)
            return
        if updated_fields:
            self.update_selection(self.selection)
            self.update_shape()
            self.update_colors()

    def copy_from(self, source):
        """ Helper method to easily make a similar selection with different identity
        :param source:
        :return:
        """
        self.selection = source.selection
        self.selection_with_children = source.selection_with_children
        self.points = list(source.points)
        self.center_point = source.center_point
        self.outline = source.outline
        self.fill = source.fill
        self.color_key = source.color_key
        self.color = source.color
        self.color_tr_tr = source.color_tr_tr
        self.path = source.path
        text = source.get_label_text()
        if text:
            self.set_label_text(text)

    def get_label_text(self):
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
            self.label_item = GroupLabel(value, parent=self)
            self.poke('label_data')
            self.label_data['text'] = value
        if self.label_item.automatic_position:
            self.label_item.position_at_bottom()
        else:
            self.label_item.update_position()

    def remove_node(self, node, delete_if_empty=True):
        """ Manual removal of single node, should be called e.g. when node is deleted.
        :param node:
        :return:
        """
        if node in self.selection:
            self.poke('selection')
            self.selection.remove(node)
        if node in self.selection_with_children:
            self.selection_with_children.remove(node)

        if self.selection:
            self.update_shape()
        else:
            if self.persistent and delete_if_empty:
                ctrl.free_drawing.remove_group(self)
            else:
                ctrl.ui.remove_ui_for(self)

    def remove_nodes(self, nodes):
        """ Remove multiple nodes, just to avoid repeated calls to expensive updates
        :param nodes:
        :return:
        """
        self.poke('selection')
        for node in nodes:
            if node in self.selection:
                self.selection.remove(node)
            if node in self.selection_with_children:
                self.selection_with_children.remove(node)
        if self.selection:
            self.update_shape()
        else:
            if self.persistent:
                ctrl.free_drawing.remove_group(self)
            else:
                ctrl.ui.remove_ui_for(self)

    def clear(self, remove=True):
        self.selection = set()
        self.selection_with_children = set()
        self.update_shape()
        if remove:
            if self.persistent:
                ctrl.free_drawing.remove_group(self)
            else:
                ctrl.ui.remove_ui_for(self)

    def add_node(self, node):
        """ Manual addition of single node
        :param node:
        :return:
        """
        if node not in self.selection:
            self.poke('selection')
            self.selection.append(node)
            self.update_selection(self.selection)
            self.update_shape()

    def update_selection(self, selection):
        if selection:
            self.selection = [item for item in selection if
                              isinstance(item, Node) and item.can_be_in_groups]
            self.selection_with_children = self.selection
        else:
            self.selection = []
            self.selection_with_children = []

    def update_shape(self):

        def embellished_corners(item):
            x1, y1, x2, y2 = item.sceneBoundingRect().getCoords()
            corners = [(x1 - 5, y1 - 5), (x2 + 5, y1 - 5), (x2 + 5, y2 + 5), (x1 - 5, y2 + 5)]

            return x1, y1, x2, y2, corners

        self.prepareGeometryChange()
        sel = [x for x in self.selection_with_children if x.isVisible()]

        if len(sel) == 0:
            self._br = QtCore.QRectF()
            self.path = QtGui.QPainterPath()
            self.center_point = 0, 0
            return
        elif len(sel) == 1:
            x1, y1, x2, y2, route = embellished_corners(sel[0])
            self.path = QtGui.QPainterPath(QtCore.QPointF(route[0][0], route[0][1]))
            for x, y in route[1:]:
                self.path.lineTo(x, y)
            self.path.closeSubpath()
        else:
            corners = []
            c = 0
            min_x = 50000
            max_x = -50000
            min_y = 50000
            max_y = -50000
            for item in sel:
                c += 2
                x1, y1, x2, y2, icorners = embellished_corners(item)
                if x1 < min_x:
                    min_x = x1
                if x2 > max_x:
                    max_x = x2
                if y1 < min_y:
                    min_y = y1
                if y2 > max_y:
                    max_y = y2
                corners += icorners
            self.prepareGeometryChange()
            cx = (min_x + max_x) / 2
            cy = (min_y + max_y) / 2
            r = max(max_x - min_x, max_y - min_y) * 1.1
            dots = 32
            step = 2 * math.pi / dots
            deg = 0
            route = []
            for n in range(0, dots):
                cpx = math.cos(deg) * r + cx
                cpy = math.sin(deg) * r + cy
                deg += step
                closest = None
                closest_d = 2000000
                for px, py in corners:
                    d = (px - cpx) ** 2 + (py - cpy) ** 2
                    if d < closest_d:
                        closest = px, py
                        closest_d = d
                if closest:
                    if route:
                        last = route[-1]
                        if last == closest:
                            continue
                    route.append(closest)

        if self.label_item:
            if self.label_item.automatic_position:
                self.label_item.position_at_bottom()
            else:
                self.label_item.update_position()

        curved_path = Group.interpolate_point_with_bezier_curves(route)
        sx, sy = route[0]
        self.path = QtGui.QPainterPath(QtCore.QPointF(sx, sy))
        xs = []
        ys = []
        for fx, fy, sx, sy, ex, ey in curved_path:
            xs += [fx, sx, ex]
            ys += [fy, sy, ey]
            self.path.cubicTo(fx, fy, sx, sy, ex, ey)
        min_x = min(xs)
        min_y = min(ys)
        self._br = QtCore.QRectF(min_x, min_y, max(xs) - min_x, max(ys) - min_y)
        center = self._br.center()
        self.center_point = center.x(), center.y()

        # This is costly
        if True:
            for item in self.collidingItems():
                if (isinstance(item, Node) and item.node_type == g.CONSTITUENT_NODE and item not
                in self.selection_with_children):
                    x, y = item.current_scene_position
                    subshape = item.shape().translated(x, y)
                    subshape_points = []
                    for i in range(0, subshape.elementCount()):
                        element = subshape.elementAt(i)
                        subshape_points.append((element.x, element.y))
                    curved_path = Group.interpolate_point_with_bezier_curves(subshape_points)
                    sx, sy = subshape_points[0]
                    subshape = QtGui.QPainterPath(QtCore.QPointF(sx, sy))
                    for fx, fy, sx, sy, ex, ey in curved_path:
                        subshape.cubicTo(fx, fy, sx, sy, ex, ey)

                    self.path = self.path.subtracted(subshape)

    def shape(self):
        if self.path is not None:
            return self.path
        else:
            return QtGui.QPainterPath()

    def update_position(self):
        self.update_shape()

    def boundingRect(self):
        if self._br is None:
            self.update_shape()
        return self._br

    def get_color_key(self):
        return self.color_key

    def set_color_key(self, color_key):
        self.color_key = color_key or "accent1"
        self.update_colors()

    def update_colors(self):
        self.color_key = self.color_key or "accent1"
        self.color = ctrl.cm.get(self.color_key)
        self.color_tr_tr = QtGui.QColor(self.color)
        self.color_tr_tr.setAlphaF(0.2)
        if self.label_item:
            self.label_item.update_color()

    def mousePressEvent(self, event):
        ctrl.press(self)
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if ctrl.pressed is self:
            ctrl.release(self)
            if ctrl.dragged_set:
                ctrl.graph_scene.kill_dragging()
                ctrl.ui.update_selections()  # drag operation may have changed visible affordances
            else:  # This is regular click on 'pressed' object
                self.select(event)
                self.update()
            return None  # this mouseRelease is now consumed
        super().mouseReleaseEvent(event)

    def select(self, adding=False, select_area=False):
        """ Scene has decided that this node has been clicked
        :param adding: bool, we are adding to selection instead of starting a new selection
        :param select_area: bool, we are dragging a selection box, method only informs that this
        node can be included
        :returns: int or str, uid of node if node is selectable
        """
        self.hovering = False
        # if we are selecting an area, select actions are not called here, but once for all
        # objects. In this case return only uid of this object.
        if select_area:
            return self.uid
        #items = [x.uid for x in self.selection]
        #items.append(self.uid)
        if adding:
            if ctrl.is_selected(self):
                print('selected group (adding=True), calling remove_from_selection for it')
                ctrl.ui.get_action('remove_from_selection').run_command([self.uid], has_params=True)
            else:
                print('selected group (adding=True), calling add_to_selection for it')
                ctrl.ui.get_action('add_to_selection').run_command([self.uid], has_params=True)
        else:
            print('selected group, calling select for it')
            ctrl.ui.get_action('select').run_command([self.uid], has_params=True)
        return self.uid

    def update_selection_status(self, value):
        """

        :param value:
        :return:
        """
        self._selected = value

    def paint(self, painter, style, QWidget_widget=None):
        if self.selection and self.path:
            if self.fill:
                painter.fillPath(self.path, self.color_tr_tr)
            if self._selected:
                painter.setPen(ctrl.cm.selection())
                painter.drawPath(self.path)
            elif self.outline:
                painter.setPen(self.color)
                painter.drawPath(self.path)

    def position_for_buttons(self):
        scb = self.sceneBoundingRect()
        return QtCore.QPointF(scb.center().x(), scb.top() - 8)

    def add_button(self, button):
        if button not in self.buttons:
            self.buttons.append(button)

    def index_for_button(self, button):
        return self.buttons.index(button), len(self.buttons)

    @staticmethod
    def interpolate_point_with_bezier_curves(points):
        """ Curved path algorithm based on example by Raul Otaño Hurtado, from
        http://www.codeproject.com/Articles/769055/Interpolate-D-points-usign-Bezier-curves-in-WPF
        :param points:
        :return:
        """
        if len(points) < 3:
            return None
        res = []

        # if is close curve then add the first point at the end
        if points[-1] != points[0]:
            points.append(points[0])

        for i, (x1, y1) in enumerate(points[:-1]):
            if i == 0:
                x0, y0 = points[-2]
            else:
                x0, y0 = points[i - 1]
            x2, y2 = points[i + 1]
            if i == len(points) - 2:
                x3, y3 = points[1]
            else:
                x3, y3 = points[i + 2]

            xc1 = (x0 + x1) / 2.0
            yc1 = (y0 + y1) / 2.0
            xc2 = (x1 + x2) / 2.0
            yc2 = (y1 + y2) / 2.0
            xc3 = (x2 + x3) / 2.0
            yc3 = (y2 + y3) / 2.0
            len1 = math.hypot(x1 - x0, y1 - y0)
            len2 = math.hypot(x2 - x1, y2 - y1)
            len3 = math.hypot(x3 - x2, y3 - y2)

            k1 = len1 / (len1 + len2)
            k2 = len2 / (len2 + len3)

            xm1 = xc1 + (xc2 - xc1) * k1
            ym1 = yc1 + (yc2 - yc1) * k1

            xm2 = xc2 + (xc3 - xc2) * k2
            ym2 = yc2 + (yc3 - yc2) * k2

            smooth = 0.8
            ctrl1_x = xm1 + (xc2 - xm1) * smooth + x1 - xm1
            ctrl1_y = ym1 + (yc2 - ym1) * smooth + y1 - ym1
            ctrl2_x = xm2 + (xc2 - xm2) * smooth + x2 - xm2
            ctrl2_y = ym2 + (yc2 - ym2) * smooth + y2 - ym2
            res.append((ctrl1_x, ctrl1_y, ctrl2_x, ctrl2_y, x2, y2))
        return res

    selection = SavedField("selection")
    color_key = SavedField("color_key")
    label_data = SavedField("label_data")
    purpose = SavedField("purpose")
    fill = SavedField("fill")
    outline = SavedField("outline")
    persistent = SavedField("persistent")
    forest = SavedField("forest")
