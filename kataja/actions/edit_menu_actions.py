# coding=utf-8
from PyQt6.QtGui import QKeySequence

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


class Cut(KatajaAction):
    k_action_uid = 'cut'
    k_command = 'Cut'
    k_tooltip = 'Cut element'
    k_shortcut = QKeySequence(QKeySequence.StandardKey.Cut)

    def method(self):
        qclipboard = ctrl.main.app.clipboard()
        ctrl.clipboard = []
        if ctrl.selected:
            for item in ctrl.selected:
                if hasattr(item, 'cut'):
                    ctrl.clipboard.append(item.cut(ctrl.selected))
        print('Cut called')

    def enabler(self):
        if ctrl.selected:
            return True
        elif ctrl.main.app:
            w = ctrl.main.app.focusWidget()
            # if w:
            #    print(w)
        return False


class Copy(KatajaAction):
    k_action_uid = 'copy'
    k_command = 'Copy'
    k_tooltip = 'Copy element'
    k_shortcut = QKeySequence(QKeySequence.StandardKey.Copy)

    def method(self):
        ctrl.clipboard = []
        for item in ctrl.selected:
            if hasattr(item, 'clipboard_copy'):
                ctrl.clipboard.append(item.clipboard_copy(ctrl.selected))

    def enabler(self):
        if ctrl.selected:
            return True
        elif ctrl.main.app:
            w = ctrl.main.app.focusWidget()
            # if w:
            #    print(w)
        return False


class Paste(KatajaAction):
    k_action_uid = 'paste'
    k_command = 'Paste'
    k_tooltip = 'Paste element'
    k_shortcut = QKeySequence(QKeySequence.StandardKey.Paste)

    def method(self):
        print('Paste called')

    def enabler(self):
        if ctrl.main.app and ctrl.main.app.clipboard():
            mimeData = ctrl.main.app.clipboard().mimeData()
            return mimeData.hasImage() or mimeData.hasHtml() or mimeData.hasText()
        return False


class Undo(KatajaAction):
    k_action_uid = 'undo'
    k_command = 'Undo'
    k_tooltip = 'Undo element'
    k_shortcut = QKeySequence(QKeySequence.StandardKey.Undo)
    k_undoable = False

    def method(self):
        """ Undo -command triggered
        :return: None
        """
        ctrl.forest.undo_manager.undo()
        ctrl.forest.forest_edited()  # <-- watch out if this is correct thing to do in
        # visualisation mode

    def enabler(self):
        return bool(ctrl.forest and ctrl.forest.undo_manager and
                    ctrl.forest.undo_manager.can_undo())


class Redo(KatajaAction):
    k_action_uid = 'redo'
    k_command = 'Redo'
    k_tooltip = 'Redo element'
    k_shortcut = QKeySequence(QKeySequence.StandardKey.Redo)
    k_undoable = False

    def method(self):
        """ Redo -command triggered
        :return: None
        """
        ctrl.forest.undo_manager.redo()
        ctrl.forest.forest_edited()  # <-- watch out if this is correct thing to do in
        # visualisation mode

    def enabler(self):
        return bool(ctrl.forest and ctrl.forest.undo_manager and
                    ctrl.forest.undo_manager.can_redo())
