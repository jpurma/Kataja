from PyQt5 import QtWidgets

from kataja.singletons import qt_prefs, ctrl
from kataja.ui_support.TwoColorButton import TwoColorButton
from kataja.ui_support.panel_utils import text_button
from kataja.ui_widgets.Panel import Panel
import kataja.globals as g

__author__ = 'purma'


class NavigationPanel(Panel):
    """ Switch between trees or derivation steps """

    def __init__(self, name, default_position='bottom', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        Panel.__init__(self, name, default_position, parent, folded)
        inner = QtWidgets.QWidget()
        inner.setMinimumWidth(160)
        self.watchlist = ['forest_changed']
        layout = QtWidgets.QGridLayout()

        label = QtWidgets.QLabel('Tree set', self)
        layout.addWidget(label, 0, 0, 1, 1)

        treeset_counter = QtWidgets.QLabel('0/0', self)
        layout.addWidget(treeset_counter, 0, 1, 1, 1)
        self.treeset_counter = treeset_counter

        prev_tree = TwoColorButton(qt_prefs.left_arrow, '', self)
        prev_tree.setMinimumWidth(72)
        layout.addWidget(prev_tree, 1, 0, 1, 1)
        self.prev_tree = prev_tree
        ui = self.ui_manager
        ui.connect_element_to_action(prev_tree, 'previous_forest')

        next_tree = TwoColorButton(qt_prefs.right_arrow, '', self)
        next_tree.setMinimumWidth(72)
        layout.addWidget(next_tree, 1, 1, 1, 1)
        self.next_tree = next_tree
        ui.connect_element_to_action(next_tree, 'next_forest')

        new_tree = text_button(ui, layout, text='New forest', action='new_forest', x=0, y=3)

        self.der_label = QtWidgets.QLabel('Derivation step', self)
        layout.addWidget(self.der_label, 2, 0, 1, 1)

        derivation_counter = QtWidgets.QLabel('0/0', self)
        layout.addWidget(derivation_counter, 2, 1, 1, 1)
        self.derivation_counter = derivation_counter

        prev_der = TwoColorButton(qt_prefs.left_arrow, '', self)
        layout.addWidget(prev_der, 3, 0, 1, 1)
        self.prev_der = prev_der
        ui.connect_element_to_action(prev_der, 'prev_derivation_step')

        next_der = TwoColorButton(qt_prefs.right_arrow, '', self)
        layout.addWidget(next_der, 3, 1, 1, 1)
        self.next_der = next_der
        ui.connect_element_to_action(next_der, 'next_derivation_step')
        inner.setLayout(layout)
        if False: #ctrl.forest.supports_derivation:
            self.der_label.hide()
            self.derivation_counter.hide()
            self.next_der.hide()
            self.prev_der.hide()
        self.setWidget(inner)
        self.widget().setAutoFillBackground(True)
        self.finish_init()

    def update_tree_counter(self):
        keeper = ctrl.main.forest_keeper
        if keeper is not None:
            display_index = keeper.current_index + 1  # indexes start at 0, we want to display 1
            max_index = len(keeper.forests)
            self.treeset_counter.setText('%s/%s' % (display_index, max_index))
            dm = ctrl.forest.derivation_steps
            if dm:
                max_der_step = len(dm.derivation_steps)
                der_step = dm.derivation_step_index + 1
                self.derivation_counter.setText('%s/%s' % (der_step, max_der_step))

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
