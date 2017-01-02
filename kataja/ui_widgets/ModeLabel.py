# coding=utf-8
from PyQt5 import QtGui
from kataja.UIItem import UIWidget
from kataja.singletons import qt_prefs, ctrl
import kataja.globals as g
from kataja.ui_widgets.OverlayButton import PanelButton

style_sheet = """
ModeLabel {border: 1px transparent none}
:hover {border: 1px solid %(draw)s; border-radius: 3}
:pressed {border: 1px solid %(lighter)s; background-color: %(paper)s; border-radius: 3}
:checked:!hover {border: 1px solid %(paper)s; background-color: %(draw)s; border-radius: 3;
color: %(paper)s}
:checked:hover {border-color: %(lighter)s; background-color: %(draw)s; border-radius: 3;
color: %(lighter)s}
"""


class ModeLabel(UIWidget, PanelButton):

    permanent_ui = True

    def __init__(self, text_options, ui_key, parent=None):
        UIWidget.__init__(self, ui_key=ui_key)
        PanelButton.__init__(self, None, text_options[0], size=24, parent=parent)
        self.setCheckable(True)
        self.text_options = text_options
        f = QtGui.QFont(qt_prefs.fonts[g.UI_FONT])
        f.setPointSize(f.pointSize() * 1.2)
        fm = QtGui.QFontMetrics(f)
        mw = max([fm.width(text) for text in text_options])
        self.setStyleSheet('font-family: "%s"; font-size: %spx;' % (
            f.family(), int(f.pointSize())))
        self.setPalette(ctrl.cm.get_qt_palette_for_ui())
        self.setFlat(True)
        self.setMinimumWidth(mw + 12)
        self.setMinimumHeight(24)

    def checkStateSet(self):
        val = self.isChecked()
        if val:
            self.setText(self.text_options[1])
        else:
            self.setText(self.text_options[0])
        self.updateGeometry()
        self.update_position()

    def update_colors(self):
        pass

    def update_style_sheet(self):
        pass