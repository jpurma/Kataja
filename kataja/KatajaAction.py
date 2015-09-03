# coding=utf-8
# ############################################################################
#
# *** Kataja - Biolinguistic Visualization tool ***
#
# Copyright 2013 Jukka Purma
#
# This file is part of Kataja.
#
# Kataja is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Kataja is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kataja.  If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################
from PyQt5 import QtCore, QtWidgets, QtGui

from kataja.singletons import ctrl
from kataja.ui.OverlayButton import PanelButton
from kataja.ui.panels.field_utils import EmbeddedMultibutton


class KatajaAction(QtWidgets.QAction):
    """
    Command
    :param key:
    :param command:
    :param command_alt:
    :param exclusive_in:
    :param shortcut:
    :param shortcut_context:
    :param viewgroup:
    :param checkable:
    :param tooltip:
    :param undoable:
    :param method:
    """

    def __init__(self, key, command=None,
                 command_alt=None, shortcut=None,
                 shortcut_context=None, viewgroup=None, sender_arg=None,
                 exclusive=None, selection=None, checkable=None,
                 tooltip=None, action_arg=None,
                 undoable=None, method=None, args=None):
        super().__init__(ctrl.main)
        self.key = key
        self.command = command
        self.command_alt = command_alt
        self.sender_arg = sender_arg
        self.action_arg = action_arg
        self.setText(command)
        self.setData(key)
        self.undoable = undoable
        self.method = method
        self.args = args or []
        # when triggered from menu, forward the call to more complex trigger handler
        self.triggered.connect(self.action_triggered)

        # if action has shortcut_context, it shouldn't have global shortcut
        # in these cases shortcut is tied to ui_element.
        if shortcut:
            self.setShortcut(QtGui.QKeySequence(shortcut))
            if shortcut_context == 'parent_and_children':
                sc = QtCore.Qt.WidgetWithChildrenShortcut
            else:
                sc = QtCore.Qt.ApplicationShortcut
            self.setShortcutContext(sc)
            self.installEventFilter(ctrl.ui.shortcut_solver)
        if viewgroup:
            ag = ctrl.ui.get_action_group(viewgroup)
            self.setActionGroup(ag)
            if not exclusive:
                ag.setExclusive(False)
        if checkable:
            self.setCheckable(True)
        if tooltip:
            #if ctrl.main.use_tooltips:
            self.setToolTip(tooltip)
            self.setStatusTip(tooltip)

    def action_triggered(self):
        """ Trigger action with parameters received from action data object and designated UI element
        :return: None
        """
        # -- Redraw and undo flags: these are on by default, can be switched off by action method
        ctrl.action_redraw = True
        if self.sender_arg:
            args = [self.sender()]
        else:
            args = []
        if self.action_arg:
            args += [self]
        if self.args:
            args += self.args
        #print("Doing action '%s' with method '%s' and with sender %s and args: %s" %
        #      (self.key, self.method, self.sender(), str(args)))
        # Disable undo if necessary
        remember_undo_state = ctrl.undo_disabled
        if not self.undoable:
            ctrl.undo_disabled = True

        # Call method
        message = self.method(*args)

        # Restore undo state to what it was
        if not self.undoable:
            ctrl.undo_disabled = remember_undo_state
        ctrl.main.action_finished(m=message or self.command,
                                  undoable=self.undoable)

    def connect_element(self, element, tooltip_suffix=''):
        """

        :param element:
        :param tooltip_suffix:
        """

        tooltip = self.toolTip()
        if tooltip and not isinstance(element, EmbeddedMultibutton):
            if tooltip_suffix:
                print(tooltip)
                element.setStatusTip(tooltip % tooltip_suffix)
                if ctrl.main.use_tooltips:
                    element.setToolTip(tooltip % tooltip_suffix)
            else:
                element.setStatusTip(tooltip)
                if ctrl.main.use_tooltips:
                    element.setToolTip(tooltip)
            element.setToolTipDuration(2000)

        shortcut = self.shortcut()
        shortcut_context = self.shortcutContext()
        if shortcut and shortcut_context:
            ctrl.ui.manage_shortcut(shortcut, element, self)

        if isinstance(element, PanelButton):
            element.clicked.connect(self.action_triggered)
            element.setFocusPolicy(QtCore.Qt.TabFocus)
        elif isinstance(element, QtWidgets.QAbstractButton):
            element.clicked.connect(self.action_triggered)
            element.setFocusPolicy(QtCore.Qt.TabFocus)
        elif isinstance(element, QtWidgets.QComboBox):
            element.activated.connect(self.action_triggered)
            element.setFocusPolicy(QtCore.Qt.TabFocus)
        elif isinstance(element, QtWidgets.QAbstractSpinBox):
            element.valueChanged.connect(self.action_triggered)
        elif isinstance(element, QtWidgets.QCheckBox):
            element.stateChanged.connect(self.action_triggered)
        elif isinstance(element, EmbeddedMultibutton):
            element.bgroup.buttonToggled.connect(self.action_triggered)


