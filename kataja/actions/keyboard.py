# coding=utf-8
from PyQt6 import QtGui, QtCore

from kataja.KatajaAction import KatajaAction
from kataja.singletons import ctrl


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
        ctrl.multiselection_start()  # don't update selections until all are removed
        for item in list(ctrl.selected):
            ctrl.drawing.delete_item(item)
        ctrl.multiselection_end()  # ok go update
        ctrl.forest.forest_edited()


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
        else:
            # elif not getattr(ctrl.ui_focus, 'grab_cursor', False):
            # This is stupid but I haven't found a better solution that works
            print('key_up -action')
            key_event = QtGui.QKeyEvent(QtCore.QEvent.Type.KeyPress, QtCore.Qt.Key_Up,
                                        QtCore.Qt.NoModifier)
            ctrl.ui_focus.keyPressEvent(key_event)


class KeyDown(KatajaAction):
    k_action_uid = 'key_down'
    k_command = 'key_down'
    k_shortcut = 'Down'
    k_undoable = False

    def method(self):
        if not ctrl.ui_focus:
            ctrl.graph_scene.move_selection('down')
        else:  # This is stupid but I haven't found a better solution that works
            key_event = QtGui.QKeyEvent(QtCore.QEvent.Type.KeyPress, QtCore.Qt.Key_Down,
                                        QtCore.Qt.NoModifier)
            ctrl.ui_focus.keyPressEvent(key_event)
