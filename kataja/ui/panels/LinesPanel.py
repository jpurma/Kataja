from PyQt5 import QtWidgets

from kataja.Edge import SHAPE_PRESETS
from kataja.singletons import ctrl
from kataja.ui.panels.UIPanel import UIPanel


__author__ = 'purma'


class LinesPanel(UIPanel):
    """

    """

    def __init__(self, name, key, default_position='right', parent=None, ui_manager=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        inner = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout()
        layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        #layout.setContentsMargins(4, 4, 4, 4)
        selector = QtWidgets.QComboBox(self)
        ui_manager.ui_buttons['line_type'] = selector
        selector.addItems([lt for lt in SHAPE_PRESETS.keys()])
        selector.activated.connect(self.change_main_line_type)
        layout.addWidget(selector)
        inner.setLayout(layout)
        self.setWidget(inner)
        self.finish_init()

    def change_main_line_type(self, index):
        """

        :param index:
        """
        ctrl.main.change_node_edge_shape(list(SHAPE_PRESETS.keys())[index])