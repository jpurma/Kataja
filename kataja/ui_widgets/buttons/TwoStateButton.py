# coding=utf-8
from PyQt5 import QtGui

import kataja.globals as g
from kataja.singletons import qt_prefs, ctrl
from kataja.ui_widgets.buttons.PanelButton import PanelButton
from kataja.utils import colored_image


class TwoStateButton(PanelButton):

    def __init__(self, text0='', text1='', pixmap0=None, pixmap1=None, **kwargs):
        self.text0 = text0
        self.text1 = text1
        self.pixmap0 = pixmap0
        self.pixmap1 = pixmap1
        self.image0 = pixmap0.toImage() if pixmap0 else None
        self.image1 = pixmap1.toImage() if pixmap1 else None
        PanelButton.__init__(self, **kwargs)
        self.setText(text0)
        self.icon0 = None
        self.icon1 = None
        self.setCheckable(True)
        if text0:
            font = QtGui.QFont(qt_prefs.fonts[g.UI_FONT])
            font.setPointSize(font.pointSize() * 1.2)
            fm = QtGui.QFontMetrics(font)
            mw = max(fm.width(text0), fm.width(text1))
            self.setMinimumWidth(mw + 24)
            ctrl.main.ui_font_changed.connect(self.update_font)
        self.setMinimumHeight(24)
        # noinspection PyUnresolvedReferences
        self.toggled.connect(self.toggle_state)
        self.compose_icon()
        self.toggle_state(False)

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

    def update_colors(self, color_key=None):
        self.compose_icon()

    def compose_icon(self):
        """ Redraw the image to be used as a basis for icon, this is necessary
        to update the overlay color.
        :return:
        """
        if not self.pixmap0:
            return
        image0 = colored_image(ctrl.cm.ui(), self.image0)
        if self.image1:
            image1 = colored_image(ctrl.cm.ui(), self.image1)
        else:
            image1 = colored_image(ctrl.cm.paper(), self.image0)
        # noinspection PyArgumentList
        self.icon0 = QtGui.QIcon(QtGui.QPixmap().fromImage(image0))
        # noinspection PyArgumentList
        self.icon1 = QtGui.QIcon(QtGui.QPixmap().fromImage(image1))

    def update_font(self):
        font = QtGui.QFont(qt_prefs.fonts[g.UI_FONT])
        font.setPointSize(font.pointSize() * 1.2)
        fm = QtGui.QFontMetrics(font)
        mw = max([fm.width(text) for text in self.text_options])
        self.setMinimumWidth(mw + 12)
        self.update()
