# coding=utf-8

from PyQt6 import QtGui
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

# quick_edit contains actions related to text editing, those active when 'quick_edit_mode' is on.


class ToggleItalic(KatajaAction):
    k_action_uid = 'toggle_italic'
    k_command = 'Toggle italics'
    k_shortcut = QKeySequence(QKeySequence.StandardKey.Italic)
    k_shortcut_context = 'parent_and_children'

    def method(self):
        """

        :return:
        """
        sender = self.sender()
        fmt = QtGui.QTextCharFormat()
        fmt.setFontItalic(sender.isChecked())
        cursor = ctrl.text_editor_focus.cursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(fmt)


class ToggleBold(KatajaAction):
    k_action_uid = 'toggle_bold'
    k_command = 'Toggle bold'
    k_shortcut = QKeySequence(QKeySequence.StandardKey.Bold)
    k_shortcut_context = 'parent_and_children'

    def method(self):
        """

        :return:
        """
        sender = self.sender()
        fmt = QtGui.QTextCharFormat()
        if sender.isChecked():
            fmt.setFontWeight(QtGui.QFont.Bold)
        else:
            fmt.setFontWeight(QtGui.QFont.Normal)
        cursor = ctrl.text_editor_focus.cursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(fmt)


class ToggleUnderline(KatajaAction):
    k_action_uid = 'toggle_underline'
    k_command = 'Toggle underline'
    k_shortcut = QKeySequence(QKeySequence.StandardKey.Underline)
    k_shortcut_context = 'parent_and_children'

    def method(self):
        """

        :return:
        """
        sender = self.sender()
        fmt = QtGui.QTextCharFormat()
        fmt.setFontUnderline(sender.isChecked())
        cursor = ctrl.text_editor_focus.cursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(fmt)


class ToggleStrikethrough(KatajaAction):
    k_action_uid = 'toggle_strikethrough'
    k_command = 'Toggle strikethrough'
    k_shortcut = 'Ctrl+Shift+u'
    k_shortcut_context = 'parent_and_children'

    def method(self):
        """

        :return:
        """
        sender = self.sender()
        fmt = QtGui.QTextCharFormat()
        fmt.setFontStrikeOut(sender.isChecked())
        cursor = ctrl.text_editor_focus.cursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(fmt)


class ToggleSubscript(KatajaAction):
    k_action_uid = 'toggle_subscript'
    k_command = 'Toggle subscript'
    k_shortcut = 'Ctrl+_'
    k_shortcut_context = 'parent_and_children'

    def method(self):
        """

        :return:
        """
        sender = self.sender()
        fmt = QtGui.QTextCharFormat()
        if sender.isChecked():
            fmt.setVerticalAlignment(QtGui.QTextCharFormat.VerticalAlignment.AlignSubScript)
        else:
            fmt.setVerticalAlignment(QtGui.QTextCharFormat.VerticalAlignment.AlignNormal)
        cursor = ctrl.text_editor_focus.cursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        cursor.mergeCharFormat(fmt)


class ToggleSuperscript(KatajaAction):
    k_action_uid = 'toggle_superscript'
    k_command = 'Toggle superscript'
    k_shortcut = 'Ctrl+^'
    k_shortcut_context = 'parent_and_children'

    def method(self):
        """

        :return:
        """
        sender = self.sender()
        fmt = QtGui.QTextCharFormat()
        if sender.isChecked():
            fmt.setVerticalAlignment(QtGui.QTextCharFormat.VerticalAlignment.AlignSuperScript)
        else:
            fmt.setVerticalAlignment(QtGui.QTextCharFormat.VerticalAlignment.AlignNormal)
        cursor = ctrl.text_editor_focus.cursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        cursor.mergeCharFormat(fmt)


class RemoveStyles(KatajaAction):
    k_action_uid = 'remove_styles'
    k_command = 'Remove styles'

    def method(self):
        """

        :return:
        """
        fmt = QtGui.QTextCharFormat()
        fmt.setVerticalAlignment(QtGui.QTextCharFormat.VerticalAlignment.AlignNormal)
        fmt.setFontStrikeOut(False)
        fmt.setFontUnderline(False)
        fmt.setFontWeight(QtGui.QFont.Weight.Normal)
        fmt.setFontItalic(False)
        cursor = ctrl.text_editor_focus.cursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
        ctrl.ui.quick_edit_buttons.update_formats(fmt)
