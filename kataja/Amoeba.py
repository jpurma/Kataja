# coding=utf-8
import math
from PyQt5 import QtWidgets, QtCore, QtGui

from kataja.BaseModel import BaseModel, Saved
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.nodes.Node import Node
import kataja.globals as g

points = 36

class Amoeba(BaseModel, QtWidgets.QGraphicsObject):

    def __init__(self, selection, persistent=False):
        BaseModel.__init__(self)
        QtWidgets.QGraphicsObject.__init__(self)
        self.ui_key = self.save_key + '_ui'
        self.host = None # not used, it is here because it is expected for UI elements
        self.selection = []
        self.selection_with_children = []
        self.persistent = persistent
        self._skip_this = not persistent
        self.points = []
        self.outline = False
        self.fill = True
        self.color_key = ''
        self.color = None
        self.color_tr = None
        self.color_tr_tr = None
        self.path = None
        self.label_text = ''
        self.label_item = None
        self.include_children = False
        self.allow_overlap = True
        self._br = None
        self.update_selection(selection)
        self.update_shape()
        self.update_colors()

    def copy_from(self, source):
        """ Helper method to easily make a similar selection with different identity
        :param source:
        :return:
        """
        self.selection = source.selection
        self.selection_with_children = source.selection_with_children
        self.points = source.points
        self.outline = source.outline
        self.fill = source.fill
        self.color_key = source.color_key
        self.color = source.color
        self.color_tr = source.color_tr
        self.color_tr_tr = source.color_tr_tr
        self.path = source.path
        self.set_label_text(source.label_text)
        self.include_children = source.include_children
        self.allow_overlap = source.allow_overlap

    def set_label_text(self, text):
        self.label_text = text
        if text:
            if not self.label_item:
                self.label_item = QtWidgets.QGraphicsSimpleTextItem(text, self)
                self.label_item.setFont(qt_prefs.font(g.SMALL_CAPS))
                self.label_item.setPen(qt_prefs.no_pen)
                self.label_item.setBrush(self.color)
            else:
                self.label_item.setText(text)
        else:
            if self.label_item:
                self.label_item.scene().removeItem(self.label_item)
                self.label_item = None


    def update_selection(self, selection):
        swc = []
        other_selections = set()
        if not self.allow_overlap:
            for amoeba in ctrl.forest.groups.values():
                other_selections = other_selections | set(amoeba.selection_with_children)

        def recursive_add_children(i):
            if isinstance(i, Node) and i not in swc and \
                    (i in selection or i not in other_selections):
                swc.append(i)
                for child in i.get_all_children():
                    recursive_add_children(child)

        if selection:
            self.selection = list(selection)
            if self.include_children:
                for item in self.selection:
                    recursive_add_children(item)
                self.selection_with_children = swc
            else:
                self.selection_with_children = self.selection
        else:
            self.selection = []
            self.selection_with_children = []

    def update_shape(self):

        def embellished_corners(item):
            x1, y1, x2, y2 = item.sceneBoundingRect().getCoords()
            # /----\
            # |    |
            # \----/
            corners = ((x1 - 5, y1),
                       (x1, y1 - 5),
                       (x2, y1 - 5),
                       (x2 + 5, y1),
                       (x2 + 5, y2),
                       (x2, y2 + 5),
                       (x1, y2 + 5),
                       (x1 - 5, y2))
            return x1, y1, x2, y2, corners
        sel = self.selection_with_children

        if len(sel) == 0:
            self._br = None
            self.path = None
            return
        elif len(sel) == 1:
            x1, y1, x2, y2, route = embellished_corners(sel[0])
            self._br = QtCore.QRectF(x1 - 5, y1 - 5, x2 - x1 + 10, y2 - y1 + 10)
            self.path = QtGui.QPainterPath(QtCore.QPointF(route[0][0], route[0][1]))
            for x, y in route[1:]:
                self.path.lineTo(x, y)
            self.path.closeSubpath()
            center = self._br.center()
            cx, cy = center.x(), center.y()

        else:
            corners = []
            c = 0
            x_sum = 0
            y_sum = 0
            min_x = 50000
            max_x = -50000
            min_y = 50000
            max_y = -50000
            for item in sel:
                c += 2
                x1, y1, x2, y2, icorners = embellished_corners(item)
                x_sum += x1
                x_sum += x2
                y_sum += y1
                y_sum += y2
                if x1 < min_x:
                    min_x = x1
                if x2 > max_x:
                    max_x = x2
                if y1 < min_y:
                    min_y = y1
                if y2 > max_y:
                    max_y = y2
                corners += icorners
            self._br = QtCore.QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
            cx = (min_x + max_x) / 2
            cy = (min_y + max_y) / 2
            r = max(max_x - min_x, max_y - min_y) * 1.1
            dots = 32
            step = 2 * math.pi / dots
            deg = 0
            route = []
            for n in range(0, dots):
                cpx = math.cos(deg)*r + cx
                cpy = math.sin(deg)*r + cy
                deg += step
                closest = None
                closest_d = 200000
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
            self.path = QtGui.QPainterPath(QtCore.QPointF(route[0][0], route[0][1]))
            for x, y in route[1:]:
                self.path.lineTo(x, y)
            self.path.closeSubpath()

        if self.label_item:
            label_width = self.label_item.boundingRect().width()
            label_height = self.label_item.boundingRect().height()
            label_center_x, label_center_y = label_width / 2, label_height / 2

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
                    items = ctrl.graph_scene.items(QtCore.QPointF(mx + label_center_x,
                                                   my + label_center_y))
                    collision = False
                    for item in items:
                        if isinstance(item, (Node, Amoeba)):
                            collision = True
                    if not collision:
                        min_dist = d
                        best_x, best_y = mx, my
                prev_x, prev_y = x, y
            self.label_item.setPos(best_x, best_y)

    def update_position(self):
        self.update_shape()

    def paint(self, painter, style, QWidget_widget=None):
        if self.selection and self.path:
            if self.fill:
                painter.fillPath(self.path, self.color_tr_tr)
            if self.outline:
                painter.setPen(self.color)
                painter.drawPath(self.path)

    def top_right_point(self):
        max_x = -30000
        min_y = 30000
        for i in range(0, self.path.elementCount()):
            element = self.path.elementAt(i)
            if element.y <= min_y and element.x > max_x:
                min_y = element.y
                max_x = element.x
        return QtCore.QPointF(max_x, min_y)

    def boundingRect(self):
        if not self._br:
            self.update_shape()
        return self._br

    def get_color_id(self):
        return self.color_key

    def update_colors(self, color_key=''):
        if not self.color_key:
            self.color_key = color_key or "accent1"
        elif color_key:
            self.color_key = color_key
        self.color = ctrl.cm.get(self.color_key)
        self.color_tr = ctrl.cm.get(self.color_key + 'tr')
        self.color_tr_tr = QtGui.QColor(self.color)
        self.color_tr_tr.setAlphaF(0.2)
        if self.label_item:
            self.label_item.setBrush(self.color)

    color_key = Saved("color_key")
    label_text = Saved("label_text")
    include_children = Saved("include_children")
    allow_overlap = Saved("allow_overlap")
    fill = Saved("fill")
    outline = Saved("outline")
    persistent = Saved("persistent")
