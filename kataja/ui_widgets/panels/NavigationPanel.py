from PyQt5 import QtWidgets

from kataja.singletons import qt_prefs, ctrl
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.PushButtonBase import PushButtonBase
from kataja.ui_widgets.buttons.TwoColorButton import TwoColorButton
from kataja.ui_widgets.KatajaSpinbox import KatajaSpinbox
from kataja.ui_support.panel_utils import box_row

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
        inner = self.widget()
        inner.setMaximumHeight(140)
        inner.setMinimumWidth(160)
        inner.setMaximumWidth(220)
        inner.setAutoFillBackground(True)
        self.watchlist = ['forest_changed']
        layout = self.vlayout
        # self.new_tree = PushButtonBase(parent=self, text='New forest', action='new_forest'
        #                               ).to_layout(layout)

        hlayout = box_row(layout)
        self.current_treeset = KatajaSpinbox(
            parent=self, range_min=1, range_max=5, wrapping=True, action='jump_to_forest'
        ).to_layout(hlayout, with_label='Tree set')
        self.current_treeset.setKeyboardTracking(False)
        self.treeset_counter = QtWidgets.QLabel('0', self)
        hlayout.addWidget(self.treeset_counter)

        hlayout = box_row(layout)
        action = ctrl.ui.get_action('previous_forest')
        self.prev_tree = TwoColorButton(text='Previous', bitmaps=qt_prefs.left_arrow, parent=self,
                                        action=action).to_layout(hlayout)
        self.prev_tree.setMinimumWidth(72)
        action = ctrl.ui.get_action('next_forest')
        self.next_tree = TwoColorButton(text='Next', bitmaps=qt_prefs.right_arrow, parent=self,
                                        action=action).to_layout(hlayout)
        self.next_tree.setMinimumWidth(72)

        hlayout = box_row(layout)
        self.current_derivation = KatajaSpinbox(
            parent=self, range_min=1, range_max=5,
            wrapping=True,
            action='jump_to_derivation').to_layout(hlayout, with_label='Derivation step')
        self.current_derivation.setKeyboardTracking(False)
        self.derivation_counter = QtWidgets.QLabel('0', self)
        hlayout.addWidget(self.derivation_counter)

        hlayout = box_row(layout)
        action = ctrl.ui.get_action('prev_derivation_step')
        self.prev_der = TwoColorButton(text='Previous', bitmaps=qt_prefs.down_arrow, parent=self,
                                       action=action).to_layout(hlayout)
        self.prev_der.setMaximumHeight(20)

        action = ctrl.ui.get_action('next_derivation_step')
        self.next_der = TwoColorButton(text='Next', bitmaps=qt_prefs.up_arrow, parent=self,
                                       action=action).to_layout(hlayout)
        self.next_der.setMaximumHeight(20)
        self.finish_init()

    def update_tree_counter(self):
        keeper = ctrl.main.document
        if keeper is not None:
            max_index = len(keeper.forests)
            self.current_treeset.setMaximum(max_index)
            self.treeset_counter.setText('/ %s' % max_index)
            dm = ctrl.forest.derivation_steps
            if dm:
                max_der_step = len(dm.derivation_steps)
                self.current_derivation.setMaximum(max_der_step)
                self.derivation_counter.setText('/ %s' % (max_der_step))

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
