# coding=utf-8
from PyQt5 import QtWidgets

from kataja.singletons import ctrl


class HUD(QtWidgets.QGraphicsSimpleTextItem):
    """

    """

    def __init__(self, parent=None):
        QtWidgets.QGraphicsSimpleTextItem.__init__(self, 'HUD')  # , scene = parent)
        self.setPos(14, 4)
        self.setBrush(ctrl.cm.ui())

    def update_color(self):
        """


        """
        self.setBrush(ctrl.cm.ui())
        self.update()

