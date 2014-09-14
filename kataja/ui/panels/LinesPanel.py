from PyQt5 import QtWidgets

from kataja.Edge import SHAPE_PRESETS, Edge
from kataja.singletons import ctrl
import kataja.globals as g
from kataja.ui.panels.UIPanel import UIPanel


__author__ = 'purma'


class LinesPanel(UIPanel):
    """ Panel for editing how edges/relations are drawn. """
    current_selection = ('Current selection', g.SELECTION)
    ambiguous_values = ('---', g.AMBIGUOUS_VALUES)

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
        # Other items may be temporarily added, they are defined as class.variables
        items = [('Constituent relations', g.CONSTITUENT_EDGE),
                 ('Feature relations', g.FEATURE_EDGE),
                 ('Attribute relations', g.ATTRIBUTE_EDGE),
                 ('Gloss relations', g.GLOSS_EDGE)]
        for text, data in items:
            self.target_selector.addItem(text, data)
        ui_manager.connect_selector_to_action(self.target_selector, 'edge_shape_scope')
        layout.addWidget(self.target_selector)
        self.target_selector.setCurrentIndex(0)

        self.shape_selector = QtWidgets.QComboBox(self)
        ui_manager.ui_buttons['line_type'] = self.shape_selector
        items = [(lt, lt) for lt in SHAPE_PRESETS.keys()]
        for text, data in items:
            self.shape_selector.addItem(text, data)
        ui_manager.connect_selector_to_action(self.shape_selector, 'change_edge_shape')
        layout.addWidget(self.shape_selector)
        inner.setLayout(layout)
        self.setWidget(inner)
        self.finish_init()


    @staticmethod
    def find_list_item(data, selector):
        """ Helper method to check the index of data item in list
        :param data: data to match
        :param selector: QComboBox instance
        :return: -1 if not found, index if found
        """
        for i in range(0, selector.count()):
            if selector.itemData(i) == data:
                return i
        return -1


    @staticmethod
    def remove_list_item(data, selector):
        """ Helper method to remove items from combo boxes
        :param data: list item's data has to match this
        :param selector: QComboBox instance
        """
        found = False
        for i in range(0, selector.count()):
            if selector.itemData(i) == data:
                found = True
                break
        if found:
            selector.removeItem(i)

    def change_scope(self, scope, user_action=False):
        """ Change which types of edges are affected by other settings in this panel

        :param scope: int, global enum for constituent edges, feature edges etc.
        :param user_action: if True, this was directly invoked by user changing the value with ComboBox.
                            if False, change of scope is side-effect of other activities and scope needs to be updated.
        """
        self.scope = scope
        if not user_action:
            if scope == g.SELECTION:
                found = False
                for i in range(0, self.target_selector.count()):
                    if self.target_selector.itemData(i) == g.SELECTION:
                        self.target_selector.setCurrentIndex(i)
                        found = True
                        break
                if not found:
                    self.target_selector.insertItem(0, LinesPanel.current_selection[0], LinesPanel.current_selection[1])
                    self.target_selector.setCurrentIndex(0)
            else:
                for i in range(0, self.target_selector.count()):
                    if self.target_selector.itemData(i) == scope:
                        self.target_selector.setCurrentIndex(i)
                        break
                self.remove_list_item(g.SELECTION, self.target_selector)
        self.update_fields()

    def update_fields(self):
        """ Update different fields in the panel to show the correct values based on selection or scope.
        There may be that this makes fields to remove or add new values to selectors or do other hard manipulation
        to fields.
        """
        # Shape selector - show shape of selected edges, or '---' if they contain more than 1 shape.
        if self.scope == g.SELECTION:
            edge_shape = None
            for edge in ctrl.get_all_selected():
                if isinstance(edge, Edge):
                    if not edge_shape:
                        edge_shape = edge.shape_name()
                    elif edge.shape_name() != edge_shape:
                        edge_shape = '---'
                        break
            if edge_shape == '---' or edge_shape is None:
                i = self.find_list_item(g.AMBIGUOUS_VALUES, self.shape_selector)
                if i == -1:
                    self.shape_selector.insertItem(0, LinesPanel.ambiguous_values[0], LinesPanel.ambiguous_values[1])
                    self.shape_selector.setCurrentIndex(0)
                else:
                    self.shape_selector.setCurrentIndex(i)
            else:
                i = self.find_list_item(edge_shape, self.shape_selector)
                assert(i > -1)
                self.shape_selector.setCurrentIndex(i)
        else:
            edge_shape = ctrl.forest.settings.edge_settings(self.scope, 'shape_name')
            i = self.find_list_item(edge_shape, self.shape_selector)
            assert(i > -1)
            self.shape_selector.setCurrentIndex(i)


    # def change_main_line_type(self, index):
    #     """
    #
    #     :param index:
    #     """
    #     ctrl.main.change_node_edge_shape(list(SHAPE_PRESETS.keys())[index])