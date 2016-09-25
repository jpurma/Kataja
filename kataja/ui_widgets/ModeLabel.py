# coding=utf-8
from PyQt5 import QtCore, QtGui, QtWidgets
from kataja.UIItem import UIWidget
from kataja.singletons import qt_prefs, ctrl
import kataja.globals as g
from kataja.ui_widgets.OverlayButton import PanelButton

style_sheet = """
ModeLabel {border: 1px transparent none}
:hover {border: 1px solid %s; border-radius: 3}
:pressed {border: 1px solid %s; background-color: %s; border-radius: 3}
:checked {border: 1px transparent none; background-color: %s; border-radius: 3; color: %s}
"""  # (c.name(), c.lighter().name(), paper.name(), c.name(), paper.name())

class ModeLabel(UIWidget, PanelButton):

    permanent_ui = True

    def __init__(self, text_options, ui_key, parent=None):
        UIWidget.__init__(self, ui_key=ui_key)
        PanelButton.__init__(self, None, text_options[0], size=24, parent=parent) #
        self.ui_key = ui_key
        # qt_prefs.v_refresh_small_icon
        self.setCheckable(True)
        self.text_options = text_options
        f = QtGui.QFont(qt_prefs.fonts[g.UI_FONT])
        f.setPointSize(f.pointSize() * 1.5)
        fm = QtGui.QFontMetrics(f)
        mw = max([fm.width(text) for text in text_options])
        self.setFont(f)
        self.setPalette(ctrl.cm.get_qt_palette_for_ui())
        self.setFlat(True)
        self.update_style_sheet()
        self.setMinimumWidth(mw + 8)

    def set_checked(self, val):
        if val:
            self.setText(self.text_options[1])
            self.setChecked(True)
        else:
            self.setText(self.text_options[0])
            self.setChecked(False)
        #self.setMinimumSize(self.minimumSizeHint() + QtCore.QSize(4, 4))
        self.updateGeometry()
        self.update_position()

    def compose_icon(self):
        """ Redraw the image to be used as a basis for icon, this is necessary
        to update the overlay color.
        :return:
        """
        if self.pixmap:
            image = self.pixmap.toImage()
            painter = QtGui.QPainter(image)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
            painter.fillRect(image.rect(), ctrl.cm.get(self.color_key))
            painter.end()
            i = QtGui.QIcon(QtGui.QPixmap.fromImage(image))
            image2 = self.pixmap.toImage()
            painter = QtGui.QPainter(image2)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
            painter.fillRect(image2.rect(), ctrl.cm.paper())
            painter.end()
            i.addPixmap(QtGui.QPixmap.fromImage(image2), state=QtGui.QIcon.On)
            self.setIcon(i)

    def update_colors(self):
        self.compose_icon()
        self.update_style_sheet()

    def update_style_sheet(self):
        paper = ctrl.cm.paper()
        c = ctrl.cm.get(self.color_key)
        self.setStyleSheet(style_sheet % (c.name(), c.lighter().name(), paper.name(), c.name(),
        paper.name()))