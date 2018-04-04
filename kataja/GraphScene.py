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
import time
from itertools import chain

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtCore import Qt

import kataja.globals as g
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.utils import to_tuple, open_symbol_data, time_me, caller
from kataja.saved.Edge import Edge
from kataja.saved.movables.Node import Node


# from BlenderExporter import export_visible_items

class GraphScene(QtWidgets.QGraphicsScene):
    """ QGraphicsScene does lots of work managing all QGraphicsItems, here are some additional
    bookkeeping and measuring related to graphicsitems. Also the timer used here (see
    timerEvent) is the main loop for moving nodes and iterating force graph steps.
    """

    def __init__(self, main=None, graph_view=None, graph_scene=None):
        """ GraphicsScene contains graph elements.
        It is associated with view-widget to display it. """
        QtWidgets.QGraphicsScene.__init__(self)
        self.main = main
        self.graph_view = graph_view

        self.setItemIndexMethod(QtWidgets.QGraphicsScene.NoIndex)
        self.setSceneRect(-300, -200, 600, 400)
        if ctrl.cm.gradient:
            self.setBackgroundBrush(ctrl.cm.gradient)
        else:
            self.setBackgroundBrush(qt_prefs.no_brush)
        self._timer_id = 0
        self._fade_timer_id = 0
        self.timer_counter = 0
        self._fade_steps = 0
        self._fade_steps_list = []
        self.manual_zoom = False
        self.match_final_derivation_size = False
        self._cached_visible_rect = None
        self.keep_updating_visible_area = False
        # self.focusItemChanged.connect(self.inspect_focus_change)
        self.setStickyFocus(True)

    #    def inspect_focus_change(self, new, old, reason):
    #        print('focus changed. new: %s old: %s reason: %s, sender: %s' % (new, old, reason,
    #                                                                    self.sender()))

    def late_init(self):
        """ Initialization that can be done only when ctrl has all the pieces in place
        :return:
        """
        self.sceneRectChanged.connect(ctrl.ui.update_positions)

    def fit_to_window(self, force=False, zoom_in=True):
        """ Fit all visible items to view window. Resizing may be skipped if there are
        :param force: force resize
        :param zoom_in: do resize when it means that

        """
        mw = prefs.edge_width
        mh = prefs.edge_height
        margins = QtCore.QMarginsF(mw, mh * 2, mw, mh)
        use_current_positions = len(ctrl.forest.nodes) < 10
        vr = self.visible_rect(current=use_current_positions) + margins
        ctrl.forest.optimal_rect = vr
        if force or not self._cached_visible_rect:
            self.graph_view.instant_fit_to_view(vr)
            self._cached_visible_rect = vr
            return
        if vr == self._cached_visible_rect:
            return
        zooming_out = vr.width() > self._cached_visible_rect.width() or vr.height() > \
                                                                        self._cached_visible_rect.height()
        if zooming_out or (zoom_in and (self.keep_updating_visible_area or prefs.auto_zoom)):
            self.graph_view.instant_fit_to_view(vr)
            self._cached_visible_rect = vr

    def fit_to_window_if_needed(self):
        if not (self.match_final_derivation_size or
                self.manual_zoom or
                ctrl.dragged_focus):
            self.fit_to_window()

    @staticmethod
    def visible_rect(current=True):
        """ Counts all visible items in scene and returns QRectF object
         that contains all of them """
        min_width = 200
        min_height = 100
        rect_top = 6000
        rect_bottom = -6000
        rect_left = 6000
        rect_right = -6000
        empty = True
        for node in ctrl.forest.nodes.values():
            if not node:
                continue
            if node.parentItem():
                continue
            if not node.isVisible():
                continue
            empty = False
            left, top, right, bottom = node.scene_rect_coordinates(current)
            rect_left = left if left < rect_left else rect_left
            rect_right = right if right > rect_right else rect_right
            rect_top = top if top < rect_top else rect_top
            rect_bottom = bottom if bottom > rect_bottom else rect_bottom
        if empty:
            return QtCore.QRectF(0, 0, 320, 240)
        sm = ctrl.forest.semantics_manager
        if sm.visible:
            for item in sm.all_items:
                left, top, right, bottom = item.sceneBoundingRect().getCoords()
                rect_left = left if left < rect_left else rect_left
                rect_right = right if right > rect_right else rect_right
                rect_top = top if top < rect_top else rect_top
                rect_bottom = bottom if bottom > rect_bottom else rect_bottom
        width = rect_right - rect_left
        if width < min_width:
            rect_right -= (min_width - width) / 2
            width = min_width
        height = rect_bottom - rect_top
        if height < min_height:
            rect_top -= (min_height - height) / 2
            height = min_height
        return QtCore.QRectF(rect_left, rect_top, width, height)

    @staticmethod
    def print_rect():
        """ A more expensive version of visible_rect, also includes curves of edges. Too slow for
        realtime resizing, but when printing you don't want edges to be clipped.
        :return:
        """
        f = ctrl.forest
        total = QtCore.QRectF()
        for item in chain(f.nodes.values(), f.groups.values(), f.edges.values(), f.semantics_manager.all_items):
            if not item.isVisible():
                continue
            total |= item.sceneBoundingRect()
        if not total:
            total = QtCore.QRectF(0, 0, 320, 240)
        else:
            total.adjust(-5, -5, 15, 10)
        return total

    def item_moved(self):
        """ Starts the animations unless they are running already
        :return: None
        """
        if ctrl.play and not self._timer_id:
            # self.graph_view.setRenderHint(QtGui.QPainter.Antialiasing, on=False)
            # self.graph_view.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, on=False)
            self._timer_id = self.startTimer(prefs._fps_in_msec)
            self.timer_counter = 0

    start_animations = item_moved

    def stop_animations(self):
        """ Stops the move animation timer
        :return: None
        """

        self.killTimer(self._timer_id)
        self._timer_id = 0
        # self.graph_view.setRenderHint(QtGui.QPainter.Antialiasing, on=True)
        # self.graph_view.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, on=True)

    def export_3d(self, path, forest):
        """ deprecated
        :param path:
        :param forest:
        """
        pass
        # export_visible_items(path = path, scene = self, forest = forest,
        # prefs = prefs)

    @staticmethod
    def next_selectable_from_node(node, direction):
        if direction == 'left':
            all_siblings = []
            for parent in node.get_parents(similar=False, visible=True):
                for child in parent.get_children(visible=True, similar=False):
                    all_siblings.append(child)
            if node in all_siblings:
                i = all_siblings.index(node)
                if i:
                    return all_siblings[i - 1]
            return node
        if direction == 'right':
            all_siblings = []
            for parent in node.get_parents(similar=False, visible=True):
                for child in parent.get_children(visible=True, similar=False):
                    all_siblings.append(child)
            if node in all_siblings:
                i = all_siblings.index(node)
                if i < len(all_siblings) - 1:
                    return all_siblings[i + 1]
            return node
        if direction == 'up':
            all_parents = node.get_parents(similar=False, visible=True)
            if all_parents:
                return node.get_edge_to(all_parents[-1])
            else:
                return node
        if direction == 'down':
            all_children = list(node.get_children(visible=True, similar=False))
            if all_children:
                return node.get_edge_to(all_children[0])
            else:
                return node

    @staticmethod
    def next_selectable_from_edge(edge, direction):
        if direction == 'left':
            all_siblings = []
            for child_edge in edge.start.get_edges_down(visible=True):
                all_siblings.append(child_edge)
            i = all_siblings.index(edge)
            if i:
                return all_siblings[i - 1]
            else:
                return edge
        if direction == 'right':
            all_siblings = []
            for child_edge in edge.start.get_edges_down(visible=True):
                all_siblings.append(child_edge)
            i = all_siblings.index(edge)
            if i < len(all_siblings) - 1:
                return all_siblings[i + 1]
            else:
                return edge
        if direction == 'up':
            if edge.start:
                return edge.start
            else:
                return edge
        if direction == 'down':
            if edge.end:
                return edge.end
            else:
                return edge

    def move_selection(self, direction, add_to_selection=False):
        """ Move selection to best candidate
        :param direction:
        """

        def edge_of_set(my_selectables):
            if direction == 'left':
                sortable = [(po[0], po[1], it) for it, po in my_selectables]
                x, y, item = min(sortable)
            elif direction == 'right':
                sortable = [(po[0], po[1], it) for it, po in my_selectables]
                x, y, item = max(sortable)
            elif direction == 'up':
                sortable = [(po[1], po[0], it) for it, po in my_selectables]
                y, x, item = min(sortable)
            elif direction == 'down':
                sortable = [(po[1], po[0], it) for it, po in my_selectables]
                y, x, item = max(sortable)
            else:
                raise KeyError
            return item

        # debugging plotter
        # for item, pos in selectables:
        # x,y = pos
        # el = QtGui.QGraphicsEllipseItem(x-2, y-2, 4, 4)
        # el.setBrush(colors.drawing)
        # self.addItem(el)
        #

        # ############### Absolute left/right/up/down ###############################
        # if nothing is selected, select the edgemost item from given direction
        if not ctrl.selected:
            selectables = [(item, to_tuple(item.sceneBoundingRect().center())) for item in
                           self.items() if hasattr(item, 'select') and item.is_visible()]
            best = edge_of_set(selectables)
            ctrl.select(best)
            return best
        # ################ Relative left/right/up/down #############################
        else:
            if len(ctrl.selected) == 1:
                current = ctrl.get_single_selected()
            else:
                # when there are many selected items, extend it to given direction, from the
                # edgemost item in that direction.
                # this behavior may give odd results, but there may be no intuitive ways how such
                #  a blob of selections should behave.
                selectables = [(item, to_tuple(item.sceneBoundingRect().center())) for item in
                               ctrl.selected if item.is_visible()]
                current = edge_of_set(selectables)
            best = None
            if isinstance(current, Node):
                best = self.next_selectable_from_node(current, direction)
            elif isinstance(current, Edge):
                best = self.next_selectable_from_edge(current, direction)
            if best:
                if add_to_selection:
                    ctrl.add_to_selection(best)
                else:
                    ctrl.select(best)
            return best

    # ######### MOUSE ##############

    def kill_dragging(self):
        """ Remove all flags and temporary things related to dragging """
        if ctrl.dragged_focus:
            ctrl.dragged_focus.finish_dragging()
        ctrl.dragged_text = None
        ctrl.press(None)
        ctrl.set_drag_hovering(None)
        ctrl.main.ui_manager.update_touch_areas()
        self.graph_view.toggle_suppress_drag(False)

    def dragging_over(self, scene_pos):
        """ Dragged kataja object is in this scene position, check if there are items that should
         react by lighting up. Update ctrl.drag_hovering_on to reflect this.
        :param scene_pos:
        :return:
        """
        self.item_moved()
        items = (x for x in self.items(scene_pos) if
                 hasattr(x, 'dragged_over_by') and x is not ctrl.pressed)
        hovering_over_something = False
        for item in items:
            if item.dragged_over_by(ctrl.pressed):
                hovering_over_something = True
                break
        if not hovering_over_something:
            ctrl.set_drag_hovering(None)
        self.main.ui_manager.update_positions()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.isAccepted():
            return
        # No object was pressed -- either clicking on nothing or ending a selection drag

        if self.graph_view.selection_mode:
            # prioritize nodes in multiple selection. e.g. if there are nodes and edges in
            # selected area, select only nodes. If there are multiple edges and no nodes, then
            # take edges
            selection = set()
            for item in self.selectedItems():
                if hasattr(item, 'select'):
                    selectable = item.select(select_area=True)
                    if selectable:
                        selection.add(selectable)

            if event.modifiers() == Qt.ShiftModifier:
                select = ctrl.ui.get_action('add_to_selection')
            else:
                select = ctrl.ui.get_action('select')
                nodes = set()
                for item in selection:
                    if isinstance(item, Node):
                        nodes.add(item)
                if nodes:
                    selection = nodes
            select.run_command(sorted([x.uid for x in selection]), has_params=True)

        # click on empty place means select nothing, unless we are shift+selecting
        elif event.modifiers() != Qt.ShiftModifier:
            select = ctrl.ui.get_action('select')
            select.run_command(None, has_params=True)

    def dragEnterEvent(self, event):
        """ Dragging new nodes from UI items or text snippets from desktop/other programs should
        raise hints of where the dragged object can connect.
        :param event:
        """
        data = event.mimeData()
        if data.hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        elif data.hasFormat("text/plain"):
            event.acceptProposedAction()
            command_identifier, *args = data.text().split(':')
            if command_identifier == 'kataja' and args:
                command, *args = args
                if command == "new_node":
                    node_type = args[0]
                    if node_type.isdigit():
                        node_type = int(node_type)
                    ctrl.dragged_text = node_type
                    ctrl.ui.prepare_touch_areas_for_dragging()
                else:
                    print('received unknown command:', command, args)

    def dragLeaveEvent(self, event):
        """ Clean up drag hints
        :param event:
        """
        ctrl.ui.remove_touch_areas()
        return QtWidgets.QGraphicsScene.dragLeaveEvent(self, event)

    def dropEvent(self, event):
        """ Support dragging of items from their panel containers, e.g. symbols from symbol panel
        or new nodes from nodes panel.
        :param event:
        """
        event.ignore()
        QtWidgets.QGraphicsScene.dropEvent(self, event)
        message = ""
        if not event.isAccepted():
            data = event.mimeData()
            event.accept()
            if data.hasFormat("application/x-qabstractitemmodeldatalist"):
                data = open_symbol_data(event.mimeData())
                if data and 'char' in data:
                    event.acceptProposedAction()
                    if ctrl.free_drawing_mode:
                        node = ctrl.free_drawing.create_node(pos=event.scenePos(),
                                                             node_type=g.CONSTITUENT_NODE,
                                                             label=data['char'])
                        node.current_position = event.scenePos().x(), event.scenePos().y()
                        node.lock()
                        message = 'Created constituent "%s"' % node
                    else:
                        node = ctrl.free_drawing.create_comment_node(text=data['char'])
                        node.current_position = event.scenePos().x(), event.scenePos().y()
                        node.lock()
                        message = 'Added "%s" as comment since we are in derivation mode and ' \
                                  'cannot change trees' % data['char']

            elif data.hasFormat("text/plain"):
                event.acceptProposedAction()
                command_identifier, *args = data.text().split(':')
                if command_identifier == 'kataja' and args:
                    command, *args = args
                    if command == "new_node":
                        node_type = args[0]
                        try:
                            node_type = int(node_type)
                        except TypeError:
                            pass
                        node = ctrl.free_drawing.create_node(pos=event.scenePos(),
                                                             node_type=node_type)
                        node.current_position = event.scenePos().x(), event.scenePos().y()
                        if node_type != g.CONSTITUENT_NODE:
                            node.lock()
                        message = 'added %s' % args[0]
                    else:
                        print('received unknown command:', command, args)
                else:
                    text = data.text().strip()
                    if ctrl.free_drawing_mode:
                        node = ctrl.forest.simple_parse(text)
                        message = 'Added tree based on "%s".' % text
                    else:
                        node = ctrl.free_drawing.create_comment_node(text=text)
                        message = 'Added text as comment node since we are in derivation mode ' \
                                  'and cannot change trees.'
            elif data.hasUrls():
                for url in data.urls():
                    path = url.toString()
                    if path.endswith(('png', 'jpg', 'pdf')):
                        node = ctrl.free_drawing.create_comment_node(pixmap_path=url.toLocalFile())
                        message = 'Added image'

        ctrl.ui.remove_touch_areas()
        if message:
            ctrl.forest.forest_edited()
            ctrl.main.action_finished(message)

    def dragMoveEvent(self, event):
        """ Support dragging of items from their panel containers, e.g. symbols from symbol panel
        or new nodes from nodes panel.
        :param event:
        """
        event.ignore()
        QtWidgets.QGraphicsScene.dragMoveEvent(self, event)
        if not event.isAccepted():
            data = event.mimeData()
            event.accept()
            if data.hasFormat("application/x-qabstractitemmodeldatalist") or data.hasFormat(
                    "text/plain"):
                event.acceptProposedAction()
            elif data.hasUrls():
                images = True
                for url in data.urls():
                    if not url.toString().endswith(('png', 'jpg', 'pdf')):
                        images = False
                if images:
                    event.acceptProposedAction()

    def mouseDoubleClickEvent(self, event):
        """ If doubleclicking an empty spot, open creation menu. If doubleclicking an object,
        it may or may not do something with it.
        :param event: some kind of mouse event?
        :return: None
        """
        super().mouseDoubleClickEvent(event)
        if not event.isAccepted():
            ctrl.ui.create_creation_dialog(event.scenePos())

    # ### Timer loop
    # #################################################################

    def fade_background_gradient(self, old_base_color, new_base_color):
        """ Fade between colors of two canvases to smoothen the change. Call this only if colors
        are different and this is worth the effort.
        :param old_base_color: QColor
        :param new_base_color: QColor
        """
        self._fade_steps = 7
        if not self._fade_timer_id:
            self._fade_timer_id = self.startTimer(prefs._fps_in_msec)

        self._fade_steps_list = []
        oh, os, ov, oa = old_base_color.getHsvF()
        nh, ns, nv, na = new_base_color.getHsvF()
        if oh < 0:
            oh = 0
        if nh < 0:
            nh = 0
        h_step = (nh - oh) / (self._fade_steps + 1)
        s_step = (ns - os) / (self._fade_steps + 1)
        v_step = (nv - ov) / (self._fade_steps + 1)
        for n in range(self._fade_steps):
            oh += h_step
            os += s_step
            ov += v_step
            color = QtGui.QColor()
            color.setHsvF(oh, os, ov)
            gradient = QtGui.QRadialGradient(0, 0, 300)
            gradient.setSpread(QtGui.QGradient.PadSpread)
            gradient.setColorAt(1, color)
            gradient.setColorAt(0, color.lighter())
            self._fade_steps_list.append(gradient)
        color = QtGui.QColor()
        color.setHsvF(nh, ns, nv)
        gradient = QtGui.QRadialGradient(0, 0, 300)
        gradient.setSpread(QtGui.QGradient.PadSpread)
        gradient.setColorAt(1, color)
        gradient.setColorAt(0, color.lighter())
        self._fade_steps_list.append(gradient)
        self._fade_steps_list.reverse()

    # @time_me
    def timerEvent(self, event):
        """ Main loop for animations and movement in the scene -- calls nodes
        and tells them to update their position
        :param event: timer event? sent by Qt
        """
        event_id = event.timerId()
        if event_id == self._timer_id:
            self.animation_tick()
        elif event_id == self._fade_timer_id:
            self.fade_tick()

    def fade_tick(self):
        if self._fade_steps:
            self.setBackgroundBrush(self._fade_steps_list[self._fade_steps - 1])
            self._fade_steps -= 1
        else:
            self.killTimer(self._fade_timer_id)
            self._fade_timer_id = 0

    def animation_tick(self):
        ctrl.items_moving = True
        f = self.main.forest
        if (not f) or (not f.is_parsed):
            return

        self.timer_counter += 1
        if ctrl.pressed:
            return

        nodes_are_moving = f.move_nodes()

        if not (nodes_are_moving or self.timer_counter > 20):
            self.stop_animations()
            ctrl.items_moving = False
            self.keep_updating_visible_area = False
        self.fit_to_window_if_needed()
