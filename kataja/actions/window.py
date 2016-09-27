# coding=utf-8

from kataja.singletons import ctrl, log
from kataja.KatajaAction import KatajaAction


class ToggleAllPanels(KatajaAction):
    k_action_uid = 'toggle_all_panels'
    k_command = 'hide or show all panels'
    k_undoable = False


class TogglePanel(KatajaAction):
    k_dynamic = True
    k_checkable = True
    k_viewgroup = 'Panels'
    k_undoable = False
    k_exclusive = False
    k_tooltip = 'Close this panel'

    def method(self, panel_id):
        """ Show or hide panel depending if it is visible or not
        :param panel_id: enum of panel identifiers (str)
        """
        ctrl.ui.toggle_panel(self, panel_id)


class ToggleFoldPanel(KatajaAction):
    k_action_uid = 'toggle_fold_panel'
    k_command = 'Fold panel'
    k_checkable = True
    k_undoable = False
    k_tooltip = 'Minimize this panel'

    def method(self):
        """ Fold panel into label line or reveal the whole panel.
        """
        panel = self.get_ui_container()
        if panel:
            panel.set_folded(not panel.folded)


class PinPanel(KatajaAction):
    k_action_uid = 'pin_panel'
    k_command = 'Pin to dock'
    k_undoable = False

    def method(self):
        """ Put panel back to panel dock area.
        """
        panel = self.get_ui_container()
        if panel:
            panel.pin_to_dock()


class ToggleFullScreen(KatajaAction):
    k_action_uid = 'fullscreen_mode'
    k_command = '&Fullscreen'
    k_undoable = False
    k_shortcut = 'f'
    k_checkable = True

    def method(self):
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
