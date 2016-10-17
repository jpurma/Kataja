from PyQt5 import QtWidgets, QtCore
from kataja.singletons import ctrl, prefs
from kataja.utils import time_me
from kataja.saved.Edge import Edge
from kataja.ui_widgets.Panel import Panel
from kataja.ui_support.panel_utils import box_row, spinbox, label, decimal_spinbox, mini_button
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
        layout.addSpacing(spac)
        hlayout = box_row(layout)
        label(self, hlayout, 'Control points')
        # Control point 1 adjustment
        self.cp1_box = QtWidgets.QWidget(inner) # box allows hiding clean hide/show for this group
        hlayout = box_row(self.cp1_box)
        label(self, hlayout, '1st')
        ui = self.ui_manager
        self.cp1_x_spinbox = spinbox(ui, self, hlayout,
                                     label='dist', range_min=-400, range_max=400,
                                     action='control_point1_dist', suffix='%')
        self.cp1_y_spinbox = spinbox(ui, self, hlayout,
                                     label='angle', range_min=-400, range_max=400,
                                     action='control_point1_angle', suffix='°')
        layout.addWidget(self.cp1_box)

        # Control point 2 adjustment
        self.cp2_box = QtWidgets.QWidget(inner) # box allows hiding clean hide/show for this group
        hlayout = box_row(self.cp2_box)
        label(self, hlayout, '2nd')
        self.cp2_x_spinbox = spinbox(ui, self, hlayout,
                                     label='dist', range_min=-400, range_max=400,
                                     action='control_point2_dist', suffix='%')
        self.cp2_y_spinbox = spinbox(ui, self, hlayout,
                                     label='angle', range_min=-400, range_max=400,
                                     action='control_point2_angle', suffix='°')
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
        self.leaf_x_spinbox = spinbox(ui, self, box_layout, label='X', range_min=-20, range_max=20,
                                      action='leaf_shape_x', suffix=' px')
        self.leaf_y_spinbox = spinbox(ui, self, box_layout, label='Y', range_min=-20, range_max=20,
                                      action='leaf_shape_y', suffix=' px')
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

    def update_panel(self):
        """ Choose which selectors to show and update their values
        :return: None
        """
        if not ctrl.forest.settings:
            return
        if ctrl.ui.scope_is_selection:
            sd = ctrl.ui.edge_styles_in_selection
            if sd:
                if sd['edge_count'] == 1:
                    self.set_title('Edge settings for selected edge')
                else:
                    self.set_title('Edge settings for selected edges')
            else:
                self.set_title('Edge settings - No edge selected')
        else:
            edge_type = ctrl.ui.active_edge_type
            edge_name_plural = edge_names.get(edge_type, '? edges')[1].lower()
            self.set_title('Edge settings for all ' + edge_name_plural)
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
                if dp.isFloating():
                    return QtCore.QPoint(p.x() / pixel_ratio, p.y() / pixel_ratio + 20)
                else:
                    return QtCore.QPoint(p.x() / pixel_ratio + dp.width() + 40, p.y() / pixel_ratio)
            else:
                return Panel.initial_position(self)
        else:
            return Panel.initial_position(self)

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
            pass
