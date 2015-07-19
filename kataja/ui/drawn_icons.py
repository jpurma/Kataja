__author__ = 'purma'

from PyQt5 import QtGui, QtCore


def fit_to_screen(painter, rect, color=None):
    w = rect.width()
    h = rect.height()
    pen = painter.pen()
    pen.setWidth(2)
    painter.setPen(pen)
    painter.drawRoundedRect(rect, 12, 12)
    pen.setStyle(QtCore.Qt.DotLine)
    painter.setPen(pen)
    painter.drawRect(QtCore.QRect(6, 6, w-12, h-12))


def arrow(painter, rect, color=None):
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
    path.lineTo(w - 10, 8 + (10 * d))
    path.lineTo(w - 8, 4 + (8 * d))
    path.lineTo(w - 12, 12 * d)
    painter.fillPath(path, color)


def divider(painter, rect, color=None):
    w = rect.width()
    h = rect.height()
    path = QtGui.QPainterPath(QtCore.QPointF(0, h - 4))
    path.cubicTo(10, h - 10, w - 10, 10, w, 4)
    p = painter.pen()
    p.setWidthF(2)
    p.setStyle(QtCore.Qt.DashLine)
    painter.setPen(p)
    painter.drawPath(path)

