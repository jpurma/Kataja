from PyQt5 import QtWidgets, QtCore
from kataja.singletons import qt_prefs
from kataja.ui.UIPanel import UIPanel

__author__ = 'purma'


class LogPanel(UIPanel):
    """ Dump window """

    def __init__(self, name, default_position='bottom', parent=None, ui_buttons=None):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, default_position, parent)
        self.setWidget(QtWidgets.QTextBrowser())
        self.widget().setFont(qt_prefs.menu_font)  # @UndefinedVariable
        self.widget().setAutoFillBackground(True)
        self.show()
        print('*** created log panel ***')
