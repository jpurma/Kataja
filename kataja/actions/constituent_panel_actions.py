# coding=utf-8
from PyQt6 import QtWidgets

import kataja.globals as g
from kataja.KatajaAction import KatajaAction
from kataja.singletons import ctrl, prefs


# ==== Class variables for KatajaActions:
#
# k_action_uid : unique id for calling this action. required, other are optional
# k_command : text used for menu command and log feedback, unless the method returns a fdback string
# k_tooltip : tooltip text for ui element. If not given, uses k_command as tooltip.
# k_undoable : is the action undoable, default is True
# k_shortcut : keyboard shortcut given as string, e.g. 'Ctrl+x'
# k_shortcut_context : can be nothing or 'parent_and_children' if shortcut is active only when the
#                      parent widget is visible and active
# k_checkable : should the action be checkable, default False
#
# ==== Methods:
#
# method : gets called when action is triggered. If it returns a string, this is used as a command
#          feedback string, otherwise k_command is printed to log.
# getter : if there is an UI element that can show state or display value, this method returns the
#          value. These are called quite often, but with values that have to change e.g. when item
#          is dragged, you'll have to update manually.
# enabler : if enabler is defined, the action is active (also reflected into its UI elements) only
#           when enabler returns True
#


class SelectLabelShape(KatajaAction):
    k_action_uid = 'select_cn_shape'
    k_command = 'Rotate between node shapes'
    k_shortcut = 'b'
    k_checkable = True

    def method(self):
        """ Brackets are visible always for non-leaves, never or for important parts
        """
        bs = ctrl.ui.get_active_setting('cn_shape')
        bs += 1
        m = ''
        if bs > 5:
            bs = 0
        while bs in ctrl.forest.visualization.banned_cn_shapes:
            bs += 1
            if bs > 5:
                bs = 0
        if bs == g.NORMAL:
            m = 'Node shape: Simple'
        elif bs == g.SCOPEBOX:
            m = 'Node shape: Scopeboxes'
        elif bs == g.BRACKETED:
            m = 'Node shape: Bracket bars'
        elif bs == g.BOX:
            m = 'Node shape: Boxes'
        elif bs == g.CARD:
            m = 'Node shape: Cards'
            ctrl.ui.set_active_setting('feature_check_display', 2)
        elif bs == g.FEATURE_SHAPE:
            m = 'Node shape: Feature'

        ctrl.ui.set_active_setting('cn_shape', bs)
        return m

    def enabler(self):
        return self.not_selection()


class ActivatePlainNodeShape(KatajaAction):
    k_action_uid = 'set_no_frame_cn_shape'
    k_command = 'Borderless nodes'
    k_checkable = True
    shape = g.NORMAL

    def method(self):
        ctrl.ui.set_active_setting('cn_shape', self.shape)
        return f'{self.k_command} ({SelectLabelShape.k_shortcut})'

    def getter(self):
        return ctrl.ui.get_active_setting('cn_shape') == self.shape

    def enabler(self):
        return ctrl.forest and self.not_selection() and ctrl.forest.visualization and \
               self.shape not in ctrl.forest.visualization.banned_cn_shapes


class ActivateScopeboxNodeShape(ActivatePlainNodeShape):
    k_action_uid = 'set_scopebox_cn_shape'
    k_command = "Box showing node's scope"
    k_checkable = True
    shape = g.SCOPEBOX


class ActivateBracketedNodeShape(ActivatePlainNodeShape):
    k_action_uid = 'set_bracketed_cn_shape'
    k_command = 'Bracketed nodes'
    k_checkable = True
    shape = g.BRACKETED


class ActivateBoxShape(ActivatePlainNodeShape):
    k_action_uid = 'set_box_cn_shape'
    k_command = 'Framed nodes'
    k_checkable = True
    shape = g.BOX


class ActivateCardNodeShape(ActivatePlainNodeShape):
    k_action_uid = 'set_card_cn_shape'
    k_command = 'Nodes as cards'
    k_checkable = True
    shape = g.CARD

    def method(self):
        ctrl.ui.set_active_setting('feature_check_display', 2)
        return super().method()


class ActivateFeatureNodeShape(ActivatePlainNodeShape):
    k_action_uid = 'set_feature_cn_shape'
    k_command = 'Node takes shape of its prominent feature'
    k_checkable = True
    shape = g.FEATURE_SHAPE

    def method(self):
        ctrl.ui.set_active_setting('feature_check_display', 0)
        return super().method()


class SelectTraceMode(KatajaAction):
    k_action_uid = 'select_trace_strategy'
    k_command = 'Show traces'
    k_shortcut = 't'

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        if isinstance(sender, QtWidgets.QComboBox):
            trace_mode = sender.currentData()
        else:
            trace_mode = None
        return [], {'trace_mode': trace_mode}

    def method(self, trace_mode=None):
        """ Switch between multidomination, showing traces and a view where
        traces are grouped to their original position.
        :param trace_mode: int or None -- either switch to given trace mode, or rotate to next one
        if None is given.
        :return: None
        """

        if trace_mode is None:
            trace_mode = ctrl.ui.get_active_setting('trace_strategy')
            trace_mode += 1
            if trace_mode == 3:
                trace_mode = 0
        ctrl.ui.set_active_setting('trace_strategy', trace_mode)
        ctrl.forest.forest_edited()
        mode_text = prefs.get_ui_text_for_choice(trace_mode, 'trace_strategy')
        return f'Set trace strategy to: {mode_text}'

    def getter(self):
        return ctrl.ui.get_active_setting('trace_strategy')

    def enabler(self):
        return ctrl.forest and self.not_selection()


class SelectLinearizationMode(KatajaAction):
    k_action_uid = 'select_linearization_mode'
    k_command = 'Select linearization strategy'
    k_shortcut = 'i'

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        if isinstance(sender, QtWidgets.QComboBox):
            linearization_mode = sender.currentData()
        else:
            linearization_mode = None
        return [], {'linearization_mode': linearization_mode}

    def method(self, linearization_mode=None):
        """
        :param linearization_mode: int or None -- either switch to given trace mode, or rotate to
        next one if None is given.
        :return: None
        """
        if linearization_mode is None:
            linearization_mode = ctrl.ui.get_active_setting('linearization_mode')
            linearization_mode += 1
            if linearization_mode == 3:
                linearization_mode = 0
        ctrl.ui.set_active_setting('linearization_mode', linearization_mode)
        ctrl.forest.forest_edited()
        mode_text = prefs.get_ui_text_for_choice(linearization_mode, 'linearization_mode')
        return f'Set linearization mode: {mode_text}'

    def getter(self):
        return ctrl.ui.get_active_setting('linearization_mode')

    def enabler(self):
        return ctrl.forest and self.not_selection()


class SetVisibleLabel(KatajaAction):
    k_action_uid = 'set_visible_label'
    k_command = 'Select label text mode'
    k_undoable = True
    k_shortcut = 'l'
    k_tooltip = 'Switch what to show as label text'

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        if isinstance(sender, QtWidgets.QComboBox):
            label_mode = sender.currentData()
        else:
            label_mode = None
        return [], {'label_mode': label_mode}

    def method(self, label_mode=None):
        """ """
        if label_mode is None:
            label_mode = ctrl.ui.get_active_setting('label_text_mode')
            syn_mode = ctrl.doc_settings.get('syntactic_mode')
            # some labels are not allowed in syn mode. If called without arguments, rotate to
            # next available mode.
            ok = False
            while not ok:
                label_mode += 1
                if label_mode == g.NODE_LABELS_FOR_LEAVES and syn_mode:
                    ok = False
                elif label_mode == g.NODE_LABELS and syn_mode:
                    ok = False
                elif label_mode > g.NO_LABELS:
                    ok = False
                    label_mode = -1
                else:
                    ok = True
        ctrl.ui.set_active_setting('label_text_mode', label_mode)
        mode_text = prefs.get_ui_text_for_choice(label_mode, 'label_text_mode')
        return f'Set labeling strategy to: {mode_text}'

    def getter(self):
        return ctrl.ui.get_active_setting('label_text_mode')

    def enabler(self):
        return ctrl.forest and self.not_selection()
