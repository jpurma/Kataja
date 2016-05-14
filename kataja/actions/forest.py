# coding=utf-8

from kataja.singletons import ctrl, prefs

a = {}


def switch_edit_mode(free_edit=None):
    """ Switch between visualisation mode and free edit mode
    :type free_edit: None to toggle between modes, True for free_drawing_mode, False for visualization
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

a['switch_edit_mode'] = {'command': 'Toggle edit mode', 'method': switch_edit_mode,
                         'undoable': False, 'shortcut': 'Shift+Space',
                         'tooltip': 'Switch between free editing and derivation-based '
                                    'visualisation (Shift+Space)'}

def switch_view_mode(bones_mode=None):
    """ Switch between showing only syntactic objects and showing richer representation
    :type bones_mode: None to toggle between modes, True for syntactic only, False for
    all items
    :return:
    """
    if bones_mode is None:
        prefs.bones_mode = not prefs.bones_mode
    else:
        prefs.bones_mode = bones_mode
    ctrl.ui.update_view_mode()
    if prefs.bones_mode:
        return 'Show only syntactic objects.'
    else:
        return 'Show all elements, including those that have no computational effects.'

a['switch_view_mode'] = {'command': 'Toggle view mode', 'method': switch_view_mode,
                         'undoable': False, 'shortcut': 'Shift+b',
                         'tooltip': 'Show only syntactic objects or show all objects (Shift+b)'}

def toggle_bones_mode():
    """
    :return:
    """
    prefs.bones_mode = not prefs.bones_mode
    for node in ctrl.forest.nodes.values():
        node.update_label()
        node.update_label_visibility()
        node.update_visibility()

def get_bones_mode():
    return prefs.bones_mode

a['toggle_bones_mode'] = {'command': 'Show only &syntactic objects', 'method': toggle_bones_mode,
                          'shortcut': 's', 'checkable': True, 'check_state': get_bones_mode}



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

