from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QSpinBox

from kataja.Edge import Edge
from kataja.singletons import ctrl, prefs
import kataja.globals as g
from kataja.ui.panels.field_utils import *
from kataja.utils import time_me
from kataja.ui.panels.UIPanel import UIPanel

__author__ = 'purma'


class LineOptionsPanel(UIPanel):
    """ Panel for editing how edges and nodes are drawn. """

    def __init__(self, name, key, default_position='float', parent=None, ui_manager=None, folded=False):
        """
        BUild all advanced line options. Then in update filter what to show based on the line type.

        All of the panel constructors follow the same format so that the construction can be automated:
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        UIPanel.__init__(self, name, key, default_position, parent, ui_manager, folded)
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
        self.cp1_x_spinbox = spinbox(ui_manager, self, hlayout, 'X', -400, 400, 'control_point1_x')
        self.cp1_y_spinbox = spinbox(ui_manager, self, hlayout, 'Y', -400, 400, 'control_point1_y')
        layout.addWidget(self.cp1_box)

        # Control point 2 adjustment
        self.cp2_box = QtWidgets.QWidget(inner) # box allows hiding clean hide/show for this group
        hlayout = box_row(self.cp2_box)
        label(self, hlayout, '2nd control point')
        self.cp2_x_spinbox = spinbox(ui_manager, self, hlayout, 'X', -400, 400, 'control_point2_x')
        self.cp2_y_spinbox = spinbox(ui_manager, self, hlayout, 'Y', -400, 400, 'control_point2_y')
        layout.addWidget(self.cp2_box)

        # Curvature
        layout.addSpacing(spac)
        hlayout = box_row(layout)
        label(self, hlayout, 'Curvature')


        hlayout = box_row(layout)
        self.relative_arc_button = mini_button(ui_manager, self, hlayout, 'relative',
                                               'edge_curvature_relative', checkable=True)
        self.relative_arc_box = QtWidgets.QWidget(inner)
        arc_layout = QtWidgets.QHBoxLayout()
        self.arc_rel_dx_spinbox = spinbox(ui_manager, self, arc_layout,
                                          label='X', range_min=-200, range_max=200,
                                          action='change_edge_relative_curvature_x',
                                          suffix='%')
        self.arc_rel_dy_spinbox = spinbox(ui_manager, self, arc_layout,
                                          label='Y', range_min=-200, range_max=200,
                                          action='change_edge_relative_curvature_y',
                                          suffix='%')
        arc_layout.setContentsMargins(0, 0, 0, 0)
        self.relative_arc_box.setLayout(arc_layout)
        hlayout.addWidget(self.relative_arc_box)


        hlayout = box_row(layout)
        self.fixed_arc_button = mini_button(ui_manager, self, hlayout, 'fixed',
                                            'edge_curvature_fixed', checkable=True)
        self.fixed_arc_box = QtWidgets.QWidget(inner)
        arc_layout = QtWidgets.QHBoxLayout()
        self.arc_fixed_dx_spinbox = spinbox(ui_manager, self, arc_layout,
                                            label='X', range_min=-200, range_max=200,
                                            action='change_edge_fixed_curvature_x',
                                            suffix=' px')
        self.arc_fixed_dy_spinbox = spinbox(ui_manager, self, arc_layout,
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
        self.thickness_box = QtWidgets.QWidget(inner)
        hlayout = box_row(self.thickness_box)
        self.thickness_spinbox = decimal_spinbox(ui_manager, self, hlayout,
                                                 label='Thickness', range_min=0.0, range_max=10.0,
                                                 step=0.1, action='edge_thickness', suffix=' px')
        layout.addWidget(self.thickness_box)

        # Leaf size
        self.leaf_box = QtWidgets.QWidget(inner)
        hlayout = box_row(self.leaf_box)
        label(self, hlayout, 'Leaf width and height')
        self.leaf_x_spinbox = spinbox(ui_manager, self, hlayout, 'X', -20, 20, 'leaf_shape_x')
        self.leaf_y_spinbox = spinbox(ui_manager, self, hlayout, 'Y', -20, 20, 'leaf_shape_y')
        layout.addWidget(self.leaf_box)
        inner.setLayout(layout)
        self.setWidget(inner)
        self.finish_init()

    def finish_init(self):
        UIPanel.finish_init(self)
        self.update_panel()
        self.show()

    def update_panel(self):
        """ Choose which selectors to show and update their values
        :return: None
        """
        if ctrl.ui.scope_is_selection:
            sd = self.build_shape_dict_for_selection()
            if sd:
                if sd['n_of_edges'] == 1:
                    self.set_title('Edge settings for selected edge')
                    self.update_cp1()
                    self.update_cp2()
                elif sd['n_of_edges'] > 1:
                    self.set_title('Edge settings for selected edges')
                    self.cp1_box.setDisabled(True)
                    self.cp2_box.setDisabled(True)
            selection = True
        else:  # Adjusting how this relation type is drawn
            sd = ctrl.forest.settings.shape_info(ctrl.ui.active_edge_type)
            self.set_title('Edge settings for all ' + prefs.edges[ctrl.ui.active_edge_type][
                'name_pl'].lower())
            # print('shape settings: ', shape_dict)
            selection = False
        if sd:
            self.fixed_arc_button.setDisabled(False)
            self.relative_arc_button.setDisabled(False)
            self.update_box_visibility(sd, selection)
            cps = sd['control_points']
            # Relative / fixed curvature
            if cps > 0:
                rel = sd.get('relative', None)
                if rel:
                    set_value(self.relative_arc_button, True)
                    set_value(self.arc_rel_dx_spinbox, sd['rel_dx'] * 100,
                              'rel_dx_conflict' in sd)
                    set_value(self.arc_rel_dy_spinbox, sd['rel_dy'] * 100,
                              'rel_dy_conflict' in sd)
                elif rel is not None:
                    set_value(self.fixed_arc_button, True)
                    set_value(self.arc_fixed_dx_spinbox, sd['fixed_dx'],
                              'fixed_dx_conflict' in sd)
                    set_value(self.arc_fixed_dy_spinbox, sd['fixed_dy'],
                              'fixed_dy_conflict' in sd)
            # Leaf-shaped lines or solid lines
            if sd['fill']:
                if 'leaf_x' in sd:
                    set_value(self.leaf_x_spinbox, sd['leaf_x'],
                              'leaf_x_conflict' in sd)
                    set_value(self.leaf_y_spinbox, sd['leaf_y'],
                              'leaf_y_conflict' in sd)
            else:
                set_value(self.thickness_spinbox, sd['thickness'],
                          'thickness_conflict' in sd)
        else:
            self.set_title('Edge settings - No edge selected')
            self.cp1_box.setDisabled(True)
            self.cp2_box.setDisabled(True)
            self.fixed_arc_box.setDisabled(True)
            self.relative_arc_box.setDisabled(True)
            self.fixed_arc_button.setDisabled(True)
            self.relative_arc_button.setDisabled(True)
            self.leaf_box.setDisabled(True)
            self.thickness_box.setDisabled(True)
            self.setFixedSize(self.sizeHint())
            self.updateGeometry()

    def disable_option(self, option):
        if isinstance(option, QSpinBox):
            option.setDisabled(True)

    def initial_position(self):
        """


        :return:
        """
        dp = self.ui_manager.get_panel(g.STYLE)
        if dp:
            pixel_ratio = dp.devicePixelRatio()
            p = dp.mapToGlobal(dp.pos())
            return QtCore.QPoint(p.x() / pixel_ratio + dp.width() + 40, p.y() / pixel_ratio)
        else:
            return UIPanel.initial_position(self)

    def update_cp1(self):
        if not ctrl.selected:
            self.cp1_box.setDisabled(True)
            return

        elif len(ctrl.selected) == 1:
            item = ctrl.selected[0]
            if isinstance(ctrl.selected[0], Edge) and item.curve_adjustment and len(
                    item.curve_adjustment) > 0:
                self.cp1_box.setDisabled(False)
                set_value(self.cp1_x_spinbox, item.curve_adjustment[0][0])
                set_value(self.cp1_y_spinbox, item.curve_adjustment[0][1])
            else:
                self.cp1_box.setDisabled(True)
        else:
            self.cp1_box.setDisabled(True)

    def update_cp2(self):
        if not ctrl.selected:
            self.cp2_box.setDisabled(True)
            return
        elif len(ctrl.selected) == 1:
            item = ctrl.selected[0]
            if isinstance(ctrl.selected[0], Edge) and item.curve_adjustment and len(
                    item.curve_adjustment) > 1:
                set_value(self.cp2_x_spinbox, item.curve_adjustment[1][0])
                set_value(self.cp2_y_spinbox, item.curve_adjustment[1][1])
                self.cp2_box.setDisabled(False)
            else:
                self.cp2_box.setDisabled(True)
        else:
            self.cp2_box.setDisabled(True)

    def update_box_visibility(self, sd, selection):
        """
        :return:
        """
        cps = sd['control_points']
        edges = [x for x in ctrl.selected if isinstance(x, Edge)]
        # Control points
        self.cp1_box.setEnabled(len(edges) == 1 and cps > 0)
        self.cp2_box.setEnabled(len(edges) == 1 and cps > 1)
        # Relative / fixed curvature
        relative = sd['relative']
        self.fixed_arc_box.setEnabled(cps and not relative)
        self.relative_arc_box.setEnabled(cps and relative)
        # Leaf-shaped lines or solid lines
        leaf = sd['fill'] and 'leaf_x' in sd
        self.leaf_box.setEnabled(leaf)
        self.thickness_box.setEnabled(not leaf)
        self.setFixedSize(self.sizeHint())
        self.updateGeometry()

    def build_shape_dict_for_selection(self):
        """ Create a dict of values to show in this panel, add a about conflicting values in
        selection so that they can be shown as special items.
        :return: dict with familiar attributes and $varname_conflict: True for conflicts.
        """
        # check if selection has conflicting values: these cannot be shown then
        edges = [item for item in ctrl.selected if isinstance(item, Edge)]
        if not edges:
            return {}
        d = edges[0].shape_info.copy()
        shape_name = edges[0].shape_name
        d['shape_name'] = shape_name
        d['n_of_edges'] = len(edges)
        if len(edges) > 1:
            keys = ['relative', 'leaf_x', 'leaf_y', 'thickness', 'rel_dx', 'rel_dy', 'fixed_dx',
                    'fixed_dy']
            for item in edges[1:]:
                e = item.shape_info.shape_info()
                if shape_name != item.shape_name:
                    d['shape_name_conflict'] = True
                for key in keys:
                    old = d.get(key, None)
                    new = e.get(key, None)
                    if old is None and new is not None:
                        d[key] = new
                    elif old is not None and new is not None and old != new:
                        d[key + '_conflict'] = True
        return d

    def close(self):
        """ Untick check box in EDGES panel """
        dp = self.ui_manager.get_panel(g.EDGES)
        if dp:
            dp.edge_options.setChecked(False)
        UIPanel.close(self)

    def show(self):
        """ Tick check box in EDGES panel """
        dp = self.ui_manager.get_panel(g.EDGES)
        if dp:
            dp.edge_options.setChecked(True)
        UIPanel.show(self)

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
            self.update_cp1()
            self.update_cp2()