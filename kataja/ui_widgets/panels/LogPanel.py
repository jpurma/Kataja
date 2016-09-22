from PyQt5 import QtWidgets, QtCore

import kataja.globals as g
from kataja.singletons import qt_prefs
from kataja.ui_widgets.Panel import Panel
from kataja.singletons import ctrl, log


__author__ = 'purma'

style_sheet = """
b {font-weight: bold;}
"""

class LogPanel(Panel):
    """ Dump window """

    def __init__(self, name, default_position='bottom', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        Panel.__init__(self, name, default_position, parent, folded)
        inner = QtWidgets.QTextBrowser()
        layout = QtWidgets.QVBoxLayout()
        inner.setMinimumHeight(48)
        inner.preferred_size = QtCore.QSize(940, 64)
        inner.setFont(qt_prefs.get_font(g.CONSOLE_FONT))  # @UndefinedVariable
        inner.setAutoFillBackground(True)
        inner.sizeHint = self.sizeHint
        inner.setFocusPolicy(QtCore.Qt.NoFocus)
        inner.document().setDefaultStyleSheet(style_sheet)
        self.resize_grip = QtWidgets.QSizeGrip(self)
        self.resize_grip.hide()
        self.setAllowedAreas(QtCore.Qt.TopDockWidgetArea | QtCore.Qt.BottomDockWidgetArea)
        layout.addWidget(self.resize_grip, 0, QtCore.Qt.AlignRight)
        inner.setLayout(layout)

        self.preferred_size = inner.preferred_size
        self.setWidget(inner)
        self.finish_init()
        log.log_handler.set_widget(inner)

    def sizeHint(self):
        if self.isFloating():
            return QtCore.QSize(480, 640)
        else:
            return self.preferred_size

    def report_top_level(self, floating):
        super().report_top_level(floating)
        if floating:
            self.resize(QtCore.QSize(480, 480))

    def update(self, *args):
        self.widget().setFont(qt_prefs.get_font(g.CONSOLE_FONT))
        super().update(*args)
