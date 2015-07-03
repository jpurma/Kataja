from PyQt5 import QtWidgets, QtCore

from kataja.Edge import Edge
from kataja.singletons import ctrl
import kataja.globals as g
from kataja.ui.panels.field_utils import *


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

        # Control point 1 adjustment
        self.cp1_box = QtWidgets.QWidget(inner) # box allows hiding clean hide/show for this group
        hlayout = box_row(self.cp1_box)
        label(self, hlayout, 'Arc adjustment 1')
        self.cp1_x_spinbox = spinbox(ui_manager, self, hlayout, 'X', -400, 400, 'control_point1_x')
        self.cp1_y_spinbox = spinbox(ui_manager, self, hlayout, 'Y', -400, 400, 'control_point1_y')
        self.cp1_reset_button = mini_button(ui_manager, hlayout, 'Reset', 'control_point1_reset')
        layout.addWidget(self.cp1_box)

        # Control point 2 adjustment
        self.cp2_box = QtWidgets.QWidget(inner) # box allows hiding clean hide/show for this group
        hlayout = box_row(self.cp2_box)
        label(self, hlayout, 'Arc adjustment 2')
        self.cp2_x_spinbox = spinbox(ui_manager, self, hlayout, 'X', -400, 400, 'control_point2_x')
        self.cp2_y_spinbox = spinbox(ui_manager, self, hlayout, 'Y', -400, 400, 'control_point2_y')
        self.cp2_reset_button = mini_button(ui_manager, hlayout, 'Reset', 'control_point2_reset')
        layout.addWidget(self.cp2_box)

        # Leaf size
        self.leaf_box = QtWidgets.QWidget(inner)
        hlayout = box_row(self.leaf_box)
        label(self, hlayout, 'Leaf thickness')
        self.leaf_x_spinbox = spinbox(ui_manager, self, hlayout, 'X', -20, 20, 'leaf_shape_x')
        self.leaf_y_spinbox = spinbox(ui_manager, self, hlayout, 'Y', -20, 20, 'leaf_shape_y')
        self.leaf_reset_button = mini_button(ui_manager, hlayout, 'Reset', 'leaf_shape_reset')
        layout.addWidget(self.leaf_box)

        # Curvature
        self.arc_box = QtWidgets.QWidget(inner)
        arc_layout = QtWidgets.QVBoxLayout()
        hlayout = box_row(arc_layout)
        label(self, hlayout, 'Curvature')
        self.arc_dx_spinbox = spinbox(ui_manager, self, hlayout, 'X', -200, 200,
                                      'edge_curvature_x')
        self.arc_dy_spinbox = spinbox(ui_manager, self, hlayout, 'Y', -200, 200,
                                      'edge_curvature_y')
        self.arc_type_selector = mini_selector(ui_manager, self, hlayout,
                                               [('pt', 'fixed'), ('%', 'relative')],
                                               'edge_curvature_type')

        hlayout = box_row(arc_layout)
        self.arc_reset_button = mini_button(ui_manager, hlayout, 'Reset',
                                            'edge_curvature_reset')
        hlayout.setAlignment(self.arc_reset_button, QtCore.Qt.AlignRight)
        arc_layout.setContentsMargins(0, 0, 0, 0)
        self.arc_box.setLayout(arc_layout)
        layout.addWidget(self.arc_box)

        # Line thickness
        self.thickness_box = QtWidgets.QWidget(inner)
        hlayout = box_row(self.thickness_box)
        self.thickness_spinbox = decimal_spinbox(ui_manager, self, hlayout, 'Thickness', 0.0,
                                                 10.0, 0.1, 'edge_thickness')
        self.thickness_reset_button = mini_button(ui_manager, hlayout, 'Reset',
                                                  'edge_thickness_reset')
        layout.addWidget(self.thickness_box)

        # Edges drawn as asymmetric
        self.asymmetry_box = QtWidgets.QWidget(inner)
        hlayout = box_row(self.asymmetry_box)
        self.asymmetry_checkbox = checkbox(ui_manager, self, hlayout, 'Edge asymmetry',
                                           'edge_asymmetry')
        layout.addWidget(self.asymmetry_box)

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
        scope = ctrl.ui.get_panel(g.EDGES).scope
        shape_dict = None
        if scope == g.SELECTION:
            shape_dict = self.build_shape_dict_for_selection()
            self.update_cp1()
            self.update_cp2()
            selection = True
        else:  # Adjusting how this relation type is drawn
            shape_dict = ctrl.forest.settings.edge_shape_settings(scope)
            # print('shape settings: ', shape_dict)
            selection = False
        if shape_dict:
            self.update_box_visibility(shape_dict, selection)
            cps = shape_dict['control_points']
            # Relative / fixed curvature
            if cps > 0:
                rel = shape_dict.get('relative', None)
                if rel:
                    set_value(self.arc_type_selector, 1)
                    set_value(self.arc_dx_spinbox, shape_dict['rel_dx'] * 100,
                              'rel_dx_conflict' in shape_dict)
                    set_value(self.arc_dy_spinbox, shape_dict['rel_dy'] * 100,
                              'rel_dy_conflict' in shape_dict)
                elif rel is not None:
                    set_value(self.arc_type_selector, 0)
                    set_value(self.arc_dx_spinbox, shape_dict['fixed_dx'],
                              'fixed_dx_conflict' in shape_dict)
                    set_value(self.arc_dy_spinbox, shape_dict['fixed_dy'],
                              'fixed_dy_conflict' in shape_dict)
            # Leaf-shaped lines or solid lines
            if shape_dict['fill']:
                if 'leaf_x' in shape_dict:
                    set_value(self.leaf_x_spinbox, shape_dict['leaf_x'],
                              'leaf_x_conflict' in shape_dict)
                    set_value(self.leaf_y_spinbox, shape_dict['leaf_y'],
                              'leaf_y_conflict' in shape_dict)
            else:
                set_value(self.thickness_spinbox, shape_dict['thickness'],
                          'thickness_conflict' in shape_dict)
        self.widget().updateGeometry()
        self.widget().update()
        self.updateGeometry()
        self.update()

    def initial_position(self):
        """


        :return:
        """
        dp = self.ui_manager.get_panel(g.EDGES)
        if dp:
            p = dp.mapToGlobal(dp.pos())
            return QtCore.QPoint(p.x() / dp.devicePixelRatio() + dp.width(), p.y() / dp.devicePixelRatio())
        else:
            return UIPanel.initial_position(self)

    def relative_curvature(self):
        """


        :return:
        """
        return self.arc_type_selector.currentData() == 'relative'


    def show_conflict(self, spinbox):
        """ Put '---' instead of value to show that there is no unambiguous value that can be put here
        (this happens when modifying several different items)
        :param spinbox:
        :return: None
        """
        spinbox.setSpecialValueText('---')
        spinbox.setValue(spinbox.minimum())

    def update_cp1(self):
        if not ctrl.selected:
            return
        elif len(ctrl.selected) == 1:
            item = ctrl.selected[0]
            if isinstance(ctrl.selected[0], Edge) and item.curve_adjustment and len(
                    item.curve_adjustment) > 0:
                set_value(self.cp1_x_spinbox, item.curve_adjustment[0][0])
                set_value(self.cp1_y_spinbox, item.curve_adjustment[0][1])
        else:
            cps = (e.curve_adjustment[0] for e in ctrl.selected if isinstance(e, Edge) and
                   e.curve_adjustment and len(e.control_points) > 0)
            x_conflict = False
            y_conflict = False
            prev_x, prev_y = 0, 0
            for x, y, z in cps:
                if prev_x and x != prev_x:
                    x_conflict = True
                prev_x = x
                if prev_y and y != prev_y:
                    y_conflict = True
                prev_y = y
                if x_conflict and y_conflict:
                    break
            set_value(self.cp1_x_spinbox, prev_x, x_conflict)
            set_value(self.cp1_y_spinbox, prev_y, y_conflict)

    def update_cp2(self):
        if not ctrl.selected:
            return
        elif len(ctrl.selected) == 1:
            item = ctrl.selected[0]
            if isinstance(ctrl.selected[0], Edge) and item.curve_adjustment and len(
                    item.curve_adjustment) > 1:
                set_value(self.cp2_x_spinbox, item.curve_adjustment[1][0])
                set_value(self.cp2_y_spinbox, item.curve_adjustment[1][1])
        else:
            cps = (e.curve_adjustment[0] for e in ctrl.selected if isinstance(e, Edge) and
                   e.curve_adjustment and len(e.control_points) > 1)
            x_conflict = False
            y_conflict = False
            prev_x, prev_y = 0, 0
            for x, y, z in cps:
                if prev_x and x != prev_x:
                    x_conflict = True
                prev_x = x
                if prev_y and y != prev_y:
                    y_conflict = True
                prev_y = y
                if x_conflict and y_conflict:
                    break
            set_value(self.cp2_x_spinbox, prev_x, x_conflict)
            set_value(self.cp2_y_spinbox, prev_y, y_conflict)

    def update_box_visibility(self, sd, selection):
        """
        :return:
        """
        cps = sd['control_points']
        # Control points
        self.cp1_box.setVisible(selection and cps > 0)
        self.cp2_box.setVisible(selection and cps > 1)
        # Relative / fixed curvature
        self.arc_box.setVisible(cps > 0)
        # Leaf-shaped lines or solid lines
        leaf = sd['fill'] and 'leaf_x' in sd
        self.leaf_box.setVisible(leaf)
        self.thickness_box.setVisible(not leaf)

    @time_me
    def build_shape_dict_for_selection(self):
        """


        :return:
        """
        d = {}
        # check if selection has conflicting values: these cannot be shown then
        shape_name = None
        keys = ['relative', 'leaf_x', 'leaf_y', 'thickness', 'rel_dx', 'rel_dy', 'fixed_dx', 'fixed_dy']
        for item in ctrl.selected:
            if isinstance(item, Edge):
                e = item.shape_args()
                if not d:
                    d = e.copy()
                if not shape_name:
                    shape_name = item.shape_name
                    d['shape_name'] = shape_name
                elif shape_name != item.shape_name:
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
        """


        """
        dp = self.ui_manager.get_panel(g.EDGES)
        if dp:
            dp.edge_options.setChecked(False)
        UIPanel.close(self)

    def show(self):
        """


        """
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