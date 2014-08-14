from PyQt5 import QtWidgets, QtCore, QtGui
from kataja.singletons import qt_prefs
from kataja.ui.TwoColorButton import TwoColorButton
from kataja.ui.UIPanel import UIPanel
from ui.TwoColorIconEngine import TwoColorIconEngine

__author__ = 'purma'


class NavigationPanel(UIPanel):
    """ Switch between trees or derivation steps """

    def __init__(self, name, default_position='bottom', parent=None, ui_buttons=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, default_position, parent, folded)
        label_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        button_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        inner = QtWidgets.QWidget()
        layout = QtWidgets.QGridLayout()

        label = QtWidgets.QLabel('Tree set', self)
        label.setSizePolicy(label_policy)
        layout.addWidget(label, 0, 0, 1, 1)

        treeset_counter = QtWidgets.QLabel('0/0', self)
        treeset_counter.setSizePolicy(label_policy)
        layout.addWidget(treeset_counter, 0, 1, 1, 1)
        ui_buttons['treeset_counter'] = treeset_counter

        prev_tree = TwoColorButton(qt_prefs.left_arrow, 'Previous', inner)
        prev_tree.setSizePolicy(button_policy)
        layout.addWidget(prev_tree, 1, 0, 1, 1)
        ui_buttons['prev_tree'] = prev_tree

        next_tree = TwoColorButton(qt_prefs.right_arrow, 'Next', self)
        next_tree.setSizePolicy(button_policy)
        layout.addWidget(next_tree, 1, 1, 1, 1)
        ui_buttons['next_tree'] = next_tree

        label = QtWidgets.QLabel('Derivation step', self)
        label.setSizePolicy(label_policy)
        layout.addWidget(label, 2, 0, 1, 1)

        derivation_counter = QtWidgets.QLabel('0/0', self)
        derivation_counter.setSizePolicy(label_policy)
        layout.addWidget(derivation_counter, 2, 1, 1, 1)
        ui_buttons['derivation_counter'] = derivation_counter

        prev_der = TwoColorButton(qt_prefs.left_arrow, 'Previous', self)
        prev_der.setSizePolicy(label_policy)
        layout.addWidget(prev_der, 3, 0, 1, 1)
        ui_buttons['prev_der'] = prev_der

        next_der = TwoColorButton(qt_prefs.right_arrow, 'Next', self)
        next_der.setSizePolicy(label_policy)
        layout.addWidget(next_der, 3, 1, 1, 1)
        ui_buttons['next_der'] = next_der
        layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        inner.setLayout(layout)
        self.setWidget(inner)
        self.widget().setAutoFillBackground(True)
        self.finish_init()
