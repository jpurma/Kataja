from PyQt5 import QtWidgets, QtCore

from kataja.singletons import ctrl, classes
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.buttons.PanelButton import PanelButton
from kataja.ui_widgets.SelectionBox import SelectionBox
import kataja.globals as g

__author__ = 'purma'


class ScopePanel(Panel):
    """ Panel for editing how edges and nodes are drawn. """

    def __init__(self, name, default_position='right', parent=None, folded=True):
        """
        All of the panel constructors follow the same format so that the
        construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        Panel.__init__(self, name, default_position, parent, folded,
                       foldable=False)
        items = [(g.SELECTION, 'scope is selection'), (g.FOREST, 'scope is forest'),
                 (g.DOCUMENT, 'scope is document'), (g.PREFS, 'scope is preferences')]

        self.scope_selector = SelectionBox(data=items, action='set_scope_for_node_style')
        self.scope_selector.setMaximumWidth(128)
        self.push_to_title(self.scope_selector)
        self.reset_button = PanelButton(text='reset', action='reset_settings')
        self.reset_button.setMinimumHeight(14)
        self.reset_button.setMaximumHeight(14)
        self.push_to_title(self.reset_button)
        inner = QtWidgets.QWidget()
        inner.setMaximumHeight(40)
        inner.setMinimumWidth(160)
        inner.setMaximumWidth(220)
        hlayout = QtWidgets.QHBoxLayout()
        inner.setLayout(hlayout)
        self.setWidget(inner)
        self.widget().setAutoFillBackground(True)
        self.finish_init()
