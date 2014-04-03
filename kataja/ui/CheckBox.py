from kataja.Controller import colors, ctrl
from PyQt5 import QtWidgets, QtCore


class CheckBox(QtWidgets.QGraphicsItem):
    def __init__(self, parent, marker='X'):
        QtWidgets.QGraphicsItem.__init__(self, parent, scene=parent.scene())
        self._hover = False
        self.setAcceptHoverEvents(False)
        self.setZValue(52)
        self.marker = marker

    def paint(self, painter, option, widget):
        r = QtCore.QRectF(-8, -4, 15, 15)
        painter.setPen(colors.ui)
        if self._hover:
            painter.setBrush(colors.ui_hover)
            painter.drawRect(r)
            painter.setPen(colors.ui)
            painter.drawText(r, self.marker)
        elif self.parentItem().checked:
            painter.setBrush(colors.ui_secondary)
            painter.drawRect(r)
            painter.setPen(colors.ui)
            painter.drawText(r, self.marker)
        else:
            painter.setBrush(colors.paper)
            painter.drawRect(r)

    def hoverEnterEvent(self, event):
        self._hover = True
        self.parentItem().hoverLeaveEvent(event)

    def hoverLeaveEvent(self, event):
        self._hover = False

    def mousePressEvent(self, event):
        self.parentItem().selectOption()
        ctrl.ui_pressed = self

    def mouseReleaseEvent(self, event):
        ctrl.ui_pressed = None

    def boundingRect(self):
        return QtCore.QRectF(-8, -4, 15, 15)
