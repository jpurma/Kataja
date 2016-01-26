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

import kataja.actions as action_methods
import kataja.globals as g
from kataja.Amoeba import Amoeba
from kataja.Edge import Edge
from kataja.KatajaAction import KatajaAction, ShortcutSolver, ButtonShortcutFilter
from kataja.actions import actions
from kataja.nodes.Node import Node
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.ui import drawn_icons
from kataja.ui.ActivityMarker import ActivityMarker
from kataja.ui.ControlPoint import ControlPoint
from kataja.ui.FadingSymbol import FadingSymbol
from kataja.ui.MessageWriter import MessageWriter
from kataja.ui.OverlayButton import OverlayButton, button_factory
from kataja.ui.StretchLine import StretchLine
from kataja.ui.TouchArea import TouchArea, create_touch_area
from kataja.ui.elements.MyColorDialog import MyColorDialog
from kataja.ui.elements.MyFontDialog import MyFontDialog
from kataja.ui.elements.ResizeHandle import GraphicsResizeHandle
from kataja.ui.elements.TableModelComboBox import TableModelComboBox
from kataja.ui.embeds.EdgeLabelEmbed import EdgeLabelEmbed
from kataja.ui.embeds.NewElementEmbed import NewElementEmbed, NewElementMarker
from kataja.ui.embeds.NodeEditEmbed import NodeEditEmbed
from kataja.ui.embeds.GroupLabelEmbed import GroupLabelEmbed
from kataja.ui.panels import UIPanel
from kataja.ui.panels.ColorThemePanel import ColorPanel
from kataja.ui.panels.ColorWheelPanel import ColorWheelPanel
from kataja.ui.panels.LineOptionsPanel import LineOptionsPanel
from kataja.ui.panels.LogPanel import LogPanel
from kataja.ui.panels.NavigationPanel import NavigationPanel
from kataja.ui.panels.NodesPanel import NodesPanel
from kataja.ui.panels.StylePanel import StylePanel
from kataja.ui.panels.SymbolPanel import SymbolPanel
from kataja.ui.panels.VisualizationOptionsPanel import VisualizationOptionsPanel
from kataja.ui.panels.VisualizationPanel import VisualizationPanel
from kataja.visualizations.available import VISUALIZATIONS, action_key
from kataja.utils import time_me

NOTHING = 0
SELECTING_AREA = 1
DRAGGING = 2
POINTING = 3

PANELS = {g.LOG: {'name': 'Log', 'position': 'bottom'},
          g.NAVIGATION: {'name': 'Trees', 'position': 'right'},
          g.VISUALIZATION: {'name': 'Visualization', 'position': 'right'},
          g.COLOR_THEME: {'name': 'Color theme', 'position': 'right'},
          g.COLOR_WHEEL: {'name': 'Color theme wheel', 'position': 'right', 'folded': True,
                          'closed': True},
          g.LINE_OPTIONS: {'name': 'More line options', 'position': 'float', 'closed': True},
          g.STYLE: {'name': 'Styles', 'position': 'right'},
          g.SYMBOLS: {'name': 'Symbols', 'position': 'right'},
          g.NODES: {'name': 'Nodes', 'position': 'right'},
          g.VIS_OPTIONS: {'name': 'Visualization options', 'position': 'float', 'closed': True}}

panel_order = [g.LOG, g.NAVIGATION, g.SYMBOLS, g.NODES, g.STYLE, g.VISUALIZATION, g.COLOR_THEME,
               g.COLOR_WHEEL, g.LINE_OPTIONS, g.VIS_OPTIONS]

panel_classes = {g.LOG: LogPanel, g.NAVIGATION: NavigationPanel,
                 g.VISUALIZATION: VisualizationPanel, g.COLOR_THEME: ColorPanel,
                 g.COLOR_WHEEL: ColorWheelPanel, g.LINE_OPTIONS: LineOptionsPanel,
                 g.SYMBOLS: SymbolPanel, g.NODES: NodesPanel, g.STYLE: StylePanel,
                 g.VIS_OPTIONS: VisualizationOptionsPanel}

menu_structure = OrderedDict([('file_menu', ('&File',
                                             ['new_project', 'new_forest', 'open', 'save',
                                              'save_as', '---', 'print_pdf', 'blender_render',
                                              '---', 'preferences', '---', 'quit'])),
                              ('edit_menu', ('&Edit', ['undo', 'redo'])), ('build_menu', (
    '&Build', ['next_forest', 'prev_forest', 'next_derivation_step', 'prev_derivation_step'])), (
                              'rules_menu', ('&Rules',
                                             ['bracket_mode', 'trace_mode', 'merge_order_attribute',
                                              'select_order_attribute'])), ('view_menu', ('&View', [
        '$visualizations', '---', 'change_colors', 'adjust_colors', 'zoom_to_fit', '---',
        'fullscreen_mode'])), ('windows_menu', ('&Windows', [('Panels', ['$panels']), '---',
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

        self._items = {}
        self._node_edits = set()
        self.log_writer = MessageWriter()

        self._timer_id = 0
        self._panels = {}
        self._panel_positions = {}
        self.moving_things = set()
        self.button_shortcut_filter = ButtonShortcutFilter()
        self.shortcut_solver = ShortcutSolver(self)

        self.scope = g.CONSTITUENT_NODE
        self.base_scope = g.CONSTITUENT_NODE
        self.selection_amoeba = None

        self.preferences_dialog = None
        self.color_dialogs = {}
        self.font_dialogs = {}

    def populate_ui_elements(self):
        """ These cannot be created in __init__, as individual panels etc.
        may refer to ctrl.ui,
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
        self.scope = scope
        if scope != g.SELECTION:
            self.base_scope = scope

    @property
    def edge_scope(self):
        return ctrl.fs.node_info(self.scope, 'edge')

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
            fd = MyFontDialog(parent, role, initial_font)
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
        item.hide()
        if isinstance(item, QtWidgets.QGraphicsItem):
            self.scene.removeItem(item)
        elif isinstance(item, QtWidgets.QWidget):
            self.remove_watched_shortcuts_for(item)
            item.close()

    def get_ui(self, ui_key) -> QtCore.QObject:
        """ Return a managed ui item
        :param ui_key:
        :return:
        """
        return self._items.get(ui_key, None)

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
            self.create_float_buttons()
        elif signal == 'viewport_changed':
            self.update_positions()

    def update_all_fields(self):
        """

        """
        print('*** ui update_all_fields called ***')

    def resize_ui(self, size):
        # self.setSceneRect(0, 0, size.width(), size.height())
        """

        :param size:
        """
        self.update_positions()

    def update_colors(self):
        """ Update colors in all ui elements that understand that demand."""
        for item in self._items.values():
            if hasattr(item, 'update_colors'):
                item.update_colors()
        for panel in self._panels.values():
            panel.update_colors()

    def update_selections(self):
        """ Many UI elements change mode depending on if object of specific
        type is selected. Also the logic of selection amoebas has to be handled somewhere. """
        # clear all ui pieces
        for item in list(self._items.values()):
            if item.host and not getattr(item, '_fade_out_active', False):
                self.remove_ui(item)
        # create ui pieces for selected elements. don't create touchareas and buttons if multiple
        # selection, it gets confusing fast
        if len(ctrl.selected) == 1:
            item = ctrl.selected[0]
            #for item in ctrl.selected:
            if isinstance(item, Edge):
                self.update_touch_areas_for_selected_edge(item)
                self.add_control_points(item)
                self.add_buttons_for_edge(item)
            elif isinstance(item, Node):
                self.update_touch_areas_for_selected_node(item)
                self.update_buttons_for_selected_node(item)
        if ctrl.selected:
            # note UI panels that they should use scope 'selection' for their activities
            if self.scope != g.SELECTION:
                self.base_scope = self.scope
            self.scope = g.SELECTION
            amoebas = []
            # check if _one_ of the groups/"amoebas" was selected
            for item in ctrl.selected:
                if isinstance(item, Amoeba):
                    amoebas.append(item)
            if len(amoebas) == 1:
                # select this amoeba
                self.selection_amoeba = amoebas[0]
                # check if any items in this amoeba's scope are _unselected_
                for group_member in self.selection_amoeba.selection:
                    if group_member not in ctrl.selected:
                        self.selection_amoeba.remove_node(group_member)
                # check if any selection contains any objects that should be added to group
                for node in ctrl.selected:
                    if isinstance(node, Node) and node.can_be_in_groups:
                        if node not in self.selection_amoeba:
                            self.selection_amoeba.add_node(node)

            # draw a selection amoeba around selected nodes
            elif not self.selection_amoeba:
                self.selection_amoeba = Amoeba(ctrl.selected, persistent=False)
                self.selection_amoeba.update_colors(
                        color_key=ctrl.forest.get_group_color_suggestion())
                self.add_ui(self.selection_amoeba)
            # or update existing selection
            else:
                self.selection_amoeba.update_selection(ctrl.selected)
                self.selection_amoeba.update_shape()
            self.add_buttons_for_amoeba(self.selection_amoeba)
        else:
            self.scope = self.base_scope
            if self.selection_amoeba:
                self.remove_ui_for(self.selection_amoeba)
                if not self.selection_amoeba.persistent:
                    self.remove_ui(self.selection_amoeba)
                self.selection_amoeba = None

    # unused, but sane
    def focusable_elements(self):
        """ Return those UI elements that are flagged focusable (Kataja's
        focusable, not Qt's).
        """
        for e in self._items:
            if getattr(e, 'focusable', False) and e.isVisible():
                yield e

    def clear_items(self):
        """ Remove all ui objects managed by UIManager.
        """
        ctrl.deselect_objects()
        for item in list(self._items.values()):
            self.remove_ui(item)

    def update_positions(self):
        """ UI has elements that point to graph scene elements, and when
        something moves there
        UI has to update its elements too."""
        for item in self._items.values():
            if hasattr(item, 'update_position'):
                item.update_position()

    def update_position_for(self, obj):
        """ Update position of ui-elements for selected (non-ui) object.
        :param obj:
        :return:
        """
        for item in self._items.values():
            if item.host is obj:
                item.update_position()

    def remove_ui_for(self, item):
        """
        :param item: item or iterable of items
        """
        if isinstance(item, (tuple, list, set)):
            for ui_item in list(self._items.values()):
                if ui_item.host in item:
                    self.remove_ui(ui_item)
        else:
            for ui_item in list(self._items.values()):
                if ui_item.host is item and not getattr(ui_item, '_fade_out_active', False):
                    self.remove_ui(ui_item)

    # ### Actions and Menus
    # ####################################################

    def create_actions(self):
        """ Build menus and other actions that can be triggered by user based
        on actions.py"""

        main = self.main

        # dynamic actions are created based on other data e.g. available
        # visualization plugins.
        # they are added into actions as everyone else, but there is a
        # special mapping to find
        # them later.
        # eg. additional_actions['visualizations'] = ['vis_1','vis_2',
        # 'vis_3'...]
        additional_actions = {}
        self.actions = actions

        additional_actions['visualizations'] = []
        for name, vis in VISUALIZATIONS.items():
            key = action_key(name)
            d = {'command': name, 'method': action_methods.change_visualization,
                 'shortcut': vis.shortcut, 'checkable': True, 'sender_arg': True, 'args': [name],
                 'viewgroup': 'visualizations', 'exclusive': True}
            self.actions[key] = d
            additional_actions['visualizations'].append(key)

        additional_actions['panels'] = []
        for panel_key, panel_data in PANELS.items():
            key = 'toggle_panel_%s' % panel_key
            d = {'command': panel_data['name'], 'method': action_methods.toggle_panel,
                 'checkable': True, 'viewgroup': 'Panels', 'args': [panel_key], 'action_arg': True,
                 'undoable': False, 'exclusive': False, 'tooltip': "Close this panel"}
            self.actions[key] = d
            additional_actions['panels'].append(key)
        # ## Create actions
        self._action_groups = {}
        self.qt_actions = {}

        for key, data in self.actions.items():
            action = KatajaAction(key, **data)
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
        d = {'command': '', 'method': action_methods.switch_project,
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
            action = KatajaAction(key, **e)
            action.setChecked(project is current_project)
            self.qt_actions[key] = action
            win_menu.addAction(action)


    # ###################################################################
    #                           PANELS
    # ###################################################################

    def get_panel(self, panel_id) -> UIPanel:
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
        for panel_key in panel_order:
            data = PANELS[panel_key]

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
                                ui_manager=self, folded=folded)
        self._panels[id] = new_panel
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

    # ### Label edge editin dialog
    # #########################################################

    def start_edge_label_editing(self, edge):
        """

        :param edge:
        """
        lp = edge.label_item.pos()
        if EDGE_LABEL_EMBED not in self._items:
            embed = EdgeLabelEmbed(self.main.graph_view, self, edge, EDGE_LABEL_EMBED)
            self.add_ui(embed)
        else:
            embed = self._items[EDGE_LABEL_EMBED]
        embed.update_embed(focus_point=lp)
        embed.wake_up()

    def toggle_group_label_editing(self, amoeba):
        """ Start group label editing or close it if it's already active.
        :param amoeba:
        :return:
        """
        lp = amoeba.boundingRect().center()
        if GROUP_LABEL_EMBED in self._items:
            embed = self._items[GROUP_LABEL_EMBED]
            if embed.host is amoeba:
                embed.close()
                self.remove_ui(embed)
                return
            else:
                embed.host = amoeba
        else:
            embed = GroupLabelEmbed(self.main.graph_view, self, amoeba, GROUP_LABEL_EMBED)
            self.add_ui(embed)
        embed.update_embed(focus_point=lp)
        embed.wake_up()


    # ### Creation dialog
    # #########################################################

    def create_creation_dialog(self, scene_pos):
        """

        :param scene_pos:
        """
        embed = self.get_ui(NEW_ELEMENT_EMBED)
        marker = self.get_ui(NEW_ELEMENT_MARKER)
        if not embed:
            embed = NewElementEmbed(self.main.graph_view, self, NEW_ELEMENT_EMBED)
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
        ui_key = node.save_key + '_edit'
        ed = self.get_ui(ui_key)
        if ed:
            self.remove_edit_embed(ed)

        ed = NodeEditEmbed(self.main.graph_view, self, ui_key, node)
        self.add_ui(ed, show=False)
        self._node_edits.add(ed)
        ed.wake_up()

    def get_editing_node(self, node):
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

        def check_conditions(cond, node):
            if isinstance(cond, list):
                return all((check_conditions(c, node) for c in cond))
            if not cond:
                return True
            cmethod = getattr(node, cond)
            if cmethod:
                return cmethod()
            else:
                raise NotImplementedError(cond)

        if not node.is_visible():
            return
        d = node.__class__.touch_areas_when_selected
        for key, values in d.items():
            cond = values.get('condition')
            ok = check_conditions(cond, node)
            if ok:
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

    # hmmmm.....
    def update_touch_areas_for_selected_edge(self, edge):
        """ Assumes that touch areas for this edge are empty and that the
        edge is selected
        :param edge: object to update
        """
        if edge.edge_type == g.CONSTITUENT_EDGE:
            if edge.has_orphan_ends():
                if edge.end and (edge.end.is_placeholder()):
                    ta = self.get_touch_area(edge.end, g.TOUCH_ADD_CONSTITUENT)
                    if not ta:
                        self.create_touch_area(edge.end, g.TOUCH_ADD_CONSTITUENT,
                                               self.get_action('replace_placeholder'))
                if edge.start and (edge.start.is_placeholder()):
                    ta = self.get_touch_area(edge.start, g.TOUCH_ADD_CONSTITUENT)
                    if not ta:
                        self.create_touch_area(edge.start, g.TOUCH_ADD_CONSTITUENT,
                                               self.get_action('replace_placeholder'))
            else:
                ta = self.get_touch_area(edge, g.LEFT_ADD_SIBLING)
                if not ta:
                    self.create_touch_area(edge, g.LEFT_ADD_SIBLING,
                                           self.get_action('add_sibling_left'))
                ta = self.get_touch_area(edge, g.RIGHT_ADD_SIBLING)
                if not ta:
                    self.create_touch_area(edge, g.RIGHT_ADD_SIBLING,
                                           self.get_action('add_sibling_right'))

    def prepare_touch_areas_for_dragging(self, drag_host=None, moving=None, dragged_type='',
                                         multidrag=False):
        """
        :param drag_host: node that is being dragged
        :param moving: set of moving nodes (does not include drag_host)
        :param dragged_type: If the node doesn't exist yet, node_type can be
        given as a hint of what to expect
        """

        def check_conditions(cond, node, drag_host, dragged_type):
            if isinstance(cond, list):
                return all((check_conditions(c, node, drag_host, dragged_type) for c in cond))
            if not cond:
                return True
            elif cond == 'is_top':
                return node.is_top_node(only_visible=False)
            elif cond == 'dragging_comment':
                return dragged_type == g.COMMENT_NODE and \
                       ((not drag_host) or (drag_host and drag_host.can_connect_with(node)))
            elif cond == 'dragging_feature':
                return dragged_type == g.FEATURE_NODE and \
                       ((not drag_host) or (drag_host and drag_host.can_connect_with(node)))
            elif cond == 'dragging_constituent':
                return dragged_type == g.CONSTITUENT_NODE and \
                       ((not drag_host) or (drag_host and drag_host.can_connect_with(node)))
            elif cond == 'dragging_gloss':
                return dragged_type == g.GLOSS_NODE and \
                       ((not drag_host) or (drag_host and drag_host.can_connect_with(node)))
            elif hasattr(node, cond):
                ncond = getattr(node, cond)
                if callable(ncond):
                    return ncond(dragged_type, drag_host)
                else:
                    return ncond
            else:
                raise NotImplementedError

        self.remove_touch_areas()
        if multidrag:
            return
        if not moving:
            moving = []
        if not dragged_type:
            dragged_type = drag_host.node_type
        for node in ctrl.forest.nodes.values():
            if not node.is_visible():
                continue
            if node in moving:
                continue
            if node is drag_host:
                continue
            d = node.__class__.touch_areas_when_dragging
            for key, values in d.items():
                cond = values.get('condition')
                ok = check_conditions(cond, node, drag_host, dragged_type)
                if ok:
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

        item = FadingSymbol(qt_prefs.lock_pixmap, node, self, ui_key, place='bottom_right')
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

    # ### Embedded buttons ############################


    def create_float_buttons(self):
        """ Create top button row
        :return:
        """
        fit_to_screen = self._create_overlay_button(host=None, key='fit_to_screen', icon=None,
                                                    role='bottom', text='Fit to screen',
                                                    action='zoom_to_fit', size=(48, 24),
                                                    draw_method=drawn_icons.fit_to_screen)
        gw = fit_to_screen.parent()
        fit_to_screen.move(gw.width() - fit_to_screen.width() - 2, 2)
        fit_to_screen.show()

    def _create_overlay_button(self, icon, host, role, key, text, action, size=None,
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
            button = OverlayButton(host, key, icon, role, text, parent=self.main.graph_view,
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

        def check_conditions(cond, node):
            if isinstance(cond, list):
                return all((check_conditions(c, node) for c in cond))
            if not cond:
                return True
            cmethod = getattr(node, cond)
            if cmethod:
                return cmethod()
            else:
                raise NotImplementedError(cond)

        if not node.is_visible():
            return
        d = node.__class__.buttons_when_selected
        for key, values in d.items():
            cond = values.get('condition', None)
            ok = check_conditions(cond, node)
            if ok:
                self.get_or_create_button(node, key)
        if node.label_object.resizable:
            handle = GraphicsResizeHandle(ctrl.graph_view, node)
            self.add_ui(handle)

    def get_or_create_button(self, node, role_key):
        if node:
            save_key = node.save_key + role_key
        else:
            save_key = role_key
        if save_key in self._items:
            return self._items[save_key]
        button = button_factory(role_key, node, save_key, self.main.graph_view)
        self.add_ui(button)
        button.update_position()
        self.connect_element_to_action(button, button.action_name)
        button.show()
        return button

    def add_buttons_for_amoeba(self, amoeba):
        """ Selection amoebas have a button to toggle their editing options
        :param amoeba:
        :return:
        """
        button = self.get_or_create_button(amoeba, g.AMOEBA_OPTIONS)
        return button


    def add_buttons_for_edge(self, edge):
        """ Constituent edges have a button to remove the edge and the node
        in between.
        :param edge:
        """
        if edge.edge_type is g.CONSTITUENT_EDGE:
            if edge.end and edge.end.is_placeholder():
                self.add_remove_merger_button(edge.start)
        # Constituent edges don't have cut-button at the start
        else:
            key = edge.save_key + "_cut_start"
            if edge.start:
                self._create_overlay_button(icon=qt_prefs.cut_icon, host=edge, role=g.START_CUT,
                                            key=key, text='Disconnect from node',
                                            action='disconnect_edge')
        key = edge.save_key + "_cut_end"
        if edge.end and not edge.end.is_placeholder():
            self._create_overlay_button(icon=qt_prefs.cut_icon, host=edge, role=g.END_CUT, key=key,
                                        text='Disconnect from node', action='disconnect_edge')

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
        if not edge.start:  # or edge.start.is_placeholder():
            _add_cp(key_base + g.START_POINT, -1, g.START_POINT)
        if not edge.end:  # or edge.end.is_placeholder():
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
            #print('ui timer id ', self._timer_id)

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
