from PyQt5 import QtWidgets

from kataja.singletons import qt_prefs, ctrl
from kataja.ui_widgets.Panel import Panel
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
        inner.setAutoFillBackground(True)
        ctrl.main.forest_changed.connect(self.update_counters)
        ctrl.main.parse_changed.connect(self.update_counters)
        layout = self.vlayout
        # self.new_tree = PushButtonBase(parent=self, text='New forest', action='new_forest'
        #                               ).to_layout(layout)

        hlayout = box_row(layout)
        self.current_treeset = KatajaSpinbox(
            parent=inner, range_min=1, range_max=5, wrapping=True, action='jump_to_forest'
        ).to_layout(hlayout, with_label='Tree set')
        self.current_treeset.setKeyboardTracking(False)
        self.treeset_counter = QtWidgets.QLabel('0', inner)
        hlayout.addWidget(self.treeset_counter)

        hlayout = box_row(layout)
        action = ctrl.ui.get_action('previous_forest')
        self.prev_tree = TwoColorButton(text='Previous', bitmaps=qt_prefs.left_arrow, parent=inner,
                                        action=action).to_layout(hlayout)
        self.prev_tree.setMinimumWidth(72)
        action = ctrl.ui.get_action('next_forest')
        self.next_tree = TwoColorButton(text='Next', bitmaps=qt_prefs.right_arrow, parent=inner,
                                        action=action).to_layout(hlayout)
        self.next_tree.setMinimumWidth(72)

        hlayout = box_row(layout)
        self.current_parse = KatajaSpinbox(
            parent=inner, range_min=1, range_max=5,
            wrapping=True,
            action='jump_to_parse').to_layout(hlayout, with_label='Parse tree')
        self.current_parse.setKeyboardTracking(False)
        self.parse_counter = QtWidgets.QLabel('0', inner)
        hlayout.addWidget(self.parse_counter)

        hlayout = box_row(layout)
        action = ctrl.ui.get_action('previous_parse')
        self.prev_parse = TwoColorButton(text='Previous', bitmaps=qt_prefs.left_arrow, parent=inner,
                                         action=action).to_layout(hlayout)
        self.prev_parse.setMaximumHeight(20)

        action = ctrl.ui.get_action('next_parse')
        self.next_parse = TwoColorButton(text='Next', bitmaps=qt_prefs.right_arrow, parent=inner,
                                         action=action).to_layout(hlayout)
        self.next_parse.setMaximumHeight(20)

        hlayout = box_row(layout)
        self.current_derivation = KatajaSpinbox(
            parent=inner, range_min=1, range_max=5,
            wrapping=True,
            action='jump_to_derivation').to_layout(hlayout, with_label='Derivation step')
        self.current_derivation.setKeyboardTracking(False)
        self.derivation_counter = QtWidgets.QLabel('0', inner)
        hlayout.addWidget(self.derivation_counter)

        hlayout = box_row(layout)
        action = ctrl.ui.get_action('prev_derivation_step')
        self.prev_der = TwoColorButton(text='Previous', bitmaps=qt_prefs.down_arrow, parent=inner,
                                       action=action).to_layout(hlayout)
        self.prev_der.setMaximumHeight(20)

        action = ctrl.ui.get_action('next_derivation_step')
        self.next_der = TwoColorButton(text='Next', bitmaps=qt_prefs.up_arrow, parent=inner,
                                       action=action).to_layout(hlayout)
        self.next_der.setMaximumHeight(20)
        self.finish_init()

    def update_counters(self):
        keeper = ctrl.document
        if keeper is not None:
            max_index = len(keeper.forests)
            self.current_treeset.setMaximum(max_index)
            self.treeset_counter.setText('/ %s' % max_index)
            if ctrl.forest:
                dm = ctrl.forest.get_derivation_steps() if ctrl.forest else 0
                max_der_step = len(dm.derivation_steps)
                self.current_derivation.setMaximum(max_der_step)
                self.derivation_counter.setText('/ %s' % max_der_step)
                parses = ctrl.forest.parse_trees
                if parses:
                    self.current_parse.setMaximum(len(parses))
                    self.parse_counter.setText('/ %s' % len(parses))

    def showEvent(self, event):
        """ Panel may have missed signals to update its contents when it was hidden: update all
        that signals would update.
        :param event:
        :return:
        """
        self.update_counters()
        super().showEvent(event)
