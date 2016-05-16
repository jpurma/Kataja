from PyQt5 import QtWidgets, QtCore

import kataja.globals as g
from kataja.singletons import qt_prefs
from kataja.ui_items.Panel import Panel


__author__ = 'purma'


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
        inner.setMinimumHeight(48)
        inner.preferred_size = QtCore.QSize(940, 64)
        inner.setFont(qt_prefs.font(g.CONSOLE_FONT))  # @UndefinedVariable
        inner.setAutoFillBackground(True)
        inner.sizeHint = self.sizeHint
        inner.setFocusPolicy(QtCore.Qt.NoFocus)
        self.preferred_size = inner.preferred_size
        self.setWidget(inner)
        self.ui_manager.log_writer.attach_display_widget(inner)
        self.finish_init()


    def sizeHint(self):
        #print("LogPanel asking for sizeHint, ", self.preferred_size)
        return self.preferred_size

    def update(self, *args):
        self.widget().setFont(qt_prefs.font(g.CONSOLE_FONT))
        super().update(*args)
