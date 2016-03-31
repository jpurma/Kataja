from PyQt5 import QtWidgets

from kataja.singletons import qt_prefs, ctrl
from kataja.ui_support.TwoColorButton import TwoColorButton
from kataja.ui_items.Panel import Panel

__author__ = 'purma'


class NavigationPanel(Panel):
    """ Switch between trees or derivation steps """

    def __init__(self, name, key, default_position='bottom', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_manager: pass a dictionary where buttons from this panel will be added
        """
        Panel.__init__(self, name, key, default_position, parent, folded)
        #label_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)
        #button_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        inner = QtWidgets.QWidget()
        inner.setMinimumWidth(160)
        #inner.setMinimumWidth(220)
        #inner.setMinimumHeight(96)
        #inner.setMaximumHeight(128)
        #inner.preferred_size = QtCore.QSize(220, 128)
        self.watchlist = ['forest_changed']
        layout = QtWidgets.QGridLayout()

        label = QtWidgets.QLabel('Tree set', self)
        #label.setSizePolicy(label_policy)
        layout.addWidget(label, 0, 0, 1, 1)

        treeset_counter = QtWidgets.QLabel('0/0', self)
        #treeset_counter.setSizePolicy(label_policy)
        layout.addWidget(treeset_counter, 0, 1, 1, 1)
        self.treeset_counter = treeset_counter

        prev_tree = TwoColorButton(qt_prefs.left_arrow, '', self)
        # prev_tree.setIconSize(QtCore.QSize(24,24))
        #prev_tree.setSizePolicy(button_policy)
        prev_tree.setMinimumWidth(72)
        # prev_tree.setMinimumHeight(32)
        layout.addWidget(prev_tree, 1, 0, 1, 1)
        self.prev_tree = prev_tree
        ui = self.ui_manager
        ui.connect_element_to_action(prev_tree, ui.qt_actions['prev_forest'])
        # prev_tree.setDefaultAction(ui_manager.qt_actions['prev_forest'])

        next_tree = TwoColorButton(qt_prefs.right_arrow, '', self)
        # next_tree.setIconSize(QtCore.QSize(24,24))
        #next_tree.setSizePolicy(button_policy)
        next_tree.setMinimumWidth(72)
        # next_tree.setMinimumHeight(32)
        layout.addWidget(next_tree, 1, 1, 1, 1)
        self.next_tree = next_tree
        ui.connect_element_to_action(next_tree, ui.qt_actions['next_forest'])
        # next_tree.setDefaultAction(ui_manager.qt_actions['next_forest'])

        self.der_label = QtWidgets.QLabel('Derivation step', self)
        #label.setSizePolicy(label_policy)
        layout.addWidget(self.der_label, 2, 0, 1, 1)

        derivation_counter = QtWidgets.QLabel('0/0', self)
        #derivation_counter.setSizePolicy(label_policy)
        layout.addWidget(derivation_counter, 2, 1, 1, 1)
        self.derivation_counter = derivation_counter

        prev_der = TwoColorButton(qt_prefs.left_arrow, '', self)
        #prev_der.setSizePolicy(label_policy)
        layout.addWidget(prev_der, 3, 0, 1, 1)
        self.prev_der = prev_der
        prev_der.clicked.connect(ui.qt_actions['prev_derivation_step'].triggered)

        next_der = TwoColorButton(qt_prefs.right_arrow, '', self)
        #next_der.setSizePolicy(label_policy)
        layout.addWidget(next_der, 3, 1, 1, 1)
        self.next_der = next_der
        #layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        inner.setLayout(layout)
        if True: #ctrl.forest.supports_derivation:
            self.der_label.hide()
            self.derivation_counter.hide()
            self.next_der.hide()
            self.prev_der.hide()
        #self.preferred_size = inner.preferred_size
        self.setWidget(inner)
        self.widget().setAutoFillBackground(True)
        self.finish_init()

    def update_tree_counter(self):
        keeper = ctrl.main.forest_keeper
        if keeper is not None:
            display_index = keeper.current_index + 1  # indexes start at 0, we want to display 1
            max_index = len(keeper.forests)
            self.treeset_counter.setText('%s/%s' % (display_index, max_index))

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
        if signal == 'forest_changed':
            self.update_tree_counter()
