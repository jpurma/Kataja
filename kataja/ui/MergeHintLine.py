########################################################
from PyQt5 import QtGui, QtCore, QtWidgets

from kataja.Controller import colors
from PyQt5.QtCore import QPointF as Pf


class MergeHintLine(QtWidgets.QGraphicsItem):
    """ A dotted line for suggesting possible merges """

    def __init__(self, start, end, graph):
        self.hover_target = None
        self.start = start
        self.end = end
        self.graph = graph
        self._ui_line = QtCore.QLineF(graph.mapFromScene(start.pos()),
                                      graph.mapFromScene(getattr(end, 'middle_point', end.pos())))
        self.setZValue(55)
        QtWidgets.QGraphicsItem.__init__(self)

    def remove(self):
        del self

    def paint(self, painter, option, widget):
        startpos = self.graph.mapFromScene(self.start.pos())
        self.prepareGeometryChange()
        if hasattr(self.end, 'middle_point'):
            endpos = self.graph.mapFromScene(self.end.middle_point)
            self._ui_line = QtCore.QLineF(startpos, endpos)
            painter.setPen(QtGui.QPen(colors.ui, max((0.1, (80 - self._ui_line.length()) / 10))))
            painter.drawLine(self._ui_line)
            if endpos.x() < startpos.x():
                painter.drawText(endpos.x(), endpos.y() - 30, unichr(8594))  # 0x2192 8594 rightarrow
            else:
                painter.drawText(endpos.x(), endpos.y() - 30, unichr(8592))  # 0x2190 8592 leftarrow

        else:
            endpos = self.graph.mapFromScene(self.end.pos())
            self._ui_line = QtCore.QLineF(startpos, endpos)
            painter.setPen(QtGui.QPen(colors.ui, max((0.1, (80 - self._ui_line.length()) / 10))))
            cp = Pf((startpos.x() + endpos.x()) / 2, ((startpos.y() + endpos.y()) / 2) - 15)
            painter.drawLine(startpos, cp)
            painter.drawLine(cp, endpos)
            xmax = max((startpos.x(), endpos.x()))
            xmin = min((startpos.x(), endpos.x()))
            ymax = max((startpos.y(), endpos.y()))
            ymin = min((startpos.y(), endpos.y(), cp.y()))
            self._ui_line = QtCore.QLineF(Pf(xmin, ymin), Pf(xmax, ymax))

    def boundingRect(self):
        l = self._ui_line
        return QtCore.QRectF(l.p1(), l.p2())

    def update_visibility(self):
        self.show()

