#!/usr/bin/env python
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

# Note: convention that I try to start following is that Kataja methods are in
# small caps and underscore (Python convention), but Qt methods are in camelcase.
# Classnames are in camelcase.

import gc
#import gzip
import json
import os.path
import shlex
import subprocess
import sys
import time
import pickle
import pprint

from PyQt5.QtCore import Qt
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
from kataja.KeyPressManager import KeyPressManager

from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.Forest import Forest
from kataja.ForestKeeper import ForestKeeper
from kataja.GraphScene import GraphScene
from kataja.GraphView import GraphView
from kataja.Presentation import TextArea
from kataja.Edge import SHAPE_PRESETS, Edge
from kataja.UIManager import UIManager
from kataja.PaletteManager import PaletteManager
import kataja.globals as g
from kataja.ui.MenuItem import MenuItem
from kataja.ui.PreferencesDialog import PreferencesDialog
from kataja.utils import time_me, save_object
from kataja.visualizations.available import VISUALIZATIONS
import kataja.debug as debug
from kataja.ui.panels.DrawingPanel import TableModelComboBox



# show labels

ONLY_LEAF_LABELS = 0
ALL_LABELS = 1
ALIASES = 2

# only for debugging (Apple-m, memory check), can be commented
# try:
# import objgraph
# except ImportError:
# objgraph = None

# KatajaMain > UIView > UIManager > GraphView > GraphScene > Leaves etc.



class KatajaMain(QtWidgets.QMainWindow):
    """ Qt's main window. When this is closed, application closes. Graphics are
    inside this, in scene objects with view widgets. This window also manages
    keypresses and menus. """

    singleton_key = 'KatajaMain'
    saved_fields = ['graph_scene', 'graph_view', 'ui_manager', 'forest_keeper', 'forest']

    @time_me
    def __init__(self, kataja_app, args):
        """ KatajaMain initializes all its children and connects itself to
        be the main window of the given application. """
        t = time.time()
        QtWidgets.QMainWindow.__init__(self)
        print('---- initialized MainWindow base class ... ', time.time() - t)
        self.app = kataja_app
        self.fontdb = QtGui.QFontDatabase()
        print('---- set up font db ... ', time.time() - t)
        self.color_manager = PaletteManager()
        print('---- Initialized color manager ... ', time.time() - t)
        qt_prefs.late_init(prefs, self.fontdb)
        self.app.setFont(qt_prefs.ui_font)
        print('---- initialized prefs ... ', time.time() - t)
        ctrl.late_init(self)
        print('---- controller late init ... ', time.time() - t)
        self.graph_scene = GraphScene(main=self, graph_view=None)
        print('---- scene init ... ', time.time() - t)
        self.graph_view = GraphView(main=self, graph_scene=self.graph_scene)
        print('---- view init ... ', time.time() - t)
        self.graph_scene.graph_view = self.graph_view
        self.ui_manager = UIManager(self)
        self.key_manager = KeyPressManager(self)
        print('---- ui init ... ', time.time() - t)
        self.forest_keeper = ForestKeeper(main=self)
        print('---- forest_keeper init ... ', time.time() - t)
        self.forest = Forest(main=self)
        print('---- forest init ... ', time.time() - t)
        self.visualizations = VISUALIZATIONS
        print('---- visualizations init ... ', time.time() - t)
        kataja_app.setPalette(self.color_manager.get_qt_palette())
        self.setCentralWidget(self.graph_view)

        print('---- set palette ... ', time.time() - t)
        self.load_treeset()
        print('---- loaded treeset ... ', time.time() - t)
        x, y, w, h = (50, 50, 940, 720)
        self.setMinimumSize(w, h)
        self.setWindowTitle(self.tr("Kataja"))
        self.setDockOptions(QtWidgets.QMainWindow.AnimatedDocks)
        self.setCorner(QtCore.Qt.TopLeftCorner, QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.TopRightCorner, QtCore.Qt.RightDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomLeftCorner, QtCore.Qt.LeftDockWidgetArea)
        self.setCorner(QtCore.Qt.BottomRightCorner, QtCore.Qt.RightDockWidgetArea)
        #toolbar = QtWidgets.QToolBar()
        #toolbar.setFixedSize(480, 40)
        #self.addToolBar(toolbar)
        self.status_bar = self.statusBar()
        self.setGeometry(x, y, w, h)
        self.add_message('Welcome to Kataja! (h) for help')
        self.action_finished()
        print('---- finished start sequence... ', time.time() - t)

    def load_treeset(self, treeset_list=None):
        """ Loads and initializes a new set of trees. Has to be done before the program can do anything sane.
        :param treeset_list:
        """
        if not treeset_list:
            treeset_list = []
        if treeset_list:
            self.forest_keeper = ForestKeeper(main=self, treelist=treeset_list)
        else:
            self.forest_keeper = ForestKeeper(main=self, file_name=prefs.debug_treeset)
        self.change_forest(self.forest_keeper.forest)

    # ### Visualization #############################################################

    def set_forest(self, forest):
        """

        :param forest:
        """
        self.forest = forest
        if not forest.visualization:
            forest.change_visualization(prefs.default_visualization)
        else:
            forest.visualization.prepare(forest)

    def change_forest(self, forest):
        """ Tells the scene to remove current tree and related data and change it to a new one
        :param forest:
        """
        if self.forest:
            self.forest.clear_scene()
        self.ui_manager.clear_items()
        self.set_forest(forest)
        self.forest.update_colors()
        if debug.DEBUG_FOREST_OPERATION:
            self.forest.info_dump()
        self.graph_scene.displayed_forest = forest
        self.forest.add_all_to_scene()
        self.graph_scene.reset_zoom()
        self.ui_manager.update_all_fields()
        self.forest.undo_manager.init_if_empty()

    def switch_to_next_forest(self):
        """


        :return:
        """
        i, forest = self.forest_keeper.next_forest()
        self.change_forest(forest)
        return i

    def switch_to_previous_forest(self):
        """


        :return:
        """
        i, forest = self.forest_keeper.prev_forest()
        self.change_forest(forest)
        return i

    def action_finished(self, m='', undoable=True):
        """

        :param m:
        """
        if undoable:
            self.forest.undo_manager.record(m)
        self.graph_scene.draw_forest(self.forest)

    def redraw(self):
        """


        """
        self.graph_scene.draw_forest(self.forest)

    def add_message(self, msg):
        """ :type msg: StringType
        :param msg:
        """
        self.ui_manager.add_message(msg)

        # ### General events ##########

        # def event(self, event):
        # print 'm:', event.type()
        # print 'Main event received: %s' % event.type()

    # return QtWidgets.QMainWindow.event(self, event)

    def mousePressEvent(self, event):
        """ KatajaMain doesn't do anything with mousePressEvents, it delegates
        :param event:
        them downwards. This is for debugging. """
        QtWidgets.QMainWindow.mousePressEvent(self, event)

    def keyPressEvent(self, event):
        #if not self.key_manager.receive_key_press(event):
        return QtWidgets.QMainWindow.keyPressEvent(self, event)


    def undo(self):
        """ Undo -command triggered """
        self.forest.undo_manager.undo()
        # self.action_finished()

    def redo(self):
        """ Redo -command triggered """
        self.forest.undo_manager.redo()
        # self.action_finished()



    # ### ConstituentNode's radial menu commands ################################

    def do_merge(self, caller, event):
        """

        :param caller:
        :param event:
        :return:
        """
        if isinstance(caller, MenuItem):
            caller = caller.host_node
        node_A = caller
        node_B = caller.get_root_node()
        assert (node_A is not node_B)
        merged = self.forest.merge_nodes(node_A, node_B)
        node_A.release()
        self.action_finished()
        merged.take_focus()
        return True

    def do_delete_node(self, caller, event):
        """

        :param caller:
        :param event:
        :return:
        """
        if isinstance(caller, MenuItem):
            caller = caller.host_node
        self.forest.command_delete(caller)
        self.action_finished()
        ctrl.focus = None
        return True

    def toggle_fold_node(self, caller, event):
        """

        :param caller:
        :param event:
        :return:
        """
        if isinstance(caller, MenuItem):
            caller = caller.host_node
        if caller.is_folded_away():
            self.add_message('Unfolding %s to %s' % (caller.linearized(), str(caller)))
            caller.unfold_triangle()
            self.action_finished()  # recalculate their positions
        else:
            self.add_message('Folding %s to %s' % (str(caller), caller.linearized()))
            caller.fold()
        return True

    def disconnect_node(self, caller=None, event=None):
        """

        :param caller:
        :param event:
        :return:
        """
        if isinstance(caller, MenuItem):
            caller = caller.host_node
        self.forest.disconnect_node_from_tree(caller)
        self.action_finished()
        ctrl.focus = None
        return True

    def copy_selected(self, **kw):
        """ Make a copy of element and put it beside the original
        :param kw:
        """
        for node in ctrl.get_all_selected():
            self.forest.copy_node(node)
        self.action_finished()
        return True

    # ## New node creation commands #############################################

    def add_text_box(self, caller=None):
        """

        :param caller:
        """
        text = ''
        if hasattr(caller, 'get_text_input'):
            text = caller.get_text_input()
            text_area = TextArea(text)
            text_area.set_original_position(caller.get_current_position())
            self.forest.store(text_area)
        self.action_finished()

    def add_new_constituent(self, caller=None):
        """

        :param caller:
        """
        text = ''
        if hasattr(caller, 'get_text_input'):
            text = caller.get_text_input()
        if ctrl.single_selection():  # live editing
            self.forest.reform_constituent_node_from_string(text, ctrl.get_selected())
        else:
            self.forest.create_node_from_string(text, caller.pos())
        self.action_finished()

    def add_new_tree(self, caller=None):
        """

        :param caller:
        """
        text = ''
        if hasattr(caller, 'get_text_input'):
            text = caller.get_text_input()
        #pos = caller.pos()
        self.forest.create_tree_from_string(text)  # , pos=pos)
        self.action_finished()

    # ## Menu management #######################################################

    def action_triggered(self):
        sender = self.sender()
        key = sender.data()
        data = self.ui_manager.actions[key]
        selector = data.get('selector', None)
        spinbox = data.get('spinbox', None)
        args = []
        args += data.get('args', [])
        if selector:
            # This is a combobox, get the data and add it as an argument
            if isinstance(selector, TableModelComboBox):
                i = selector.view().currentIndex()
                args.append(selector.model().itemFromIndex(i).data())
            elif isinstance(selector, QtWidgets.QComboBox):
                args.append(selector.itemData(selector.currentIndex()))
        elif spinbox:
            args.append(spinbox.value())
        context = data.get('context', 'main')
        if context == 'main':
            c = self
        elif context == 'selected':
            c = ctrl.selected
        elif context == 'ui':
            c = self.ui_manager
        elif context == 'app':
            c = self.app
        else:
            c = self
        print('Doing action %s, args: %s' % (key, str(args)))
        method = getattr(c, data['method'])
        if args:
            method(*args)
        else:
            method()
        if 'no_undo' in data:
            undoable = False
        else:
            undoable = True
        self.action_finished(undoable=undoable)


    def enable_actions(self):
        """ Restores menus """
        for action in self.ui_manager.qt_actions.values():
            action.setDisabled(False)

    def disable_actions(self):
        """ Actions shouldn't be initiated when there is other multi-phase
        action going on """
        for action in self.ui_manager.qt_actions.values():
            action.setDisabled(True)

    # ## Menu actions ##########################################################

    def toggle_label_visibility(self):
        """
        toggle label visibility -action (l)


        """
        new_value = self.forest.settings.label_style() + 1
        if new_value == 3:
            new_value = 0
        if new_value == ONLY_LEAF_LABELS:
            self.add_message('(l) 0: show only leaf labels')
        elif new_value == ALL_LABELS:
            self.add_message('(l) 1: show all labels')
        elif new_value == ALIASES:
            self.add_message('(l) 2: show leaf labels and aliases')
        # testing how to change labels
        # ConstituentNode.font = prefs.sc_font
        self.forest.settings.label_style(new_value)

        for node in self.forest.nodes.values():
            node.update_visibility(label=new_value)
            # change = node.update_label()
        self.action_finished('toggle label visibility')

    def change_colors(self):
        """
        change colors -action (shift-c)


        """
        color_panel = self.ui_manager._ui_panels['Colors']
        if not color_panel.isVisible():
            color_panel.show()
        else:
            self.forest.settings._hsv = None
            self.forest.update_colors()
            self.activateWindow()
            # self.ui.add_message('Color seed: H: %.2f S: %.2f L: %.2f' % ( h, s, l))
            self.action_finished()

    def adjust_colors(self, hsv):
        """
        adjust colors -action (shift-alt-c)

        :param hsv:
        """
        self.forest.settings.hsv(hsv)
        self.forest.update_colors(adjusting=True)
        # adjust_colorsself.activateWindow()
        # self.action_finished('adjust colors')

    def change_color_mode(self, mode):
        """
        triggered by color mode selector in colors panel

        :param mode:
        """
        print(mode)
        if mode != prefs.color_mode:
            prefs.color_mode = mode
            self.forest.update_colors()

            # Show traces -action (t)

    def toggle_traces(self):
        """


        """
        if self.forest.settings.traces_are_grouped_together() and not self.forest.settings.uses_multidomination():
            self.forest.settings.uses_multidomination(True)
            self.forest.settings.traces_are_grouped_together(False)
            self.add_message('(t) use multidominance')
            self.forest.traces_to_multidomination()
        elif (
                not self.forest.settings.traces_are_grouped_together()) and not self.forest.settings.uses_multidomination():
            self.forest.settings.uses_multidomination(False)
            self.forest.settings.traces_are_grouped_together(True)
            self.add_message('(t) use traces, group them to one spot')
            self.forest.group_traces_to_chain_head()
        elif self.forest.settings.uses_multidomination():
            self.forest.settings.uses_multidomination(False)
            self.forest.settings.traces_are_grouped_together(False)
            self.add_message('(t) use traces, show constituents in their base merge positions')
            self.forest.multidomination_to_traces()

    # Brackets are visible always for non-leaves, never or for important parts
    def toggle_brackets(self):
        """


        """
        bs = self.forest.settings.bracket_style()
        bs += 1
        if bs == 3:
            bs = 0
        if bs == 0:
            self.add_message('(b) 0: No brackets')
        elif bs == 1:
            self.add_message('(b) 1: Use brackets for embedded structures')
        elif bs == 2:
            self.add_message('(b) 2: Always use brackets')
        self.forest.settings.bracket_style(bs)
        self.forest.bracket_manager.update_brackets()

    # Show order-feature
    def show_merge_order(self):
        """


        """
        if self.forest.settings.shows_merge_order():
            self.add_message('(o) Hide merge order')
            self.forest.settings.shows_merge_order(False)
            self.forest.remove_order_features('M')
        else:
            self.add_message('(o) Show merge order')
            self.forest.settings.shows_merge_order(True)
            self.forest.add_order_features('M')

    def show_select_order(self):
        """


        """
        if self.forest.settings.shows_select_order():
            self.add_message('(O) Hide select order')
            self.forest.settings.shows_select_order(False)
            self.forest.remove_order_features('S')
        else:
            self.add_message('(O) Show select order')
            self.forest.settings.shows_select_order(True)
            self.forest.add_order_features('S')


    # Lines connect to margins -action (b)
    def toggle_magnets(self):
        """


        """
        if self.forest.settings.uses_magnets():
            self.add_message('(c) 0: Lines connect to node margins')
            self.forest.settings.uses_magnets(False)
        else:
            self.add_message('(c) 1: Lines aim to the center of the node')
            self.forest.settings.uses_magnets(True)


    def change_edge_panel_scope(self, selection):
        p = self.ui_manager.get_panel(g.DRAWING)
        p.change_scope(selection)
        p.update_panel()
        p = self.ui_manager.get_panel(g.LINE_OPTIONS)
        p.update_panel()


    def change_edge_shape(self, shape):
        if shape is g.AMBIGUOUS_VALUES:
            return
        scope = self.ui_manager.get_panel(g.DRAWING).scope
        if scope == g.SELECTION:
            for edge in ctrl.get_all_selected():
                if isinstance(edge, Edge):
                    edge.shape_name(shape)
                    edge.update_shape()
        elif scope:
            self.forest.settings.edge_settings(scope, 'shape_name', shape)
            ctrl.announce(g.EDGE_SHAPES_CHANGED, scope, shape)
        self.add_message('(s) Changed relation shape to: %s' % shape)

    def change_edge_color(self, color):
        if color is g.AMBIGUOUS_VALUES:
            return
        panel = self.ui_manager.get_panel(g.DRAWING)
        if not color:
            self.ui_manager.start_color_dialog(panel, 'color_changed')
            return
        if panel.scope == g.SELECTION:
            for edge in ctrl.get_all_selected():
                if isinstance(edge, Edge):
                    edge.color(color)
                    #edge.update_shape()
                    edge.update()
        elif panel.scope:
            self.forest.settings.edge_settings(panel.scope, 'color', color)
            #ctrl.announce(g.EDGE_SHAPES_CHANGED, scope, color)
        panel.update_color(color)
        panel.update_panel()
        self.add_message('(s) Changed relation color to: %s' % ctrl.cm.get_color_name(color))


    # Change node edge shapes -action (s)
    def change_node_edge_shape(self, shape=''):
        """

        :param shape:
        """
        if shape and shape in SHAPE_PRESETS:
            self.forest.settings.edge_settings(g.CONSTITUENT_EDGE, 'shape_name', shape)
            i = list(SHAPE_PRESETS.keys()).index(shape)
        else:
            shape = self.forest.settings.edge_settings(g.CONSTITUENT_EDGE, 'shape_name')
            i = list(SHAPE_PRESETS.keys()).index(shape)
            i += 1
            if i == len(SHAPE_PRESETS):
                i = 0
            shape = list(SHAPE_PRESETS.keys())[i]
            self.forest.settings.edge_settings(g.CONSTITUENT_EDGE, 'shape_name', shape)
        self.add_message('(s) Change constituent edge shape: %s-%s' % (i, shape))
        ctrl.announce(g.EDGE_SHAPES_CHANGED, g.CONSTITUENT_EDGE, i)

    # Change feature edge shapes -action (S)
    def change_feature_edge_shape(self, shape):
        """


        """
        if shape and shape in SHAPE_PRESETS:
            self.forest.settings.edge_shape_name(g.CONSTITUENT_EDGE, shape)
            i = list(SHAPE_PRESETS.keys()).index(shape)
        else:
            i = list(SHAPE_PRESETS.keys()).index(self.forest.settings.edge_shape_name(g.FEATURE_EDGE))
            if i == len(SHAPE_PRESETS):
                i = 0
            shape = list(SHAPE_PRESETS.keys())[i]
            self.forest.settings.edge_shape_name(g.FEATURE_EDGE, shape)
        self.ui_manager.ui_buttons['feature_line_type'].setCurrentIndex(i)
        self.add_message('(s) Change feature edge shape: %s-%s' % (i, shape))

    def adjust_control_point(self, cp_index, dim, value=0):
        """ Adjusting control point can be done only for selected edges, not for an edge type. So this method is
        simpler than other adjustments, as it doesn't have to handle both cases.
        :param cp_index: 1 or 2
        :param dim: 'x', 'y' or 'r' for reset
        :param value: new value for given dimension, doesn't matter for reset.
        :return:
        """
        cp_index -= 1
        for edge in ctrl.get_all_selected():
            if isinstance(edge, Edge):
                if dim == 'r':
                    edge.reset_control_point(cp_index)
                else:
                    edge.adjust_control_point_xy(cp_index, dim, value)


    def change_leaf_shape(self, dim, value=0):
        #if value is g.AMBIGUOUS_VALUES:
        #  if we need this, we'll need to find some impossible ambiguous value to avoid weird, rare incidents
        #    return
        panel = self.ui_manager.get_panel(g.DRAWING)
        if panel.scope == g.SELECTION:
            for edge in ctrl.get_all_selected():
                if isinstance(edge, Edge):
                    edge.change_leaf_shape(dim, value)
        elif panel.scope:
            if dim == 'w':
                self.forest.settings.edge_shape_settings(panel.scope, 'leaf_x', value)
            elif dim == 'h':
                self.forest.settings.edge_shape_settings(panel.scope, 'leaf_y', value)
            elif dim == 'r':
                self.forest.settings.edge_shape_settings(panel.scope, 'leaf_x', g.DELETE)
                self.forest.settings.edge_shape_settings(panel.scope, 'leaf_y', g.DELETE)
                options_panel = self.ui_manager.get_panel(g.LINE_OPTIONS)
                options_panel.update_panel()
            else:
                raise ValueError
            ctrl.announce(g.EDGE_SHAPES_CHANGED, panel.scope, value)
        #panel.update_color(color)
        #panel.update_panel()
        #self.add_message('(s) Changed relation color to: %s' % ctrl.cm.get_color_name(color))

    # Next structure -action (.)
    def next_structure(self):
        """


        """
        i = self.switch_to_next_forest()
        self.ui_manager.clear_items()
        self.add_message('(.) tree %s: %s' % (i + 1, self.forest.textual_form()))

    # Prev structure -action (,)
    def previous_structure(self):
        """


        """
        i = self.switch_to_previous_forest()
        self.ui_manager.clear_items()
        self.add_message('(,) tree %s: %s' % (i + 1, self.forest.textual_form()))

    def change_visualization(self, i):
        """
        :param i: index of selected visualization in relevant panel
        :return:
        """
        pass

    # Change visualization style -action (1...9)
    def change_visualization_command(self):
        """


        """
        visualization_key = str(self.sender().text())
        self.ui_manager.update_field('visualization_selector', visualization_key)
        self.forest.change_visualization(visualization_key)
        self.add_message(visualization_key)

    def toggle_full_screen(self):
        """ Full screen -action (f) """
        if self.isFullScreen():
            self.showNormal()
            self.add_message('(f) windowed')
            self.ui_manager.restore_panel_positions()
        else:
            self.ui_manager.store_panel_positions()
            self.showFullScreen()
            self.add_message('(f) fullscreen')
        self.graph_scene.fit_to_window()

    def fit_to_window(self):
        """ Fit graph to current window. Usually happens automatically, but also available as user action
        :return: None
        """
        self.graph_scene.fit_to_window()

    # Blender export -action (Command-r)
    def render_in_blender(self):
        """
        Try to export as a blender file and run blender render.
        """
        self.graph_scene.export_3d(prefs.blender_env_path + '/temptree.json', self.forest)
        self.add_message('Command-r  - render in blender')
        command = '%s -b %s/puutausta.blend -P %s/treeloader.py -o //blenderkataja -F JPEG -x 1 -f 1' % (
            prefs.blender_app_path, prefs.blender_env_path, prefs.blender_env_path)
        args = shlex.split(command)
        subprocess.Popen(args)  # , cwd =prefs.blender_env_path)

    # print as pdf -action (Command-p)
    def print_to_file(self):
        # hide unwanted components
        """


        """
        debug.keys("Print to file called")
        sc = self.graph_scene
        no_brush = QtGui.QBrush(Qt.NoBrush)
        sc.setBackgroundBrush(no_brush)
        gloss = prefs.include_gloss_to_print
        if gloss:
            self.graph_scene.photo_frame = self.graph_scene.addRect(sc.visible_rect_and_gloss().adjusted(-1, -1, 2, 2),
                                                                    self.color_manager.drawing())
        else:
            if self.forest.gloss and self.forest.gloss.isVisible():
                self.forest.gloss.hide()
            self.graph_scene.photo_frame = self.graph_scene.addRect(sc.visible_rect().adjusted(-1, -1, 2, 2),
                                                                    self.color_manager.selection())
        self.graph_scene.update()
        self.graph_view.repaint()
        self.startTimer(50)

    def timerEvent(self, event):
        """ Timer event only for printing, for 'snapshot' effect
        :param event:
        """
        self.killTimer(event.timerId())
        # Prepare file and path
        path = prefs.print_file_path or prefs.userspace_path or prefs.default_userspace_path
        if not path.endswith('/'):
            path += '/'
        if not os.path.exists(path):
            print("bad path for printing (print_file_path in preferences) , using '.' instead.")
            path = './'
        filename = prefs.print_file_name
        if filename.endswith('.pdf'):
            filename = filename[:-4]
        full_path = path + filename + '.pdf'
        counter = 0
        while os.path.exists(full_path):
            counter += 1
            full_path = path + filename + str(counter) + '.pdf'
        # Prepare image
        gloss = prefs.include_gloss_to_print
        if gloss:
            source = self.graph_scene.visible_rect_and_gloss()
        else:
            source = self.graph_scene.visible_rect()
        self.graph_scene.removeItem(self.graph_scene.photo_frame)
        self.graph_scene.photo_frame = None
        target = QtCore.QRectF(0, 0, source.width()/2.0, source.height()/2.0)
        dpi = 25.4
        # Prepare printer
        writer = QtGui.QPdfWriter(full_path)
        writer.setResolution(dpi)
        writer.setPageSizeMM(target.size())
        writer.setPageMargins(QtCore.QMarginsF(0, 0, 0, 0))

        painter = QtGui.QPainter()
        painter.begin(writer)
        self.graph_scene.render(painter, target=target, source=source)
        painter.end()
        # Thank you!
        print('printing done.')
        self.add_message("printed to %s as PDF with %s dpi." % (full_path, dpi))
        # Restore image
        self.graph_scene.setBackgroundBrush(self.color_manager.gradient)
        if self.forest.gloss:
            self.forest.gloss.show()
        # hide unwanted components

    def animation_step_forward(self):
        """ User action "step forward (>)", Move to next derivation step """
        self.forest.derivation_steps.next_derivation_step()
        self.add_message('Step forward')


    def animation_step_backward(self):
        """ User action "step backward (<)" , Move backward in derivation steps """
        self.forest.derivation_steps.previous_derivation_step()
        self.add_message('Step backward')

    # Not called from anywhere yet, but useful
    def release_selected(self, **kw):
        """

        :param kw:
        :return:
        """
        for node in ctrl.get_all_selected():
            node.release()
        self.action_finished()
        return True

    # help -action (h)
    def show_help_message(self):
        """


        """
        m = ""

        # m ="""(h):------- KatajaMain commands ----------
        # (left arrow/,):previous structure   (right arrow/.):next structure
        # (1-5):change or refresh visualization of the tree
        # (f):fullscreen/windowed mode
        # (p):print tree to file
        # (b):show/hide labels in middle of edges
        # (c):curved/straight edges
        # (q):quit"""
        self.add_message(m)

    def open_preferences(self):
        """


        """
        if not self.ui_manager.preferences_dialog:
            self.ui_manager.preferences_dialog = PreferencesDialog(self)
        self.ui_manager.preferences_dialog.open()

        # open -action (Command-o)

    def open_kataja_file(self):
        """ Open file browser to load kataja data file"""
        # fileName  = QtGui.QFileDialog.getOpenFileName(self,
        # self.tr("Open File"),
        # QtCore.QDir.currentPath())
        file_help = "KatajaMain files (*.kataja *.zkataja);;Text files containing bracket trees (*.txt, *.tex)"

        # inspection doesn't recognize that getOpenFileName is static, switch it off:
        # noinspection PyTypeChecker,PyCallByClass
        filename, filetypes = QtWidgets.QFileDialog.getOpenFileName(self, "Open KatajaMain tree", "", file_help)
        # filename = 'savetest.kataja'
        if filename:
            self.load_state_from_file(filename)
            self.add_message("Loaded '%s'." % filename)


    def load_state_from_file(self, filename=''):
        """
        Perform the loading of kataja state from a file.
        :param filename: string
        """
        self.clear_all()
        self.scene.displayed_forest = None
        if filename.endswith('.zkataja'):
            #f = gzip.open(filename, 'r')
            f = open(filename, 'r')
        else:
            f = open(filename, 'r')
            # f = codecs.open(filename, 'rb', encoding = 'utf-8')
        pickle_worker = pickle.Pickler(f)
        data = pickle_worker.load()
        f.close()
        prefs.update(data['preferences'].__dict__)
        qt_prefs.update(prefs)
        self.forest_keeper.load(data['forest_keeper'])
        ctrl.loading = False
        ctrl.change_forest(self.forest_keeper.forest)
        ctrl.update_colors()

    # save -action (Command-s)
    def save_kataja_file(self):
        """ Save kataja data with an existing file name. """
        # action  = self.sender()
        self.action_finished()
        filename = prefs.file_name
        all_data = self.create_save_data()
        t=time.time()
        pickle_format = 4
        if filename.endswith('.zkataja'):
            #f = gzip.open(filename, 'wb')
            f = open(filename, 'wb')
        else:
            f = open(filename, 'wb')
        pickle_worker = pickle.Pickler(f, protocol=pickle_format)
        pickle_worker.dump(all_data)
        f.close()
        self.add_message("Saved to '%s'. Took %s seconds." % (filename, time.time()-t))
        t=time.time()
        filename = prefs.file_name + '.dict'
        f = open(filename, 'w')
        pp = pprint.PrettyPrinter(indent=1, stream=f)
        print('is readable: ', pprint.isreadable(all_data))
        pp.pprint(all_data)
        f.close()
        self.add_message("Saved to '%s'. Took %s seconds." % (filename, time.time()-t))

        filename = prefs.file_name + '.json'
        f = open(filename, 'w')
        json.dump(all_data, f, indent="\t", sort_keys=False)
        f.close()
        self.add_message("Saved to '%s'. Took %s seconds." % (filename, time.time()-t))
        # fileFormat  = action.data().toByteArray()
        # self.saveFile(fileFormat)

    def save_as(self):
        """ Save kataja data to file set by file dialog """
        self.action_finished()
        # noinspection PyCallByClass,PyTypeChecker
        filename = QtWidgets.QFileDialog.getSaveFileName(self, "Save KatajaMain tree", "",
                                                         "KatajaMain files (*.kataja *.zkataja)")
        prefs.file_name = filename
        ctrl.save_state_to_file(filename)
        self.add_message("Saved to '%s'." % filename)

    def clear_all(self):
        """ Empty everything - maybe necessary before loading new data. """
        if self.forest:
            self.forest.clear_scene()
        self.ui_manager.clear_items()
        self.forest_keeper = ForestKeeper(self)

    # ### Action preconditions ##################################################

    # return True or False: should the related action be enabled or disabled

    # noinspection PyMethodMayBeStatic
    def can_root_merge(self):
        """ Check if the selected node can be merged upwards to the root node of its current tree.
        :return: bool
        """
        return ctrl.single_selection() and not ctrl.get_selected().is_root_node()

    # ### Unused two-phase actions ###############################################

    def start_pointing_mode(self, event, method=None, data=None):
        """ Begin pointing mode, mouse pointer draws a line behind it and normal actions are disabled
        :param event:
        :param method:
        :param data:
        """
        if not data:
            data = {}
        ctrl.pointing_mode = True
        ctrl.pointing_method = method
        ctrl.pointing_data = data
        self.ui_manager.begin_stretchline(data['start'].pos(), event.scenePos())  # +data['startposF']
        self.app.setOverrideCursor(QtCore.Qt.CrossCursor)
        self.graph.setDragMode(QtWidgets.QGraphicsView.NoDrag)

    # noinspection PyUnusedLocal
    def end_pointing_mode(self, event):
        """ End pointing mode and return to normal """
        ctrl.pointing_mode = False
        ctrl.pointing_data = {}
        self.ui_manager.end_stretchline()
        self.app.restoreOverrideCursor()
        self.graph.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def begin_merge_to(self, event):
        """ MergeTo is a two phase action. First the target is selected in pointing mode, then 'end_merge_to' is called
        :param event:
        """
        self.start_pointing_mode(event, method=self.end_merge_to, data={'start': ctrl.get_selected()})
        return False

    def end_merge_to(self, event):
        """
        Merging a node -activity ends.
        :param event: mouse-event that triggered the end.
        :return:
        """
        node_a = ctrl.pointing_data['target']
        self.forest.merge_nodes(node_a, node_b)
        node_a.release()
        # node_A.state =SELECTED # deselect doesn't have effect unless node is selected
        self.end_pointing_mode(event)
        self.action_finished()
        return True

    def begin_move_to(self, event):
        """
        Moving a branch or node -activity starts.
        :param event: mouseevent that triggered the action, if available
        :return:
        """
        self.start_pointing_mode(event, method=self.end_move_to, data={'start': ctrl.get_selected()})
        return False

    def end_move_to(self, event):
        """
        Moving a branch or node -activity ends.
        :param event: mouseevent that triggered the end, if available
        :return:
        """
        node_a = ctrl.pointing_data['start']
        node_b = ctrl.pointing_data['target']
        self.forest.cut_and_merge(node_a, node_b)
        node_a.release()
        # node_A.state =SELECTED # deselect doesn't have effect unless node is selected
        self.end_pointing_mode(event)
        self.action_finished()
        return True

    # ### Other window events ###################################################

    def closeEvent(self, event):
        """ Shut down the program, give some debug info
        :param event:
        """
        QtWidgets.QMainWindow.closeEvent(self, event)
        if ctrl.print_garbage:
            # import objgraph
            print('garbage stats:', gc.get_count())
            gc.collect()
            print('after collection:', gc.get_count())
            if gc.garbage:
                print('garbage:', gc.garbage)

                # objgraph.show_most_common_types(limit =40)
        prefs.save_preferences()
        print('...done')

    @time_me
    def create_save_data(self):
        """
        Make a large dictionary of all objects with all of the complex stuff and circular references stripped out.
        :return: dict
        """
        savedata = {}
        open_references = {}
        savedata['save_scheme_version'] = 0.1
        save_object(self, savedata, open_references)
        c = 0
        while open_references and c < 10:
            c += 1
            print(len(savedata))
            print('---------------------------')
            for obj in list(open_references.values()):
                save_object(obj, savedata, open_references)

        # savedata['forest_keeper'] = self.forest_keeper.save()
        # savedata['ui_manager'] = self.ui_manager.save()
        # savedata['graph_scene'] = self.graph_scene.save()
        # savedata['graph_view'] = self.graph_view.save()
        # print savedata
        print('total savedata: %s chars.' % len(str(savedata)))
        print(savedata)
        return savedata

        # f = open('kataja_default.cfg', 'w')
        # json.dump(prefs.__dict__, f, indent = 1)
        # f.close()

# def maybeSave(self):
# if False and self.scribbleArea.isModified():
# ret  = QtGui.QMessageBox.warning(self, self.tr("Scribble"),
# self.tr("The image has been modified.\n"
# "Do you want to save your changes?"),
# QtGui.QMessageBox.Yes | QtGui.QMessageBox.Default,
# QtGui.QMessageBox.No,
# QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Escape)
# if ret  == QtGui.QMessageBox.Yes:
# return True # self.saveFile("png")
# elif ret  == QtGui.QMessageBox.Cancel:
# return False
#
# return True
#
# def saveFile(self, fileFormat):
# initialPath  = QtCore.QDir.currentPath() + "/untitled." + fileFormat
#
# fileName  = QtGui.QFileDialog.getSaveFileName(self, self.tr("Save As"),
# initialPath,
# self.tr("%1 Files (*.%2);;All Files (*)")
# .arg(QtCore.QString(fileFormat.toUpper()))
# .arg(QtCore.QString(fileFormat)))
# if fileName.isEmpty():
# return False
#        else:
#            return self.scribbleArea.saveImage(fileName, fileFormat)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = KatajaMain(app, sys.argv)
    window.show()

    sys.exit(app.exec_())
