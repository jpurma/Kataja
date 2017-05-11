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
import logging

from PyQt5 import QtCore, QtWidgets, QtGui

from kataja.singletons import ctrl, log, running_environment
from kataja.ui_widgets.OverlayButton import PanelButton
from kataja.ui_support.EmbeddedRadiobutton import EmbeddedRadiobutton
from kataja.ui_support.SelectionBox import SelectionBox
from kataja.ui_graphicsitems.TouchArea import TouchArea


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
    """ Actions are defined as classes that have only one instance. Action method()
    performs the actual work, but class variables below can be used to finetune how action is
    presented for the user.
     """
    k_action_uid = ''
    k_command = ''
    k_command_alt = ''
    k_tooltip = ''
    k_tooltip_alt = ''
    k_undoable = True
    k_shortcut_context = ''
    k_shortcut = ''
    k_exclusive = False
    k_checkable = False
    k_viewgroup = False
    k_start_animations = False

    def __init__(self):
        super().__init__(ctrl.main)
        self.key = self.k_action_uid
        self.elements = set()
        self.command = self.k_command
        self.command_alt = self.k_command_alt
        self.state_arg = None  # used to hold button states, or whatever activated triggers send
        self.args = []
        if self.command:
            self.setText(self.command)
        self.setData(self.key)
        self.transit_menus = []
        self.host_menu = None
        self.undoable = self.k_undoable
        self.tip0 = self.k_tooltip or self.command
        self.tip1 = self.k_tooltip_alt or self.command_alt or self.tip0
        self.disable_undo_and_message = False
        # when triggered from menu, forward the call to more complex trigger handler
        self.triggered.connect(self.action_triggered)
        shortcut = self.k_shortcut
        # if action has shortcut_context, it shouldn't have global shortcut
        # in these cases shortcut is tied to ui_element.
        if shortcut:
            self.setShortcut(QtGui.QKeySequence(shortcut))
            # those actions that have shortcut context are tied to (possibly nonexisting) UI
            # widgets and they can resolve ambiguous shortcuts only when the UI widgets are
            # connected. So disable these actions until the connection has been made.
            if self.k_shortcut_context == 'parent_and_children':
                sc = QtCore.Qt.WidgetWithChildrenShortcut
                self.setEnabled(False)
            elif self.k_shortcut_context == 'widget':
                sc = QtCore.Qt.WidgetShortcut
                self.setEnabled(False)
            else:
                sc = QtCore.Qt.ApplicationShortcut
            self.setShortcutContext(sc)
            self.installEventFilter(ctrl.ui.shortcut_solver)
            self.tip0, self.tip1 = self.tips_with_shortcuts()
        if self.k_viewgroup:
            ag = ctrl.ui.get_action_group(self.k_viewgroup)
            self.setActionGroup(ag)
            ag.setExclusive(self.k_exclusive)
        self.setCheckable(self.k_checkable)
        self.setToolTip(self.tip0)
        self.setStatusTip(self.tip0)

    def prepare_parameters(self):
        return [], {}

    def method(self, *args, **kwargs):
        pass

    def enabler(self):
        return True

    def getter(self):
        return None

    def action_triggered(self, *args, **kwargs):
        """ Trigger action with parameters received from action data object and designated UI element
        :param state_arg: argument provided by some triggers, e.g. toggle buttons. We don't forward
         this, instead it is saved in self.state_arg, method can use it from there if needed.
        :return: None
        """

        if not self.isEnabled():
            return
        #self.state_arg = state_arg
        # -- Redraw and undo flags: these are on by default, can be switched off by action method
        ctrl.action_redraw = True
        # Disable undo if necessary
        if not self.undoable:
            ctrl.disable_undo()

        sender = self.sender()

        # Some rare triggers pass values, e.g. ButtonGroups pass the id of button.
        # prepare_parameters should put these to args, kwargs, but we don't want to burden that
        # method with parameters, so keep store them as instance variables.
        if args:
            self.args = args

        if sender and sender != ctrl.ui.command_prompt:
            args, kwargs = self.prepare_parameters()

        autoplay = self.k_start_animations or not ctrl.free_drawing_mode

        # Print the command into console
        arg_parts = [repr(a) for a in args]
        kwarg_parts = [f'{key}={repr(value)}' for key, value in kwargs.items()]
        argstring = ', '.join(arg_parts + kwarg_parts)
        print(f'>>> {self.k_action_uid}({argstring})')
        try:
            message = self.method(*args, **kwargs)
            error = None
        except:
            message = ''
            error = "Action %r ('%s')<br/>" % (self, self.key)
            error += '<br/>'.join(traceback.format_exception(*sys.exc_info()))
            print("Unexpected error:", sys.exc_info())
            traceback.print_exc()
        # Restore undo state to what it was
        if not self.undoable:
            ctrl.resume_undo()
        if self.disable_undo_and_message:
            ctrl.main.action_finished(undoable=False, play=autoplay)
        else:
            sc = self.shortcut()
            if sc:
                sc = sc.toString()
                sc = sc.replace('Ctrl', running_environment.cmd_or_ctrl)
                reply = f'({sc}) {message or self.command}'
            else:
                reply = message or self.command
            ctrl.main.action_finished(m=reply, undoable=self.undoable and not ctrl.undo_disabled,
                                      error=error, play=autoplay)

    def update_action(self):
        """ If action is tied to some meter (e.g. number field that is used to show value and
        change it), update the value in the meter and see if it should be enabled.
        :return:
        """
        on = self.enabler()
        self.set_enabled(on)
        val = self.getter()
        if val is not None:
            self.set_displayed_value(val)

    def tips_with_shortcuts(self):
        sc = self.shortcut()
        if sc:
            if isinstance(sc, QtGui.QKeySequence):
                sc = sc.toString()
                sc = sc.replace('Ctrl', running_environment.cmd_or_ctrl)
            return f'{self.tip0} ({sc})', f'{self.tip1} ({sc})'
        else:
            return self.tip0, self.tip1

    def update_ui_value(self):
        """ This can be called for manually updating the field values for element, e.g. when
        having to update numbers while dragging. update_action is automatic, but called only
        between actions
        :return:
        """
        val = self.getter()
        if val is not None:
            self.set_displayed_value(val)

    def trigger_but_suppress_undo(self, *args, **kwargs):
        ctrl.disable_undo()
        self.disable_undo_and_message = True
        self.action_triggered(*args, **kwargs)
        self.disable_undo_and_message = False
        ctrl.resume_undo()

    def connect_element(self, element, connect_slot=None):
        """

        :param element:
        """
        self.elements.add(element)

        tooltip = self.toolTip()
        if tooltip:
            self.set_tooltip_for_element(tooltip, element)

        # gray out ui element and its label if action is disabled
        if hasattr(element, 'setEnabled'):
            element.setEnabled(self.isEnabled())
        if hasattr(element, 'k_buddy') and element.k_buddy:
            element.k_buddy.setEnabled(self.isEnabled())
        if self.isCheckable() and hasattr(element, 'setCheckable'):
            element.setCheckable(True)
        shortcut = self.shortcut()
        shortcut_context = self.shortcutContext()
        if shortcut and shortcut_context:
            ctrl.ui.manage_shortcut(shortcut, element, self)
            # shortcuts (or actions in total were disabled before this connection to avoid
            # accidental firings)
            #self.setEnabled(True)
        if isinstance(element, QtWidgets.QWidget):
            element.setFocusPolicy(QtCore.Qt.TabFocus)

        if connect_slot:
            connect_slot.connect(self.action_triggered)
        elif isinstance(element, PanelButton):
            element.clicked.connect(self.action_triggered)
            element.setFocusPolicy(QtCore.Qt.TabFocus)
        elif isinstance(element, EmbeddedRadiobutton):
            element.bgroup.buttonToggled.connect(self.action_triggered)
        elif isinstance(element, QtWidgets.QCheckBox):
            element.stateChanged.connect(self.action_triggered)
        elif isinstance(element, QtWidgets.QAbstractButton):
            element.clicked.connect(self.action_triggered)
            element.setFocusPolicy(QtCore.Qt.TabFocus)
        elif isinstance(element, QtWidgets.QButtonGroup):
            element.buttonClicked.connect(self.action_triggered)
        elif isinstance(element, QtWidgets.QComboBox):
            element.activated.connect(self.action_triggered)
            element.setFocusPolicy(QtCore.Qt.TabFocus)
        elif isinstance(element, QtWidgets.QAbstractSpinBox):
            element.valueChanged.connect(self.trigger_but_suppress_undo)
            element.editingFinished.connect(self.action_triggered)
        elif isinstance(element, QtWidgets.QAbstractSlider):
            element.sliderMoved.connect(self.trigger_but_suppress_undo)
            element.sliderReleased.connect(self.action_triggered)
        elif isinstance(element, TouchArea):
            element.clicked.connect(self.action_triggered)

    def disconnect_element(self, element):
        if element in self.elements:
            self.elements.remove(element)

    @staticmethod
    def set_tooltip_for_element(tooltip, element):
        if isinstance(element, QtWidgets.QGraphicsObject):
            # These don't have setStatusTip
            element.status_tip = tooltip
        else:
            try:
                element.setStatusTip(tooltip)
                element.setToolTipDuration(2000)
            except AttributeError:
                return
        if ctrl.main.use_tooltips:
            element.setToolTip(tooltip)

    def set_enabled(self, value):
        """ Sets the action enabled/disabled and also the connected ui_items.
        :param value:
        :return:
        """
        value = bool(value)
        old_v = self.isEnabled()
        self.setEnabled(value)
        if old_v != value and self.elements:
            for item in self.elements:
                if hasattr(item, 'setEnabled'):
                    item.setEnabled(value)
                k_label = getattr(item, 'k_buddy', None)
                if k_label:
                    k_label.setEnabled(value)

    def set_displayed_value(self, value):
        """ Call ui_items that are related to this action and try to update them to show value
        given here. Can be boolean for checkboxes or menu items, something more complex if the
        ui_items support it.
        :param value:
        :return:
        """
        #print('setting displayed value for %s to %s' % (self.key, value))
        if self.isCheckable():
            for element in self.elements:
                element.blockSignals(True)
                if value != element.isChecked():
                    element.setChecked(value)
                    if value:
                        self.set_tooltip_for_element(self.tip1, element)
                    else:
                        self.set_tooltip_for_element(self.tip0, element)
                element.blockSignals(False)
        else:
            for element in self.elements:
                if isinstance(element, SelectionBox):
                    element.blockSignals(True)
                    if element.uses_data:
                        element.select_by_data(value)
                    else:
                        element.select_by_text(value)
                    element.blockSignals(False)
                elif hasattr(element, 'setValue'):
                    element.blockSignals(True)
                    element.setValue(value)
                    element.blockSignals(False)
                elif isinstance(element, QtWidgets.QAbstractButton):
                    element.blockSignals(True)
                    element.setText(value)
                    element.blockSignals(False)
            for menu in self.transit_menus:
                menu.blockSignals(True)
                if menu.key == value:
                    menu.setChecked(True)
                else:
                    menu.setChecked(False)
                menu.blockSignals(False)

    def get_ui_container(self):
        """ Traverse qt-objects until something governed by UIManager is
        found. Return this.
        :return:
        """
        sender = self.sender()

        def _ui_container(qt_object):
            if getattr(qt_object, 'ui_key', None):
                return qt_object
            else:
                p = qt_object.parent()
                if p:
                    return _ui_container(p)
                else:
                    return None

        if not sender:
            print('couldnt receive sender!')
            return None
        return _ui_container(sender)

    def get_host(self):
        """ Get the Kataja object that this action is about, the 'host' element.
        :return:
        """
        container = self.get_ui_container()
        if container:
            return container.host

    def set_checked_for(self, menu_key, value):
        """ There may be several menu items representing one (parametrised) action.
        :return:
        """
        for menu in self.transit_menus:
            if menu.key == menu_key:
                menu.setChecked(value)


class TransmitAction(QtWidgets.QAction):

    def __init__(self, text='', target=None, key=''):
        QtWidgets.QAction.__init__(self, text)
        self.key = key
        self.target = target
        self.triggered.connect(target.trigger)
        self.setCheckable(True)
        target.transit_menus.append(self)

