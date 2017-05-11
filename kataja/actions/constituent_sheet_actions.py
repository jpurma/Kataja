# coding=utf-8
from PyQt5 import QtWidgets

from kataja.globals import FOREST, DOCUMENT, PREFS
from kataja.singletons import ctrl, prefs, log
import kataja.globals as g
from kataja.KatajaAction import KatajaAction


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


class ToggleLabelShape(KatajaAction):
    k_action_uid = 'toggle_label_shape'
    k_command = 'Rotate between node shapes'
    k_shortcut = 'b'
    k_checkable = True

    def method(self):
        """ Brackets are visible always for non-leaves, never or for important parts
        """
        bs = ctrl.settings.get('label_shape', level=ctrl.ui.active_scope)
        bs += 1
        if bs > 4:
            bs = 0
        while bs in ctrl.forest.visualization.banned_node_shapes:
            bs += 1
            if bs > 4:
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
            ctrl.settings.set('feature_check_display', 2, level=ctrl.ui.active_scope)

        ctrl.settings.set('label_shape', bs, level=ctrl.ui.active_scope)
        ctrl.forest.update_label_shapes()
        return m

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION


class ActivateNoFrameNodeShape(KatajaAction):
    k_action_uid = 'set_no_frame_node_shape'
    k_command = 'Borderless nodes'
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('label_shape', g.NORMAL, level=ctrl.ui.active_scope)
        ctrl.forest.update_label_shapes()
        return f'{self.k_command} ({ToggleLabelShape.k_shortcut})'

    def getter(self):
        return ctrl.settings.get('label_shape', level=ctrl.ui.active_scope) == g.NORMAL

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION and ctrl.forest.visualization and \
               g.NORMAL not in ctrl.forest.visualization.banned_node_shapes


class ActivateScopeboxNodeShape(KatajaAction):
    k_action_uid = 'set_scopebox_node_shape'
    k_command = "Box showing node's scope"
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('label_shape', g.SCOPEBOX, level=ctrl.ui.active_scope)
        ctrl.forest.update_label_shapes()
        return f'{self.k_command} ({ToggleLabelShape.k_shortcut})'

    def getter(self):
        return ctrl.settings.get('label_shape', level=ctrl.ui.active_scope) == g.SCOPEBOX

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION and ctrl.forest.visualization and \
               g.SCOPEBOX not in ctrl.forest.visualization.banned_node_shapes


class ActivateBracketedNodeShape(KatajaAction):
    k_action_uid = 'set_bracketed_node_shape'
    k_command = 'Bracketed nodes'
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('label_shape', g.BRACKETED, level=ctrl.ui.active_scope)
        ctrl.forest.update_label_shapes()
        return f'{self.k_command} ({ToggleLabelShape.k_shortcut})'

    def getter(self):
        return ctrl.settings.get('label_shape', level=ctrl.ui.active_scope) == g.BRACKETED

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION and ctrl.forest.visualization and \
               g.BRACKETED not in ctrl.forest.visualization.banned_node_shapes


class ActivateBoxShape(KatajaAction):
    k_action_uid = 'set_box_node_shape'
    k_command = 'Framed nodes'
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('label_shape', g.BOX, level=ctrl.ui.active_scope)
        ctrl.forest.update_label_shapes()
        return f'{self.k_command} ({ToggleLabelShape.k_shortcut})'

    def getter(self):
        return ctrl.settings.get('label_shape', level=ctrl.ui.active_scope) == g.BOX

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION and ctrl.forest.visualization and \
               g.BOX not in ctrl.forest.visualization.banned_node_shapes


class ActivateCardNodeShape(KatajaAction):
    k_action_uid = 'set_card_node_shape'
    k_command = 'Nodes as cards'
    k_checkable = True

    def method(self):
        """ Set nodes to be frameless and small
        :return:
        """
        ctrl.settings.set('label_shape', g.CARD, level=ctrl.ui.active_scope)
        ctrl.settings.set('feature_check_display', 2, level=ctrl.ui.active_scope)
        ctrl.forest.update_label_shapes()
        return f'{self.k_command} ({ToggleLabelShape.k_shortcut})'

    def getter(self):
        return ctrl.settings.get('label_shape', level=ctrl.ui.active_scope) == g.CARD

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION and ctrl.forest.visualization and \
               g.CARD not in ctrl.forest.visualization.banned_node_shapes


class SwitchTraceMode(KatajaAction):
    k_action_uid = 'select_trace_strategy'
    k_command = 'Show traces'
    k_shortcut = 't'

    def method(self):
        """ Switch between multidomination, showing traces and a view where
        traces are grouped to their original position
        :return: None
        """

        level = ctrl.ui.active_scope
        sender = self.sender()
        if isinstance(sender, QtWidgets.QComboBox):
            value = sender.currentData()
        else:
            value = ctrl.settings.get('trace_strategy', level=level)
            value += 1
            if value == 3:
                value = 0
        ctrl.settings.set('trace_strategy', value, level=level)
        ctrl.forest.forest_edited()
        mode_text = prefs.get_ui_text_for_choice(value, 'trace_strategy')
        return f'Set trace strategy to: {mode_text}'

    def getter(self):
        return ctrl.settings.get('trace_strategy', level=ctrl.ui.active_scope)

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION


class ToggleLabelTextModes(KatajaAction):
    k_action_uid = 'toggle_label_text_mode'
    k_command = 'Switch label text mode'
    k_undoable = True
    k_shortcut = 'l'
    k_tooltip = 'Switch what to show as label text'

    def method(self):
        """ """
        sender = self.sender()
        if isinstance(sender, QtWidgets.QComboBox):
            value = sender.currentData()
        else:
            value = ctrl.settings.get('label_text_mode', level=ctrl.ui.active_scope)
            syn_mode = ctrl.settings.get('syntactic_mode')
            support_secondary = ctrl.forest.syntax.supports_secondary_labels
            # some labels are not allowed in syn mode.
            ok = False
            while not ok:
                value += 1
                if value == g.SECONDARY_LABELS and not support_secondary:
                    ok = False
                elif value == g.NODE_LABELS_FOR_LEAVES and syn_mode:
                    ok = False
                elif value == g.NODE_LABELS and syn_mode:
                    ok = False
                elif value == g.XBAR_LABELS and syn_mode:
                    ok = False
                elif value > g.SECONDARY_LABELS:
                    ok = False
                    value = -1
                else:
                    ok = True
        ctrl.settings.set('label_text_mode', value, level=ctrl.ui.active_scope)
        ctrl.forest.update_label_shapes()
        mode_text = prefs.get_ui_text_for_choice(value, 'label_text_mode')
        return f'Set labeling strategy to: {mode_text}'

    def getter(self):
        return ctrl.settings.get('label_text_mode')


class SelectProjectionStyle(KatajaAction):
    k_action_uid = 'select_projection_style'
    k_command = 'Select projection style'
    k_tooltip = 'Switch between different ways to show projecting constituents'
    k_shortcut = 'Shift+P'

    def method(self):
        """ """
        sender = self.sender()
        if isinstance(sender, QtWidgets.QComboBox):
            value = sender.currentData()
        else:
            value = ctrl.settings.get('projection_style', level=ctrl.ui.active_scope)
            value += 1
            if value == 3:
                value = 0
        ctrl.settings.set('projection_style', value, level=ctrl.ui.active_scope)
        ctrl.forest.projection_manager.update_projection_display()
        mode_text = prefs.get_ui_text_for_choice(value, 'projection_style')
        return 'Projection style: ' + mode_text

    def getter(self):
        return ctrl.settings.get('projection_style', level=ctrl.ui.active_scope)

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION

