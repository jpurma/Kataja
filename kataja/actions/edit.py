# coding=utf-8
from kataja.singletons import ctrl


a = {}


def cut_method():
    qclipboard = ctrl.main.app.clipboard()
    ctrl.clipboard = []
    if ctrl.selected:
        for item in ctrl.selected:
            if hasattr(item, 'cut'):
                ctrl.clipboard.append(item.cut(ctrl.selected))

    print('Cut called')

def can_cut_or_copy():
    if ctrl.selected:
        return True
    elif ctrl.main.app:
        w = ctrl.main.app.focusWidget()
        #if w:
        #    print(w)
    return False

a['cut'] = {'command': 'Cut', 'method': cut_method, 'shortcut': 'Ctrl+x',
            'tooltip': 'Cut element', 'enabler': can_cut_or_copy}


def copy_method():
    ctrl.clipboard = []
    for item in ctrl.selected:
        if hasattr(item, 'clipboard_copy'):
            ctrl.clipboard.append(item.clipboard_copy(ctrl.selected))


a['copy'] = {'command': 'Copy', 'method': copy_method, 'shortcut': 'Ctrl+c',
             'tooltip': 'Copy element', 'enabler': can_cut_or_copy}


def paste_method():
    print('Paste called')


def can_paste():
    if ctrl.main.app and ctrl.main.app.clipboard():
        mimeData = ctrl.main.app.clipboard().mimeData()
        return mimeData.hasImage() or mimeData.hasHtml() or mimeData.hasText()
    return False

a['paste'] = {'command': 'Paste', 'method': paste_method, 'shortcut': 'Ctrl+v',
              'tooltip': 'Paste element', 'enabler': can_paste}


def undo():
    """ Undo -command triggered
    :return: None
    """
    ctrl.forest.undo_manager.undo()


def can_undo():
    return bool(ctrl.forest and ctrl.forest.undo_manager.can_undo())

a['undo'] = {'command': 'undo', 'method': undo, 'undoable': False,
             'shortcut': 'Ctrl+z', 'enabler': can_undo}


def redo():
    """ Redo -command triggered
    :return: None
    """
    ctrl.forest.undo_manager.redo()


def can_redo():
    return bool(ctrl.forest and ctrl.forest.undo_manager.can_redo())

a['redo'] = {'command': 'redo', 'method': redo, 'undoable': False,
             'shortcut': 'Ctrl+Shift+z', 'enabler': can_redo}

