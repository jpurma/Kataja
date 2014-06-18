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

from kataja.ForestSettings import ForestSettings
from kataja.Preferences import Preferences, QtPreferences
from kataja.utils import caller
from syntax.BareConstituent import BareConstituent
from syntax.BaseUG import UG
from syntax.ConfigurableFeature import Feature
from PyQt5 import QtCore, QtWidgets

global prefs, qt_prefs, colors
prefs = Preferences()
qt_prefs = QtPreferences()
forest_settings = ForestSettings(None, prefs)

# gc.set_debug(gc.DEBUG_LEAK)

# flags = (gc.DEBUG_COLLECTABLE |
# gc.DEBUG_UNCOLLECTABLE |
# gc.DEBUG_OBJECTS
# )
# gc.set_debug(flags)

class Controller:
    """

    """

    def __init__(self):
        # self.set_prefs('default')
        # : :type self.main: KatajaMain
        self.main = None
        self.ui = None
        self.Constituent = BareConstituent
        self.Feature = Feature
        self.UG = UG(constituent=self.Constituent, feature=self.Feature)
        self.structure = None
        self.selected = []
        self.selected_root = None
        self.rootmarker = '/'
        self.pointing_mode = False
        self.pointing_method = None
        self.pointing_data = {}
        self.pressed = None  # set() # prepare for multitouch
        self.ui_pressed = None  # set() # different coordinates to pressed set
        self.dragged = set()
        self.dragged_positions = set()
        self.ui_focus = None
        self.selection_tool = False
        self.move_tool = False
        self.references_to_fix = []
        self.rebuild_dict = {}
        self.print_garbage = True
        self.focus = None
        self.loading = False  # flag that affects if pickle.load assumes
        # an empty workspace (loading new) or if it tries to compare changes (undo).
        self.unassigned_objects = {}
        self.on_cancel_delete = []
        self.watch_for_drag_end = False

    def late_init(self, main):
        """

        :param main:
        """
        self.main = main

    def cm(self):
        """ Shortcut to color manager, which replaces palettes, colors etc. older solutions. """
        return self.main.color_manager

    def forest(self):
        """ Shortcut to active forest """
        return self.main.forest

    def fs(self):
        """ Shortcut to active forest's settings """
        return self.main.forest.settings


    def add_message(self, msg):
        """

        :param msg:
        """
        self.main.add_message(msg)

    def announce(self, signal, *args):
        """ Announcing is used to broadcast update requests to objects in graph scene
        or UI items. Items need to support this by having signal in 
        'receives_signals'- list and by having 'receive_signal' method that then
        :param signal:
        :param args:
        distinguishes between different signals. Announcements can include arguments. """
        # self.main.ui_manager.forward_signal(signal, *args)
        self.main.graph_scene.forward_signal(signal, *args)

    def sendEvent(self, event_id, **kwargs):
        """

        :param event_id:
        :param kwargs:
        """
        event = QtCore.QEvent(event_id)
        QtWidgets.QApplication.sendEvent(self.main, event)
        # sevent = QtWidgets.QGraphicsSceneEvent(event_id)
        self.main.graph_scene.sceneEvent(event)

        # ******* Selection *******

    # trees and edges can be selected. UI objects are focused. multiple items can be selected, but actions do not necessary apply to them.

    def single_selection(self):
        """


        :return:
        """
        return len(self.selected) == 1

    def multiple_selection(self):
        """


        :return:
        """
        return len(self.selected) > 1

    def get_selected(self):
        """


        :return:
        """
        if self.selected:
            return self.selected[-1]
        else:
            return None

    def get_all_selected(self):
        """


        :return:
        """
        return self.selected

    def is_selected(self, obj):
        """

        :param obj:
        :return:
        """
        return obj in self.selected

    def deselect_objects(self, update_ui=True):
        """

        :param update_ui:
        """
        olds = list(self.selected)
        self.selected = []
        for obj in olds:
            obj.set_selection_status(False)
        if update_ui:
            self.main.ui_manager.update_selections()

    def select(self, obj):
        """

        :param obj:
        """
        if hasattr(obj, 'info_dump'):
            obj.info_dump()
        if self.selected:
            self.deselect_objects(update_ui=False)
        self.selected = [obj]
        self.add_message(u'selected %s' % unicode(obj))
        obj.set_selection_status(True)
        self.main.ui_manager.update_selections()

    def add_to_selection(self, obj):
        """

        :param obj:
        """
        if obj not in self.selected:
            self.selected.append(obj)
            self.add_message(u'added to selection %s' % unicode(obj))
            obj.set_selection_status(True)
            self.main.ui_manager.update_selections()

    def remove_from_selection(self, obj):
        """

        :param obj:
        """
        if obj in self.selected:
            self.selected.remove(obj)
            obj.set_selection_status(False)
            self.main.ui_manager.update_selections()

    # ******** /selection *******

    # ******** Focus *********
    # focus is used only for UI objects. scene objects use selection. only one ui object or its part can have focus

    def get_focus_object(self):
        """


        :return:
        """
        return self.ui_focus

    def has_focus(self, ui_obj):
        """

        :param ui_obj:
        :return:
        """
        return self.ui_focus == ui_obj

    def hosts_focus(self, ui_obj):
        """

        :param ui_obj:
        :return:
        """
        return self.ui_focus and self.ui_focus.host == ui_obj

    def take_focus(self, ui_obj):
        """

        :param ui_obj:
        """
        if self.ui_focus:
            self.release_focus()
        self.ui_focus = ui_obj
        ui_obj.update()

    def release_focus(self):
        """


        """
        old = self.ui_focus
        self.ui_focus = None
        if old:
            old.update()

    # ******** /focus *******
    #


    @caller
    def quit(self):
        """*** calling quits ***"""
        sys.exit()


ctrl = Controller()  # Controller()