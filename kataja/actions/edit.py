# coding=utf-8
from kataja.KatajaAction import KatajaAction
from kataja.singletons import ctrl


class Cut(KatajaAction):
    k_action_uid = 'cut'
    k_command = 'Cut'
    k_tooltip = 'Cut element'
    k_shortcut = 'Ctrl+x'

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
            #if w:
            #    print(w)
        return False


class Copy(KatajaAction):
    k_action_uid = 'copy'
    k_command = 'Copy'
    k_tooltip = 'Copy element'
    k_shortcut = 'Ctrl+c'

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
    k_shortcut = 'Ctrl+v'

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
    k_shortcut = 'Ctrl+z'
    k_undoable = False

    def method(self):
        """ Undo -command triggered
        :return: None
        """
        ctrl.forest.undo_manager.undo()

    def enabler(self):
        return bool(ctrl.forest and ctrl.forest.undo_manager.can_undo())


class Redo(KatajaAction):
    k_action_uid = 'redo'
    k_command = 'Redo'
    k_tooltip = 'Redo element'
    k_shortcut = 'Ctrl+Shift+z'
    k_undoable = False

    def method(self):
        """ Redo -command triggered
        :return: None
        """
        ctrl.forest.undo_manager.redo()

    def enabler(self):
        return bool(ctrl.forest and ctrl.forest.undo_manager.can_redo())


