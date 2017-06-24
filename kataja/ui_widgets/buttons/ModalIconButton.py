# coding=utf-8
from PyQt5 import QtGui
from kataja.singletons import ctrl
from kataja.ui_widgets.PushButtonBase import PushButtonBase


class ModalIconButton(PushButtonBase):

    permanent_ui = True

    def __init__(self, pixmap0=None, pixmap1=None, **kwargs):
        PushButtonBase.__init__(self, **kwargs)
        self.pixmap0 = pixmap0
        self.pixmap1 = pixmap1
        self.icon0 = None
        self.icon1 = None
        self.setCheckable(True)
        self.setFlat(True)
        self.tooltip0 = ''
        self.tooltip1 = ''
        if 'size' in kwargs:
            self.setMinimumSize(self.iconSize())
        self.setContentsMargins(0, 0, 0, 0)
        self.update_colors()
        self.compose_icon()
        self.toggled.connect(self.toggle_state)
        self.setIcon(self.icon0)

    def toggle_state(self, value):
        if value:
            self.setIcon(self.icon1)
            self.k_tooltip = self.tooltip1
        else:
            self.setIcon(self.icon0)
            self.k_tooltip = self.tooltip0
        self.updateGeometry()
        self.update_position()

    def update_colors(self, color_key=None):
        if color_key:
            self.color_key = color_key
        self.compose_icon()

    def compose_icon(self):
        """ Redraw the image to be used as a basis for icon, this is necessary
        to update the overlay color.
        :return:
        """
        c = ctrl.cm.ui()
        image = QtGui.QImage(self.pixmap0)
        painter = QtGui.QPainter(image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
        painter.fillRect(image.rect(), c)
        painter.end()
        self.icon0 = QtGui.QIcon(QtGui.QPixmap().fromImage(image))
        image = QtGui.QImage(self.pixmap1)
        painter = QtGui.QPainter(image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
        painter.fillRect(image.rect(), c)
        painter.end()
        self.icon1 = QtGui.QIcon(QtGui.QPixmap().fromImage(image))
