from kataja.singletons import ctrl
from kataja.ui_widgets.KatajaTextarea import KatajaTextarea
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.buttons.EyeButton import EyeButton

__author__ = 'purma'


class SemanticsPanel(Panel):
    """ Switch between trees or derivation steps """

    def __init__(self, name, default_position='right', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be
        automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        Panel.__init__(self, name, default_position, parent, folded, foldable=False)
        widget = self.widget()
        self.semantics_visible = EyeButton(action='toggle_semantics_view', width=26, height=20)
        self.push_to_title(self.semantics_visible)
        layout = self.vlayout
        tt = 'Optional semantic data. Use depends on plugin.'
        self.semantics_text = KatajaTextarea(widget, tooltip=tt).to_layout(layout, with_label='Semantics')
        self.semantics_text.setMaximumHeight(36)

        inner = self.widget()
        inner.setAutoFillBackground(True)
        self.finish_init()

    def prepare_lexicon(self):
        if ctrl.main.signalsBlocked():
            return
        if not ctrl.syntax:
            return
        semantics = ctrl.syntax.get_editable_semantics()
        self.semantics_text.setText(semantics)
        ctrl.graph_view.activateWindow()
