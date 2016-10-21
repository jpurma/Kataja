from PyQt5 import QtWidgets, QtCore
from kataja.singletons import ctrl, prefs
from kataja.utils import time_me
from kataja.saved.Edge import Edge
from kataja.ui_widgets.Panel import Panel
from kataja.ui_support.panel_utils import box_row, spinbox, label, decimal_spinbox, mini_button, \
    knob, KnobDial, checkbox, radiobutton
import kataja.globals as g
from kataja.edge_styles import names as edge_names

__author__ = 'purma'


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
        inner = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout()
        layout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum,
                                                 QtWidgets.QSizePolicy.MinimumExpanding))
        self.setMaximumWidth(220)
        self.setMaximumHeight(160)
        self.watchlist = ['edge_shape', 'scope_changed', 'selection_changed', 'edge_adjustment']

        spac = 8
        ui = self.ui_manager
        hlayout = box_row(layout)
        self.reset_adjustment = mini_button(ui, self, hlayout, text='Reset arc adjustments',
                                            action='reset_control_points', width=-1)
        self.reset_all = mini_button(ui, self, hlayout, text='Reset edge settings',
                                     action='reset_edge_settings', width=-1)
        layout.addSpacing(spac)

        hlayout = box_row(layout)
        self.arrowhead_start_button = checkbox(ui, self, hlayout, label='Arrowheads at start',
                                               action='edge_arrowhead_start')
        self.arrowhead_end_button = checkbox(ui, self, hlayout, label='at end',
                                             action='edge_arrowhead_end')
        # Curvature
        layout.addSpacing(spac)
        hlayout = box_row(layout)
        curve_modes = QtWidgets.QButtonGroup()
        self.relative_arc_button = radiobutton(ui, self, hlayout, label='Relative curve',
                                               action='edge_curvature_relative', group=curve_modes)
        self.arc_rel_dx_spinbox = spinbox(ui, self, hlayout,
                                          label='X', range_min=-200, range_max=200,
                                          action='change_edge_relative_curvature_x',
                                          suffix='%')
        self.arc_rel_dy_spinbox = spinbox(ui, self, hlayout,
                                          label='Y', range_min=-200, range_max=200,
                                          action='change_edge_relative_curvature_y',
                                          suffix='%')

        hlayout = box_row(layout)
        self.fixed_arc_button = radiobutton(ui, self, hlayout, label='Fixed curve',
                                            action='edge_curvature_fixed', group=curve_modes)
        self.arc_fixed_dx_spinbox = spinbox(ui, self, hlayout,
                                            label='X', range_min=-200, range_max=200,
                                            action='change_edge_fixed_curvature_x',
                                            suffix=' px')
        self.arc_fixed_dy_spinbox = spinbox(ui, self, hlayout,
                                            label='Y', range_min=-200, range_max=200,
                                            action='change_edge_fixed_curvature_y',
                                            suffix=' px')
        self.arc_reference_buttons = QtWidgets.QButtonGroup(self)
        self.arc_reference_buttons.addButton(self.fixed_arc_button)
        self.arc_reference_buttons.addButton(self.relative_arc_button)

        # Line thickness
        layout.addSpacing(spac)
        hlayout = box_row(layout)
        self.fill_button = checkbox(ui, self, hlayout, label='Fill',
                                    action='edge_shape_fill')

        self.line_button = checkbox(ui, self, hlayout, label='Outline',
                                    action='edge_shape_line')
        self.thickness_spinbox = decimal_spinbox(ui, self, hlayout,
                                                 label='Thickness', range_min=0.0, range_max=10.0,
                                                 step=0.1, action='edge_thickness', suffix=' px')

        # Leaf size
        hlayout = box_row(layout)
        self.leaf_x_spinbox = decimal_spinbox(ui, self, hlayout, label='Brush spread X',
                                              range_min=-20.0,
                                              range_max=20.0,
                                              step=0.5,
                                              action='leaf_shape_x', suffix=' px')
        self.leaf_y_spinbox = decimal_spinbox(ui, self, hlayout, label='Y',
                                              range_min=-20.0,
                                              range_max=20.0,
                                              step=0.5,
                                              action='leaf_shape_y', suffix=' px')
        inner.setLayout(layout)
        self.setWidget(inner)
        self.finish_init()

    def finish_init(self):
        Panel.finish_init(self)
        self.update_panel()
        self.show()

    def update_panel(self):
        """ Choose which selectors to show and update their values
        :return: None
        """
        if not ctrl.forest.settings:
            return
        if ctrl.ui.scope_is_selection:
            es = ctrl.ui.active_edge_style
            if es:
                if es.get('edge_count', 0) == 1:
                    self.set_title('Settings for selected edge')
                else:
                    self.set_title('Settings for selected edges')
            else:
                self.set_title('Edge settings - No edge selected')
        else:
            edge_type = ctrl.ui.active_edge_type
            edge_name_plural = edge_names.get(edge_type, '? edges')[1].lower()
            self.set_title('Settings for all ' + edge_name_plural)
        self.setFixedSize(self.sizeHint())
        self.updateGeometry()

    def initial_position(self, next_to=''):
        """
        :return:
        """
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
        if signal == 'scope_changed':
            self.update_panel()
        elif signal == 'edge_shape':
            print('received edge_shape update')
            self.update_panel()
        elif signal == 'selection_changed':
            self.update_panel()
        elif signal == 'edge_adjustment':
            pass
