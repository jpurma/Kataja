from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs, prefs, classes
from kataja.saved.Edge import Edge
from kataja.saved.movables.Node import Node
from kataja.ui_widgets.Panel import Panel
from kataja.ui_support.panel_utils import set_value, box_row, font_selector, \
    color_selector, icon_button, shape_selector, text_button, selector, mini_button

__author__ = 'purma'


class StylePanel(Panel):
    """ Panel for editing how edges and nodes are drawn. """

    def __init__(self, name, default_position='right', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the
        construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        Panel.__init__(self, name, default_position, parent, folded)
        inner = QtWidgets.QWidget(self)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
        layout = QtWidgets.QVBoxLayout()
        self.setMaximumWidth(220)
        self.setMaximumHeight(140)
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
        ui = self.ui_manager
        hlayout = box_row(layout)

        styles_data = []
        current_style_i = 0
        for i, value in enumerate(prefs.available_styles):
            if value == ctrl.settings.get('style'):
                current_style_i = i
            styles_data.append((value, value))
        self.overall_style_box = selector(ui, self, hlayout,
                                          data=styles_data,
                                          action='change_master_style')
        self.overall_style_box.setCurrentIndex(current_style_i)
        #self.custom_overall_style = text_button(ui, hlayout,
        #                                        text='customize',
        #                                        action='customize_master_style',
        #                                        checkable=True)
        self.overall_style_box.hide()
        self.style_widgets = QtWidgets.QWidget(inner)
        sw_layout = QtWidgets.QVBoxLayout()
        sw_layout.setContentsMargins(0, 0, 0, 0)
        hlayout = box_row(sw_layout)
        self.scope_selector = selector(ui, self.style_widgets, hlayout,
                                       data=[],
                                       action='style_scope',
                                       label='Style for')
        self.scope_selector.setMinimumWidth(96)
        vline = QtWidgets.QFrame()
        vline.setFrameShape(QtWidgets.QFrame.VLine)
        hlayout.addWidget(vline)
        self.style_reset = mini_button(ui, self.style_widgets, hlayout,
                                       text='reset',
                                       action='reset_style_in_scope')

        hlayout = box_row(sw_layout)

        self.font_selector = font_selector(ui, self.style_widgets, hlayout,
                                           action='select_font',
                                           label='Text style')

        self.node_color_selector = color_selector(ui, self.style_widgets, hlayout,
                                                  action='change_node_color')

        self.open_font_dialog = icon_button(ui, self.style_widgets, hlayout,
                                            icon=qt_prefs.font_icon,
                                            text='Add custom font',
                                            action='start_font_dialog',
                                            size=20)

        hlayout = box_row(sw_layout)
        self.shape_selector = shape_selector(ui, self.style_widgets, hlayout,
                                             action='change_edge_shape',
                                             label='Edge style')

        self.edge_color_selector = color_selector(ui, self.style_widgets, hlayout,
                                                  action='change_edge_color')

        self.edge_options = icon_button(ui, self.style_widgets, hlayout,
                                        icon=qt_prefs.settings_icon,
                                        text='More line options',
                                        action='toggle_panel_LineOptionsPanel',
                                        checkable=True)
        self.style_widgets.setLayout(sw_layout)
        layout.addWidget(self.style_widgets)
        inner.setLayout(layout)
        inner.setBackgroundRole(QtGui.QPalette.AlternateBase)
        #self.style_widgets.hide()
        self.setWidget(inner)

        self.finish_init()

    def toggle_customization(self, value):
        if value:
            self.style_widgets.show()
        else:
            self.style_widgets.hide()
        self.setFixedSize(self.sizeHint())
        self.updateGeometry()

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
        self.scope_selector.select_by_data(ctrl.ui.active_scope)

    def receive_font_from_selector(self, font_key, font):
        ctrl.ui.set_font(font_key, font)
        self.cached_font_id = font_key
        self.update_font_selector(font_key)
        ctrl.main.trigger_action('select_font_from_dialog')

    def update_font_selector(self, font_id):
        self.cached_font_id = font_id
        font = qt_prefs.fonts[font_id]
        item = self.font_selector.find_list_item(font_id)
        self.font_selector.setFont(font)
        if item:
            item.setToolTip('%s, %spt' % (font.family(), font.pointSize()))
            item.setFont(font)
        else:
            self.font_selector.add_font(font_id, qt_prefs.fonts[font_id])
            self.font_selector.select_by_data(font_id)

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
        s.select_by_data(color_key)
        s.update()

    def update_edge_color_selector(self, color_key):
        s = self.edge_color_selector
        self.cached_edge_color = color_key
        s.select_by_data(color_key)
        s.update()
        self.shape_selector.update()

    def update_panel(self):
        """ Panel update should be necessary when changing ctrl.selection or
        after the trees has otherwise changed.
        :return:
        """
        self.update_fields()

    def update_colors(self):
        self.shape_selector.update_colors()

    # @time_me
    def update_scope_selector_options(self):
        """ Redraw scope selector, show only scopes that are used in this
        forest """
        ni = classes.node_info
        items = [('Current selection', g.SELECTION)]
        items += [(ni[key]['name_pl'], key) for key in classes.node_types_order]
        self.scope_selector.add_items(items)

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
                    self.cached_node_color = item.get_color_id()
                    set_value(self.node_color_selector, self.cached_node_color)
                    self.cached_font_id = item.get_font_id()
                    set_value(self.font_selector, self.cached_font_id)
                elif no_edge and isinstance(item, Edge):
                    no_edge = False
                    self.cached_edge_color = item.color_id
                    set_value(self.edge_color_selector, item.color_id)
                    set_value(self.shape_selector, item.shape_name)
                elif not (no_edge or no_node):
                    break
        elif ctrl.forest:
            node_type = ctrl.ui.active_node_type
            edge_type = ctrl.ui.active_edge_type
            node_color = ctrl.settings.get_node_setting('color_id', node_type=node_type)
            node_font = ctrl.settings.get_node_setting('font_id', node_type=node_type)
            edge_color = ctrl.settings.get_edge_setting('color_id', edge_type=edge_type)
            edge_shape = ctrl.settings.get_edge_setting('shape_name', edge_type=edge_type)
            # Color selector - show
            set_value(self.node_color_selector, node_color)
            set_value(self.font_selector, node_font)
            set_value(self.edge_color_selector, edge_color)
            set_value(self.shape_selector, edge_shape)
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
