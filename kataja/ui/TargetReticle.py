########################################################
from PyQt5 import QtCore, QtWidgets

from kataja.Controller import colors


class TargetReticle(QtWidgets.QGraphicsItem):
    width = 30
    height = 30

    def __init__(self, parent=None, graph=None):
        QtWidgets.QGraphicsItem.__init__(self)
        # MovableUI.__init__(self)
        self.setZValue(52)
        self._host_node = parent
        self.setPos(parent.pos())
        self.bounding_rect = QtCore.QRectF(TargetReticle.width / -2, TargetReticle.height / -2, TargetReticle.width,
                                           TargetReticle.height)

    def paint(self, painter, option, widget):
        painter.setPen(colors.selection_pen)
        painter.drawLine(0, -15, 0, 15)
        painter.drawLine(-15, 0, 15, 0)
        painter.drawEllipse(-10, -10, 20, 20)

    def boundingRect(self):
        return self.bounding_rect

    def update_host(self, parent):
        self._host_node = parent

    def is_over(self, node):
        return node is self._host_node

    def update_position(self, graph):
        self.setPos(graph.mapFromScene(self._host_node.pos()))


