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

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. List of types is kept as comments in globals.py,
        but for performance reasons just hardcode it here.
        :return:
        """
        return 65654

    def update_colors(self):
        """


        """
        self.setBrush(ctrl.cm.ui())
        self.update()

