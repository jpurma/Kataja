from PyQt5 import QtWidgets, QtCore

from kataja.singletons import qt_prefs, ctrl
from kataja.ui.TwoColorButton import TwoColorButton
from kataja.ui.panels.UIPanel import UIPanel
import kataja.globals as g
from collections import OrderedDict
from kataja.ui.OverlayButton import OverlayButton

__author__ = 'purma'

nodes_table = OrderedDict([(g.ABSTRACT_NODE, {'name': 'Abstract Node', 'show':False}),
                           (g.CONSTITUENT_NODE, {'name': 'Constituent', 'show': True}),
                           (g.FEATURE_NODE, {'name': 'Feature', 'show': True}),
                           (g.GLOSS_NODE, {'name': 'Gloss', 'show': True}),
                           (g.COMMENT_NODE, {'name': 'Comment', 'show': True}),
                           (g.ATTRIBUTE_NODE, {'name': 'Attribute', 'show': False}),
                           (g.PROPERTY_NODE, {'name': 'Property', 'show': False})])


class NodesPanel(UIPanel):
    """ Switch between trees or derivation steps """

    def __init__(self, name, key, default_position='bottom', parent=None, ui_manager=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_manager: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        inner = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        if ctrl.forest:
            print(ctrl.fs.node_settings())
        for key, item in nodes_table.items():
            if not item['show']:
                continue
            hlayout = QtWidgets.QHBoxLayout()
            add_button = OverlayButton(qt_prefs.add_icon, None, 'panel', text='Add '+item['name'], parent=self, size=24)
            add_button.setFixedSize(26, 26)

            hlayout.addWidget(add_button)
            label = QtWidgets.QLabel(item['name'])
            hlayout.addWidget(label)
            conf_button = OverlayButton(qt_prefs.settings_icon, None, 'panel', text='Modify %s behaviour' % item['name'], parent=self, size=16)
            conf_button.setFixedSize(26, 26)
            hlayout.addWidget(conf_button, 1, QtCore.Qt.AlignRight)
            layout.addLayout(hlayout)

        inner.setLayout(layout)
        self.setWidget(inner)
        self.widget().setAutoFillBackground(True)
        self.finish_init()

    def update_panel(self):
        """ Panel update should be necessary when changing ctrl.selection or after the tree has otherwise changed.
        :return:
        """
        print(ctrl.fs.node_settings())

