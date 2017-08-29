# coding=utf-8
from PyQt5 import QtWidgets

from kataja.globals import FOREST, DOCUMENT, PREFS
from kataja.singletons import ctrl, prefs, log
import kataja.globals as g
from kataja.KatajaAction import KatajaAction
from kataja.actions.constituent_sheet_actions import SetVisibleLabel

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


class SetVisibleLabelsToSynlabels(SetVisibleLabel):
    k_action_uid = 'set_visible_labels_to_synlabels'
    k_command = 'Nodes show syntactic labels'
    k_undoable = True
    k_tooltip = 'Set nodes to use syntactic node labels'
    k_checkable = True

    def prepare_parameters(self, args, kwargs):
        new_val = g.SYN_LABELS
        node_uid = ''
        node = ctrl.get_single_selected()
        if node:
            node_uid = node.uid
            old_val = ctrl.settings.get('label_text_mode', obj=node)
            if old_val == new_val or old_val == g.SYN_LABELS_FOR_LEAVES:
                new_val = g.NO_LABELS
                self.sender().setChecked(False)
        return [], {'label_mode': new_val, 'node_uid': node_uid}

    def getter(self):
        m = ctrl.settings.get_active_setting('label_text_mode')
        return m == g.SYN_LABELS or m == g.SYN_LABELS_FOR_LEAVES

    def enabler(self):
        node = ctrl.get_single_selected()
        return node and node.syntactic_object


class SetVisibleLabelsToNodelabels(SetVisibleLabel):
    k_action_uid = 'set_visible_labels_to_nodelabels'
    k_command = 'Nodes show node labels'
    k_undoable = True
    k_tooltip = 'Set nodes to use user-provided node labels'
    k_checkable = True

    def prepare_parameters(self, args, kwargs):
        new_val = g.NODE_LABELS
        node_uid = ''
        node = ctrl.get_single_selected()
        if node:
            node_uid = node.uid
            old_val = ctrl.settings.get('label_text_mode', obj=node)
            if old_val == new_val or old_val == g.NODE_LABELS_FOR_LEAVES:
                new_val = g.NO_LABELS
                self.sender().setChecked(False)
        return [], {'label_mode': new_val, 'node_uid': node_uid}

    def getter(self):
        m = ctrl.settings.get_active_setting('label_text_mode')
        return m == g.NODE_LABELS_FOR_LEAVES or m == g.NODE_LABELS

    def enabler(self):
        return not ctrl.settings.get('syntactic_mode')


class SetVisibleLabelToAutolabel(SetVisibleLabel):
    k_action_uid = 'set_visible_labels_to_autolabels'
    k_command = 'Nodes show generated labels'
    k_undoable = True
    k_tooltip = 'Set nodes to use labels generated from projected leaves'
    k_checkable = True

    def prepare_parameters(self, args, kwargs):
        new_val = g.XBAR_LABELS
        node_uid = ''
        node = ctrl.get_single_selected()
        if node:
            node_uid = node.uid
            old_val = ctrl.settings.get('label_text_mode', obj=node)
            if old_val == new_val:
                new_val = g.NO_LABELS
                self.sender().setChecked(False)
        return [], {'label_mode': new_val, 'node_uid': node_uid}

    def getter(self):
        node = ctrl.get_single_selected()
        if not node:
            return False
        value = ctrl.settings.get('label_text_mode', obj=node, level=g.OBJECT)
        return value == g.XBAR_LABELS
