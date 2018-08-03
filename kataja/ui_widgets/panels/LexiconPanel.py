from PyQt5 import QtWidgets
from kataja.singletons import ctrl, qt_prefs
from kataja.globals import CONSOLE_FONT
from kataja.ui_widgets.KatajaTextarea import KatajaTextarea
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.PushButtonBase import PushButtonBase

__author__ = 'purma'


class LexiconPanel(Panel):
    """ Browse and build the lexicon """

    def __init__(self, name, default_position='bottom', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_manager: pass a dictionary where buttons from this panel will be added
        """
        Panel.__init__(self, name, default_position, parent, folded)
        ctrl.main.forest_changed.connect(self.prepare_lexicon)
        layout = self.vlayout
        tt = 'Editable lexicon'
        self.lextext = KatajaTextarea(self, tooltip=tt).to_layout(layout, with_label='Lexicon')
        self.lextext.setMinimumHeight(200)
        tt = 'Sentence to parse'
        self.input_text = KatajaTextarea(self, tooltip=tt).to_layout(layout, with_label='Input sentence')
        self.input_text.setMaximumHeight(36)

        tt = 'Optional semantic data. Use depends on plugin.'
        self.semantics_text = KatajaTextarea(self, tooltip=tt).to_layout(layout, with_label='Semantics')
        self.semantics_text.setMaximumHeight(36)

        self.derive_button = PushButtonBase(parent=self, text='Derive again',
                                            action='derive_from_lexicon').to_layout(layout)
        self.widget().setAutoFillBackground(True)
        self.prepare_lexicon()
        self.finish_init()
        ctrl.graph_view.activateWindow()
        ctrl.graph_view.setFocus()

    def prepare_lexicon(self):
        if ctrl.main.signalsBlocked():
            return
        text = ctrl.syntax.get_editable_lexicon()
        sentence = ctrl.syntax.get_editable_sentence()
        semantics = ctrl.syntax.get_editable_semantics()
        print('preparing lexicon as: ', repr(text))
        self.lextext.setText(text)
        self.input_text.setText(sentence)
        if len(sentence) > 150:
            self.input_text.setMaximumHeight(200)
            self.input_text.setMinimumHeight(200)
        else:
            self.input_text.setMinimumHeight(48)
            self.input_text.setMaximumHeight(48)
        self.input_text.update()
        self.semantics_text.setText(semantics)
        ctrl.graph_view.activateWindow()

    def showEvent(self, event):
        """ Panel may have missed signals to update its contents when it was hidden: update all
        that signals would update.
        :param event:
        :return:
        """
        self.prepare_lexicon()
        super().showEvent(event)

