# coding=utf-8

from kataja.singletons import ctrl

a = {}


def switch_edit_mode(free_edit=None):
    """ Switch between visualisation mode and free edit mode
    :type free_edit: None to toggle between modes, True for free_edit_mode, False for visualization
    :return:
    """
    if free_edit is None:
        ctrl.free_edit_mode = not ctrl.free_edit_mode
    else:
        ctrl.free_edit_mode = free_edit
    ctrl.ui.update_edit_mode()
    if ctrl.free_edit_mode:
        return 'Free drawing mode: draw as you will, but there is no access to derivation ' \
               'history for the structure.'
    else:
        return 'Derivation mode: you can edit the visualisation and browse the derivation ' \
               'history, but the underlying structure cannot be changed.'

a['switch_edit_mode'] = {'command': 'Toggle edit mode', 'method': switch_edit_mode,
                         'undoable': False, 'shortcut': 'Shift+Space',
                         'tooltip': 'Switch between free editing and derivation-based '
                                    'visualisation (Shift+Space)'}

def next_structure():
    """ Show the next 'slide', aka Forest from a list in ForestKeeper.
    :return: None
    """
    i, forest = ctrl.main.forest_keeper.next_forest()
    ctrl.main.change_forest()
    return 'Next forest (.): %s: %s' % (i + 1, forest.textual_form())


a['next_forest'] = {'command': 'Next forest', 'method': next_structure,
                    'undoable': False, 'shortcut': '.',
                    'tooltip': 'Switch to next forest'}


def previous_structure():
    """ Show the previous 'slide', aka Forest from a list in ForestKeeper.
    :return: None
    """
    i, forest = ctrl.main.forest_keeper.prev_forest()
    ctrl.main.change_forest()
    return 'Previous forest (,): %s: %s' % (i + 1, forest.textual_form())


a['prev_forest'] = {'command': 'Previous forest', 'method': previous_structure,
                    'shortcut': ',', 'undoable': False,
                    'tooltip': 'Switch to previous forest'}


def animation_step_forward():
    """ User action "step forward (>)", Move to next derivation step """
    ctrl.forest.derivation_steps.next_derivation_step()
    ctrl.main.add_message('Step forward')


a['next_derivation_step'] = {'command': 'Animation step forward',
                             'method': animation_step_forward, 'shortcut': '>'}


def animation_step_backward():
    """ User action "step backward (<)" , Move backward in derivation steps """
    ctrl.forest.derivation_steps.previous_derivation_step()
    ctrl.main.add_message('Step backward')


a['prev_derivation_step'] = {'command': 'Animation step backward',
                             'method': animation_step_backward, 'shortcut': '<'}

