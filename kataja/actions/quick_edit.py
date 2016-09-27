# coding=utf-8
import random

from PyQt5 import QtGui
from kataja.KatajaAction import KatajaAction

from kataja.singletons import ctrl


class ToggleItalic(KatajaAction):
    k_action_uid = 'toggle_italic'
    k_command = 'Toggle italics'
    k_shortcut = 'Ctrl+i'
    k_shortcut_context = 'parent_and_children'

    def method(self):
        """

        :return:
        """
        sender = self.sender()
        fmt = QtGui.QTextCharFormat()
        fmt.setFontItalic(sender.isChecked())
        cursor = ctrl.text_editor_focus.textCursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(fmt)


class ToggleBold(KatajaAction):
    k_action_uid = 'toggle_bold'
    k_command = 'Toggle bold'
    k_shortcut = 'Ctrl+b'
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
        cursor = ctrl.text_editor_focus.textCursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(fmt)


class ToggleUnderline(KatajaAction):
    k_action_uid = 'toggle_underline'
    k_command = 'Toggle underline'
    k_shortcut = 'Ctrl+u'
    k_shortcut_context = 'parent_and_children'

    def method(self):
        """

        :return:
        """
        sender = self.sender()
        fmt = QtGui.QTextCharFormat()
        fmt.setFontUnderline(sender.isChecked())
        cursor = ctrl.text_editor_focus.textCursor()
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
        cursor = ctrl.text_editor_focus.textCursor()
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
            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignSubScript)
        else:
            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignNormal)
        cursor = ctrl.text_editor_focus.textCursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(fmt)


class ToggleSuperscript(KatajaAction):
    k_action_uid = 'toggle_superscript'
    k_command = 'Toggle superscript'
    k_shortcut = 'Ctrl+'
    k_shortcut_context = 'parent_and_children'

    def method(self):
        """

        :return:
        """
        sender = self.sender()
        fmt = QtGui.QTextCharFormat()
        if sender.isChecked():
            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignSuperScript)
        else:
            fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignNormal)
        cursor = ctrl.text_editor_focus.textCursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(fmt)


class RemoveStyles(KatajaAction):
    k_action_uid = 'remove_styles'
    k_command = 'Remove styles'

    def method(self):
        """

        :return:
        """
        fmt = QtGui.QTextCharFormat()
        fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignNormal)
        fmt.setFontStrikeOut(False)
        fmt.setFontUnderline(False)
        fmt.setFontWeight(QtGui.QFont.Normal)
        fmt.setFontItalic(False)
        cursor = ctrl.text_editor_focus.textCursor()
        if not cursor.hasSelection():
            cursor.select(QtGui.QTextCursor.WordUnderCursor)
        cursor.mergeCharFormat(fmt)
        ctrl.ui.quick_edit_buttons.update_formats(fmt)

