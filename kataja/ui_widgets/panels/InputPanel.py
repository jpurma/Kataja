from PyQt5 import QtCore
from kataja.singletons import ctrl
from kataja.ui_widgets.KatajaTextarea import KatajaTextarea
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.PushButtonBase import PushButtonBase

__author__ = 'purma'


class InputPanel(Panel):
    """ Enter the sentence or structure to parse """

    def __init__(self, name, default_position='bottom', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_manager: pass a dictionary where buttons from this panel will be added
        """
        Panel.__init__(self, name, default_position, parent, folded)
        ctrl.main.forest_changed.connect(self.prepare_input)
        layout = self.vlayout

        tt = 'Sentence to parse'
        self.input_text = KatajaTextarea(self, tooltip=tt).to_layout(layout)

        self.derive_button = PushButtonBase(parent=self, text='Derive again',
                                            action='derive_from_input').to_layout(layout)
        self.widget().setAutoFillBackground(True)
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
