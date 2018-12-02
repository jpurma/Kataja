from PyQt5 import QtWidgets, QtCore

from kataja.singletons import ctrl, classes
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.buttons.PanelButton import PanelButton
from kataja.ui_widgets.SelectionBox import SelectionBox
import kataja.globals as g

__author__ = 'purma'

choices_when_selection = [(g.SELECTION, 'is selection')]
choices_when_not_selection = [(g.FOREST, 'is forest'), (g.DOCUMENT, 'is document')]


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
        Panel.__init__(self, name, default_position, parent, folded, foldable=False)
        widget = self.widget()
        self.scope_selector = SelectionBox(parent=widget, data=choices_when_not_selection,
                                           action='set_editing_scope')
        self.was_selection = False
        self.scope_selector.setMaximumWidth(128)
        self.push_to_title(self.scope_selector)
        self.reset_button = PanelButton(parent=widget, text='reset', action='reset_settings')
        self.reset_button.setMinimumHeight(14)
        self.reset_button.setMaximumHeight(14)
        self.push_to_title(self.reset_button)
        widget.setAutoFillBackground(True)
        self.finish_init()

    def prepare_selections(self):
        selection = ctrl.ui.active_scope == g.SELECTION
        if (selection and self.was_selection) or (not selection) and (not self.was_selection):
            return
        if selection:
            self.scope_selector.rebuild_choices(choices_when_selection)
            self.scope_selector.setEnabled(False)
            self.was_selection = True
        else:
            self.scope_selector.rebuild_choices(choices_when_not_selection)
            self.scope_selector.setEnabled(True)
            self.was_selection = False
