from PyQt5 import QtWidgets, QtCore

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon, QColor, QStandardItem
from kataja.Edge import SHAPE_PRESETS, Edge
from kataja.singletons import ctrl, qt_prefs
import kataja.globals as g
from kataja.ui.panels.UIPanel import UIPanel
from kataja.ui.DrawnIconEngine import DrawnIconEngine
from kataja.ui.OverlayButton import PanelButton
from kataja.ui.panels.field_utils import find_list_item, add_and_select_ambiguous_marker, \
    remove_ambiguous_marker, TableModelComboBox, ColorSelector

__author__ = 'purma'

scope_display_order = [g.SELECTION, g.CONSTITUENT_EDGE, g.FEATURE_EDGE, g.GLOSS_EDGE, g.ARROW, g.PROPERTY_EDGE,
                       g.ATTRIBUTE_EDGE, g.ABSTRACT_EDGE]

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
        # pixmap = QPixmap(60, 20)
        # pixmap.fill(ctrl.cm.ui())
        # self.addPixmap(pixmap)

    def paint_settings(self):
        s = SHAPE_PRESETS[self.shape_key]
        pen = self.panel.current_color
        if not isinstance(pen, QColor):
            pen = ctrl.cm.get(pen)

        d = {'color': pen}
        return d


class ShapeSelector(TableModelComboBox):
    def __init__(self, parent):
        QtWidgets.QComboBox.__init__(self, parent)
        self.setIconSize(QSize(64, 16))
        # self.shape_selector.setView(view)
        items = []

        for lt in SHAPE_PRESETS.keys():
            item = QStandardItem(LineStyleIcon(lt, parent), '')
            item.setData(lt)
            item.setToolTip(lt)
            item.setSizeHint(QSize(64, 16))
            items.append(item)
        model = self.model()
        model.setRowCount(len(items))
        for r, item in enumerate(items):
            model.setItem(r, 0, item)
        self.view().setModel(model)


class EdgesPanel(UIPanel):
    """ Panel for editing how edges and nodes are drawn. """

    def __init__(self, name, key, default_position='right', parent=None, ui_manager=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        UIPanel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        inner = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout()
        layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        # layout.setContentsMargins(4, 4, 4, 4)
        self.scope = g.CONSTITUENT_EDGE
        self._old_scope = g.CONSTITUENT_EDGE
        self.scope_selector = QtWidgets.QComboBox(self)
        self.scope_selector.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._visible_scopes = []
        self.cached_edge_types = set()
        self.current_color = ctrl.cm.drawing()
        self.watchlist = ['edge_shape', 'edge_color', 'selection_changed', 'forest_changed']
        # Other items may be temporarily added, they are defined as class.variables
        ui_manager.connect_element_to_action(self.scope_selector, 'edge_shape_scope')
        layout.addWidget(self.scope_selector)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)

        self.shape_selector = ShapeSelector(self)
        ui_manager.connect_element_to_action(self.shape_selector, 'change_edge_shape')
        hlayout.addWidget(self.shape_selector)

        self.color_selector = ColorSelector(self)
        ui_manager.connect_element_to_action(self.color_selector, 'change_edge_color')
        hlayout.addWidget(self.color_selector)

        self.edge_options = PanelButton(qt_prefs.settings_icon, text='More line options',
                                        parent=self, size=16)
        self.edge_options.setCheckable(True)
        ui_manager.connect_element_to_action(self.edge_options, 'toggle_line_options')
        hlayout.addWidget(self.edge_options, 1, QtCore.Qt.AlignRight)
        layout.addLayout(hlayout)

        inner.setLayout(layout)
        self.setWidget(inner)
        self.finish_init()

    def are_there_edges_in_selection(self):
        """ Helper method for checking if line options should react to selection
        :return:
        """
        for item in ctrl.selected:
            if isinstance(item, Edge):
                return True
        return False

    def update_selection(self):
        """ Called after ctrl.selection has changed. Prepare panel to use selection as scope
        :return:
        """
        if self.are_there_edges_in_selection():
            # store previous scope selection so it can be returned to
            if self.scope != g.SELECTION:
                self._old_scope = self.scope
            self.scope = g.SELECTION
            self.update_scope_selector_options(selection_changed=True)
        elif self.scope == g.SELECTION:
            # return to previous selection
            self.scope = self._old_scope
            self.update_scope_selector_options(selection_changed=True)
        elif not self.cached_edge_types:
            self.update_scope_selector_options()
        i = find_list_item(self.scope, self.scope_selector)
        self.scope_selector.setCurrentIndex(i)

    def update_color(self, color):
        self.current_color = color
        self.color_selector.select_data(color)
        self.color_selector.update()
        self.shape_selector.update()

    def update_panel(self):
        """ Panel update should be necessary when changing ctrl.selection or after the tree has
        otherwise changed.
        :return:
        """
        self.update_fields()

    # @time_me
    def update_scope_selector_options(self, selection_changed=False):
        """ Redraw scope selector, show only scopes that are used in this forest """
        if (not self.cached_edge_types) or (self.cached_edge_types != ctrl.forest.edge_types) or \
                selection_changed:
            scope_list = [x for x in scope_display_order if x in ctrl.forest.edge_types]
            self.scope_selector.clear()
            if self.are_there_edges_in_selection():
                self.scope_selector.addItem(scope_display_items[g.SELECTION], g.SELECTION)
            if not scope_list:
                self.scope_selector.addItem(scope_display_items[g.CONSTITUENT_EDGE],
                                            g.CONSTITUENT_EDGE)
            for item in scope_list:
                self.scope_selector.addItem(scope_display_items[item], item)
            self.cached_edge_types = ctrl.forest.edge_types.copy()

    def update_fields(self):
        """ Update different fields in the panel to show the correct values based on selection
        or current scope. There may be that this makes fields to remove or add new values to
        selectors or do other hard manipulation to fields.

        First find what are the properties of the selected edges.
        If they are conflicting, e.g. there are two different colors in selected edges, they cannot
         be shown in the color selector. They can still be overridden with new selection.
        """

        if self.scope == g.SELECTION:
            if self.are_there_edges_in_selection():
            edge_shape = None
            edge_color = None
            ambiguous_edge = False
            ambiguous_color = False
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    if not edge_shape:
                        edge_shape = edge.shape_name
                    elif edge.shape_name != edge_shape:
                        ambiguous_edge = True
                    if not edge_color:
                        edge_color = edge.color_id
                    elif edge.color_id != edge_color:
                        ambiguous_color = True
            ### Color selector - show
            if edge_color:
                if ambiguous_color:
                    add_and_select_ambiguous_marker(self.color_selector)
                else:
                    remove_ambiguous_marker(self.color_selector)
                    self.color_selector.select_data(edge_color)
                    self.current_color = edge_color

            ### Shape selector - show shape of selected edges, or '---' if they contain more than 1 shape.
            if edge_shape:
                if ambiguous_edge:
                    self.shape_selector.add_and_select_ambiguous_marker()
                else:
                    self.shape_selector.remove_ambiguous_marker()
                    self.shape_selector.select_data(edge_shape)
            self.shape_selector.update()
        else:
            ### Color selector
            self.color_selector.remove_ambiguous_marker()
            self.current_color = ctrl.forest.settings.edge_type_settings(self.scope, 'color')
            self.color_selector.select_data(self.current_color)

            ### Edge selector
            self.shape_selector.remove_ambiguous_marker()
            edge_shape = ctrl.forest.settings.edge_type_settings(self.scope, 'shape_name')
            self.shape_selector.select_data(edge_shape)
            self.shape_selector.update()

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
        print('EdgesPanel alerted: ', obj, signal, field_name, value)
        if signal == 'selection_changed':
            self.update_selection()
            self.update_fields()
        elif signal == 'forest_changed':
            self.update_selection()
            self.update_fields()






