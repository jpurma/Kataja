import math

from PyQt5 import QtCore, QtWidgets, QtGui

from kataja.globals import SMALL_FEATURE
from kataja.singletons import ctrl, qt_prefs

FREE = 0
SENTENCE = 1
NOUN_PHRASE = 2


class SemanticsItem(QtWidgets.QGraphicsSimpleTextItem):

    def __init__(self, sm, label, array_id, color_key, x=0, y=0):
        QtWidgets.QGraphicsSimpleTextItem.__init__(self, label)
        self.label = label
        self.setFont(qt_prefs.get_font(SMALL_FEATURE))
        self.array_id = array_id
        self.color_key = color_key
        self.color_key_tr = color_key if color_key.endswith('tr') else color_key + 'tr'
        self.members = []
        self.setZValue(2)
        self.setPos(x, y)
        if not sm.visible:
            self.hide()

    def add_member(self, node):
        if node not in self.members:
            self.members.append(node)

    def update_text(self):
        words = [self.label]
        for node in self.members:
            if node.syntactic_object:
                checked_features = getattr(node.syntactic_object, 'checked_features', [])
                if checked_features and isinstance(checked_features, tuple):
                    checked_feat, valuing_feat = checked_features
                    feat_node = ctrl.forest.get_node(checked_feat)
                    parents = feat_node.get_parents()
                    words.append('(' + ' '.join([x.label for x in parents]) + ')')
                    feat_node = ctrl.forest.get_node(valuing_feat)
                    parents = feat_node.get_parents()
                    words.append(' '.join([x.label for x in parents]))

        self.setText(' '.join(words))

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
            painter.setBrush(ctrl.cm.get(self.color_key))
            painter.drawRoundedRect(label_rect, 4, 4)
            p = QtGui.QPen(ctrl.cm.get(self.color_key_tr), 3)
            painter.setPen(p)
            scene_pos = self.pos()
            x = scene_pos.x()
            y = scene_pos.y()
            mid_height = label_rect.height() / 2
            painter.setBrush(QtCore.Qt.NoBrush)

            for member in self.members:
                if member.cached_sorted_feature_edges:
                    max_i = len(member.cached_sorted_feature_edges)
                    i_shift = math.ceil((max_i - 1) / 2) * -3
                else:
                    i_shift = 0
                pos = member.scenePos()
                px = pos.x()
                py = pos.y()
                px += i_shift
                if True:
                    painter.setPen(QtCore.Qt.NoPen)
                    grad = QtGui.QLinearGradient(0, 0, px - x, 0)
                    grad.setColorAt(0, ctrl.cm.get(self.color_key))
                    grad.setColorAt(0.1, ctrl.cm.get(self.color_key_tr))
                    grad.setColorAt(0.6, ctrl.cm.get(self.color_key_tr))
                    grad.setColorAt(1, ctrl.cm.get(self.color_key))
                    painter.setBrush(grad)
                    # painter.setBrush(ctrl.cm.get(self.color_key_tr))
                    # p.lineTo(px - x, py - y)

                    if py < y:
                        p = QtGui.QPainterPath(QtCore.QPointF(0, mid_height + 2))
                        p.lineTo((px - x) / 2, mid_height + 2)
                        p.quadTo(((px - x) / 4) * 3 - 2, mid_height + 2, px - x - 0.5, py - y - 1)
                        p.lineTo(px - x + 3, py - y - 5)
                        p.quadTo(((px - x) / 4) * 3 + 2, mid_height - 2, (px - x) / 2, mid_height
                                 - 2)
                        p.lineTo(0, mid_height - 2)
                    else:
                        p = QtGui.QPainterPath(QtCore.QPointF(0, mid_height - 2))
                        p.lineTo((px - x) / 2, mid_height - 2)
                        p.quadTo(((px - x) / 4) * 3 - 2, mid_height - 2, px - x - 0.5, py - y - 1)
                        p.lineTo(px - x + 3, py - y - 5)
                        p.quadTo(((px - x) / 4) * 3 + 2, mid_height + 2, (px - x) / 2, mid_height
                                 + 2)
                        p.lineTo(0, mid_height + 2)
                    painter.drawPath(p)
                # else:
                #     p = QtGui.QPainterPath(QtCore.QPointF(0, mid_height))
                #     p.lineTo((px - x) / 2, mid_height)
                #     p.quadTo(((px - x) / 4) * 3, mid_height, px - x, py - y)
                #     painter.drawPath(p)
            self.setBrush(ctrl.cm.paper())
            QtWidgets.QGraphicsSimpleTextItem.paint(self, painter, *args, **kwargs)
        else:
            painter.setBrush(ctrl.cm.get(self.color_key_tr))
            painter.drawRoundedRect(label_rect, 4, 4)
