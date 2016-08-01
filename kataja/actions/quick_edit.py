# coding=utf-8
import random

from PyQt5 import QtCore, QtGui

import kataja.globals as g
from kataja.singletons import ctrl

a = {}


def toggle_italic(sender=None):
    """

    :return:
    """
    fmt = QtGui.QTextCharFormat()
    fmt.setFontItalic(sender.isChecked())
    cursor = ctrl.text_editor_focus.textCursor()
    if not cursor.hasSelection():
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
    cursor.mergeCharFormat(fmt)


a['toggle_italic'] = {'command': 'Toggle italics', 'method': toggle_italic, 'sender_arg': True,
                      'shortcut': 'Ctrl+i', 'shortcut_context': 'parent_and_children'}


def toggle_bold(sender=None):
    """

    :return:
    """
    fmt = QtGui.QTextCharFormat()
    if sender.isChecked():
        fmt.setFontWeight(QtGui.QFont.Bold)
    else:
        fmt.setFontWeight(QtGui.QFont.Normal)
    cursor = ctrl.text_editor_focus.textCursor()
    if not cursor.hasSelection():
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
    cursor.mergeCharFormat(fmt)


a['toggle_bold'] = {'command': 'Toggle bold', 'method': toggle_bold, 'sender_arg': True,
                    'shortcut': 'Ctrl+b', 'shortcut_context': 'parent_and_children'}


def toggle_underline(sender=None):
    """

    :return:
    """
    fmt = QtGui.QTextCharFormat()
    fmt.setFontUnderline(sender.isChecked())
    cursor = ctrl.text_editor_focus.textCursor()
    if not cursor.hasSelection():
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
    cursor.mergeCharFormat(fmt)


a['toggle_underline'] = {'command': 'Toggle underline', 'method': toggle_underline,
                         'sender_arg': True, 'shortcut': 'Ctrl+u',
                         'shortcut_context': 'parent_and_children'}


def toggle_strikethrough(sender=None):
    """

    :return:
    """
    fmt = QtGui.QTextCharFormat()
    fmt.setFontStrikeOut(sender.isChecked())
    cursor = ctrl.text_editor_focus.textCursor()
    if not cursor.hasSelection():
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
    cursor.mergeCharFormat(fmt)


a['toggle_strikethrough'] = {'command': 'Toggle strikethrough', 'method': toggle_strikethrough,
                             'sender_arg': True, 'shortcut': 'Ctrl+shift+u',
                             'shortcut_context': 'parent_and_children'}


def toggle_subscript(sender=None):
    """

    :return:
    """
    fmt = QtGui.QTextCharFormat()
    if sender.isChecked():
        fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignSubScript)
    else:
        fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignNormal)
    cursor = ctrl.text_editor_focus.textCursor()
    if not cursor.hasSelection():
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
    cursor.mergeCharFormat(fmt)


a['toggle_subscript'] = {'command': 'Toggle subscript', 'method': toggle_subscript,
                         'sender_arg': True, 'shortcut': 'Ctrl+_',
                         'shortcut_context': 'parent_and_children'}


def toggle_superscript(sender=None):
    """

    :return:
    """
    fmt = QtGui.QTextCharFormat()
    if sender.isChecked():
        fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignSuperScript)
    else:
        fmt.setVerticalAlignment(QtGui.QTextCharFormat.AlignNormal)
    cursor = ctrl.text_editor_focus.textCursor()
    if not cursor.hasSelection():
        cursor.select(QtGui.QTextCursor.WordUnderCursor)
    cursor.mergeCharFormat(fmt)


a['toggle_superscript'] = {'command': 'Toggle superscript', 'method': toggle_superscript,
                           'sender_arg': True, 'shortcut': 'Ctrl+^',
                           'shortcut_context': 'parent_and_children'}


def remove_styles():
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


a['remove_styles'] = {'command': 'Remove styles', 'method': remove_styles,
                      'shortcut_context': 'parent_and_children'}



