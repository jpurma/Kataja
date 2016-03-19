# coding=utf-8

from kataja.singletons import ctrl

a = {}

def next_structure():
    """ Show the next 'slide', aka Forest from a list in ForestKeeper.
    :return: None
    """
    i, forest = ctrl.main.forest_keeper.next_forest()
    ctrl.main.change_forest()
    ctrl.main.add_message('(.) trees %s: %s' % (i + 1, forest.textual_form()))


a['next_forest'] = {'command': 'Next forest', 'method': next_structure,
                    'undoable': False, 'shortcut': '.',
                    'tooltip': 'Switch to next forest'}


def previous_structure():
    """ Show the previous 'slide', aka Forest from a list in ForestKeeper.
    :return: None
    """
    i, forest = ctrl.main.forest_keeper.prev_forest()
    ctrl.main.change_forest()
    ctrl.main.add_message('(,) trees %s: %s' % (i + 1, forest.textual_form()))


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

