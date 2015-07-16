from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QIcon, QStandardItem

from kataja.nodes.Node import Node
from kataja.Edge import SHAPE_PRESETS, Edge
from kataja.singletons import ctrl, qt_prefs, prefs
import kataja.globals as g
from kataja.ui.panels.UIPanel import UIPanel
from kataja.ui.DrawnIconEngine import DrawnIconEngine
from kataja.ui.OverlayButton import PanelButton
from kataja.ui.panels.field_utils import find_list_item, TableModelComboBox, \
    ColorSelector, set_value, FontSelector

__author__ = 'purma'


class LineStyleIcon(QIcon):
    def __init__(self, shape_key, panel):
        self.shape_key = shape_key
        self.engine = DrawnIconEngine(SHAPE_PRESETS[shape_key]['icon'],
                                      owner=self)
        QIcon.__init__(self, self.engine)
        self.panel = panel
        # pixmap = QPixmap(60, 20)
        # pixmap.fill(ctrl.cm.ui())
        # self.addPixmap(pixmap)

    def paint_settings(self):
        pen = self.panel.cached_edge_color
        if not pen:
            pen = 'content1'
        d = {'color': ctrl.cm.get(pen)}
        return d


class ShapeSelector(TableModelComboBox):
    def __init__(self, parent):
        super().__init__(parent)
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


class StylePanel(UIPanel):
    """ Panel for editing how edges and nodes are drawn. """

    def __init__(self, name, key, default_position='right', parent=None,
                 ui_manager=None, folded=False):
        """
        All of the panel constructors follow the same format so that the
        construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        UIPanel.__init__(self, name, key, default_position, parent, ui_manager,
                         folded)
        inner = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout()
        layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        # layout.setContentsMargins(4, 4, 4, 4)
        self._nodes_in_selection = []
        self._edges_in_selection = []
        self.cached_node_types = set()
        self.current_color = ctrl.cm.drawing()
        self.cached_node_color = None
        self.cached_edge_color = None
        self.cached_font_id = None
        self.watchlist = ['edge_shape', 'edge_color', 'selection_changed',
                          'forest_changed', 'scope_changed']
        # Other items may be temporarily added, they are defined as
        # class.variables

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        label = QtWidgets.QLabel('Style for', self)
        hlayout.addWidget(label)
        self.scope_selector = QtWidgets.QComboBox(self)
        # self.scope_selector.setSizePolicy(QtWidgets.QSizePolicy.Fixed,
        # QtWidgets.QSizePolicy.Fixed)
        # self.scope_selector.setMinimumWidth(120)
        ui_manager.connect_element_to_action(self.scope_selector, 'style_scope')
        hlayout.addWidget(self.scope_selector, 1, QtCore.Qt.AlignLeft)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)

        self.font_selector = FontSelector(self)
        ui_manager.connect_element_to_action(self.font_selector,
                                             'font_selector')
        hlayout.addWidget(self.font_selector)

        self.open_font_dialog = PanelButton(qt_prefs.font_icon,
                                            text='Add custom font', parent=self,
                                            size=20)
        ui_manager.connect_element_to_action(self.open_font_dialog,
                                             'start_font_dialog')
        hlayout.addWidget(self.open_font_dialog, 1, QtCore.Qt.AlignLeft)

        self.node_color_selector = ColorSelector(self)
        ui_manager.connect_element_to_action(self.node_color_selector,
                                             'change_node_color')
        hlayout.addWidget(self.node_color_selector, 1, QtCore.Qt.AlignLeft)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)

        self.shape_selector = ShapeSelector(self)
        ui_manager.connect_element_to_action(self.shape_selector,
                                             'change_edge_shape')
        hlayout.addWidget(self.shape_selector, 1, QtCore.Qt.AlignLeft)

        self.edge_color_selector = ColorSelector(self)
        ui_manager.connect_element_to_action(self.edge_color_selector,
                                             'change_edge_color')
        hlayout.addWidget(self.edge_color_selector, 1, QtCore.Qt.AlignLeft)

        self.edge_options = PanelButton(qt_prefs.settings_icon,
                                        text='More line options', parent=self,
                                        size=20)
        self.edge_options.setCheckable(True)
        ui_manager.connect_element_to_action(self.edge_options,
                                             'toggle_line_options')
        hlayout.addWidget(self.edge_options, 1, QtCore.Qt.AlignRight)
        layout.addLayout(hlayout)

        inner.setLayout(layout)
        self.setWidget(inner)
        self.finish_init()

    def update_selection(self):
        """ Called after ctrl.selection has changed. Prepare panel to use
        selection as scope
        :return:
        """
        self._edges_in_selection = []
        self._nodes_in_selection = []
        self.cached_node_types = set()
        for item in ctrl.selected:
            if isinstance(item, Node):
                self._nodes_in_selection.append(item)
                self.cached_node_types.add(item.node_type)
            elif isinstance(item, Edge):
                self._edges_in_selection.append(item)
        self.update_scope_selector_options()
        i = find_list_item(ctrl.ui.scope, self.scope_selector)
        self.scope_selector.setCurrentIndex(i)

    def update_color_for_role(self, role, color=None):
        scope = ctrl.ui.scope
        if role == 'node_color':
            s = self.node_color_selector
            prev_color = self.cached_node_color
            color_id = s.currentData()
            self.cached_node_color = color_id
            # Replace color in palette with new color
            if color:
                ctrl.cm.d[color_id] = color
            # ... or launch a color dialog if color_id is unknown or if clicking
            # already selected color
            elif prev_color == color_id or (not color_id) or (
                    not ctrl.cm.get(color_id)):
                ctrl.ui.start_color_dialog(s, self, 'node_color', color_id)
                return
            else:
                ctrl.ui.update_color_dialog('node_color', color_id)

            # Update color for selected nodes
            if scope == g.SELECTION:
                for node in self._nodes_in_selection:
                    node.color_id = color_id
                    node.update_label()
            # ... or update color for all nodes of this type
            elif scope:
                ctrl.forest.settings.node_settings(scope, 'color', color_id)
                for node in ctrl.forest.nodes.values():
                    node.update_label()
            # make sure that selector has correct choice selected
            s.select_data(color_id)
            s.update()
            return color_id
        elif role == 'edge_color':
            s = self.edge_color_selector
            prev_color = self.cached_edge_color
            color_id = s.currentData()
            self.cached_edge_color = color_id
            # Replace color in palette with new color
            if color:
                ctrl.cm.d[color_id] = color
            # ...or launch a color dialog if color_id is unknown or clicking
            # already selected color
            elif prev_color == color_id or (not color_id) or (
                    not ctrl.cm.get(color_id)):
                ctrl.ui.start_color_dialog(s, self, 'edge_color', color_id)
                return
            else:
                ctrl.ui.update_color_dialog('edge_color', color_id)

            # Update color for selected edges
            if scope == g.SELECTION:
                for edge in self._edges_in_selection:
                    edge.color_id = color_id
                    edge.update()
            # ... or update color for all edges of this type
            elif scope:
                edge_type = ctrl.forest.settings.node_settings(scope, 'edge')
                ctrl.forest.settings.edge_type_settings(edge_type, 'color',
                                                        color_id)
                for edge in ctrl.forest.edges.values():
                    edge.update()
            s.select_data(color_id)
            s.update()
            self.shape_selector.update()
            return color_id

    def update_font_for_role(self, role, font_id):
        """ Make sure that new font_id is updated to all items under the scope.
        :param role: Not used, only one font dialog currently here
        :param font_id:
        :return:
        """
        self.cached_font_id = font_id
        if not self.font_selector.find_item(font_id):
            self.font_selector.add_font(font_id, qt_prefs.fonts[font_id])
        self.font_selector.select_data(font_id)
        if ctrl.ui.scope == g.SELECTION:
            for node in ctrl.selected:
                if isinstance(node, Node):
                    node.font_id = font_id
                    node.update_label()
        elif ctrl.ui.scope:
            ctrl.forest.settings.node_settings(ctrl.ui.scope, 'font', font_id)
            for node in ctrl.forest.nodes.values():
                node.update_label()

    def update_panel(self):
        """ Panel update should be necessary when changing ctrl.selection or
        after the tree has otherwise changed.
        :return:
        """
        self.update_fields()

    # @time_me
    def update_scope_selector_options(self):
        """ Redraw scope selector, show only scopes that are used in this
        forest """
        nd = prefs.nodes
        scope_list = [(key, nd[key]['name_pl']) for key in
                      prefs.node_types_order]
        self.scope_selector.clear()
        if self._nodes_in_selection or self._edges_in_selection:
            self.scope_selector.addItem('Current selection', g.SELECTION)
        for key, name in scope_list:
            self.scope_selector.addItem(name, key)

    def update_fields(self):
        """ Update different fields in the panel to show the correct values
        based on selection or current scope. Change of scope may remove or
        add new choices to selectors or do other hard manipulation to fields.

        First find what are the properties of the selected edges.
        If they are conflicting, e.g. there are two different colors in selected
         edges, they cannot be shown in the color selector. They can still be
         overridden with new selection.
        """
        scope = ctrl.ui.scope
        if scope == g.SELECTION:
            d = self.build_display_values()
            for key, item in d.items():
                value, enabled, conflict = item
                if key == 'edge_color':
                    f = self.edge_color_selector
                elif key == 'node_color':
                    f = self.node_color_selector
                elif key == 'node_font':
                    f = self.font_selector
                elif key == 'edge_shape':
                    f = self.shape_selector
                else:
                    continue
                set_value(f, value, conflict=conflict, enabled=enabled)
            # self.font_selector.setFont(qt_prefs.font(d['node_font'][0]))
            if d['node_color'][0]:
                self.cached_node_color = d['node_color'][0]
            if d['edge_color'][0]:
                self.cached_edge_color = d['edge_color'][0]
            if d['node_font'][0]:
                self.cached_font_id = d['node_font'][0]
        else:
            ns = ctrl.forest.settings.node_settings
            es = ctrl.forest.settings.edge_type_settings
            edge_scope = ns(scope, 'edge')
            node_color = ns(scope, 'color')
            node_font = ns(scope, 'font')
            edge_color = es(edge_scope, 'color')
            edge_shape = es(edge_scope, 'shape_name')
            # Color selector - show
            set_value(self.node_color_selector, node_color, False)
            set_value(self.font_selector, node_font, False)
            set_value(self.edge_color_selector, edge_color, False)
            set_value(self.shape_selector, edge_shape, False)
            # self.font_selector.setFont(qt_prefs.font(node_font))
            self.cached_node_color = node_color
            self.cached_edge_color = edge_color
            self.cached_font_id = node_font

    def build_display_values(self):
        d = {}
        if len(self._edges_in_selection) + len(self._nodes_in_selection) == 1:
            if self._edges_in_selection:
                e = self._edges_in_selection[0]
                d['edge_color'] = (e.color_id, True, False)
                d['edge_shape'] = (e.shape_name, True, False)
                d['node_color'] = ('', False, False)
                d['node_font'] = ('', False, False)
            elif self._nodes_in_selection:
                n = self._nodes_in_selection[0]
                d['edge_color'] = ('', False, False)
                d['edge_shape'] = ('', False, False)
                d['node_color'] = (n.get_color_id(), True, False)
                d['node_font'] = (n.get_font_id(), True, False)
        else:
            color_conflict = False
            shape_conflict = False
            color = None
            shape = None
            for e in self._edges_in_selection:
                if not color:
                    color = e.color_id
                elif e.color_id != color:
                    color_conflict = True
                if not shape:
                    shape = e.shape_name
                elif e.shape_name != shape:
                    shape_conflict = True
            ncolor_conflict = False
            font_conflict = False
            ncolor = None
            font = None
            for n in self._nodes_in_selection:
                if not ncolor:
                    ncolor = n.color_id
                elif n.color_id != ncolor:
                    ncolor_conflict = True
                if not font:
                    font = n.font_id
                elif n.font_id != font:
                    font_conflict = True
            d['edge_color'] = (color, bool(color), color_conflict)
            d['edge_shape'] = (shape, bool(shape), shape_conflict)
            d['node_color'] = (ncolor, bool(ncolor), ncolor_conflict)
            d['node_font'] = (font, bool(font), font_conflict)
        return d

    def watch_alerted(self, obj, signal, field_name, value):
        """ Receives alerts from signals that this object has chosen to
        listen. These signals
         are declared in 'self.watchlist'.

         This method will try to sort out the received signals and act
         accordingly.

        :param obj: the object causing the alarm
        :param signal: identifier for type of the alarm
        :param field_name: name of the field of the object causing the alarm
        :param value: value given to the field
        :return:
        """
        # print('StylePanel alerted: ', obj, signal, field_name, value)
        if signal == 'selection_changed':
            self.update_selection()
            self.update_fields()
        elif signal == 'forest_changed':
            self.update_selection()
            self.update_fields()
        elif signal == 'scope_changed':
            self.update_fields()
