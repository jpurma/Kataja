# coding=utf-8
import math
from PyQt5 import QtWidgets, QtCore, QtGui

from kataja.BaseModel import BaseModel, Saved
from kataja.singletons import ctrl, prefs, qt_prefs

points = 36

class Amoeba(BaseModel, QtWidgets.QGraphicsObject):

    def __init__(self, selection):
        BaseModel.__init__(self)
        QtWidgets.QGraphicsObject.__init__(self)
        self.ui_key = self.save_key + '_ui'
        self.host = None
        if selection:
            self.selection = list(selection)
        else:
            self.selection = []
        self.persistent = False
        self.points = []
        self.color_key = ''
        self.color = None
        self.color_tr = None
        self.color_tr_tr = None
        self.path = None
        self._br = None
        self.update_shape()
        self.update_colors()

    def update_selection(self, selection):
        if selection:
            self.selection = list(selection)
        else:
            self.selection = []

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

        if len(self.selection) == 0:
            self._br = None
            self.path = None
        elif len(self.selection) == 1:
            x1, y1, x2, y2, path_points = embellished_corners(self.selection[0])
            self._br = QtCore.QRectF(x1 - 5, y1 - 5, x2 - x1 + 10, y2 - y1 + 10)
            self.path = QtGui.QPainterPath(QtCore.QPointF(path_points[0][0], path_points[0][1]))
            for x, y in path_points[1:]:
                self.path.lineTo(x, y)
            self.path.closeSubpath()

        else:
            corners = []
            c = 0
            x_sum = 0
            y_sum = 0
            min_x = 50000
            max_x = -50000
            min_y = 50000
            max_y = -50000
            for item in self.selection:
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

    def update_position(self):
        self.update_shape()

    def paint(self, painter, style, QWidget_widget=None):
        if self.selection and self.path:
            painter.setPen(self.color_tr)
            painter.fillPath(self.path, self.color_tr_tr)

    def boundingRect(self):
        if not self._br:
            self.update_shape()
        return self._br

    def update_colors(self):
        self.color_key = 'accent1'
        self.color = ctrl.cm.get(self.color_key)
        self.color_tr = ctrl.cm.get(self.color_key + 'tr')
        self.color_tr_tr = QtGui.QColor(self.color)
        self.color_tr_tr.setAlphaF(0.2)

    color_key = Saved("color_key")
    name = Saved("name")
