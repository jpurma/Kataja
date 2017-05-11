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

class SetSynlabelsVisible(KatajaAction):
    k_action_uid = 'set_synlabels_visible'
    k_command = 'Nodes show syntactic labels'
    k_undoable = True
    k_tooltip = 'Set nodes to use syntactic node labels'

    def method(self):
        """ """
        ctrl.settings.set('label_text_mode', g.SYN_LABELS, level=ctrl.ui.active_scope)
        ctrl.forest.update_label_shapes()
        mode_text = prefs.get_ui_text_for_choice(g.SYN_LABELS, 'label_text_mode')
        return f'Set label text mode to: {mode_text}'

    def getter(self):
        m = ctrl.settings.get('label_text_mode')
        return m == g.SYN_LABELS or m == g.SYN_LABELS_FOR_LEAVES


class SetNodeLabelsVisible(KatajaAction):
    k_action_uid = 'set_node_labels_visible'
    k_command = 'Nodes show node labels'
    k_undoable = True
    k_tooltip = 'Set nodes to use user-provided node labels'

    def method(self):
        """ """
        ctrl.settings.set('label_text_mode', g.NODE_LABELS, level=ctrl.ui.active_scope)
        ctrl.forest.update_label_shapes()
        mode_text = prefs.get_ui_text_for_choice(g.NODE_LABELS, 'label_text_mode')
        return f'Set label text mode to: {mode_text}'

    def getter(self):
        m = ctrl.settings.get('label_text_mode', level=ctrl.ui.active_scope)
        return m == g.NODE_LABELS_FOR_LEAVES or m == g.NODE_LABELS

    def enabler(self):
        return ctrl.ui.active_scope != g.SELECTION and not ctrl.settings.get('syntactic_mode')


class SetAutolabelsVisible(KatajaAction):
    k_action_uid = 'set_autolabels_visible'
    k_command = 'Nodes show generated labels'
    k_undoable = True
    k_tooltip = 'Set nodes to use labels generated from projected leaves'

    def method(self):
        """ """
        ctrl.settings.set('label_text_mode', g.XBAR_LABELS, level=ctrl.ui.active_scope)
        ctrl.forest.update_label_shapes()
        mode_text = prefs.get_ui_text_for_choice(g.XBAR_LABELS, 'label_text_mode')
        return f'Set label text mode to: {mode_text}'

    def getter(self):
        m = ctrl.settings.get('label_text_mode', level=ctrl.ui.active_scope)
        return m == g.XBAR_LABELS
