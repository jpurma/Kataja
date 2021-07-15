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
#############################################################################

import math
import random

from PyQt6 import QtWidgets, QtCore

from kataja.FadeInOut import FadeInOut
from kataja.SavedField import SavedField
from kataja.SavedObject import SavedObject
from kataja.globals import TOP, MIDDLE, BOTTOM, LEFT_ALIGN, CENTER_ALIGN, \
    NO_ALIGN, DELETED, CREATED
from kataja.singletons import prefs, qt_prefs, ctrl


def about_there(pos1, pos2):
    """ Two triplets are about equal
    :param pos1:
    :param pos2:
    :return:
    """
    return round(pos1[0]) == round(pos2[0]) and round(pos1[1]) == round(pos2[1])


class Movable(QtWidgets.QGraphicsObject, SavedObject, FadeInOut):
    """
    Movable items
    -------------

    Movable items are items on canvas that can be affected by visualisation algorithms.
    There are three types of movement:

    set_position(p3):
    item is immediately put to given position.

    move_to(p3):
    item slides to given position

    use_physics(True|False)
    physics_x = True|False:
    physics_y = True|False:
    after move, the item can wander around according to physics, in set dimensions. use_physics sets
    all xy to True|False.
    Physics is handled by visualization algorithm, Movable only announces if it is responsive for
    physics.

    Movements using move_to -are affected by adjustment. Adjustment is a vector that displaces the
    item given amount from the move_to -command.

    Movement is triggered manually with move_to. Element may have wandered away from its target
    position: target position should not be used after the movement if node uses physics.
    Adjustment needs to be taken into account always when using target_position

    Nodes that use physics disable adjustment after the move_to has ended.

    When nodes that use physics are dragged around, they are locked into position. 'Locked' state
    overrides physics: the node stays in those coordinates.
    When nodes that don't use physics are dragged, the adjustment.

    """

    def __init__(self, forest=None):
        FadeInOut.__init__(self)
        SavedObject.__init__(self)
        QtWidgets.QGraphicsObject.__init__(self)

        # Common movement-related elements
        self._current_position = (random.random() * 150) - 75, (random.random() * 150) - 75
        self._dragged = False

        self.k_tooltip = ''
        self.k_action = None
        # MOVE_TO -elements
        self.target_position = 0, 0
        self.adjustment = 0, 0
        self._start_position = 0, 0
        self._move_frames = 0
        self._move_counter = 0
        self.is_moving = False
        self._use_easing = True
        self._distance = None
        self.unmoved = True  # flag to distinguish newly created nodes
        self.use_adjustment = False
        self._high_priority_move = False
        self.locked_to_node = None
        # PHYSICS -elements
        self.locked = False
        self.physics_x = False
        self.physics_y = False
        self.repulsion = 0.2
        # Other
        self._visible_by_logic = True
        self._fade_anim = None
        self.is_fading_in = False
        self.is_fading_out = False
        self._direct_hovering = False
        self._indirect_hovering = False
        self.setZValue(self.preferred_z_value())
        self.forest = forest

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

    def late_init(self):
        pass

    def after_model_update(self, updated_fields, transition_type):
        """ Compute derived effects of updated values in sensible order.
        :param updated_fields: field keys of updates
        :param transition_type: 0:edit, 1:CREATED, -1:DELETED
        :return: None
        """
        # print('movable after_model_update, ', transition_type, revert_transition)
        if transition_type == CREATED:
            self.forest.store(self)
            self.forest.add_to_scene(self)
        elif transition_type == DELETED:
            self.forest.remove_from_scene(self, fade_out=False)
            return
        self.update_position()

    def use_physics(self):
        return (self.physics_x or self.physics_y) and not self.locked_to_node

    def preferred_z_value(self):
        """ Return z-value appropriate for this type of object. May be constant value or require
        more complicated computation.
        :return:
        """
        return 10

    def reset(self):
        """ Remove mode information, eg. hovering
        :return: None
        """
        self._indirect_hovering = False
        self._direct_hovering = False

    @property
    def current_position(self):
        return self._current_position

    @current_position.setter
    def current_position(self, value):
        self._current_position = value
        self.setPos(*value)

    @property
    def current_scene_position(self):
        """ Return current position in scene coordinates and turned to xy -tuple.
        :return:
        """
        xy = self.scenePos()
        return xy.x(), xy.y()

    def from_scene_position(self, x, y):
        """ Return position in local coordinates given a scene position
        :return:
        """
        if self.parentItem():
            p = self.parentItem().mapFromScene(x, y)
            return p.x(), p.y()
        else:
            return x, y

    # ## Movement ##############################################################

    def move_to(self, x, y, valign=MIDDLE, align=NO_ALIGN, can_adjust=True):
        """ Start movement to given position
        :param x:
        :param y:
        :param valign: What position inside the moved item should correspond to given coordinates.
        By default align is in center, but often you may want to move items
        so that e.g. their top rows are aligned.
        Values are TOP(0),  MIDDLE(2), and BOTTOM(4)_
        :param align: NO_ALIGN, LEFT_ALIGN, CENTER_ALIGN, RIGHT_ALIGN
        :param can_adjust: can use movable's adjustment to adjust the target position
        :return:
        """
        if self.use_adjustment and can_adjust:
            ax, ay = self.adjustment
            x += ax
            y += ay
        if valign == MIDDLE:
            pass
        elif valign == TOP:
            y -= self.boundingRect().top()
        elif valign == BOTTOM:
            y -= self.boundingRect().bottom()
        if align == NO_ALIGN:
            pass
        elif align == CENTER_ALIGN:
            br = self.boundingRect()
            x -= br.width() / 2 + br.x()
        elif align == LEFT_ALIGN:
            x -= self.boundingRect().x()
        if (x, y) == self.target_position and self._move_counter:
            # already moving there
            return
        self.target_position = x, y
        if ctrl.play:
            self.start_moving()
        else:
            self.current_position = x, y
            self.forest.order_recalculation_of_positions_relative_to_nodes()

    def move(self, other_nodes: list, heat: float) -> (int, int, bool, bool):
        """ Do one frame of movement: either move towards target position or
        take a step according to algorithm
        1. item folding towards position in part of animation to disappear etc.
        2. item is being dragged
        3. item is locked by user
        4. item is tightly attached to another node which is moving (then the move is handled by
        the other node, it is _not_ parent node, though.)
        5. visualisation algorithm setting it specifically
        (6) or (0) -- places where subclasses can add new movements.
        :param: x_sum
        :param: y_sum
        :param: normalizable_nodes
        :return: diff_x, diff_y, normalize, ban_normalization  -- announce how much we moved and if 
        the movement is such that it should be included in normalization calculations. 
        Any node can prevent normalization altogether, as it is harmful in cases where there is 
        a good reason for many free moving feature nodes to flock into one direction.  
        """
        self.unmoved = False
        diff_x = 0
        diff_y = 0
        can_normalize = not self.locked_to_node
        ban_normalization = False
        # _high_priority_move can be used together with _move_counter
        if not self._high_priority_move:
            # Dragging overrides (almost) everything, don't try to move this anywhere
            if self._dragged:
                return 0, 0, False, True
            # Locked nodes are immune to physics
            elif self.locked:
                return 0, 0, False, False
        # MOVE_TO -based movement has priority over physics. This way e.g. triangles work without
        # additional stipulation
        sx, sy = self.current_position
        if self._move_counter:
            if not self.locked_to_node:
                ban_normalization = True
            # stop even despite the _move_counter, if we are already there
            if self.current_position == self.target_position:
                self.stop_moving()
                return diff_x, diff_y, can_normalize, ban_normalization
            self._move_counter -= 1
            # move a precalculated step
            if self._use_easing:
                if self._move_frames != self._move_counter:
                    time_f = 1 - (self._move_counter / self._move_frames)
                    f = qt_prefs.curve.valueForProgress(time_f)
                else:
                    f = 0
                # 'o' as in original
                odx, ody = self._distance
                osx, osy = self._start_position
                dx = odx * f
                dy = ody * f
                diff_x = osx + dx - sx
                diff_y = osy + dy - sy
                self.current_position = osx + dx, osy + dy
            else:
                ox, oy = self.target_position
                diff_x = (ox - sx) / self._move_counter
                diff_y = (oy - sy) / self._move_counter
                self.current_position = sx + diff_x, sy + diff_y
            # if move counter reaches zero, stop and do clean-up.
            if not self._move_counter:
                self.stop_moving()
            if self.locked_to_node:
                self.locked_to_node.update_bounding_rect()
        # Physics move node around only if other movement types have not overridden it
        elif self.use_physics() and self.is_visible():
            diff_x, diff_y = self.forest.visualization.calculate_movement(self, other_nodes, heat)
            if not self.physics_x:
                diff_x = 0
            elif diff_x > 6:
                diff_x = 6
            elif diff_x < -6:
                diff_x = -6
            if not self.physics_y:
                diff_y = 0
            elif diff_y > 6:
                diff_y = 6
            elif diff_y < -6:
                diff_y = -6
            self.current_position = sx + diff_x, sy + diff_y
        else:
            ban_normalization = True
        return diff_x, diff_y, can_normalize, ban_normalization

    def distance_to(self, movable):
        """ Return current x,y distance to another movable
        :param movable:
        :return: x, y
        """
        sx, sy = self.current_position
        mx, my = movable.current_position
        return sx - mx, sy - my

    def set_original_position(self, pos):
        """ Sets both current position and computed position to same place,
        use when first adding items to scene to prevent them wandering from afar
        :param pos: tuple (x, y)
        """
        if isinstance(pos, (QtCore.QPoint, QtCore.QPointF)):
            pos = pos.x(), pos.y()
        self.target_position = tuple(pos)
        self.use_adjustment = False
        self.adjustment = (0, 0)
        self.current_position = tuple(pos)
        self._dragged = False
        self.locked = False

    def start_moving(self):
        """ Initiate moving animation for object.
        :return: None
        """
        self.is_moving = True
        self.setAcceptHoverEvents(False)
        self._use_easing = True
        tx, ty = self.target_position
        x, y = self.current_position
        dx, dy = tx - x, ty - y
        d = math.sqrt(dx * dx + dy * dy)
        self._distance = dx, dy
        # We want longer movements to take longer time, but not linearly so. It helps viewer to
        # differentiate many movements instead of everything happening at once.
        # this scales nicely:
        # d = 0 -> p = 0
        # d = 50 -> p = 0.5849
        # d = 100 -> p = 1
        # d = 200 -> p = 1.5849
        # d = 500 -> p = 2.5849
        # d = 1000 -> p = 3.4594
        p = math.log2(d * 0.01 + 1)
        self._move_frames = int(p * prefs.move_frames)
        if self._move_frames == 0:
            self._move_frames = 1
        # self._move_frames = prefs.move_frames
        self._move_counter = self._move_frames
        self._start_position = self.current_position
        # self.adjustment affects both elements in the previous subtraction, so it can be ignored
        # ctrl.graph_scene.item_moved()

    def stop_moving(self):
        """ Kill moving animation for this object.
        :return: None
        """
        self.setAcceptHoverEvents(True)
        self._high_priority_move = False
        self.target_position = self.current_position
        self._move_counter = 0
        self.is_moving = False

    def _current_position_changed(self, value):
        self.setPos(value[0], value[1])

    def update_position(self):
        """ Compute new current_position and target_position
        :return: None
        """
        # if (not self.use_physics()) and (not self._move_counter):

        if hasattr(self, 'setPos'):
            self.setPos(*self.current_position)

    def release(self):
        """ Remove lock and adjustment"""
        if self.locked:
            self.locked = False
        elif self.use_adjustment:
            self.adjustment = (0, 0)
            self.use_adjustment = False
        self.update_position()

    def lock(self):
        """ Item cannot be moved by physics or it is set to use adjustment"""
        if self.use_physics():
            self.locked = True
        else:
            self.use_adjustment = True

    def is_visible(self):
        """ Our own tracking of object visibility, not based on Qt's scene
        visibility.
        :return: bool
        """
        return self._visible_by_logic

    # ## Hover ################################################################

    # def shape(self):
    #    p = QtGui.QPainterPath()
    #    p.addRect(self.boundingRect())
    #    return p

    def hoverEnterEvent(self, event):
        """ Hovering has some visual effects, usually handled in paint-method
        :param event:
        """
        self.start_hovering()
        if not ctrl.scene_moving:
            ctrl.ui.show_help(self, event)
        event.accept()

    def hoverMoveEvent(self, event):
        if not ctrl.scene_moving:
            ctrl.ui.move_help(event)

    def hoverLeaveEvent(self, event):
        """ Object needs to be updated
        :param event:
        """
        if self._direct_hovering:
            self.stop_hovering()
        ctrl.ui.hide_help(self, event)

    def start_hovering(self):
        if not self._direct_hovering:
            self._start_direct_hover()
        if not self._indirect_hovering:
            self._start_indirect_hover()

    def stop_hovering(self):
        if self._direct_hovering:
            self._stop_direct_hover()
        if self._indirect_hovering:
            self._stop_indirect_hover()

    def is_direct_hovering(self):
        return self._direct_hovering

    @property
    def hovering(self):
        """ Public access to _hovering. Pretty useless.
        :return:
        """
        return self._indirect_hovering or self._direct_hovering

    @hovering.setter
    def hovering(self, value):
        """ Toggle hovering effects and internal bookkeeping
        :param value: bool
        :return:
        """
        if value and not self._indirect_hovering:
            self._start_indirect_hover()
        elif self._indirect_hovering and not value:
            self._stop_indirect_hover()

    def _start_direct_hover(self):
        """  Start hovering effects for directly hovering over this item.
        :return:
        """
        self._direct_hovering = True
        if ctrl.hovering:
            ctrl.hovering._stop_direct_hover()
        ctrl.hovering = self
        self.update_tooltip()

    def _start_indirect_hover(self):
        """ Start hovering effects that are caused by hovering over this or some other item
        :return:
        """
        self._indirect_hovering = True
        self.update()
        if self.zValue() < 150:
            self.setZValue(150)

    def _stop_direct_hover(self):
        """ Stop hovering effects that were directly caused by hover over this item.
        :return:
        """
        self._direct_hovering = False
        ctrl.hovering = None

    def _stop_indirect_hover(self):
        """ Stop hovering effects that were caused by hover over some other object or this item
        :return:
        """
        self._indirect_hovering = False
        # self.prepareGeometryChange()
        self.setZValue(self.preferred_z_value())
        self.update()

    def update_tooltip(self):
        pass

    # ## Selection ############################################################

    def is_selected(self):
        """Return the selection status of this object.
        :return: boolean
        """
        return ctrl.is_selected(self)

    # ## Dragging ############################################################

    def set_current_pos_from_scene_pos(self, scene_pos):
        self.locked = True
        self.current_position = self.from_scene_position(*scene_pos)

    def set_adjustment_from_scene_pos(self, scene_pos):
        nx, ny = self.from_scene_position(*scene_pos)
        x, y = self.current_position
        self.use_adjustment = True
        dx, dy = nx - x, ny - y

        self.adjustment = self.adjustment[0] + dx, self.adjustment[1] + dy
        self.target_position = nx, ny
        self.current_position = nx, ny

    def dragged_to(self, scene_pos):
        """ Dragged focus is in scene_pos. Move there.
        :param scene_pos: current drag focus
        :return:
        """
        if self.use_physics():
            self.set_current_pos_from_scene_pos(scene_pos)
        else:
            self.set_adjustment_from_scene_pos(scene_pos)

    def dragged_over_by(self, dragged):
        """ When dragging other items on top of this item, should this item react, e.g. show
        somehow that item can be dropped on this.

        :param dragged:
        """
        if ctrl.drag_hovering_on is self:
            return True
        elif self.accepts_drops(dragged):
            ctrl.set_drag_hovering(self)
            return True
        else:
            return False

    def drop_to(self, x, y, recipient=None, shift_down=False):
        """
        This item is dropped to screen coordinates. Evaluate if there are
        sensitive objects (TouchAreas) there and if
        there are, call their 'drop'-method with self as argument.
        """
        print('movable drop to %s,%s , recipient=%s, shift_down=%s' % (x, y, recipient, shift_down))

    def accepts_drops(self, dragged):
        """ Reimplement this to evaluate if this Movable should accept drops from dragged. Default returns False.

        :param dragged: Item that is being dragged. You may want to look into what kind of object
        this is and decide from that.
        :return:
        """
        return False

    # ## Existence ############################################################

    def show(self):
        if not self.isVisible():
            super().show()

    def update_visibility(self, fade_in=True, fade_out=True) -> bool:
        """ Subclasses should set _visible_by_logic based on their many factors. In this level
        the actual hide/show/fade -operations are made.

        This is called logical visibility and can be checked with is_visible().
        Qt's isVisible() checks for scene visibility. Items that are e.g. fading away
        have False for logical visibility but True for scene visibility and items that are part
        of graph in a forest that is not currently drawn may have True for logical visibility but
        false for scene visibility.


        :return: True if visibility has changed. Use this information to notify related parties
        """
        if self.scene():
            if self._visible_by_logic:
                if self.is_fading_out:
                    if fade_in:
                        self.fade_in()
                        return True
                    else:
                        self._fade_anim.stop()
                        self.is_fading_out = False
                        self.show()
                        return True
                elif not self.isVisible():
                    if fade_in:
                        self.fade_in()
                        return True
                    else:
                        self.show()
                        return True
            else:
                if self.isVisible():
                    if fade_out:
                        if not self.is_fading_out:
                            self.fade_out()
                            return True
                    else:
                        self.hide()
                        return True
        return False

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    # current_position = Saved("current_position", if_changed=_current_position_changed)
    target_position = SavedField("target_position")
    adjustment = SavedField("adjustment")
    use_adjustment = SavedField("use_adjustment")
    locked = SavedField("locked")
    physics_x = SavedField("physics_x")
    physics_y = SavedField("physics_y")
    locked_to_node = SavedField("locked_to_node")
    forest = SavedField("forest")
