# coding=utf-8
from PyQt5 import QtGui

from kataja.singletons import ctrl, prefs, running_environment, log
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


class NewStructure(KatajaAction):
    k_action_uid = 'new_forest'
    k_command = 'New forest'
    k_tooltip = 'Create a new forest after the current one'
    k_shortcut = QtGui.QKeySequence(QtGui.QKeySequence.New)
    k_undoable = False

    def method(self):
        """ Create new Forest, insert it after the current one and select it.
        :return: None
        """
        i, forest = ctrl.main.document.new_forest()
        ctrl.main.change_forest()
        log.info('(Cmd-n) New forest, n.%s' % (i + 1))


class NextForest(KatajaAction):
    k_action_uid = 'next_forest'
    k_command = 'Next forest'
    k_shortcut = 'Right'
    k_undoable = False
    k_tooltip = 'Switch to next forest'

    def method(self):
        """ Show the next 'slide', aka Forest from a list in KatajaDocument.
        :return: None
        """
        i, forest = ctrl.main.document.next_forest()
        ctrl.main.change_forest()
        return f'Next forest: {i + 1}: {forest.textual_form()}'


class PreviousForest(KatajaAction):
    k_action_uid = 'previous_forest'
    k_command = 'Previous forest'
    k_shortcut = 'Left'
    k_undoable = False
    k_tooltip = 'Switch to previous forest'

    def method(self):
        """ Show the previous 'slide', aka Forest from a list in KatajaDocument.
        :return: None
        """
        i, forest = ctrl.main.document.prev_forest()
        ctrl.main.change_forest()
        return f'Previous forest: {i + 1}: {forest.textual_form()}'


class JumpToForest(KatajaAction):
    k_action_uid = 'jump_to_forest'
    k_command = 'Jump to tree set'

    def prepare_parameters(self, args, kwargs):
        if not args:
            args = [ctrl.main.document.current_index + 1]
        try:
            i = int(args[0])
            args = [i]
        except ValueError:
            args = [ctrl.main.document.current_index + 1]
        return args, kwargs

    def method(self, n):
        current = ctrl.main.document.current_index
        i, forest = ctrl.main.document.jump_to_forest(n - 1)
        if i != current:
            ctrl.main.change_forest()
            return f'Jump to tree set: {i + 1}: {forest.textual_form()}'

    def getter(self):
        return ctrl.main.document.current_index + 1

    def enabler(self):
        return ctrl.main.document


class NextStep(KatajaAction):
    k_action_uid = 'next_derivation_step'
    k_command = 'Next derivation step'
    k_shortcut = 'Up'
    k_undoable = False
    k_tooltip = 'Move to next frame in animation / derivation'

    def method(self):
        """ User action "step forward", Move to next derivation step """
        ctrl.forest.derivation_steps.next_derivation_step()
        i = ctrl.forest.derivation_steps.derivation_step_index
        max_i = len(ctrl.forest.derivation_steps.derivation_steps)
        ctrl.forest.forest_edited()
        return f'Next derivation step: {i + 1}/{max_i}'


class PreviousStep(KatajaAction):
    k_action_uid = 'prev_derivation_step'
    k_command = 'Previous derivation step'
    k_shortcut = 'Down'
    k_undoable = False
    k_tooltip = 'Move to previous frame in animation / derivation'

    def method(self):
        """ User action "step backward" , Move backward in derivation steps """
        ctrl.forest.derivation_steps.previous_derivation_step()
        i = ctrl.forest.derivation_steps.derivation_step_index
        max_i = len(ctrl.forest.derivation_steps.derivation_steps)
        ctrl.forest.forest_edited()
        return f'Previous derivation step: {i + 1}/{max_i}'


class JumpToDerivation(KatajaAction):
    k_action_uid = 'jump_to_derivation'
    k_command = 'Jump to derivation step'

    def prepare_parameters(self, args, kwargs):
        if not args:
            args = [ctrl.forest.derivation_steps.derivation_step_index + 1]
        try:
            i = int(args[0])
            args = [i]
        except ValueError:
            args = [ctrl.forest.derivation_steps.derivation_step_index + 1]
        return args, kwargs

    def method(self, n):
        ctrl.forest.derivation_steps.jump_to_derivation_step(n - 1)
        ctrl.forest.forest_edited()
        msg = ctrl.forest.derivation_steps.current.msg
        return f'Jump to derivation step: {n}: {msg}'

    def getter(self):
        return ctrl.forest.derivation_steps.derivation_step_index + 1

    def enabler(self):
        return ctrl.forest.derivation_steps
