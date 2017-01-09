from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs, prefs, classes
from kataja.saved.Edge import Edge
from kataja.saved.movables.Node import Node
from kataja.ui_widgets.Panel import Panel
from kataja.ui_support.panel_utils import  box_row, font_selector, color_selector, icon_button, \
    shape_selector, selector, mini_button

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

        self.watchlist = ['selection_changed', 'forest_changed']
        # Other items may be temporarily added, they are defined as
        # class.variables
        ui = self.ui_manager
        # hlayout = box_row(layout)
        #
        # styles_data = []
        # current_style_i = 0
        # for i, value in enumerate(prefs.available_styles):
        #     if value == ctrl.settings.get('style'):
        #         current_style_i = i
        #     styles_data.append((value, value))
        # self.overall_style_box = selector(ui, self, hlayout,
        #                                   data=styles_data,
        #                                   action='change_master_style')
        # self.overall_style_box.setCurrentIndex(current_style_i)
        # #self.custom_overall_style = text_button(ui, hlayout,
        # #                                        text='customize',
        # #                                        action='customize_master_style',
        # #                                        checkable=True)
        # self.overall_style_box.hide()
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

        self.node_color_selector = color_selector(ui, self.style_widgets, hlayout,
                                                  action='change_node_color', role='node',
                                                  label='Node color')
        self.font_selector = font_selector(ui, self.style_widgets, hlayout,
                                           action='select_font',
                                           label='font')

        hlayout = box_row(sw_layout)
        self.shape_selector = shape_selector(ui, self.style_widgets, hlayout,
                                             action='change_edge_shape',
                                             label='Edge style')

        self.edge_color_selector = color_selector(ui, self.style_widgets, hlayout,
                                                  action='change_edge_color', role='edge')

        self.edge_options = icon_button(ui, self.style_widgets, hlayout,
                                        icon=qt_prefs.settings_icon,
                                        text='More edge options',
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

    # @time_me
    def update_scope_selector_options(self):
        """ Redraw scope selector, show only scopes that are used in this
        forest """
        ni = classes.node_info
        items = [('Current selection', g.SELECTION)]
        items += [(ni[key]['name_pl'], key) for key in classes.node_types_order]
        self.scope_selector.add_items(items)

    def showEvent(self, event):
        """ Panel may have missed signals to update its contents when it was hidden: update all
        that signals would update.
        :param event:
        :return:
        """
        self.update_selection()
        super().showEvent(event)

    def watch_alerted(self, obj, signal, field_name, value):
        """ Receives alerts from signals that this object has chosen to
        listen. These signals are declared in 'self.watchlist'.

         This method will try to sort out the received signals and act
         accordingly.

        :param obj: the object causing the alarm
        :param signal: identifier for type of the alarm
        :param field_name: name of the field of the object causing the alarm
        :param value: value given to the field
        :return:
        """
        if signal == 'selection_changed':
            self.update_selection()
        elif signal == 'forest_changed':
            self.update_selection()
