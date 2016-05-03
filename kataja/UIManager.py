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

from PyQt5 import QtCore, QtWidgets

from kataja.UIItem import UIItem
from kataja.ui_support.MyFontDialog import MyFontDialog
from kataja.ui_support.ResizeHandle import GraphicsResizeHandle
from kataja.ui_support.TableModelComboBox import TableModelComboBox
from kataja.ui_support.TopBarButtons import TopBarButtons
from kataja.ui_items.panels.ColorThemePanel import ColorPanel
from kataja.ui_items.panels.ColorWheelPanel import ColorWheelPanel
from kataja.ui_items.panels.FaceCamPanel import FaceCamPanel
from kataja.ui_items.panels.LineOptionsPanel import LineOptionsPanel
from kataja.ui_items.panels.LogPanel import LogPanel
from kataja.ui_items.panels.NavigationPanel import NavigationPanel
from kataja.ui_items.panels.NodesPanel import NodesPanel
from kataja.ui_items.panels.StylePanel import StylePanel
from kataja.ui_items.panels.VisualizationOptionsPanel import VisualizationOptionsPanel
from kataja.ui_items.panels.VisualizationPanel import VisualizationPanel

import kataja.globals as g
from kataja.Action import Action, ShortcutSolver, ButtonShortcutFilter
from kataja.actions import actions_dict
from kataja.actions.file import switch_project
from kataja.actions.view import change_visualization
from kataja.actions.window import toggle_panel
from kataja.singletons import ctrl, prefs, qt_prefs, classes
from kataja.ui_support import drawn_icons
from kataja.ui_support.MessageWriter import MessageWriter
from kataja.visualizations.available import VISUALIZATIONS, action_key
from kataja.saved.Group import Group
from kataja.saved.Edge import Edge
from kataja.saved.movables.Node import Node
from kataja.ui_items.Panel import Panel
from kataja.ui_items.ActivityMarker import ActivityMarker
from kataja.ui_items.ControlPoint import ControlPoint
from kataja.ui_items.FadingSymbol import FadingSymbol
from kataja.ui_items.OverlayButton import OverlayButton, button_factory, TopRowButton, \
    CutFromEndButton, CutFromStartButton
from kataja.ui_items.StretchLine import StretchLine
from kataja.ui_items.TouchArea import TouchArea, create_touch_area
from kataja.ui_items.embeds.EdgeLabelEmbed import EdgeLabelEmbed
from kataja.ui_items.embeds.GroupLabelEmbed import GroupLabelEmbed
from kataja.ui_items.embeds.NewElementEmbed import NewElementEmbed
from kataja.ui_items.NewElementMarker import NewElementMarker
from kataja.ui_items.embeds.NodeEditEmbed import NodeEditEmbed
from kataja.ui_items.panels.SymbolPanel import SymbolPanel
from kataja.ui_support.MyColorDialog import MyColorDialog
from kataja.ui_items.ModeLabel import ModeLabel

NOTHING = 0
SELECTING_AREA = 1
DRAGGING = 2
POINTING = 3

PANELS = OrderedDict([(g.LOG, {'name': 'Log', 'position': 'bottom'}),
                      (g.NAVIGATION, {'name': 'Trees', 'position': 'right'}),
                      (g.NODES, {'name': 'Nodes', 'position': 'right'}),
                      (g.VISUALIZATION, {'name': 'Visualization', 'position': 'right'}),
                      (g.STYLE, {'name': 'Styles', 'position': 'right'}),
                      (g.COLOR_THEME, {'name': 'Color theme', 'position': 'right'}),
                      (g.COLOR_WHEEL, {'name': 'Color theme wheel', 'position': 'right',
                                       'folded': True, 'closed': True}),
                      (g.LINE_OPTIONS, {'name': 'More line options', 'position': 'float',
                                        'closed': True}),
                      (g.SYMBOLS, {'name': 'Symbols', 'position': 'right'}),
                      (g.CAMERA, {'name': 'Camera', 'position': 'float', 'closed': True}),
                      (g.VIS_OPTIONS, {'name': 'Visualization options', 'position': 'float',
                                       'closed': True})])


panel_classes = {g.LOG: LogPanel, g.NAVIGATION: NavigationPanel,
                 g.VISUALIZATION: VisualizationPanel, g.COLOR_THEME: ColorPanel,
                 g.COLOR_WHEEL: ColorWheelPanel, g.LINE_OPTIONS: LineOptionsPanel,
                 g.SYMBOLS: SymbolPanel, g.NODES: NodesPanel, g.STYLE: StylePanel,
                 g.CAMERA: FaceCamPanel,
                 g.VIS_OPTIONS: VisualizationOptionsPanel}

menu_structure = OrderedDict([('file_menu', ('&File',
                                             ['new_project', 'new_forest', 'open', 'save',
                                              'save_as', '---', 'print_pdf', 'blender_render',
                                              '---', 'preferences', '---', 'quit'])),
                              ('edit_menu', ('&Edit', ['undo', 'redo'])),
                              ('build_menu', ('&Build', ['next_forest', 'prev_forest',
                                                         'next_derivation_step',
                                                         'prev_derivation_step'])),
                              ('rules_menu', ('&Rules', ['bracket_mode', 'trace_mode',
                                                         'merge_order_attribute',
                                                         'select_order_attribute'])),
                              ('view_menu', ('&View', ['$visualizations', '---',
                                                       'toggle_bones_mode', 'change_colors',
                                                       'adjust_colors', 'zoom_to_fit', '---',
                                                       'fullscreen_mode'])),
                              ('windows_menu', ('&Windows', [('Panels', ['$panels']), '---',
                                                             'toggle_all_panels', '---'])),
                              ('help_menu', ('&Help', ['help']))])

NEW_ELEMENT_EMBED = 'new_element_embed'
NEW_ELEMENT_MARKER = 'new_element_marker'
EDGE_LABEL_EMBED = 'edge_label_embed'
GROUP_LABEL_EMBED = 'group_label_embed'
STRETCHLINE = 'stretchline'
ACTIVITY_MARKER = 'activity_marker'
UI_ACTIVITY_MARKER = 'ui_activity_marker'


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
        self.qt_actions = {}
        self._top_menus = {}
        self.top_bar_buttons = None
        self._edit_mode_button = None

        self._items = {}
        self._items_by_host = {}
        self._node_edits = set()
        self.log_writer = MessageWriter()

        self._timer_id = 0
        self._panels = {}
        self._panel_positions = {}
        self.moving_things = set()
        self.button_shortcut_filter = ButtonShortcutFilter()
        self.shortcut_solver = ShortcutSolver(self)

        self.scope_is_selection = False
        self.default_node_type = g.CONSTITUENT_NODE
        self.active_node_type = g.CONSTITUENT_NODE
        self.active_edge_type = g.CONSTITUENT_EDGE
        self.selection_group = None

        self.preferences_dialog = None
        self.color_dialogs = {}
        self.font_dialogs = {}

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
                self.active_edge_type = node_class.default_edge['id']
        ctrl.call_watchers(self, 'scope_changed')


    def start_color_dialog(self, receiver, parent, role, initial_color='content1'):
        """ There can be several color dialogs active at same time. Even when
        closed they are kept in the color_dialogs -dict.

        Color dialogs store their role (e.g. the field they are connected to)
         in 'role' variable. When they report color change, the role redirects
         the change to correct field.

        :param receiver:
        :param parent:
        :param slot_name:
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
            initial_font = g.MAIN_FONT
        if role in self.font_dialogs:
            fd = self.font_dialogs[role]
            fd.setCurrentFont(qt_prefs.font(initial_font))
        else:
            fd = MyFontDialog(parent, initial_font)
            self.font_dialogs[role] = fd
        fd.show()

    def update_font_dialog(self, role, font_id):
        if role in self.font_dialogs:
            self.font_dialogs[role].setCurrentFont(qt_prefs.font(font_id))

    def create_or_set_font(self, font_id, font):
        if not font_id.startswith('custom'):
            font_id = qt_prefs.get_key_for_font(font)
        qt_prefs.fonts[font_id] = font
        return font_id

    def add_ui(self, item, show=True):
        """

        :param item:
        :param show: by default, show it. Easy to forget otherwise.
        """
        if item.ui_key in self._items:
            raise KeyError
        self._items[item.ui_key] = item
        if item.host:
            key = item.host.save_key
            if key in self._items_by_host:
                self._items_by_host[key].append(item)
            else:
                self._items_by_host[key] = [item]
        if isinstance(item, QtWidgets.QGraphicsItem):
            self.scene.addItem(item)
        if show:
            item.show()

    def remove_ui(self, item):
        """

        :param item:
        """
        if item.ui_key in self._items:
            del self._items[item.ui_key]
        if item.host:
            key = item.host.save_key
            if key in self._items_by_host:
                parts = self._items_by_host.get(item, [])
                if item in parts:
                    parts.remove(item)
                    if not parts:
                        del self._items_by_host[key]
        item.hide()
        if isinstance(item, QtWidgets.QGraphicsItem):
            self.scene.removeItem(item)
        elif isinstance(item, QtWidgets.QWidget):
            self.remove_watched_shortcuts_for(item)
            item.close()

    def get_ui(self, ui_key) -> QtCore.QObject:
        """ Return a managed ui_support item
        :param ui_key:
        :return:
        """
        return self._items.get(ui_key, None)

    def get_uis_for(self, obj):
        """ Return ui_items that have this object as host, generally objects related to given object
        :param obj:
        :return:
        """
        return self._items_by_host.get(obj.save_key, [])

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
        elif signal == 'forest_changed':
            self.clear_items()
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

        # clear all ui_support pieces
        for item in list(self._items.values()):
            if item.host and not getattr(item, '_fade_out_active', False):
                self.remove_ui(item)
        # create ui_support pieces for selected elements. don't create touchareas and buttons if multiple
        # selection, it gets confusing fast
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
                        self.selection_group = Group(groupable_nodes, persistent=False)
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
        :param obj: Saved item, needs to have save_key
        """
        for ui_item in list(self.get_uis_for(obj)):
            if not getattr(ui_item, '_fade_out_active', False):
                ui_item.update_position()

    # ### Actions and Menus
    # ####################################################

    def create_actions(self):
        """ Build menus and other actions that can be triggered by user based
        on actions/ """

        main = self.main

        # dynamic actions are created based on other data e.g. available
        # visualization plugins.
        # they are added into actions as everyone else, but there is a
        # special mapping to find
        # them later.
        # eg. additional_actions['visualizations'] = ['vis_1','vis_2',
        # 'vis_3'...]
        additional_actions = {}
        self.actions = actions_dict

        additional_actions['visualizations'] = []
        for name, vis in VISUALIZATIONS.items():
            key = action_key(name)
            d = {'command': name, 'method': change_visualization,
                 'shortcut': vis.shortcut, 'checkable': True, 'sender_arg': True, 'args': [name],
                 'viewgroup': 'visualizations', 'exclusive': True}
            self.actions[key] = d
            additional_actions['visualizations'].append(key)

        additional_actions['panels'] = []
        for panel_key, panel_data in PANELS.items():
            key = 'toggle_panel_%s' % panel_key
            d = {'command': panel_data['name'], 'method': toggle_panel,
                 'checkable': True, 'viewgroup': 'Panels', 'args': [panel_key], 'action_arg': True,
                 'undoable': False, 'exclusive': False, 'tooltip': "Close this panel"}
            self.actions[key] = d
            additional_actions['panels'].append(key)
        # ## Create actions
        self._action_groups = {}
        self.qt_actions = {}

        for key, data in self.actions.items():
            action = Action(key, **data)
            self.qt_actions[key] = action
            main.addAction(action)
        return additional_actions

    def get_action(self, key):
        """ Returns action method for key, None if no such action
        :param key:
        :return: KatajaAction
        """
        if key:
            a = self.qt_actions.get(key, None)
            if a:
                return a
            print('missing action ', key)
        return None

    def create_menus(self, additional_actions):
        """ Put actions to menus. Menu structure is defined at the top of
        this file.
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
                    new_menu.addAction(self.qt_actions[item])
                    #if item in self.actions:
                    #    getter = self.actions[item].get('check_state', None)
                    #    if getter:
                    #        self.qt_actions[item].setChecked(getter())


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
        d = {'command': '', 'method': switch_project,
             'checkable': True, 'args': [],
             'exclusive': True, 'undoable': False}

        win_menu = self._top_menus['windows_menu']
        last_separator = 0
        for i, item in enumerate(win_menu.actions()):
            if item.isSeparator():
                last_separator = i
        for action in win_menu.actions()[last_separator+1:]:
            del self.qt_actions[action.key]
            del self.actions[action.key]
            win_menu.removeAction(action)
        for i, project in enumerate(projects):
            e = d.copy()
            e['command'] = project.name
            e['args'] = [i]
            key = 'project_%s' % project.name
            self.actions[key] = e
            action = Action(key, **e)
            action.setChecked(project is current_project)
            self.qt_actions[key] = action
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
        for panel_key, data in PANELS.items():
            if data.get('closed', False):
                checked = False
            else:
                self.create_panel(panel_key, **data)
                checked = True
            toggle_action = self.get_action('toggle_panel_%s' % panel_key)
            toggle_action.setChecked(checked)

    def create_panel(self, id, name='', position=None, folded=False, default=False, **kwargs):
        """ Create single panel. Panels come in different classes, but we have
        a local dict panel_classes to figure out which kind of panel should
        be created.
        :param id: globals provides some constants for panel ids
        :param name:
        :param position:
        :param folded:
        :param default: bool -- use the PANELS settings
        :return:
        """
        if default:
            data = PANELS[id]
            position = data.get('position', None)
            folded = data.get('folded', False)
            name = data.get('name', '')
        constructor = panel_classes[id]
        new_panel = constructor(name, id, default_position=position, parent=self.main,
                                folded=folded)
        self._panels[id] = new_panel
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

    def toggle_panel(self, action, panel_id):
        """ Show or hide panel depending if it is visible or not
        :param panel_id: enum of panel identifiers (str)
        :return: None
        """
        panel = self.get_panel(panel_id)

        if panel:
            if panel.isVisible():
                panel.close()
                action.setChecked(False)
            else:
                panel.setVisible(True)
                panel.set_folded(False)
                action.setChecked(True)
        else:
            panel = self.create_panel(panel_id, default=True)
            panel.setVisible(True)
            panel.set_folded(False)
            action.setChecked(True)

    # Action connections ###########################

    def connect_element_to_action(self, element, action, tooltip_suffix=''):
        """

        :param element:
        :param action:
        :param tooltip_suffix:
        """
        if isinstance(action, str):
            action = self.get_action(action)
        if not action:
            print('missing action: ', action)
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
        action.installEventFilter(self.shortcut_solver)
        if isinstance(element, QtWidgets.QAbstractButton):
            element.installEventFilter(self.button_shortcut_filter)
            self.shortcut_solver.add_solvable_action(key_seq, element)
            element.destroyed.connect(self.remove_watched_shortcuts_for)
        element.setShortcut(key_seq)

    def remove_watched_shortcuts_for(self, element):
        if self.shortcut_solver:
            self.shortcut_solver.remove_solvable_action(element)

    def get_element_value(self, element):
        """

        :param element:
        :return:
        """
        if not element:
            return []
        args = []
        if isinstance(element, TableModelComboBox):
            i = element.view().currentIndex()
            args.append(element.model().itemFromIndex(i).data())
        elif isinstance(element, QtWidgets.QComboBox):
            args.append((element.currentIndex(), element.itemData(element.currentIndex())))
        elif isinstance(element, QtWidgets.QCheckBox):
            args.append(element.checkState())
        elif isinstance(element, QtWidgets.QAbstractSpinBox):
            args.append(element.value())
        return args

    def get_selector_value(self, selector):
        """

        :param selector:
        :return:
        """
        i = selector.currentIndex()
        return selector.itemData(i)

    # Embedded dialogs, general methods
    ##########################################################

    def release_editor_focus(self):
        """ Make sure that quick editing is turned off before opening new editors
        :return:
        """
        if ctrl.text_editor_focus:
            ctrl.text_editor_focus.release_editor_focus()

    # ### Label edge editing dialog
    # #########################################################

    def start_edge_label_editing(self, edge):
        """

        :param edge:
        """
        self.release_editor_focus()
        lp = edge.label_item.pos()
        if EDGE_LABEL_EMBED not in self._items:
            embed = EdgeLabelEmbed(self.main.graph_view, edge, EDGE_LABEL_EMBED)
            self.add_ui(embed)
        else:
            embed = self._items[EDGE_LABEL_EMBED]
        embed.update_embed(focus_point=lp)
        embed.wake_up()

    def toggle_group_label_editing(self, group):
        """ Start group label editing or close it if it's already active.
        :param group:
        :return:
        """
        self.release_editor_focus()
        lp = group.boundingRect().center()
        if GROUP_LABEL_EMBED in self._items:
            embed = self._items[GROUP_LABEL_EMBED]
            if embed.host is group:
                embed.close()
                self.remove_ui(embed)
                return
            else:
                embed.host = group
        else:
            embed = GroupLabelEmbed(self.main.graph_view, group, GROUP_LABEL_EMBED)
            self.add_ui(embed)
        embed.update_embed(focus_point=lp)
        embed.wake_up()

    # ### Creation dialog
    # #########################################################

    def create_creation_dialog(self, scene_pos):
        """

        :param scene_pos:
        """
        self.release_editor_focus()
        embed = self.get_ui(NEW_ELEMENT_EMBED)
        marker = self.get_ui(NEW_ELEMENT_MARKER)
        if not embed:
            embed = NewElementEmbed(self.main.graph_view, NEW_ELEMENT_EMBED)
            self.add_ui(embed, show=False)
        if not marker:
            marker = NewElementMarker(scene_pos, embed, NEW_ELEMENT_MARKER)
            self.add_ui(marker)
        embed.marker = marker
        embed.update_embed(focus_point=scene_pos)
        marker.update_position(scene_pos=scene_pos)
        embed.wake_up()

    def clean_up_creation_dialog(self):
        """ Remove both
        :return:
        """
        embed = self.get_ui(NEW_ELEMENT_EMBED)
        marker = self.get_ui(NEW_ELEMENT_MARKER)
        if marker:
            self.remove_ui(marker)
        if embed:
            self.remove_ui(embed)

    # ### Node editing #########################################################

    def start_editing_node(self, node):
        """
        :param node:
        """
        self.release_editor_focus()
        ui_key = node.save_key + '_edit'
        ed = self.get_ui(ui_key)
        if ed:
            self.remove_edit_embed(ed)

        ed = NodeEditEmbed(self.main.graph_view, ui_key, node)
        self.add_ui(ed, show=False)
        self._node_edits.add(ed)
        ed.wake_up()

    def get_editing_embed_for_node(self, node):
        ui_key = node.save_key + '_edit'
        return self.get_ui(ui_key)

    def close_all_edits(self):
        """ Remove all node edit embeds from UI. e.g. when changing forests
        :return:
        """
        for edit in self._node_edits:
            edit.close()
            self.remove_ui(edit)
        self._node_edits = set()

    def remove_edit_embed(self, embed):
        """ Remove embed object from known UI.
        :param embed: UIEmbed object
        """
        self.remove_ui(embed)
        self._node_edits.remove(embed)

    # ### Touch areas
    # #####################################################################

    def get_touch_area(self, host, type):
        """ Get touch area for specific purpose or create one if it doesn't
        exist.
        :param host:
        :param type:
        :return:
        """
        ui_key = host.save_key + '_ta_' + str(type)
        return self.get_ui(ui_key)

    def create_touch_area(self, host, type, action):
        """ Get touch area for specific purpose or create one if it doesn't
        exist.
        :param host:
        :param type:
        :param action:
        :return:
        """
        ui_key = host.save_key + '_ta_' + str(type)
        ta = create_touch_area(host, type, ui_key, action)
        self.add_ui(ta)
        return ta

    def remove_touch_areas(self):
        """ Remove all touch areas from UI. Needs to be done when changing
        selection or starting
         dragging, or generally before touch areas are recalculated """
        for item in list(self._items.values()):
            if isinstance(item, TouchArea):
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
        for key, values in d.items():
            if node.check_conditions(values):
                action = self.get_action(values.get('action'))
                place = values.get('place', '')
                if place == 'edge_up':
                    for edge in node.get_edges_up(similar=True, visible=True):
                        ta = self.get_touch_area(edge, key)
                        if not ta:
                            self.create_touch_area(edge, key, action)
                elif place == 'parent_above':
                    for parent in node.get_parents(only_similar=True, only_visible=True):
                        ta = self.get_touch_area(parent, key)
                        if not ta:
                            self.create_touch_area(parent, key, action)

                elif not place:
                    ta = self.get_touch_area(node, key)
                    if not ta:
                        self.create_touch_area(node, key, action)
                else:
                    raise NotImplementedError

    # hmmmm.....
    def update_touch_areas_for_selected_edge(self, edge):
        """ Assumes that touch areas for this edge are empty and that the
        edge is selected
        :param edge: object to update
        """
        if self.free_drawing_mode() and edge.edge_type == g.CONSTITUENT_EDGE:
            ta = self.get_touch_area(edge, g.INNER_ADD_SIBLING_LEFT)
            if not ta:
                self.create_touch_area(edge, g.INNER_ADD_SIBLING_LEFT,
                                       self.get_action('inner_add_sibling_left'))
            ta = self.get_touch_area(edge, g.INNER_ADD_SIBLING_RIGHT)
            if not ta:
                self.create_touch_area(edge, g.INNER_ADD_SIBLING_RIGHT,
                                       self.get_action('inner_add_sibling_right'))

    def prepare_touch_areas_for_dragging(self, moving=None, multidrag=False):
        """
        :param drag_host: node that is being dragged
        :param moving: set of moving nodes (does not include drag_host)
        :param dragged_type: If the node doesn't exist yet, node_type can be
        given as a hint of what to expect
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
            for key, values in d.items():
                if node.check_conditions(values):
                    action = self.get_action(values.get('action'))
                    place = values.get('place', '')
                    if place == 'edge_up':
                        for edge in node.get_edges_up(similar=True, visible=True):
                            ta = self.get_touch_area(edge, key)
                            if not ta:
                                self.create_touch_area(edge, key, action)
                    elif not place:
                        ta = self.get_touch_area(node, key)
                        if not ta:
                            self.create_touch_area(node, key, action)
                    else:
                        raise NotImplementedError

    # ### Flashing symbols
    # ################################################################

    def show_anchor(self, node):
        """

        :param node:
        """
        # assert (node.locked or node.use_adjustment)
        ui_key = node.save_key + '_lock_icon'
        if ui_key in self._items:
            return

        item = FadingSymbol(qt_prefs.lock_pixmap, node, ui_key, place='bottom_right')
        # print u"\U0001F512" , unichr(9875) # unichr(9875)
        self.add_ui(item)
        item.fade_out()

    # ### Stretchlines
    # ####################################################################

    def begin_stretchline(self, start, end):
        """
        :param start:
        :param end:
        """
        sl = self.get_ui(STRETCHLINE)
        if sl:
            line = sl.line()
            line.setPoints(start, end)
            sl.setLine(line)
        else:
            line = QtCore.QLineF(start, end)
            sl = StretchLine(line, STRETCHLINE)
            sl.setPen(ctrl.cm.ui())
            self.add_ui(sl)
        sl.show()

    def draw_stretchline(self, end):
        """
        :param end:
        """
        sl = self.get_ui(STRETCHLINE)
        if sl:
            line = sl.line()
            line.setP2(end)
            sl.setLine(line)

    def end_stretchline(self):
        """
        :return:
        """
        sl = self.get_ui(STRETCHLINE)
        if sl:
            self.remove_ui(sl)

    # ### Messages
    # ####################################################################

    def add_command_feedback(self, msg):
        """ Insert new row of text to message window
        :param msg:
        """
        self.log_writer.add('>>>' + msg)

    def add_message(self, msg):
        """ Insert new row of text to log
        :param msg:
        """
        self.log_writer.add(msg)

    def show_command_prompt(self):
        """ Show '>>>_' in log """
        self.log_writer.add('>>>_')

    # Mode HUD
    def update_edit_mode(self):
        if ctrl.free_drawing_mode:
            text = 'Free drawing mode'
            checked = False
        else:
            text = 'Derivation mode'
            checked = True
        self._edit_mode_button.set_text(text)
        self._edit_mode_button.setChecked(checked)
        ctrl.call_watchers(self, 'mode_changed', value=not checked)

    # ### Embedded buttons ############################

    def create_float_buttons(self):
        """ Create top button row
        :return:
        """
        #for item in self._float_buttons:
        #    item.close()
        self.top_bar_buttons = TopBarButtons(ctrl.graph_view, self)

        self._edit_mode_button = ModeLabel('Free drawing mode',
                                           ui_key='edit_mode_label',
                                           parent=ctrl.graph_view)
        self.add_ui(self._edit_mode_button)
        self._edit_mode_button.update_position()
        self.connect_element_to_action(self._edit_mode_button, 'switch_edit_mode')
        self.update_edit_mode()
        self.top_bar_buttons.update_position()
        self.update_drag_mode(True) # selection mode

    def update_drag_mode(self, selection_mode):
        pan_around = self.get_ui('pan_around')
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

    def _create_overlay_button(self, icon, host, role, key, tooltip, action, size=None,
                               draw_method=None):
        """

        :param icon:
        :param host:
        :param role:
        :param key:
        :param text:
        :param action:
        :param size:
        """
        if key not in self._items:
            button = OverlayButton(host, key, role, pixmap=icon, tooltip=text,
                                   parent=self.main.graph_view,
                                   size=size or 16, draw_method=draw_method)
            self.add_ui(button)
            button.update_position()
            self.connect_element_to_action(button, action)
            button.show()
            return button
        else:
            return self._items[key]

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
        if node.label_object.resizable:
            handle = GraphicsResizeHandle(ctrl.graph_view, node)
            self.add_ui(handle)

    def get_or_create_button(self, node, role_key, action):
        if node:
            save_key = node.save_key + role_key
        else:
            save_key = role_key
        if save_key in self._items:
            return self._items[save_key]
        button = button_factory(role_key, node, save_key, self.main.graph_view)
        self.add_ui(button)
        button.update_position()
        if action:
            self.connect_element_to_action(button, action)
        else:
            print('missing action for button ', button, save_key)
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
        #if edge.edge_type is not g.CONSTITUENT_EDGE:
        key = edge.save_key + "_cut_start"
        if edge.start:
            self.add_button(CutFromStartButton(host=edge, ui_key=key, parent=ctrl.graph_view),
                            'disconnect_edge_start')
        key = edge.save_key + "_cut_end"
        if edge.end:
            self.add_button(CutFromEndButton(host=edge, ui_key=key, parent=ctrl.graph_view),
                            'disconnect_edge_end')

    # ### Control points
    # ####################################################################

    def add_control_points(self, edge):
        """ Display control points for this edge
        :param edge:
        """

        def _add_cp(key, index, role):
            cp = ControlPoint(edge, key, index=index, role=role)
            self.add_ui(cp)
            cp.update_position()

        key_base = edge.save_key + '_cp_'
        for i, point in enumerate(edge.control_points):
            _add_cp(key_base + str(i), i, '')
        if not edge.start:
            _add_cp(key_base + g.START_POINT, -1, g.START_POINT)
        if not edge.end:
            _add_cp(key_base + g.END_POINT, -1, g.END_POINT)
        if edge.label_item:
            _add_cp(key_base + g.LABEL_START, -1, g.LABEL_START)

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
        am = self.get_ui(ACTIVITY_MARKER)
        if not am:
            am = ActivityMarker(0, ACTIVITY_MARKER)
            self.add_ui(am)
        return am

    def get_ui_activity_marker(self):
        """

        :return:
        """
        am = self.get_ui(UI_ACTIVITY_MARKER)
        if not am:
            am = ActivityMarker(1, UI_ACTIVITY_MARKER)
            self.add_ui(am)
        return am

    # ### Timer ########################################################

    def item_moved(self):
        """


        """
        if not self._timer_id:
            self._timer_id = self.startTimer(prefs._fps_in_msec)
            #print('ui_support timer id ', self._timer_id)

    def timerEvent(self, event):
        """

        :param event:
        """
        items_have_moved = False
        for item in self.moving_things:
            if item.move_towards_target_position():
                items_have_moved = True
        if items_have_moved:
            self.get_ui_activity_marker().show()
        if not items_have_moved:
            self.get_ui_activity_marker().hide()
            self.killTimer(self._timer_id)
            self._timer_id = 0


    def free_drawing_mode(self, *args, **kwargs):
        """ Utility method for checking conditions for editing operations
        :param args: ignored
        :param kwargs: ignored
        :return:
        """
        return ctrl.free_drawing_mode
