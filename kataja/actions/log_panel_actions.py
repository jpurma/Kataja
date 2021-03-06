# coding=utf-8

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


class SetLogLevel(KatajaAction):
    k_action_uid = 'set_log_level'
    k_command = 'Set log level'
    k_undoable = False
    k_tooltip = 'Set minimum priority for visible messages'

    def prepare_parameters(self, args, kwargs):
        value = self.sender().currentData()
        return [value], kwargs

    def method(self, value):
        prefs.set('log_level', value)
        panel = ctrl.ui.get_panel('LogPanel')
        panel.rebuild_log()

    def getter(self):
        return prefs.get('log_level')


class ClearLog(KatajaAction):
    k_action_uid = 'clear_log'
    k_command = 'Clear log'
    k_undoable = False
    k_tooltip = 'Clear log'

    def method(self):
        panel = ctrl.ui.get_panel('LogPanel')
        panel.clear_log()
