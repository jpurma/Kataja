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
from collections import OrderedDict
import logging

from PyQt5 import QtCore, QtWidgets

import kataja.globals as g
import kataja.actions
import kataja.ui_graphicsitems.TouchArea
import kataja.ui_widgets.OverlayButton
from kataja.KatajaAction import KatajaAction, ShortcutSolver, ButtonShortcutFilter
from kataja.saved.Edge import Edge
from kataja.saved.Group import Group
from kataja.saved.movables.Node import Node
from kataja.singletons import ctrl, prefs, qt_prefs, classes, log
from kataja.ui_graphicsitems.ActivityMarker import ActivityMarker
from kataja.ui_graphicsitems.ControlPoint import ControlPoint
from kataja.ui_graphicsitems.FadingSymbol import FadingSymbol
from kataja.ui_graphicsitems.NewElementMarker import NewElementMarker
from kataja.ui_support.MyColorDialog import MyColorDialog
from kataja.ui_support.MyFontDialog import MyFontDialog
from kataja.ui_support.TableModelSelectionBox import TableModelSelectionBox
from kataja.ui_support.TopBarButtons import TopBarButtons
from kataja.ui_widgets.QuickEditButtons import QuickEditButtons
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.embeds.EdgeLabelEmbed import EdgeLabelEmbed
from kataja.ui_widgets.embeds.GroupLabelEmbed import GroupLabelEmbed
from kataja.ui_widgets.embeds.NewElementEmbed import NewElementEmbed
from kataja.ui_widgets.embeds.NodeEditEmbed import NodeEditEmbed
from kataja.ui_widgets.panels.ColorThemePanel import ColorPanel
from kataja.ui_widgets.panels.ColorWheelPanel import ColorWheelPanel
from kataja.ui_widgets.panels.FaceCamPanel import FaceCamPanel
from kataja.ui_widgets.panels.LineOptionsPanel import LineOptionsPanel
from kataja.ui_widgets.panels.LogPanel import LogPanel
from kataja.ui_widgets.panels.NavigationPanel import NavigationPanel
from kataja.ui_widgets.panels.NodesPanel import NodesPanel
from kataja.ui_widgets.panels.StylePanel import StylePanel
from kataja.ui_widgets.panels.SymbolPanel import SymbolPanel
from kataja.ui_widgets.panels.VisualizationOptionsPanel import VisualizationOptionsPanel
from kataja.ui_widgets.panels.VisualizationPanel import VisualizationPanel
from kataja.ui_widgets.panels.LexiconPanel import LexiconPanel
from kataja.visualizations.available import VISUALIZATIONS, action_key
from kataja.ui_widgets.ResizeHandle import GraphicsResizeHandle

NOTHING = 0
SELECTING_AREA = 1
DRAGGING = 2
POINTING = 3

PANELS = [{'class': LogPanel, 'name': 'Log', 'position': 'bottom'},
          {'class': NavigationPanel, 'name': 'Trees', 'position': 'right'},
          {'class': NodesPanel, 'name': 'Nodes', 'position': 'right'},
          {'class': VisualizationPanel, 'name': 'Visualization', 'position': 'right'},
          {'class': StylePanel, 'name': 'Styles', 'position': 'right'},
          {'class': ColorPanel, 'name': 'Color theme', 'position': 'right'},
          {'class': ColorWheelPanel, 'name': 'Color theme wheel', 'position': 'right',
           'folded': True, 'closed': True},
          {'class': LineOptionsPanel, 'name': 'More line options', 'position': 'float',
           'closed': True},
          {'class': SymbolPanel, 'name': 'Symbols', 'position': 'right'},
          {'class': FaceCamPanel, 'name': 'Camera', 'position': 'float', 'closed': True},
          {'class': VisualizationOptionsPanel, 'name': 'Visualization options',
           'position': 'float', 'closed': True},
          {'class': LexiconPanel, 'name': 'Lexicon', 'position': 'float', 'closed': True}]

menu_structure = OrderedDict([('file_menu', ('&File',
                                             ['new_project', 'new_forest', 'open', 'save',
                                              'save_as', '---', 'print_pdf', 'blender_render',
                                              '---', 'preferences', '---', 'quit'])),
                              ('edit_menu', ('&Edit', ['undo', 'redo', '---', 'cut', 'copy',
                                                       'paste'])),
                              ('build_menu', ('&Build', ['next_forest', 'previous_forest',
                                                         'next_derivation_step',
                                                         'prev_derivation_step'])),
                              ('rules_menu', ('&Rules', ['bracket_mode', 'trace_mode',
                                                         'merge_order_attribute',
                                                         'select_order_attribute'])),
                              ('view_menu', ('&View', ['$visualizations', '---',
                                                       'switch_view_mode', 'change_colors',
                                                       'zoom_to_fit', '---',
                                                       'fullscreen_mode'])),
                              ('windows_menu', ('&Windows', [('Panels', ['$panels']), '---',
                                                             'toggle_all_panels', '---'])),
                              ('help_menu', ('&Help', ['help']))])


class UIManager:
    """
    UIManager Keeps track of all UI-related widgets and tries to do the most
    work to keep
    KatajaMain as simple as possible.
    """

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
        self.button_shortcut_filter = ButtonShortcutFilter()
        self.shortcut_solver = ShortcutSolver(self)
        self.active_scope = g.CONSTITUENT_NODE
        self.scope_is_selection = False
        self.default_node_type = g.CONSTITUENT_NODE
        self.active_node_type = g.CONSTITUENT_NODE
        self.active_edge_type = g.CONSTITUENT_EDGE
        self.selection_group = None
        # this is a reference dict for many ui elements adjusting edges
        self.edge_styles_in_selection = {}
        self.active_edge_style = {}
        self.active_node_style = {}
        self.preferences_dialog = None
        self.color_dialogs = {}
        self.font_dialogs = {}
        self.activity_marker = None
        self.ui_activity_marker = None

    def populate_ui_elements(self):
        """ These cannot be created in __init__, as individual panels etc.
        may refer to ctrl.ui_support,
        which doesn't exist until the __init__  is completed.
        :return:
        """
        # Create actions based on actions.py and menus based on
        additional_actions = self.create_actions()
        # Create top menus, requires actions to exist
        self.create_menus(additional_actions)
        # Create UI panels, requires actions to exist
        self.create_panels()
        self.create_float_buttons()
        ctrl.add_watcher('selection_changed', self)
        ctrl.add_watcher('forest_changed', self)
        ctrl.add_watcher('viewport_changed', self)

    def disable_item(self, ui_key):
        """ Disable ui_item, assuming it can be disabled (buttons etc).
        :param ui_key:
        :return:
        """
        item = self.get_ui(ui_key)
        item.setEnabled(False)

    def enable_item(self, ui_key):
        """ Set ui_item enabled, for those that have enabled/disabled mode (buttons etc).
        :param ui_key:
        :return:
        """
        item = self.get_ui(ui_key)
        item.setEnabled(True)

    def hide_item(self, ui_key):
        """ Hide ui_item. Doesn't remove it, so use carefully -- only for objects that are
        restored to visible at some point
        :param ui_key:
        :return:
        """
        item = self.get_ui(ui_key)
        item.hide()

    def show_item(self, ui_key):
        """ Restore ui_item to visible. Assuming one exists.
        :param ui_key:
        :return:
        """
        item = self.get_ui(ui_key)
        item.show()

    def get_action_group(self, action_group_name):
        """ Get action group with this name, or create one if it doesn't exist
        :param action_group_name:
        :return:
        """
        if action_group_name not in self._action_groups:
            self._action_groups[action_group_name] = QtWidgets.QActionGroup(self.main)
        return self._action_groups[action_group_name]

    def set_scope(self, scope):
        if scope == g.SELECTION:
            self.scope_is_selection = True
        else:
            self.scope_is_selection = False
            if scope in classes.nodes:
                self.active_node_type = scope
                node_class = classes.nodes[scope]
                self.active_edge_type = node_class.default_edge
        self.active_scope = scope
        ctrl.call_watchers(self, 'scope_changed')

    def start_color_dialog(self, receiver, parent, role, initial_color='content1'):
        """ There can be several color dialogs active at same time. Even when
        closed they are kept in the color_dialogs -dict.

        Color dialogs store their role (e.g. the field they are connected to)
         in 'role' variable. When they report color change, the role redirects
         the change to correct field.

        :param receiver:
        :param parent:
        :param role:
        :param initial_color:
        :return:
        """
        if role in self.color_dialogs:
            cd = self.color_dialogs[role]
            cd.setCurrentColor(ctrl.cm.get(initial_color))
        else:
            cd = MyColorDialog(parent, role, initial_color)
            self.color_dialogs[role] = cd
        cd.show()
        receiver.update()

    def update_color_dialog(self, role, color_id):
        if role in self.color_dialogs:
            self.color_dialogs[role].setCurrentColor(ctrl.cm.get(color_id))

    def start_font_dialog(self, parent, role, initial_font=None):
        if not initial_font:
            initial_font = role
        if role in self.font_dialogs:
            fd = self.font_dialogs[role]
            fd.setCurrentFont(qt_prefs.get_font(initial_font))
        else:
            fd = MyFontDialog(parent, initial_font)
            self.font_dialogs[role] = fd
        fd.show()

    def get_role_of_font_dialog(self, dialog):
        for key, value in self.font_dialogs.items():
            if value is dialog:
                return key

    def update_font_dialog(self, role, font_id):
        if role in self.font_dialogs:
            self.font_dialogs[role].setCurrentFont(qt_prefs.get_font(font_id))

    @staticmethod
    def set_font(font_id, font):
        qt_prefs.fonts[font_id] = font

    def add_ui(self, item, show=True):
        """

        :param item:
        :param show: by default, show it. Easy to forget otherwise.
        """
        if item.ui_key in self._items:
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
        if show:
            item.show()

    def remove_ui(self, item, fade=True):
        """ Remove ui_item from active and displayed ui_items. The item may still exist in scene
        as a fading item, but it cannot be reached by ui_manager. Such items have to take care
        that they are removed from scene when they finish fading.
        :param item:
        :param fade:
        """
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
        """ Return a managed ui_support item
        :param ui_key:
        :return:
        """
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
        """ Return ui_items that have this object as host, generally objects related to given object
        :param obj:
        :return:
        """
        return self._items_by_host.get(obj.uid, [])

    def watch_alerted(self, obj, signal, field_name, value):
        """ Receives alerts from signals that this object has chosen to
        listen. These signals
         are declared in 'self.watchlist'.

         This method will try to sort out the received signals and act
         accordingly.

        :param obj: the object causing the alarm
        :param signal: identifier for type of the alarm
        :param field_name: name of the field of the object causing the alarm
        :param value: value given to the field
        :return:
        """
        if signal == 'selection_changed':
            self.update_selections()
            self.update_actions()
        elif signal == 'forest_changed':
            self.clear_items()
            self.update_actions()
        elif signal == 'viewport_changed':
            self.update_positions()
            if self.top_bar_buttons:
                self.top_bar_buttons.update_position()

    def resize_ui(self, size):
        """

        :param size:
        """
        self.update_positions()

    def update_colors(self):
        """ Update colors in all ui_support elements that understand that demand."""
        for item in self._items.values():
            item.update_colors()

    def update_actions(self):
        # prepare style dictionaries for selections, to be used for displaying style values in UI
        self.build_active_style_info()
        for action in self.actions.values():
            action.update_action()

    def update_action(self, key):
        """ If action is tied to some meter (e.g. number field that is used to show value and
        change it), update the value in the meter and see if it should be enabled.
        :param key:
        :return:
        """
        self.actions[key].update_action()

    def build_active_style_info(self):
        """ Build dicts for representative edge styles and node styles to be displayed by ui
        :return: two dicts
        """
        es = {}
        ns = {}
        if self.scope_is_selection:
            ecount = 0
            ncount = 0
            for item in ctrl.selected:
                if isinstance(item, Edge):
                    if not ecount:
                        es = item.shape_info.copy()
                        shape_name = item.shape_name
                        es['shape_name'] = shape_name
                        es['sample_edge'] = item
                        es['arrowhead_at_start'] = item.shape_info.has_arrowhead_at_start()
                        es['arrowhead_at_end'] = item.shape_info.has_arrowhead_at_end()
                        es['curve_adjustment'] = item.curve_adjustment or [(0, 0), (0, 0)]
                        #print('selection-based edge style:', es)
                    ecount += 1
                elif isinstance(item, Node):
                    if not ncount:
                        ns = item.get_style()
                        #print('selection node style:', ns)
                    ncount += 1
            if ecount:
                es['edge_count'] = ecount
            if ncount:
                ns['node_count'] = ncount
        elif ctrl.fs:
            if self.active_edge_type:
                es = ctrl.fs.shape_info(self.active_edge_type)
                es['arrowhead_at_start'] = ctrl.fs.edge_info(self.active_edge_type,
                                                             'arrowhead_at_start')
                es['arrowhead_at_end'] = ctrl.fs.edge_info(self.active_edge_type, 'arrowhead_at_end')
                es['shape_name'] = ctrl.fs.edge_info(self.active_edge_type, 'shape_name')
                #print('fs-based edge style: ', es)
            else:
                es = {}
            if self.active_node_type:
                ns = ctrl.fs.node_style(self.active_node_type)
                #print('fs-based node style: ', ns)
        self.active_edge_style = es
        self.active_node_style = ns

    def update_selections(self):
        """ Many UI elements change mode depending on if object of specific
        type is selected. Also the logic of selection groups has to be handled somewhere. """

        def groups_in_selection(selection):
            groups = []
            # check if _one_ of the groups was selected
            for item in selection:
                if isinstance(item, Group):
                    groups.append(item)
            if len(groups) == 1:
                return groups[0]
            return None

        # why this was here?
        #if self.active_embed:
        #    self.active_embed = None

        # clear all ui_support pieces
        for item in list(self._items.values()):
            if item.host and not item.is_fading_out:
                self.remove_ui(item)

        # create ui_support pieces for selected elements. don't create touchareas and buttons
        # if multiple selection, it gets confusing fast
        if len(ctrl.selected) == 1:
            item = ctrl.selected[0]
            if isinstance(item, Edge):
                self.update_touch_areas_for_selected_edge(item)
                self.add_control_points(item)
                self.add_buttons_for_edge(item)
            elif isinstance(item, Node):
                self.update_touch_areas_for_selected_node(item)
                self.update_buttons_for_selected_node(item)
        if ctrl.selected:
            # note UI panels that they should use scope 'selection' for their activities
            self.set_scope(g.SELECTION)

            selected_group = groups_in_selection(ctrl.selected)
            if selected_group:
                if self.selection_group:
                    self.remove_selection_group()
                # select this group
                self.selection_group = selected_group
                # check if any items in this group's scope are _unselected_
                for group_member in self.selection_group.selection:
                    if group_member not in ctrl.selected:
                        self.selection_group.remove_node(group_member)
                # check if any selection contains any objects that should be added to group
                for node in ctrl.selected:
                    if isinstance(node, Node) and node.can_be_in_groups:
                        if node not in self.selection_group:
                            self.selection_group.add_node(node)
                self.add_buttons_for_group(self.selection_group)
            # draw a selection group around selected nodes
            elif ctrl.area_selection:
                # Verify that selection contains nodes that can be in group
                groupable_nodes = [item for item in ctrl.selected if
                                   isinstance(item, Node) and item.can_be_in_groups]
                if groupable_nodes:
                    # Create new group for this selection
                    if not self.selection_group:
                        self.selection_group = Group(selection=groupable_nodes, persistent=False,
                                                     forest=ctrl.forest)
                        self.selection_group.update_colors(
                                color_key=ctrl.forest.get_group_color_suggestion())
                        self.add_ui(self.selection_group)
                    # or update existing selection
                    else:
                        self.selection_group.update_selection(groupable_nodes)
                        self.selection_group.update_shape()
                    self.add_buttons_for_group(self.selection_group)
                elif self.selection_group:
                    # Selection had only items that don't fit inside group, there is one already
                    self.remove_selection_group()
            elif self.selection_group:
                # Selection was empty, but there is existing selection group visible
                self.remove_selection_group()
        else:
            if self.scope_is_selection:
                self.scope_is_selection = False
                ctrl.call_watchers(self, 'scope_changed')
            if self.selection_group:
                self.remove_selection_group()

    def remove_selection_group(self):
        self.remove_ui_for(self.selection_group)
        if not self.selection_group.persistent:
            self.remove_ui(self.selection_group)
        self.selection_group = None

    # unused, but sane
    def focusable_elements(self):
        """ Return those UI elements that are flagged focusable (Kataja's
        focusable, not Qt's).
        """
        for e in self._items:
            if getattr(e, 'focusable', False) and e.isVisible():
                yield e

    def clear_items(self):
        """ Remove all ui_support objects managed by UIManager.
        """
        ctrl.deselect_objects()
        for item in list(self._items.values()):
            if not item.permanent_ui:
                self.remove_ui(item)

    def update_positions(self):
        """ UI has elements that point to graph scene elements, and when
        something moves there
        UI has to update its elements too."""
        for item in self._items.values():
            item.update_position()

    def update_position_for(self, obj):
        """ Update position of ui_support-elements for selected (non-ui_support) object.
        :param obj:
        :return:
        """
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

    def create_actions(self):
        """ Build menus and other actions that can be triggered by user based
        on actions/ """
        main = self.main
        a_class_type = type(KatajaAction)
        self.actions = {}
        self._action_groups = {}
        for class_name in vars(kataja.actions):
            a_class = getattr(kataja.actions, class_name)
            if type(a_class) != a_class_type or not issubclass(a_class, KatajaAction):
                continue
            if a_class.k_dynamic:
                continue
            action = a_class()
            self.actions[action.key] = action
            main.addAction(action)

        # dynamic actions are created based on other data e.g. available
        # visualization plugins.
        # they are added into actions as everyone else, but there is a
        # special mapping to find
        # them later.
        # eg. additional_actions['visualizations'] = ['vis_1','vis_2',
        # 'vis_3'...]
        vis_actions = []
        for name, vis in VISUALIZATIONS.items():
            key = action_key(name)
            action = kataja.actions.ChangeVisualisation(action_uid=key, command=name, args=[name],
                                                        shortcut=vis.shortcut)
            self.actions[key] = action
            vis_actions.append(key)

        panel_actions = []
        for panel_data in PANELS:
            # noinspection PyTypeChecker
            panel_key = panel_data['class'].__name__
            key = 'toggle_panel_%s' % panel_key
            # noinspection PyTypeChecker
            action = kataja.actions.TogglePanel(action_uid=key,
                                                command=panel_data['name'],
                                                args=[panel_key])
            self.actions[key] = action
            panel_actions.append(key)

        log.info('Prepared %s actions.' % len(self.actions))
        return {'visualizations': vis_actions, 'panels': panel_actions}

    def get_action(self, key) -> KatajaAction:
        """ Returns action method for key, None if no such action
        :param key:
        :return: Action
        """
        if key:
            a = self.actions.get(key, None)
            if a:
                return a
            print('missing action ', key)

    def create_menus(self, additional_actions):
        """ Put actions to menus. Menu structure is defined at the top of this file.
        :param additional_actions: dict where each key returns a list of action schemas. This way
        programmatically generated actions and those coming from e.g. plugins can be added to
        menus.
        :return: None
        """

        def add_menu(parent, menu_label, menu_items):
            """
            :param parent:
            :param menu_label:
            :param menu_items:
            :return:
            """
            new_menu = QtWidgets.QMenu(menu_label, self.main)
            for item in menu_items:
                if isinstance(item, tuple):
                    add_menu(new_menu, item[0], item[1])
                elif item == '---':
                    new_menu.addSeparator()
                else:
                    new_menu.addAction(self.actions[item])

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
                    exp_items += additional_actions[item[1:]]
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

    def update_projects_menu(self, projects, current_project):

        win_menu = self._top_menus['windows_menu']
        last_separator = 0
        for i, item in enumerate(win_menu.actions()):
            if item.isSeparator():
                last_separator = i
        for action in win_menu.actions()[last_separator+1:]:
            del self.actions[action.key]
            win_menu.removeAction(action)
        for i, project in enumerate(projects):
            key = 'project_%s' % project.name
            action = kataja.actions.SwitchProject(action_uid=key,
                                                  command=project.name,
                                                  args=[i])
            self.actions[key] = action
            action.setChecked(project is current_project)
            win_menu.addAction(action)

    # ###################################################################
    #                           PANELS
    # ###################################################################

    def get_panel(self, panel_id) -> Panel:
        """
        :param panel_id: panel key. Probably from constant from globals
        :return: UIPanel instance or None
        """
        return self._panels.get(panel_id, None)

    def redraw_panels(self):
        for panel in self._panels.values():
            panel.update()

    def create_panels(self):
        """ Put actions to panels. Panel contents are defined at the top of
        this file.
        :return: None
        """
        self._panels = {}
        for panel_data in PANELS:
            # noinspection PyTypeChecker
            panel_key = panel_data['class'].__name__

            if panel_data.get('closed', False):
                checked = False
            else:
                self.create_panel(panel_data)
                checked = True
            toggle_action = self.get_action('toggle_panel_%s' % panel_key)
            toggle_action.setChecked(checked)

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
        new_panel = constructor(name, default_position=position, parent=self.main,
                                folded=folded)
        self._panels[constructor.__name__] = new_panel
        self.add_ui(new_panel)
        return new_panel

    def restore_panel_positions(self):
        """ Restore panel to its previous position using our own panel geometry
        storage
        """
        for name, panel in self._panels.items():
            if name in self._panel_positions:
                panel.setGeometry(self._panel_positions[name])

    def store_panel_positions(self):
        """ Store panel positions temporarily. UI manager doesn't save to
        file, if that is
        wanted, data has to be sent to some permanency supporting object.
        """
        self._panel_positions = {}
        for panel_id, panel in self._panels.items():
            self._panel_positions[panel_id] = panel.geometry()

    def reset_panel_fields(self):
        """ Update all panel elements, may be costly -- try to do specific
        updates instead.
        :return:
        """
        for panel in self._panels.values():
            panel.update_fields()

    def toggle_panel(self, toggle_action, panel_id):
        """ Show or hide panel depending if it is visible or not
        :param toggle_action:
        :param panel_id: enum of panel identifiers (str)
        :return: None
        """
        panel = self.get_panel(panel_id)

        if panel:
            if panel.isVisible():
                panel.close()
                toggle_action.setChecked(False)
            else:
                panel.setVisible(True)
                panel.set_folded(False)
                toggle_action.setChecked(True)
        else:
            panel_data = None
            for panel_data in PANELS:
                # noinspection PyTypeChecker
                if panel_data['class'].__name__ == panel_id:
                    break
            if panel_data:
                # noinspection PyTypeChecker
                panel = self.create_panel(panel_data)
                panel.setVisible(True)
                panel.set_folded(False)
                toggle_action.setChecked(True)

    # Action connections ###########################

    def connect_element_to_action(self, element, action, tooltip_suffix=''):
        """

        :param element:
        :param action:
        :param tooltip_suffix:
        """
        if isinstance(action, str):
            action = self.get_action(action)
        assert action
        action.connect_element(element, tooltip_suffix)

    def manage_shortcut(self, key_seq, element, action):
        """ Some shortcut become ambiguous as they are used for several
        buttons and menus at
        the same time and we need some extra information to solve these.

        :param key_seq:
        :param element:
        :param action:
        :return:
        """
        if not hasattr(element, 'setShortcut'):
            log.critical('trying to put shortcut for element that doesnt support it: %s %s ' % (
                element, action))
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
        """

        :param element:
        :return:
        """
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

    def start_edge_label_editing(self, edge):
        """

        :param edge:
        """
        self.close_active_embed()
        self.active_embed = EdgeLabelEmbed(self.main.graph_view, edge)
        self.add_ui(self.active_embed)
        self.active_embed.update_embed(focus_point=edge.label_item.pos())
        self.active_embed.wake_up()

    def toggle_group_label_editing(self, group):
        """ Start group label editing or close it if it's already active.
        :param group:
        :return:
        """
        if self.active_embed and self.active_embed.host == group:
            self.close_active_embed()
        else:
            self.start_group_label_editing(group)

    def close_group_label_editing(self, group):
        if self.active_embed and self.active_embed.host == group:
            self.close_active_embed()

    def start_group_label_editing(self, group):
        """ Start group label editing or close it if it's already active.
        :param group:
        :return:
        """
        self.close_active_embed()
        self.active_embed = GroupLabelEmbed(self.main.graph_view, group)
        self.add_ui(self.active_embed)
        self.active_embed.update_embed(focus_point=group.boundingRect().center())
        self.active_embed.wake_up()

    # ### Creation dialog
    # #########################################################

    def create_creation_dialog(self, scene_pos):
        """

        :param scene_pos:
        """
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

    def start_editing_node(self, node):
        """
        :param node:
        """
        self.close_active_embed()
        self.active_embed = NodeEditEmbed(self.main.graph_view, node)
        self.add_ui(self.active_embed, show=False)
        self.active_embed.wake_up()

    # ### Touch areas
    # #####################################################################

    def get_or_create_touch_area(self, host, subtype, action=None):
        """ Get touch area for specific purpose or create one if it doesn't exist.
        :param host: element that has UI items associated with it
        :param subtype: toucharea type id
        :param action: action to associate with toucharea if one is created
        :return:
        """
        ta = self.get_ui_by_type(host=host, ui_type=subtype)
        if not ta:
            ta = self.create_touch_area(host, subtype, action)
        return ta

    def get_touch_area(self, host, subtype):
        """ Get existing touch area for a node or other scene element.
        :param host: element that has UI items associated with it
        :param subtype: toucharea type id
        :return:
        """
        return self.get_ui_by_type(host=host, ui_type=subtype)

    def create_touch_area(self, host, subtype, action):
        """ Create touch area, doesn't check if it exists already.
        :param host: element that has UI items associated with it
        :param subtype: toucharea type id
        :param action: action to associate with toucharea
        :return:
        """
        ta_class = getattr(kataja.ui_graphicsitems.TouchArea, subtype)
        ta = ta_class(host, action)
        self.add_ui(ta)
        return ta

    def remove_touch_areas(self):
        """ Remove all touch areas from UI. Needs to be done when changing
        selection or starting dragging, or generally before touch areas are recalculated """
        for item in list(self._items.values()):
            if isinstance(item, kataja.ui_graphicsitems.TouchArea.TouchArea):
                self.remove_ui(item)

    def update_touch_areas(self):
        """ Create touch areas as necessary
        """
        self.remove_touch_areas()
        for item in ctrl.selected:
            if isinstance(item, Edge):
                self.update_touch_areas_for_selected_edge(item)
            elif isinstance(item, Node):
                self.update_touch_areas_for_selected_node(item)

    def update_touch_areas_for_selected_node(self, node):
        """ Assumes that touch areas for this node are empty and that the
        node is selected
        :param node: object to update
        """
        if not node.is_visible():
            return
        d = node.__class__.touch_areas_when_selected
        for ta_type, values in d.items():
            if node.check_conditions(values):
                action = self.get_action(values.get('action'))
                place = values.get('place', '')
                if place == 'edge_up':
                    hosts = node.get_edges_up(similar=True, visible=True)
                elif place == 'parent_above':
                    hosts = node.get_parents(similar=True, visible=True)
                else:
                    hosts = [node]
                for host in hosts:
                    self.get_or_create_touch_area(host, ta_type, action)

    # hmmmm.....
    def update_touch_areas_for_selected_edge(self, edge):
        """ Assumes that touch areas for this edge are empty and that the
        edge is selected
        :param edge: object to update
        """
        if ctrl.free_drawing_mode and edge.edge_type == g.CONSTITUENT_EDGE:
            self.get_or_create_touch_area(edge, g.INNER_ADD_SIBLING_LEFT,
                                          self.get_action('inner_add_sibling_left'))
            self.get_or_create_touch_area(edge, g.INNER_ADD_SIBLING_RIGHT,
                                          self.get_action('inner_add_sibling_right'))

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
            d = node.__class__.touch_areas_when_dragging
            for ta_type, values in d.items():
                if node.check_conditions(values):
                    action = self.get_action(values.get('action'))
                    place = values.get('place', '')
                    if place == 'edge_up':
                        for edge in node.get_edges_up(similar=True, visible=True):
                            self.get_or_create_touch_area(edge, ta_type, action)
                    elif not place:
                        self.get_or_create_touch_area(node, ta_type, action)
                    else:
                        raise NotImplementedError

    # ### Flashing symbols
    # ################################################################

    def show_anchor(self, node):
        """

        :param node:
        """
        # assert (node.locked or node.use_adjustment)
        anchor = self.get_ui_by_type(node, 'FadingSymbol')
        if not anchor:
            anchor = FadingSymbol(qt_prefs.lock_pixmap, node, place='bottom_right')
            # print u"\U0001F512" , unichr(9875) # unichr(9875)
            self.add_ui(anchor)
            anchor.fade_out()


    # ### Messages
    # ####################################################################

    def add_message(self, msg, level=logging.INFO):
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

    # Mode HUD
    def update_edit_mode(self):
        val = ctrl.free_drawing_mode
        self.top_bar_buttons.edit_mode_button.setChecked(not val)
        ctrl.call_watchers(self, 'edit_mode_changed', value=val)

    # ### Embedded buttons ############################

    def create_float_buttons(self):
        """ Create top button row
        :return:
        """
        #  for item in self._float_buttons:
        #     item.close()
        self.top_bar_buttons = TopBarButtons(ctrl.graph_view, self)
        self.top_bar_buttons.update_position()
        self.update_edit_mode()
        self.update_drag_mode(True) # selection mode

    def update_drag_mode(self, selection_mode):
        pan_around = self.get_ui('pan_mode')
        select_mode = self.get_ui('select_mode')
        if selection_mode:
            pan_around.setChecked(False)
            select_mode.setChecked(True)
        else:
            pan_around.setChecked(True)
            select_mode.setChecked(False)

    def add_button(self, button, action):
        if button.ui_key not in self._items:
            self.add_ui(button)
            button.update_position()
            self.connect_element_to_action(button, action)
            button.show()
        return button

    def update_buttons_for_selected_node(self, node):
        """ Assumes that buttons for this node are empty and that the
        node is selected
        :param node: object to update
        """
        if not node.is_visible():
            return
        d = node.__class__.buttons_when_selected
        for key, values in d.items():
            if node.check_conditions(values):
                action = values.get('action', '')
                self.get_or_create_button(node, key, action)
        if node.resizable:
            handle = self.get_ui_by_type(node, 'GraphicsResizeHandle')
            if not handle:
                handle = GraphicsResizeHandle(ctrl.graph_view, node)
                self.add_ui(handle)
            # self.scene.addItem(handle)

    def get_or_create_button(self, node, class_key, action):
        button = self.get_ui_by_type(host=node, ui_type=class_key)
        if button:
            return button
        constructor = getattr(kataja.ui_widgets.OverlayButton, class_key)
        button = constructor(node, self.main.graph_view)

        self.add_ui(button)
        button.update_position()
        if action:
            self.connect_element_to_action(button, action)
        else:
            print('missing action for button ', button, class_key)
        button.show()
        return button

    def add_buttons_for_group(self, group):
        """ Selection groups have a button to toggle their editing options
        :param group:
        :return:
        """
        button = self.get_or_create_button(group, g.GROUP_OPTIONS, 'toggle_group_options')
        return button

    def add_buttons_for_edge(self, edge):
        """ Constituent edges have a button to remove the edge and the node
        in between.
        :param edge:
        """
        # Constituent edges don't have cut-button at the start
        # if edge.edge_type is not g.CONSTITUENT_EDGE:
        if edge.start:
            self.get_or_create_button(edge, g.CUT_FROM_START_BUTTON, 'disconnect_edge_start')
        if edge.end:
            self.get_or_create_button(edge, g.CUT_FROM_END_BUTTON, 'disconnect_edge_end')

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

    def add_control_points(self, edge):
        """ Display control points for this edge
        :param edge:
        """

        def _add_cp(index, role):
            cp = ControlPoint(edge, index=index, role=role)
            self.add_ui(cp)
            cp.update_position()

        for i, point in enumerate(edge.control_points):
            _add_cp(i, g.CURVE_ADJUSTMENT)
        if not edge.start:
            _add_cp(-1, g.START_POINT)
        if not edge.end:
            _add_cp(-1, g.END_POINT)
        if edge.label_item:
            _add_cp(-1, g.LABEL_START)

    def update_control_points(self):
        """ Create all necessary control points
        :return:
        """
        self.remove_control_points()
        for item in ctrl.selected:
            if isinstance(item, Edge):
                self.add_control_points(item)

    def remove_control_points(self):
        """ Remove all control points
        :return:
        """
        for item in list(self._items.values()):
            if isinstance(item, ControlPoint):
                self.remove_ui(item)

    # ### Activity marker ##############################################

    def get_activity_marker(self):
        """

        :return:
        """
        if not self.activity_marker:
            self.activity_marker = ActivityMarker(role=0)
        return self.activity_marker

    def get_ui_activity_marker(self):
        """

        :return:
        """
        if not self.ui_activity_marker:
            self.ui_activity_marker = ActivityMarker(role=0)
        return self.ui_activity_marker

    # ### Timer for moving UI items ########################################################
    # This is currently unused, there are no spontaneously moving UI elements that require this
    # kind of timer. To reactivate this, this should reside in some QObject. UIManager is plain
    # python object.

    # def item_moved(self):
    #     """ Wake up timer if it is not running """
    #     assert(False)
    #     if not self._timer_id:
    #         self._timer_id = self.startTimer(prefs._fps_in_msec)
    #         #print('ui_support timer id ', self._timer_id)
    #
    # def timerEvent(self, event):
    #     """ Called by Qt on timer tick
    #     :param event: timer event, could be used to inspect how far it is
    #     """
    #     items_have_moved = False
    #     for item in self.moving_things:
    #         if item.move_towards_target_position():
    #             items_have_moved = True
    #     if items_have_moved:
    #         self.get_ui_activity_marker().show()
    #     if not items_have_moved:
    #         self.get_ui_activity_marker().hide()
    #         self.killTimer(self._timer_id)
    #         self._timer_id = 0
