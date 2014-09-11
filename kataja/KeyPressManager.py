from PyQt5 import QtWidgets, QtCore

import kataja.debug as debug
from kataja.singletons import ctrl

__author__ = 'purma'

class KeyPressManager:

    def __init__(self, main):
        self.main = main
        self.ui_manager = main.ui_manager
        self._shortcuts = {}
        self.build_shortcuts()

    #### build action dict ###############

    def build_shortcuts(self):
        for qaction in self.ui_manager.qt_actions.values():
            sclist = qaction.shortcuts()
            if sclist:
                for sc in sclist:
                    self._shortcuts[sc.toString()] = qaction
        debug.keys(self._shortcuts)


    #### Key presses ###################################################################

    def receive_key_press(self, event):
        """ keyPresses are intercepted here and some feedback of them is given,
        :param event:
        then they are delegated further """

        kc = event.key()
        ks = event.text()
        debug.keys('received key press: ', ks)
        self.ui_manager.add_feedback_from_command(ks)
        if ctrl.selected and all([item.can_take_keyevent(event) for item in ctrl.selected]):
            for item in ctrl.selected:
                item.take_keyevent(event)
            return True

        act = self._shortcuts.get(k)
        if act:
            debug.keys('triggering action ', act.data())
            act.trigger()
            self.ui_manager.show_command_prompt()
            return True
        else:
            self.ui_manager.show_command_prompt()
            return False


    def key_press(self, event):
        """ Other widgets can send their key presses here for global navigation
        :param event:
        """
        key = event.key()
        debug.keys("key_press:", key)
        qtkey = QtCore.Qt.Key
        focus = ctrl.focus  # : :type focus: Movable

        if key == qtkey.Key_Down:
            if not focus:
                if self.forest.roots:
                    self.forest.roots[0].take_focus()
            else:
                focus.move_focus_down()
        elif key == qtkey.Key_Right:
            if not focus:
                if self.forest.roots:
                    self.forest.roots[0].take_focus()
            else:
                focus.move_focus_right()
        elif key == qtkey.Key_Up:
            if not focus:
                if self.forest.roots:
                    self.forest.roots[0].take_focus()
            else:
                focus.move_focus_up()
        elif key == qtkey.Key_Left:
            if not focus:
                if self.forest.roots:
                    self.forest.roots[0].take_focus()
            else:
                focus.move_focus_left()
        elif key == qtkey.Key_Space:
            if focus:
                focus.activate_menu()
        elif key == qtkey.Key_Enter or key == qtkey.Key_Return:
            if focus:
                focus.trigger_menu()


    # ### Keyboard reading ######################################################

    # Since QGraphicsItems cannot have actions and action shortcuts tend to
    # override QGraphicsItems' keyevents, we can make main window's actions as general mechanism
    # for delivering keypresses to further items.

    def key_backspace(self):
        """


        """
        for item in ctrl.selected:
            item.undoable_delete()
        self.action_finished()


    def key_return(self, **kw):
        """

        :param kw:
        """
        if ctrl.ui_focus:
            pass
        elif ctrl.selected:
            for item in ctrl.selected:
                if hasattr(item, 'click'):
                    item.click(None)

    def key_m(self):
        """


        """
        if ctrl.single_selection():
            item = ctrl.get_selected()
            if isinstance(item, ConstituentNode):
                print('merge up, missing function call here')
                assert False

    def key_left(self):
        """ Move selection left """
        if not ctrl.ui_focus:
            self.graph_scene.move_selection('left')

    def key_right(self):
        """ Move selection right """
        if not ctrl.ui_focus:
            self.graph_scene.move_selection('right')

    def key_up(self):
        """ Move selection up """
        if not ctrl.ui_focus:
            self.graph_scene.move_selection('up')

    def key_down(self):
        """ Move selection down """
        if not ctrl.ui_focus:
            self.graph_scene.move_selection('down')

    def key_esc(self):
        """ Esc pressed, escape from current menu/focus/action """
        if ctrl.ui_focus:
            ui_focus = ctrl.ui_focus  # : :type ui_focus = MovableUI
            ui_focus.cancel()
        for item in ctrl.on_cancel_delete:
            self.forest.delete_item(item)

    def key_tab(self):
        """ Tab pressed, move focus to next whatever"""
        print('tab-tab!')

