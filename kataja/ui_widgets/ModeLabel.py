# coding=utf-8
from PyQt5 import QtGui
from kataja.UIItem import UIWidget
from kataja.singletons import qt_prefs, ctrl
import kataja.globals as g
from kataja.ui_widgets.OverlayButton import PanelButton


class ModeLabel(UIWidget, PanelButton):

    permanent_ui = True

    def __init__(self, text_options, ui_key, parent=None):
        UIWidget.__init__(self, ui_key=ui_key)
        PanelButton.__init__(self, None, text_options[0], size=24, parent=parent)
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
        else:
            self.setText(self.text_options[0])
        self.updateGeometry()
        self.update_position()

    def update_colors(self):
        self.compose_icon()

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
