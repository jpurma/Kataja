# coding=utf-8

from kataja.singletons import ctrl, prefs, running_environment
from kataja.KatajaAction import KatajaAction
from kataja.globals import DOCUMENT, SELECTION
from kataja.ui_widgets.Panel import PanelAction

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


class SetScopeForNodeStyle(PanelAction):
    k_action_uid = 'set_editing_scope'
    k_command = 'Set scope for style changes'
    k_tooltip = 'Changes here affect only selected nodes, nodes in this tree, nodes in this ' \
                'document or they are set as user defaults.'
    k_undoable = False

    def method(self):
        """ Change drawing panel to work on selected nodes, constituent nodes or
        other available
        nodes
        """
        sender = self.sender()
        if sender:
            value = sender.currentData(256)
            ctrl.ui.set_scope(value)

    def enabler(self):
        return ctrl.forest

    def getter(self):
        if self.panel:
            self.panel.prepare_selections()
        return ctrl.ui.active_scope


class ResetSettings(KatajaAction):
    k_action_uid = 'reset_settings'
    k_command = 'Reset node settings'
    k_tooltip = 'Reset settings in certain level and in all of the more specific levels'

    def prepare_parameters(self, args, kwargs):
        level = ctrl.ui.active_scope
        return [level], kwargs

    def method(self, level: int):
        """ Reset node settings in given level and in more specific levels.
        :param level: int, level enum: 66 = SELECTED, 2 = FOREST, 3 = DOCUMENT, 4 = PREFS.
        """
        log.warning('not implemented: reset_settings')

