from PyQt5 import QtWidgets, QtCore
from kataja.singletons import ctrl, prefs
from kataja.utils import time_me
from kataja.saved.Edge import Edge
from kataja.ui_items.Panel import Panel
from kataja.ui_support.panel_utils import box_row, spinbox, label, decimal_spinbox, mini_button, \
    set_value
import kataja.globals as g

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
        self.watchlist = ['edge_shape', 'scope_changed', 'selection_changed', 'edge_adjustment']

        spac = 8
        layout.addSpacing(spac)
        hlayout = box_row(layout)
        label(self, hlayout, 'Control points')
        # Control point 1 adjustment
        self.cp1_box = QtWidgets.QWidget(inner) # box allows hiding clean hide/show for this group
        hlayout = box_row(self.cp1_box)
        label(self, hlayout, '1st control point')
        ui = self.ui_manager
        self.cp1_x_spinbox = spinbox(ui, self, hlayout, 'X', -400, 400, 'control_point1_x')
        self.cp1_y_spinbox = spinbox(ui, self, hlayout, 'Y', -400, 400, 'control_point1_y')
        layout.addWidget(self.cp1_box)

        # Control point 2 adjustment
        self.cp2_box = QtWidgets.QWidget(inner) # box allows hiding clean hide/show for this group
        hlayout = box_row(self.cp2_box)
        label(self, hlayout, '2nd control point')
        self.cp2_x_spinbox = spinbox(ui, self, hlayout, 'X', -400, 400, 'control_point2_x')
        self.cp2_y_spinbox = spinbox(ui, self, hlayout, 'Y', -400, 400, 'control_point2_y')
        layout.addWidget(self.cp2_box)

        # Curvature
        layout.addSpacing(spac)
        hlayout = box_row(layout)
        label(self, hlayout, 'General curvature')

        hlayout = box_row(layout)
        self.relative_arc_button = mini_button(ui, self, hlayout, text='relative',
                                               action='edge_curvature_relative', checkable=True)
        self.relative_arc_box = QtWidgets.QWidget(inner)
        arc_layout = QtWidgets.QHBoxLayout()
        self.arc_rel_dx_spinbox = spinbox(ui, self, arc_layout,
                                          label='X', range_min=-200, range_max=200,
                                          action='change_edge_relative_curvature_x',
                                          suffix='%')
        self.arc_rel_dy_spinbox = spinbox(ui, self, arc_layout,
                                          label='Y', range_min=-200, range_max=200,
                                          action='change_edge_relative_curvature_y',
                                          suffix='%')
        arc_layout.setContentsMargins(0, 0, 0, 0)
        self.relative_arc_box.setLayout(arc_layout)
        hlayout.addWidget(self.relative_arc_box)

        hlayout = box_row(layout)
        self.fixed_arc_button = mini_button(ui, self, hlayout, text='fixed',
                                            action='edge_curvature_fixed', checkable=True)
        self.fixed_arc_box = QtWidgets.QWidget(inner)
        arc_layout = QtWidgets.QHBoxLayout()
        self.arc_fixed_dx_spinbox = spinbox(ui, self, arc_layout,
                                            label='X', range_min=-200, range_max=200,
                                            action='change_edge_fixed_curvature_x',
                                            suffix=' px')
        self.arc_fixed_dy_spinbox = spinbox(ui, self, arc_layout,
                                            label='Y', range_min=-200, range_max=200,
                                            action='change_edge_fixed_curvature_y',
                                            suffix=' px')
        arc_layout.setContentsMargins(0, 0, 0, 0)
        self.fixed_arc_box.setLayout(arc_layout)
        hlayout.addWidget(self.fixed_arc_box)
        self.arc_reference_buttons = QtWidgets.QButtonGroup(self)
        self.arc_reference_buttons.addButton(self.fixed_arc_button)
        self.arc_reference_buttons.addButton(self.relative_arc_button)

        # Line thickness
        layout.addSpacing(spac)
        hlayout = box_row(layout)
        label(self, hlayout, 'Shape and thickness')

        hlayout = box_row(layout)
        self.line_button = mini_button(ui, self, hlayout, 'Line',
                                       'edge_shape_line', checkable=True)
        self.thickness_box = QtWidgets.QWidget(inner)
        box_layout = QtWidgets.QHBoxLayout()
        box_layout.setContentsMargins(0, 0, 0, 0)
        self.thickness_spinbox = decimal_spinbox(ui, self, box_layout,
                                                 label='Thickness', range_min=0.0, range_max=10.0,
                                                 step=0.1, action='edge_thickness', suffix=' px')
        self.thickness_box.setLayout(box_layout)
        hlayout.addWidget(self.thickness_box)

        # Leaf size
        hlayout = box_row(layout)
        self.fill_button = mini_button(ui, self, hlayout, 'Filled',
                                       'edge_shape_fill', checkable=True)
        self.leaf_box = QtWidgets.QWidget(inner)
        box_layout = QtWidgets.QHBoxLayout()
        box_layout.setContentsMargins(0, 0, 0, 0)
        label(self, box_layout, 'Spread')
        self.leaf_x_spinbox = spinbox(ui, self, box_layout, 'X', -20, 20, 'leaf_shape_x')
        self.leaf_y_spinbox = spinbox(ui, self, box_layout, 'Y', -20, 20, 'leaf_shape_y')
        self.leaf_box.setLayout(box_layout)
        hlayout.addWidget(self.leaf_box)

        self.shape_fill_buttons = QtWidgets.QButtonGroup(self)
        self.shape_fill_buttons.addButton(self.fill_button)
        self.shape_fill_buttons.addButton(self.line_button)

        layout.addSpacing(spac)
        hlayout = box_row(layout)
        label(self, hlayout, 'Arrowheads')
        self.arrowhead_start_button = mini_button(ui, self, hlayout, 'at start',
                                                  'edge_arrowhead_start',
                                                  checkable=True)
        self.arrowhead_end_button = mini_button(ui, self, hlayout, 'at end',
                                                'edge_arrowhead_end',
                                                checkable=True)
        inner.setLayout(layout)
        self.setWidget(inner)
        self.finish_init()

    def finish_init(self):
        Panel.finish_init(self)
        self.update_panel()
        self.show()

    @time_me
    def update_panel(self):
        """ Choose which selectors to show and update their values
        :return: None
        """
        print('updating shape options panel ')
        if not ctrl.forest.settings:
            return
        if ctrl.ui.scope_is_selection:
            sd = ctrl.ui.edge_styles_in_selection
            if sd:
                if sd['edge_count'] == 1:
                    self.set_title('Edge settings for selected edge')
                    self.update_control_points(sd['sample_edge'])
                else:
                    self.set_title('Edge settings for selected edges')
                arrowhead_at_start = sd['arrowhead_at_start']
                arrowhead_at_end = sd['arrowhead_at_end']
            else:
                arrowhead_at_start = False
                arrowhead_at_end = False
        else:
            edge_type = ctrl.ui.active_edge_type
            sd = ctrl.forest.settings.shape_info(edge_type)
            arrowhead_at_start = ctrl.forest.settings.edge_info(edge_type, 'arrowhead_at_start')
            arrowhead_at_end = ctrl.forest.settings.edge_info(edge_type, 'arrowhead_at_end')

            self.set_title('Edge settings for all ' + prefs.edge_styles[edge_type][
                'name_pl'].lower())
        if sd:
            # Relative / fixed curvature
            control_points = sd['control_points']
            relative = sd.get('relative', None)
            if relative is None or not control_points:  # linear shape, no arc of any kind
                pass
            #elif relative:
            #    set_value(self.relative_arc_button, True)
            #    set_value(self.arc_rel_dx_spinbox, sd['rel_dx'] * 100)
            #    set_value(self.arc_rel_dy_spinbox, sd['rel_dy'] * 100)
            #else:
            #    set_value(self.fixed_arc_button, True)
            #    set_value(self.arc_fixed_dx_spinbox, sd['fixed_dx'])
            #    set_value(self.arc_fixed_dy_spinbox, sd['fixed_dy'])

            # Leaf-shaped lines or solid lines
            fill = sd.get('fill', None)
            if fill:
                if 'leaf_x' in sd:
                    #set_value(self.leaf_x_spinbox, sd['leaf_x'])
                    #set_value(self.leaf_y_spinbox, sd['leaf_y'])
                    #set_value(self.fill_button, True)
                    pass
            elif fill is not None:
                if sd.get('thickness', None) is not None:
                    #set_value(self.thickness_spinbox, sd['thickness'])
                    #set_value(self.line_button, True)
                    pass
            # Arrowheads
            if arrowhead_at_start is not None:
                #set_value(self.arrowhead_start_button, arrowhead_at_start)
                pass
            if arrowhead_at_end is not None:
                #set_value(self.arrowhead_end_button, arrowhead_at_end)
                pass
        else:
            self.set_title('Edge settings - No edge selected')

        self.setFixedSize(self.sizeHint())
        self.updateGeometry()

    def initial_position(self):
        """


        :return:
        """
        dp = self.ui_manager.get_panel('StylePanel')
        if dp:
            pixel_ratio = dp.devicePixelRatio()
            p = dp.mapToGlobal(dp.pos())
            if pixel_ratio:
                return QtCore.QPoint(p.x() / pixel_ratio + dp.width() + 40, p.y() / pixel_ratio)
            else:
                return Panel.initial_position(self)
        else:
            return Panel.initial_position(self)

    def update_control_points(self, edge):
        if (not edge) or not edge.curve_adjustment:
            return
        points = len(edge.curve_adjustment)
        if points == 1:
            pass
            #set_value(self.cp1_x_spinbox, edge.curve_adjustment[0][0])
            #set_value(self.cp1_y_spinbox, edge.curve_adjustment[0][1])
        elif points == 2:
            pass
            #set_value(self.cp1_x_spinbox, edge.curve_adjustment[0][0])
            #set_value(self.cp1_y_spinbox, edge.curve_adjustment[0][1])
            #set_value(self.cp2_x_spinbox, edge.curve_adjustment[1][0])
            #set_value(self.cp2_y_spinbox, edge.curve_adjustment[1][1])

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
            self.update_panel()
        elif signal == 'selection_changed':
            self.update_panel()
        elif signal == 'edge_adjustment':
            e = ctrl.get_single_selected()
            if e and isinstance(e, Edge):
                self.update_control_points(e)
