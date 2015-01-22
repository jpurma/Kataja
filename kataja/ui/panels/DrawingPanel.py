from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QRect, QSize
from PyQt5.QtGui import QIcon, QColor, QPixmap, QStandardItem

from kataja.Edge import SHAPE_PRESETS, Edge
from kataja.singletons import ctrl, qt_prefs
import kataja.globals as g
from kataja.ui.panels.UIPanel import UIPanel
from kataja.utils import time_me
from kataja.ui.DrawnIconEngine import DrawnIconEngine
from kataja.ui.ColorSwatchIconEngine import ColorSwatchIconEngine
from kataja.ui.TwoColorButton import TwoColorButton


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
        pen = self.panel.current_color
        if not isinstance(pen, QColor):
            pen = ctrl.cm.get(pen)

        d = {'color':pen}
        return d

class LineColorIcon(QIcon):
    def __init__(self, color_id):
        QIcon.__init__(self, ColorSwatchIconEngine(color_id))



class TableModelComboBox(QtWidgets.QComboBox):

    def find_item(self, data):
        """ Return the item corresponding to this data
        :param data: data to match
        :return: None if not found, item itself if it is found
        """
        model = self.model()
        for i in range(0, model.columnCount()):
            for j in range(0, model.rowCount()):
                item = model.item(j, i)
                if item and item.data() == data:
                    return item
        return None

    def add_and_select_ambiguous_marker(self):
        item = self.find_item(g.AMBIGUOUS_VALUES)
        if item:
            self.setCurrentIndex(item.row())
            self.setModelColumn(item.column())
        else:
            row = []
            for i in range(0, self.model().rowCount()):
                item = QStandardItem('---')
                item.setData(g.AMBIGUOUS_VALUES)
                item.setSizeHint(QSize(22, 20))
                row.append(item)
            self.model().insertRow(0, row)
            self.setCurrentIndex(0)
            self.setModelColumn(0)

    def remove_ambiguous_marker(self):
        item = self.find_item(g.AMBIGUOUS_VALUES)
        if item:
            self.model().removeRow(item.row())


    def select_data(self, data):
        item = self.find_item(data)
        assert(item)
        self.setCurrentIndex(item.row())
        self.setModelColumn(item.column())


class ColorSelector(TableModelComboBox):

    def __init__(self, parent):
        QtWidgets.QComboBox.__init__(self, parent)
        self.setIconSize(QSize(16, 16))
        #self.color_selector.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        model = self.model()
        model.setRowCount(8)
        model.setColumnCount(4)
        items = []
        for c in ctrl.cm.color_keys:
            item = QStandardItem(LineColorIcon(c), '')
            item.setData(c)
            item.setSizeHint(QSize(22, 20))
            items.append(item)
        new_view = QtWidgets.QTableView()
        add_icon = QIcon()
        add_icon.fromTheme("list-add")
        add_item = QStandardItem('+')
        add_item.setTextAlignment(QtCore.Qt.AlignCenter)
        add_item.setSizeHint(QSize(22,20))
        table = [items[0:3], items[5:13], items[13:21], [add_item]]
        for c, column in enumerate(table):
            for r, item in enumerate(column):
                model.setItem(r, c, item)
        new_view.horizontalHeader().hide()
        new_view.verticalHeader().hide()
        new_view.setCornerButtonEnabled(False)
        new_view.setModel(model)
        new_view.resizeColumnsToContents()
        cw = new_view.columnWidth(0)
        new_view.setMinimumWidth(model.columnCount() * cw)
        self.setView(new_view)


class ShapeSelector(TableModelComboBox):

    def __init__(self, parent):
        QtWidgets.QComboBox.__init__(self, parent)
        self.setIconSize(QSize(64, 16))
        #self.shape_selector.setView(view)
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
        # new_view.horizontalHeader().hide()
        # new_view.verticalHeader().hide()
        # new_view.setCornerButtonEnabled(False)
        # new_view.setModel(model)
        # new_view.resizeColumnsToContents()
        # cw = new_view.columnWidth(0)
        # new_view.setMinimumWidth(model.columnCount() * cw)
        # self.setView(new_view)



class DrawingPanel(UIPanel):
    """ Panel for editing how edges and nodes are drawn. """

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
        self.current_color = ctrl.cm.drawing()
        ui_manager.ui_buttons['line_type_target'] = self.scope_selector
        # Other items may be temporarily added, they are defined as class.variables
        ui_manager.connect_element_to_action(self.scope_selector, 'edge_shape_scope')
        layout.addWidget(self.scope_selector)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)

        self.shape_selector = ShapeSelector(self)
        ui_manager.ui_buttons['line_type'] = self.shape_selector
        ui_manager.connect_element_to_action(self.shape_selector, 'change_edge_shape')
        hlayout.addWidget(self.shape_selector)

        self.color_selector = ColorSelector(self)
        ui_manager.ui_buttons['line_color'] = self.color_selector
        ui_manager.connect_element_to_action(self.color_selector, 'change_edge_color')
        hlayout.addWidget(self.color_selector)

        self.edge_options = QtWidgets.QPushButton('more...', self)
        self.edge_options.setCheckable(True)
        self.edge_options.setMinimumSize(QSize(40, 24))
        self.edge_options.setMaximumSize(QSize(40, 24))
        #self.edge_options.setMinimumWidth(40)
        #self.edge_options.setMaximumWidth(40)
        ui_manager.ui_buttons['line_options'] = self.edge_options
        ui_manager.connect_element_to_action(self.edge_options, 'toggle_line_options')
        #self.edge_options.setFlat(True)
        hlayout.addWidget(self.edge_options)
        layout.addLayout(hlayout)




        inner.setLayout(layout)
        self.setWidget(inner)
        self.finish_init()




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

    def update_color(self, color):
        self.current_color = color
        self.color_selector.select_data(color)


    def update_panel(self):
        """ Panel update should be necessary when changing ctrl.selection or after the tree has otherwise changed.
        :return:
        """
        self.update_scope_selector_options()
        self.update_scope_selector()
        self.update_fields()

    #@time_me
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
        """ Update different fields in the panel to show the correct values based on selection or current scope.
        There may be that this makes fields to remove or add new values to selectors or do other hard manipulation
        to fields.
        """

        ### First find what are the properties of the selected edges.
        ### If they are conflicting, e.g. there are two different colors in selected edges,
        ### then they cannot be shown in the color selector. They can still be overridden with new selection.
        if self.scope == g.SELECTION:
            edge_shape = None
            edge_color = None
            ambiguous_edge = False
            ambiguous_color = False
            for edge in ctrl.get_all_selected():
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
                    self.color_selector.add_and_select_ambiguous_marker()
                else:
                    self.color_selector.remove_ambiguous_marker()
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






