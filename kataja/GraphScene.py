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


from PyQt5.QtCore import QPointF as Pf, Qt
import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
from kataja.Edge import Edge
from kataja.ConstituentNode import ConstituentNode
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.Movable import Movable
from kataja.Node import Node
from kataja.utils import to_tuple, time_me
from kataja.ui import TouchArea
import kataja.globals as g




# from BlenderExporter import export_visible_items


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
        self._signal_forwarding = {}

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

    def forward_signal(self, signal, *args):
        """ When graph scene receives signals, they are forwarded to Kataja's graphic item subclasses. They all have a signal receiver class that can handle certain kinds of signals and modify the item accordingly. 
        :param signal:
        :param args:
        """
        receiving_items = self._signal_forwarding.get(signal, [])
        for item in receiving_items:
            item.receive_signal(signal, *args)

    def add_to_signal_receivers(self, item):
        """ Add item to scene's items that receive certain types of signals. 
        Types of signals that item receives are determined by its receives_signals -list.
        :param item:
        """
        receives = getattr(item.__class__, 'receives_signals', [])

        for signal in receives:
            if signal in self._signal_forwarding:
                receiving_items = self._signal_forwarding[signal]
                receiving_items.add(item)
            else:
                self._signal_forwarding[signal] = {item}

    def remove_from_signal_receivers(self, item):
        """

        :param item:
        """
        receives = getattr(item.__class__, 'receives_signals', [])
        for signal in receives:
            if id(signal) in self._signal_forwarding:
                receiving_items = self._signal_forwarding[signal]
                receiving_items.remove(item)


    # Overriding QGraphicsScene method
    def addItem(self, item):
        """

        :param item:
        """
        self.add_to_signal_receivers(item)
        QtWidgets.QGraphicsScene.addItem(self, item)

        # Overriding QGraphicsScene method

    def removeItem(self, item):
        """

        :param item:
        """
        self.remove_from_signal_receivers(item)
        if item.scene() != self:
            print('wrong scene: ', item)
        QtWidgets.QGraphicsScene.removeItem(self, item)


    def reset_edge_shapes(self):
        """


        """
        if ctrl.forest:
            for e in ctrl.forest.edges.values():
                e.update_shape_method()
                e.update()
        print('received signal')

    # ####

    # @time_me
    def fit_to_window(self):
        """ Calls up to graph view and makes it to fit all visible items here to view window."""
        self.graph_view.instant_fit_to_view(self.visible_rect())

    def visible_rect(self):
        """ Counts all visible items in scene and returns QRectF object
         that contains all of them """
        # r = QtCore.QRectF(self.min_x, self.min_y, self.max_x - self.min_x, self.max_y - self.min_y)
        r = self.itemsBoundingRect()
        return r

    @time_me
    def visible_rect_old(self):
        """ Counts all visible items in scene and returns QRectF object
         that contains all of them -- deprecated, it is slower than calling itemsBoundingRect, but
          on the other hand this doesn't count invisible objects."""
        lefts = []
        rights = []
        tops = []
        bottoms = []
        for item in self.items():
            if isinstance(item, ConstituentNode) and not item.is_fading_away():
                top_left_x, top_left_y, top_left_z = item.magnet(0)
                bottom_right_x, bottom_right_y, bottom_right_z = item.magnet(11)
                lefts.append(top_left_x)
                rights.append(bottom_right_x)
                tops.append(top_left_y)
                bottoms.append(bottom_right_y)
            elif isinstance(item, Movable) and not item.is_fading_away():
                br = item.boundingRect()
                x, y, z = item.current_position  # try using final position here
                lefts.append(x + br.left())
                rights.append(x + br.right())
                tops.append(y + br.top())
                bottoms.append(y + br.bottom())
            elif isinstance(item, Edge):
                if not item.start:
                    lefts.append(item.start_point[0])
                    rights.append(item.start_point[0])
                    tops.append(item.start_point[1])
                    bottoms.append(item.start_point[1])
                if not item.end:
                    lefts.append(item.end_point[0])
                    rights.append(item.end_point[0])
                    tops.append(item.end_point[1])
                    bottoms.append(item.end_point[1])

        if lefts and rights and bottoms and tops:
            r = QtCore.QRectF(Pf(min(lefts), min(tops)), Pf(max(rights), max(bottoms)))
        else:
            r = QtCore.QRectF(-50, -50, 100, 100)
        return r

    def visible_rect_and_gloss(self):
        """


        :return:
        """
        if self.main.forest.gloss:
            return self.visible_rect().united(self.main.forest.gloss.sceneBoundingRect())
        else:
            return self.visible_rect()

    def item_moved(self):
        """ Starts the animations unless they are running already
        :return: None
        """
        if not self._timer_id:
            self._timer_id = self.startTimer(prefs.fps_in_msec)

    start_animations = item_moved

    def stop_animations(self):
        """ Stops the move and fade animation timer
        :return: None
        """
        self.killTimer(self._timer_id)
        self._timer_id = 0


    def export_3d(self, path, forest):
        """

        :param path:
        :param forest:
        """
        pass
        # export_visible_items(path = path, scene = self, forest = forest, prefs = prefs)


    def move_selection(self, direction):

        """
        Compute which is the closest or most appropriate object in given direction. Used for keyboard movement.
        :param direction:
        """
        selectables = [(item, to_tuple(item.sceneBoundingRect().center())) for item in self.items() if
                       getattr(item, 'selectable', False) and item.is_visible()]
        # debugging plotter
        # for item, pos in selectables:
        # x,y = pos
        # el = QtGui.QGraphicsEllipseItem(x-2, y-2, 4, 4)
        # el.setBrush(colors.drawing)
        # self.addItem(el)

        # if nothing is selected, select the edgemost item from given direction
        if not ctrl.selected:
            best = None
            if direction == 'left':
                min_x = 999
                min_y = 999
                for item, pos in selectables:
                    x, y = pos
                    if x < min_x or (x == min_x and y < min_y):
                        min_x = x
                        min_y = y
                        best = item
            elif direction == 'right':
                max_x = -999
                max_y = -999
                for item, pos in selectables:
                    x, y = pos
                    if x > max_x or (x == max_x and y < max_y):
                        max_x = x
                        max_y = y
                        best = item
            if direction == 'up':
                min_x = 999
                min_y = 999
                for item, pos in selectables:
                    x, y = pos
                    if y < min_y or (y == min_y and x < min_x):
                        min_x = x
                        min_y = y
                        best = item
            elif direction == 'down':
                max_x = -999
                max_y = -999
                for item, pos in selectables:
                    x, y = pos
                    if y > max_y or (y == max_y and x < max_x):
                        max_x = x
                        max_y = y
                        best = item
        else:
            current = ctrl.get_selected()
            best = current
            x, y = to_tuple(current.sceneBoundingRect().center())
            x = int(x)
            y = int(y)
            min_x = 999
            min_y = 999
            min_xy = 99999

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
                        # if dx > 0 and ((dx < min_x) or (dx == min_x and (dy > 0 and dy < min_y ))):
                        if (dx < 0 and (dxy < min_xy)) or (dx == 0 and dy < 0 and (dxy < min_xy)):
                            min_x = dx
                            min_y = dy
                            min_xy = dxy
                            best = item
            if direction == 'right':
                found = False
                if isinstance(current, Node):
                    edges = current.get_edges_down(similar=True, visible=True)
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
                        # if dx > 0 and ((dx < min_x) or (dx == min_x and (dy > 0 and dy < min_y ))):
                        if (dx > 0 and (dxy < min_xy)) or (dx == 0 and dy > 0 and (dxy < min_xy)):
                            min_x = dx
                            min_y = dy
                            min_xy = dxy
                            best = item
            if direction == 'up':
                found = False
                if isinstance(current, Node):
                    edges = current.get_edges_up(visible=True)
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
                        # if dy > 0 and ((dy < min_y) or (dy == min_y and (dx > 0 and dx < min_x ))):
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
    def get_closest_item(self, x, y, candidates, must_contain=False):
        """ If there are several partially overlapping items at the point, choose
        the one that where we clicked closest to center.

        :param x:
        :param y:
        :param candidates:
        :param must_contain:
        :return:
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
                if (event.buttonDownScenePos(QtCore.Qt.LeftButton) - event.scenePos()).manhattanLength() > 6:
                    self.start_dragging()
                    ctrl.pressed.drag(event)
                    self.item_moved()
        return QtWidgets.QGraphicsScene.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        """ deliver clicks, drops and selections to correct objects and make sure that the Controller
        state is up to date.
        :param event:
        :return:
        """
        self.graph_view.toggle_suppress_drag(False)
        if self._dblclick and not ctrl.pressed:  # doubleclick sends one release event at the end, swallow that
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
            ctrl.deselect_objects(update_ui=False)
            # prioritize nodes in multiple selection. e.g. if there are nodes and edges in selected area,
            #  select only nodes. If there are multiple edges and no nodes, then take edges
            only_nodes = False
            for item in self.selectedItems():
                if isinstance(item, Node):
                    only_nodes = True
                    break
            for item in self.selectedItems():
                if ((not only_nodes) or isinstance(item, Node)) and getattr(item, 'selectable', False):
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
                    ctrl.ui.prepare_touch_areas_for_dragging(node_type=node_type)
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
                print('adding symbol as a what kind of a node?')
            elif data.hasFormat("text/plain"):
                event.acceptProposedAction()
                command_identifier, *args = data.text().split(':')
                if command_identifier == 'kataja' and args:
                    command, *args = args
                    if command == "new_node":
                        node_type = args[0]
                        node = ctrl.forest.create_empty_node(pos=event.scenePos(), node_type=node_type)
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
            if data.hasFormat("application/x-qabstractitemmodeldatalist") or data.hasFormat("text/plain"):
                event.acceptProposedAction()

    def mouseDoubleClickEvent(self, event):
        """ If doubleclicking an empty spot, open creation menu. If doubleclicking an object, it may or may not
        do something with it.
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
            self._timer_id = self.startTimer(prefs.fps_in_msec)
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


    #@time_me
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
        md = {'xsum': 0, 'ysum': 0, 'zsum': 0, 'nodes': []}
        self.main.ui_manager.activity_marker.show()
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
            avg_x = md['xsum'] / ln
            avg_y = md['ysum'] / ln
            avg_z = md['zsum'] / ln
            for node in md['nodes']:
                x, y, z = node.current_position
                x -= avg_x
                y -= avg_y
                z -= avg_z
                node.current_position = (x, y, z)
        if items_have_moved and (not self.manual_zoom) and (not ctrl.dragged_focus):
            self.fit_to_window()

        if items_have_moved:
            if f.settings.bracket_style:
                f.bracket_manager.update_positions()
                # for area in f.touch_areas:
                # area.update_position()
        if not (items_have_moved or items_fading or frame_has_moved or background_fade):
            self.stop_animations()
            self.main.ui_manager.activity_marker.hide()
            ctrl.items_moving = False

