from PyQt5 import QtWidgets, QtCore

import kataja.debug as debug
from kataja.singletons import ctrl

__author__ = 'purma'

class ShortcutSolver(QtCore.QObject):
    """ I want to have Shortcuts available in Menus and also to have 'button clicked' effect in panels when the
    relevant shortcut is pressed. Qt doesn't like ambiguous shortcuts, so we interrupt those and only pseudo-click
    the button in those cases.

    :param ui_manager:
    """

    def __init__(self, ui_manager):
        QtCore.QObject.__init__(self)
        self.ui_manager = ui_manager

    def eventFilter(self, action, event):
        if event.type() == QtCore.QEvent.Shortcut and event.isAmbiguous():
            print('Dealing with ambiguous action shortcut, ', action, action.isEnabled(), action.data())
            act_data = self.ui_manager.actions[action.data()]
            element = act_data.get('ui_element', None)
            if element and isinstance(element, QtWidgets.QAbstractButton):
                assert(element.isVisible())
                print('Coming from element, ', element, element.isVisible())
                if element.isVisible():
                    element.animateClick()
                    return True
            else:
                print("Don't know how to handle this ambiguous shortcut in ", action)
        return False

class ButtonShortcutFilter(QtCore.QObject):
    """ For some reason button shortcut sometimes focuses instead of clicks.

    """

    def eventFilter(self, button, event):
        if event.type() == QtCore.QEvent.Shortcut:
            button.animateClick()
            return True
        return False
    # events:
    # paint: 12
    # WindowActivate: 24
    # WindowDeactivate: 25
    # StatusTip: 112
    # HoverLeave: 127
    # HoverEnter: 128
    # Enter: 10
    # Leave: 11
    # Timer: 1
    # Shortcut: 117
    # ShortcutOerride: 51
    # Move: 13
    #



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

        ks = event.text()
        debug.keys('received key press: ', ks)
        self.ui_manager.add_feedback_from_command(ks)
        #if ctrl.selected and all([item.can_take_keyevent(event) for item in ctrl.selected]):
        #    for item in ctrl.selected:
        #        item.take_keyevent(event)
        #    return True

        act = self._shortcuts.get(ks)
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

    def key_tab(self):
        """ Tab pressed, move focus to next whatever"""
        print('tab-tab!')

