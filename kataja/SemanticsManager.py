
from PyQt5 import QtCore, QtWidgets, QtGui

import itertools

from collections import defaultdict
from singletons import classes

from kataja.Projection import Projection
from kataja.singletons import ctrl, classes, qt_prefs
from kataja.globals import CONSTITUENT_NODE, FEATURE_NODE, SMALL_FEATURE
from kataja.utils import time_me


class SemanticsItem(QtWidgets.QGraphicsSimpleTextItem):

    def __init__(self, label, array_id, color_id, x=0, y=0):
        QtWidgets.QGraphicsSimpleTextItem.__init__(self, label)
        self.label = label
        self.setFont(qt_prefs.get_font(SMALL_FEATURE))
        self.array_id = array_id
        self.color_id = color_id
        self.color_id_tr = color_id if color_id.endswith('tr') else color_id + 'tr'
        self.members = []
        self.setZValue(2)
        self.setPos(x, y)

    def add_member(self, node):
        if node not in self.members:
            self.members.append(node)

    def boundingRect(self):
        base = self.label_rect()
        if not self.members:
            return base.adjusted(-2, -2, 2, 2)
        scene_pos = self.pos()
        x = scene_pos.x()
        y = scene_pos.y()
        left = x + base.left()
        up = y + base.top()
        right = x + base.right()
        down = y + base.bottom()
        for member in self.members:
            p = member.scenePos()
            px = p.x()
            py = p.y()
            if px < left:
                left = px
            elif px > right:
                right = px
            if py < up:
                up = py
            elif py > down:
                down = py
        return QtCore.QRectF(left - x, up - y, right - left + 2, down - up + 2)

    def label_rect(self):
        min_w = 40
        if not self.members:
            return QtCore.QRectF(-2, -1, min_w, 4)
        r = QtWidgets.QGraphicsSimpleTextItem.boundingRect(self).adjusted(-2, -1, 2, 1)
        if r.width() < min_w:
            r.setWidth(min_w)
        return r

    def paint(self, painter, *args, **kwargs):
        painter.setPen(QtCore.Qt.NoPen)
        label_rect = self.label_rect()
        if self.members:
            painter.setBrush(ctrl.cm.get(self.color_id))
            painter.drawRoundedRect(label_rect, 4, 4)
            p = QtGui.QPen(ctrl.cm.get(self.color_id_tr), 3)
            painter.setPen(p)
            scene_pos = self.pos()
            x = scene_pos.x()
            y = scene_pos.y()
            mid_height = label_rect.height() / 2
            painter.setBrush(QtCore.Qt.NoBrush)
            for member in self.members:
                pos = member.scenePos()
                px = pos.x()
                py = pos.y()
                if True:
                    painter.setPen(QtCore.Qt.NoPen)
                    painter.setBrush(ctrl.cm.get(self.color_id_tr))
                    # p.lineTo(px - x, py - y)
                    if py < y:
                        p = QtGui.QPainterPath(QtCore.QPointF(0, mid_height + 2))
                        p.lineTo((px - x) / 2, mid_height + 2)
                        p.quadTo(((px - x) / 4) * 3, mid_height + 2, px - x - 1, py - y + 1)
                        p.lineTo(px - x + 1, py - y - 1)
                        p.quadTo(((px - x) / 4) * 3, mid_height - 2, (px - x) / 2, mid_height - 2)
                        p.lineTo(0, mid_height - 2)
                    else:
                        p = QtGui.QPainterPath(QtCore.QPointF(0, mid_height - 2))
                        p.lineTo((px - x) / 2, mid_height - 2)
                        p.quadTo(((px - x) / 4) * 3, mid_height - 2, px - x - 1, py - y - 1)
                        p.lineTo(px - x + 1, py - y + 1)
                        p.quadTo(((px - x) / 4) * 3, mid_height + 2, (px - x) / 2, mid_height + 2)
                        p.lineTo(0, mid_height + 2)
                    painter.drawPath(p)
                else:
                    p = QtGui.QPainterPath(QtCore.QPointF(0, mid_height))
                    p.lineTo((px - x) / 2, mid_height)
                    #p.lineTo(px - x, py - y)
                    p.quadTo(((px - x) / 4) * 3, mid_height, px - x, py - y)
                    painter.drawPath(p)
            self.setBrush(ctrl.cm.paper())
            QtWidgets.QGraphicsSimpleTextItem.paint(self, painter, *args, **kwargs)
        else:
            painter.setBrush(ctrl.cm.get(self.color_id_tr))
            painter.drawRoundedRect(label_rect, 4, 4)
        #painter.setPen(ctrl.cm.get(self.color_id))
        #painter.drawRect(self.boundingRect())

class SemanticsArray:

    def __init__(self, array_id, model, x=0, y=0):
        self.array_id = array_id
        self.array = []
        self.x = x
        self.y = y
        get_color_for = classes.get('FeatureNode').get_color_for
        for label in model:
            item = SemanticsItem(label, array_id, get_color_for(label), x, y)
            self.array.append(item)
            y += item.label_rect().height()

    def total_size(self):
        h = 0
        w = 0
        for item in self.array:
            r = item.label_rect()
            if r.width() > w:
                w = r.width()
            h += r.height()
        return w, h

    def move_to(self, x, y):
        for item in self.array:
            item.prepareGeometryChange()
            item.setPos(x, y)
            y += item.label_rect().height()
            item.update()


class SemanticsManager:

    def __init__(self, forest):
        self.forest = forest
        self.clause_model = list(reversed(self.forest.syntax.clause_hierarchy))
        self.dp_model = list(reversed(self.forest.syntax.dp_hierarchy))
        self.all_items = []
        self.arrays = {}
        self.arrays_list = []

    def add_to_array(self, node, label, array_id):
        """ Create new arrays when necessary
        :param node:
        :param label:
        :param array_id:
        :return:
        """
        if array_id not in self.arrays:
            if label in self.clause_model:
                model = self.clause_model
            elif label in self.dp_model:
                model = self.dp_model
            else:
                print('no suitable semantic array for ', label, array_id)
                return
            if self.arrays_list:
                last = self.arrays_list[-1]
                x = last.x
                y = last.y + last.total_size()[1] + 8
            else:
                x, y = self.find_good_position()
            array = SemanticsArray(array_id, model, x, y)
            self.arrays[array_id] = array
            self.all_items += array.array
            self.arrays_list.append(array)
            for item in array.array:
                self.forest.add_to_scene(item)
        else:
            array = self.arrays[array_id]
        for item in array.array:
            if label == item.label:
                item.add_member(node)
        self.update_position()

    def update_position(self):
        x, y = self.find_good_position()
        for array in self.arrays_list:
            array.move_to(x, y)
            y += array.total_size()[1] + 8

    def find_good_position(self):
        x = 0
        y = 0
        for node in self.forest.nodes.values():
            nx, ny = node.current_position
            if nx > x:
                x = nx
            if ny < y:
                y = ny
        return x + 40, y

    def clear(self):
        for item in self.all_items:
            self.forest.remove_from_scene(item, fade_out=False)
        self.all_items = []
        self.arrays = {}
        self.arrays_list = []


