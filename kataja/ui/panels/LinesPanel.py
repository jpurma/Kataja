from PyQt5 import QtWidgets

from kataja.Edge import SHAPE_PRESETS, Edge
from kataja.singletons import ctrl
import kataja.globals as g
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
        self.scope = ui_manager.scope_for_edge_changes
        self.target_selector = QtWidgets.QComboBox(self)
        ui_manager.ui_buttons['line_type_target'] = self.target_selector
        items = [('Current selection', g.SELECTION),
                 ('Constituent relations', g.CONSTITUENT_EDGE),
                 ('Feature relations', g.FEATURE_EDGE),
                 ('Attribute relations', g.ATTRIBUTE_EDGE),
                 ('Gloss relations', g.GLOSS_EDGE)]
        for text, data in items:
            self.target_selector.addItem(text, data)
        ui_manager.connect_selector_to_action(self.target_selector, 'edge_shape_scope')
        layout.addWidget(self.target_selector)
        self.target_selector.setCurrentIndex(1)

        selector = QtWidgets.QComboBox(self)
        ui_manager.ui_buttons['line_type'] = selector
        items = [(lt, lt) for lt in SHAPE_PRESETS.keys()]
        for text, data in items:
            selector.addItem(text, data)
        ui_manager.connect_selector_to_action(selector, 'change_edge_shape')
        layout.addWidget(selector)
        inner.setLayout(layout)
        self.setWidget(inner)
        self.finish_init()

    def change_scope(self, scope):
        print('Change scope called, ', scope)
        self.scope = scope
        if scope == g.SELECTION:
            for i in range(0, self.target_selector.count()):
                if self.target_selector.itemData(i) == g.SELECTION:
                    self.target_selector.setCurrentIndex(i)
        else:
            for i in range(0, self.target_selector.count()):
                if self.target_selector.itemData(i) == scope:
                    self.target_selector.setCurrentIndex(i)
        self.update_fields()

    def update_fields(self):
        if self.scope == g.SELECTION:
            edge_shape = None
            for item in ctrl.get_all_selected():
                if isinstance(item, Edge):
                    pass

    # def change_main_line_type(self, index):
    #     """
    #
    #     :param index:
    #     """
    #     ctrl.main.change_node_edge_shape(list(SHAPE_PRESETS.keys())[index])