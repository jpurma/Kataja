# coding=utf-8

from kataja.singletons import ctrl, log
import kataja.actions._utils

a = {}

def toggle_panel(panel_id, action=None):
    """ Show or hide panel depending if it is visible or not
    :param panel_id: enum of panel identifiers (str)
    :param action:
    :return: None
    """
    ctrl.ui.toggle_panel(action, panel_id)

# actions that call ^- this method are defined programmatically

def toggle_fold_panel(sender=None):
    """ Fold panel into label line or reveal the whole panel.
    :param sender: field that called this action
    :return: None
    """
    panel = kataja.actions._utils.get_ui_container(sender)
    if panel:
        panel.set_folded(not panel.folded)


a['toggle_fold_panel'] = {'command': 'Fold panel', 'method': toggle_fold_panel,
                          'sender_arg': True, 'checkable': True,
                          'undoable': False, 'tooltip': "Minimize this panel"}


def pin_panel(sender=None):
    """ Put panel back to panel dock area.
    :param sender: field that called this action
    :return: None
    """
    panel = kataja.actions._utils.get_ui_container(sender)
    if panel:
        panel.pin_to_dock()


a['pin_panel'] = {'command': 'Pin to dock', 'method': pin_panel,
                  'sender_arg': True, 'undoable': False,
                  'tooltip': "Pin to dock"}


def toggle_full_screen():
    """ Toggle between fullscreen mode and windowed mode
    :return: None
    """
    if ctrl.main.isFullScreen():
        ctrl.main.showNormal()
        log.info('(f) windowed')
        ctrl.ui.restore_panel_positions()
    else:
        ctrl.ui.store_panel_positions()
        ctrl.main.showFullScreen()
        log.info('(f) fullscreen')
    ctrl.graph_scene.fit_to_window(force=True)

a['fullscreen_mode'] = {'command': '&Fullscreen', 'method': toggle_full_screen,
                        'shortcut': 'f', 'undoable': False, 'checkable': True}
