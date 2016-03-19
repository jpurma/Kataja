# coding=utf-8
from kataja.singletons import ctrl

a = {}


def key_backspace():
    """ In many contexts this will delete something. Expand this as necessary
    for contexts that don't otherwise grab keyboard.
    :return: None
    """
    ctrl.multiselection_start() # don't update selections until all are removed
    for item in list(ctrl.selected):
        ctrl.forest.delete_item(item)
    ctrl.multiselection_end() # ok go update


a['key_backspace'] = {'command': 'key_backspace', 'method': key_backspace,
                      'shortcut': 'Backspace'}


a['toggle_all_panels'] = {'command': 'Hide all panels',
                          'command_alt': 'Show all panels',
                          'method': 'toggle_all_panels'} # missing!


def key_left():
    """ Placeholder for keypress
    :return: None
    """
    if not ctrl.ui_focus:
        ctrl.graph_scene.move_selection('left')


a['key_left'] = {'command': 'key_left', 'undoable': False, 'method': key_left,
                 'shortcut': 'Left'}


def key_right():
    """ Placeholder for keypress
    :return: None
    """
    if not ctrl.ui_focus:
        ctrl.graph_scene.move_selection('right')


a['key_right'] = {'command': 'key_right', 'undoable': False,
                  'method': key_right, 'shortcut': 'Right'}


def key_up():
    """ Placeholder for keypress
    :return: None
    """
    if not ctrl.ui_focus:
        ctrl.graph_scene.move_selection('up')


a['key_up'] = {'command': 'key_up', 'undoable': False, 'method': key_up,
               'shortcut': 'Up'}


def key_down():
    """ Placeholder for keypress
    :return: None
    """
    if not ctrl.ui_focus:
        ctrl.graph_scene.move_selection('down')


a['key_down'] = {'command': 'key_down', 'undoable': False, 'method': key_down,
                 'shortcut': 'Down'}
