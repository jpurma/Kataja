#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#############################################################################
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
#############################################################################

# Note: convention that I try to start following is that Kataja methods are in
# small caps and underscore (Python convention), but Qt methods are in camelcase.
# Classnames are in camelcase.

import encodings
import gc
import os.path
import shlex
import subprocess
import sys
import time
import cPickle
import pprint

from PyQt5.QtCore import Qt
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtPrintSupport as QtPrintSupport
import PyQt5.QtWidgets as QtWidgets
from kataja.ConstituentNode import ConstituentNode
from kataja.Controller import ctrl, prefs, qt_prefs, colors
from kataja.Forest import Forest
from kataja.ForestKeeper import ForestKeeper
from kataja.GraphScene import GraphScene
from kataja.GraphView import GraphView
from kataja.Preferences import Preferences, QtPreferences
from kataja.Presentation import TextArea
from kataja.Edge import SHAPE_PRESETS, EDGE_PRESETS
from kataja.UIManager import UIManager
from kataja.globals import FEATURE_EDGE, CONSTITUENT_EDGE
from kataja.ui.UIPanel import ColorWheelPanel
from kataja.ui.MenuItem import MenuItem
from kataja.ui.PreferencesDialog import PreferencesDialog
from kataja.utils import to_unicode, time_me, save_object
from kataja.visualizations.available import VISUALIZATIONS



# show labels
ONLY_LEAF_LABELS = 0
ALL_LABELS = 1
ALIASES = 2

# only for debugging (Apple-m, memory check), can be commented
# try:
#    import objgraph
# except ImportError:
#    objgraph = None

# KatajaMain > UIView > UIManager > GraphView > GraphScene > Leaves etc.

class KatajaMain(QtWidgets.QMainWindow):
    """ Qt's main window. When this is closed, application closes. Graphics are
    inside this, in scene objects with view widgets. This window also manages
    keypresses and menus. """

    singleton_key = 'KatajaMain'
    saved_fields = ['graph_scene', 'graph_view', 'ui_manager', 'forest_keeper', 'forest']

    @time_me
    def __init__(self, app, args):
        """ KatajaMain initializes all its children and connects itself to
        be the main window of the given application. """
        t = time.time()
        QtWidgets.QMainWindow.__init__(self)
        print '---- initialized MainWindow base class ... ', time.time() - t
        self.app = app
        self.fontdb = QtGui.QFontDatabase()
        print '---- set up font db ... ', time.time() - t
        qt_prefs.late_init(prefs, self.fontdb)
        self.app.setFont(qt_prefs.ui_font)
        print '---- initialized prefs ... ', time.time() - t
        ctrl.late_init(self)
        print '---- controller late init ... ', time.time() - t
        self.graph_scene = GraphScene(main=self, graph_view=None)
        print '---- scene init ... ', time.time() - t
        self.graph_view = GraphView(main=self, graph_scene=self.graph_scene)
        print '---- view init ... ', time.time() - t
        self.graph_scene.graph_view = self.graph_view
        self.ui_manager = UIManager(self)
        print '---- ui init ... ', time.time() - t
        self.forest_keeper = ForestKeeper(main=self)
        print '---- forest_keeper init ... ', time.time() - t
        self.forest = Forest(main=self)
        print '---- forest init ... ', time.time() - t
        self.visualizations = VISUALIZATIONS
        print '---- visualizations init ... ', time.time() - t
        app.setPalette(colors.palette)
        self.setCentralWidget(self.graph_view)

        print '---- set palette ... ', time.time() - t
        self.load_treeset()
        print '---- loaded treeset ... ', time.time() - t
        self._actions = {}
        self._shortcuts = {}
        x, y, w, h = (50, 50, 940, 720)
        self.create_actions()
        self.setMinimumSize(w, h)
        self.setWindowTitle(self.tr("Kataja"))
        self.setGeometry(x, y, w, h)
        self.add_message('Welcome to Kataja! (h) for help')
        self.color_wheel = None
        self.action_finished()
        print '---- finished start sequence... ', time.time() - t


    def load_treeset(self, treeset_list=[]):
        """ Loads and initializes a new set of trees. Has to be done before the program can do anything sane. """
        if treeset_list:
            self.forest_keeper = ForestKeeper(main=self, treelist=treeset_list)
        else:
            self.forest_keeper = ForestKeeper(main=self, file_name=prefs.debug_treeset)
        self.change_forest(self.forest_keeper.forest)


    #### Visualization #############################################################



    def set_forest(self, forest):
        self.forest = forest
        if not forest.visualization:
            forest.change_visualization(prefs.default_visualization)
        else:
            forest.visualization.prepare(forest)

    def change_forest(self, forest):
        """ Tells the scene to remove current tree and related data and change it to a new one """
        if self.forest:
            self.forest.clear_scene()
        self.ui_manager.clear_items()
        self.set_forest(forest)
        self.forest.update_colors()
        self.forest.info_dump()
        self.graph_scene.displayed_forest = forest
        self.forest.add_all_to_scene()
        self.graph_scene.reset_zoom()
        self.ui_manager.update_all_fields()
        self.forest.undo_manager.init_if_empty()

    def switch_to_next_forest(self):
        i, forest = self.forest_keeper.next()
        self.change_forest(forest)
        return i

    def switch_to_previous_forest(self):
        i, forest = self.forest_keeper.prev()
        self.change_forest(forest)
        return i

    def action_finished(self, m=''):
        self.forest.undo_manager.record(m)
        self.graph_scene.draw_forest(self.forest)

    def redraw(self):
        self.graph_scene.draw_forest(self.forest)

    def add_message(self, msg):
        """ :type msg: StringType """
        self.ui_manager.add_message(msg)


    #### Keyboard events ##########
    def mousePressEvent(self, event):
        """ KatajaMain doesn't do anything with mousePressEvents, it delegates
        them downwards. This is for debugging. """
        QtWidgets.QMainWindow.mousePressEvent(self, event)

    def kkeyPressEvent(self, event):
        """ keyPresses are intercepted here and some feedback of them is given,
        then they are delegated further """
        self.ui_manager.add_feedback_from_command(event.text())
        # if all([item.can_take_keyevent(event) for item in ctrl.selected]):
        #    for item in ctrl.selected:
        #        item.take_keyevent(event)
        #    return

        # if event.text() in self._shortcuts:
        #    act = self._shortcuts[event.text()]
        #    act.trigger()
        self.ui_manager.show_command_prompt()
        return QtWidgets.QMainWindow.keyPressEvent(self, event)

    def key_press(self, event):
        """ Other widgets can send their key presses here for global navigation
        """
        key = event.key()
        qtkey = QtCore.Qt.Key
        focus = ctrl.focus  # : :type focus: Movable

        if key == qtkey.Key_Down:
            if not focus:
                if self.forest.roots:
                    self.forest.roots[0].take_focus()
            else:
                focus.move_focus_down()
        elif key == qtkey.Key_Right:
            if not focus:
                if self.forest.roots:
                    self.forest.roots[0].take_focus()
            else:
                focus.move_focus_right()
        elif key == qtkey.Key_Up:
            if not focus:
                if self.forest.roots:
                    self.forest.roots[0].take_focus()
            else:
                focus.move_focus_up()
        elif key == qtkey.Key_Left:
            if not focus:
                if self.forest.roots:
                    self.forest.roots[0].take_focus()
            else:
                focus.move_focus_left()
        elif key == qtkey.Key_Space:
            if focus:
                focus.activate_menu()
        elif key == qtkey.Key_Enter or key == qtkey.Key_Return:
            if focus:
                focus.trigger_menu()

    #### Actions and Menus ####################################################

    def action(self, text, method, shortcut='', local_shortcut='', trig=None, checkable=False, checked=False,
               viewgroup=None, condition=None, clickable=False, menu_type='', source=None, button=''):
        """ Creates Qt's QAction and populates it with some properties. Action
        is added to our dictionary of actions, which is used to disable and
        enable actions when necessary. """
        act = QtWidgets.QAction(text, self)
        act.triggered.connect(method)
        data = {}
        if shortcut:
            # self._shortcuts[shortcut] = act
            act.setShortcut(QtGui.QKeySequence(shortcut))
            act.setShortcutContext(QtCore.Qt.ApplicationShortcut)
        if local_shortcut:
            data['local_shortcut'] = QtGui.QKeySequence(local_shortcut)
        if viewgroup:
            act.setActionGroup(viewgroup)
        if checkable or checked:
            act.setCheckable(True)
            act.setChecked(checked)
        if condition:
            data['condition'] = condition
        if menu_type:
            data['menu_type'] = menu_type
        if source:
            data['source'] = source
        if data:
            act.setData(data)
        if button:
            if button in self.ui_manager.ui_buttons:
                button_item = self.ui_manager.ui_buttons[button]
                if hasattr(button_item, 'clicked'):
                    button_item.clicked.connect(act.trigger)
                elif hasattr(button_item, 'activated'):
                    button_item.activated.connect(act.trigger)

        self._actions[text] = act
        return act


    def create_actions(self):
        """ Build menus and other actions that can be triggered by user"""

        def _build_menu(menu, actions):
            for item in actions:
                if isinstance(item, str) and item == '---':
                    menu.addSeparator()
                else:
                    menu.addAction(item)
                    self.addAction(item)
            self.menuBar().addMenu(menu)

        # File menu
        file_menu = QtWidgets.QMenu(self.tr("&File"), self)
        actions = [self.action('&Open', self.open_kataja_file, shortcut='Ctrl+o'), '---',
                   self.action('&Save', self.save_kataja_file, shortcut='Ctrl+s'), self.action('Save as', self.save_as),
                   '---', self.action('&Print', self.print_to_file, 'Ctrl+p'),
                   self.action('&Render in Blender', self.render_in_blender, 'Ctrl+r'), '---',
                   self.action("Preferences", self.open_preferences),
                   self.action("&Quit", self.app.closeAllWindows, 'Ctrl+q')]
        _build_menu(file_menu, actions)

        # Build menu
        build_menu = QtWidgets.QMenu(self.tr("&Build"), self)
        actions = [self.action('&Next structure', self.next_structure, shortcut='.', button='next_tree'),
                   self.action('&Prev structure', self.previous_structure, shortcut=',', button='prev_tree'),
                   self.action('Animation step forward', self.animation_step_forward, shortcut='>'),
                   self.action('Animation step backward', self.animation_step_backward, shortcut='<')]
        _build_menu(build_menu, actions)

        # Add a visualization design menu, where you can change all attributes of visualization. Or make it a Panel.

        # Rules menu
        rules_menu = QtWidgets.QMenu('&Rules', self)

        # change this to show 3 options instead of check.
        actions = [self.action('Show &labels in middle nodes', self.toggle_label_visibility, 'l', checkable=True,
                               checked=self.forest.settings.label_style()),
                   self.action('Show &brackets', self.toggle_brackets, 'b', checkable=True),
                   self.action('&connections end at center', self.toggle_magnets, 'c', checkable=True,
                               checked=not prefs.use_magnets),
                   self.action('Show &traces', self.toggle_traces, 't', checkable=True,
                               checked=not self.forest.settings.uses_multidomination()),
                   self.action('Edge &shapes', self.change_node_edge_shape, 's', checkable=False),
                   self.action('Feature edge &Shapes', self.change_feature_edge_shape, 'Shift+S', checkable=False),
                   self.action('Show merge &order', self.show_merge_order, 'o', checkable=True),
                   self.action('Show select &Order', self.show_select_order, 'Shift+o', checkable=True)]
        _build_menu(rules_menu, actions)

        # View
        view_actions = QtWidgets.QActionGroup(self)
        view_menu = QtWidgets.QMenu('View', self)
        vis_actions = []
        for name, vis in VISUALIZATIONS.items():
            vis_actions.append(self.action(name, self.change_visualization_command, vis.shortcut, checkable=True,
                                           viewgroup=view_actions))

        actions = vis_actions + ['---', self.action('Change &Colors', self.change_colors, 'Shift+C', checkable=False),
                                 self.action('Adjust &Colors', self.adjust_colors, 'Shift+Alt+C', checkable=False),
                                 self.action('&Zoom to fit', self.graph_scene.fit_to_window, 'z'), '---',
                                 self.action('&Fullscreen', self.toggle_full_screen, 'F', checkable=True)]
        _build_menu(view_menu, actions)

        # Help
        help_menu = QtWidgets.QMenu(self.tr("Help"), self)
        actions = [self.action('&Help', self.show_help_message, 'h')]
        _build_menu(help_menu, actions)

        self.addAction(self.action('key_esc', self.key_esc, 'Escape'))
        self.addAction(self.action('key_backspace', self.key_backspace, 'Backspace'))
        self.addAction(self.action('key_return', self.key_return, 'Return'))
        self.addAction(self.action('key_left', self.key_left, 'Left'))
        self.addAction(self.action('key_right', self.key_right, 'Right'))
        self.addAction(self.action('key_up', self.key_up, 'Up'))
        self.addAction(self.action('key_down', self.key_down, 'Down'))
        self.addAction(self.action('key_tab', self.key_tab, 'Tab'))
        self.addAction(self.action('undo', self.undo, 'Ctrl+z'))
        self.addAction(self.action('redo', self.redo, 'Ctrl+Shift+z'))
        self.addAction(self.action('key_m', self.key_m, 'm'))

    #### Keyboard reading ######################################################

    # Since QGraphicsItems cannot have actions and action shortcuts tend to
    # override QGraphicsItems' keyevents, we can make main window's actions as general mechanism
    # for delivering keypresses to further items.

    def key_backspace(self):
        for item in ctrl.selected:
            item.undoable_delete()
        self.action_finished()


    def key_return(self, **kw):
        if ctrl.ui_focus:
            pass
        elif ctrl.selected:
            for item in ctrl.selected:
                if hasattr(item, 'click'):
                    item.click(None)

    def key_m(self):
        if ctrl.single_selection():
            item = ctrl.get_selected()
            if isinstance(item, ConstituentNode):
                print 'merge up, missing function call here'
                assert (False)

    def key_left(self):
        if not ctrl.ui_focus:
            self.graph_scene.move_selection('left')

    def key_right(self):
        if not ctrl.ui_focus:
            self.graph_scene.move_selection('right')

    def key_up(self):
        if not ctrl.ui_focus:
            self.graph_scene.move_selection('up')

    def key_down(self):
        if not ctrl.ui_focus:
            self.graph_scene.move_selection('down')

    def key_esc(self):
        if ctrl.ui_focus:
            ui_focus = ctrl.ui_focus  # : :type ui_focus = MovableUI
            ui_focus.cancel()
        for item in ctrl.on_cancel_delete:
            self.forest.delete_item(item)

    def key_tab(self):
        print 'tab-tab!'

    def undo(self):
        self.forest.undo_manager.undo()
        #self.action_finished()

    def redo(self):
        self.forest.undo_manager.redo()
        #self.action_finished()


    #### ConstituentNode's radial menu commands ################################

    def do_merge(self, caller, event):
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
        if isinstance(caller, MenuItem):
            caller = caller.host_node
        self.forest.command_delete(caller)
        self.action_finished()
        ctrl.focus = None
        return True

    def toggle_fold_node(self, caller, event):
        if isinstance(caller, MenuItem):
            caller = caller.host_node
        if caller.is_folded_away():
            self.add_message(u'Unfolding %s to %s' % (caller.linearized(), unicode(caller)))
            caller.unfold_triangle()
            self.action_finished()  # recalculate their positions
        else:
            self.add_message(u'Folding %s to %s' % (unicode(caller), caller.linearized()))
            caller.fold()
        return True

    def disconnect_node(self, caller=None, event=None):
        if isinstance(caller, MenuItem):
            caller = caller.host_node
        self.forest.disconnect_node_node_from_tree(caller)
        self.action_finished()
        ctrl.focus = None
        return True

    def copy_selected(self, **kw):
        """ Make a copy of element and put it beside the original """
        for node in ctrl.get_all_selected():
            self.forest.copy_node(node)
        self.action_finished()
        return True


    ### New node creation commands #############################################

    def add_text_box(self, caller=None):
        text = ''
        if hasattr(caller, 'get_text_input'):
            text = caller.get_text_input()
            text_area = TextArea(text)
            text_area.set_original_position(caller.get_current_position())
            self.forest.store(text_area)
            text_area.assert_scene()
        self.action_finished()

    def add_new_constituent(self, caller=None):
        text = ''
        if hasattr(caller, 'get_text_input'):
            text = caller.get_text_input()
        if ctrl.single_selection():  # live editing
            self.forest.reform_constituent_node_from_string(text, ctrl.get_selected())
        else:
            self.forest.create_node_from_string(text, caller.pos())
        self.action_finished()

    def add_new_tree(self, caller=None):
        text = ''
        if hasattr(caller, 'get_text_input'):
            text = caller.get_text_input()
        pos = caller.pos()
        self.forest.create_tree_from_string(text, pos=pos)
        self.action_finished()


    ### Menu management #######################################################

    def enable_actions(self):
        """ Restores menus """
        for action in self._actions.values():
            action.setDisabled(False)

    def disable_actions(self):
        """ Actions shouldn't be initiated when there is other multi-phase
        action going on """
        for action in self._actions.values():
            action.setDisabled(True)


    ### Menu actions ##########################################################

    # toggle label visibility -action (l)
    def toggle_label_visibility(self):
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


    # change colors -action (shift-c)
    def change_colors(self):
        color_panel = self.ui_manager.ui_panels['Colors']
        if not color_panel.isVisible():
            color_panel.show()
        else:
            self.forest.settings._hsv = None
            self.forest.update_colors()
            self.activateWindow()
            # self.ui.add_message('Color seed: H: %.2f S: %.2f L: %.2f' % ( h, s, l))
            self.action_finished()

    # adjust colors -action (shift-alt-c)
    def adjust_colors(self, hsv):
        self.forest.settings.hsv(hsv)
        self.forest.update_colors(adjusting=True)
        #adjust_colorsself.activateWindow()
        #self.action_finished('adjust colors')

    # triggered by color mode selector in colors panel 
    def change_color_mode(self, mode):
        print mode
        if mode != prefs.color_mode:
            prefs.color_mode = mode
            self.forest.update_colors()

            # Show traces -action (t)

    def toggle_traces(self):
        if self.forest.settings.traces_are_grouped_together() and not self.forest.settings.uses_multidomination():
            self.forest.settings.uses_multidomination(True)
            self.forest.settings.traces_are_grouped_together(False)
            self.add_message('(t) use multidominance')
            self.forest.traces_to_multidomination()
            self.action_finished('use multidominance')
        elif (not self.forest.settings.traces_are_grouped_together()) and not self.forest.settings.uses_multidomination():
            self.forest.settings.uses_multidomination(False)
            self.forest.settings.traces_are_grouped_together(True)
            self.add_message('(t) use traces, group them to one spot')
            self.action_finished('use traces, group them to one spot')
            self.forest.group_traces_to_chain_head()
        elif self.forest.settings.uses_multidomination():
            self.forest.settings.uses_multidomination(False)
            self.forest.settings.traces_are_grouped_together(False)
            self.add_message('(t) use traces, show constituents in their base merge positions')
            self.forest.multidomination_to_traces()
            self.action_finished('use traces, show constituents in their base merge positions')

    # Brackets are visible always for non-leaves, never or for important parts
    def toggle_brackets(self):
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
        self.action_finished('toggle brackets')

    # Show order-feature
    def show_merge_order(self):
        if self.forest.settings.shows_merge_order():
            self.add_message('(o) Hide merge order')
            self.forest.settings.shows_merge_order(False)
            self.forest.remove_order_features('M')
        else:
            self.add_message('(o) Show merge order')
            self.forest.settings.shows_merge_order(True)
            self.forest.add_order_features('M')
        self.action_finished('toggle merge order')

    def show_select_order(self):
        if self.forest.settings.shows_select_order():
            self.add_message('(O) Hide select order')
            self.forest.settings.shows_select_order(False)
            self.forest.remove_order_features('S')
        else:
            self.add_message('(O) Show select order')
            self.forest.settings.shows_select_order(True)
            self.forest.add_order_features('S')
        self.action_finished('toggle select order')


    # Lines connect to margins -action (b)
    def toggle_magnets(self):
        if self.forest.settings.uses_magnets():
            self.add_message('(c) 0: Lines connect to node margins')
            self.forest.settings.uses_magnets(False)
        else:
            self.add_message('(c) 1: Lines aim to the center of the node')
            self.forest.settings.uses_magnets(True)
        self.action_finished('toggle magnets')

    # Change node edge shapes -action (s)
    def change_node_edge_shape(self, shape=''):
        if shape and shape in SHAPE_PRESETS:
            self.forest.settings.edge_shape_name(CONSTITUENT_EDGE, shape)
            i = SHAPE_PRESETS.keys().index(shape)
        else:
            i = SHAPE_PRESETS.keys().index(self.forest.settings.edge_shape_name(CONSTITUENT_EDGE))
            if i == len(SHAPE_PRESETS):
                i = 0
            shape = SHAPE_PRESETS.keys()[i]
            self.forest.settings.edge_shape_name(CONSTITUENT_EDGE, name)
        self.ui_manager.ui_buttons['line_type'].setCurrentIndex(i)
        self.add_message('(s) Change constituent edge shape: %s-%s' % (i, shape))
        #EDGE_PRESETS[CONSTITUENT_EDGE]['shape'] = shape 
        #for forest in self.forest_keeper.get_forests():
        #    for edge in [x for x in forest.edges.values() if x.edge_type == CONSTITUENT_EDGE]:
        #        edge.set_shape(shape)
        #        self.ui_manager.reset_control_points(edge)
        #        edge.update()

        self.action_finished('change edge shape')


    # Change feature edge shapes -action (S)
    def change_feature_edge_shape(self):
        if shape and shape in SHAPE_PRESETS:
            self.forest.settings.edge_shape_name(CONSTITUENT_EDGE, shape)
            i = SHAPE_PRESETS.keys().index(shape)
        else:
            i = SHAPE_PRESETS.keys().index(self.forest.settings.edge_shape_name(FEATURE_EDGE))
            if i == len(SHAPE_PRESETS):
                i = 0
            shape = SHAPE_PRESETS.keys()[i]
            self.forest.settings.edge_shape_name(FEATURE_EDGE, name)
        self.ui_manager.ui_buttons['feature_line_type'].setCurrentIndex(i)
        self.add_message('(s) Change feature edge shape: %s-%s' % (i, shape))

        self.action_finished('change feature edge shape')


    # Next structure -action (.)
    def next_structure(self):
        i = self.switch_to_next_forest()
        self.ui_manager.clear_items()
        self.add_message(u'(.) tree %s: %s' % (i + 1, self.forest.textual_form()))
        self.action_finished('switch next tree set')

    # Prev structure -action (,)
    def previous_structure(self):
        i = self.switch_to_previous_forest()
        self.ui_manager.clear_items()
        self.add_message(u'(,) tree %s: %s' % (i + 1, self.forest.textual_form()))
        self.action_finished('switch previous tree set')

    # Change visualization style -action (1...9)
    def change_visualization_command(self):
        visualization_key = str(self.sender().text())
        self.ui_manager.update_field('visualization_selector', visualization_key)
        self.forest.change_visualization(visualization_key)
        self.add_message(visualization_key)
        self.action_finished('change visualization to %s' % visualization_key)

    # Full screen -action (f)
    def toggle_full_screen(self):
        if self.isFullScreen():
            self.showNormal()
            self.add_message('(f) windowed')
            self.ui_manager.restore_panel_positions()
        else:
            self.ui_manager.store_panel_positions()
            self.showFullScreen()
            self.add_message('(f) fullscreen')
        self.graph_scene.fit_to_window()
        self.action_finished('resize to full screen')

    # Blender export -action (Command-r)
    def render_in_blender(self):
        self.graph_scene.export_3d(prefs.blender_env_path + '/temptree.json')
        self.add_message('Command-r  - render in blender')
        command = '%s -b %s/puutausta.blend -P %s/treeloader.py -o //blenderkataja -F JPEG -x 1 -f 1' % (
            prefs.blender_app_path, prefs.blender_env_path, prefs.blender_env_path)
        args = shlex.split(command)
        subprocess.Popen(args)  # , cwd =prefs.blender_env_path)

    # print as pdf -action (Command-p)
    def print_to_file(self):
        # hide unwanted components
        sc = self.graph_scene
        no_brush = QtGui.QBrush(Qt.NoBrush)
        sc.setBackgroundBrush(no_brush)
        gloss = prefs.include_gloss_to_print
        if gloss:
            self.graph_scene.photo_frame = self.graph_scene.addRect(sc.visible_rect_and_gloss().adjusted(-1, -1, 2, 2),
                                                                    colors.selection_pen)
        else:
            if self.forest.gloss and self.forest.gloss.isVisible():
                self.forest.gloss.hide()
            self.graph_scene.photo_frame = self.graph_scene.addRect(sc.visible_rect().adjusted(-1, -1, 2, 2),
                                                                    colors.selection_pen)
        self.graph_scene.update()
        self.graph_view.repaint()
        self.startTimer(50)

    def timerEvent(self, event):
        """ Timer event only for printing, for 'snapshot' effect """
        self.killTimer(event.timerId())
        # Prepare file and path
        path = prefs.print_file_path
        if not path.endswith('/'):
            path += '/'
        if not os.path.exists(path):
            print "bad path for printing (print_file_path in preferences) , using '.' instead."
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
        target = QtCore.QRectF(0, 0, source.width(), source.height())
        # Prepare printer
        pr = QtPrintSupport.QPrinter

        printer = pr(pr.ScreenResolution)
        # printer = QtGui.QPrinter(QtGui.QPrinter.HighResolution)
        printer.setPaperSize(target.size(), pr.DevicePixel)
        printer.setOutputFormat(pr.NativeFormat)
        printer.setResolution(prefs.dpi)
        # printer.setFontEmbeddingEnabled(True)
        # print printer.fontEmbeddingEnabled()
        # printer.setOutputFormat(QtGui.QPrinter.PdfFormat)

        printer.setOutputFileName(full_path)
        printer.setFullPage(True)
        # Paint it
        painter = QtGui.QPainter()
        painter.begin(printer)
        self.graph_scene.render(painter, target=target, source=source)
        painter.end()
        # Thank you!
        self.add_message("printed to %s as PDF with %s dpi." % (full_path, prefs.dpi))
        # Restore image
        self.graph_scene.setBackgroundBrush(colors.gradient)
        if self.forest.gloss:
            self.forest.gloss.show()
        self.action_finished()
        # hide unwanted components

    # step forward -action (>)
    def animation_step_forward(self):
        self.forest.next_derivation_step()
        self.add_message('Step forward')
        self.action_finished()

    # step backward -action (<)
    def animation_step_backward(self):
        self.forest.previous_derivation_step()
        self.add_message('Step backward')
        self.action_finished()

    # Not called from anywhere yet, but useful
    def release_selected(self, **kw):
        for node in ctrl.get_all_selected():
            node.release()
        self.action_finished()
        return True


    # help -action (h)
    def show_help_message(self):
        m = ""

        #        m ="""(h):------- KatajaMain commands ----------
        # (left arrow/,):previous structure   (right arrow/.):next structure
        # (1-5):change or refresh visualization of the tree
        # (f):fullscreen/windowed mode
        # (p):print tree to file
        # (b):show/hide labels in middle of edges
        # (c):curved/straight edges
        # (q):quit"""
        self.add_message(m)


    def open_preferences(self):
        if not self.ui_manager.preferences_dialog:
            self.ui_manager.preferences_dialog = PreferencesDialog(self)
        self.ui_manager.preferences_dialog.open()

        # open -action (Command-o)

    def open_kataja_file(self):
        """ Load kataja data """
        # fileName  = QtGui.QFileDialog.getOpenFileName(self,
        #                                             self.tr("Open File"),
        #                                             QtCore.QDir.currentPath())
        filename, filetypes = QtWidgets.QFileDialog.getOpenFileName(self, "Open KatajaMain tree", "",
                                                                    "KatajaMain files (*.kataja *.zkataja);;Text files containing bracket trees (*.txt, *.tex)")
        # filename = 'savetest.kataja'
        if filename:
            self.load_state_from_file(filename)
            self.add_message("Loaded '%s'." % to_unicode(filename))
            self.action_finished()

    def load_state_from_file(self, filename=u''):
        ctrl.loading = True
        self.clear_all()
        self.scene.displayed_forest = None
        if filename.endswith('.zkataja'):
            f = gzip.open(filename, 'rb')
            data = cPickle.load(f)
        else:
            f = open(filename, 'rb')
            # f = codecs.open(filename, 'rb', encoding = 'utf-8')
            data = cPickle.load(f)
        f.close()
        prefs.update(data['preferences'].__dict__)
        qt_prefs.update(prefs)
        self.forest_keeper.load(data['forest_keeper'])
        ctrl.loading = False
        ctrl.change_forest(self.forest_keeper.forest)
        ctrl.update_colors()


    # save -action (Command-s)
    def save_kataja_file(self):
        """ Save kataja data """
        # action  = self.sender()
        self.action_finished()
        filename = prefs.file_name
        all_data = self.create_save_data()
        pickle_format = 0
        if filename.endswith('.zkataja'):
            f = gzip.open(filename, 'w')
        else:
            f = open(filename, 'w')
        cPickle.dump(all_data, f, pickle_format)
        f.close()
        self.add_message("Saved to '%s'." % filename)

        filename = prefs.file_name + '.dict'
        f = open(filename, 'w')
        pp = pprint.PrettyPrinter(indent=1, stream=f)
        print 'is readable: ', pprint.isreadable(all_data)
        pp.pprint(all_data)
        f.close()
        self.add_message("Saved to '%s'." % filename)

        # fileFormat  = action.data().toByteArray()
        # self.saveFile(fileFormat)

    def save_as(self):
        self.action_finished()
        filename = to_unicode(QtWidgets.QFileDialog.getSaveFileName(self, "Save KatajaMain tree", "",
                                                                    "KatajaMain files (*.kataja *.zkataja)"))
        prefs.file_name = filename
        ctrl.save_state_to_file(filename)
        self.add_message("Saved to '%s'." % filename)

    def clear_all(self):
        if self.forest:
            self.forest.clear_scene()
        self.ui_manager.clear_items()
        self.forest_keeper = ForestKeeper()


    #### Action preconditions ##################################################

    # return True or False: should the related action be enabled or disabled

    def can_root_merge(self, event):
        return ctrl.single_selection() and not ctrl.get_selected().is_root_node()

    #### Unused two-phase actions ###############################################

    def start_pointing_mode(self, event, method=None, data={}):
        """ Begin pointing mode, mouse pointer draws a line behind it and normal actions are disabled """
        ctrl.pointing_mode = True
        ctrl.pointing_method = method
        ctrl.pointing_data = data
        self.ui_manager.begin_stretchline(data['start'].pos(), event.scenePos())  # +data['startposF']
        # self.setMouseTracking(True)
        self.app.setOverrideCursor(QtCore.Qt.CrossCursor)
        self.graph.setDragMode(QtWidgets.QGraphicsView.NoDrag)

    def end_pointing_mode(self, event):
        """ End pointing mode and return to normal """
        ctrl.pointing_mode = False
        ctrl.pointing_data = {}
        self.ui_manager.end_stretchline()
        # self.setMouseTracking(False)
        self.app.restoreOverrideCursor()
        self.graph.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def begin_merge_to(self, event):
        """ MergeTo is a two phase action. First the target is selected in pointing mode, then 'end_merge_to' is called """
        self.start_pointing_mode(event, method=self.end_merge_to, data={'start': ctrl.get_selected()})
        return False

    def end_merge_to(self, event):
        node_A = ctrl.pointing_data['start']
        node_B = ctrl.pointing_data['target']
        self.forest.Merge(node_A, node_B)
        node_A.release()
        # node_A.state =SELECTED # deselect doesn't have effect unless node is selected
        self.end_pointing_mode(event)
        self.action_finished()
        return True

    def begin_move_to(self, event):
        self.start_pointing_mode(event, method=self.end_move_to, data={'start': ctrl.get_selected()})
        return False

    def end_move_to(self, event):
        node_A = ctrl.pointing_data['start']
        node_B = ctrl.pointing_data['target']
        self.forest.cut_and_merge(node_A, node_B)
        node_A.release()
        # node_A.state =SELECTED # deselect doesn't have effect unless node is selected
        self.end_pointing_mode(event)
        self.action_finished()
        return True


    #### Other window events ###################################################

    def closeEvent(self, event):
        """ Shut down the program, give some debug info """
        QtWidgets.QMainWindow.closeEvent(self, event)
        if ctrl.print_garbage:
            # import objgraph
            print 'garbage stats:', gc.get_count()
            gc.collect()
            print 'after collection:', gc.get_count()
            if gc.garbage:
                print 'garbage:', gc.garbage

                # objgraph.show_most_common_types(limit =40)
        print '...done'


    @time_me
    def create_save_data(self):
        savedata = {}
        open_references = {}
        save_object(prefs, savedata, open_references)
        savedata['save_scheme_version'] = 0.1
        save_object(self, savedata, open_references)
        c = 0
        while open_references and c < 10:
            c += 1
            print len(savedata)
            print '---------------------------'
            for obj in open_references.values():
                save_object(obj, savedata, open_references)

        #savedata['forest_keeper'] = self.forest_keeper.save()
        #savedata['ui_manager'] = self.ui_manager.save()
        #savedata['graph_scene'] = self.graph_scene.save()
        #savedata['graph_view'] = self.graph_view.save()
        #print savedata
        print 'total savedata: %s chars.' % len(str(savedata))
        return savedata

        # f = open('kataja_default.cfg', 'w')
        # json.dump(prefs.__dict__, f, indent = 1)
        # f.close()


#    def maybeSave(self):
#        if False and self.scribbleArea.isModified():
#            ret  = QtGui.QMessageBox.warning(self, self.tr("Scribble"),
#                        self.tr("The image has been modified.\n"
#                                "Do you want to save your changes?"),
#                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.Default,
#                        QtGui.QMessageBox.No,
#                        QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Escape)
#            if ret  == QtGui.QMessageBox.Yes:
#                return True # self.saveFile("png")
#            elif ret  == QtGui.QMessageBox.Cancel:
#                return False
#
#        return True
#
#    def saveFile(self, fileFormat):
#        initialPath  = QtCore.QDir.currentPath() + "/untitled." + fileFormat
#
#        fileName  = QtGui.QFileDialog.getSaveFileName(self, self.tr("Save As"),
#                                    initialPath,
#                                    self.tr("%1 Files (*.%2);;All Files (*)")
#                                    .arg(QtCore.QString(fileFormat.toUpper()))
#                                    .arg(QtCore.QString(fileFormat)))
#        if fileName.isEmpty():
#            return False
#        else:
#            return self.scribbleArea.saveImage(fileName, fileFormat)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = KatajaMain(app, sys.argv)
    window.show()

    sys.exit(app.exec_())
