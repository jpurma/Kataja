from PyQt5 import QtWidgets, QtCore

from kataja.singletons import qt_prefs
from kataja.ui.panels.UIPanel import UIPanel
import kataja.globals as g


__author__ = 'purma'


class LogPanel(UIPanel):
    """ Dump window """

    def __init__(self, name, key, default_position='bottom', parent=None, ui_manager=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        UIPanel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        inner = QtWidgets.QTextBrowser()
        inner.setMinimumHeight(48)
        inner.preferred_size = QtCore.QSize(940, 64)
        inner.setFont(qt_prefs.font(g.CONSOLE_FONT))  # @UndefinedVariable
        inner.setAutoFillBackground(True)
        inner.sizeHint = self.sizeHint
        self.preferred_size = inner.preferred_size
        self.setWidget(inner)
        ui_manager.log_writer.attach_display_widget(inner)
        self.finish_init()


    def sizeHint(self):
        #print("LogPanel asking for sizeHint, ", self.preferred_size)
        return self.preferred_size