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
import sys
import traceback

from PyQt5 import QtCore, QtWidgets, QtGui

from kataja.singletons import ctrl
from kataja.ui.OverlayButton import PanelButton
from kataja.ui.elements.EmbeddedMultibutton import EmbeddedMultibutton


class ShortcutSolver(QtCore.QObject):
    """ I want to have Shortcuts available in Menus and also to have 'button clicked' effect in
    panels when the relevant shortcut is pressed. Qt doesn't like ambiguous shortcuts,
    so we interrupt those and only pseudo-click the button in those cases.

    :param ui_manager:
    """

    def __init__(self, ui_manager):
        QtCore.QObject.__init__(self)
        self.ui_manager = ui_manager
        self.clickable_actions = {}
        self.watched_elements = set()

    def eventFilter(self, action, event):
        """

        :param action:
        :param event:
        :return:
        """
        if event.type() == QtCore.QEvent.Shortcut and event.isAmbiguous():
            key = event.key().toString()
            if key in self.clickable_actions:
                els = self.clickable_actions.get(key, [])
                for e in els:
                    if e.isVisible():
                        e.animateClick()
                        return True
                return True
            else:
                print('couldnt solve ambiguous action: ', action.command, action.key, event, key,
                      self.clickable_actions)
        return False

    def add_solvable_action(self, key_seq, element):
        """

        :param key_seq: QKeySequence
        :return:
        """
        key = key_seq.toString()
        if key not in self.clickable_actions:
            self.clickable_actions[key] = [element]
            self.watched_elements.add(element)
        else:
            self.clickable_actions[key].append(element)
            self.watched_elements.add(element)

    def remove_solvable_action(self, element):
        if element in self.watched_elements:
            self.watched_elements.remove(element)
            for key, value in self.clickable_actions.items():
                if element in value:
                    value.remove(element)
                    self.clickable_actions[key] = value


class ButtonShortcutFilter(QtCore.QObject):
    """ For some reason button shortcut sometimes focuses instead of clicks. """
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


class KatajaAction(QtWidgets.QAction):
    """
    Command
    :param key:
    :param command:
    :param command_alt:
    :param exclusive:
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
                 tooltip=None, action_arg=None, trigger_args=False,
                 undoable=True, method=None, args=None):
        super().__init__(ctrl.main)
        self.key = key
        self.command = command
        self.command_alt = command_alt
        self.sender_arg = sender_arg
        self.action_arg = action_arg
        self.trigger_args = trigger_args
        self.setText(command)
        self.setData(key)
        self.undoable = undoable
        self.method = method
        self.args = args or []
        self.tip = tooltip or command
        self.disable_undo_and_message = False
        # when triggered from menu, forward the call to more complex trigger handler
        self.triggered.connect(self.action_triggered)

        # if action has shortcut_context, it shouldn't have global shortcut
        # in these cases shortcut is tied to ui_element.
        if shortcut:
            self.setShortcut(QtGui.QKeySequence(shortcut))
            # those actions that have shortcut context are tied to (possibly nonexisting) UI
            # widgets and they can resolve ambiguous shortcuts only when the UI widgets are
            # connected. So disable these actions until the connection has been made.
            if shortcut_context == 'parent_and_children':
                sc = QtCore.Qt.WidgetWithChildrenShortcut
                self.setEnabled(False)
            elif shortcut_context == 'widget':
                sc = QtCore.Qt.WidgetShortcut
                self.setEnabled(False)
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

    def action_triggered(self, *args, **kwargs):
        """ Trigger action with parameters received from action data object and designated UI element
        :param sender: optional sender object if triggered manually
        :return: None
        """
        if self.trigger_args:
            trigger_args = list(args) + self.args
        else:
            trigger_args = self.args
        if not self.isEnabled():
            return
        # -- Redraw and undo flags: these are on by default, can be switched off by action method
        ctrl.action_redraw = True
        if self.sender_arg:
            if not 'sender' in kwargs:
                kwargs['sender'] = self.sender()
        if self.action_arg:
            kwargs['action'] = self
        # Disable undo if necessary
        if not self.undoable:
            ctrl.disable_undo()

        # Call method
        try:
            print(trigger_args, kwargs)
            message = self.method(*trigger_args, **kwargs)
        except:
            e = sys.exc_info()[1]
            message = str(e)
            print("Unexpected error:", e)
            traceback.print_exc()
        # Restore undo state to what it was
        if not self.undoable:
            ctrl.resume_undo()
        if self.disable_undo_and_message:
            ctrl.main.action_finished(undoable=False)
        else:
            ctrl.main.action_finished(m=message or self.command,
                                      undoable=self.undoable and not ctrl.undo_disabled)

    def trigger_but_suppress_undo(self, *args, **kwargs):
        ctrl.disable_undo()
        self.disable_undo_and_message = True
        self.action_triggered(*args, **kwargs)
        self.disable_undo_and_message = False
        ctrl.resume_undo()


    def connect_element(self, element, tooltip_suffix=''):
        """

        :param element:
        :param tooltip_suffix:
        """

        tooltip = self.toolTip()
        if tooltip and not isinstance(element, EmbeddedMultibutton):
            if tooltip_suffix:
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
            # shortcuts (or actions in total were disabled before this connection to avoi)
            self.setEnabled(True)

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
            element.valueChanged.connect(self.trigger_but_suppress_undo)
            element.editingFinished.connect(self.action_triggered)
        elif isinstance(element, QtWidgets.QCheckBox):
            element.stateChanged.connect(self.action_triggered)
        elif isinstance(element, EmbeddedMultibutton):
            element.bgroup.buttonToggled.connect(self.action_triggered)


