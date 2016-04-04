# coding=utf-8
from PyQt5 import QtCore, QtGui, QtWidgets
from kataja.UIItem import UIItem
from kataja.singletons import qt_prefs, ctrl
import kataja.globals as g

borderstyle = """
PanelButton {border: 1px transparent none}
:hover {border: 1px solid %s; border-radius: 3}
:pressed {border: 1px solid %s; background-color: %s; border-radius: 3}
:checked {border: 1px transparent none; background-color: %s; border-radius: 3; color: %s}
"""


class ModeLabel(UIItem, QtWidgets.QPushButton):
    def __init__(self, text, ui_key, parent=None):
        UIItem.__init__(self, ui_key, None)
        QtWidgets.QLabel.__init__(self, text, parent=parent)
        self.setCheckable(True)
        f = QtGui.QFont(qt_prefs.fonts[g.UI_FONT])
        f.setPointSize(f.pointSize() * 1.5)
        self.setFont(f)
        self.setPalette(ctrl.cm.get_qt_palette_for_ui())
        #self.setPalette(ctrl.cm.palette_from_key(color_key))
        self.setFlat(True)
        c = ctrl.cm.ui()
        paper = ctrl.cm.paper()
        self.setContentsMargins(2, 2, 2, 2)
        self.setStyleSheet(
            borderstyle % (c.name(), c.lighter().name(), paper.name(), c.name(), paper.name()))

    def update_position(self):
        self.move(6, 4)

    def update_colors(self):
        self.setPalette(ctrl.cm.get_qt_palette_for_ui())
        c = ctrl.cm.ui()
        paper = ctrl.cm.paper()
        self.setStyleSheet(
            borderstyle % (c.name(), c.lighter().name(), paper.name(), c.name(), paper.name()))

    def set_text(self, text):
        self.setText(text)
        self.setContentsMargins(2, 2, 2, 2)
        w = self.minimumSizeHint().width()
        self.setMinimumWidth(w + 4)
        self.updateGeometry()
        self.update_position()
        #self.resize(self.minimumSizeHint()) # + QtCore.QSize(4, 4))
