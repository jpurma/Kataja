#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#############################################################################
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
#############################################################################


from PyQt5.QtCore import QPointF as Pf, Qt

import PyQt5.QtCore as QtCore
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
from Edge import Edge
from kataja.ConstituentNode import ConstituentNode
from kataja.Controller import ctrl, prefs, qt_prefs, colors
from kataja.TouchArea import TouchArea
from kataja.Movable import Movable
from kataja.Node import Node
from kataja.utils import to_tuple


# from BlenderExporter import export_visible_items
class GraphScene(QtWidgets.QGraphicsScene):
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
        if colors.gradient:
            self.setBackgroundBrush(colors.gradient)
        else:
            self.setBackgroundBrush(qt_prefs.no_brush)
        # else:
        #    self.setBackgroundBrush(QtGui.QBrush(colors.paper))
        self.displayed_forest = None
        self._timer_id = 0
        self._dblclick = False
        self._dragging = False
        self._fade_steps = 0
        self._left_border = -50
        self._right_border = 50
        self._top_border = -50
        self._bottom_border = 50
        self._manual_zoom = False

        # self.ants = []
        # for n in range(0,1000):
        #     ant = QtGui.QGraphicsRectItem(0,0,10,10)
        #     ant.setPos(random.random()*400-200, random.random()*400-200)
        #     #ant.setPen(colors.drawing2)
        #     self.addItem(ant)
        #     self.ants.append(ant)

    def reset_zoom(self):
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
                # if item.uses_scope_area:
                #     br = item.scope_rect
                #     x, y, z = item.get_current_position()
                #     lefts.append(x + br.left())
                #     rights.append(x + br.right())
                #     tops.append(y + br.top())
                #     bottoms.append(y + br.bottom())
                # else:
                top, right, bottom, left = item.magnets
                x, y, z = item.get_current_position()  # try using final position here
                lefts.append(x + left)
                rights.append(x + right)
                tops.append(y + top)
                bottoms.append(y + bottom)
            elif isinstance(item, Movable) and not item.is_fading_away():
                br = item.boundingRect()
                x, y, z = item.get_current_position()  # try using final position here
                lefts.append(x + br.left())
                rights.append(x + br.right())
                tops.append(y + br.top())
                bottoms.append(y + br.bottom())
        if lefts and rights and bottoms and tops:
            r = QtCore.QRectF(Pf(min(lefts), min(tops)), Pf(max(rights), max(bottoms)))
        else:
            r = QtCore.QRectF(-50, -50, 100, 100)
        return r

    def visible_rect_and_gloss(self):
        if self.main.forest.gloss:
            return self.visible_rect().united(self.main.forest.gloss.sceneBoundingRect())
        else:
            return self.visible_rect()

    # @time_me
    def draw_forest(self, forest):
        """ Update all trees in the forest """
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
        pass
        # export_visible_items(path = path, scene = self, forest = forest, prefs = prefs)

    def item_moved(self):
        if not self._timer_id:
            self._timer_id = self.startTimer(prefs.fps_in_msec)

    def move_selection(self, direction):

        selectables = [(item, to_tuple(item.sceneBoundingRect().center())) for item in self.items() if
                       getattr(item, 'selectable', False) and item.is_visible()]
        # debugging plotter
        # for item, pos in selectables:
        #     x,y = pos
        #     el = QtGui.QGraphicsEllipseItem(x-2, y-2, 4, 4)
        #     el.setBrush(colors.drawing)
        #     self.addItem(el)

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
                    if not current.left:
                        if current.top and current.host.top_left_touch_area:
                            best = current.host.top_left_touch_area
                            found = True
                        elif current.host.left_touch_area:
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
                    if current.left:
                        if current.top and current.host.top_right_touch_area:
                            best = current.host.top_right_touch_area
                            found = True
                        elif current.host.right_touch_area:
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


    ########## MOUSE ##############
    def get_closest_item(self, x, y, candidates, must_contain=True):
        min_d = 1000
        closest_item = None
        for item in candidates:
            if item.isObscured():
                continue
            sbr = item.sceneBoundingRect()
            if must_contain and not sbr.contains(x, y):
                continue
            sx, sy = to_tuple(sbr.center())
            dist = abs(sx - x) + abs(sy - y)

            # isObscured doesn't work with semi-transparent items, use zValues instead
            if dist < min_d and (not closest_item) or (not item.zValue() < closest_item.zValue()):
                closest_item = item
                min_d = dist
        return closest_item


    def mousePressEvent(self, event):
        print 'gs mousePressEvent'
        x, y = to_tuple(event.scenePos())
        um = self.main.ui_manager
        assert (not ctrl.pressed)
        assert (not ctrl.ui_pressed)

        # Check if any UI items can receive this press
        items = self.items(event.scenePos())

        ui_items = um.filter_active_items_from(items, x, y)
        while ui_items:
            closest_item = self.get_closest_item(x, y, ui_items)
            consumed = um.mouse_press_event(closest_item, event)
            if consumed:
                self.graph_view.setDragMode(QtWidgets.QGraphicsView.NoDrag)
                print 'eating gs mousePressEvent 1'
                return None
            ui_items.remove(closest_item)
        # It wasn't consumed, continue with other selectables:
        selectables = [i for i in items if i.isVisible() and getattr(i, 'selectable', True)]
        if selectables:
            closest_item = self.get_closest_item(x, y, selectables)
            if closest_item:
                ctrl.pressed = closest_item
                if closest_item.draggable:
                    print 'pressed on ', closest_item
                    print '--- turning drag hand off ---'
                    self.graph_view.setDragMode(QtWidgets.QGraphicsView.NoDrag)
                    self._drag_start_point = to_tuple(event.screenPos())
            print 'eating gs mousePressEvent 2'
            return None  # QtWidgets.QGraphicsScene.mousePressEvent(self, event)  # None
        else:
            return QtWidgets.QGraphicsScene.mousePressEvent(self, event)


    def start_dragging(self):
        print '--- start dragging ---'
        ctrl.watch_for_drag_end = True
        # these should be activated by constituentnode instead in start_dragging -method
        # for ma in ctrl.forest.touch_areas:
        #    if ma.host not in ctrl.dragged and ma.host is not ctrl.pressed:
        #        ma.set_hint_visible(True)
        self._dragging = True


    def kill_dragging(self):
        print '--- killing dragging ---'
        ctrl.dragged = set()
        ctrl.dragged_positions = set()
        ctrl.pressed = None
        ctrl.watch_for_drag_end = False
        self._dragging = False
        f = self.main.forest
        ctrl.main.ui_manager.remove_touch_areas()  # @UndefinedVariable
        ctrl.main.ui_manager.update_touch_areas()  # @UndefinedVariable
        print '--- turning drag hand on ---'
        self.graph_view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)


    def mouseReleaseEvent(self, event):
        print 'gs mouseReleaseEvent'
        self.graph_view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

        consumed = self.main.ui_manager.mouse_release_event(event)
        if consumed:
            print 'mouse release consumed, exit now'
            ctrl.main.action_finished()  # @UndefinedVariable
            print 'eating gs mouseReleaseEvent'
            return

        if self._dblclick and not ctrl.pressed:  # doubleclick sends one release event at the end, swallow that
            self._dblclick = False
            print 'swallowed doubleclick'
            print 'eating gs mouseReleaseEvent'
            return
        elif ctrl.pressed:

            pressed = ctrl.pressed  # : :type pressed: Movable
            x, y = to_tuple(event.scenePos())
            success = False
            if self._dragging:
                success = ctrl.main.ui_manager.drop_item_to(pressed, event)  # @UndefinedVariable
                pressed.drop_to(x, y, received=success)
                self.kill_dragging()
            elif pressed.sceneBoundingRect().contains(x, y):
                if pressed.clickable:
                    print 'click on ', pressed
                    success = pressed.click(event)
                pressed.update()
            ctrl.pressed = None
            if success:
                ctrl.main.action_finished()  # @UndefinedVariable
            print 'set pressed to none'
            print 'eating gs mouseReleaseEvent'
            return None  # this mouseRelease is now consumed
        else:
            if event.modifiers() == Qt.ShiftModifier:
                pass
            else:
                ctrl.deselect_objects()
        event.released = None
        if self._dragging or ctrl.pressed:
            assert (False)
        return QtWidgets.QGraphicsScene.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        # ctrl.ui_manager.info(str((event.scenePos().x(), event.scenePos().y())))
        if ctrl.ui_pressed:
            self.main.ui_manager.mouse_move_event(event)
        elif ctrl.pressed:
            um = self.main.ui_manager
            pressed = ctrl.pressed  # : :type pressed: Movable
            if pressed.draggable:
                if self._dragging:
                    pressed.drag(event)
                    self.item_moved()
                    um.update_positions()
                else:
                    scx, scy = to_tuple(event.screenPos())
                    startx, starty = self._drag_start_point
                    if abs(scx - startx) + abs(scy - starty) > 5:
                        self.start_dragging()
                        pressed.drag(event)
                        self.item_moved()
                um.drag_over(event)
                return None
        return QtWidgets.QGraphicsScene.mouseMoveEvent(self, event)

    def dragEnterEvent(self, event):
        QtWidgets.QGraphicsScene.dragEnterEvent(self, event)

    def dragLeaveEvent(self, event):
        QtWidgets.QGraphicsScene.dragLeaveEvent(self, event)

    def dragMoveEvent(self, event):
        QtWidgets.QGraphicsScene.dragMoveEvent(self, event)

    def dropEvent(self, event):
        print 'dropEvent registered'
        QtWidgets.QGraphicsScene.dropEvent(self, event)

    def mouseDoubleClickEvent(self, event):
        print 'doubleClick registered'
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
        x, y = to_tuple(event.scenePos())
        z = 0
        node = forest.create_empty_node(pos=(x, y, z))
        ctrl.select(node)
        ctrl.on_cancel_delete = [node]
        node._hovering = False
        node.open_menus()

    #### Timer loop #################################################################

    def fade_background_gradient(self, old_base_color, new_base_color):
        self._fade_steps = 3
        if not self._timer_id:
            self._timer_id = self.startTimer(prefs.fps_in_msec)
        self._fade_steps_list = []
        # oh, os, ov, oa = old_base_color.getRgbF()
        # nh, ns, nv, na = new_base_color.getRgbF()
        oh, os, ov, oa = old_base_color.getHsvF()
        nh, ns, nv, na = new_base_color.getHsvF()

        h_step = (nh - oh) / self._fade_steps
        s_step = (ns - os) / self._fade_steps
        v_step = (nv - ov) / self._fade_steps
        for n in range(self._fade_steps):
            oh += h_step
            os += s_step
            ov += v_step
            color = QtGui.QColor()
            color.setRgbF(oh, os, ov)
            color.setHsvF(oh, os, ov)
            color2 = QtGui.QColor()
            color2.setRgbF(min((oh + .1, 1.0)), min((os + .1, 1.0)), min((ov + .1, 1.0)))
            gradient = QtGui.QRadialGradient(0, 0, 300)
            gradient.setSpread(QtGui.QGradient.PadSpread)
            gradient.setColorAt(1, color)
            gradient.setColorAt(0, color.lighter())
            self._fade_steps_list.append(gradient)
        self._fade_steps_list.reverse()


    # @time_me
    def timerEvent(self, event):
        # Main loop for animations and movement in scene
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
        if self._fade_steps:
            self.setBackgroundBrush(self._fade_steps_list[self._fade_steps - 1])
            self._fade_steps -= 1
            if self._fade_steps:
                background_fade = True

        f = self.main.forest
        if f.gloss and f.roots:
            pt = f.roots[0].get_current_position()
            f.gloss.setPos(pt[0] - 20, pt[1] - 40)

        # for ant in self.ants:
        #     ant.moveBy(random.random()*4-2, random.random()*4-2)
        for e in f.edges.values():
            e.update_end_points()
            e.make_path()
            e.update()

        for n, node in enumerate(f.visible_nodes()):
            node.adjust_opacity()
            #    items_have_moved = True
            if node.folding_towards and node.folding_towards is not node:
                x, y, z = node.folding_towards.get_computed_position()
                node.set_computed_position((x, y + 30, z))
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
                        x, y, z = node.get_current_position()
                        x += xvel
                        y += yvel
                        z += zvel
                        node.set_current_position((x, y, z))
                        items_have_moved = True

                        # if x < self._left_border:
                        #     self._left_border = x
                        #     resize_required = True
                        # elif x > self._right_border:
                        #     self._right_border = x
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
                        x, y, z = node.get_current_position()
                        x += xvel
                        y += yvel
                        z += zvel
                        node.set_current_position((x, y, z))
                        items_have_moved = True

                        # for xvel,yvel,zvel, node in moved_nodes:
                        #     x, y, z = node.get_current_position()
                        #     if x < self._left_border:
                        #         self._left_border = x
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
            if f.settings.bracket_style():
                f.bracket_manager.update_positions()
                # for area in f.touch_areas:
                #    area.update_position()
        if not (items_have_moved or frame_has_moved or background_fade):
            self.killTimer(self._timer_id)
            self.main.ui_manager.activity_marker.hide()
            self._timer_id = 0

