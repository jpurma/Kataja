from PyQt5 import QtCore
from kataja.singletons import ctrl
from kataja.ui_widgets.KatajaTextarea import KatajaTextarea
from kataja.ui_widgets.Panel import Panel

__author__ = 'purma'


class ParseTreePanel(Panel):
    """ Display parses and their derivation states as a tree """

    def __init__(self, name, default_position='bottom', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_manager: pass a dictionary where buttons from this panel will be added
        """
        Panel.__init__(self, name, default_position, parent, folded)
        ctrl.main.forest_changed.connect(self.prepare_tree)
        layout = self.vlayout
        widget = self.widget()
        self.preferred_size = QtCore.QSize(240, 200)
        self.preferred_floating_size = QtCore.QSize(320, 320)
        tt = 'Parse progress tree'
        self.lextext = KatajaTextarea(widget, tooltip=tt).to_layout(layout)
        widget.setAutoFillBackground(True)
        self.prepare_lexicon()
        self.finish_init()
        ctrl.graph_view.activateWindow()
        ctrl.graph_view.setFocus()

    def prepare_tree(self):
        if ctrl.main.signalsBlocked():
            return
        if not ctrl.syntax:
            return
        #ctrl.forest.derivation_branches
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
