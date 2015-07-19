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

from kataja.KatajaAction import KatajaAction
from kataja.managers.KeyPressManager import ShortcutSolver, ButtonShortcutFilter
from kataja.nodes.BaseConstituentNode import BaseConstituentNode
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.Edge import Edge
from kataja.ui.ActivityMarker import ActivityMarker
from kataja.ui.ControlPoint import ControlPoint
from kataja.ui.FadingSymbol import FadingSymbol
from kataja.ui.MessageWriter import MessageWriter
from kataja.ui.StretchLine import StretchLine
import kataja.actions as action_methods
from kataja.actions import actions
import kataja.globals as g
from kataja.ui.TouchArea import TouchArea, create_touch_area
from kataja.ui.panels.ColorThemePanel import ColorPanel
from kataja.ui.panels.ColorWheelPanel import ColorWheelPanel
from kataja.ui.panels.StylePanel import TableModelComboBox
from kataja.ui.panels.LogPanel import LogPanel
from kataja.ui.panels.NavigationPanel import NavigationPanel
from kataja.ui.panels.TestPanel import TestPanel
from kataja.ui.panels.VisualizationPanel import VisualizationPanel
from kataja.visualizations.available import VISUALIZATIONS, action_key
from kataja.ui.panels.LineOptionsPanel import LineOptionsPanel
from kataja.ui.embeds.NewElementEmbed import NewElementEmbed, NewElementMarker
from kataja.ui.embeds.EdgeLabelEmbed import EdgeLabelEmbed
from kataja.ui.panels import UIPanel
from kataja.ui.OverlayButton import OverlayButton
from kataja.ui.panels.SymbolPanel import SymbolPanel
from kataja.ui.panels.NodesPanel import NodesPanel
from kataja.ui.embeds.NodeEditEmbed import NodeEditEmbed
from kataja.ui.panels.StylePanel import StylePanel
from kataja.ui.panels.field_utils import MyColorDialog, MyFontDialog
from kataja.nodes.Node import Node
from utils import time_me

NOTHING = 0
SELECTING_AREA = 1
DRAGGING = 2
POINTING = 3

PANELS = {g.LOG: {'name': 'Log', 'position': 'bottom'},
          g.TEST: {'name': 'Test', 'position': 'right'},
          g.NAVIGATION: {'name': 'Trees', 'position': 'right'},
          g.VISUALIZATION: {'name': 'Visualization', 'position': 'right'},
          g.COLOR_THEME: {'name': 'Color theme', 'position': 'right'},
          g.COLOR_WHEEL: {'name': 'Color theme wheel', 'position': 'right',
                          'folded': True, 'closed': True},
          g.LINE_OPTIONS: {'name': 'More line options', 'position': 'float',
                           'closed': True},
          g.STYLE: {'name': 'Styles', 'position': 'right'},
          g.SYMBOLS: {'name': 'Symbols', 'position': 'right'},
          g.NODES: {'name': 'Nodes', 'position': 'right'}}

panel_order = [g.LOG, g.NAVIGATION, g.SYMBOLS, g.NODES, g.STYLE,
               g.VISUALIZATION, g.COLOR_THEME, g.COLOR_WHEEL,
               g.LINE_OPTIONS]  # g.TEST

panel_classes = {g.LOG: LogPanel, g.TEST: TestPanel,
                 g.NAVIGATION: NavigationPanel,
                 g.VISUALIZATION: VisualizationPanel, g.COLOR_THEME: ColorPanel,
                 g.COLOR_WHEEL: ColorWheelPanel,
                 g.LINE_OPTIONS: LineOptionsPanel, g.SYMBOLS: SymbolPanel,
                 g.NODES: NodesPanel, g.STYLE: StylePanel}

menu_structure = OrderedDict([('file_menu', ('&File',
                                             ['open', 'save', 'save_as', '---',
                                              'print_pdf', 'blender_render',
                                              '---', 'preferences', '---',
                                              'quit'])),
    ('edit_menu', ('&Edit', ['undo', 'redo'])), ('build_menu', ('&Build',
                                                                ['next_forest',
                                                                 'prev_forest',
                                                                 'next_derivation_step',
                                                                 'prev_derivation_step'])),
    ('rules_menu', ('&Rules', ['label_visibility', 'bracket_mode', 'trace_mode',
                               'merge_order_attribute',
                               'select_order_attribute'])), ('view_menu', (
    '&View',
    ['$visualizations', '---', 'change_colors', 'adjust_colors', 'zoom_to_fit',
     '---', 'fullscreen_mode'])),
    ('panels_menu', ('&Panels', ['$panels', '---', 'toggle_all_panels'])),
    ('help_menu', ('&Help', ['help']))])

NEW_ELEMENT_EMBED = 'new_element_embed'
NEW_ELEMENT_MARKER = 'new_element_marker'
EDGE_LABEL_EMBED = 'edge_label_embed'
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
        ctrl.add_watcher('selection_changed', self)
        ctrl.add_watcher('forest_changed', self)
        ctrl.add_watcher('viewport_changed', self)

    def get_panel(self, panel_id) -> UIPanel:
        """
        :param panel_id: panel key. Probably from constant from globals
        :return: UIPanel instance or None
        """
        return self._panels.get(panel_id, None)

    def get_action_group(self, action_group_name):
        """ Get action group with this name, or create one if it doesn't exist
        :param action_group_name:
        :return:
        """
        if action_group_name not in self._action_groups:
            self._action_groups[action_group_name] = QtWidgets.QActionGroup(
                self.main)
        return self._action_groups[action_group_name]

    def set_scope(self, scope):
        self.scope = scope
        if scope != g.SELECTION:
            self.base_scope = scope

    @property
    def edge_scope(self):
        return ctrl.fs.node_info(self.scope, 'edge')

    def start_color_dialog(self, receiver, parent, role,
                           initial_color='content1'):
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

    def add_ui(self, item):
        """

        :param item:
        """
        if item.ui_key in self._items:
            raise KeyError
        self._items[item.ui_key] = item
        if isinstance(item, QtWidgets.QGraphicsItem):
            self.scene.addItem(item)
            item.show()

    def remove_ui(self, item):
        """

        :param item:
        """
        if item.ui_key in self._items:
            del self._items[item.ui_key]
        if isinstance(item, QtWidgets.QGraphicsItem):
            item.hide()
            self.scene.removeItem(item)
        elif isinstance(item, QtWidgets.QWidget):
            item.close()
            item.hide()

    def get_ui(self, ui_key):
        """ Return a managed ui item
        :param ui_key:
        :return:
        """
        return self._items.get(ui_key, None)

    def store_panel_positions(self):
        """ Store panel positions temporarily. UI manager doesn't save to
        file, if that is
        wanted, data has to be sent to some permanency supporting object.
        """
        self._panel_positions = {}
        for panel_id, panel in self._panels.items():
            self._panel_positions[panel_id] = panel.geometry()

    def reset_panel_fields(self):
        """ Update all panel fields, may be costly -- try to do specific
        updates instead.
        :return:
        """
        for panel in self._panels.values():
            panel.update_fields()

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

    def update_all_fields(self):
        """

        """
        print('*** ui update_all_fields called ***')

    def restore_panel_positions(self):
        """


        """
        for name, panel in self._panels.items():
            if name in self._panel_positions:
                panel.setGeometry(self._panel_positions[name])

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
        type is selected """
        # clear all ui pieces
        for item in list(self._items.values()):
            if item.host:
                self.remove_ui(item)
        # create ui pieces for selected elements
        for item in ctrl.selected:
            if isinstance(item, Edge):
                self.update_touch_areas_for_selected_edge(item)
                self.add_control_points(item)
                self.add_buttons_for_edge(item)
            elif isinstance(item, Node):
                self.update_touch_areas_for_selected_node(item)
                if item.node_type == g.CONSTITUENT_NODE:
                    self.add_buttons_for_constituent_node(item)
                #elif item.node_type == g.COMMENT_NODE:
                #    self.add_buttons_for_comment_node(item)
        if ctrl.selected:
            if self.scope != g.SELECTION:
                self.base_scope = self.scope
            self.scope = g.SELECTION
        else:
            self.scope = self.base_scope

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
                if ui_item.host is item:
                    self.remove_ui(ui_item)

    # ### Actions, Menus and Panels
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

        i = 0
        additional_actions['visualizations'] = []
        for name, vis in VISUALIZATIONS.items():
            key = action_key(name)
            d = {'command': name, 'method': action_methods.change_visualization,
                 'shortcut': vis.shortcut, 'checkable': True,
                 'sender_arg': True, 'args': [name],
                 'viewgroup': 'visualizations', 'exclusive': True}
            self.actions[key] = d
            additional_actions['visualizations'].append(key)

        additional_actions['panels'] = []
        for panel_key, panel_data in PANELS.items():
            key = 'toggle_panel_%s' % panel_key
            d = {'command': panel_data['name'],
                 'method': action_methods.toggle_panel, 'checkable': True,
                 'viewgroup': 'Panels', 'args': [panel_key], 'undoable': False,
                 'exclusive': False, 'tooltip': "Close this panel"}
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

    def create_menus(self, additional_actions):
        """ Put actions to menus. Menu structure is defined at the top of
        this file.
        :return: None
        """

        def add_menu(parent, data):
            """

            :param parent:
            :param data:
            :return:
            """
            menu_label, menu_items = data
            menu = QtWidgets.QMenu(menu_label, self.main)
            for item in menu_items:
                if isinstance(item, tuple):
                    add_menu(menu, item)
                elif item == '---':
                    menu.addSeparator()
                else:
                    menu.addAction(self.qt_actions[item])
            parent.addMenu(menu)
            return menu

        def expand_list(data):
            """

            :param data:
            :return:
            """
            label, items = data
            exp_items = []
            for item in items:
                if isinstance(item, str) and item.startswith("$"):
                    exp_items += additional_actions[item[1:]]
                elif isinstance(item, tuple):
                    exp_items.append(expand_list(item))
                else:
                    exp_items.append(item)
            return label, exp_items

        # replace '$names' with dynamic actions
        expanded_menu_structure = OrderedDict()
        for key, data in menu_structure.items():
            expanded_menu_structure[key] = expand_list(data)

        # build menus
        self._top_menus = {}
        for key, data in expanded_menu_structure.items():
            menu = add_menu(self.main.menuBar(), data)
            self._top_menus[key] = menu

    def create_panels(self):
        """ Put actions to panels. Panel contents are defined at the top of
        this file.
        :return: None
        """
        self._panels = {}
        for panel_key in panel_order:
            data = PANELS[panel_key]
            if not data.get('closed', False):
                self.create_panel(panel_key, **data)

    def create_panel(self, id, name='', position=None, folded=False,
                     default=False, **kwargs):
        """

        :param id:
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
        constructor = panel_classes[id]
        new_panel = constructor(name, id, default_position=position,
                                parent=self.main, ui_manager=self,
                                folded=folded)
        self._panels[id] = new_panel
        return new_panel

    def connect_element_to_action(self, element, action, tooltip_suffix=''):
        """

        :param element:
        :param action:
        :param tooltip_suffix:
        """
        if isinstance(action, str):
            action = self.qt_actions[action]
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
        element.setShortcut(key_seq)

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
            args.append((element.currentIndex(),
                         element.itemData(element.currentIndex())))
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
            embed = EdgeLabelEmbed(self.main.graph_view, self, edge,
                                   EDGE_LABEL_EMBED)
            self.add_ui(embed)
        else:
            embed = self._items[EDGE_LABEL_EMBED]
        embed.update_embed(scenePos=lp)
        embed.wake_up()

    # ### Creation dialog
    # #########################################################

    def create_creation_dialog(self, scenePos):
        """

        :param scenePos:
        """
        embed = self.get_ui(NEW_ELEMENT_EMBED)
        marker = self.get_ui(NEW_ELEMENT_MARKER)
        if not embed:
            embed = NewElementEmbed(self.main.graph_view, self,
                                    NEW_ELEMENT_EMBED)
            self.add_ui(embed)
        if not marker:
            marker = NewElementMarker(scenePos, embed, NEW_ELEMENT_MARKER)
            self.add_ui(marker)
        embed.marker = marker
        embed.update_embed(scenePos=scenePos)
        marker.update_position(scenePos=scenePos)
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
            embed.blur_away()

    # ### Node editing #########################################################

    def start_editing_node(self, node):
        """
        :param node:
        """
        ui_key = node.save_key + '_edit'
        ed = self.get_ui(ui_key)
        if ed:
            self.remove_ui(ed)

        ed = NodeEditEmbed(self.main.graph_view, self, ui_key, node)
        self.add_ui(ed)
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
        ta = self.get_ui(ui_key)
        if not ta:
            ta = create_touch_area(host, type, ui_key)
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
            elif cond == 'is_root':
                return node.is_root_node(only_visible=False)
            elif cond == 'edge_down':
                return list(node.get_edges_down(similar=True, visible=True))
            else:
                raise NotImplementedError(cond)

        if not node.is_visible():
            return
        d = node.__class__.touch_areas_when_selected
        for key, values in d.items():
            cond = values.get('condition')
            ok = check_conditions(cond, node)
            if ok:
                place = values.get('place', '')
                if place == 'edge_up':
                    for edge in node.get_edges_up(similar=True,
                                                  visible=True):
                        self.get_touch_area(edge, key)
                elif not place:
                    self.get_touch_area(node, key)
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
                    self.get_touch_area(edge.end, g.TOUCH_ADD_CONSTITUENT)
                if edge.start and (edge.start.is_placeholder()):
                    self.get_touch_area(edge.start, g.TOUCH_ADD_CONSTITUENT)
            else:
                self.get_touch_area(edge, g.LEFT_ADD_SIBLING)
                self.get_touch_area(edge, g.RIGHT_ADD_SIBLING)


    def prepare_touch_areas_for_dragging(self, drag_host=None, moving=None,
                                         dragged_type='', multidrag=False):
        """
        :param drag_host: node that is being dragged
        :param moving: set of moving nodes (does not include drag_host)
        :param dragged_type: If the node doesn't exist yet, node_type can be
        given as a hint of what to expect
        """
        def check_conditions(cond, node, drag_host, dragged_type):
            if isinstance(cond, list):
                return all((check_conditions(c, node, drag_host, dragged_type)
                            for c in
                          cond))
            if not cond:
                return True
            elif cond == 'is_root':
                return node.is_root_node(only_visible=False)
            elif cond == 'dragging_comment':
                return dragged_type == g.COMMENT_NODE
            elif cond == 'dragging_feature':
                return dragged_type == g.FEATURE_NODE
            elif cond == 'dragging_constituent':
                return dragged_type == g.CONSTITUENT_NODE
            elif cond == 'dragging_gloss':
                return dragged_type == g.GLOSS_NODE
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
                    place = values.get('place', '')
                    if place == 'edge_up':
                        for edge in node.get_edges_up(similar=True,
                                                      visible=True):
                            self.get_touch_area(edge, key)
                    elif not place:
                        self.get_touch_area(node, key)
                    else:
                        raise NotImplementedError


    # ### Flashing symbols
    # ################################################################

    def show_anchor(self, node):
        """

        :param node:
        """
        assert (node.is_locked())
        ui_key = node.save_key + '_lock_icon'
        item = FadingSymbol(qt_prefs.lock_pixmap, node, self, ui_key,
                            place='bottom_right')
        # print u"\U0001F512" , unichr(9875) # unichr(9875)
        self.add_ui(item)
        item.fade_out('slow')

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

    def _create_overlay_button(self, icon, host, role, key, text, action,
                               size=None):
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
            button = OverlayButton(icon, host, role, key, text,
                                   parent=self.main.graph_view, size=size or 16)
            self.add_ui(button)
            button.update_position()
            self.connect_element_to_action(button, action)
            button.show()

    def add_remove_merger_button(self, node):
        """

        :param node:
        :param edge:
        """
        self._create_overlay_button(icon=qt_prefs.delete_icon, host=node,
                                    role=g.REMOVE_TRIANGLE,
                                    key=node.save_key + g.REMOVE_MERGER,
                                    text='Remove this non-merging node',
                                    action='remove_merger')

    def add_unfold_triangle_button(self, node):
        """

        :param node:
        """
        self._create_overlay_button(icon=qt_prefs.triangle_close_icon,
                                    host=node, role=g.REMOVE_TRIANGLE,
                                    key=node.save_key + g.REMOVE_TRIANGLE,
                                    text='Reveal nodes inside the triangle',
                                    action='remove_triangle', size=(48, 24))

    def add_fold_triangle_button(self, node):
        """

        :param node:
        """
        self._create_overlay_button(icon=qt_prefs.triangle_icon, host=node,
                                    role=g.ADD_TRIANGLE,
                                    key=node.save_key + g.ADD_TRIANGLE,
                                    text='Turn into a triangle',
                                    action='add_triangle', size=(48, 24))

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
                self._create_overlay_button(icon=qt_prefs.cut_icon, host=edge,
                                            role=g.START_CUT, key=key,
                                            text='Disconnect from node',
                                            action='disconnect_edge')
        key = edge.save_key + "_cut_end"
        if edge.end and not edge.end.is_placeholder():
            self._create_overlay_button(icon=qt_prefs.cut_icon, host=edge,
                                        role=g.END_CUT, key=key,
                                        text='Disconnect from node',
                                        action='disconnect_edge')

    def add_buttons_for_constituent_node(self, node):
        """

        :param node:
        """
        for child in node.get_children():
            if child.is_placeholder():
                self.add_remove_merger_button(node)
                break
        if node.triangle:
            self.add_unfold_triangle_button(node)
        elif ctrl.forest.can_fold(node):
            self.add_fold_triangle_button(node)

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
