__author__ = 'purma'

from PyQt5 import QtGui, QtCore


def fit_to_screen(painter, rect, color=None):
    w = rect.width()
    h = rect.height()
    pen = painter.pen()
    if color:
        pen.setColor(color)
    pen.setWidth(2)
    painter.setPen(pen)
    # painter.drawRoundedRect(rect, 12, 12)
    pen.setStyle(QtCore.Qt.DotLine)
    painter.setPen(pen)
    painter.drawRect(QtCore.QRect(6, 6, w - 12, h - 12))

    pen.setStyle(QtCore.Qt.SolidLine)

    painter.setPen(pen)
    painter.drawLine(10, 10, 20, 20)
    painter.drawLine(10, 10, 14, 10)
    painter.drawLine(10, 10, 10, 14)

    painter.drawLine(w - 10, 10, w - 20, 20)
    painter.drawLine(w - 10, 10, w - 14, 10)
    painter.drawLine(w - 10, 10, w - 10, 14)

    painter.drawLine(10, h - 10, 20, h - 20)
    painter.drawLine(10, h - 10, 14, h - 10)
    painter.drawLine(10, h - 10, 10, h - 14)

    painter.drawLine(w - 10, h - 10, w - 20, h - 20)
    painter.drawLine(w - 10, h - 10, w - 14, h - 10)
    painter.drawLine(w - 10, h - 10, w - 10, h - 14)


def pan_around(painter, rect, color=None, paper=None):
    w = rect.width()
    h = rect.height()
    cx = w / 2.0
    cy = h / 2.0
    pen = painter.pen()
    if paper:
        painter.fillRect(rect, paper)
    if color:
        pen.setColor(color)
    pen.setWidth(2)
    painter.setPen(pen)
    pen.setStyle(QtCore.Qt.DotLine)
    painter.setPen(pen)
    painter.drawRect(QtCore.QRect(6, 6, w - 12, h - 12))

    pen.setStyle(QtCore.Qt.SolidLine)

    painter.setPen(pen)
    left = cx - 12
    right = cx + 12
    up = cy - 12
    down = cy + 12
    painter.drawLine(cx, up, cx, down)
    painter.drawLine(cx - 4, up + 4, cx, up)
    painter.drawLine(cx + 4, up + 4, cx, up)
    painter.drawLine(cx - 4, down - 4, cx, down)
    painter.drawLine(cx + 4, down - 4, cx, down)

    painter.drawLine(left, cy, right, cy)
    painter.drawLine(left + 4, cy - 4, left, cy)
    painter.drawLine(left + 4, cy + 4, left, cy)
    painter.drawLine(right - 4, cy - 4, right, cy)
    painter.drawLine(right - 4, cy + 4, right, cy)


def select_mode(painter, rect, color=None, paper=None):
    w = rect.width()
    h = rect.height()
    pen = painter.pen()
    if paper:
        painter.fillRect(rect, paper)
    if color:
        pen.setColor(color)
    pen.setWidth(2)
    painter.setPen(pen)
    pen.setStyle(QtCore.Qt.DotLine)
    painter.setPen(pen)
    painter.drawRect(QtCore.QRect(6, 6, w - 12, h - 12))

    painter.drawRect(QtCore.QRect(10, 10, w - 30, h - 30))
    pen.setStyle(QtCore.Qt.SolidLine)
    painter.setPen(pen)
    cx = 10 + w - 30
    cy = 10 + h - 30
    painter.drawLine(cx, cy - 6, cx, cy + 6)
    painter.drawLine(cx - 6, cy, cx + 6, cy)


def arrow(painter, rect, color=None):
    w = rect.width()
    h = rect.height()
    if w == 0 or h == 0:
        return
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
