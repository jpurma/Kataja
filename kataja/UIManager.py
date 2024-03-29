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
import importlib
import inspect
import logging
import os
from collections import OrderedDict

from PyQt6 import QtCore, QtWidgets, QtGui

import kataja.actions
import kataja.globals as g
import kataja.ui_graphicsitems.TouchArea
import kataja.ui_widgets.buttons.OverlayButton as ob
from kataja.KatajaAction import KatajaAction, ShortcutSolver, ButtonShortcutFilter, MediatingAction
from kataja.saved.Edge import Edge
from kataja.saved.Group import Group
from kataja.saved.movables.Arrow import Arrow
from kataja.saved.movables.Node import Node
from kataja.singletons import ctrl, prefs, log
from kataja.ui_graphicsitems.ControlPoint import ControlPoint
from kataja.ui_graphicsitems.NewElementMarker import NewElementMarker
from kataja.ui_support.FloatingTip import FloatingTip
from kataja.ui_widgets.DragInfo import DragInfo
from kataja.ui_widgets.HeadingWidget import HeadingWidget
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.ResizeHandle import GraphicsResizeHandle
from kataja.ui_widgets.buttons.QuickEditButtons import QuickEditButtons
from kataja.ui_widgets.buttons.TopBarButtons import TopBarButtons
from kataja.ui_widgets.embeds.ArrowLabelEmbed import ArrowLabelEmbed
from kataja.ui_widgets.embeds.GroupLabelEmbed import GroupLabelEmbed
from kataja.ui_widgets.embeds.NewElementEmbed import NewElementEmbed
from kataja.ui_widgets.panels.ColorThemePanel import ColorPanel
from kataja.ui_widgets.panels.ColorWheelPanel import ColorWheelPanel
from kataja.ui_widgets.panels.CommentPanel import CommentPanel
from kataja.ui_widgets.panels.ConstituentPanel import ConstituentPanel
from kataja.ui_widgets.panels.FeaturePanel import FeaturePanel
from kataja.ui_widgets.panels.GlossPanel import GlossPanel
from kataja.ui_widgets.panels.HelpPanel import HelpPanel
from kataja.ui_widgets.panels.InputPanel import InputPanel
from kataja.ui_widgets.panels.LexiconPanel import LexiconPanel
from kataja.ui_widgets.panels.LineOptionsPanel import LineOptionsPanel
from kataja.ui_widgets.panels.LogPanel import LogPanel
from kataja.ui_widgets.panels.NavigationPanel import NavigationPanel
from kataja.ui_widgets.panels.ParseTreePanel import ParseTreePanel
from kataja.ui_widgets.panels.ScopePanel import ScopePanel
from kataja.ui_widgets.panels.SemanticsPanel import SemanticsPanel
from kataja.ui_widgets.panels.SymbolPanel import SymbolPanel
from kataja.ui_widgets.panels.VisualizationOptionsPanel import VisualizationOptionsPanel
from kataja.ui_widgets.panels.VisualizationPanel import VisualizationPanel
from kataja.ui_widgets.selection_boxes.TableModelSelectionBox import TableModelSelectionBox
from kataja.visualizations.available import VISUALIZATIONS

NOTHING = 0
SELECTING_AREA = 1
DRAGGING = 2
POINTING = 3

PANELS = [{'class': LogPanel, 'name': 'Log', 'position': 'bottom'},
          {'class': NavigationPanel, 'name': 'Trees', 'position': 'right'},
          {'class': SemanticsPanel, 'name': 'Semantics', 'position': 'right', 'folded': True},
          {'class': VisualizationPanel, 'name': 'Visualization', 'position': 'right'},
          {'class': ScopePanel, 'name': 'Scope', 'position': 'right', 'folded': True},
          {'class': ConstituentPanel, 'name': 'Constituents', 'position': 'right'},
          {'class': FeaturePanel, 'name': 'Features', 'position': 'right'},
          {'class': GlossPanel, 'name': 'Glossa', 'position': 'right', 'folded': True},
          {'class': CommentPanel, 'name': 'Comments', 'position': 'right', 'folded': True},
          {'class': ColorPanel, 'name': 'Color theme', 'position': 'right'},
          {'class': ColorWheelPanel, 'name': 'Color picker', 'position': 'float',
           'closed': True},
          {'class': LineOptionsPanel, 'name': 'Edge drawing', 'position': 'float',
           'closed': True},
          {'class': SymbolPanel, 'name': 'Symbols', 'position': 'right', 'folded': True},
          {'class': VisualizationOptionsPanel, 'name': 'Visualization options',
           'position': 'float', 'closed': True},
          {'class': InputPanel, 'name': 'Input tree', 'position': 'bottom', 'closed': False},
          {'class': LexiconPanel, 'name': 'Lexicon', 'position': 'float', 'closed': False},
          {'class': ParseTreePanel, 'name': 'Parses', 'position': 'float', 'closed': False},
          {'class': HelpPanel, 'name': 'Help', 'position': 'float', 'closed': True}]

menu_structure = OrderedDict([('file_menu', ('&File',
                                             ['new_project', 'new_forest', 'open', 'save',
                                              'save_as', '---', 'print_pdf',  # 'blender_render'
                                              '---', 'preferences', '---', 'quit'])),
                              ('edit_menu', ('&Edit', ['undo', 'redo', '---', 'cut', 'copy',
                                                       'paste'])),
                              ('trees_menu', ('&Trees', ['next_forest', 'previous_forest',
                                                         'next_parse', 'previous_parse',
                                                         'next_derivation_step',
                                                         'prev_derivation_step'])),
                              ('drawing_menu', ('&Drawing', ['$set_visualization',
                                                             '---',
                                                             'select_cn_shape',
                                                             'select_trace_strategy',
                                                             'select_feature_display_mode',
                                                             'switch_syntax_view_mode',
                                                             'toggle_semantics_view'])),
                              ('view_menu', ('&View', ['zoom_to_fit',
                                                       'auto_zoom',
                                                       '---',
                                                       'fullscreen_mode',
                                                       'toggle_recording'])),
                              ('windows_menu', ('&Windows', ['$toggle_panel', '---',
                                                             'toggle_all_panels'])),
                              ('plugin_menu', ('&Plugin', ['manage_plugins', 'reload_plugin',
                                                           '---', '$toggle_plugin'])),
                              ('help_menu', ('&Help', ['help']))])


class UIManager:
    """ UIManager Keeps track of all UI-related widgets and tries to do the most
    work to keep KatajaMain as simple as possible. """

    def __init__(self, main=None):
        self.main = main
        self.scene = main.graph_scene
        self.actions = {}
        self._action_groups = {}
        self._top_menus = {}
        self.top_bar_buttons = None
        self._edit_mode_button = None
        self.quick_edit_buttons = None
        self._items = {}
        self._items_by_host = {}
        self._timer_id = 0
        self._panels = {}
        self._panel_positions = {}
        self.active_embed = None
        self.moving_things = set()
        self.heading = None
        self.button_shortcut_filter = ButtonShortcutFilter()
        self.shortcut_solver = ShortcutSolver(self)
        self.active_scope = g.DOCUMENT
        self._prev_active_scope = g.DOCUMENT
        self.scope_is_selection = False
        self.default_node_type = g.CONSTITUENT_NODE
        self.selection_group = None
        self.preferences_dialog = None
        self.qe_label = None
        self.drag_info = None
        self.floating_tip = None
        self.arrow_actions = []

    def populate_ui_elements(self):
        """ These cannot be created in __init__, as individual panels etc.
        may refer to ctrl.ui_support, which doesn't exist until the __init__  is completed.
        :return:
        """
        # Create actions based on actions.py
        self.create_actions()
        # Create top menus, requires actions to exist
        self.create_menus()
        # Create UI panels, requires actions to exist
        self.create_panels()
        self.create_float_buttons()
        ctrl.main.selection_changed.connect(self.update_selections)
        ctrl.main.forest_changed.connect(self.clear_and_refresh_heading)
        ctrl.main.viewport_moved.connect(self.update_positions)
        ctrl.main.viewport_resized.connect(self.update_positions_and_top_bar)
        ctrl.main.ui_font_changed.connect(self.redraw_panels)

    def position_panels(self):
        for panel in self._panels.values():
            if panel.isFloating():
                panel.move(panel.initial_position())

    def disable_item(self, ui_key):
        """ Disable ui_item, assuming it can be disabled (buttons etc). """
        item = self.get_ui(ui_key)
        item.setEnabled(False)

    def enable_item(self, ui_key):
        """ Set ui_item enabled, for those that have enabled/disabled mode (buttons etc). """
        item = self.get_ui(ui_key)
        item.setEnabled(True)

    def get_action_group(self, action_group_name):
        """ Get action group with this name, or create one if it doesn't exist """
        if action_group_name not in self._action_groups:
            self._action_groups[action_group_name] = QtGui.QActionGroup(self.main)
        return self._action_groups[action_group_name]

    def set_scope(self, scope):
        if scope == g.SELECTION:
            if self.active_scope != g.SELECTION:
                self._prev_active_scope = self.active_scope
            self.scope_is_selection = True
        else:
            self.scope_is_selection = False
        self.active_scope = scope
        ctrl.main.scope_changed.emit()

    def set_help_text(self, text, append=False, prepend=False):
        panel = self.get_panel('HelpPanel')
        if panel:
            if append:
                s = panel.default_text
                panel.set_text('<br/>'.join((s, text)))
            elif prepend:
                s = panel.default_text
                panel.set_text('<br/>'.join((text, s)))
            else:
                panel.set_text(text)

    def set_help_source(self, searchpath, filename):
        panel = self.get_panel('HelpPanel')
        if panel:
            if filename:
                panel.browser.setSearchPaths([searchpath])
                panel.browser.setSource(QtCore.QUrl(filename))
            else:
                panel.set_text(panel.default_text)
                panel.browser.setSearchPaths([])

    def add_ui(self, item, show=True):
        if item.ui_key in self._items:
            print('ui_key ', item.ui_key, ' already exists')
            raise KeyError
        self._items[item.ui_key] = item
        if item.host:
            key = item.host.uid
            if key in self._items_by_host:
                self._items_by_host[key].append(item)
            else:
                self._items_by_host[key] = [item]
        if item.scene_item:
            self.scene.addItem(item)
        # if show:
        #    item.show()

    def remove_ui(self, item, fade=True):
        """ Remove ui_item from active and displayed ui_items. The item may still exist in scene
        as a fading item, but it cannot be reached by ui_manager. Such items have to take care
        that they are removed from scene when they finish fading.
        """
        if fade and not ctrl.play:
            fade = False
        if item.ui_key in self._items:
            del self._items[item.ui_key]
        if item.host:
            key = item.host.uid
            if key in self._items_by_host:
                parts = self._items_by_host.get(key, [])
                if item in parts:
                    parts.remove(item)
                    if not parts:
                        del self._items_by_host[key]
        if item.is_widget:
            self.remove_watched_shortcuts_for(item)
        if fade and item.can_fade:
            item.fade_out()
        else:
            item.hide()
            if item.scene_item:
                self.scene.removeItem(item)
            elif item.is_widget:
                item.close()

    def remove_from_scene(self, item):
        self.scene.removeItem(item)

    def get_ui(self, ui_key) -> QtCore.QObject:
        """ Return a managed ui_support item """
        return self._items.get(ui_key, None)

    def get_ui_by_type(self, host=None, ui_type=None):
        if host is not None:
            items = self.get_uis_for(host)
        else:
            items = self._items.values()
        for item in items:
            if item.ui_type == ui_type:
                return item

    def get_ui_by_role(self, host=None, role=None):
        if host is not None:
            items = self.get_uis_for(host)
        else:
            items = self._items.values()
        for item in items:
            if item.role == role:
                return item

    def get_uis_for(self, obj):
        """ Return ui_items that have this object as host, generally objects related to given object """
        return self._items_by_host.get(obj.uid, [])

    def resize_ui(self, size):
        self.update_positions()

    def update_actions(self):
        # prepare style dictionaries for selections, to be used for displaying style values in UI
        for action in self.actions.values():
            action.update_action()

    def update_action(self, key):
        """ If action is tied to some meter (e.g. number field that is used to show value and
        change it), update the value in the meter and see if it should be enabled. """
        self.actions[key].update_action()

    def update_selections(self):
        """ Many UI elements change mode depending on if object of specific
        type is selected. Also the logic of selection groups has to be handled somewhere. """

        active_embed = self.active_embed

        # clear all ui_support pieces
        for item in list(self._items.values()):
            if item.host and not (item.is_fading_out or item.selection_independent):
                self.remove_ui(item)

        # Have a better way to do this -- halos as UI-items?
        if ctrl.forest and ctrl.forest.nodes:
            for node in ctrl.forest.nodes.values():
                if node.node_type == g.CONSTITUENT_NODE and node.halo:
                    node.toggle_halo(False)

        # create ui_support pieces for selected elements. don't create touchareas and buttons
        # if multiple selection, it gets confusing fast
        if not ctrl.selected:
            self.remove_selection_group()
            self.set_scope(self._prev_active_scope)
        elif len(ctrl.selected) == 1:
            self.remove_selection_group()
            self.set_scope(g.SELECTION)
            item = ctrl.selected[0]
            if isinstance(item, Edge):
                self.update_touch_areas_for_selected_edge(item)
                self.add_control_points(item)
                self.add_buttons_for_edge(item)
            elif isinstance(item, Node):
                self.update_touch_areas_for_selected_node(item)
                self.update_buttons_for_selected_node(item)
                if item.node_type == g.CONSTITUENT_NODE:
                    item.toggle_halo(True)
                    if not active_embed and ctrl.forest.settings.get('highlight_dominated_nodes_on_selection'):
                        for node in item.get_sorted_nodes():
                            if node.node_type == g.CONSTITUENT_NODE and node.is_visible():
                                node.toggle_halo(True, small=True)
            elif isinstance(item, Group):
                self.selection_group = item
                self.add_buttons_for_group(item)
            elif isinstance(item, Arrow):
                self.add_control_points_for_arrow(item)
                self.selection_group = item
                self.add_buttons_for_arrow(item)

        else:
            nodes = []
            groups = []
            for item in ctrl.selected:
                if isinstance(item, Node) and item.can_be_in_groups:
                    nodes.append(item)
                elif isinstance(item, Group):
                    groups.append(item)
            if nodes or groups:
                if self.selection_group and not self.selection_group.persistent:
                    self.selection_group.update_selection(ctrl.selected)
                    self.selection_group.update_shape()
                else:
                    self.selection_group = Group(
                        selection=nodes,
                        persistent=False,
                        color_key=ctrl.drawing.get_group_color_suggestion())
                    self.add_ui(self.selection_group)
                self.add_buttons_for_group(self.selection_group)
            else:
                self.remove_selection_group()

    def has_nodes_in_scope(self, of_type):
        if self.scope_is_selection:
            for item in ctrl.selected:
                if isinstance(item, Node) and item.node_type == of_type:
                    return True
            return False
        return True  # all scope options allow defining node color

    def has_edges_in_scope(self, of_type=None):
        if self.scope_is_selection:
            for item in ctrl.selected:
                if isinstance(item, Edge) and ((not of_type) or item.edge_type == of_type):
                    return True
            return False
        return True  # all scope options allow defining node color

    def remove_selection_group(self):
        if self.selection_group:
            self.remove_ui_for(self.selection_group)
            if not self.selection_group.persistent:
                self.remove_ui(self.selection_group)
            self.selection_group = None

    # unused, but sane
    def focusable_elements(self):
        """ Return those UI elements that are flagged focusable (Kataja's
        focusable, not Qt's). """
        for e in self._items:
            if getattr(e, 'focusable', False) and e.isVisible():
                yield e

    def clear_items(self):
        """ Remove all ui_support objects managed by UIManager. """
        ctrl.deselect_objects()
        for item in list(self._items.values()):
            if not item.permanent_ui:
                self.remove_ui(item, fade=False)

    def update_positions(self):
        """ UI has elements that point to graph scene elements, and when
        something moves there UI has to update its elements too."""
        for item in self._items.values():
            item.update_position()

    def update_positions_and_top_bar(self):
        self.update_positions()
        if self.top_bar_buttons:
            self.top_bar_buttons.update_position()

    def update_position_for(self, obj):
        """ Update position of ui_support-elements for selected (non-ui_support) object. """
        for ui_item in self.get_uis_for(obj):
            ui_item.update_position()

    def remove_ui_for(self, obj):
        """ Remove ui_support-elements for given(non-ui_support) object.
        :param obj: Saved item, needs to have uid
        """
        for ui_item in list(self.get_uis_for(obj)):
            if not ui_item.is_fading_out:
                ui_item.update_position()
                self.remove_ui(ui_item)

    # ### Actions and Menus
    # ####################################################

    def load_actions_from_module(self, mod, added=None, replaced=None):
        """ Seek and import actions from a module. Lower level operation, called from
        create_actions and when initialising plugins.
        :param mod: Python module
        :param added: if a list is provided, these keys were added to a dict from this module. Useful when unloading a
            plugin module.
        :param replaced: if a dict is provided, store an existing action replaced by a new action here.
            Useful for restoring the original state when a plugin has overrode actions.
        :return: list of found action classes
        """
        for class_name in vars(mod):
            if class_name.startswith(
                    '_') or class_name == 'KatajaAction':
                continue
            a_class = getattr(mod, class_name)
            if not (inspect.isclass(a_class) and issubclass(a_class, KatajaAction)):
                continue
            if not a_class.k_action_uid:  # Ignore abstract classes, they are there only to
                # reduce amount of copied code across e.g. different node types.
                continue
            action = a_class()
            if added is not None:
                added.append(action.key)
            if replaced is not None and action.key in self.actions:
                replaced[action.key] = self.actions[action.key]
            self.actions[action.key] = action

    def unload_actions_from_module(self, added, replaced):
        for action_key in added:
            del self.actions[action_key]
        self.actions.update(replaced)

    def create_actions(self):
        """ KatajaActions define user commands and interactions. They are loaded from modules in
        kataja.actions or from plugin's plugin.actions.any_module. """
        def uses_arrow_key(keystr):
            return keystr.endswith('Left') or keystr.endswith('Up') or keystr.endswith('Right') or keystr.endswith('Down')

        self.actions = {}
        self._action_groups = {}
        for module in os.listdir(os.path.dirname(kataja.actions.__file__)):
            if module == '__init__.py' or module[-3:] != '.py':
                continue
            mod_path = 'kataja.actions.' + module[:-3]
            mod = importlib.import_module(mod_path)
            self.load_actions_from_module(mod)
        self.arrow_actions = [a for a in self.actions.values() if a.k_shortcut and uses_arrow_key(str(a.k_shortcut))]
        log.info('Prepared %s actions.' % len(self.actions))

    def prepare_panel_menus(self):
        menu_items = []
        base_action = self.actions['toggle_panel']
        for panel_data in PANELS:
            panel_key = panel_data['class'].__name__
            action = MediatingAction(text=panel_data['name'], target=base_action, key=panel_key)
            menu_items.append(action)
        return menu_items

    def prepare_visualisation_menus(self):
        menu_items = []
        base_action = self.actions['set_visualization']
        for name, vis in VISUALIZATIONS.items():
            action = MediatingAction(text=name, target=base_action, key=name)
            menu_items.append(action)
        return menu_items

    def prepare_plugin_menus(self):
        menu_items = []
        base_action = self.actions['toggle_plugin']
        for key in sorted(self.main.plugin_manager.available_plugins):
            action = MediatingAction(text=key, target=base_action, key=key)
            action.setChecked(key == prefs.active_plugin_name)
            menu_items.append(action)
        return menu_items

    def update_plugin_menu(self):
        plugin_menu = self._top_menus.get('plugin_menu', None)
        if not plugin_menu:
            return
        for action in list(plugin_menu.actions()):
            if isinstance(action, MediatingAction):
                action.host_menu = None
                plugin_menu.removeAction(action)
        for action in self.prepare_plugin_menus():
            plugin_menu.addAction(action)
            action.host_menu = plugin_menu

    def get_action(self, key) -> KatajaAction:
        """ Returns action method for key, None if no such action """
        if key:
            a = self.actions.get(key, None)
            if a:
                return a
            else:
                log.critical(f'missing action: "{key}"')
        else:
            log.critical(f'get_action called with empty key')

    def create_menus(self):
        """ Put actions to menus. Menu structure is defined at the top of this file."""

        def add_menu(parent, menu_label, menu_items):
            new_menu = QtWidgets.QMenu(menu_label, self.main)
            for item in menu_items:
                if isinstance(item, tuple):
                    add_menu(new_menu, item[0], item[1])
                elif item == '---':
                    new_menu.addSeparator()
                elif isinstance(item, QtGui.QAction):
                    new_menu.addAction(item)
                    item.host_menu = new_menu
                else:
                    action = self.actions[item]
                    new_menu.addAction(action)
                    action.host_menu = new_menu

            parent.addMenu(new_menu)
            return new_menu

        def expand_list(label, items):
            """
            :param label: menu title
            :param items: menu items
            :return:
            """
            exp_items = []
            for item in items:
                if isinstance(item, str) and item.startswith("$"):
                    key = item[1:]
                    if key == 'toggle_panel':
                        exp_items += self.prepare_panel_menus()
                    elif key == 'set_visualization':
                        exp_items += self.prepare_visualisation_menus()
                    elif key == 'toggle_plugin':
                        exp_items += self.prepare_plugin_menus()
                elif isinstance(item, tuple):
                    exp_items.append(expand_list(item[0], item[1]))
                else:
                    exp_items.append(item)
            return label, exp_items

        # replace '$names' with dynamic actions
        expanded_menu_structure = OrderedDict()
        for key, data in menu_structure.items():
            expanded_menu_structure[key] = expand_list(*data)

        # build menus
        self._top_menus = {}

        for key, data in expanded_menu_structure.items():
            menu = add_menu(self.main.menuBar(), *data)
            self._top_menus[key] = menu

    # ###################################################################
    #                           PANELS
    # ###################################################################

    def get_panel(self, panel_id) -> Panel:
        return self._panels.get(panel_id, None)

    def get_panel_by_node_type(self, node_type):
        for panel in self._panels.values():
            if getattr(panel, 'node_type', '') == node_type:
                return panel

    def redraw_panels(self):
        for panel in self._panels.values():
            panel.update()

    def show_panel(self, panel_id):
        panel = self.get_panel(panel_id)
        if not panel:
            for panel_data in PANELS:
                if panel_id == panel_data['class'].__name__:
                    self.create_panel(panel_data)
                    panel = self.get_panel(panel_id)
                    break
        if not panel.isVisible():
            panel.show()
        toggle_action = self.get_action('toggle_panel')
        toggle_action.set_checked_for(panel_id, True)

    def hide_panel(self, panel_id):
        panel = self.get_panel(panel_id)
        if panel and panel.isVisible():
            panel.close()
        toggle_action = self.get_action('toggle_panel')
        toggle_action.set_checked_for(panel_id, False)

    def create_panels(self):
        self._panels = {}
        for panel_data in PANELS:
            # noinspection PyTypeChecker
            panel_key = panel_data['class'].__name__

            if panel_data.get('closed', False):
                checked = False
            else:
                self.create_panel(panel_data)
                checked = True
            toggle_action = self.get_action('toggle_panel')
            toggle_action.set_checked_for(panel_key, checked)

    def create_panel(self, data):
        """ Create single panel. Panels come in different classes, but we have
        a local dict panel_classes to figure out which kind of panel should
        be created.
        :param data: dict, see top of this file
        :return:
        """
        constructor = data['class']
        position = data.get('position', 'float')
        folded = data.get('folded', False)
        name = data.get('name', 'New panel')
        new_panel = constructor(name, default_position=position, parent=self.main, folded=folded)
        self._panels[constructor.__name__] = new_panel
        self.add_ui(new_panel)
        return new_panel

    def restore_panel_positions(self):
        """ Restore panel to its previous position using our own panel geometry storage """
        for name, panel in self._panels.items():
            if name in self._panel_positions:
                panel.setGeometry(self._panel_positions[name])

    def store_panel_positions(self):
        """ Store panel positions temporarily. UI manager doesn't save to
        file, if that is wanted, data has to be sent to some permanency supporting object."""
        self._panel_positions = {}
        for panel_id, panel in self._panels.items():
            self._panel_positions[panel_id] = panel.geometry()

    def reset_panel_fields(self):
        """ Update all panel elements, may be costly -- try to do specific updates instead. """
        for panel in self._panels.values():
            panel.update_fields()

    def toggle_panel(self, panel_id):
        """ Show or hide panel depending if it is visible or not
        :param panel_id: str, panel_id:s are their class names
        :return: None
        """
        panel = self.get_panel(panel_id)
        if panel and panel.isVisible():
            panel.close()
        else:
            self.show_panel(panel_id)

    # Panel scopes

    def get_scope(self, scope_id):
        action = self.get_action(scope_id)
        return action and action.getter()

    def get_active_scope(self):
        return self.active_scope

    # Action connections ###########################

    def connect_element_to_action(self, element, action, connect_slot=None):
        if isinstance(action, str):
            kataja_action = self.get_action(action)
            if not kataja_action:
                log.error(f'trying to connect non-existing action: "{action}"')
            else:
                kataja_action.connect_element(element, connect_slot=connect_slot)
        elif isinstance(action, KatajaAction):
            action.connect_element(element)

    def manage_shortcut(self, key_seq, element, action):
        """ Some shortcut become ambiguous as they are used for several
        buttons and menus at the same time and we need some extra information to solve these.
        """
        if not hasattr(element, 'setShortcut'):
            return
        action.installEventFilter(self.shortcut_solver)
        if isinstance(element, QtWidgets.QAbstractButton):
            element.installEventFilter(self.button_shortcut_filter)
            self.shortcut_solver.add_solvable_action(key_seq, element)
            # noinspection PyUnresolvedReferences
            element.destroyed.connect(self.remove_watched_shortcuts_for)
        element.setShortcut(key_seq)

    def remove_watched_shortcuts_for(self, element):
        if self.shortcut_solver:
            self.shortcut_solver.remove_solvable_action(element)

    @staticmethod
    def get_element_value(element):
        if not element:
            return []
        args = []
        if isinstance(element, TableModelSelectionBox):
            i = element.view().currentIndex()
            args.append(element.model().itemFromIndex(i).data())
        elif isinstance(element, QtWidgets.QComboBox):
            args.append((element.currentIndex(), element.itemData(element.currentIndex())))
        elif isinstance(element, QtWidgets.QCheckBox):
            args.append(element.checkState())
        elif isinstance(element, QtWidgets.QAbstractSpinBox):
            args.append(element.value())
        return args

    # Embedded dialogs, general methods
    ##########################################################

    def close_active_embed(self):
        if ctrl.text_editor_focus:
            ctrl.text_editor_focus.release_editor_focus()
        if self.active_embed:
            if self.active_embed.graphic_item:
                self.remove_ui(self.active_embed.graphic_item)
            self.remove_ui(self.active_embed)
        self.active_embed = None

    # ### Label edge editing dialog
    # #########################################################

    def start_arrow_label_editing(self, arrow):
        self.close_active_embed()
        self.active_embed = ArrowLabelEmbed(self.main.graph_view, arrow)
        self.add_ui(self.active_embed)
        self.active_embed.update_embed(focus_point=arrow.label_item.pos())
        self.active_embed.wake_up()

    def toggle_group_label_editing(self, group):
        if self.active_embed and self.active_embed.host == group:
            self.close_active_embed()
        else:
            self.start_group_label_editing(group)

    def close_group_label_editing(self, group):
        if self.active_embed and self.active_embed.host == group:
            self.close_active_embed()

    def start_group_label_editing(self, group):
        """ Start group label editing or close it if it's already active. """
        self.close_active_embed()
        self.active_embed = GroupLabelEmbed(self.main.graph_view, group)
        self.add_ui(self.active_embed)
        self.active_embed.update_embed(focus_point=group.boundingRect().center())
        self.active_embed.wake_up()

    # ### Creation dialog
    # #########################################################

    def create_creation_dialog(self, scene_pos):
        self.close_active_embed()
        self.active_embed = NewElementEmbed(self.main.graph_view)
        self.add_ui(self.active_embed, show=False)
        marker = NewElementMarker(scene_pos, self.active_embed)
        self.add_ui(marker)
        self.active_embed.marker = marker
        self.active_embed.update_embed(focus_point=scene_pos)
        marker.update_position(scene_pos=scene_pos)
        self.active_embed.wake_up()

    # ### Node editing #########################################################

    def start_editing_node(self, node, previous_embed=None):
        """
        :param node:
        :param previous_embed: UIEmbed -- if one is given, we'll try to use the old position to 
        miminimise panels jumping around.
        """
        self.close_active_embed()
        self.active_embed = node.embed_edit(self.main.graph_view, node)
        if previous_embed:
            self.active_embed.move(previous_embed.pos())
            self.active_embed.update_position()
        self.add_ui(self.active_embed, show=False)
        self.active_embed.wake_up()
        if ctrl.forest and ctrl.forest.nodes:
            for node in ctrl.forest.nodes.values():
                if node.node_type == g.CONSTITUENT_NODE and node.halo:
                    node.toggle_halo(False)

    # ### Touch areas
    # #####################################################################

    def get_touch_area(self, host, subtype):
        """ Get existing touch area for a node or other scene element.
        :param host: element that has UI items associated with it
        :param subtype: toucharea type id
        :return:
        """
        return self.get_ui_by_type(host=host, ui_type=subtype)

    def remove_touch_areas(self):
        """ Remove all touch areas from UI. Needs to be done when changing
        selection or starting dragging, or generally before touch areas are recalculated """
        for item in list(self._items.values()):
            if isinstance(item, kataja.ui_graphicsitems.TouchArea.TouchArea):
                self.remove_ui(item)

    def update_touch_areas(self):
        """ Create touch areas as necessary """
        self.remove_touch_areas()
        for item in ctrl.selected:
            if isinstance(item, Edge):
                self.update_touch_areas_for_selected_edge(item)
            elif isinstance(item, Node):
                self.update_touch_areas_for_selected_node(item)

    def update_touch_areas_for_selected_node(self, node):
        """ Assumes that touch areas for this node are empty and that the
        node is selected """
        if not node.is_visible():
            return
        ta_classes = node.__class__.touch_areas_when_selected
        for ta_class in ta_classes:
            hosts = ta_class.hosts_for_node(node)
            for host in hosts:
                if ta_class.select_condition(host):
                    ta = ta_class(host)
                    self.add_ui(ta)

    # hmmmm.....
    def update_touch_areas_for_selected_edge(self, edge):
        """ Assumes that touch areas for this edge are empty and that the
        edge is selected """
        pass

    def prepare_touch_areas_for_dragging(self, moving=None, multidrag=False):
        """ Show connection points for dragged nodes.
        :param moving: set of moving nodes (does not include drag_host)
        :param multidrag: are we dragging multiple disconnected items? (not parent and its children)
        """
        self.remove_touch_areas()
        if multidrag:
            return
        if not moving:
            moving = []
        for node in ctrl.forest.nodes.values():
            if not node.is_visible():
                continue
            if node in moving:
                continue
            if node is ctrl.dragged_focus:
                continue

            ta_classes = node.__class__.touch_areas_when_dragging
            for ta_class in ta_classes:
                hosts = ta_class.hosts_for_node(node)
                for host in hosts:
                    if ta_class.drop_condition(host):
                        ta = ta_class(host)
                        self.add_ui(ta)

    @staticmethod
    def is_dragging_this_type(dtype):
        """ Check if the currently dragged item is in principle compatible with self. """
        if ctrl.dragged_focus:
            return ctrl.dragged_focus.node_type == dtype
        elif ctrl.dragged_text:
            return ctrl.dragged_text == dtype
        return False

    # ### Flashing symbols
    # ################################################################

    def show_anchor(self, node):
        anchor = self.get_or_create_button(node, ob.LockButton)
        anchor.fade_out()

    # ### Messages
    # ####################################################################

    @staticmethod
    def add_message(msg, level=logging.INFO):
        """ Insert new row of text to log
        possible logger levels are those from logging library:
        CRITICAL	50
        ERROR	40
        WARNING	30
        INFO	20
        DEBUG	10
        NOTSET	0
        :param msg: str -- message
        :param level:
        """
        log.log(level, msg)

    # ### Embedded buttons ############################

    def create_float_buttons(self):
        """ Create top button row """
        #  for item in self._float_buttons:
        #     item.close()
        self.top_bar_buttons = TopBarButtons(ctrl.graph_view, self)
        self.top_bar_buttons.update_position()

    @staticmethod
    def add_button(button, action):
        button.update_position()
        button.show()
        return button

    def update_buttons_for_selected_node(self, node):
        """ Assumes that buttons for this node are empty and that the
        node is selected
        :param node: object to update
        """
        if not node.is_visible():
            return
        for button_class in node.__class__.buttons_when_selected:
            if button_class.condition(node):
                self.get_or_create_button(node, button_class)
        if node.resizable:
            handle = self.get_ui_by_type(node, 'GraphicsResizeHandle')
            if not handle:
                handle = GraphicsResizeHandle(ctrl.graph_view, node)
                self.add_ui(handle)
            # self.scene.addItem(handle)

    def get_or_create_button(self, host, button_class):
        button = self.get_ui_by_type(host=host, ui_type=button_class.__name__)
        if button:
            return button
        button = button_class(host=host, parent=self.main.graph_view)
        button.update_position()
        button.show()
        return button

    def add_buttons_for_group(self, group):
        """ Selection groups have a button to toggle their editing options """
        for button_class in [ob.GroupPersistenceButton, ob.GroupOptionsButton]:
            if button_class.condition(group):
                button = self.get_or_create_button(group, button_class)
                group.add_button(button)

    def add_buttons_for_arrow(self, arrow):
        """ Arrows need release button when they are connected to nodes and delete button """
        if ob.CutArrowButton.condition(arrow):
            self.get_or_create_button(arrow, ob.CutEdgeButton)
        if ob.RemoveArrowButton.condition(arrow):
            self.get_or_create_button(arrow, ob.RemoveArrowButton)

    def add_buttons_for_edge(self, edge):
        """ Constituent edges have a button to remove the edge and the node in between. """
        if ob.CutEdgeButton.condition(edge):
            self.get_or_create_button(edge, ob.CutEdgeButton)

    def add_quick_edit_buttons_for(self, node, doc):
        if not self.quick_edit_buttons:
            self.quick_edit_buttons = QuickEditButtons(parent=ctrl.graph_view, ui=self)
            self.add_ui(self.quick_edit_buttons)
        else:
            self.quick_edit_buttons.show()
        self.quick_edit_buttons.connect_to(node=node, doc=doc)
        self.quick_edit_buttons.update_position()
        self.quick_edit_buttons.update_values()

    def remove_quick_edit_buttons(self):
        self.quick_edit_buttons.hide()

    # ### Control points
    # ####################################################################

    def _add_cp(self, host, index, role):
        cp = ControlPoint(host, index=index, role=role)
        self.add_ui(cp)
        cp.update_position()

    def add_control_points(self, edge):
        """ Display control points for this edge """
        for i, point in enumerate(edge.path.control_points):
            self._add_cp(edge, i, g.CURVE_ADJUSTMENT)

    def add_control_points_for_arrow(self, arrow):

        self._add_cp(arrow, 0, g.CURVE_ADJUSTMENT)
        if not arrow.start:
            self._add_cp(arrow, -1, g.START_POINT)
        if not arrow.end:
            self._add_cp(arrow, -1, g.END_POINT)
        if arrow.label_item:
            self._add_cp(arrow, -1, g.LABEL_START)

    def update_control_points(self):
        """ Create all necessary control points """
        self.remove_control_points()
        for item in ctrl.selected:
            if isinstance(item, Edge):
                self.add_control_points(item)
            elif isinstance(item, Arrow):
                self.add_control_points_for_arrow(item)

    def remove_control_points(self):
        for item in list(self._items.values()):
            if isinstance(item, ControlPoint):
                self.remove_ui(item)

    # ### Drag info ###################################################

    def create_drag_info(self, node):
        if not self.drag_info:
            self.drag_info = DragInfo(host=node, parent=self.main.graph_view)
            self.add_ui(self.drag_info)
        else:
            self.drag_info.host = node

    def show_drag_adjustment(self):
        self.drag_info.update_value()
        self.drag_info.update_position()

    def remove_drag_info(self):
        if self.drag_info:
            self.remove_ui(self.drag_info)
            self.drag_info = None

    def show_help(self, item, event: [QtGui.QEnterEvent, QtWidgets.QGraphicsSceneHoverEvent]):
        if not (item.k_tooltip or (item.k_action and item.k_action.active_tooltip)):
            if self.floating_tip and self.floating_tip.isVisible():
                self.floating_tip.hide()
            # print('item %s is missing k_tooltip.' % item)
            return
        if not self.floating_tip:
            self.floating_tip = FloatingTip()
        self.floating_tip.set_item(item)
        if not self.floating_tip.isVisible():
            self.floating_tip.show()
        if isinstance(event, QtWidgets.QGraphicsSceneHoverEvent):
            pos = event.screenPos()
        else:
            pos = event.globalPosition().toPoint()
        self.floating_tip.set_position(pos + QtCore.QPoint(20, 20))

    def hide_help(self, item, event):
        if self.floating_tip and self.floating_tip.item is item:
            self.floating_tip.hide()

    def force_hide_help(self):
        if self.floating_tip:
            self.floating_tip.hide()

    def move_help(self, event):
        if isinstance(event, QtWidgets.QGraphicsSceneHoverEvent):
            pos = event.screenPos()
        else:
            pos = event.globalPosition().toPoint()
        if self.floating_tip:
            self.floating_tip.set_position(pos + QtCore.QPoint(20, 20))

    def refresh_heading(self):
        if not (ctrl.document and ctrl.forest):
            return
        heading = ctrl.forest.heading_text or ''
        if not self.heading:
            self.heading = HeadingWidget(ctrl.graph_view)
            self.heading.move(10, 570)
            self.heading.show()
        self.heading.set_text(heading)

    def toggle_heading(self):
        self.heading.set_folded(not self.heading.folded)

    def clear_and_refresh_heading(self):
        self.clear_items()
        self.refresh_heading()

    # Active settings ###########################

    def get_active_setting(self, key):
        if self.scope_is_selection or self.active_scope == g.FOREST:
            return ctrl.forest.settings.get(key)
        elif self.active_scope == g.DOCUMENT and ctrl.document:
            return ctrl.doc_settings.get(key)
        else:
            return prefs.get(key)

    def set_active_setting(self, key, value):
        if self.scope_is_selection or self.active_scope == g.FOREST:
            return ctrl.forest.settings.set(key, value)
        elif self.active_scope == g.DOCUMENT and ctrl.document:
            return ctrl.doc_settings.set(key, value)
        else:
            return prefs.set(key, value)

    def get_active_node_setting(self, key, node_type, skip_selection=False):
        if self.scope_is_selection:
            if not skip_selection:
                nodes = ctrl.get_selected_nodes()
                if nodes:
                    for node in nodes:
                        ns = node.get_settings()
                        if key in ns:
                            return ns[key]
                    return nodes[0].settings.get(key)
            return ctrl.forest.settings.get_for_node_type(key, node_type)
        elif self.active_scope == g.FOREST:
            return ctrl.forest.settings.get_for_node_type(key, node_type)
        elif self.active_scope == g.DOCUMENT and ctrl.document:
            return ctrl.doc_settings.get_for_node_type(key, node_type)
        else:
            return prefs.get_for_node_type(key, node_type)

    def set_active_node_setting(self, key, value, node_type):
        if self.scope_is_selection:
            nodes = ctrl.get_selected_nodes()
            if nodes:
                for node in nodes:
                    if node.node_type == node_type:
                        node.settings.set(key, value)
        elif self.active_scope == g.FOREST:
            return ctrl.forest.settings.set_for_node_type(key, value, node_type)
        elif self.active_scope == g.DOCUMENT:
            return ctrl.doc_settings.set_for_node_type(key, value, node_type)
        else:
            return prefs.set_for_node_type(key, value, node_type)

    def get_active_edge_setting(self, key, edge_type, skip_selection=False):
        if self.scope_is_selection:
            if not skip_selection:
                edges = ctrl.get_selected_edges()
                if edges:
                    for edge in edges:
                        es = edge.get_settings()
                        if key in es:
                            return es[key]
                    return edges[0].settings.get(key)
            return ctrl.forest.settings.get_for_edge_type(key, edge_type)
        elif self.active_scope == g.FOREST:
            return ctrl.forest.settings.get_for_edge_type(key, edge_type)
        elif self.active_scope == g.DOCUMENT and ctrl.document:
            return ctrl.doc_settings.get_for_edge_type(key, edge_type)
        else:
            return prefs.get_for_edge_type(key, edge_type)

    def set_active_edge_setting(self, key, value, edge_type):
        if self.scope_is_selection:
            edges = ctrl.get_selected_edges()
            if edges:
                for edge in edges:
                    if edge.edge_type == edge_type:
                        edge.settings.set(key, value)
        elif self.active_scope == g.FOREST:
            return ctrl.forest.settings.set_for_edge_type(key, value, edge_type)
        elif self.active_scope == g.DOCUMENT:
            return ctrl.doc_settings.set_for_edge_type(key, value, edge_type)
        else:
            return prefs.set_for_edge_type(key, value, edge_type)

    def set_active_edge_shape_setting(self, key, value, edge_type):
        shape_name = ctrl.ui.get_active_edge_setting('shape_name', edge_type)
        if self.scope_is_selection:
            edges = ctrl.get_selected_edges()
            if edges:
                for edge in edges:
                    if edge.edge_type == edge_type:
                        edge.path.my_shape.set(key, value)
        elif self.active_scope == g.FOREST:
            return ctrl.forest.settings.set_for_edge_shape(key, value, shape_name)
        elif self.active_scope == g.DOCUMENT:
            return ctrl.doc_settings.set_for_edge_shape(key, value, shape_name)
        else:
            return prefs.set_for_edge_shape(key, value, shape_name)


    def reset_active_edge_setting(self, edge_type):
        if self.scope_is_selection:
            edges = ctrl.get_selected_edges()
            if edges:
                for edge in edges:
                    if edge.edge_type == edge_type:
                        edge.settings.reset()
        elif self.active_scope == g.FOREST:
            return ctrl.forest.settings.reset_edge_type(edge_type)
        elif self.active_scope == g.DOCUMENT:
            return ctrl.doc_settings.reset_edge_type(edge_type)
