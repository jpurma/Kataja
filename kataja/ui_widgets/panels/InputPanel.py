from PyQt6 import QtCore

from kataja.singletons import ctrl
from kataja.ui_widgets.KatajaTextarea import KatajaTextarea
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.PushButtonBase import PushButtonBase

__author__ = 'purma'


class InputPanel(Panel):
    """ Enter the sentence or structure to parse """

    def __init__(self, name, default_position='bottom', parent=None, folded=False):
        Panel.__init__(self, name, default_position, parent, folded)
        ctrl.main.forest_changed.connect(self.prepare_input)
        layout = self.vlayout
        widget = self.widget()

        tt = 'Sentence to parse'
        self.input_text = KatajaTextarea(widget, tooltip=tt).to_layout(layout)
        self.preferred_size = QtCore.QSize(220, 96)
        self.preferred_floating_size = QtCore.QSize(220, 200)

        self.derive_button = PushButtonBase(parent=widget, text='Derive again',
                                            action='derive_from_input').to_layout(layout)
        widget.setAutoFillBackground(True)
        self.finish_init()
        self.prepare_input()
        ctrl.graph_view.activateWindow()
        ctrl.graph_view.setFocus()

    def prepare_input(self):
        if ctrl.main.signalsBlocked():
            return
        if not ctrl.syntax:
            return
        sentence = ctrl.syntax.get_editable_sentence()
        self.input_text.setText(sentence)
        ctrl.graph_view.activateWindow()
