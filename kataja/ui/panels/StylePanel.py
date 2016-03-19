from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.Node import Node
from kataja.Edge import Edge
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
        self.cached_node_color = 'content1'
        self.cached_edge_color = 'content1'
        self.cached_font_id = 'main_font'
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
        vline = QtWidgets.QFrame()
        vline.setFrameShape(QtWidgets.QFrame.VLine)
        hlayout.addWidget(vline)
        self.style_reset = mini_button(ui_manager, self.style_widgets, hlayout,
                                       text='reset',
                                       action='reset_style_in_scope')

        hlayout = box_row(sw_layout)

        self.font_selector = font_selector(ui_manager, self.style_widgets, hlayout,
                                           action='select_font',
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

    def receive_font_from_selector(self, font):
        font_key = self.cached_font_id
        print('received font from selector, font_id: ', font_key, self.cached_font_id)
        print(self.font_selector.currentData(), self.font_selector.currentIndex())
        ctrl.ui.create_or_set_font(font_key, font)
        ctrl.main.trigger_action('select_font')

    def update_font_selector(self, font_id):
        print('update font selector called w. font_id ', font_id)
        self.cached_font_id = font_id
        if not self.font_selector.find_item(font_id):
            self.font_selector.add_font(font_id, qt_prefs.fonts[font_id])
            self.font_selector.select_data(font_id)

    def receive_color_from_color_dialog(self, role, color):
        """ Replace color in palette with new color
        :param role: 'node' or 'edge'
        :param color:
        :return:
        """
        if role == 'node':
            color_key = self.cached_node_color
            ctrl.cm.d[color_key] = color
            ctrl.main.trigger_but_suppress_undo('change_node_color')
        else:
            color_key = self.cached_edge_color
            ctrl.cm.d[color_key] = color
            ctrl.main.trigger_but_suppress_undo('change_edge_color')

    def update_node_color_selector(self, color_key):
        s = self.node_color_selector
        self.cached_node_color = color_key
        # launch a color dialog if color_id is unknown or if clicking
        # already selected color
        s.select_data(color_key)
        s.update()

    def update_edge_color_selector(self, color_key):
        s = self.edge_color_selector
        self.cached_edge_color = color_key
        s.select_data(color_key)
        s.update()
        self.shape_selector.update()

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
            no_node = True
            no_edge = True
            for item in ctrl.selected:
                if no_node and isinstance(item, Node):
                    no_node = False
                    self.node_color_selector.setEnabled(True)
                    self.cached_node_color = item.get_color_id()
                    set_value(self.node_color_selector, self.cached_node_color)
                    self.font_selector.setEnabled(True)
                    self.cached_font_id = item.get_font_id()
                    set_value(self.font_selector, self.cached_font_id)
                elif no_edge and isinstance(item, Edge):
                    no_edge = False
                    self.edge_color_selector.setEnabled(True)
                    self.cached_edge_color = item.color_id
                    set_value(self.edge_color_selector, item.color_id)
                    self.shape_selector.setEnabled(True)
                    set_value(self.shape_selector, item.shape_name)
                elif not (no_edge or no_node):
                    break
            if no_edge:
                self.edge_color_selector.setEnabled(False)
                self.shape_selector.setEnabled(False)
            if no_node:
                self.node_color_selector.setEnabled(False)
                self.font_selector.setEnabled(False)
        elif ctrl.forest:
            ns = ctrl.fs.node_info
            es = ctrl.fs.edge_info
            node_type = ctrl.ui.active_node_type
            edge_type = ctrl.ui.active_edge_type
            node_color = ns(node_type, 'color')
            node_font = ns(node_type, 'font')
            edge_color = es(edge_type, 'color')
            edge_shape = es(edge_type, 'shape_name')
            # Color selector - show
            self.node_color_selector.setEnabled(True)
            set_value(self.node_color_selector, node_color)
            self.font_selector.setEnabled(True)
            set_value(self.font_selector, node_font)
            self.edge_color_selector.setEnabled(True)
            set_value(self.edge_color_selector, edge_color)
            self.shape_selector.setEnabled(True)
            set_value(self.shape_selector, edge_shape)
            # self.font_selector.setFont(qt_prefs.font(node_font))
            self.cached_node_color = node_color
            self.cached_edge_color = edge_color
            self.cached_font_id = node_font

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
