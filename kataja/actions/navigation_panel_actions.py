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
        i, forest = ctrl.main.forest_keeper.new_forest()
        ctrl.main.change_forest()
        log.info('(Cmd-n) New forest, n.%s' % (i + 1))


class NextForest(KatajaAction):
    k_action_uid = 'next_forest'
    k_command = 'Next forest'
    k_shortcut = 's'
    k_undoable = False
    k_tooltip = 'Switch to next forest'

    def method(self):
        """ Show the next 'slide', aka Forest from a list in KatajaDocument.
        :return: None
        """
        i, forest = ctrl.main.forest_keeper.next_forest()
        ctrl.main.change_forest()
        return f'Next forest: {i + 1}: {forest.textual_form()}'


class PreviousForest(KatajaAction):
    k_action_uid = 'previous_forest'
    k_command = 'Previous forest'
    k_shortcut = 'w'
    k_undoable = False
    k_tooltip = 'Switch to previous forest'

    def method(self):
        """ Show the previous 'slide', aka Forest from a list in KatajaDocument.
        :return: None
        """
        i, forest = ctrl.main.forest_keeper.prev_forest()
        ctrl.main.change_forest()
        return f'Previous forest: {i + 1}: {forest.textual_form()}'


class NextStep(KatajaAction):
    k_action_uid = 'next_derivation_step'
    k_command = 'Next derivation step'
    k_shortcut = 'd'
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
    k_shortcut = 'a'
    k_undoable = False
    k_tooltip = 'Move to previous frame in animation / derivation'

    def method(self):
        """ User action "step backward" , Move backward in derivation steps """
        ctrl.forest.derivation_steps.previous_derivation_step()
        i = ctrl.forest.derivation_steps.derivation_step_index
        max_i = len(ctrl.forest.derivation_steps.derivation_steps)
        ctrl.forest.forest_edited()
        return f'Previous derivation step: {i + 1}/{max_i}'
