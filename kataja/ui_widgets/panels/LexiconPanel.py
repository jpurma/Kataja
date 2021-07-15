from PyQt6 import QtCore

from kataja.singletons import ctrl
from kataja.ui_widgets.KatajaTextarea import KatajaTextarea
from kataja.ui_widgets.Panel import Panel

__author__ = 'purma'


class LexiconPanel(Panel):
    """ Browse and build the lexicon """

    def __init__(self, name, default_position='bottom', parent=None, folded=False):
        Panel.__init__(self, name, default_position, parent, folded)
        ctrl.main.forest_changed.connect(self.prepare_lexicon)
        layout = self.vlayout
        widget = self.widget()
        self.preferred_size = QtCore.QSize(240, 200)
        self.preferred_floating_size = QtCore.QSize(320, 320)
        tt = 'Editable lexicon'
        self.lextext = KatajaTextarea(widget, tooltip=tt).to_layout(layout)
        widget.setAutoFillBackground(True)
        self.prepare_lexicon()
        self.finish_init()
        ctrl.graph_view.activateWindow()
        ctrl.graph_view.setFocus()

    def initial_position(self, next_to=''):
        return Panel.initial_position(self, next_to=next_to or 'ConstituentPanel')

    def prepare_lexicon(self):
        if ctrl.main.signalsBlocked():
            return
        if not ctrl.syntax:
            return
        lexicon = ctrl.syntax.get_editable_lexicon()
        self.lextext.setText(lexicon)
        ctrl.graph_view.activateWindow()

    def showEvent(self, event):
        """ Panel may have missed signals to update its contents when it was hidden: update all
        that signals would update.
        :param event:
        :return:
        """
        self.prepare_lexicon()
        super().showEvent(event)
