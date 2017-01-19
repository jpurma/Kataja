# coding=utf-8
from PyQt5 import QtGui
from kataja.UIItem import UIWidget
from kataja.singletons import qt_prefs, ctrl
import kataja.globals as g
from kataja.ui_widgets.OverlayButton import PanelButton


class ModeLabel(UIWidget, PanelButton):

    permanent_ui = True

    def __init__(self, text_options, ui_key, parent=None, icon=None):
        UIWidget.__init__(self, ui_key=ui_key)
        self.negated_icon = None
        PanelButton.__init__(self, icon, text_options[0], size=24, parent=parent)
        self.setCheckable(True)
        self.text_options = text_options
        font = QtGui.QFont(qt_prefs.fonts[g.UI_FONT])
        font.setPointSize(font.pointSize() * 1.2)
        fm = QtGui.QFontMetrics(font)
        mw = max([fm.width(text) for text in text_options])
        self.setFlat(True)
        self.setMinimumWidth(mw + 12)
        self.setMinimumHeight(24)
        ctrl.add_watcher(self, 'ui_font_changed')

    def checkStateSet(self):
        val = self.isChecked()
        if val:
            self.setText(self.text_options[1])
            if self.negated_icon:
                self.setIcon(self.negated_icon)
        else:
            self.setText(self.text_options[0])
            if self.normal_icon:
                self.setIcon(self.normal_icon)
        self.updateGeometry()
        self.update_position()

    def update_colors(self):
        self.compose_icon()

    def compose_icon(self):
        """ Redraw the image to be used as a basis for icon, this is necessary
        to update the overlay color.
        :return:
        """
        super().compose_icon()
        c = ctrl.cm.paper()
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
        self.negated_icon = QtGui.QIcon(QtGui.QPixmap().fromImage(image))

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
