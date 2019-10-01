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
from collections import abc

from PyQt5 import QtCore

from kataja.utils import caller

# gc.set_debug(gc.DEBUG_LEAK)

# flags = (gc.DEBUG_COLLECTABLE |
# gc.DEBUG_UNCOLLECTABLE |
# gc.DEBUG_OBJECTS
# )
# gc.set_debug(flags)
from kataja.parser.LatexToINode import LatexFieldToINode
from kataja.parser.HTMLToINode import HTMLToINode
from kataja.parser.PlainTextToINode import PlainTextToINode
from kataja.parser.QDocumentToINode import QDocumentToINode


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

    Note that almost every class imports Controller, so we have to be careful not to try
    importing those classes in here. Method annotation remains incomplete because of this.
    """

    def __init__(self, prefs):
        # self.set_prefs('default')
        # : :type self.main: KatajaMain

        self.main = None
        self.prefs = prefs
        self.structure = None
        self.selected = []
        self.selected_root = None
        self.rootmarker = '/'
        self.pointing_mode = False
        self.pointing_method = None
        self.pointing_data = {}
        self.pressed = None  # set() # prepare for multitouch
        self.ui_pressed = None  # set() # different coordinates to pressed set
        self.hovering = None
        self.text_editor_focus = None
        self.dragged_focus = None
        self.dragged_text = None
        self.dragged_set = set()
        self.dragged_groups = set()
        self.drag_hovering_on = None  # used only while dragging, because
        # standard hovering doesn't work while dragging
        self.ui_focus = None
        self.focus_point = None
        self.selection_tool = False
        self.move_tool = False
        self.references_to_fix = []
        self.rebuild_dict = {}
        self.print_garbage = True
        self.focus = None
        self.undo_disabled = 0  # stacking flag that affects if pickle.load assumes
        # an empty workspace (loading new) or if it tries to compare changes (undo).
        self.printing = False
        self.unassigned_objects = {}
        self.items_moving = False
        self.multiselection_delay = False
        self.plugin_settings = None
        self.latex_field_parser = LatexFieldToINode()
        self.html_field_parser = HTMLToINode(rows_mode=False)
        self.plain_field_parser = PlainTextToINode(rows_mode=False)
        self.qdocument_parser = QDocumentToINode()
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
    def syntax(self) -> 'kataja.syntax.SyntaxAPI':
        """
        :return: SyntaxAPI
        """
        return self.main.forest and self.main.forest.syntax

    @property
    def ui(self) -> 'kataja.UIManager':
        """
        :return: UIManager
        """
        return self.main.ui_manager  # getattr(self.main, 'ui_manager', None)

    @property
    def cm(self) -> 'kataja.PaletteManager':
        """ Shortcut to color manager, which replaces palettes, colors etc.
        older solutions.
        :return: PaletteManager
        """
        return self.main.color_manager

    @property
    def doc_settings(self):
        return self.document.settings if self.document else self.prefs

    @property
    def forest(self) -> 'kataja.saved.Forest':
        """ Shortcut to active forest
        :return: Forest
        """
        return self.main.document and self.main.document.forest

    @property
    def drawing(self) -> 'kataja.ForestDrawing':
        return self.main.forest.drawing

    @property
    def view_manager(self) -> 'kataja.ViewManager':
        return self.main.view_manager

    @property
    def graph_scene(self) -> 'kataja.GraphScene':
        return self.main.graph_scene

    @property
    def graph_view(self) -> 'kataja.GraphView':
        return self.main.graph_view

    @property
    def scene_moving(self) -> bool:
        return self.items_moving or self.main.view_manager.is_zooming()

    @property
    def document(self) -> 'kataja.saved.KatajaDocument':
        return self.main.document

    @property
    def play(self) -> bool:
        return self.main.document.play
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
        self.main.selection_changed.emit()
        self.ui.add_message(f'selected {len(self.selected)} objects')

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
        if not self.selected:
            return
        for obj in self.selected:
            obj.update_selection_status(False)
        self.selected = []
        self.main.selection_changed.emit()

    def select(self, objs):
        """

        :param objs:
        """
        if objs == self.selected:
            return
        had_objs = bool(self.selected)
        if had_objs:
            for obj in self.selected:
                obj.update_selection_status(False)
            self.selected = []
        if not objs:
            if had_objs:
                self.main.selection_changed.emit()
            return
        if not isinstance(objs, abc.Sequence):
            objs = [objs]
        for obj in objs:
            obj.update_selection_status(True)
        self.selected = objs
        self.main.selection_changed.emit()

    def add_to_selection(self, objs):
        """

        :param objs:
        """
        if not objs:
            return
        if not isinstance(objs, abc.Sequence):
            objs = [objs]
        found = False
        for obj in objs:
            if obj not in self.selected:
                self.selected.append(obj)
                obj.update_selection_status(True)
                found = True
        if found:
            self.main.selection_changed.emit()

    def remove_from_selection(self, objs):
        """

        :param objs:
        """
        if not objs:
            return
        found = False
        if isinstance(objs, abc.Sequence):
            for obj in objs:
                if obj in self.selected:
                    self.selected.remove(obj)
                    obj.update_selection_status(False)
                    found = True
        else:
            if objs in self.selected:
                self.selected.remove(objs)
                objs.update_selection_status(False)
                found = True
        if found:
            self.main.selection_changed.emit()

    def get_selected_nodes(self, of_type=None):
        nclass = self.main.classes.base_node_class
        if of_type:
            return [node for node in self.selected if
                    isinstance(node, nclass) and node.node_type == of_type]
        else:
            return [node for node in self.selected if isinstance(node, nclass)]

    def get_selected_edges(self, of_type=None):
        eclass = self.main.classes.default_edge_class
        if of_type:
            return [edge for edge in self.selected if
                    isinstance(edge, eclass) and edge.edge_type == of_type]
        else:
            return [edge for edge in self.selected if isinstance(edge, eclass)]

    def press(self, obj):
        """ Mark object to be the last pressed object.
        :param obj:
        :return:
        """
        if self.pressed is obj:
            # better do nothing in this case so that on_press -animations don't freak out
            return
        self.pressed = obj
        self.graph_view.toggle_suppress_drag(True)

    def release(self, obj):
        self.graph_view.toggle_suppress_drag(False)
        if self.pressed is obj:
            self.pressed = None

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
        print('quit?')
        sys.exit()

    def disable_undo(self):
        self.undo_disabled += 1

    def resume_undo(self):
        if self.undo_disabled:
            self.undo_disabled -= 1

    def release_editor_focus(self):
        if self.text_editor_focus:
            self.text_editor_focus.release_editor_focus()
        self.text_editor_focus = None

    def allow_arrow_shortcuts(self):
        for action in self.ui.arrow_actions:
            action.setEnabled(bool(action.enabler()))

    def suppress_arrow_shortcuts(self):
        for action in self.ui.arrow_actions:
            action.setEnabled(False)
