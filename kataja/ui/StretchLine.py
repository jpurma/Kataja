# coding=utf-8
# #######################################################
from PyQt5 import QtWidgets

from kataja.shapes import draw_arrow_shape, arrow_shape_bounding_rect


class StretchLine(QtWidgets.QGraphicsLineItem):
    """ Temporary arrow for dragging and pointing """

    def __init__(self, line):
        self._arrow_size = 5.0
        self.setZValue(52)
        QtWidgets.QGraphicsLineItem.__init__(self, line)

    def remove(self):
        """


        """
        del self
        # self.removeFromIndex()

    def paint(self, painter, option, widget):
        """

        :param painter:
        :param option:
        :param widget:
        """
        draw_arrow_shape(self, painter)

    def boundingRect(self):
        """


        :return:
        """
        return arrow_shape_bounding_rect(self)

    def update_visibility(self):
        """


        """
        self.show()

