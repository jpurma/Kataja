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

    def __init__(self, name, key, default_position='float', parent=None, ui_manager=None, folded=False):
        """
        BUild all advanced line options. Then in update filter what to show based on the line type.

        All of the panel constructors follow the same format so that the construction can be automated:
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        inner = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout()
        #layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)

        # Control point 1 adjustment
        self.cp1_box = QtWidgets.QWidget(inner)
        cp1_layout = QtWidgets.QHBoxLayout()
        cp1_label = QtWidgets.QLabel('Arc adjust 1', self)
        cp1_x_label = QtWidgets.QLabel('X', self)
        cp1_x_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.cp1_x_spinbox = QtWidgets.QSpinBox()
        cp1_x_label.setBuddy(self.cp1_x_spinbox)
        cp1_y_label = QtWidgets.QLabel('Y', self)
        cp1_y_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.cp1_y_spinbox = QtWidgets.QSpinBox()
        cp1_y_label.setBuddy(self.cp1_y_spinbox)
        cp1_layout.addWidget(cp1_label)
        cp1_layout.addWidget(cp1_x_label)
        cp1_layout.addWidget(self.cp1_x_spinbox)
        cp1_layout.addWidget(cp1_y_label)
        cp1_layout.addWidget(self.cp1_y_spinbox)
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
        cp2_x_label.setBuddy(self.cp2_x_spinbox)
        cp2_y_label = QtWidgets.QLabel('Y', self)
        cp2_y_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.cp2_y_spinbox = QtWidgets.QSpinBox()
        cp2_y_label.setBuddy(self.cp2_y_spinbox)
        cp2_layout.addWidget(cp2_label)
        cp2_layout.addWidget(cp2_x_label)
        cp2_layout.addWidget(self.cp2_x_spinbox)
        cp2_layout.addWidget(cp2_y_label)
        cp2_layout.addWidget(self.cp2_y_spinbox)
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
        leaf_x_label.setBuddy(self.leaf_x_spinbox)
        leaf_y_label = QtWidgets.QLabel('Y', self)
        leaf_y_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.leaf_y_spinbox = QtWidgets.QSpinBox()
        leaf_y_label.setBuddy(self.leaf_y_spinbox)
        leaf_layout.addWidget(leaf_label)
        leaf_layout.addWidget(leaf_x_label)
        leaf_layout.addWidget(self.leaf_x_spinbox)
        leaf_layout.addWidget(leaf_y_label)
        leaf_layout.addWidget(self.leaf_y_spinbox)
        leaf_layout.setContentsMargins(0, 0, 0, 0)
        self.leaf_box.setLayout(leaf_layout)
        layout.addWidget(self.leaf_box)

        # Relative arc
        self.rel_box = QtWidgets.QWidget(inner)
        rel_layout = QtWidgets.QHBoxLayout()
        rel_label = QtWidgets.QLabel('Relative arc', self)
        rel_dx_label = QtWidgets.QLabel('X', self)
        rel_dx_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.rel_dx_spinbox = QtWidgets.QDoubleSpinBox()
        rel_dx_label.setBuddy(self.rel_dx_spinbox)
        rel_dy_label = QtWidgets.QLabel('Y', self)
        rel_dy_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.rel_dy_spinbox = QtWidgets.QDoubleSpinBox()
        rel_dy_label.setBuddy(self.rel_dy_spinbox)
        rel_layout.addWidget(rel_label)
        rel_layout.addWidget(rel_dx_label)
        rel_layout.addWidget(self.rel_dx_spinbox)
        rel_layout.addWidget(rel_dy_label)
        rel_layout.addWidget(self.rel_dy_spinbox)
        rel_layout.setContentsMargins(0, 0, 0, 0)
        self.rel_box.setLayout(rel_layout)
        layout.addWidget(self.rel_box)

        # Fixed arc
        self.fixed_box = QtWidgets.QWidget(inner)
        fixed_layout = QtWidgets.QHBoxLayout()
        fixed_label = QtWidgets.QLabel('Fixed arc', self)
        fixed_dx_label = QtWidgets.QLabel('X', self)
        fixed_dx_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self.fixed_dx_spinbox = QtWidgets.QDoubleSpinBox()
        fixed_dx_label.setBuddy(self.fixed_dx_spinbox)
        fixed_dy_label = QtWidgets.QLabel('Y', self)
        self.fixed_dy_spinbox = QtWidgets.QDoubleSpinBox()
        fixed_dy_label.setBuddy(self.fixed_dy_spinbox)
        fixed_dy_label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        fixed_layout.addWidget(fixed_label)
        fixed_layout.addWidget(fixed_dx_label)
        fixed_layout.addWidget(self.fixed_dx_spinbox)
        fixed_layout.addWidget(fixed_dy_label)
        fixed_layout.addWidget(self.fixed_dy_spinbox)
        fixed_layout.setContentsMargins(0, 0, 0, 0)
        self.fixed_box.setLayout(fixed_layout)
        layout.addWidget(self.fixed_box)

        # Line thickness
        self.thickness_box = QtWidgets.QWidget(inner)
        thickness_layout = QtWidgets.QHBoxLayout()
        thickness_label = QtWidgets.QLabel('Thickness', self)
        self.thickness_spinbox = QtWidgets.QSpinBox()
        thickness_label.setBuddy(self.thickness_spinbox)
        thickness_layout.addWidget(thickness_label)
        thickness_layout.addWidget(self.thickness_spinbox)
        thickness_layout.setContentsMargins(0, 0, 0, 0)
        self.thickness_box.setLayout(thickness_layout)
        layout.addWidget(self.thickness_box)

        # Edges drawn as asymmetric
        self.asymmetry_box = QtWidgets.QWidget(inner)
        asymmetry_layout = QtWidgets.QHBoxLayout()
        asymmetry_label = QtWidgets.QLabel('Edge asymmetry', self)
        self.asymmetry_checkbox = QtWidgets.QCheckBox()
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
        d = None
        cps = 0
        filled = False
        if scope == g.SELECTION:
            # check if selection has conflicting values: these cannot be shown then
            shape_name_conflict = False
            shape_name = None
            for item in ctrl.get_all_selected():
                if isinstance(item, Edge):
                    if not shape_name:
                        shape_name = item.shape_name()
                    elif shape_name != item.shape_name():
                        shape_name_conflict = True
                        break
            if shape_name:
                d = SHAPE_PRESETS[shape_name]
                cps = d.get('control_points', 0)
        else: # Adjusting how this relation type is drawn
            e = ctrl.forest.settings.edge_settings
            shape_name = e(scope, 'shape_name')
            filled = e(scope, 'fill', False)
            d = ctrl.forest.settings.edge_shape_settings(scope)
            print('necessary settings for this edge: ', d)
            #d = SHAPE_PRESETS[shape_name]
        if d:
            # Control points
            if cps == 2:
                self.cp1_box.setVisible(True)
                self.cp2_box.setVisible(True)
            elif cps == 1:
                self.cp1_box.setVisible(True)
                self.cp2_box.setVisible(False)
            else:
                self.cp1_box.setVisible(False)
                self.cp2_box.setVisible(False)
            # Relative / fixed curvature
            if cps > 0:
                self.rel_box.setVisible(True)
                self.fixed_box.setVisible(True)
            else:
                self.rel_box.setVisible(False)
                self.fixed_box.setVisible(False)
            # Leaf-shaped lines or solid lines
            if filled:
                self.leaf_box.setVisible(True)
                self.thickness_box.setVisible(False)
            else:
                self.leaf_box.setVisible(False)
                self.thickness_box.setVisible(True)



        else: # This shouldn't happen
            self.cp1_box.setVisible(False)
            self.cp2_box.setVisible(False)
            self.leaf_layout.setEnabled(False)
        self.updateGeometry()
        self.update()

    def initial_position(self):
        dp = self.ui_manager.get_panel(g.DRAWING)
        if dp:
            p = dp.mapToGlobal(dp.pos())
            return QtCore.QPoint(p.x() / dp.devicePixelRatio() + dp.width(), p.y() / dp.devicePixelRatio())
        else:
            return UIPanel.initial_position(self)

