from PyQt5 import QtWidgets
from PyQt5.QtCore import QRect, QSize
from PyQt5.QtGui import QIcon, QColor

from kataja.Edge import SHAPE_PRESETS, Edge
from kataja.singletons import ctrl
import kataja.globals as g
from kataja.ui.panels.UIPanel import UIPanel
from kataja.utils import time_me
from kataja.ui.DrawnIconEngine import DrawnIconEngine


__author__ = 'purma'

scope_display_order = [g.SELECTION, g.CONSTITUENT_EDGE, g.FEATURE_EDGE, g.GLOSS_EDGE, g.ARROW, g.PROPERTY_EDGE, g.ATTRIBUTE_EDGE, g.ABSTRACT_EDGE]

scope_display_items = {
    g.SELECTION: 'Current selection',
    g.CONSTITUENT_EDGE: 'Constituent relations',
    g.FEATURE_EDGE: 'Feature relations',
    g.GLOSS_EDGE: 'Gloss relations',
    g.ARROW: 'Arrows',
    g.PROPERTY_EDGE: 'Property relations',
    g.ATTRIBUTE_EDGE: 'Attribute relatios',
    g.ABSTRACT_EDGE: 'Unspecified relations'
}

line_icons = {

}


class LineStyleIcon(QIcon):
    def __init__(self, shape_key, panel):
        self.shape_key = shape_key
        self.engine = DrawnIconEngine(SHAPE_PRESETS[shape_key]['icon'], owner=self)
        QIcon.__init__(self, self.engine)
        self.panel = panel
        #pixmap = QPixmap(60, 20)
        #pixmap.fill(ctrl.cm.ui())
        #self.addPixmap(pixmap)


    def paint_settings(self):
        s = SHAPE_PRESETS[self.shape_key]
        pen = self.panel.active_line_pen
        if not isinstance(pen, QColor):
            pen = ctrl.cm.get(pen)

        d = {'color':pen}
        return d


    def pen(self):
        c = self.panel.active_line_pen
        if not isinstance(c, QColor):
            return ctrl.cm.get(c)
        else:
            return c


class LinesPanel(UIPanel):
    """ Panel for editing how edges/relations are drawn. """

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
        self.scope = g.CONSTITUENT_EDGE
        self._old_scope = g.CONSTITUENT_EDGE
        self.scope_selector = QtWidgets.QComboBox(self)
        self.scope_selector.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._visible_scopes = []
        self.active_line_pen = ctrl.cm.drawing()
        ui_manager.ui_buttons['line_type_target'] = self.scope_selector
        # Other items may be temporarily added, they are defined as class.variables
        ui_manager.connect_selector_to_action(self.scope_selector, 'edge_shape_scope')
        layout.addWidget(self.scope_selector)

        self.shape_selector = QtWidgets.QComboBox(self)
        self.shape_selector.setIconSize(QSize(64, 16))
        self.shape_selector.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        #self.shape_selector.setView(view)
        ui_manager.ui_buttons['line_type'] = self.shape_selector
        items = [('', LineStyleIcon(lt, self), lt) for lt in SHAPE_PRESETS.keys()]
        for text, icon, data in items:
            self.shape_selector.addItem(icon, text, data)
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
            return i
        else:
            return -1


    def selected_objects_changed(self):
        """ Called after ctrl.selection has changed. Prepare panel to use selection as scope
        :return:
        """
        selection = ctrl.get_all_selected()
        found = False
        for item in selection:
            if isinstance(item, Edge):
                found = True
                break
        if found:
            if self.scope != g.SELECTION:
                self._old_scope = self.scope
            self.scope = g.SELECTION
        elif self.scope == g.SELECTION:
            self.scope = self._old_scope


    def change_scope(self, value):
        """ Change the scope of other manipulations in this panel.
        Could change value directly, but just in case.
        :param value: new scope
        :return: None
        """
        self.scope = value

    def update_panel(self):
        """ Panel update should be necessary when changing ctrl.selection or after the tree has otherwise changed.
        :return:
        """
        self.update_scope_selector_options()
        self.update_scope_selector()
        self.update_fields()

    @time_me
    def update_scope_selector_options(self):
        """ Redraw scope selector, show only scopes that are used in this forest """
        used_scopes = {self.scope}
        for edge in ctrl.main.forest.edges.values():
            used_scopes.add(edge.edge_type)
        scope_list = [x for x in scope_display_order if x in used_scopes]
        self.scope_selector.clear()
        for item in scope_list:
            self.scope_selector.addItem(scope_display_items[item], item)


    def update_scope_selector(self):
        """ Visual update for scope selector value """
        i = self.find_list_item(self.scope, self.scope_selector)
        self.scope_selector.setCurrentIndex(i)

    def update_fields(self):
        """ Update different fields in the panel to show the correct values based on selection or scope.
        There may be that this makes fields to remove or add new values to selectors or do other hard manipulation
        to fields.
        """
        def add_and_select_ambiguous_marker():
            i = self.find_list_item(g.AMBIGUOUS_VALUES, self.shape_selector)
            if i == -1:
                self.shape_selector.insertItem(0, '---', g.AMBIGUOUS_VALUES)
                self.shape_selector.setCurrentIndex(0)
            else:
                self.shape_selector.setCurrentIndex(i)

        def remove_ambiguous_marker():
            i = self.find_list_item(g.AMBIGUOUS_VALUES, self.shape_selector)
            if i > -1:
                self.shape_selector.removeItem(i)


        # Shape selector - show shape of selected edges, or '---' if they contain more than 1 shape.
        if self.scope == g.SELECTION:
            edge_shape = None
            ambiguous = False
            for edge in ctrl.get_all_selected():
                if isinstance(edge, Edge):
                    if not edge_shape:
                        edge_shape = edge.shape_name()
                    elif edge.shape_name() != edge_shape:
                        ambiguous = True
                        break
            if ambiguous:
                add_and_select_ambiguous_marker()
            else:
                i = self.find_list_item(edge_shape, self.shape_selector)
                self.shape_selector.setCurrentIndex(i)
                assert(i > -1)
                remove_ambiguous_marker()
                self.active_line_pen = edge.color()

        else:
            edge_shape = ctrl.forest.settings.edge_settings(self.scope, 'shape_name')
            self.active_line_pen = ctrl.forest.settings.edge_settings(self.scope, 'color')
            i = self.find_list_item(edge_shape, self.shape_selector)
            assert(i > -1)
            self.shape_selector.setCurrentIndex(i)
            remove_ambiguous_marker()
