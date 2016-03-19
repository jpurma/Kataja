# coding=utf-8
from kataja.singletons import ctrl


a = {}


def cut_method():
    print('Cut called')

a['cut'] = {'command': 'Cut', 'method': cut_method, 'shortcut': 'Ctrl+x',
            'tooltip': 'Cut element'}


def copy_method():
    print('Copy called')

a['copy'] = {'command': 'Copy', 'method': copy_method, 'shortcut': 'Ctrl+c',
             'tooltip': 'Copy element'}


def paste_method():
    print('Paste called')

a['paste'] = {'command': 'Paste', 'method': paste_method, 'shortcut': 'Ctrl+v',
              'tooltip': 'Paste element'}


def undo():
    """ Undo -command triggered
    :return: None
    """
    ctrl.forest.undo_manager.undo()


a['undo'] = {'command': 'undo', 'method': undo, 'undoable': False,
             'shortcut': 'Ctrl+z'}


def redo():
    """ Redo -command triggered
    :return: None
    """
    ctrl.forest.undo_manager.redo()


a['redo'] = {'command': 'redo', 'method': redo, 'undoable': False,
             'shortcut': 'Ctrl+Shift+z'}

