__author__ = 'purma'

from PyQt5 import QtGui, QtCore
from kataja.ui.DrawnIconEngine import DrawnIconEngine
from kataja.singletons import ctrl


class ArrowIcon(QtGui.QIcon):
    def __init__(self):
        QtGui.QIcon.__init__(self, DrawnIconEngine(self.paint_method, self))

    @staticmethod
    def paint_method(painter, rect, color=None):
        w = rect.width()
        h = rect.height()
        path = QtGui.QPainterPath(QtCore.QPointF(0, h - 4))
        path.lineTo(w, 4)
        p = painter.pen()
        p.setWidthF(1.5)
        painter.setPen(p)
        painter.drawPath(path)
        d = (h - 8.0) / w
        path = QtGui.QPainterPath(QtCore.QPointF(w, 4))
        path.lineTo(w - 10,  8 + (10 * d))
        path.lineTo(w - 8,  4 + (8 * d))
        path.lineTo(w - 12,  12 * d)
        painter.fillPath(path, color)

    def paint_settings(self):
        return {'color':ctrl.cm.d['accent4']}


class DividerIcon(QtGui.QIcon):
    def __init__(self):
        QtGui.QIcon.__init__(self, DrawnIconEngine(self.paint_method, self))

    @staticmethod
    def paint_method(painter, rect, color=None):
        w = rect.width()
        h = rect.height()
        path = QtGui.QPainterPath(QtCore.QPointF(0, h - 4))
        path.cubicTo(10, h - 10 , w - 10, 10, w, 4)
        p = painter.pen()
        p.setWidthF(2)
        p.setStyle(QtCore.Qt.DashLine)
        painter.setPen(p)
        painter.drawPath(path)

    def paint_settings(self):
        return {'color':ctrl.cm.d['accent5']}


class TriangleIcon(QtGui.QIcon):

    def __init__(self):
        QtGui.QIcon.__init__(self, DrawnIconEngine(self.paint_method, self))

    @staticmethod
    def paint_method(painter, rect, color=None):
        w2 = rect.width() / 2
        h2 = rect.height() / 2
        path = QtGui.QPainterPath(QtCore.QPointF(w2, 1))
        path.lineTo(w2 + w2 - 1, h2)
        path.lineTo(1, h2)
        path.lineTo(w2, 1)
        #p = painter.pen()
        #p.setWidthF(2)
        #painter.setPen(p)
        painter.drawPath(path)

    def paint_settings(self):
        return {'color':ctrl.cm.ui()}

