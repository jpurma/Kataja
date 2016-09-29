# coding=utf-8

from kataja.singletons import ctrl, prefs
from kataja.KatajaAction import KatajaAction


class SwitchEditMode(KatajaAction):
    k_action_uid = 'switch_edit_mode'
    k_command = 'Toggle edit mode'
    k_shortcut = 'Ctrl+Shift+Space'
    k_undoable = False
    k_tooltip = 'Switch between free editing and derivation-based visualisation (Shift+Space)'

    def method(self, free_edit=None):
        """ Switch between visualisation mode and free edit mode
        :type free_edit: None to toggle between modes, True for free_drawing_mode,
        False for visualization
        :param state: triggering button or menu item state
        :return:
        """
        if free_edit is None:
            ctrl.free_drawing_mode = not ctrl.free_drawing_mode
        else:
            ctrl.free_drawing_mode = free_edit
        ctrl.ui.update_edit_mode()
        if ctrl.free_drawing_mode:
            return 'Free drawing mode: draw as you will, but there is no access to derivation ' \
                   'history for the structure.'
        else:
            return 'Derivation mode: you can edit the visualisation and browse the derivation ' \
                   'history, but the underlying structure cannot be changed.'

    def getter(self):
        return ctrl.free_drawing_mode


class NextForest(KatajaAction):
    k_action_uid = 'next_forest'
    k_command = 'Next forest'
    k_shortcut = '.'
    k_undoable = False
    k_tooltip = 'Switch to next forest'

    def method(self):
        """ Show the next 'slide', aka Forest from a list in ForestKeeper.
        :return: None
        """
        i, forest = ctrl.main.forest_keeper.next_forest()
        ctrl.main.change_forest()
        return 'Next forest (.): %s: %s' % (i + 1, forest.textual_form())


class PreviousForest(KatajaAction):
    k_action_uid = 'previous_forest'
    k_command = 'Previous forest'
    k_shortcut = ','
    k_undoable = False
    k_tooltip = 'Switch to previous forest'

    def method(self):
        """ Show the previous 'slide', aka Forest from a list in ForestKeeper.
        :return: None
        """
        i, forest = ctrl.main.forest_keeper.prev_forest()
        ctrl.main.change_forest()
        return 'Previous forest (,): %s: %s' % (i + 1, forest.textual_form())


class NextStep(KatajaAction):
    k_action_uid = 'next_derivation_step'
    k_command = 'Next derivation step'
    k_shortcut = '>'
    k_undoable = False
    k_tooltip = 'Move to next frame in animation / derivation'

    def method(self):
        """ User action "step forward (>)", Move to next derivation step """
        ctrl.forest.derivation_steps.next_derivation_step()


class PreviousStep(KatajaAction):
    k_action_uid = 'prev_derivation_step'
    k_command = 'Previous derivation step'
    k_shortcut = '<'
    k_undoable = False
    k_tooltip = 'Move to previous frame in animation / derivation'

    def method(self):
        """ User action "step backward (<)" , Move backward in derivation steps """
        ctrl.forest.derivation_steps.previous_derivation_step()


