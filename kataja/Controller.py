# -*- coding: UTF-8 -*-
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

from kataja.utils import caller


# gc.set_debug(gc.DEBUG_LEAK)

# flags = (gc.DEBUG_COLLECTABLE |
# gc.DEBUG_UNCOLLECTABLE |
# gc.DEBUG_OBJECTS
# )
# gc.set_debug(flags)


class Controller:
    """ Controller provides
    a) access to shared objects or objects upstream in containers.
    b) selected objects
    c) focused UI object
    d) capability to send announcements, which are announcement_id + argument
    that is sent to all objects that listen
    to such announcements. These can be used to e.g. send requests to update
    ui_support elements without having to know what
    elements there are.
    e) capability to send Qt signals as main application.
    """

    def __init__(self):
        # self.set_prefs('default')
        # : :type self.main: KatajaMain

        self.main = None
        self.watchers = {}
        self.structure = None
        self.selected = []
        self.selected_root = None
        self.rootmarker = '/'
        self.pointing_mode = False
        self.pointing_method = None
        self.pointing_data = {}
        self.pressed = None  # set() # prepare for multitouch
        self.ui_pressed = None  # set() # different coordinates to pressed set
        self.text_editor_focus = None
        self.free_drawing_mode = True
        self.dragged_focus = None
        self.dragged_set = set()
        self.dragged_groups = set()
        self.drag_hovering_on = None  # used only while dragging, because
        # standard hovering doesn't work while dragging
        self.ui_focus = None
        self.focus_point = None
        self.selection_tool = False
        self.move_tool = False
        self.area_selection = False
        self.references_to_fix = []
        self.rebuild_dict = {}
        self.print_garbage = True
        self.focus = None
        self.undo_disabled = 0  # stacking flag that affects if pickle.load assumes
        # an empty workspace (loading new) or if it tries to compare changes
        # (undo).
        self.watchers_disabled = False # flag to suppress watchers -- not
        # sure if it is *ever* a good idea
        self.unassigned_objects = {}
        self.items_moving = False
        self.multiselection_delay = False
        # -- After user action, should the visualization be redrawn and
        # should it make an undo savepoint
        # these are True by default, but action method may toggle them off
        # temporarily. The next action will
        # set these back on.
        self.action_redraw = True
        self.undo_pile = set()
        # ---------------------------

    def late_init(self, main):
        """

        :param main: KatajaMain
        """
        self.main = main

    @property
    def FL(self):
        """
        :return: BaseFL
        """
        return self.main.FL

    @property
    def ui(self):
        """
        :return: UIManager
        """
        return self.main.ui_manager

    @property
    def cm(self):
        """ Shortcut to color manager, which replaces palettes, colors etc.
        older solutions.
        :return: PaletteManager
        """
        return self.main.color_manager

    @property
    def forest(self):
        """ Shortcut to active forest
        :return: Forest
        """
        return self.main.forest

    @property
    def fs(self):
        """ Shortcut to active forest's settings """
        if self.main.forest:
            return self.main.forest.settings

    @property
    def graph_scene(self):
        return self.main.graph_scene

    @property
    def graph_view(self):
        return self.main.graph_view

    def add_message(self, msg):
        """

        :param msg:
        """
        self.ui.add_message(msg)

    def is_zooming(self):
        return self.main.graph_view.zoom_timer.isActive()

    def set_status(self, msg):
        """ Show message in status bar. Send empty message to clear status
        bar. """
        if not (self.items_moving or self.is_zooming()):
            if msg:
                self.main.status_bar.showMessage(msg)
            else:
                self.main.status_bar.clearMessage()

    def remove_status(self, msg):
        """ Clears status message, but only if it is not been replaced by
        another message
            (E.g. when contained object has put its own message,
            and hoverLeaveEvent has not been called for containing object. )
        """
        if not (self.items_moving or self.is_zooming()):
            if msg == self.main.status_bar.currentMessage():
                self.main.status_bar.clearMessage()

                # ******* Selection *******

    # trees and edges can be selected.
    # UI objects are focused. multiple items can be selected, but actions do
    # not necessary apply to them.

    def single_selection(self) -> bool:
        """


        :return:
        """
        return len(self.selected) == 1

    def multiselection_start(self):
        """ Allow delaying of 'selection_changed' signal until all selections are done. Call
        multiselection_end when done, and 'selection_changed' will be sent.
        :return:
        """
        self.multiselection_delay = True

    def multiselection_end(self):
        self.multiselection_delay = False
        self.call_watchers(self, 'selection_changed', value=self.selected)

    def multiple_selection(self):
        """


        :return:
        """
        return len(self.selected) > 1

    def get_single_selected(self):
        """ Return as one object
        :return:
        """

        if len(self.selected) == 1:
            return self.selected[-1]
        else:
            return None

    def is_selected(self, obj) -> bool:
        """

        :param obj:
        :return:
        """
        return obj in self.selected

    def deselect_objects(self):
        """

        :param update_ui:
        """
        olds = list(self.selected)
        self.selected = []
        for obj in olds:
            obj.update_selection_status(False)
        if not self.multiselection_delay:
            self.call_watchers(self, 'selection_changed', value=self.selected)

    def select(self, obj):
        """

        :param obj:
        """
        for o in self.selected:
            o.update_selection_status(False)
        self.selected = [obj]
        if hasattr(obj, 'on_press'):
            obj.on_press(False)
        if hasattr(obj, 'syntactic_object'):
            # here is room for constituent specific print information
            self.add_message('selected %s' % str(obj))
        else:
            self.add_message('selected %s' % str(obj))
        obj.update_selection_status(True)
        if not self.multiselection_delay:
            self.call_watchers(self, 'selection_changed', value=self.selected)

    def add_to_selection(self, obj):
        """

        :param obj:
        :param call_watchers: Immediately call watchers or if you want to call them manually (
        after adding multiple items)
        """
        if obj not in self.selected:
            self.selected.append(obj)
            self.add_message('added to selection %s' % str(obj))
            obj.update_selection_status(True)
            if not self.multiselection_delay:
                self.call_watchers(self, 'selection_changed', value=self.selected)

    def press(self, obj):
        """ Mark object to be the last pressed object. If it has on_press -hook, do it.
        :param obj:
        :return:
        """
        if self.pressed is obj:
            # better do nothing in this case so that on_press -animations don't freak out
            return
        if self.pressed and hasattr(self.pressed, 'on_press'):
            self.pressed.on_press(False)
        self.pressed = obj
        if hasattr(obj, 'on_press'):
            obj.on_press(True)

    def remove_from_selection(self, obj):
        """

        :param obj:
        :param call_watchers: Immediately call watchers or if you want to call them manually (
        after removing multiple items)
        """
        if obj in self.selected:
            self.selected.remove(obj)
            obj.update_selection_status(False)
            if not self.multiselection_delay:
                self.call_watchers(self, 'selection_changed', value=self.selected)

    def set_drag_hovering(self, item):
        """ Drag is hovering over one item that can receive drop.
        :param item: item that can receive drops or None
        :return:
        """
        if self.drag_hovering_on and self.drag_hovering_on is not item:
            self.drag_hovering_on.hovering = False
        self.drag_hovering_on = item
        if item:
            item.hovering = True

    def add_my_group_to_dragged_groups(self, item):
        """

        :param item:
        :return:
        """
        for group in self.forest.groups.values():
            if item in group:
                self.dragged_groups.add(group)

    # ******** /selection *******

    # ******** Focus *********
    # focus is used only for UI objects. scene objects use selection. only
    # one ui_support object or its part can have focus

    def get_focus_object(self):
        """


        :return:
        """
        return self.main.app.focusWidget()

    # ******** /focus *******
    #

    @caller
    def quit(self):
        """*** calling quits ***"""
        sys.exit()

    # Watchers #####################################

    def add_watcher(self, signal, obj):
        """

        :param signal:
        :param obj:
        """
        if signal in self.watchers:
            watchlist = self.watchers[signal]
            if obj not in watchlist:
                watchlist.append(obj)
        else:
            self.watchers[signal] = [obj]

    def remove_from_watch(self, obj):
        """

        :param obj:
        """
        for watchlist in self.watchers.values():
            if obj in watchlist:
                watchlist.remove(obj)

    def get_watchers(self, signal):
        """
        :param signal:
        :return:
        """
        return self.watchers.get(signal, [])

    def call_watchers(self, obj, signal, field_name=None, value=None):
        """ Alert (UI) objects that are watching for changes for given field
        in given object
        :param obj:
        :param signal:
        :param field_name
        :param value:
        :return:
        """
        if not self.watchers_disabled:
            watchers = self.get_watchers(signal)
            for watcher in watchers:
                watcher.watch_alerted(obj, signal, field_name, value)
                # if not watchers:
                #    print('no watcher found for signal "%s"' % signal)

    def disable_undo(self):
        self.undo_disabled += 1

    def resume_undo(self):
        if self.undo_disabled:
            self.undo_disabled -= 1