from PyQt5 import QtGui

from kataja.ui_support.ColorSwatchIconEngine import ColorSwatchIconEngine


class LineColorIcon(QtGui.QIcon):
    """

    :param color_id:
    :param model:
    """

    def __init__(self, color_id, model):
        QtGui.QIcon.__init__(self, ColorSwatchIconEngine(color_id, model))