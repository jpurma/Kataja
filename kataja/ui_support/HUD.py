# coding=utf-8
from PyQt5 import QtWidgets

from kataja.singletons import ctrl
from kataja.qtype_generator import next_available_type_id


class HUD(QtWidgets.QGraphicsSimpleTextItem):
    """

    """
    __qt_type_id__ = next_available_type_id()

    def __init__(self, parent=None):
        QtWidgets.QGraphicsSimpleTextItem.__init__(self, 'HUD')  # , scene = parent)
        self.setPos(14, 4)
        self.setBrush(ctrl.cm.ui())

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

    def update_colors(self):
        """


        """
        self.setBrush(ctrl.cm.ui())
        self.update()

