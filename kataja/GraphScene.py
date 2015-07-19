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


from PyQt5.QtCore import Qt
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

from kataja.Edge import Edge
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.nodes.Node import Node
from kataja.utils import to_tuple, sub_xyz, div_xyz, time_me
from kataja.ui import TouchArea
import kataja.globals as g


# from BlenderExporter import export_visible_items
from kataja.nodes.BaseConstituentNode import BaseConstituentNode


class GraphScene(QtWidgets.QGraphicsScene):
    """

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
        # else:
        # self.setBackgroundBrush(QtGui.QBrush(colors.paper))
        self.min_x = 100
        self.max_x = -100
        self.min_y = 100
        self.max_y = -100
        self._timer_id = 0
        self._dblclick = False
        self._dragging = False
        self._fade_steps = 0
        self._left_border = -50
        self._right_border = 50
        self._top_border = -50
        self._bottom_border = 50
        self.manual_zoom = False
        self._cached_visible_rect = None

        # self.ants = []
        # for n in range(0,1000):
        # ant = QtGui.QGraphicsRectItem(0,0,10,10)
        # ant.setPos(random.random()*400-200, random.random()*400-200)
        # #ant.setPen(colors.drawing2)
        # self.addItem(ant)
        # self.ants.append(ant)

        # ### General events ##########

    # def event(self, event):
    # print 's:', event.type()
    # #print 'Scene event received: %s' % event.type()
    # return QtWidgets.QGraphicsScene.event(self, event)

    # ####

    # @time_me
    def fit_to_window(self):
        """ Calls up to graph view and makes it to fit all visible items here to view window."""
        vr = self.visible_rect()
        if self._cached_visible_rect:
            if vr != self._cached_visible_rect:
                self.graph_view.instant_fit_to_view(vr)
        else:
            self.graph_view.instant_fit_to_view(vr)
        self._cached_visible_rect = vr

    def visible_rect(self):
        """ Counts all visible items in scene and returns QRectF object
         that contains all of them """
        return self.itemsBoundingRect()

    def item_moved(self):
        """ Starts the animations unless they are running already
        :return: None
        """
        if not self._timer_id:
            self._timer_id = self.startTimer(prefs._fps_in_msec)

    start_animations = item_moved

    def stop_animations(self):
        """ Stops the move and fade animation timer
        :return: None
        """
        self.killTimer(self._timer_id)
        self._timer_id = 0

    def export_3d(self, path, forest):
        """ deprecated

        :param path:
        :param forest:
        """
        pass
        # export_visible_items(path = path, scene = self, forest = forest, prefs = prefs)

    def move_selection(self, direction):
        """
        Compute which is the closest or most appropriate object in given direction. Used for
        keyboard movement.
        :param direction:
        """
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
                           self.items() if getattr(item, 'selectable', False) and
                           item.is_visible()]
            if direction == 'left':
                sortable = [(po[0], po[1], it) for it, po in selectables]
                x, y, item = min(sortable)
            elif direction == 'right':
                sortable = [(po[0], po[1], it) for it, po in selectables]
                x, y, item = max(sortable)
            elif direction == 'up':
                sortable = [(po[1], po[0], it) for it, po in selectables]
                y, x, item = min(sortable)
            elif direction == 'down':
                sortable = [(po[1], po[0], it) for it, po in selectables]
                y, x, item = max(sortable)
            else:
                raise KeyError
            ctrl.select(item)
            return item
        # ################ Relative left/right/up/down #############################
        else:
            current = ctrl.get_single_selected()
            # ################### Nodes #############################
            if isinstance(current, Node):
                if direction == 'left':
                    lefts = list(current.get_edges_down(similar=True, visible=True, align=g.LEFT))
                    if len(lefts) == 1:
                        ctrl.select(lefts[0])
                        return lefts[0]
                    elif len(lefts) >= 1:
                        distances = [current.distance_to(x.end) for x in lefts]
                        i = distances.index(min(distances))
                        ctrl.select(lefts[i])
                        return lefts[i]




            best = current
            x, y = to_tuple(current.sceneBoundingRect().center())
            x = int(x)
            y = int(y)
            selectables = []


            if direction == 'left':
                found = False
                if isinstance(current, Node):
                    edges = current.get_edges_down(similar=True, visible=True)
                    if len(edges) == 2:
                        best = edges[0]
                        found = True
                elif isinstance(current, Edge):
                    if current.start and current.alignment == 2:
                        best = current.start
                        found = True
                    elif current.end and current.alignment == 1:
                        best = current.end
                        found = True
                elif isinstance(current, TouchArea):
                    if current.type == g.RIGHT_ADD_ROOT and current.host.top_left_touch_area:
                        best = current.host.top_left_touch_area
                        found = True
                    elif current.type == g.RIGHT_ADD_SIBLING and current.host.left_touch_area:
                        best = current.host.left_touch_area
                        found = True
                if not found:
                    for item, pos in selectables:
                        if item == current:
                            continue
                        ix, iy = pos
                        ix, iy = int(ix), int(iy)
                        dx = ix - x
                        dy = iy - y
                        dxy = (dx * dx) + (2 * dy * dy)
                        if (dx < 0 and (dxy < min_xy)) or (dx == 0 and dy < 0 and (dxy < min_xy)):
                            min_x = dx
                            min_y = dy
                            min_xy = dxy
                            best = item
            if direction == 'right':
                found = False
                if isinstance(current, Node):
                    edges = list(current.get_edges_down(similar=True, visible=True))
                    if len(edges) == 2:
                        best = edges[1]
                        found = True
                elif isinstance(current, Edge):
                    if current.end and current.alignment == 2:
                        best = current.end
                        found = True
                    elif current.start and current.alignment == 1:
                        best = current.start
                        found = True
                elif isinstance(current, TouchArea):
                    if current.type == g.LEFT_ADD_ROOT and current.host.top_right_touch_area:
                        best = current.host.top_right_touch_area
                        found = True
                    elif current.type == g.LEFT_ADD_SIBLING and current.host.right_touch_area:
                        best = current.host.right_touch_area
                        found = True
                if not found:
                    for item, pos in selectables:
                        if item == current:
                            continue
                        ix, iy = pos
                        ix, iy = int(ix), int(iy)
                        dx = ix - x
                        dy = iy - y
                        dxy = (dx * dx) + (2 * dy * dy)
                        if (dx > 0 and (dxy < min_xy)) or (dx == 0 and dy > 0 and (dxy < min_xy)):
                            min_x = dx
                            min_y = dy
                            min_xy = dxy
                            best = item
            if direction == 'up':
                found = False
                if isinstance(current, Node):
                    edges = list(current.get_edges_up(visible=True))
                    if len(edges) == 1:
                        best = edges[0]
                        found = True
                if not found:
                    for item, pos in selectables:
                        if item == current:
                            continue
                        ix, iy = pos
                        ix, iy = int(ix), int(iy)
                        dx = ix - x
                        dy = iy - y
                        dxy = (dx * dx * 2) + (dy * dy)
                        if (dy < 0 and (dxy < min_xy)) or (dy == 0 and dx < 0 and (dxy < min_xy)):
                            min_x = dx
                            min_y = dy
                            min_xy = dxy
                            best = item
            if direction == 'down':
                for item, pos in selectables:
                    if item == current:
                        continue
                    ix, iy = pos
                    ix, iy = int(ix), int(iy)
                    dx = ix - x
                    dy = iy - y
                    dxy = (dx * dx * 2) + (dy * dy)
                    # if dy > 0 and ((dy < min_y) or (dy == min_y and (dx > 0 and dx < min_x ))):
                    if (dy > 0 and (dxy < min_xy)) or (dy == 0 and dx > 0 and (dxy < min_xy)):
                        min_x = dx
                        min_y = dy
                        min_xy = dxy
                        best = item

                        # x,y = to_tuple(best.sceneBoundingRect().center())
                        # el = QtGui.QGraphicsEllipseItem(x-4, y-4, 8, 8)
                        # self.addItem(el)
                        # ctrl.ui_manager.info('dx: %s, dy: %s, dxy: %s' % (min_x, min_y, min_xy))
        ctrl.select(best)

    # ######### MOUSE ##############

    @staticmethod
    def get_closest_item(x, y, candidates, must_contain=False):
        """ If there are several partially overlapping items at the point, choose
        the one that where we clicked closest to center.
        :param x:
        :param y:
        :param candidates:
        :param must_contain:
        :return: GraphicsItem or None
        """
        min_d = 1000
        closest_item = None
        for item in candidates:
            sbr = item.sceneBoundingRect()
            if must_contain and not sbr.contains(x, y):
                continue
            sx, sy = to_tuple(sbr.center())
            dist = abs(sx - x) + abs(sy - y)
            # isObscured doesn't work with semi-transparent items, use zValues instead
            if closest_item:
                if dist < min_d and item.zValue() >= closest_item.zValue():
                    closest_item = item
                    min_d = dist
            else:
                closest_item = item
                min_d = dist
        return closest_item

    def mousePressEvent(self, event):
        """

        :param event:
        :return:
        """
        x, y = to_tuple(event.scenePos())
        # um = self.main.ui_manager
        assert (not ctrl.pressed)
        assert (not ctrl.ui_pressed)

        # Check if any UI items can receive this press
        items = self.items(event.scenePos())
        clickables = [i for i in items if getattr(i, 'clickable', False)]
        # print('clickables: ', clickables)
        success = False
        draggable = False
        if clickables:
            closest_item = self.get_closest_item(x, y, clickables)
            if closest_item:
                ctrl.pressed = closest_item
                draggable = closest_item.draggable
            success = True
        if not success:
            # It wasn't consumed, continue with other selectables:
            draggables = [i for i in items if getattr(i, 'draggable', False)]
            # print('draggables: ', draggables)
            if draggables:
                closest_item = self.get_closest_item(x, y, draggables)
                if closest_item:
                    ctrl.pressed = closest_item
                    draggable = True
                success = True
        if not success:
            selectables = [i for i in items if getattr(i, 'selectable', False)]
            # print('selectables: ', selectables)
            if selectables:
                closest_item = self.get_closest_item(x, y, selectables)
                if closest_item:
                    ctrl.pressed = closest_item
                    draggable = closest_item.draggable
        if draggable:
            self.graph_view.toggle_suppress_drag(True)
        return QtWidgets.QGraphicsScene.mousePressEvent(self, event)

    def start_dragging(self):
        """ Raise graph scene flags related to dragging -- the dragged nodes have already
        alerted controller.
        """
        self._dragging = True

    def kill_dragging(self):
        """ Remove all flags and temporary things related to dragging """
        if ctrl.dragged_focus:
            ctrl.dragged_focus.finish_dragging()
        ctrl.pressed = None
        self._dragging = False
        if ctrl.latest_hover:
            ctrl.latest_hover.hovering = False
            ctrl.latest_hover = None
        ctrl.main.ui_manager.update_touch_areas()
        self.graph_view.toggle_suppress_drag(False)

    def mouseMoveEvent(self, event):
        """

        :param event:
        :return:
        """
        if ctrl.pressed and ctrl.pressed.draggable:
            if self._dragging:
                ctrl.pressed.drag(event)
                self.item_moved()
                items = [x for x in self.items(event.scenePos()) if
                         hasattr(x, 'dragged_over_by') and x is not ctrl.pressed]
                if items:
                    for item in items:
                        item.dragged_over_by(ctrl.pressed)
                elif ctrl.latest_hover:
                    ctrl.latest_hover.hovering = False
                    ctrl.latest_hover = None
                self.main.ui_manager.update_positions()
            else:
                if (event.buttonDownScenePos(QtCore.Qt.LeftButton) -
                        event.scenePos()).manhattanLength() > 6:
                    self.start_dragging()
                    ctrl.pressed.drag(event)
                    self.item_moved()
        return QtWidgets.QGraphicsScene.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        """ deliver clicks, drops and selections to correct objects and make sure that the
        Controller state is up to date.
        :param event:
        :return:
        """
        self.graph_view.toggle_suppress_drag(False)
        if self._dblclick and not ctrl.pressed:
            # doubleclick sends one release event at the end, swallow that
            self._dblclick = False
            if self._dragging:
                print('dblclick while dragging? Unpossible!')
            ctrl.pressed = None
            return
        elif ctrl.pressed:
            pressed = ctrl.pressed  # : :type pressed: Movable
            x, y = to_tuple(event.scenePos())
            if self._dragging:
                recipient = self.get_drop_recipient(pressed, event)  # @UndefinedVariable
                message = pressed.drop_to(x, y, recipient=recipient)
                self.kill_dragging()
                ctrl.ui.update_selections()  # drag operation may have changed visible affordances
                ctrl.main.action_finished(message)  # @UndefinedVariable
            else:
                if pressed.clickable:
                    pressed.click(event)
                if pressed.selectable:
                    pressed.select(event)
                pressed.update()
                ctrl.pressed = None
            return None  # this mouseRelease is now consumed
        else:
            if event.modifiers() == Qt.ShiftModifier:
                pass
            else:
                ctrl.deselect_objects()
        if self._dragging:
            print('still _dragging!')
        elif ctrl.pressed:
            print('mouseReleaseEvent, but still ctrl.pressed!:', ctrl.pressed)
        if self.graph_view.rubberband_mode():
            ctrl.deselect_objects()
            # prioritize nodes in multiple selection. e.g. if there are nodes and edges in
            # selected area, select only nodes. If there are multiple edges and no nodes, then
            # take edges
            only_nodes = False
            for item in self.selectedItems():
                if isinstance(item, Node):
                    only_nodes = True
                    break
            for item in self.selectedItems():
                if ((not only_nodes) or isinstance(item, Node)) and \
                        getattr(item, 'selectable', False):
                    item.select(event, multi=True)
        return QtWidgets.QGraphicsScene.mouseReleaseEvent(self, event)

    def get_drop_recipient(self, pressed, event):
        """ Check which of the items in scene should accept the dropped item, if any
        :param pressed:
        :param event:
        """
        # redo this to be more generic
        return ctrl.latest_hover

    def dragEnterEvent(self, event):
        """

        :param event:
        """
        print('dragEnterEvent in GraphScene!')
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
                    try:
                        node_type = int(node_type)
                    except TypeError:
                        pass
                    ctrl.ui.prepare_touch_areas_for_dragging(
                        dragged_type=node_type)
                else:
                    print('received unknown command:', command, args)

    def dragLeaveEvent(self, event):
        """

        :param event:
        """
        ctrl.ui.remove_touch_areas()
        QtWidgets.QGraphicsScene.dragLeaveEvent(self, event)

    def dropEvent(self, event):
        """

        :param event:
        """
        event.ignore()
        QtWidgets.QGraphicsScene.dropEvent(self, event)
        if not event.isAccepted():
            data = event.mimeData()
            event.accept()
            if data.hasFormat("application/x-qabstractitemmodeldatalist"):
                event.acceptProposedAction()
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
                        node = ctrl.forest.create_node(pos=event.scenePos(),
                                                       node_type=node_type)
                        node.set_fixed_position(event.scenePos())
                        node.lock()
                        ctrl.main.action_finished('added %s' % args[0])
                    else:
                        print('received unknown command:', command, args)
                else:
                    print('adding plain text, what to do?')
        ctrl.ui.remove_touch_areas()

    def dragMoveEvent(self, event):
        """

        :param event:
        """
        event.ignore()
        QtWidgets.QGraphicsScene.dragMoveEvent(self, event)
        if not event.isAccepted():
            data = event.mimeData()
            event.accept()
            if data.hasFormat("application/x-qabstractitemmodeldatalist") or \
                    data.hasFormat("text/plain"):
                event.acceptProposedAction()

    def mouseDoubleClickEvent(self, event):
        """ If doubleclicking an empty spot, open creation menu. If doubleclicking an object,
        it may or may not do something with it.
        :param event: some kind of mouse event?
        :return: None
        """
        self._dblclick = True
        QtWidgets.QGraphicsScene.mouseDoubleClickEvent(self, event)
        found = False
        for item in self.items(event.scenePos()):
            if hasattr(item, 'double_click'):
                item.double_click(event)
                return
            else:
                found = True
        if found:
            return
        ctrl.ui.create_creation_dialog(event.scenePos())

    # ### Timer loop #################################################################

    def fade_background_gradient(self, old_base_color, new_base_color):
        """

        :param old_base_color:
        :param new_base_color:
        """
        self._fade_steps = 7
        if not self._timer_id:
            self._timer_id = self.startTimer(prefs._fps_in_msec)
        self._fade_steps_list = []
        # oh, os, ov, oa = old_base_color.getRgbF()
        # nh, ns, nv, na = new_base_color.getRgbF()
        oh, os, ov, oa = old_base_color.getHsvF()
        nh, ns, nv, na = new_base_color.getHsvF()
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

    def timerEvent(self, event):
        """ Main loop for animations and movement in the scene -- calls nodes and tells them to update
        their position
        :param event: timer event? sent by Qt
        """
        items_have_moved = False
        items_fading = False
        frame_has_moved = False
        background_fade = False
        can_normalize = True
        md = {'sum': (0, 0, 0), 'nodes': []}
        ctrl.items_moving = True
        if self._fade_steps:
            self.setBackgroundBrush(self._fade_steps_list[self._fade_steps - 1])
            self._fade_steps -= 1
            if self._fade_steps:
                background_fade = True

        f = self.main.forest
        #if f.gloss and f.roots and not f.gloss.use_fixed_position:
        #    pt = f.roots[0].current_position
        #    f.gloss.setPos(pt[0] - 20, pt[1] - 40)
        #    f.gloss.lock()
        f.edge_visibility_check()
        for e in f.edges.values():
            e.make_path()
            e.update()

        if ctrl.pressed:
            return
        d=0
        for node in f.visible_nodes():
            if node.adjust_opacity():
                items_fading = True
            # Computed movement
            moved, normalizable = node.move(md)
            if moved:
                items_have_moved = True
            if not normalizable:
                can_normalize = False

        # normalize movement so that the tree won't glide away
        ln = len(md['nodes'])
        if ln and can_normalize:
            avg = div_xyz(md['sum'], ln)
            for node in md['nodes']:
                node.current_position = sub_xyz(node.current_position, avg)
        if items_have_moved and (not self.manual_zoom) and (not ctrl.dragged_focus):
            self.fit_to_window()

        if items_have_moved:
            self.main.ui_manager.get_activity_marker().show()
            if f.settings.bracket_style:
                f.bracket_manager.update_positions()
                # for area in f.touch_areas:
                # area.update_position()
        if not (items_have_moved or items_fading or frame_has_moved or background_fade):
            self.stop_animations()
            self.main.ui_manager.get_activity_marker().hide()
            ctrl.items_moving = False

