# coding=utf-8
from PyQt5 import QtGui, QtWidgets
from kataja.UIItem import UIWidget
from kataja.singletons import qt_prefs, ctrl
import kataja.globals as g
from kataja.ui_widgets.PushButtonBase import PushButtonBase


class ModalTextButton(PushButtonBase):

    def __init__(self, text0, text1, pixmap=None, **kwargs):
        PushButtonBase.__init__(self, **kwargs)
        self.setText(text0)
        self.setCheckable(True)
        self.pixmap = pixmap
        self.text0 = text0
        self.text1 = text1
        self.icon0 = None
        self.icon1 = None
        self.tooltip0 = ''
        self.tooltip1 = ''
        self.setCheckable(True)
        self.setFlat(True)
        font = QtGui.QFont(qt_prefs.fonts[g.UI_FONT])
        font.setPointSize(font.pointSize() * 1.2)
        fm = QtGui.QFontMetrics(font)
        mw = max(fm.width(text0), fm.width(text1))
        self.setMinimumWidth(mw + 24)
        self.setMinimumHeight(24)
        self.toggled.connect(self.toggle_state)
        self.compose_icon()
        self.toggle_state(False)
        ctrl.add_watcher(self, 'ui_font_changed')

    def toggle_state(self, value):
        if value:
            if self.icon1:
                self.setIcon(self.icon1)
            self.setText(self.text1)
            self.k_tooltip = self.tooltip1
        else:
            if self.icon0:
                self.setIcon(self.icon0)
            self.setText(self.text0)
            self.k_tooltip = self.tooltip0
        self.updateGeometry()
        self.update_position()

    def update_colors(self):
        self.compose_icon()

    def compose_icon(self):
        """ Redraw the image to be used as a basis for icon, this is necessary
        to update the overlay color.
        :return:
        """
        if self.pixmap:
            c = ctrl.cm.ui()
            image = QtGui.QImage(self.pixmap)
            painter = QtGui.QPainter(image)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
            painter.fillRect(image.rect(), c)
            painter.end()
            self.icon0 = QtGui.QIcon(QtGui.QPixmap().fromImage(image))
            c = ctrl.cm.paper()
            image = QtGui.QImage(self.pixmap)
            painter = QtGui.QPainter(image)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
            painter.fillRect(image.rect(), c)
            painter.end()
            self.icon1 = QtGui.QIcon(QtGui.QPixmap().fromImage(image))

    def watch_alerted(self, obj, signal, field_name, value):
        """ Receives alerts from signals that this object has chosen to listen. These signals
         are declared in 'self.watchlist'.

         This method will try to sort out the received signals and act accordingly.

        :param obj: the object causing the alarm
        :param signal: identifier for type of the alarm
        :param field_name: name of the field of the object causing the alarm
        :param value: value given to the field
        :return:
        """
        if signal == 'ui_font_changed':
            font = QtGui.QFont(qt_prefs.fonts[g.UI_FONT])
            font.setPointSize(font.pointSize() * 1.2)
            fm = QtGui.QFontMetrics(font)
            mw = max([fm.width(text) for text in self.text_options])
            self.setMinimumWidth(mw + 12)
            self.update()