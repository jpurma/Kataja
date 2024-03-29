# coding=utf-8
from PyQt6 import QtGui

from kataja.KatajaAction import KatajaAction
from kataja.singletons import ctrl, log


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
    k_shortcut = QtGui.QKeySequence(QtGui.QKeySequence.StandardKey.New)
    k_undoable = False

    def method(self):
        """ Create new Forest, insert it after the current one and select it.
        :return: None
        """
        ctrl.document.new_forest()
        log.info('(Cmd-n) New forest, n.%s' % (ctrl.document.current_index + 1))


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
        ctrl.document.next_forest()
        return f'Next forest: {ctrl.document.current_index + 1}: {ctrl.forest.textual_form()}'


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
        ctrl.document.prev_forest()
        return f'Previous forest: {ctrl.document.current_index + 1}: {ctrl.forest.textual_form()}'


class JumpToForest(KatajaAction):
    k_action_uid = 'jump_to_forest'
    k_command = 'Jump to tree set'

    def prepare_parameters(self, args, kwargs):
        if not args:
            i = self.fetch_spinbox_value()
            args = [i if i is not None else ctrl.document.current_index + 1]
        return args, kwargs

    def method(self, n):
        ctrl.document.set_forest_by_index(n - 1)
        return f'Jump to tree set: {ctrl.document.current_index + 1}: {ctrl.forest.textual_form()}'

    def getter(self):
        return ctrl.document.current_index + 1

    def enabler(self):
        return ctrl.document


class NextParse(KatajaAction):
    k_action_uid = 'next_parse'
    k_command = 'Next parse tree'
    k_shortcut = 'Shift+Right'
    k_undoable = False
    k_tooltip = 'Switch to next parse tree'

    def method(self):
        """ Show the next possible parse, if there are more than one.
        :return: None
        """
        dt = ctrl.forest.derivation_tree
        dt.next_parse()
        return f'Next tree: {dt.current_branch_index + 1}: {ctrl.forest.textual_form()}'

    def enabler(self):
        dt = ctrl.forest.derivation_tree
        return ctrl.forest and len(dt.branches) > 1


class PreviousParse(KatajaAction):
    k_action_uid = 'previous_parse'
    k_command = 'Previous parse tree'
    k_shortcut = 'Shift+Left'
    k_undoable = False
    k_tooltip = 'Switch to previous parse tree'

    def method(self):
        """ Show the previous parse, if there are more than one
        :return: None
        """
        dt = ctrl.forest.derivation_tree
        dt.previous_parse()
        return f'Previous tree: {dt.current_branch_index + 1}: {ctrl.forest.textual_form()}'

    def enabler(self):
        dt = ctrl.forest.derivation_tree
        return ctrl.forest and len(dt.branches) > 1


#
# class NextMatchingParse(KatajaAction):
#     k_action_uid = 'next_matching_parse'
#     k_command = 'Next matching parse tree'
#     k_shortcut = '>'
#     k_undoable = False
#     k_tooltip = 'Switch to next parse tree with similar state'
#
#     def method(self):
#         """ Show the next possible parse, if there are more than one.
#         :return: None
#         """
#         found = ctrl.forest.find_next_matching_parse()
#         if found:
#             if isinstance(found, tuple):
#                 return f'Next matching tree: {ctrl.forest.current_parse_index + 1}: {ctrl.forest.textual_form()}'
#             return found
#         return 'No matching tree found'
#
#     def enabler(self):
#         return ctrl.forest and len(ctrl.forest.derivation_branches) > 1
#
#
# class PreviousMatchingParse(KatajaAction):
#     k_action_uid = 'previous_matching_parse'
#     k_command = 'Previous matching parse tree'
#     k_shortcut = '<'
#     k_undoable = False
#     k_tooltip = 'Switch to previous parse tree with similar state'
#
#     def method(self):
#         """ Show the previous parse, if there are more than one
#         :return: None
#         """
#         found = ctrl.forest.find_previous_matching_parse()
#         if found:
#             if isinstance(found, tuple):
#                 return f'Previous matching tree: {ctrl.forest.current_parse_index + 1}: {ctrl.forest.textual_form()}'
#             return found
#         return 'No matching tree found'
#
#     def enabler(self):
#         return ctrl.forest and len(ctrl.forest.derivation_branches) > 1


class JumpToParse(KatajaAction):
    k_action_uid = 'jump_to_parse'
    k_command = 'Jump to parse tree'

    def prepare_parameters(self, args, kwargs):
        dt = ctrl.forest.derivation_tree
        if not args:
            i = self.fetch_spinbox_value()
            args = [i if i is not None else dt.current_branch_index + 1]
        return args, kwargs

    def method(self, n):
        dt = ctrl.forest.derivation_tree
        dt.show_parse(n - 1)
        return f'Jump to tree set: {dt.current_branch_index + 1}: {ctrl.forest.textual_form()}'

    def getter(self):
        dt = ctrl.forest.derivation_tree
        return dt.current_branch_index + 1 if dt.current_branch_index is not None else 0

    def enabler(self):
        return ctrl.forest and ctrl.forest.derivation_tree


class NextStep(KatajaAction):
    k_action_uid = 'next_derivation_step'
    k_command = 'Next derivation step'
    k_shortcut = 'Up'
    k_undoable = False
    k_tooltip = 'Move to next frame in animation / derivation'

    def method(self):
        """ User action "step forward", Move to next derivation step """
        dt = ctrl.forest.derivation_tree
        dt.next_derivation_step()
        i = dt.current_step_index
        max_i = len(dt.branch)
        ctrl.forest.forest_edited()
        return f'Next derivation step: {i + 1}/{max_i}'

    def enabler(self):
        return ctrl.forest and ctrl.forest.derivation_tree.branch


class PreviousStep(KatajaAction):
    k_action_uid = 'prev_derivation_step'
    k_command = 'Previous derivation step'
    k_shortcut = 'Down'
    k_undoable = False
    k_tooltip = 'Move to previous frame in animation / derivation'

    def method(self):
        """ User action "step backward" , Move backward in derivation steps """
        dt = ctrl.forest.derivation_tree
        dt.previous_derivation_step()
        i = dt.current_step_index
        max_i = len(dt.branch)
        ctrl.forest.forest_edited()
        return f'Previous derivation step: {i + 1}/{max_i}'

    def enabler(self):
        return ctrl.forest and ctrl.forest.derivation_tree.branch


class JumpToDerivation(KatajaAction):
    k_action_uid = 'jump_to_derivation'
    k_command = 'Jump to derivation step'

    def prepare_parameters(self, args, kwargs):
        if not args:
            i = self.fetch_spinbox_value()
            args = [i if i is not None else ctrl.forest.derivation_tree.current_step_index + 1]
        return args, kwargs

    def method(self, n):
        dt = ctrl.forest.derivation_tree
        if dt.branch:
            dt.jump_to_derivation_step(n - 1)
            ctrl.forest.forest_edited()
            return f'Jump to derivation step: {n}'

    def getter(self):
        return ctrl.forest.derivation_tree.current_step_index + 1

    def enabler(self):
        return ctrl.forest and ctrl.forest.derivation_tree.branch


class JumpToDerivationById(KatajaAction):
    k_action_uid = 'jump_to_derivation_by_id'
    k_command = 'Jump to derivation step by id'

    def prepare_parameters(self, args, kwargs):
        return args, kwargs

    def method(self, state_id):
        dt = ctrl.forest.derivation_tree
        if dt.branch:
            dt.jump_to_derivation_step_by_id(state_id)
            ctrl.forest.forest_edited()
        return f'Jump to derivation step: {state_id}'
