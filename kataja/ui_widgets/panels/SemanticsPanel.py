from PyQt5 import QtWidgets, QtCore

from kataja.singletons import qt_prefs, ctrl
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
        self.semantics_visible = EyeButton(action='toggle_semantics_view', width=26, height=20)
        self.push_to_title(self.semantics_visible)
        inner = QtWidgets.QWidget()
        inner.setMaximumHeight(40)
        inner.setMinimumWidth(160)
        inner.setMaximumWidth(220)
        hlayout = QtWidgets.QHBoxLayout()
        #    .to_layout(hlayout, with_label='Show semantics', label_first=False)
        inner.setLayout(hlayout)
        self.setWidget(inner)
        self.widget().setAutoFillBackground(True)
        self.finish_init()

