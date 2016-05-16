# coding=utf-8
# #######################################################
from PyQt5 import QtWidgets

from kataja.shapes import draw_arrow_shape, arrow_shape_bounding_rect
from kataja.UIItem import UIItem
from kataja.uniqueness_generator import next_available_type_id


class StretchLine(UIItem, QtWidgets.QGraphicsLineItem):
    """ Temporary arrow for dragging and pointing """
    __qt_type_id__ = next_available_type_id()

    def __init__(self, line, host):
        UIItem.__init__(unique=True, host=host)
        QtWidgets.QGraphicsLineItem.__init__(self, line)
        self._arrow_size = 5.0
        self.setZValue(52)

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

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

