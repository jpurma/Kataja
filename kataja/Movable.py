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

import random

from PyQt5 import QtWidgets, QtCore

from kataja.singletons import prefs, qt_prefs, ctrl
from kataja.BaseModel import BaseModel, Saved
from kataja.utils import add_xyz, sub_xy, multiply_xyz, div_xyz, sub_xyz, time_me


def about_there(pos1, pos2):
    """ Two triplets are about equal
    :param pos1:
    :param pos2:
    :return:
    """
    return round(pos1[0]) == round(pos2[0]) and round(pos1[1]) == round(
        pos2[1]) and round(pos1[2]) == round(pos2[2])

class Movable(BaseModel):
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
physics_z = True|False:
after move, the item can wander around according to physics, in set dimensions. use_physics sets
all xyz to True|False.
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
    def __init__(self):
        super().__init__()
        # Common movement-related fields
        self.current_position = ((random.random() * 150) - 75, (random.random() * 150) - 75, 0)
        self.z = 0
        self._dragged = False
        self.tree = set() # each Movable belongs to some tree, either formed by Movable alone or set
        # of Movables. Tree has abstract position adjustment information.

        # MOVE_TO -fields
        self.target_position = (0, 0, 0)
        self.adjustment = (0, 0, 0)
        self._move_counter = 0
        self._use_easing = True
        self._step = None
        self.after_move_function = None
        self.use_adjustment = False
        # PHYSICS -fields
        self.locked = False
        self.physics_x = False
        self.physics_y = False
        self.physics_z = False
        # Other
        self._fade_in_counter = 0
        self._fade_out_counter = 0
        self.selectable = False
        self.draggable = False
        self.clickable = False
        self._hovering = False

    def after_model_update(self, updated_fields, update_type):
        """ This is called after the item's model has been updated, to run
        the side-effects of various
        setters in an order that makes sense.
        :param updated_fields: list of names of fields that have been updated.
        :param update_type: can be CREATED or DELETED -- in case of DELETED,
        it may be that fields have
        not changed, but the object should go the deletion routines. It can
        get a bit complicated.
        :return: None
        """
        self.update_position()

    def use_physics(self):
        return self.physics_x or self.physics_y or self.physics_z

    def reset(self):
        """ Remove mode information, eg. hovering
        :return: None
        """
        self._hovering = False

    # Tree membership ##########################################################

    def pick_any_tree(self):
        for tree in self.tree:
            return tree

    def add_to_tree(self, tree):
        self.tree.add(tree)
        self.setParentItem(tree)

    def remove_from_tree(self, tree):
        if tree in self.tree:
            self.tree.remove(tree)
            if self.tree:
                self.setParentItem(self.pick_any_tree())
            else:
                self.setParentItem(None)


    # ## Movement ##############################################################

    def move_to(self, x, y, z, after_move_function=None):
        """ Start movement to given position
        :param x:
        :param y:
        :param z:
        :param after_move_function: Function to call when the movement is finished
        :return:
        """
        if (x, y, z) == self.target_position:
            # already moving there
            return
        self.target_position = x, y, z
        if after_move_function:
            self.after_move_function = after_move_function
        self.start_moving()

    def move(self, md):
        """ Do one frame of movement: either move towards target position or
        take a step according to algorithm
        :param md: movement data dict, collects sum of all movement to help normalize it
        :return:
        """
        # Dragging overrides everything, don't try to move this anywhere
        if self._dragged:
            return False, False
        # MOVE_TO -based movement has priority over physics. This way e.g. triangles work without
        # additional stipulation
        elif self._move_counter:
            if self.use_adjustment:
                position = sub_xyz(self.current_position, self.adjustment)
            else:
                position = self.current_position
            # stop even despite the _move_counter, if we are close enough
            if about_there(position, self.target_position):
                self.stop_moving()
                return False, False
            # move a precalculated step
            if self._use_easing:
                movement = multiply_xyz(self._step, qt_prefs.easing_curve[self._move_counter - 1])
            else:
                movement = div_xyz(sub_xyz(self.target_position, position), self._move_counter)
            self._move_counter -= 1
            # if move counter reaches zero, stop and do clean-up.
            if not self._move_counter:
                self.stop_moving()
            self.current_position = add_xyz(self.current_position, movement)
            return True, False
        # Locked nodes are immune to physics
        elif self.locked:
            return False, False
        # Physics move node around only if other movement types have not overridden it
        elif self.use_physics():
            movement = ctrl.forest.visualization.calculate_movement(self)
            md['sum'] = add_xyz(movement, md['sum'])
            md['nodes'].append(self)
            self.current_position = add_xyz(self.current_position, movement)
            return abs(movement[0]) + abs(movement[1]) + abs(movement[2]) > 0.6, True
        return False, False

    def copy_position(self, other, ax=0, ay=0, az=0):
        """ Helper method for newly created items. Takes other item and copies movement related
        attributes from it (physics settings, locks, adjustment etc). ax, ay, az can be used to
        adjust these a little to avoid complete overlap.
        :param other:
        :param ax:
        :param ay:
        :param az:
        :return:
        """
        shift = (ax, ay, az)
        self.current_position = add_xyz(other.current_position, shift)
        self.adjustment = other.adjustment
        self.target_position = other.target_position
        self.locked = other.locked
        self.use_adjustment = other.use_adjustment
        self.physics_x = other.physics_x
        self.physics_y = other.physics_y
        self.physics_z = other.physics_z

    def distance_to(self, movable):
        """ Return current x,y distance to another movable
        :param movable:
        :return: x, y
        """
        return sub_xy(self.current_position, movable.current_position)

    def set_original_position(self, pos):
        """ Sets both current position and computed position to same place,
        use when first adding items to scene to prevent them wandering from afar
        :param pos: tuple (x, y, z)
        """
        if isinstance(pos, (QtCore.QPoint, QtCore.QPointF)):
            pos = pos.x(), pos.y(), 0
        self.target_position = tuple(pos)
        self.use_adjustment = False
        self.adjustment = (0, 0, 0)
        self.current_position = tuple(pos)
        self._dragged = False
        self.locked = False

    def start_moving(self):
        """ Initiate moving animation for object.
        :return: None
        """
        self._use_easing = True
        self._move_counter = prefs.move_frames
        self._step = sub_xyz(self.target_position, self.current_position)
        # self.adjustment affects both elements in the previous subtraction, so it can be ignored
        ctrl.graph_scene.item_moved()

    def stop_moving(self):
        """ Kill moving animation for this object.
        :return: None
        """
        if self.after_move_function:
            self.after_move_function()
            self.after_move_function = None
        self._move_counter = 0

    def _current_position_changed(self, value):
        if isinstance(self, QtWidgets.QGraphicsItem):
            QtWidgets.QGraphicsItem.setPos(self, value[0], value[1])

    def update_position(self):
        """ Compute new current_position and target_position
        :return: None
        """
        #if (not self.use_physics()) and (not self._move_counter):

        x, y, z = self.current_position
        if hasattr(self, 'setPos'):
            self.setPos(x, y)

    def release(self):
        """ Remove lock and adjustment"""
        if self.locked:
            self.locked = False
        elif self.use_adjustment:
            self.adjustment = (0, 0, 0)
            self.use_adjustment = False
        self.update_position()

    def lock(self):
        """ Item cannot be moved by physics or it is set to use adjustment"""
        if self.use_physics():
            self.locked = True
        else:
            self.use_adjustment = True

    # ## Opacity ##############################################################

    def is_fading_away(self):
        """ Fade animation is ongoing or just finished
        :return: bool
        """
        if self._fade_out_counter:
            return True
        if hasattr(self, "isVisible"):
            return not self.isVisible()
        return False

    def fade_in(self):
        """ Simple fade effect. The object exists already when fade starts.
        :return: None
        """
        if hasattr(self, "setOpacity"):
            self.setOpacity(0)
        if hasattr(self, "show"):
            self.show()
        self._fade_in_counter = 10
        self._fade_out_counter = 0

    def fade_out(self):
        """ Start fade out. The object exists until fade end.
        :return: None
        """
        self._fade_out_counter = 10
        self._fade_in_counter = 0

    def is_fading(self):
        """ Either fade in or fade out is ongoing
        :return: bool
        """
        return self._fade_in_counter or self._fade_out_counter

    def adjust_opacity(self):
        """ Takes one step in fading trajectory or finishes fading
        :return: bool, is the fade in/out still going on
        """
        active = False
        if self._fade_in_counter:
            self._fade_in_counter -= 1
            if hasattr(self, "setOpacity"):
                self.setOpacity((10 - self._fade_in_counter) / 10.0)
            active = True
        if self._fade_out_counter:
            self._fade_out_counter -= 1
            if self._fade_out_counter:
                if hasattr(self, "setOpacity"):
                    self.setOpacity(self._fade_out_counter / 10.0)
                active = True
            else:
                self.hide()
                self.update_visibility()
        return active

    def is_visible(self):
        """ Our own tracking of object visibility, not based on Qt's scene
        visibility.
        :return: bool
        """
        return self.isVisible()


    # ## Selection ############################################################

    def is_selected(self):
        """Return the selection status of this object.
        :return: boolean
        """
        return ctrl.is_selected(self)

    # ## Dragging ############################################################

    def dragged_to(self, now_x, now_y):
        """ Dragged focus is in now_x, now_y. Move there.
        :param now_x: current drag focus x
        :param now_y: current drag focus y
        :return:
        """
        if self.use_physics():
            self.locked = True
        else:
            self.use_adjustment = True
            ax, ay, az = self.target_position
            self.adjustment = (now_x - ax, now_y - ay, az)
        self.current_position = now_x, now_y, self.z

    def dragged_over_by(self, dragged):
        """

        :param dragged:
        """
        if not self._hovering and self.accepts_drops(dragged):
            if ctrl.latest_hover and not ctrl.latest_hover is self:
                ctrl.latest_hover.hovering = False
            ctrl.latest_hover = self
            self.hovering = True

    def drop_to(self, x, y, recipient=None):
        """
        This item is dropped to screen coordinates. Evaluate if there are
        sensitive objects (TouchAreas) there and if
        there are, call their 'drop'-method with self as argument.
        :param x: int or float
        :param y: int or float
        :param recipient: Movable?
        """
        print('movable drop to %s,%s , recipient=%s' % (x, y, recipient))
        # closest_ma = None
        # for ma in ctrl.main.ui_manager.touch_areas:  # @UndefinedVariable
        # if ma.sceneBoundingRect().contains(x, y):
        # closest_ma = ma
        # break
        # if closest_ma:
        # closest_ma.drop(self)
        # print('dropped to:', closest_ma)
        # # ctrl.scene.fit_to_window()

    def accepts_drops(self, dragged):
        """

        :param dragged:
        :return:
        """
        return False

    # ## Existence ############################################################

    def update_visibility(self, **kwargs):
        """ Simplest case of update_visibility.
        Forces item to be visible, mainly for debugging purposes.
        This will be overridden for more complex objects
        :param kwargs: dict of arguments, which are ignored
        """
        if hasattr(self, "isVisible") and hasattr(self, "show"):
            if not self.isVisible():
                self.show()

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    current_position = Saved("current_position", if_changed=_current_position_changed)
    target_position = Saved("target_position")
    adjustment = Saved("adjustment")
    use_adjustment = Saved("use_adjustment")
    locked = Saved("locked")
    physics_x = Saved("physics_x")
    physics_y = Saved("physics_y")
    physics_z = Saved("physics_z")
