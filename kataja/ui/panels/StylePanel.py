from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.Edge import Edge
from kataja.nodes.Node import Node
from kataja.singletons import ctrl, qt_prefs, prefs
from kataja.ui.panels.UIPanel import UIPanel
from kataja.ui.panels.field_utils import find_list_item, set_value, box_row, font_selector, \
    color_selector, icon_button, shape_selector, text_button, selector, mini_button

__author__ = 'purma'


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
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        layout = QtWidgets.QVBoxLayout()
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

        hlayout = box_row(layout)
        styles_data = [('fancy', 'fancy'), ('basic', 'basic')]
        self.overall_style_box = selector(ui_manager, self, hlayout,
                                          data=styles_data,
                                          action='change_master_style')
        self.custom_overall_style = text_button(ui_manager, hlayout,
                                                text='customize',
                                                action='customize_master_style',
                                                checkable=True)
        self.ostyle = 'fancy'

        self.style_widgets = QtWidgets.QWidget(self)
        sw_layout = QtWidgets.QVBoxLayout()
        sw_layout.setContentsMargins(0, 0, 0, 0)
        hlayout = box_row(sw_layout)
        self.scope_selector = selector(ui_manager, self.style_widgets, hlayout,
                                       data=[],
                                       action='style_scope',
                                       label='Style for')
        self.style_reset = mini_button(ui_manager, self.style_widgets, hlayout,
                                       text='reset',
                                       action='reset_style_in_scope')

        hlayout = box_row(sw_layout)

        self.font_selector = font_selector(ui_manager, self.style_widgets, hlayout,
                                           action='font_selector',
                                           label='Text style')

        self.node_color_selector = color_selector(ui_manager, self.style_widgets, hlayout,
                                                  action='change_node_color')

        self.open_font_dialog = icon_button(ui_manager, self.style_widgets, hlayout,
                                            icon=qt_prefs.font_icon,
                                            text='Add custom font',
                                            action='start_font_dialog',
                                            size=20)

        hlayout = box_row(sw_layout)
        self.shape_selector = shape_selector(ui_manager, self.style_widgets, hlayout,
                                             action='change_edge_shape',
                                             label='Edge style')

        self.edge_color_selector = color_selector(ui_manager, self.style_widgets, hlayout,
                                                  action='change_edge_color')

        self.edge_options = icon_button(ui_manager, self.style_widgets, hlayout,
                                        icon=qt_prefs.settings_icon,
                                        text='More line options',
                                        action='toggle_panel_%s' % g.LINE_OPTIONS,
                                        checkable=True)
        self.style_widgets.setLayout(sw_layout)
        layout.addWidget(self.style_widgets)
        inner.setLayout(layout)
        self.style_widgets.hide()
        self.setWidget(inner)

        self.finish_init()

    def toggle_customization(self, value):
        if value:
            self.style_widgets.show()
        else:
            self.style_widgets.hide()


        #self.resize(self.sizeHint())
        self.setFixedSize(self.sizeHint())
        self.updateGeometry()

        #self.update()

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
        if ctrl.ui.scope_is_selection:
            i = find_list_item(g.SELECTION, self.scope_selector)
        else:
            i = find_list_item(ctrl.ui.active_node_type, self.scope_selector)
        self.scope_selector.setCurrentIndex(i)

    def update_color_for_role(self, role, color=None):
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
            if ctrl.ui.scope_is_selection:
                for node in self._nodes_in_selection:
                    node.color_id = color_id
                    node.update_label()
            # ... or update color for all nodes of this type
            else:
                ctrl.fs.set_node_info(ctrl.ui.active_node_type, 'color', color_id)
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
            if ctrl.ui.scope_is_selection:
                for edge in self._edges_in_selection:
                    edge.color_id = color_id
                    edge.update()
            # ... or update color for all edges of this type
            else:
                ctrl.fs.set_edge_info(ctrl.ui.active_node_type, 'color', color_id)
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
        if ctrl.ui.scope_is_selection:
            for node in ctrl.selected:
                if isinstance(node, Node):
                    node.font_id = font_id
                    node.update_label()
        else:
            ctrl.fs.set_node_info(ctrl.ui.active_node_type, 'font', font_id)
            for node in ctrl.forest.nodes.values():
                node.update_label()

    def update_panel(self):
        """ Panel update should be necessary when changing ctrl.selection or
        after the trees has otherwise changed.
        :return:
        """
        self.update_fields()

    # @time_me
    def update_scope_selector_options(self):
        """ Redraw scope selector, show only scopes that are used in this
        forest """
        nd = prefs.nodes
        ss = self.scope_selector
        ss.clear()
        item = QtGui.QStandardItem('Current selection')
        item.setData(g.SELECTION, 256)
        if not (self._nodes_in_selection or self._edges_in_selection):
            item.setFlags(QtCore.Qt.ItemIsEnabled) #QtCore.Qt.NoItemFlags)
        items = [item]
        for key in prefs.node_types_order:
            name = nd[key]['name_pl']
            item = QtGui.QStandardItem(name)
            item.setData(key, 256)
            items.append(item)
        model = ss.model()
        for r, item in enumerate(items):
            model.setItem(r, item)

    def update_fields(self):
        """ Update different elements in the panel to show the correct values
        based on selection or current scope. Change of scope may remove or
        add new choices to selectors or do other hard manipulation to elements.

        First find what are the properties of the selected edges.
        If they are conflicting, e.g. there are two different colors in selected
         edges, they cannot be shown in the color selector. They can still be
         overridden with new selection.
        """
        if ctrl.ui.scope_is_selection:
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
        elif ctrl.forest:
            ns = ctrl.fs.node_info
            es = ctrl.fs.edge_info
            node_color = ns(ctrl.ui.active_node_type, 'color')
            node_font = ns(ctrl.ui.active_node_type, 'font')
            edge_color = es(ctrl.ui.active_edge_type, 'color')
            edge_shape = es(ctrl.ui.active_edge_type, 'shape_name')
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
