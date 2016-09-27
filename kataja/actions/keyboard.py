# coding=utf-8
from kataja.singletons import ctrl
from kataja.KatajaAction import KatajaAction


class KeyBackspace(KatajaAction):
    k_action_uid = 'key_backspace'
    k_command = 'key_backspace'
    k_shortcut = 'Backspace'

    def method(self):
        """ In many contexts this will delete something. Expand this as necessary
        for contexts that don't otherwise grab keyboard.
        :return: None
        """
        print('key_backspace - action')
        ctrl.multiselection_start() # don't update selections until all are removed
        for item in list(ctrl.selected):
            ctrl.forest.delete_item(item)
        ctrl.multiselection_end() # ok go update


class KeyLeft(KatajaAction):
    k_action_uid = 'key_left'
    k_command = 'key_left'
    k_shortcut = 'Left'
    k_undoable = False

    def method(self):
        if not ctrl.ui_focus:
            ctrl.graph_scene.move_selection('left')


class KeyRight(KatajaAction):
    k_action_uid = 'key_right'
    k_command = 'key_right'
    k_shortcut = 'Right'
    k_undoable = False

    def method(self):
        if not ctrl.ui_focus:
            ctrl.graph_scene.move_selection('right')


class KeyUp(KatajaAction):
    k_action_uid = 'key_up'
    k_command = 'key_up'
    k_shortcut = 'Up'
    k_undoable = False

    def method(self):
        if not ctrl.ui_focus:
            ctrl.graph_scene.move_selection('up')


class KeyDown(KatajaAction):
    k_action_uid = 'key_down'
    k_command = 'key_down'
    k_shortcut = 'Down'
    k_undoable = False

    def method(self):
        if not ctrl.ui_focus:
            ctrl.graph_scene.move_selection('down')
