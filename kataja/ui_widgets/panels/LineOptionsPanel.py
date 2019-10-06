from PyQt5 import QtWidgets, QtGui, QtCore

import kataja.globals as g
from kataja.Shapes import SHAPE_PRESETS
from kataja.edge_styles import names as edge_names
from kataja.singletons import ctrl, prefs, classes
from kataja.ui_support.panel_utils import box_row
from kataja.ui_widgets.KatajaCheckBox import KatajaCheckBox
from kataja.ui_widgets.KatajaSpinbox import KatajaSpinbox, KatajaDecimalSpinbox
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.SelectionBox import SelectionBox
from kataja.ui_widgets.buttons.PanelButton import PanelButton
from kataja.ui_widgets.selection_boxes.ColorSelector import ColorSelector
from kataja.ui_widgets.selection_boxes.ShapeSelector import ShapeSelector

__author__ = 'purma'


def hdivider():
    # noinspection PyArgumentList
    hline = QtWidgets.QFrame()
    hline.setForegroundRole(QtGui.QPalette.AlternateBase)
    hline.setFrameShape(QtWidgets.QFrame.HLine)
    return hline


class LineOptionsPanel(Panel):
    """ Panel for editing how edges and nodes are drawn. """

    def __init__(self, name, default_position='float', parent=None, folded=False):
        """
        BUild all advanced line options. Then in update filter what to show based on the line type.

        All of the panel constructors follow the same format so that the construction can be automated:
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        Panel.__init__(self, name, default_position, parent, folded)
        layout = self.vlayout
        widget = self.widget()
        self.active_node_type = g.CONSTITUENT_NODE
        self.shape_selector = None

        ctrl.main.selection_changed.connect(self.update_panel)
        ctrl.main.scope_changed.connect(self.update_panel)

        spac = 8
        hlayout = box_row(layout)

        self.edge_type_selector = SelectionBox(parent=widget, data=[],
                                               action='set_edge_type_for_editing'
                                               ).to_layout(hlayout, with_label='Style for')
        self.edge_type_selector.setFixedWidth(148)

        layout.addWidget(hdivider())
        layout.addSpacing(spac)

        hlayout = box_row(layout)
        self.shape_selector = ShapeSelector(parent=widget,
                                            action='change_edge_shape',
                                            ).to_layout(hlayout, with_label='Shape')
        self.shape_selector.for_edge_type = self.active_edge_type

        self.edge_color_selector = ColorSelector(parent=widget,
                                                 action='change_edge_color',
                                                 role='edge').to_layout(hlayout, with_label='Color')
        # Line thickness
        hlayout = box_row(layout)
        self.fill_button = KatajaCheckBox(parent=widget,
                                          action='edge_shape_fill'
                                          ).to_layout(hlayout, with_label='Fill')

        self.line_button = KatajaCheckBox(parent=widget,
                                          action='edge_shape_line'
                                          ).to_layout(hlayout, with_label='Outline')
        self.thickness_spinbox = KatajaDecimalSpinbox(parent=widget,
                                                      range_min=0.0,
                                                      range_max=10.0,
                                                      step=0.1,
                                                      action='edge_thickness',
                                                      suffix=' px'
                                                      ).to_layout(hlayout, with_label='Thickness')
        layout.addWidget(hdivider())
        layout.addSpacing(spac)

        hlayout = box_row(layout)
        self.arrowhead_start_button = KatajaCheckBox(parent=widget,
                                                     action='edge_arrowhead_start'
                                                     ).to_layout(hlayout,
                                                                 with_label='Arrowheads at start')
        self.arrowhead_end_button = KatajaCheckBox(parent=widget,
                                                   action='edge_arrowhead_end'
                                                   ).to_layout(hlayout, with_label='at end')
        layout.addWidget(hdivider())
        layout.addSpacing(spac)
        # Curvature
        hlayout = box_row(layout)
        hlayout.addWidget(QtWidgets.QLabel('Curvature'))
        hlayout.setAlignment(QtCore.Qt.AlignRight)
        self.arc_rel_dx_spinbox = KatajaSpinbox(parent=widget, range_min=-200, range_max=200,
                                                action='change_edge_relative_curvature_x',
                                                suffix='%'
                                                ).to_layout(hlayout, with_label='X')
        self.arc_rel_dy_spinbox = KatajaSpinbox(parent=widget, range_min=-200, range_max=200,
                                                action='change_edge_relative_curvature_y',
                                                suffix='%'
                                                ).to_layout(hlayout, with_label='Y')

        hlayout = box_row(layout)
        hlayout.setAlignment(QtCore.Qt.AlignRight)
        self.arc_fixed_dx_spinbox = KatajaSpinbox(parent=widget, range_min=-200, range_max=200,
                                                  action='change_edge_fixed_curvature_x',
                                                  suffix=' px'
                                                  ).to_layout(hlayout, with_label='X')

        self.arc_fixed_dy_spinbox = KatajaSpinbox(parent=widget, range_min=-200, range_max=200,
                                                  action='change_edge_fixed_curvature_y',
                                                  suffix=' px'
                                                  ).to_layout(hlayout, with_label='Y')

        # Leaf size
        hlayout = box_row(layout)
        self.leaf_x_spinbox = KatajaDecimalSpinbox(parent=widget,
                                                   range_min=-20.0,
                                                   range_max=20.0,
                                                   step=0.5,
                                                   action='leaf_shape_x',
                                                   suffix=' px'
                                                   ).to_layout(hlayout, with_label='Brush spread X')
        self.leaf_y_spinbox = KatajaDecimalSpinbox(parent=widget,
                                                   range_min=-20.0,
                                                   range_max=20.0,
                                                   step=0.5,
                                                   action='leaf_shape_y',
                                                   suffix=' px'
                                                   ).to_layout(hlayout, with_label='Y')
        layout.addWidget(hdivider())
        layout.addSpacing(spac)

        hlayout = box_row(layout)
        self.reset_all = PanelButton(parent=widget, text='Reset edge settings',
                                     action='reset_edge_settings').to_layout(hlayout)
        self.reset_all.setMaximumHeight(20)

        self.reset_adjustment = PanelButton(parent=widget,
                                            text='Reset curves',
                                            action='reset_control_points').to_layout(hlayout)
        self.reset_adjustment.setMaximumHeight(20)
        self.finish_init()

    @property
    def active_edge_type(self):
        if self.active_node_type:
            return classes.node_type_to_edge_type[self.active_node_type]
        else:
            return g.CONSTITUENT_EDGE

    @property
    def active_shape_name(self):
        if self.active_node_type:
            return ctrl.forest.settings.get_for_edge_type('edge_shape', self.active_edge_type)

    def finish_init(self):
        Panel.finish_init(self)
        self.update_panel()
        self.show()

    def update_panel(self):
        """ Choose which selectors to show and update their values
        :return: None
        """
        if not ctrl.forest:
            return
        self.update_scope_selector_options()
        if self.shape_selector:
            self.shape_selector.for_edge_type = self.active_edge_type
        self.setFixedSize(self.sizeHint())
        self.updateGeometry()

    def update_scope_selector_options(self):
        """ Redraw scope selector, show only scopes that are used in this
        forest """
        edge_types = []
        items = []
        for node_type in classes.node_types_order:
            default_edge = classes.nodes[node_type].default_edge
            if default_edge not in edge_types:
                edge_types.append(default_edge)
                if default_edge in edge_names:
                    edge_name_plural = edge_names[default_edge][1]
                else:
                    edge_name_plural = default_edge
                items.append((node_type, edge_name_plural))
        self.edge_type_selector.add_items(items)

    def update_selection(self):
        self.update_scope_selector_options()
        # if ctrl.ui.scope_is_selection:
        #    self.edge_type_selector.setEnabled(False)
        # else:
        #    self.edge_type_selector.setEnabled(False)
        #    self.edge_type_selector.select_by_data(self.active_node_type)
        # self.scope_selector.select_by_data(ctrl.ui.active_scope)

    def initial_position(self, next_to=''):
        return Panel.initial_position(self, next_to=next_to or 'StylePanel')

    def close(self):
        """ Untick check box in EDGES panel """
        dp = self.ui_manager.get_panel('StylePanel')
        if dp:
            dp.edge_options.setChecked(False)
        Panel.close(self)

    def show(self):
        """ Tick check box in EDGES panel """
        dp = self.ui_manager.get_panel('StylePanel')
        if dp:
            dp.edge_options.setChecked(True)
        Panel.show(self)

    def showEvent(self, event):
        """ Panel may have missed signals to update its contents when it was hidden: update all
        that signals would update.
        :param event:
        :return:
        """
        self.update_panel()
        super().showEvent(event)

    def get_active_node_setting(self, key):
        return ctrl.ui.get_active_node_setting(key, self.active_node_type)

    def active_edge_has_setting(self, key):
        shape_name = ctrl.ui.get_active_edge_setting('shape_name', self.active_edge_type)
        return key in SHAPE_PRESETS[shape_name].defaults

    def get_active_shape_setting(self, key):
        """ Return edge setting either from selected items or from ui.active_edge_type. If there
        are settings made in node level, return first of such occurence.
        :param key:
        :return:
        """
        if ctrl.ui.scope_is_selection:
            nodes = ctrl.get_selected_nodes()
            if nodes:
                for node in nodes:
                    ns = node.get_settings()
                    if key in ns:
                        return ns[key]
                return nodes[0].settings.get(key)
            shape_name = ctrl.ui.get_active_edge_setting('shape_name', self.active_edge_type)
            return ctrl.forest.settings.get_for_edge_shape(key, shape_name)
        shape_name = ctrl.ui.get_active_edge_setting('shape_name', self.active_edge_type)
        if ctrl.ui.active_scope == g.FOREST:
            return ctrl.forest.settings.get_for_edge_shape(key, shape_name)
        elif ctrl.ui.active_scope == g.DOCUMENT:
            return ctrl.doc_settings.get_for_edge_shape(key, shape_name)
        else:
            return prefs.get_for_edge_shape(key, shape_name)

    def get_active_shape_property(self, key):
        """ Return the class property of currently active edge shape.
        :param key:
        :return:
        """
        if ctrl.ui.scope_is_selection:
            edges = ctrl.get_selected_edges()
            if edges:
                for edge in edges:
                    if key in edge.settings:
                        return edge.settings[key]
                return getattr(edges[0].path.my_shape, key)
        shape_name = ctrl.ui.get_active_edge_setting('shape_name', self.active_edge_type)
        return getattr(SHAPE_PRESETS[shape_name], key)

    def is_active_fillable(self):
        return self.get_active_shape_property('fillable')

    def has_active_outline(self):
        return self.get_active_shape_setting('outline')

    def has_active_fill(self):
        fillable = self.get_active_shape_property('fillable')
        if fillable:
            return self.get_active_shape_setting('fill')
        return False
