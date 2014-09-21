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
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        inner = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout()
        layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        #layout.setContentsMargins(4, 4, 4, 4)
        hlayout = QtWidgets.QHBoxLayout()
        cp1_x_label = QtWidgets.QLabel('Arc adjust 1: X', self)
        self.cp1_x_spinbox = QtWidgets.QSpinBox()
        cp1_x_label.setBuddy(self.cp1_x_spinbox)
        cp1_y_label = QtWidgets.QLabel('Y', self)
        self.cp1_y_spinbox = QtWidgets.QSpinBox()
        cp1_y_label.setBuddy(self.cp1_y_spinbox)

        hlayout.addWidget(cp1_x_label)
        hlayout.addWidget(self.cp1_x_spinbox)
        hlayout.addWidget(cp1_y_label)
        hlayout.addWidget(self.cp1_y_spinbox)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        cp2_x_label = QtWidgets.QLabel('Arc adjust 2: X', self)
        self.cp2_x_spinbox = QtWidgets.QSpinBox()
        cp2_x_label.setBuddy(self.cp2_x_spinbox)
        cp2_y_label = QtWidgets.QLabel('Y', self)
        self.cp2_y_spinbox = QtWidgets.QSpinBox()
        cp2_y_label.setBuddy(self.cp2_y_spinbox)

        hlayout.addWidget(cp2_x_label)
        hlayout.addWidget(self.cp2_x_spinbox)
        hlayout.addWidget(cp2_y_label)
        hlayout.addWidget(self.cp2_y_spinbox)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        leaf_x_label = QtWidgets.QLabel('Leaf thickness: X', self)
        self.leaf_x_spinbox = QtWidgets.QSpinBox()
        leaf_x_label.setBuddy(self.leaf_x_spinbox)
        leaf_y_label = QtWidgets.QLabel('Y', self)
        self.leaf_y_spinbox = QtWidgets.QSpinBox()
        leaf_y_label.setBuddy(self.leaf_y_spinbox)

        hlayout.addWidget(leaf_x_label)
        hlayout.addWidget(self.leaf_x_spinbox)
        hlayout.addWidget(leaf_y_label)
        hlayout.addWidget(self.leaf_y_spinbox)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        rel_dx_label = QtWidgets.QLabel('Relative arc: X', self)
        self.rel_dx_spinbox = QtWidgets.QDoubleSpinBox()
        rel_dx_label.setBuddy(self.rel_dx_spinbox)
        rel_dy_label = QtWidgets.QLabel('Y', self)
        self.rel_dy_spinbox = QtWidgets.QDoubleSpinBox()
        rel_dy_label.setBuddy(self.rel_dy_spinbox)

        hlayout.addWidget(rel_dx_label)
        hlayout.addWidget(self.rel_dx_spinbox)
        hlayout.addWidget(rel_dy_label)
        hlayout.addWidget(self.rel_dy_spinbox)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        fixed_dx_label = QtWidgets.QLabel('Fixed arc: X', self)
        self.fixed_dx_spinbox = QtWidgets.QDoubleSpinBox()
        fixed_dx_label.setBuddy(self.fixed_dx_spinbox)
        fixed_dy_label = QtWidgets.QLabel('Y', self)
        self.fixed_dy_spinbox = QtWidgets.QDoubleSpinBox()
        fixed_dy_label.setBuddy(self.fixed_dy_spinbox)

        hlayout.addWidget(fixed_dx_label)
        hlayout.addWidget(self.fixed_dx_spinbox)
        hlayout.addWidget(fixed_dy_label)
        hlayout.addWidget(self.fixed_dy_spinbox)
        layout.addLayout(hlayout)


        hlayout = QtWidgets.QHBoxLayout()
        thickness_label = QtWidgets.QLabel('Thickness: ', self)
        self.thickness_spinbox = QtWidgets.QSpinBox()
        thickness_label.setBuddy(self.thickness_spinbox)

        hlayout.addWidget(thickness_label)
        hlayout.addWidget(self.thickness_spinbox)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        asymmetry_label = QtWidgets.QLabel('Edge asymmetry: ', self)
        self.asymmetry_checkbox = QtWidgets.QCheckBox()
        asymmetry_label.setBuddy(self.asymmetry_checkbox)

        hlayout.addWidget(asymmetry_label)
        hlayout.addWidget(self.asymmetry_checkbox)
        layout.addLayout(hlayout)


        inner.setLayout(layout)
        self.setWidget(inner)
        self.finish_init()





