from PyQt5 import QtCore, QtGui

from kataja.singletons import qt_prefs, ctrl
from kataja.ui_widgets.PushButtonBase import PushButtonBase


class PanelButton(PushButtonBase):
    """ Buttons that change their color according to widget where they are.
        Currently this is not doing anything special that can't be done by
        setting TwoColorIconEngine for normal button, but let's keep this in case we
        need to deliver palette updates to icon engines."""

    def __init__(self, pixmap=None, color_key='accent8', draw_method=None, **kwargs):
        PushButtonBase.__init__(self, **kwargs)
        self.draw_method = draw_method
        self.color_key = color_key
        self.base_image = None
        self.normal_icon = None
        self.hover_icon = None
        size = self.iconSize()
        if isinstance(pixmap, str):
            pixmap = getattr(qt_prefs, pixmap)
        if isinstance(pixmap, QtGui.QIcon):
            self.pixmap = pixmap.pixmap(size)
        else:
            self.pixmap = pixmap
        if self.pixmap:
            self.base_image = self.pixmap.toImage()
        elif self.draw_method:
            isize = QtCore.QSize(size.width() * 2, size.height() * 2)
            self.base_image = QtGui.QImage(
                isize, QtGui.QImage.Format_ARGB32_Premultiplied)
            self.base_image.fill(QtCore.Qt.transparent)
        self.compose_icon()

        self.w2 = self.iconSize().width() / 2
        self.h2 = self.iconSize().height() / 2
        self.setContentsMargins(0, 0, 0, 0)
        self.setFlat(True)
        self.update_colors()

    def contextual_color(self):
        if self.isDown():
            return ctrl.cm.get(self.color_key).lighter()
        else:
            return ctrl.cm.get(self.color_key)

    def compose_icon(self):
        """ Redraw the image to be used as a basis for icon, this is necessary
        to update the overlay color.
        :return:
        """
        c = ctrl.cm.get(self.color_key)
        if self.pixmap:
            image = QtGui.QImage(self.base_image)
            painter = QtGui.QPainter(image)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
            painter.fillRect(image.rect(), c)
            painter.end()

        elif self.draw_method:

            image = QtGui.QImage(self.base_image)

            painter = QtGui.QPainter(image)
            #painter.setDevicePixelRatio(2.0)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setPen(c)
            self.draw_method(painter, image.rect(), c)
            painter.end()
        else:
            return
        self.normal_icon = QtGui.QIcon(QtGui.QPixmap().fromImage(image))
        self.setIcon(self.normal_icon)

    def update_colors(self, color_key=None):
        if color_key:
            self.color_key = color_key
        #self.update_style_sheet()
        self.compose_icon()