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

from PyQt5 import QtCore, QtWidgets, QtGui

from kataja.KatajaAction import KatajaAction
from kataja.KeyPressManager import ShortcutSolver, ButtonShortcutFilter
from kataja.BaseConstituentNode import BaseConstituentNode
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
from kataja.ui.TouchArea import TouchArea
from kataja.ui.panels.ColorThemePanel import ColorPanel
from kataja.ui.panels.ColorWheelPanel import ColorWheelPanel
from kataja.ui.panels.EdgesPanel import EdgesPanel, TableModelComboBox
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
          g.COLOR_WHEEL: {'name': 'Color theme wheel', 'position': 'right', 'folded': True,
                          'closed': True},
          g.LINE_OPTIONS: {'name': 'More line options', 'position': 'float', 'closed': True},
          g.EDGES: {'name': 'Edge drawing', 'position': 'right'},
          g.SYMBOLS: {'name': 'Symbols', 'position': 'right'},
          g.NODES: {'name': 'Nodes', 'position': 'right'}
}

panel_order = [g.LOG, g.NAVIGATION, g.SYMBOLS, g.NODES, g.VISUALIZATION, g.COLOR_THEME,
               g.COLOR_WHEEL, g.LINE_OPTIONS, g.EDGES]

panel_classes = {g.LOG: LogPanel, g.TEST: TestPanel, g.NAVIGATION: NavigationPanel,
                 g.VISUALIZATION: VisualizationPanel,
                 g.COLOR_THEME: ColorPanel, g.COLOR_WHEEL: ColorWheelPanel, g.EDGES: EdgesPanel,
                 g.LINE_OPTIONS: LineOptionsPanel, g.SYMBOLS: SymbolPanel, g.NODES: NodesPanel}

menu_structure = OrderedDict([
    ('file_menu',
     ('&File', ['open', 'save', 'save_as', '---', 'print_pdf', 'blender_render', '---',
                'preferences', '---', 'quit'])),
    ('edit_menu', ('&Edit', ['undo', 'redo'])),
    ('build_menu', ('&Build', ['next_forest', 'prev_forest', 'next_derivation_step',
                               'prev_derivation_step'])),
    ('rules_menu', ('&Rules',
                    ['label_visibility', 'bracket_mode', 'trace_mode', 'merge_edge_shape',
                     'feature_edge_shape', 'merge_order_attribute', 'select_order_attribute'])),
    ('view_menu',
     ('&View', ['$visualizations', '---', 'change_colors', 'adjust_colors', 'zoom_to_fit', '---',
                'fullscreen_mode'])),
    ('panels_menu', ('&Panels', ['$panels', '---', 'toggle_all_panels'])),
    ('help_menu', ('&Help', ['help']))
])

NEW_ELEMENT_EMBED = 'new_element_embed'
NEW_ELEMENT_MARKER = 'new_element_marker'
EDGE_LABEL_EMBED = 'edge_label_embed'
STRETCHLINE = 'stretchline'


class UIManager:
    """
    UIManager Keeps track of all UI-related widgets and tries to do the most work to keep
    KatajaMain as simple as possible.
    """

    def __init__(self, main=None):
        self.main = main
        self.scene = main.graph_scene
        self.actions = {}
        self._action_groups = {}
        self._dynamic_action_groups = {}
        self.qt_actions = {}
        self._top_menus = {}

        self._items = {}
        # self.setSceneRect(view.parent.geometry())
        self._message = None
        self._control_points = []
        self._rubber_band = None
        self._rubber_band_origin = None
        self._node_edits = set()
        self.log_writer = MessageWriter()

        self._timer_id = 0
        self._ui_panels = {}
        self.ui_buttons = {}
        self.moving_things = set()
        self.touch_areas = set()
        self.symbols = set()
        self.button_shortcut_filter = ButtonShortcutFilter()

        self.activity_marker = None
        self.ui_activity_marker = None
        self.preferences_dialog = None
        self.color_dialog = None

        # self.hud = HUD(self)
        # self.info('free drawing')

    def populate_ui_elements(self):
        """ These cannot be created in __init__, as individual panels etc. may refer to ctrl.ui,
        which doesn't exist until the __init__  is completed.
        :return:
        """
        # Create actions based on actions.py and menus based on
        self.create_actions()
        # Create top menus, requires actions to exist
        self.create_menus()
        # Create UI panels, requires actions to exist
        self.create_panels()

        self.activity_marker = ActivityMarker('activity')
        self.add_ui(self.activity_marker)
        self.activity_marker.setPos(5, 5)
        self.activity_marker.show()
        self.ui_activity_marker = ActivityMarker('ui_activity')
        self.add_ui(self.ui_activity_marker)
        self.ui_activity_marker.setPos(15, 5)
        self.ui_activity_marker.hide()

    def get_panel(self, panel_id) -> UIPanel:
        """
        :param panel_id: panel key. Probably from constant from globals
        :return: UIPanel instance or None
        """
        return self._ui_panels.get(panel_id, None)

    def get_action_group(self, action_group_name):
        """ Get action group with this name, or create one if it doesn't exist
        :param action_group_name:
        :return:
        """
        if action_group_name not in self._action_groups:
            self._action_groups[action_group_name] = QtWidgets.QActionGroup(self.main)
        return self._action_groups[action_group_name]

    def start_color_dialog(self, receiver, slot_name):
        if not self.color_dialog:
            self.color_dialog = QtWidgets.QColorDialog(self.main)
            self.color_dialog.setOption(QtWidgets.QColorDialog.NoButtons)
        self.color_dialog.show()
        self.color_dialog.setCurrentColor(ctrl.cm.drawing())

    def add_ui(self, item):
        """

        :param item:
        """
        self._items[item.ui_key] = item
        if isinstance(item, QtWidgets.QGraphicsItem):
            self.scene.addItem(item)

    def remove_ui(self, item):
        """

        :param item:
        """
        if item.ui_key in self._items:
            del self._items[item.ui_key]
        if isinstance(item, QtWidgets.QGraphicsItem):
            self.scene.removeItem(item)

    def get_ui(self, ui_key):
        """ Return a managed ui item
        :param ui_key:
        :return:
        """
        return self._items.get(ui_key, None)

    def store_panel_positions(self):
        """


        """
        self._panel_positions = {}
        for panel_id, panel in self._ui_panels.items():
            self._panel_positions[panel_id] = panel.geometry()
            # self.log_panel.setGeometry(0, self.size().height() - self.log_panel.height(),
            # self.log_panel.width(), self.log_panel.height())

    def update_all_fields(self):
        """


        """
        print('*** ui update_all_fields called ***')
        self.update_field('treeset_counter',
                          '%s/%s' % (self.main.forest_keeper.current_index + 1, len(self.main.forest_keeper.forests)))
        self.update_field('visualization_selector', self.main.forest.visualization.name)

    def update_edge_shapes(self, edge_type, i):
        """

        :param edge_type:
        :param i:
        """
        if edge_type == g.CONSTITUENT_EDGE:
            self.ui_buttons['line_type'].setCurrentIndex(i)
        elif edge_type == g.FEATURE_EDGE:
            self.ui_buttons['feature_line_type'].setCurrentIndex(i)

    def update_field(self, field_name, value):
        """ Delegate updating action to panel that hosts that field
        :param field_name:
        :param value:
        """
        print('update_field for "%s", value: "%s"' % (field_name, value))
        if field_name in self.ui_buttons:
            field = self.ui_buttons[field_name]
            parent = field.parent()
            while (not hasattr(parent, 'update_field')) and parent:
                parent = parent.parent()
            if parent:
                parent.update_field(field_name, field, value)
            else:
                print('did not found field %s from any ui panels' % field_name)
        else:
            print('did not found field %s from any ui panels' % field_name)

    def restore_panel_positions(self):
        """


        """
        for name, panel in self._ui_panels.items():
            if name in self._panel_positions:
                panel.setGeometry(self._panel_positions[name])

    def resize_ui(self, size):
        # self.setSceneRect(0, 0, size.width(), size.height())
        """

        :param size:
        """
        self.activity_marker.setPos(5, 5)
        if self._message:
            self._message.update_position()
        self.update_positions()

    def update_colors(self):
        """


        """
        if self._message:
            self._message.update_color()
        if NEW_ELEMENT_EMBED in self._items:
            self._items[NEW_ELEMENT_EMBED].update_color()

        for panel_key in [g.COLOR_THEME, g.COLOR_WHEEL, g.NODES]:
            panel = self.get_panel(panel_key)
            if panel:
                panel.update_colors()

    def update_selections(self, selected=None, deselected=None):
        """ Many UI elements change mode depending on if object of specific type is selected
        :param selected:
        :param deselected:
        """
        if selected is None:
            selected = ctrl.get_all_selected()
        lp = self.get_panel(g.EDGES)
        if lp:
            lp.selected_objects_changed()
            lp.update_panel()
        lop = self.get_panel(g.LINE_OPTIONS)
        if lop:
            lop.update_panel()
        np = self.get_panel(g.NODES)
        if np:
            np.update_panel()

        if deselected:
            for item in deselected:
                self.update_touch_areas_for(item, False)
                self.update_control_points_for(item, False)
                self.update_overlay_buttons_for(item, False)
        for item in selected:
            self.update_touch_areas_for(item, True)
            self.update_control_points_for(item, True)
            self.update_overlay_buttons_for(item, True)
        self.update_touch_areas()

    # unused, but sane
    def focusable_elements(self):
        """


        """
        for e in self._items:
            if getattr(e, 'focusable', False) and e.isVisible():
                yield e

    def clear_items(self):
        """


        """
        for item in self.symbols:
            self.remove_ui(item)

        self.symbols = set()
        ctrl.deselect_objects()

    @time_me
    def update_positions(self):
        """ UI has elements that point to graph scene elements, and when something moves there
        UI has to update its elements too."""
        for item in self._items.values():
            if hasattr(item, 'update_position'):
                item.update_position()
        # for cp in self._control_points:
        #     cp.update_position()
        # for symbol in self.symbols:
        #     symbol.update_position()
        # #for button in self._overlay_buttons.values():
        # #    button.update_position()
        # for touch_area in self.touch_areas:
        #     touch_area.update_position()
        # if NEW_ELEMENT_MARKER in self._items:
        #     self._items[NEW_ELEMENT_MARKER].update_position()
        # for edit in self._node_edits:
        #     edit.update_position()

    def delete_ui_elements_for(self, item):
        """

        :param item:
        """
        self.remove_touch_areas_for(item)
        self.remove_control_points(item)
        if isinstance(item, BaseConstituentNode):
            self.remove_buttons_for_constituent_node(item)
        elif isinstance(item, Edge):
            self.remove_buttons_for_edge(item)

    # ### Actions, Menus and Panels ####################################################

    def create_actions(self):
        """ Build menus and other actions that can be triggered by user based on actions.py"""

        main = self.main
        shortcut_solver = ShortcutSolver(self)

        # dynamic actions are created based on other data e.g. available visualization plugins.
        # they are added into actions as everyone else, but there is a special mapping to find
        # them later.
        # eg. self._dynamic_action_groups['visualizations'] = ['vis_1','vis_2','vis_3'...]
        self._dynamic_action_groups = {}
        self.actions = actions

        i = 0
        self._dynamic_action_groups['visualizations'] = []
        for name, vis in VISUALIZATIONS.items():
            key = action_key(name)
            d = {'command': name,
                 'method': action_methods.change_visualization,
                 'shortcut': vis.shortcut,
                 'checkable': True,
                 'sender_arg': True,
                 'args': [name],
                 'viewgroup': 'visualizations',
                 'exclusive': True}
            self.actions[key] = d
            self._dynamic_action_groups['visualizations'].append(key)

        self._dynamic_action_groups['panels'] = []
        for panel_key, panel_data in PANELS.items():
            key = 'toggle_panel_%s' % panel_key
            d = {'command': panel_data['name'],
                 'method': action_methods.toggle_panel,
                 'checkable':  True,
                 'viewgroup': 'Panels',
                 'args': [panel_key],
                 'undoable': False,
                 'exclusive': False,
                 'tooltip': "Close this panel"}
            self.actions[key] = d
            self._dynamic_action_groups['panels'].append(key)
        # ## Create actions
        self._action_groups = {}
        self.qt_actions = {}

        for key, data in self.actions.items():
            action = KatajaAction(key, **data)
            self.qt_actions[key] = action
            main.addAction(action)

    def create_menus(self):
        """ Put actions to menus. Menu structure is defined at the top of this file.
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
                    exp_items += self._dynamic_action_groups[item[1:]]
                elif isinstance(item, tuple):
                    exp_items.append(expand_list(item))
                else:
                    exp_items.append(item)
            return (label, exp_items)

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
        """ Put actions to panels. Panel contents are defined at the top of this file.
        :return: None
        """
        self._ui_panels = {}
        for panel_key in panel_order:
            data = PANELS[panel_key]
            if not data.get('closed', False):
                self.create_panel(panel_key, **data)

    def create_panel(self, id, name='', position=None, folded=False, default=False, **kwargs):
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
        new_panel = constructor(name, id, default_position=position, parent=self.main,
                                ui_manager=self, folded=folded)
        self._ui_panels[id] = new_panel
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

    # ### Label edge editin dialog #########################################################

    def start_edge_label_editing(self, edge):
        """

        :param edge:
        """
        lp = edge.label_item.pos()
        if EDGE_LABEL_EMBED not in self._items:
            embed = EdgeLabelEmbed(self.main.graph_view, self, EDGE_LABEL_EMBED)
            self.add_ui(embed)
        else:
            embed = self._items[EDGE_LABEL_EMBED]
        embed.update_embed(scenePos=lp, edge=edge)
        embed.wake_up()

    # ### Creation dialog #########################################################

    def create_creation_dialog(self, scenePos):
        """

        :param scenePos:
        """
        embed = self.get_ui(NEW_ELEMENT_EMBED)
        marker = self.get_ui(NEW_ELEMENT_MARKER)
        if not embed:
            embed = NewElementEmbed(self.main.graph_view, self, NEW_ELEMENT_EMBED)
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
        """
        :param node_key:
        """
        self.remove_ui(embed)
        self._node_edits.remove(embed)

    # ### Touch areas #####################################################################

    def create_touch_area(self, host=None, type=''):
        """


        :param type:
        :param host:
        :return:
        """
        ui_key = host.save_key + '_ta_' + str(type)
        if ui_key in self._items:
            print('skip ta creation: it already exists')
            return self._items[ui_key]
        ta = TouchArea(host, type, ui_key)
        self.touch_areas.add(ta)
        self.add_ui(ta)
        return ta

    def delete_touch_area(self, touch_area):
        """ remove from scene and remove references from nodes
        :param touch_area:
        """
        self.touch_areas.remove(touch_area)
        self.remove_ui(touch_area)

    def remove_touch_areas(self):
        """


        """
        for ta in list(self.touch_areas):
            self.delete_touch_area(ta)

    def remove_touch_areas_for(self, host):
        """

        :param host:
        """
        my_areas = [x for x in self.touch_areas if x.host is host]
        for ta in my_areas:
            self.delete_touch_area(ta)

    def update_touch_areas(self):
        """


        """
        self.remove_touch_areas()
        for item in ctrl.get_all_selected():
            self.update_touch_areas_for(item, True)

    def update_touch_areas_for(self, item, selected=True):
        """

        :param item: object to update
        :param selected: is item being selected or deselected
        """
        if selected and item.visible:
            if isinstance(item, BaseConstituentNode):
                if item.is_root_node():
                    self.create_touch_area(item, g.LEFT_ADD_ROOT)
                    self.create_touch_area(item, g.RIGHT_ADD_ROOT)
                if not item.is_placeholder():
                    for edge in item.get_edges_up(visible=True):
                        self.create_touch_area(edge, g.LEFT_ADD_SIBLING)
                        self.create_touch_area(edge, g.RIGHT_ADD_SIBLING)
            elif isinstance(item, Edge) and item.edge_type == g.CONSTITUENT_EDGE:
                if item.has_orphan_ends():
                    if item.end and (item.end.is_placeholder()):
                        self.add_completion_suggestions(item.end)
                    if item.start and (item.start.is_placeholder()):
                        self.add_completion_suggestions(item.start)
                else:
                    self.create_touch_area(item, g.LEFT_ADD_SIBLING)
                    self.create_touch_area(item, g.RIGHT_ADD_SIBLING)
        else:
            self.remove_touch_areas_for(item)

    def add_completion_suggestions(self, node):
        """ Node has selected and if it is a placeholder or otherwise lacking, it may suggest an
         option to add a proper node here.
        :param node: any node
        :return:
        """
        if node.is_placeholder():
            self.create_touch_area(node, g.TOUCH_ADD_CONSTITUENT)

    def remove_completion_suggestins(self, node):
        """ Completion suggestions may be there even if the node is complete, as it can be completed
        after it has been selected.
        :param node: any node
        :return:
        """
        self.remove_touch_areas_for(node)

    def prepare_touch_areas_for_dragging(self, drag_host=None, moving=None, node_type='',
                                         multidrag=False):
        """
        :param drag_host: node that is being dragged
        :param moving: set of moving nodes (does not include drag_host)
        :param node_type: If the node doesn't exist yet, node_type can be given as a hint of what to expect
        """
        self.remove_touch_areas()
        if multidrag:
            return
        if not moving:
            moving = []
        if not node_type:
            node_type = drag_host.node_type
        if node_type == g.CONSTITUENT_NODE:
            for root in ctrl.forest.roots:
                if root in moving or root is drag_host:
                    continue
                self.create_touch_area(root, g.LEFT_ADD_ROOT)
                self.create_touch_area(root, g.RIGHT_ADD_ROOT)
            for edge in ctrl.forest.get_constituent_edges():
                if edge.start in moving or edge.end in moving or edge.start is drag_host or \
                   edge.end is drag_host:
                    continue
                self.create_touch_area(edge, g.LEFT_ADD_SIBLING)
                self.create_touch_area(edge, g.RIGHT_ADD_SIBLING)
            for node in ctrl.forest.get_constituent_nodes():
                if node.is_placeholder():
                    self.create_touch_area(node, g.TOUCH_ADD_CONSTITUENT)
        else:
            if node_type == g.FEATURE_NODE:
                touch_area_type = g.TOUCH_CONNECT_FEATURE
            elif node_type == g.GLOSS_NODE:
                touch_area_type = g.TOUCH_CONNECT_GLOSS
            elif node_type == g.COMMENT_NODE:
                touch_area_type = g.TOUCH_CONNECT_COMMENT
            for node in ctrl.forest.get_constituent_nodes():
                if node in moving or node is drag_host:
                    continue
                if drag_host and node.is_connected_to(drag_host):
                    continue
                self.create_touch_area(node, touch_area_type)

    # ### Flashing symbols ################################################################

    def show_anchor(self, node):
        """

        :param node:
        """
        assert(node.is_locked())
        ui_key = node.save_key + '_lock_icon'
        item = FadingSymbol(qt_prefs.lock_icon, node, self, ui_key, place='bottom_right')
        # print u"\U0001F512" , unichr(9875) # unichr(9875)
        self.add_ui(item)
        self.symbols.add(item)
        item.fade_out('slow')

    # ### Stretchlines ####################################################################

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

    # def beginRename(self, node):
    # ctrl.selected=node
    # if self.radial_menu:
    # self.radial_menu.close()
    # self.radial_menu=TextEditor(node)
    # self.radial_menu.open()
    # node.label.hide()
    # ctrl.main.disable_actions()

    # ### Messages ####################################################################

    def add_command_feedback(self, msg):
        """ Insert new row of text to message window
        :param msg:
        """
        self.log_writer.add('>>>'+msg)

    def add_message(self, msg):
        """ Insert new row of text to log
        :param msg:
        """
        self.log_writer.add(msg)

    def show_command_prompt(self):
        """ Show '>>>_' in log """
        self.log_writer.add('>>>_')

    # ### Edge buttons ############################

    def _create_overlay_button(self, icon, host, role, key, text, action, size=None):
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
            button = OverlayButton(icon, host, role, key, text, parent=self.main.graph_view,
                                   size=size or 16)
            self.add_ui(button)
            button.update_position()
            self.connect_element_to_action(button, action)
            button.show()

    def _del_button(self, key):
        if key in self._items:
            button = self.get_ui(key)
            button.close()
            button.hide()
            self.remove_ui(button)

    def add_remove_merger_button(self, node):
        """

        :param node:
        :param edge:
        """
        self._create_overlay_button(icon=qt_prefs.delete_icon,
                                    host=node,
                                    role=g.REMOVE_TRIANGLE,
                                    key=node.save_key + g.REMOVE_MERGER,
                                    text='Remove this non-merging node',
                                    action='remove_merger')

    def add_unfold_triangle_button(self, node):
        """

        :param node:
        """
        self._create_overlay_button(icon=qt_prefs.triangle_close_icon,
                                    host=node,
                                    role=g.REMOVE_TRIANGLE,
                                    key=node.save_key + g.REMOVE_TRIANGLE,
                                    text='Reveal nodes inside the triangle',
                                    action='remove_triangle',
                                    size=(48, 24))

    def add_fold_triangle_button(self, node):
        """

        :param node:
        """
        self._create_overlay_button(icon=qt_prefs.triangle_icon,
                                    host=node,
                                    role=g.ADD_TRIANGLE,
                                    key=node.save_key + g.ADD_TRIANGLE,
                                    text='Turn into a triangle',
                                    action='add_triangle',
                                    size=(48, 24))

    def add_buttons_for_edge(self, edge):
        # Constituent edges have a button to remove the edge and the node in between.
        """

        :param edge:
        """
        if edge.edge_type is g.CONSTITUENT_EDGE:
            if edge.end and edge.end.is_placeholder():
                self.add_remove_merger_button(edge.start)
        # Constituent edges don't have cut-button at the start
        else:
            key = edge.save_key + "_cut_start"
            if edge.start:
                self._create_overlay_button(icon=qt_prefs.cut_icon,
                                            host=edge,
                                            role=g.START_CUT,
                                            key=key,
                                            text='Disconnect from node',
                                            action='disconnect_edge')
            else:
                self._del_button(key)
        key = edge.save_key + "_cut_end"
        if edge.end and not edge.end.is_placeholder():
            self._create_overlay_button(icon=qt_prefs.cut_icon,
                                        host=edge,
                                        role=g.END_CUT,
                                        key=key,
                                        text='Disconnect from node',
                                        action='disconnect_edge')
        else:
            self._del_button(key)

    def remove_buttons_for_edge(self, edge):
        """

        :param edge:
        """
        keys = [edge.save_key + "_cut_start", edge.save_key + "_cut_end"]
        if edge.start:
            keys.append(edge.start.save_key + g.REMOVE_MERGER)
        for key in keys:
            self._del_button(key)

    def update_edge_button_positions(self, edge):
        """

        :param edge:
        """
        keys = [edge.save_key + "_cut_start", edge.save_key + "_cut_end"]
        if edge.start:
            keys.append(edge.start.save_key + g.REMOVE_MERGER)
        for key in keys:
            button = self.get_ui(key)
            if button:
                button.update_position()

    def update_overlay_buttons_for(self, item, selected):
        """

        :param item:
        :param selected:
        """
        if isinstance(item, Edge):
            if selected:
                self.add_buttons_for_edge(item)
            else:
                self.remove_buttons_for_edge(item)
        elif isinstance(item, BaseConstituentNode):
            if selected:
                self.remove_buttons_for_constituent_node(item)
                self.add_buttons_for_constituent_node(item)
            else:
                self.remove_buttons_for_constituent_node(item)

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

    def remove_buttons_for_constituent_node(self, node):
        """

        :param node:
        """
        for key_part in [g.REMOVE_MERGER, g.REMOVE_TRIANGLE, g.ADD_TRIANGLE]:
            self._del_button(node.save_key + key_part)

    # ### Control points ####################################################################

    def add_control_points(self, edge):
        """ Display control points for this edge
        :param edge:
        """
        def _add_cp(key, index, role):
            cp = ControlPoint(edge, key, index=index, role=role)
            self.add_ui(cp)
            self._control_points.append(cp)
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

    def update_control_points_for(self, item, selected=True):
        """

        :param item:
        :param selected:
        :return:
        """
        if not isinstance(item, Edge):
            return
        if selected:
            self.add_control_points(item)
        else:
            self.remove_control_points(item)

    def update_control_point_positions(self):
        """ Update positions for all control points without doing any checks to see if they are legit or used.
        We assume that there won't be too many of them
        :return:
        """
        for item in self._control_points:
            if not item.update_position():
                self.remove_ui(item)
                self._control_points.remove(item)
                del item

    def remove_control_points(self, edge):
        """ Removes control points from this edge
        :param edge:
        """
        cps = [cp for cp in self._control_points if cp.host_edge == edge]
        for cp in cps:
            self.remove_ui(cp)
            self._control_points.remove(cp)
            del cp

    def reset_control_points(self, edge):
        """
        :param edge:
        """
        self.remove_control_points(edge)
        if ctrl.is_selected(edge):
            self.add_control_points(edge)

    # ### Timer ########################################################

    def item_moved(self):
        """


        """
        if not self._timer_id:
            self._timer_id = self.startTimer(prefs.fps_in_msec)

    def timerEvent(self, event):
        """

        :param event:
        """
        self.ui_activity_marker.show()
        items_have_moved = False
        for item in self.moving_things:
            if item.move_towards_target_position():
                items_have_moved = True
        if not items_have_moved:
            self.ui_activity_marker.hide()
            self.killTimer(self._timer_id)
            self._timer_id = 0

