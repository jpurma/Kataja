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

from kataja.ConstituentNode import ConstituentNode
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.Edge import Edge
from kataja.ui.ActivityMarker import ActivityMarker
from kataja.ui.ControlPoint import ControlPoint
from kataja.ui.FadingSymbol import FadingSymbol
from kataja.ui.MergeHintLine import MergeHintLine
from kataja.ui.MessageItem import MessageItem
from kataja.ui.RadialMenu import RadialMenu
from kataja.ui.StretchLine import StretchLine
from kataja.ui.TargetReticle import TargetReticle
from kataja.actions import actions
import kataja.globals as g
from kataja.utils import to_tuple, debug_mouse
from kataja.ui.TouchArea import TouchArea
from kataja.ui.panels.ColorThemePanel import ColorPanel
from kataja.ui.panels.ColorWheelPanel import ColorWheelPanel
from kataja.ui.panels.LinesPanel import LinesPanel
from kataja.ui.panels.LogPanel import LogPanel
from kataja.ui.panels.NavigationPanel import NavigationPanel
from kataja.ui.panels.TestPanel import TestPanel
from kataja.ui.panels.VisualizationPanel import VisualizationPanel
from kataja.visualizations.available import VISUALIZATIONS


NOTHING = 0
SELECTING_AREA = 1
DRAGGING = 2
POINTING = 3

panels = [{'id': g.LOG, 'name': 'Log', 'position': 'bottom'},
          {'id': g.TEST, 'name': 'Test', 'position': 'right'},
          {'id': g.NAVIGATION, 'name': 'Trees', 'position': 'right'},
          {'id': g.VISUALIZATION, 'name': 'Visualization', 'position': 'right'},
          {'id': g.COLOR_THEME, 'name': 'Color theme', 'position': 'right'},
          {'id': g.COLOR_WHEEL, 'name': 'Color theme wheel', 'position': 'right', 'folded': True, 'closed': True},
          {'id': g.LINES, 'name': 'Lines', 'position': 'right'}]

panel_classes = {g.LOG: LogPanel, g.TEST: TestPanel, g.NAVIGATION: NavigationPanel, g.VISUALIZATION: VisualizationPanel,
                 g.COLOR_THEME: ColorPanel, g.COLOR_WHEEL: ColorWheelPanel, g.LINES: LinesPanel}


menu_structure = OrderedDict([
    ('file_menu', ('&File', ['open', 'save', 'save_as', '---', 'print_pdf', 'blender_render', '---', 'preferences', '---', 'quit'])),
    ('build_menu', ('&Build', ['next_forest', 'prev_forest', 'next_derivation_step', 'prev_derivation_step'])),
    ('rules_menu', ('&Rules', ['label_visibility', 'bracket_mode', 'trace_mode', 'merge_edge_shape', 'feature_edge_shape', 'merge_order_attribute', 'select_order_attribute'])),
    ('view_menu', ('&View', ['$visualizations', '---', 'change_colors', 'adjust_colors', 'zoom_to_fit', '---', 'fullscreen_mode'])),
    ('panels_menu', ('&Panels', ['$panels', '---', 'toggle_all_panels'])),
    ('help_menu', ('&Help', ['help']))
])

class UIManager:
    """
    UIManager Keeps track of all UI-related widgets and tries to do the most work to keep KatajaMain as simple as possible.
    """
    saved_fields = ['main', 'scene']
    singleton_key = 'UIManager'

    def __init__(self, main=None):
        self.main = main
        self.scene = main.graph_scene
        self.actions = {}
        self._action_groups = {}
        self._dynamic_action_groups = {}
        self.qt_actions = {}
        self._top_menus = {}

        self._items = set()
        # self.setSceneRect(view.parent.geometry())
        self._merge_hint = None
        self._stretchline = None
        self._message = None
        self._radial_menus = []
        self._control_points = []
        self._target_reticle = None
        self._rubber_band = None
        self._rubber_band_origin = None
        self._timer_id = 0
        self._ui_panels = {}
        self.ui_buttons = {}
        self.moving_things = set()
        self.touch_areas = set()
        self.symbols = set()

        ## Create actions based on actions.py and menus based on
        self.create_actions()
        ## Create top menus, requires actions to exist
        self.create_menus()
        ## Create UI panels, requires actions to exist
        self.create_panels()

        self.activity_marker = ActivityMarker(self)
        self.add_ui(self.activity_marker)
        self.activity_marker.setPos(5, 5)
        self.activity_marker.show()
        self.ui_activity_marker = ActivityMarker(self)
        self.add_ui(self.ui_activity_marker)
        self.ui_activity_marker.setPos(15, 5)
        self.ui_activity_marker.hide()
        self.preferences_dialog = None
        self.hud = None

        # self.hud = HUD(self)
        # self.info('free drawing')


    # def parseConstituentNodebox(self, escaped=False, finish=False):
    # text=unicode(self.nodebox.get_value())
    # tree=ctrl.forest.add_root(text=text, pos=self.nodebox.pos(), replace=False)
    # ctrl.action_finished()
    #
    # if finish and tree:
    # self.abortConstituentNodebox()
    # ctrl.action_finished()

    def get_panel(self, panel_id):
        return self._ui_panels[panel_id]

    def toggle_panel(self, panel_id):
        """
        UI action.
        :return:
        """
        panel = self.get_panel(panel_id)
        if panel.isVisible():
            panel.close()
        else:
            panel.setVisible(True)
            panel.set_folded(False)

    def toggle_fold_panel(self, panel_id):
        panel = self.get_panel(panel_id)
        panel.set_folded(not panel.folded)

    def pin_panel(self, panel_id):
        panel = self.get_panel(panel_id)
        panel.pin_to_dock()

    def add_ui(self, item):
        """

        :param item:
        """
        self._items.add(item)
        self.scene.addItem(item)

    def remove_ui(self, item):
        """

        :param item:
        """
        self._items.remove(item)
        self.scene.removeItem(item)

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
        self.update_field('treeset_counter',
                          '%s/%s' % (self.main.forest_keeper.current_index() + 1, self.main.forest_keeper.size()))
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
        field = self.ui_buttons[field_name]
        parent = field.parent()
        while (not hasattr(parent, 'update_field')) and parent:
            parent = parent.parent()
        if parent:
            parent.update_field(field_name, field, value)
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
        if self.hud:
            self.hud.update_color()
        self._ui_panels[g.COLOR_THEME].update_colors()
        self._ui_panels[g.COLOR_WHEEL].update_colors()

    def update_selections(self):
        """


        """
        self.update_touch_areas()

    # unused, but sane
    def focusable_elements(self):
        """


        """
        for e in self._items:
            if getattr(e.focusable) and e.isVisible():
                yield e


    def clear_items(self):
        """


        """
        for menu in self._radial_menus:
            menu.close(immediately=True)
        if self._target_reticle:
            self._target_reticle.hide()
        for item in self.symbols:
            self.remove_ui(item)

        self.symbols = set()
        ctrl.deselect_objects()
        ctrl.release_focus()

    def update_positions(self):
        """ UI has elements that point to graph scene elements, and when something moves there
        UI has to update its elements too."""
        if self._target_reticle:
            self._target_reticle.update_position()
        for menu in self._radial_menus:
            menu.update_position()
        for cp in self._control_points:
            cp.update_position()
        for symbol in self.symbols:
            symbol.update_position()

    def delete_ui_elements_for(self, item):
        """

        :param item:
        """
        if hasattr(item, 'touch_areas'):
            for touch_area in list(item.touch_areas.values()):
                self.delete_touch_area(touch_area)


    def filter_active_items_from(self, items, x, y):
        """

        :param items:
        :param x:
        :param y:
        :return:
        """
        candidates = []
        for item in items:
            if isinstance(item, RadialMenu):
                for nitem in item.menu_items:
                    if nitem.enabled and nitem.sceneBoundingRect().contains(x, y):
                        candidates.append(nitem)
            elif item in self._items:
                candidates.append(item)
        return candidates


    # ### Actions, Menus and Panels ####################################################

    def create_actions(self):
        """ Build menus and other actions that can be triggered by user based on actions.py"""

        main = self.main

        # dynamic actions are created based on other data e.g. available visualization plugins.
        # they are added into actions as everyone else, but there is a special mapping to find them later.
        # eg. self._dynamic_action_groups['visualizations'] = ['vis_1','vis_2','vis_3'...]
        self._dynamic_action_groups = {}
        self.actions = actions

        i = 0
        self._dynamic_action_groups['visualizations'] = []
        for name, vis in VISUALIZATIONS.items():
            i += 1
            key = 'vis_%s' % i
            self.actions[key] = {'command': name, 'method': 'change_visualization_command', 'shortcut': vis.shortcut,
                      'checkable': True, 'action_group': 'visualizations'}
            self._dynamic_action_groups['visualizations'].append(key)

        self._dynamic_action_groups['panels'] = []
        for panel_data in panels:
            key = 'toggle_panel_%s' % panel_data['id']
            self.actions[key] = {'command': panel_data['name'], 'method': 'toggle_panel', 'checkable': True,
                            'action_group': 'Panels', 'args': [panel_data['id']], 'context': 'ui', 'no_undo': True,
                            'tooltip': "Close this panel"}
            self._dynamic_action_groups['panels'].append(key)
            key = 'toggle_fold_panel_%s' % panel_data['id']
            self.actions[key] = {'command': 'Fold %s' % panel_data['name'], 'method': 'toggle_fold_panel', 'checkable': True,
                            'action_group': 'Panels', 'args': [panel_data['id']], 'context': 'ui', 'no_undo': True,
                            'tooltip': "Minimize this panel"}
            key = 'pin_panel_%s' % panel_data['id']
            self.actions[key] = {'command': 'Pin to dock %s' % panel_data['name'], 'method': 'pin_panel',
                            'action_group': 'Panels', 'args': [panel_data['id']], 'context': 'ui', 'no_undo': True,
                            'tooltip': "Pin to dock"}


        # ## Create actions
        self._action_groups = {}
        self.qt_actions = {}

        for key, data in self.actions.items():
            act = QtWidgets.QAction(data['command'], main)
            # noinspection PyUnresolvedReferences
            act.triggered.connect(main.action_triggered)
            act.setData(key)
            shortcut = data.get('shortcut', None)
            if shortcut:
                act.setShortcut(QtGui.QKeySequence(shortcut))
                act.setShortcutContext(QtCore.Qt.ApplicationShortcut)
            viewgroup = data.get('viewgroup', None)
            if viewgroup:
                if viewgroup not in self._action_groups:
                    self._action_groups[viewgroup] = QtWidgets.QActionGroup(main)
                act.setActionGroup(self._action_groups[viewgroup])
            checkable = data.get('checkable', None)
            if checkable:
                act.setCheckable(True)
            tooltip = data.get('tooltip', None)
            if tooltip:
                act.setToolTip(tooltip)
                act.setStatusTip(tooltip)
            self.qt_actions[key] = act


    def create_menus(self):
        """ Put actions to menus. Menu structure is defined at the top of this file.
        :return: None
        """
        def add_menu(parent, data):
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
        for panel in panels:
            id = panel['id']
            print(id)
            constructor = panel_classes[id]
            name = panel['name']
            position = panel.get('position', None)
            folded = panel.get('folded', False)
            print("Creating panel type ", constructor)
            new_panel = constructor(name, id,  default_position=position, parent=self.main, ui_manager=self,
                                    folded=folded)
            self._ui_panels[id] = new_panel
            # use action to toggle panel visible or hidden, so that menu gets updated properly
            new_panel.get_visibility_action().setChecked(not panel.get('closed', False))


    # ### Touch areas #####################################################################


    def create_touch_area(self, host=None, type='', for_dragging=False):
        """

        :param host:
        :param place:
        :param for_dragging:
        :return:
        """
        assert (not host.get_touch_area(type))
        ta = TouchArea(host, type, for_dragging)
        host.add_touch_area(ta)
        self.touch_areas.add(ta)
        self.add_ui(ta)
        return ta


    def delete_touch_area(self, touch_area):
        """ remove from scene and remove references from nodes
        :param touch_area:
        """
        touch_area.host.remove_touch_area(touch_area)
        self.touch_areas.remove(touch_area)
        self.remove_ui(touch_area)


    def remove_touch_areas(self):
        """


        """
        for ta in list(self.touch_areas):
            self.delete_touch_area(ta)

    def update_touch_areas(self):
        """


        """
        self.remove_touch_areas()
        for item in ctrl.get_all_selected():
            if isinstance(item, ConstituentNode):
                if item.is_root_node():
                    self.create_touch_area(item, g.LEFT_ADD_ROOT)
                    self.create_touch_area(item, g.RIGHT_ADD_ROOT)
                for edge in item.get_edges_up():
                    self.create_touch_area(edge, g.LEFT_ADD_SIBLING)
                    self.create_touch_area(edge, g.RIGHT_ADD_SIBLING)
            elif isinstance(item, Edge) and item.edge_type == g.CONSTITUENT_EDGE:
                self.create_touch_area(item, g.LEFT_ADD_SIBLING)
                self.create_touch_area(item, g.RIGHT_ADD_SIBLING)


    # ### Flashing symbols ################################################################


    def show_anchor(self, node):
        """

        :param node:
        """
        assert node.locked_to_position
        item = FadingSymbol(qt_prefs.lock_icon, node, self, place='bottom_right')
        # print u"\U0001F512" , unichr(9875) # unichr(9875)
        self.add_ui(item)
        self.symbols.add(item)
        item.fade_out('slow')

    # ### Radial menus ####################################################################

    def remove_menu(self, menu):
        """

        :param menu:
        """
        if menu in self._radial_menus:
            self._radial_menus.remove(menu)
        self.remove_ui(menu)

    def create_menu(self, host, actions=None, shape='ring', radius=100):
        """

        :param host:
        :param actions:
        :param shape:
        :param radius:
        :return:
        """
        if not actions:
            actions = []
        menu = RadialMenu(host, actions, shape, radius)
        self.add_ui(menu)
        self._radial_menus.append(menu)
        return menu

    def trigger_menu(self):
        """


        """
        assert False

    def get_menus(self):
        """


        :return:
        """
        return [menu for menu in self._radial_menus if menu.isVisible()]

    def close_menus(self):
        """


        """
        for menu in self._radial_menus:
            menu.close()

            # ctrl.ui.creation_menu=RadialMenu(ctrl.ui, 'creation', [
            # self.action('Text', ctrl.ui.trigger_menu, menu_type= 'TextArea'),
            # self.action('Add new comment box', self.add_text_box, local_shortcut= 'a',menu_type= 'RadioButton'),
            # self.action('Add new Constituent', self.add_new_constituent, local_shortcut= 'c',menu_type= 'RadioButton',checked=True),
            # self.action('Add new Tree', self.add_new_tree, local_shortcut= 't',menu_type= 'RadioButton')
            # ])
            # ctrl.ui.rename_menu=RadialMenu(ctrl.ui, 'rename', [
            # self.action('Text', ctrl.ui.trigger_menu, menu_type= 'TextArea'),
            # ])


    # ### Stretchlines ####################################################################

    def begin_stretchline(self, start, end):
        """

        :param start:
        :param end:
        """
        if not self._stretchline:
            line = QtCore.QLineF(start, end)
            self._stretchline = StretchLine(line)  # QtGui.QGraphicsLineItem(line)
            self._stretchline.setPen(ctrl.cm.ui())
            self.add_ui(self._stretchline)
        else:
            line = self._stretchline.line()
            line.setPoints(start, end)
            self._stretchline.setLine(line)
        self._stretchline.show()

    def draw_stretchline(self, end):
        """

        :param end:
        """
        if self._stretchline:
            line = self._stretchline.line()
            line.setP2(end)
            self._stretchline.setLine(line)

    def end_stretchline(self):
        """


        :return:
        """
        if not self._stretchline:
            return
        if self._stretchline:
            self._stretchline.hide()
        self.remove_ui(self._stretchline)
        self._stretchline = None

    # def beginRename(self, node):
    # ctrl.selected=node
    # if self.radial_menu:
    # self.radial_menu.close()
    # self.radial_menu=TextEditor(node)
    # self.radial_menu.open()
    # node.label.hide()
    # ctrl.main.disable_actions()


    # ### Messages ####################################################################

    def add_feedback_from_command(self, msg):
        """ Insert new row of text to message window
        :param msg:
        """
        if not self._message:
            self._message = MessageItem('>>>' + msg)
            self.add_ui(self._message)
        else:
            self._message.add_feedback_from_command(msg)

    def add_message(self, msg):
        """ Insert new row of text to message window
        :param msg:
        """

        if not self._message:
            if g.LOG in self._ui_panels:
                message_area = self._ui_panels[g.LOG].widget()
                print('Creating messages to: ', message_area)
                self._message = MessageItem(msg, message_area, self)
                self.add_ui(self._message)
            else:
                print("what happened to 'Log' panel?")
                quit()
        else:
            self._message.add(msg)

    def get_message(self):
        """


        """
        self._message.display_message()

    def show_command_prompt(self):
        """


        """
        self._message.show_next_query()

    def info(self, msg):
        """

        :param msg:
        """
        self.hud.setText(msg)

    # ### Target reticle ####################################################################

    def is_target_reticle_over(self, node):
        """

        :param node:
        :return:
        """
        return self._target_reticle and self._target_reticle.is_over(node)

    def update_target_reticle_position(self):
        """


        """
        self._target_reticle.update_position()

    def draw_target_reticle(self, node):
        """

        :param node:
        """
        if not self._target_reticle:
            self._target_reticle = TargetReticle(node)
            self.add_ui(self._target_reticle)
        else:
            self._target_reticle.update_host(node)
            self._target_reticle.update_position()
            self._target_reticle.show()

    def hide_target_reticle(self, node):
        """

        :param node:
        """
        if self.is_target_reticle_over(node):
            self._target_reticle.hide()


    # ### Merge hint ####################################################################

    def begin_merge_hint(self, start_node, end_item):
        """

        :param start_node:
        :param end_item:
        """
        self._merge_hint = MergeHintLine(start_node, end_item)
        self.add_ui(self._merge_hint)
        self._merge_hint.show()

    def end_merge_hint(self):
        """


        :return:
        """
        if not self._merge_hint:
            return
        self._merge_hint.hide()
        self.remove_ui(self._merge_hint)
        self._merge_hint = None

    def dragging_node_over_position(self, node, scenepos, scene):
        # calculate closest edge under mouse pointer
        """

        :param node:
        :param scenepos:
        :param scene:
        :return:
        """
        edge = None
        if self._merge_hint:
            min_d = 100
        else:
            min_d = 20
        if self._merge_hint:
            item = self._merge_hint.end
            pos = getattr(item, 'middle_point', item.pos())
            d = (pos - scenepos).manhattanLength()
            if d < min_d:
                min_d = d
                edge = item
        for item in scene.items(scenepos):
            if isinstance(item, Edge) and (item.role == 'left_merge' or item.role == 'right_merge'):
                if item.source == node or item.dest == node:
                    continue
                d = (item.middle_point - scenepos).manhattanLength()
                if d < min_d:
                    min_d = d
                    edge = item
            elif isinstance(item, ConstituentNode) and item is not node and item.is_root_node():
                d = (item.pos() - scenepos).manhattanLength()
                if d < min_d:
                    min_d = d
                    edge = item
        if not edge:
            self.end_merge_hint()
            return
        if not self._merge_hint:
            self.begin_merge_hint(node, edge)
        return edge


    # ### Control points ####################################################################

    def add_control_points(self, edge):
        """ Display control points for this edge
        :param edge:
        """
        for i, adjust in enumerate(edge.adjust):
            point = edge.control_points[i]
            if point:
                cp = ControlPoint(edge, index=i, point=point, adjust=adjust)
                self.add_ui(cp)
                assert (cp not in self._control_points)
                self._control_points.append(cp)
                cp.update_position()

    def hide_control_points(self, edge):
        """

        :param edge:
        """
        for cp in self._control_points:
            if cp.host_edge == edge:
                cp.hide()

    def show_control_points(self, edge):
        """

        :param edge:
        """
        for cp in self._control_points:
            if cp.host_edge == edge:
                cp.show()

    def remove_control_points(self, edge):
        """ Removes control points from this edge
        :param edge:
        """
        cps = [cp for cp in self._control_points if cp.host_edge == edge]
        for cp in cps:
            # print 'removing ', cp
            self.remove_ui(cp)
            self._control_points.remove(cp)
            del cp

    def reset_control_points(self, edge):
        """

        :param edge:
        """
        edges = [x.host_edge for x in self._control_points]
        if edge in edges:
            # print 'reseting control points'
            self.remove_control_points(edge)
            self.add_control_points(edge)

    # ######### MOUSE ########################################################

    def mouse_press_event(self, item, event):
        """ UIManager is interested in setting focus and sending clicks to UI elements. GraphScene should send an item here and depending on what kind of object it is, we take focus or
            redelegate click to child object.
        :param item:
        :param event:
            """
        # print type(event)
        # print self.itemAt(event.scenePos())
        debug_mouse('mouse_press_event at UIManager')
        drag = getattr(item, 'draggable', False)
        focus = getattr(item, 'focusable', False)
        if drag or focus:
            if isinstance(item, RadialMenu):
                debug_mouse('clicked child item of RadialMenu')
                for child in item.childItems():
                    if child.sceneBoundingRect().contains(event.scenePos()):
                        child.pressed = True
                        ctrl.ui_pressed = child
                        if child.focusable and not ctrl.has_focus(child):
                            ctrl.take_focus(child)
                        return True
            if focus and not ctrl.has_focus(item):
                ctrl.take_focus(item)
            item.pressed = True
            ctrl.ui_pressed = item
            return True
        return False


    def mouse_move_event(self, event):
        """

        :param event:
        :return:
        """
        ui_pressed = ctrl.ui_pressed
        if not ctrl.has_focus(ui_pressed):
            return False
        else:
            if getattr(ui_pressed, 'draggable', False):
                ui_pressed.drag(event)
                return True

    def mouse_release_event(self, event):
        """ This reacts only when ui_pressed -flag is on.

        :param event:
            """
        debug_mouse('ui mouseReleaseEvent', ctrl.watch_for_drag_end)
        if ctrl.watch_for_drag_end:
            debug_mouse("ending drag at UIManager. shouldn't be done here")
            x, y = to_tuple(event.scenePos())
            pressed = ctrl.pressed
            if pressed:
                pressed.drop_to(x, y)
            self.main.graph_scene.kill_dragging()
        elif ctrl.ui_pressed:
            item = ctrl.ui_pressed
            debug_mouse('release on ui item ', item)
            if ctrl.has_focus(item):
                item.pressed = False
                consume = item.click(event)
                debug_mouse('click on ', item)
                item.update()
                ctrl.ui_pressed = None
                ctrl.dragged = set()
                ctrl.dragged_positions = set()
                return consume
        return False

    def drag_over(self, event):
        """

        :param event:
        """
        pos = event.scenePos()
        for ta in self.touch_areas:
            ta.toggle_hovering(ta.sensitive_area().contains(pos))


    def drop_item_to(self, pressed, event):
        """ Check if any of the UI items is ready to accept dropped item
        :param pressed:
        :param event:
        """
        x, y = to_tuple(event.scenePos())
        for ma in self.touch_areas:
            if ma.sensitive_area().contains(x, y):
                closest_touch_area = ma
                break
        if closest_touch_area:
            success = closest_touch_area.drop(pressed)
            if success:
                f = self.main.forest
                f.chain_manager.rebuild_chains()
                if not f.settings.use_multidomination:
                    f.multidomination_to_traces()
                return True
        return False


    #### Timer ########################################################

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




