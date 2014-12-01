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
from kataja.debug import mouse
from kataja.Edge import Edge
from kataja.ConstituentNode import ConstituentNode
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.Movable import Movable
from kataja.Node import Node
from kataja.utils import to_tuple
from kataja.ui import TouchArea
import kataja.globals as g




# from BlenderExporter import export_visible_items


class GraphScene(QtWidgets.QGraphicsScene):
    """

    """
    saved_fields = ['main', 'graph_view', 'displayed_forest']
    singleton_key = 'GraphScene'

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
        self._timer_id = 0
        self._dblclick = False
        self._dragging = False
        self._fade_steps = 0
        self._left_border = -50
        self._right_border = 50
        self._top_border = -50
        self._bottom_border = 50
        self._manual_zoom = False
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

    def reset_zoom(self):
        """


        """
        self._manual_zoom = False

    def fit_to_window(self):
        """ Calls up to graph view and makes it to fit all visible items here to view window."""
        vr = self.visible_rect()
        border = 60
        new_rect = QtCore.QRectF(vr.x() - border / 2, vr.y() - border / 2, vr.width() + border, vr.height() + border)
        # sc = ctrl.graph.sceneRect()
        # if abs(sc.x()-new_rect.x())>5 or abs(sc.y()-new_rect.y())>5 or abs(sc.height()-new_rect.height())>5 or abs(sc.width()-new_rect.width())>5:
        self.graph_view.instant_fit_to_view(new_rect)

    def visible_rect(self):
        """ Counts all visible items in scene and returns QRectF object
         that contains all of them """
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

    # @time_me
    def draw_forest(self, forest):
        """ Update all trees in the forest
        :param forest:
        """
        self.killTimer(self._timer_id)
        self._timer_id = 0
        if not forest.visualization:
            forest.change_visualization(prefs.default_visualization)
        forest.update_all()
        forest.visualization.draw()
        if not self._manual_zoom:
            self.fit_to_window()
        self.item_moved()
        self.graph_view.repaint()

    def export_3d(self, path, forest):
        """

        :param path:
        :param forest:
        """
        pass
        # export_visible_items(path = path, scene = self, forest = forest, prefs = prefs)

    def item_moved(self):
        """


        """
        if not self._timer_id:
            self._timer_id = self.startTimer(prefs.fps_in_msec)

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
                    if current.start and current.align == 2:
                        best = current.start
                        found = True
                    elif current.end and current.align == 1:
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
                    if current.end and current.align == 2:
                        best = current.end
                        found = True
                    elif current.start and current.align == 1:
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
        #um = self.main.ui_manager
        assert (not ctrl.pressed)
        assert (not ctrl.ui_pressed)

        # Check if any UI items can receive this press
        items = self.items(event.scenePos())
        clickables = [i for i in items if getattr(i, 'clickable', False)]
        #print('clickables: ', clickables)
        if clickables:
            closest_item = self.get_closest_item(x, y, clickables)
            if closest_item:
                ctrl.pressed = closest_item
                if closest_item.draggable:
                    self.graph_view.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            return QtWidgets.QGraphicsScene.mousePressEvent(self, event)  # None
        # It wasn't consumed, continue with other selectables:
        draggables = [i for i in items if getattr(i, 'draggable', False)]
        #print('draggables: ', draggables)
        if draggables:
            closest_item = self.get_closest_item(x, y, draggables)
            if closest_item:
                ctrl.pressed = closest_item
                self.graph_view.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            return QtWidgets.QGraphicsScene.mousePressEvent(self, event)  # None

        selectables = [i for i in items if getattr(i, 'selectable', False)]
        #print('selectables: ', selectables)
        if selectables:
            closest_item = self.get_closest_item(x, y, selectables)
            if closest_item:
                ctrl.pressed = closest_item
                if closest_item.draggable:
                    self.graph_view.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            return QtWidgets.QGraphicsScene.mousePressEvent(self, event)  # None

        else:
            return QtWidgets.QGraphicsScene.mousePressEvent(self, event)


    def start_dragging(self):
        """


        """
        ctrl.watch_for_drag_end = True
        # these should be activated by constituentnode instead in start_dragging -method
        # for ma in ctrl.forest.touch_areas:
        # if ma.host not in ctrl.dragged and ma.host is not ctrl.pressed:
        # ma.set_hint_visible(True)
        self._dragging = True


    def kill_dragging(self):
        """


        """
        ctrl.dragged = set()
        ctrl.dragged_positions = set()
        ctrl.pressed = None
        ctrl.watch_for_drag_end = False
        self._dragging = False
        f = self.main.forest
        if ctrl.latest_hover:
            ctrl.latest_hover.set_hovering(False)
            ctrl.latest_hover = None

        ctrl.main.ui_manager.remove_touch_areas()  # @UndefinedVariable
        ctrl.main.ui_manager.update_touch_areas()  # @UndefinedVariable
        self.graph_view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def mouseMoveEvent(self, event):
        """

        :param event:
        :return:
        """
        if ctrl.pressed and ctrl.pressed.draggable:
            if self._dragging:
                ctrl.pressed.drag(event)
                self.item_moved()
                items = [x for x in self.items(event.scenePos()) if hasattr(x, 'dragged_over_by') and x is not ctrl.pressed]
                if items:
                    for item in items:
                        item.dragged_over_by(ctrl.pressed)
                elif ctrl.latest_hover:
                    ctrl.latest_hover.set_hovering(False)
                    ctrl.latest_hover = None
                self.main.ui_manager.update_positions()
            else:
                if (event.buttonDownScenePos(QtCore.Qt.LeftButton) - event.scenePos()).manhattanLength() > 4:
                    self.start_dragging()
                    ctrl.pressed.drag(event)
                    self.item_moved()
            return QtWidgets.QGraphicsScene.mouseMoveEvent(self, event)

        return QtWidgets.QGraphicsScene.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        """

        :param event:
        :return:
        """
        self.graph_view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

        if self._dblclick and not ctrl.pressed:  # doubleclick sends one release event at the end, swallow that
            self._dblclick = False
            return
        elif ctrl.pressed:

            pressed = ctrl.pressed  # : :type pressed: Movable
            x, y = to_tuple(event.scenePos())
            success = False
            if self._dragging:
                recipient = self.get_drop_recipient(pressed, event)  # @UndefinedVariable
                pressed.drop_to(x, y, recipient=recipient)
                self.kill_dragging()
                ctrl.ui.update_selections() # drag operation may have changed visible affordances
            else:
                if pressed.clickable:
                    success = pressed.click(event)
                if pressed.selectable:
                    success = pressed.select(event)
                pressed.update()
            ctrl.pressed = None
            if success:
                ctrl.main.action_finished()  # @UndefinedVariable
            return None  # this mouseRelease is now consumed
        else:

            if event.modifiers() == Qt.ShiftModifier:
                pass
            else:
                ctrl.deselect_objects()
        assert(not self._dragging or ctrl.pressed)
        return QtWidgets.QGraphicsScene.mouseReleaseEvent(self, event)

    def get_drop_recipient(self, pressed, event):
        """ Check which of the items in scene should accept the dropped item, if any
        :param pressed:
        :param event:
        """
        # redo this to be more generic
        return ctrl.latest_hover

    def dropEvent(self, event):
         """ Not used at the moment! May be handy when we e.g. drop text snippets on Kataja,
         but then again this may be better done in graph_view or in MainWindow

         :param event:
         """
         ctrl.pressed=None
         self.kill_dragging()
         QtWidgets.QGraphicsScene.dropEvent(self, event)

    def drag_exact_start_point(self):
        return self._drag_start_point

    def mouseDoubleClickEvent(self, event):
        """

        :param event:
        :return:
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
        forest = self.main.forest
        forest.undo_manager.record()
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


    # @time_me
    def timerEvent(self, event):
        # Main loop for animations and movement in scene
        """

        :param event:
        """
        items_have_moved = False
        frame_has_moved = False
        background_fade = False
        resize_required = False
        moved_nodes = []
        normalize = True
        x_sum = 0
        y_sum = 0
        z_sum = 0
        self.main.ui_manager.activity_marker.show()
        ctrl.items_moving = True
        if self._fade_steps:
            self.setBackgroundBrush(self._fade_steps_list[self._fade_steps - 1])
            self._fade_steps -= 1
            if self._fade_steps:
                background_fade = True

        f = self.main.forest
        if f.gloss and f.roots:
            pt = f.roots[0].current_position
            f.gloss.setPos(pt[0] - 20, pt[1] - 40)

        for e in f.edges.values():
            e.update_end_points()
            e.make_path()
            e.update()

        for n, node in enumerate(f.visible_nodes()):
            node.adjust_opacity()
            if node.folding_towards and node.folding_towards is not node:
                x, y, z = node.folding_towards.computed_position
                node.computed_position = (x, y + 30, z)
            if node in ctrl.dragged:
                items_have_moved = True
                continue
            elif node.locked_to_position:
                normalize = False
                moved_nodes.append((0, 0, 0, node))
                continue
            # Computed movement
            elif node.bind_x and node.bind_y:
                if node.move_towards_target_position():
                    items_have_moved = True
                normalize = False
                moved_nodes.append((0, 0, 0, node))
                # print '%s is bound' % node
                continue
            elif node.bind_x or node.bind_y:
                normalize = True
                if node.move_towards_target_position():
                    items_have_moved = True
            # Dynamic movement
            xvel, yvel, zvel = node.calculate_movement()
            moved_nodes.append((xvel, yvel, zvel, node))
            x_sum += xvel
            y_sum += yvel
            z_sum += zvel
        # normalize movement so that the tree won't glide away
        if moved_nodes:
            resize_required = True
            if normalize:
                # print 'normalizing'
                avg_x = x_sum / len(moved_nodes)
                avg_y = y_sum / len(moved_nodes)
                avg_z = z_sum / len(moved_nodes)
                for xvel, yvel, zvel, node in moved_nodes:
                    xvel -= avg_x
                    yvel -= avg_y
                    zvel -= avg_z
                    if abs(xvel) > 0.25 or abs(yvel) > 0.25 or abs(zvel) > 0.25:
                        x, y, z = node.current_position
                        x += xvel
                        y += yvel
                        z += zvel
                        node.current_position = (x, y, z)
                        items_have_moved = True

                        # if x < self._left_border:
                        # self._left_border = x
                        # resize_required = True
                        # elif x > self._right_border:
                        # self._right_border = x
                        #     resize_required = True
                        # if y < self._top_border:
                        #     self._top_border = y
                        #     resize_required = True
                        # elif y > self._bottom_border:
                        #     self._bottom_border = y
                        #     resize_required = True

            else:
                for xvel, yvel, zvel, node in moved_nodes:
                    if abs(xvel) > 0.25 or abs(yvel) > 0.25 or abs(zvel) > 0.25:
                        x, y, z = node.current_position
                        x += xvel
                        y += yvel
                        z += zvel
                        node.current_position = (x, y, z)
                        items_have_moved = True

                        # for xvel,yvel,zvel, node in moved_nodes:
                        # x, y, z = node.current_position
                        # if x < self._left_border:
                        # self._left_border = x
                        #         resize_required = True
                        #     elif x > self._right_border:
                        #         self._right_border = x
                        #         resize_required = True
                        #     if y < self._top_border:
                        #         self._top_border = y
                        #         resize_required = True
                        #     elif y > self._bottom_border:
                        #         self._bottom_border = y
                        #         resize_required = True
        if resize_required and (not self._manual_zoom) and (not ctrl.dragged):
            self.fit_to_window()

        if items_have_moved:
            if f.settings.bracket_style:
                f.bracket_manager.update_positions()
                # for area in f.touch_areas:
                # area.update_position()
        if not (items_have_moved or frame_has_moved or background_fade):
            self.killTimer(self._timer_id)
            self.main.ui_manager.activity_marker.hide()
            ctrl.items_moving = False
            self._timer_id = 0
