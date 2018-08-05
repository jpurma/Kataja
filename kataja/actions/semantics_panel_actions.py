# coding=utf-8

from kataja.singletons import ctrl, prefs, running_environment
from kataja.KatajaAction import KatajaAction
from kataja.globals import DOCUMENT, SELECTION

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


class ToggleSemanticsView(KatajaAction):
    k_action_uid = 'toggle_semantics_view'
    k_command = 'Show or hide semantics'
    k_undoable = False
    k_tooltip = 'Show or hide semantics'
    k_shortcut = 's'
    k_checkable = True

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        return [sender.isChecked()], {}

    def method(self, checked):
        ctrl.settings.set('show_semantics', checked, level=ctrl.ui.active_scope)
        if ctrl.settings.get('show_semantics'):
            ctrl.forest.semantics_manager.show()
        else:
            ctrl.forest.semantics_manager.hide()

    def getter(self):
        return ctrl.settings.get('show_semantics', level=ctrl.ui.active_scope)

    def enabler(self):
        return ctrl.forest and ctrl.forest.in_display and ctrl.forest.semantics_manager.models and \
               self.not_selection()
