from PyQt5 import QtWidgets

from kataja.ui.panels.UIPanel import UIPanel
from kataja.parser.latex_to_unicode import latex_to_unicode
from kataja.singletons import qt_prefs
import kataja.globals as g
from utils import time_me

__author__ = 'purma'


class SymbolPanel(UIPanel):
    """
        Panel for rapid testing of various UI elements that otherwise may be hidden behind complex screens or logic.
    """

    def __init__(self, name, key, default_position='right', parent=None, ui_manager=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        inner = QtWidgets.QListWidget()
        #inner.setUniformItemSizes(True)
        inner.setSpacing(8)
        inner.setMovement(QtWidgets.QListWidget.Static)
        inner.setViewMode(QtWidgets.QListWidget.IconMode)
        inner.setFont(qt_prefs.fonts[g.BIG_FONT])
        self.prepare_symbols(inner)
        self.setWidget(inner)
        self.finish_init()

    @time_me
    def prepare_symbols(self, inner):
        keys = list(latex_to_unicode.keys())
        keys.sort()
        for key in keys:
            char, description = latex_to_unicode[key]
            item = QtWidgets.QListWidgetItem(char)
            item.setToolTip(description)
            inner.addItem(item)
