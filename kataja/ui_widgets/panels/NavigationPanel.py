from PyQt5 import QtWidgets

from kataja.singletons import qt_prefs, ctrl
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.PushButtonBase import PushButtonBase
from kataja.ui_widgets.buttons.TwoColorButton import TwoColorButton
from kataja.ui_widgets.KatajaSpinbox import KatajaSpinbox

__author__ = 'purma'


class NavigationPanel(Panel):
    """ Switch between trees or derivation steps """

    def __init__(self, name, default_position='bottom', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be
        automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        Panel.__init__(self, name, default_position, parent, folded)
        inner = QtWidgets.QWidget()
        inner.setMaximumHeight(140)
        inner.setMinimumWidth(160)
        inner.setMaximumWidth(220)
        self.watchlist = ['forest_changed']
        layout = QtWidgets.QGridLayout()

        label = QtWidgets.QLabel('Tree set', self)
        layout.addWidget(label, 0, 0, 1, 1)
        hlayout = QtWidgets.QHBoxLayout()
        self.current_treeset = KatajaSpinbox(parent=self, range_min=1, range_max=5, wrapping=True,
                                             action='jump_to_forest').to_layout(hlayout)
        self.current_treeset.setKeyboardTracking(False)
        self.treeset_counter = QtWidgets.QLabel('0', self)
        hlayout.addWidget(self.treeset_counter)

        layout.addLayout(hlayout, 0, 1, 1, 1)

        action = ctrl.ui.get_action('previous_forest')
        self.prev_tree = TwoColorButton(text='Previous', bitmaps=qt_prefs.left_arrow, parent=self,
                                        action=action)
        self.prev_tree.setMinimumWidth(72)
        layout.addWidget(self.prev_tree, 1, 0, 1, 1)

        action = ctrl.ui.get_action('next_forest')
        self.next_tree = TwoColorButton(text='Next', bitmaps=qt_prefs.right_arrow, parent=self,
                                        action=action)
        self.next_tree.setMinimumWidth(72)
        layout.addWidget(self.next_tree, 1, 1, 1, 1)

        new_tree = PushButtonBase(parent=self, text='New forest', action='new_forest')
        layout.addWidget(new_tree, 3, 0)

        self.der_label = QtWidgets.QLabel('Derivation step', self)
        layout.addWidget(self.der_label, 2, 0, 1, 1)

        derivation_counter = QtWidgets.QLabel('0/0', self)
        layout.addWidget(derivation_counter, 2, 1, 1, 1)
        self.derivation_counter = derivation_counter

        action = ctrl.ui.get_action('prev_derivation_step')
        self.prev_der = TwoColorButton(text='Previous', bitmaps=qt_prefs.down_arrow, parent=self,
                                       action=action)
        self.prev_der.setMaximumHeight(20)
        layout.addWidget(self.prev_der, 3, 0, 1, 1)

        action = ctrl.ui.get_action('next_derivation_step')
        self.next_der = TwoColorButton(text='Next', bitmaps=qt_prefs.up_arrow, parent=self,
                                       action=action)
        self.next_der.setMaximumHeight(20)
        layout.addWidget(self.next_der, 3, 1, 1, 1)
        inner.setLayout(layout)
        if False:  # ctrl.forest.supports_derivation:
            self.der_label.hide()
            self.derivation_counter.hide()
            self.next_der.hide()
            self.prev_der.hide()
        self.setWidget(inner)
        self.widget().setAutoFillBackground(True)
        self.finish_init()

    def update_tree_counter(self):
        keeper = ctrl.main.document
        if keeper is not None:
            display_index = keeper.current_index + 1  # indexes start at 0, we want to display 1
            max_index = len(keeper.forests)
            self.current_treeset.setMaximum(max_index)
            self.treeset_counter.setText('/ %s' % max_index)
            dm = ctrl.forest.derivation_steps
            if dm:
                max_der_step = len(dm.derivation_steps)
                der_step = dm.derivation_step_index + 1
                self.derivation_counter.setText('%s/%s' % (der_step, max_der_step))

    def showEvent(self, event):
        """ Panel may have missed signals to update its contents when it was hidden: update all
        that signals would update.
        :param event:
        :return:
        """
        self.update_tree_counter()
        super().showEvent(event)

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
