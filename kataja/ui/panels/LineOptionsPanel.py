from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QRect, QSize
from PyQt5.QtGui import QIcon, QColor, QPixmap, QStandardItem

from kataja.Edge import SHAPE_PRESETS, Edge
from kataja.singletons import ctrl, qt_prefs
import kataja.globals as g
from kataja.ui.panels.UIPanel import UIPanel


__author__ = 'purma'



class LineOptionsPanel(UIPanel):
    """ Panel for editing how edges and nodes are drawn. """

    def __init__(self, name, key, default_position='float', parent=None, ui_manager=None, folded=False, closed=False):
        """
        BUild all advanced line options. Then in update filter what to show based on the line type.

        All of the panel constructors follow the same format so that the construction can be automated:
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, key, default_position, parent, ui_manager, folded, closed)
        inner = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout()
        layout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding))

        # Control point 1 adjustment
        self.cp1_box = QtWidgets.QWidget(inner)
        cp1_layout = QtWidgets.QHBoxLayout()
        cp1_label = QtWidgets.QLabel('Arc adjust 1', self)
        cp1_x_label = QtWidgets.QLabel('X', self)
        cp1_x_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.cp1_x_spinbox = QtWidgets.QSpinBox()
        self.cp1_x_spinbox.setRange(-400, 400)
        ui_manager.connect_element_to_action(self.cp1_x_spinbox, 'control_point1_x')
        cp1_x_label.setBuddy(self.cp1_x_spinbox)
        cp1_y_label = QtWidgets.QLabel('Y', self)
        cp1_y_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.cp1_y_spinbox = QtWidgets.QSpinBox()
        self.cp1_y_spinbox.setRange(-400, 400)
        ui_manager.connect_element_to_action(self.cp1_y_spinbox, 'control_point1_y')
        cp1_y_label.setBuddy(self.cp1_y_spinbox)
        self.cp1_reset_button = QtWidgets.QPushButton('Reset')
        self.cp1_reset_button.setMinimumSize(QSize(40, 20))
        self.cp1_reset_button.setMaximumSize(QSize(40, 20))
        ui_manager.connect_element_to_action(self.cp1_reset_button, 'control_point1_reset')
        cp1_layout.addWidget(cp1_label)
        cp1_layout.addWidget(cp1_x_label)
        cp1_layout.addWidget(self.cp1_x_spinbox)
        cp1_layout.addWidget(cp1_y_label)
        cp1_layout.addWidget(self.cp1_y_spinbox)
        cp1_layout.addWidget(self.cp1_reset_button)
        cp1_layout.setContentsMargins(0, 0, 0, 0)
        self.cp1_box.setLayout(cp1_layout)
        layout.addWidget(self.cp1_box)

        # Control point 1 adjustment
        self.cp2_box = QtWidgets.QWidget(inner)
        cp2_layout = QtWidgets.QHBoxLayout()
        cp2_label = QtWidgets.QLabel('Arc adjust 2', self)
        cp2_x_label = QtWidgets.QLabel('X', self)
        cp2_x_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.cp2_x_spinbox = QtWidgets.QSpinBox()
        self.cp2_x_spinbox.setRange(-400, 400)
        ui_manager.connect_element_to_action(self.cp2_x_spinbox, 'control_point2_x')
        cp2_x_label.setBuddy(self.cp2_x_spinbox)
        cp2_y_label = QtWidgets.QLabel('Y', self)
        cp2_y_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.cp2_y_spinbox = QtWidgets.QSpinBox()
        self.cp2_y_spinbox.setRange(-400, 400)
        cp2_y_label.setBuddy(self.cp2_y_spinbox)
        ui_manager.connect_element_to_action(self.cp2_y_spinbox, 'control_point2_y')
        self.cp2_reset_button = QtWidgets.QPushButton('Reset')
        self.cp2_reset_button.setMinimumSize(QSize(40, 20))
        self.cp2_reset_button.setMaximumSize(QSize(40, 20))
        ui_manager.connect_element_to_action(self.cp2_reset_button, 'control_point2_reset')

        cp2_layout.addWidget(cp2_label)
        cp2_layout.addWidget(cp2_x_label)
        cp2_layout.addWidget(self.cp2_x_spinbox)
        cp2_layout.addWidget(cp2_y_label)
        cp2_layout.addWidget(self.cp2_y_spinbox)
        cp2_layout.addWidget(self.cp2_reset_button)
        cp2_layout.setContentsMargins(0, 0, 0, 0)
        self.cp2_box.setLayout(cp2_layout)
        layout.addWidget(self.cp2_box)

        # Leaf size
        self.leaf_box = QtWidgets.QWidget(inner)
        leaf_layout = QtWidgets.QHBoxLayout()
        leaf_label = QtWidgets.QLabel('Leaf thickness', self)
        leaf_x_label = QtWidgets.QLabel('X', self)
        leaf_x_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.leaf_x_spinbox = QtWidgets.QSpinBox()
        self.leaf_x_spinbox.setRange(-20, 20)
        leaf_x_label.setBuddy(self.leaf_x_spinbox)
        ui_manager.connect_element_to_action(self.leaf_x_spinbox, 'leaf_shape_x')
        leaf_y_label = QtWidgets.QLabel('Y', self)
        leaf_y_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.leaf_y_spinbox = QtWidgets.QSpinBox()
        self.leaf_y_spinbox.setRange(-20, 20)
        leaf_y_label.setBuddy(self.leaf_y_spinbox)
        ui_manager.connect_element_to_action(self.leaf_y_spinbox, 'leaf_shape_y')
        self.leaf_reset_button = QtWidgets.QPushButton('Reset')
        self.leaf_reset_button.setMinimumSize(QSize(40, 20))
        self.leaf_reset_button.setMaximumSize(QSize(40, 20))
        ui_manager.connect_element_to_action(self.leaf_reset_button, 'leaf_shape_reset')

        leaf_layout.addWidget(leaf_label)
        leaf_layout.addWidget(leaf_x_label)
        leaf_layout.addWidget(self.leaf_x_spinbox)
        leaf_layout.addWidget(leaf_y_label)
        leaf_layout.addWidget(self.leaf_y_spinbox)
        leaf_layout.addWidget(self.leaf_reset_button)
        leaf_layout.setContentsMargins(0, 0, 0, 0)
        self.leaf_box.setLayout(leaf_layout)
        layout.addWidget(self.leaf_box)

        # Curvature
        self.arc_box = QtWidgets.QWidget(inner)
        arc_layout = QtWidgets.QVBoxLayout()
        l1_layout = QtWidgets.QHBoxLayout()
        l2_layout = QtWidgets.QHBoxLayout()
        arc_label = QtWidgets.QLabel('Curvature', self)
        arc_dx_label = QtWidgets.QLabel('X', self)
        arc_dx_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.arc_dx_spinbox = QtWidgets.QSpinBox()
        self.arc_dx_spinbox.setRange(-200, 200)
        ui_manager.connect_element_to_action(self.arc_dx_spinbox, 'edge_curvature_x')
        arc_dx_label.setBuddy(self.arc_dx_spinbox)
        self.arc_type_selector = QtWidgets.QComboBox(self)
        self.arc_type_selector.addItems(['pt', '%'])
        self.arc_type_selector.setItemData(0, 'fixed')
        self.arc_type_selector.setItemData(1, 'relative')
        self.arc_type_selector.setMinimumSize(QSize(40, 20))
        self.arc_type_selector.setMaximumSize(QSize(40, 20))
        ui_manager.connect_element_to_action(self.arc_type_selector, 'edge_curvature_type')

        arc_dy_label = QtWidgets.QLabel('Y', self)
        arc_dy_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.arc_dy_spinbox = QtWidgets.QSpinBox()
        self.arc_dy_spinbox.setRange(-200, 200)
        ui_manager.connect_element_to_action(self.arc_dy_spinbox, 'edge_curvature_y')
        arc_dy_label.setBuddy(self.arc_dy_spinbox)
        self.arc_reset_button = QtWidgets.QPushButton('Reset curvature')
        #self.arc_reset_button.setMinimumSize(QSize(40, 20))
        #self.arc_reset_button.setMaximumSize(QSize(40, 20))
        ui_manager.connect_element_to_action(self.arc_reset_button, 'edge_curvature_reset')

        l1_layout.addWidget(arc_label)
        l1_layout.addWidget(arc_dx_label)
        l1_layout.addWidget(self.arc_dx_spinbox)
        l1_layout.addWidget(arc_dy_label)
        l1_layout.addWidget(self.arc_dy_spinbox)
        l1_layout.addWidget(self.arc_type_selector)
        l2_layout.addWidget(self.arc_reset_button)
        l2_layout.setAlignment(self.arc_reset_button, QtCore.Qt.AlignRight)
        l1_layout.setContentsMargins(0, 0, 0, 0)
        l2_layout.setContentsMargins(0, 0, 0, 0)
        arc_layout.setContentsMargins(0, 0, 0, 0)
        arc_layout.addLayout(l1_layout)
        arc_layout.addLayout(l2_layout)
        self.arc_box.setLayout(arc_layout)
        layout.addWidget(self.arc_box)

        # Line thickness
        self.thickness_box = QtWidgets.QWidget(inner)
        thickness_layout = QtWidgets.QHBoxLayout()
        thickness_label = QtWidgets.QLabel('Thickness', self)
        self.thickness_spinbox = QtWidgets.QDoubleSpinBox()
        self.thickness_spinbox.setRange(0.0, 10.0)
        self.thickness_spinbox.setSingleStep(0.1)
        ui_manager.connect_element_to_action(self.thickness_spinbox, 'edge_thickness')
        thickness_label.setBuddy(self.thickness_spinbox)
        self.thickness_reset_button = QtWidgets.QPushButton('Reset')
        ui_manager.connect_element_to_action(self.thickness_reset_button, 'edge_thickness_reset')
        thickness_layout.addWidget(thickness_label)
        thickness_layout.addWidget(self.thickness_spinbox)
        thickness_layout.addWidget(self.thickness_reset_button)
        thickness_layout.setContentsMargins(0, 0, 0, 0)
        self.thickness_box.setLayout(thickness_layout)
        layout.addWidget(self.thickness_box)

        # Edges drawn as asymmetric
        self.asymmetry_box = QtWidgets.QWidget(inner)
        asymmetry_layout = QtWidgets.QHBoxLayout()
        asymmetry_label = QtWidgets.QLabel('Edge asymmetry', self)
        self.asymmetry_checkbox = QtWidgets.QCheckBox()
        ui_manager.connect_element_to_action(self.asymmetry_checkbox, 'edge_asymmetry')

        asymmetry_label.setBuddy(self.asymmetry_checkbox)
        asymmetry_layout.addWidget(asymmetry_label)
        asymmetry_layout.addWidget(self.asymmetry_checkbox)
        asymmetry_layout.setContentsMargins(0, 0, 0, 0)
        self.asymmetry_box.setLayout(asymmetry_layout)
        layout.addWidget(self.asymmetry_box)

        inner.setLayout(layout)
        self.setWidget(inner)
        self.finish_init()

    def update_panel(self):
        """ Choose which selectors to show and update their values
        :return: None
        """
        scope = ctrl.ui.get_panel(g.DRAWING).scope
        shape_dict = None
        if scope == g.SELECTION:
            shape_dict = self.build_shape_dict_for_selection()
            self.update_control_point_spinboxes()
            selection = True
        else: # Adjusting how this relation type is drawn
            shape_dict = ctrl.forest.settings.edge_shape_settings(scope)
            #print('shape settings: ', shape_dict)
            selection = False
        if shape_dict:
            cps = shape_dict['control_points']

            # Control points
            if selection and cps > 1:
                self.cp2_box.setVisible(True)
            else:
                self.cp2_box.setVisible(False)
            if selection and cps > 0:
                self.cp1_box.setVisible(True)
            else:
                self.cp1_box.setVisible(False)
            # Relative / fixed curvature
            if cps > 0:
                self.arc_box.setVisible(True)
                rel = shape_dict.get('relative', None)
                self.arc_type_selector.blockSignals(True)
                self.arc_dx_spinbox.blockSignals(True)
                self.arc_dy_spinbox.blockSignals(True)
                if rel:
                    self.arc_type_selector.setCurrentIndex(1)
                    self.arc_dx_spinbox.setValue(shape_dict['rel_dx'] * 100)
                    self.arc_dy_spinbox.setValue(shape_dict['rel_dy'] * 100)
                    if 'rel_dx_conflict' in shape_dict:
                        self.add_and_select_ambiguous_marker(self.arc_dx_spinbox)
                    else:
                        self.remove_ambiguous_marker(self.arc_dx_spinbox)
                    if 'rel_dy_conflict' in shape_dict:
                        self.add_and_select_ambiguous_marker(self.arc_dy_spinbox)
                    else:
                        self.remove_ambiguous_marker(self.arc_dy_spinbox)
                elif rel is not None:
                    self.arc_type_selector.setCurrentIndex(0)
                    self.arc_dx_spinbox.setValue(shape_dict['fixed_dx'])
                    self.arc_dy_spinbox.setValue(shape_dict['fixed_dy'])
                    if 'fixed_dx_conflict' in shape_dict:
                        self.add_and_select_ambiguous_marker(self.arc_dx_spinbox)
                    else:
                        self.remove_ambiguous_marker(self.arc_dx_spinbox)
                    if 'fixed_dy_conflict' in shape_dict:
                        self.add_and_select_ambiguous_marker(self.arc_dy_spinbox)
                    else:
                        self.remove_ambiguous_marker(self.arc_dy_spinbox)
                self.arc_type_selector.blockSignals(False)
                self.arc_dx_spinbox.blockSignals(False)
                self.arc_dy_spinbox.blockSignals(False)
            else:
                self.arc_box.setVisible(False)
            # Leaf-shaped lines or solid lines
            if shape_dict['fill']:
                if 'leaf_x' in shape_dict:
                    self.leaf_box.setVisible(True)
                    self.leaf_x_spinbox.blockSignals(True)
                    self.leaf_y_spinbox.blockSignals(True)
                    self.leaf_x_spinbox.setValue(shape_dict['leaf_x'])
                    self.leaf_y_spinbox.setValue(shape_dict['leaf_y'])
                    if 'leaf_x_conflict' in shape_dict:
                        self.add_and_select_ambiguous_marker(self.leaf_x_spinbox)
                    else:
                        self.remove_ambiguous_marker(self.leaf_x_spinbox)
                    if 'leaf_y_conflict' in shape_dict:
                        self.add_and_select_ambiguous_marker(self.leaf_y_spinbox)
                    else:
                        self.remove_ambiguous_marker(self.leaf_y_spinbox)

                    self.leaf_x_spinbox.blockSignals(False)
                    self.leaf_y_spinbox.blockSignals(False)
                else:
                    self.leaf_box.setVisible(False)
                self.thickness_box.setVisible(False)
            else:
                self.leaf_box.setVisible(False)
                self.thickness_box.setVisible(True)
                self.thickness_spinbox.blockSignals(True)
                self.thickness_spinbox.setValue(shape_dict['thickness'])
                if 'thickness_conflict' in shape_dict:
                    self.add_and_select_ambiguous_marker(self.thickness_spinbox)
                else:
                    self.remove_ambiguous_marker(self.thickness_spinbox)

                self.thickness_spinbox.blockSignals(False)
        else: # This shouldn't happen
            assert False
            #self.cp1_box.setVisible(False)
            #self.cp2_box.setVisible(False)
            #self.leaf_layout.setEnabled(False)
        self.widget().updateGeometry()
        self.widget().update()
        self.updateGeometry()
        self.update()

    def initial_position(self):
        dp = self.ui_manager.get_panel(g.DRAWING)
        if dp:
            p = dp.mapToGlobal(dp.pos())
            return QtCore.QPoint(p.x() / dp.devicePixelRatio() + dp.width(), p.y() / dp.devicePixelRatio())
        else:
            return UIPanel.initial_position(self)

    def relative_curvature(self):
        return self.arc_type_selector.currentData() == 'relative'


    def show_conflict(self, spinbox):
        """ Put '---' instead of value to show that there is no unambiguous value that can be put here
        (this happens when modifying several different items)
        :return: None
        """
        spinbox.setSpecialValueText('---')
        spinbox.setValue(spinbox.minimum())

    def update_control_point_spinboxes(self):
        """ Only applies to selected edges, and only if the selection doesn't have conflicting values
        :return: None
        """
        cp1_x_conflict = False
        cp2_x_conflict = False
        cp1_y_conflict = False
        cp2_y_conflict = False
        cp1_x = None
        cp1_y = None
        cp2_x = None
        cp2_y = None
        for item in ctrl.get_all_selected():
            if isinstance(item, Edge):
                if len(item.adjust) > 1:
                    if cp2_x is None:
                        cp2_x = item.adjust[1][0]
                        cp2_y = item.adjust[1][1]
                    else:
                        if cp2_x != item.adjust[1][0]:
                            cp2_x_conflict = True
                        if cp2_y != item.adjust[1][1]:
                            cp2_y_conflict = True
                if len(item.adjust) > 0:
                    if cp1_x is None:
                        cp1_x = item.adjust[0][0]
                        cp1_y = item.adjust[0][1]
                    else:
                        if cp1_x != item.adjust[0][0]:
                            cp1_x_conflict = True
                        if cp1_y != item.adjust[0][1]:
                            cp1_y_conflict = True
        self.cp1_x_spinbox.blockSignals(True)
        self.cp1_y_spinbox.blockSignals(True)
        self.cp2_x_spinbox.blockSignals(True)
        self.cp2_y_spinbox.blockSignals(True)
        if cp1_x is not None:
            self.cp1_x_spinbox.setValue(cp1_x)
            if cp1_x_conflict:
                self.add_and_select_ambiguous_marker(self.cp1_x_spinbox)
            else:
                self.remove_ambiguous_marker(self.cp1_x_spinbox)
        if cp1_y is not None:
            self.cp1_y_spinbox.setValue(cp1_y)
            if cp1_y_conflict:
                self.add_and_select_ambiguous_marker(self.cp1_y_spinbox)
            else:
                self.remove_ambiguous_marker(self.cp1_y_spinbox)
        if cp2_x is not None:
            self.cp2_x_spinbox.setValue(cp2_x)
            if cp2_x_conflict:
                self.add_and_select_ambiguous_marker(self.cp2_x_spinbox)
            else:
                self.remove_ambiguous_marker(self.cp2_x_spinbox)
        if cp2_y is not None:
            self.cp2_y_spinbox.setValue(cp2_y)
            if cp2_y_conflict:
                self.add_and_select_ambiguous_marker(self.cp2_y_spinbox)
            else:
                self.remove_ambiguous_marker(self.cp2_y_spinbox)
        self.cp1_x_spinbox.blockSignals(False)
        self.cp1_y_spinbox.blockSignals(False)
        self.cp2_x_spinbox.blockSignals(False)
        self.cp2_y_spinbox.blockSignals(False)



    def build_shape_dict_for_selection(self):
        d = {}
        # check if selection has conflicting values: these cannot be shown then
        shape_name = None
        keys = ['relative', 'leaf_x', 'leaf_y', 'thickness', 'rel_dx', 'rel_dy', 'fixed_dx', 'fixed_dy']
        for item in ctrl.get_all_selected():
            if isinstance(item, Edge):
                e = item.shape_args()
                if not d:
                    d = e.copy()
                if not shape_name:
                    shape_name = item.shape_name()
                    d['shape_name'] = shape_name
                elif shape_name != item.shape_name():
                    d['shape_name_conflict'] = True
                for key in keys:
                    old = d.get(key, None)
                    new = e.get(key, None)
                    if old is None and new is not None:
                        d[key] = new
                    elif old is not None and new is not None and old != new:
                        d[key + '_conflict'] = True
        return d