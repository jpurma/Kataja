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

import itertools
import math
from collections import defaultdict
import time
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt

import kataja.globals as g
from kataja.ComplexLabel import ComplexLabel
from kataja.SavedField import SavedField
from kataja.saved.Movable import Movable
# from kataja.saved.movables.Node import Node
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.ui_graphicsitems.ControlPoint import ControlPoint
from kataja.uniqueness_generator import next_available_type_id
from kataja.utils import to_tuple, create_shadow_effect, add_xy, time_me, create_blur_effect
from kataja.parser.INodes import as_html
import kataja.ui_widgets.buttons.OverlayButton as Buttons

call_counter = [0]


class DragData:
    """ Helper object to contain drag-related data for duration of dragging """

    def __init__(self, node: 'Node', is_host, mousedown_scene_pos):
        self.is_host = is_host
        self.position_before_dragging = node.current_position
        self.adjustment_before_dragging = node.adjustment
        mx, my = mousedown_scene_pos
        scx, scy = node.current_scene_position
        self.distance_from_pointer = scx - mx, scy - my
        self.dragged_distance = None
        bg = ctrl.cm.paper2().lighter(102)
        bg.setAlphaF(.65)
        self.background = bg
        parent = node.parentItem()
        if parent:
            self.parent = parent
        else:
            self.parent = None


qbytes_scale = QtCore.QByteArray()
qbytes_scale.append("scale")


# ctrl = Controller object, gives accessa to other modules


class Draggable(Movable):
    """ Basic class for any visualization elements that can be connected to
    each other """

    def __init__(self: Movable):
        """ Node is an abstract class that shouldn't be used by itself, though
        it should contain all methods to make it work. Inherit and modify
        this for
        Constituents, Features etc. """
        # self.setFlag(QtWidgets.QGraphicsObject.ItemIsMovable)
        self.drag_data = None
        self.setFlag(QtWidgets.QGraphicsObject.ItemIsSelectable)
        self.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

    # ### MOUSE - kataja
    # ########################################################

    # Drag flow:

    # 0.
    #

    # 1. drag -- compute drag's current situation, where is mouse cursor, should we start
    # dragging or just announce new position for 'dragged_to'.
    #
    #   2. start_dragging -- drag is initiated from this node. If the node was already selected,
    #   then other nodes that were selected at the same time are also understood to be dragged.
    #   If the node has unambiguous children, these are also dragged. If node is top node of a tree,
    #   then the tree is the object of dragging, and not node.
    #
    #   2b. prepare_children_for_dragging -- compute what should be included in drag for this
    #   type of node.
    #
    #   3. prepare_dragging_participiant -- this is called for each node that is included into drag.
    #   Prepares drag data and sets up animations.
    #
    #   4. dragged_to -- this is called for each node in drag set. Node moves to position
    #   relative to drag given scene position (given position is the position of drag pointer
    #   and main dragged element.
    #
    # 5. drop_to -- with dragged node, activate whatever happens in this position if something is
    # dropped there. Call finish_dragging.
    #
    #   6. finish_dragging -- if called with dragged node, calls finish_dragging also for other
    #   nodes in drag set. Clears temporary data and restores node to normal. Should always be
    #   called, even when dragging is cancelled or interrupted.

    def start_dragging(self: 'Node', scene_pos):
        """ Figure out which nodes belong to the dragged set of nodes.
        :param scene_pos:
        """
        print('start dragging')
        ctrl.dragged_focus = self
        ctrl.dragged_set = set()
        ctrl.dragged_groups = set()
        multidrag = False
        # if we are working with selection, this is more complicated, as there may be many nodes
        # and trees dragged at once, with one focus for dragging.
        if self.selected:
            selected_nodes = [x for x in ctrl.selected if isinstance(x, Draggable)]
            # include those nodes in selection and their children that are not part of wholly
            # dragged trees
            for item in selected_nodes:
                if item.drag_data:
                    continue
                elif getattr(item, 'draggable', True):
                    item.prepare_dragging_participiant(host=False, scene_pos=scene_pos)
                    item.prepare_children_for_dragging(scene_pos)
                    multidrag = True
        # no selection -- drag what is under the pointer
        else:
            self.prepare_children_for_dragging(scene_pos)
            self.prepare_dragging_participiant(host=True, scene_pos=scene_pos)

        moving = ctrl.dragged_set
        ctrl.ui.prepare_touch_areas_for_dragging(moving=moving, multidrag=multidrag)
        ctrl.ui.create_drag_info(self)
        self.start_moving()

    def prepare_children_for_dragging(self, scene_pos):
        """ Implement this if structure is supposed to drag with the node
        :return:
        """
        pass

    def prepare_dragging_participiant(self: 'Node', host=False, scene_pos=None):
        """ Add this node into the entourage of dragged node. These nodes will
        maintain their relative position to dragged node while dragging.
        This can and should be called also for the host of the dragging operation. In this case
        host=True.
        :return: None
        :param host: is this the main dragged node or one of its children
        :param scene_pos: mouse position when dragging started -- dragging participiant will keep
        its distance from pointer fixed during dragging
        """
        ctrl.dragged_set.add(self)
        ctrl.add_my_group_to_dragged_groups(self)
        self.drag_data = DragData(self, is_host=host, mousedown_scene_pos=scene_pos)

        parent = self.parentItem()
        if parent:
            parent.setZValue(500)
            # self.anim = QtCore.QPropertyAnimation(self, qbytes_scale)
            # self.anim.setEasingCurve(QtCore.QEasingCurve.Linear)
            # self.anim.setDuration(600)
            # self.anim.setStartValue(self.scale())
            # self.anim.setEndValue(1.5)
            # self.anim.start()

    def drag(self, event):
        """ Drag also elements that are counted to be involved: features,
        children etc. Drag is called to only one principal drag host element. 'dragged_to' is
        called for each element.
        :param event:
        """
        crossed_out_flag = event.modifiers() == QtCore.Qt.ShiftModifier
        for edge in self.edges_up:
            edge.crossed_out_flag = crossed_out_flag
        scene_pos = to_tuple(event.scenePos())
        nx, ny = scene_pos

        # Call dragged_to -method for all nodes that are dragged with the drag focus
        # Their positions are relative to this focus, compute how much.
        for node in ctrl.dragged_set:
            d = node.drag_data
            dx, dy = d.distance_from_pointer
            node.dragged_to((int(nx + dx), int(ny + dy)))
        ctrl.ui.show_drag_adjustment()
        for group in ctrl.dragged_groups:
            group.update_shape()

    def dragged_to(self, scene_pos):
        """ Dragged focus is in scene_pos. Move there or to position relative to that
        :param scene_pos: current pos of drag pointer (tuple x,y)
        :return:
        """
        Movable.dragged_to(self, scene_pos)
        edge_list = [self.edges_up, self.edges_down]
        for item in self.childItems():
            if isinstance(item, Movable):
                edge_list.append(item.edges_up)
                edge_list.append(item.edges_down)
        for edge in itertools.chain.from_iterable(edge_list):
            edge.make_path()
            edge.update()

    def accepts_drops(self, dragged):
        """

        :param dragged:
        :return:
        """
        if isinstance(dragged, ControlPoint):
            if dragged.role == g.START_POINT or dragged.role == g.END_POINT:
                return True
        # elif isinstance(dragged, TouchArea):
        # return True
        return False

    def drop_to(self, x, y, recipient=None, shift_down=False):
        """

        :param recipient:
        :param x:
        :param y:
        :param shift_down:
        :return: action finished -message (str)
        """
        self.stop_moving()
        self.update()
        for edge in self.edges_up:
            edge.crossed_out_flag = False
            if shift_down:
                ctrl.free_drawing.disconnect_node(edge=edge)
        if recipient and recipient.accepts_drops(self):
            self.release()
            recipient.drop(self)
        else:
            if self.use_physics():
                drop_action = ctrl.ui.get_action('move_node')
                drop_action.run_command(self.uid, x, y, has_params=True)
            else:
                adj_x, adj_y = self.adjustment
                drop_action = ctrl.ui.get_action('adjust_node')
                drop_action.run_command(self.uid, adj_x, adj_y, has_params=True)
        self.update_position()
        self.finish_dragging()

    def finish_dragging(self):
        """ Flush dragging-related temporary variables. Called always when
        dragging is finished for any
         reason.
        :return:
        """
        if self is ctrl.dragged_focus:
            for node in ctrl.dragged_set:
                if node is not self:
                    node.finish_dragging()
            ctrl.dragged_set = set()
            ctrl.dragged_focus = None
            ctrl.dragged_groups = set()
            ctrl.dragged_text = None
        self.setZValue(self.preferred_z_value())
        self.drag_data = None
        ctrl.ui.remove_drag_info()

    def cancel_dragging(self):
        """ Fixme: not called by anyone
        Revert dragged items to their previous positions.
        :return: None
        """
        d = self.drag_data
        if d:
            self.adjustment = d.adjustment_before_dragging
            self.current_position = d.position_before_dragging
            self.update_position()
            if d.is_host:
                for node in ctrl.dragged_set:
                    node.cancel_dragging()
            self.setZValue(self.preferred_z_value())
            self.drag_data = None

    def lock(self):
        Movable.lock(self)
        if self.is_visible():
            ctrl.main.ui_manager.show_anchor(self)

    # ### Mouse - Qt events ##################################################

    def mousePressEvent(self, event):
        ctrl.press(self)
        Movable.mousePressEvent(self, event)

    def mouseMoveEvent(self, e):
        # mouseMoveEvents only happen between mousePressEvents and mouseReleaseEvents
        scene_pos_pf = e.scenePos()
        if ctrl.dragged_focus is self:
            self.drag(e)
            ctrl.graph_scene.dragging_over(scene_pos_pf)
        elif (e.buttonDownScenePos(QtCore.Qt.LeftButton) - scene_pos_pf).manhattanLength() > 6:
            scene_pos = to_tuple(scene_pos_pf)
            self.start_dragging(scene_pos)
            self.drag(e)
            ctrl.graph_scene.dragging_over(scene_pos_pf)
        Movable.mouseMoveEvent(self, e)

    def mouseReleaseEvent(self, event):
        """ Either we are finishing dragging or clicking the node. If clicking a node with
        editable label, the click has to be replayed to Label (QGraphicsTextItem) when it has
        toggled the edit mode on, to let its inaccessible method for positioning cursor on click
        position to do its work.
        :param event:
        :return:
        """
        replay_click = False
        shift = event.modifiers() == QtCore.Qt.ShiftModifier

        if ctrl.pressed is self:
            ctrl.release(self)
            if ctrl.dragged_set:
                x, y = to_tuple(event.scenePos())
                self.drop_to(int(x), int(y), recipient=ctrl.drag_hovering_on, shift_down=shift)
                ctrl.graph_scene.kill_dragging()
                ctrl.ui.update_selections()  # drag operation may have changed visible affordances
            else:  # This is a regular click on 'pressed' object
                self.select(adding=shift, select_area=False)
                if self.label_object.is_quick_editing():
                    replay_click = True
                self.update()
        Movable.mouseReleaseEvent(self, event)
        if replay_click and False:
            ctrl.graph_view.replay_mouse_press()
            self.label_object.mouseReleaseEvent(event)
            ctrl.release(self)

    def dragEnterEvent(self, event):
        """ Dragging a foreign object (could be from ui_support) over a node, entering.
        :param event:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist") \
                or event.mimeData().hasFormat("text/plain"):
            self.label_object.dragEnterEvent(event)
            self.hovering = True
        else:
            QtWidgets.QGraphicsObject.dragEnterEvent(self, event)

    def dragLeaveEvent(self, event):
        """ Dragging a foreign object (could be from ui_support) over a node, leaving.
        :param event:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist") \
                or event.mimeData().hasFormat("text/plain"):
            event.acceptProposedAction()
            self.hovering = False
        else:
            QtWidgets.QGraphicsObject.dragLeaveEvent(self, event)

    def dropEvent(self, event: 'QGraphicsSceneDragDropEvent'):
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist") \
                or event.mimeData().hasFormat("text/plain"):
            self.label_object.dropEvent(event)

