from PyQt5 import QtWidgets
from kataja.singletons import ctrl, qt_prefs
from kataja.globals import CONSOLE_FONT
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.PushButtonBase import PushButtonBase

__author__ = 'purma'

stylesheet = 'QPlainTextEdit, QLineEdit {font-family: "%s"; font-size: %spx;}'


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
        layout = self.vlayout
        f = qt_prefs.get_font(CONSOLE_FONT)
        self.lextext = QtWidgets.QPlainTextEdit()
        self.setStyleSheet(stylesheet % (f.family(), f.pointSize()))
        self.watchlist = ['forest_changed', 'ui_font_changed']
        layout.addWidget(self.lextext)
        self.sentence_text = QtWidgets.QLineEdit()
        layout.addWidget(self.sentence_text)
        self.semantics_text = QtWidgets.QLineEdit()
        layout.addWidget(self.semantics_text)
        #self.info = QtWidgets.QLabel('info text here')
        self.derive_button = PushButtonBase(parent=self, text='Derive again',
                                            action='derive_from_lexicon').to_layout(layout)
        #layout.addWidget(self.info)
        self.widget().setAutoFillBackground(True)
        self.prepare_lexicon()
        self.finish_init()
        ctrl.graph_view.activateWindow()
        ctrl.graph_view.setFocus()

    def prepare_lexicon(self):
        if not ctrl.forest:
            return
        if not ctrl.syntax:
            return
        text = ctrl.syntax.get_editable_lexicon()
        if text:
            self.lextext.setPlainText(text)
        else:
            self.lextext.clear()
        sentence = ctrl.syntax.get_editable_sentence()
        semantics = ctrl.syntax.get_editable_semantics()
        self.sentence_text.setText(sentence)
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

    def watch_alerted(self, obj, signal, field_name, value):
        """ Receives alerts from signals that this object has chosen to listen. These signals
         are declared in 'self.watchlist'.

         This method will try to sort out the received signals and act accordingly.

        :param obj: the object causing the alarm
        :param signal: identifier for type of the alarm
        :param field_name: name of the field of the object causing the alarm
        :param value: value given to the field
        :return:
        """
        if signal == 'forest_changed':
            print('LexPanel got forest_changed -signal')
            self.prepare_lexicon()
        if signal == 'ui_font_changed':
            f = qt_prefs.get_font(CONSOLE_FONT)
            self.setStyleSheet(stylesheet % (f.family(), f.pointSize()))

