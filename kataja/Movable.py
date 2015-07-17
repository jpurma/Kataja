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
from kataja.utils import add_xyz, sub_xy, multiply_xyz, div_xyz, sub_xyz


def about_there(pos1, pos2):
    """ Two triplets are about equal
    :param pos1:
    :param pos2:
    :return:
    """
    return round(pos1[0]) == round(pos2[0]) and round(pos1[1]) == round(
        pos2[1]) and round(pos1[2]) == round(pos2[2])


class Movable(BaseModel):
    """ Movable objects have support for smooth movement from one point to
    another with
        set_target_position, and fade_in and fade_out. Once set,
        the animation derivation_steps are
        triggered by timerEvent in GraphScene.

        Class using Movable has to inherit also some kind of QtGraphicsItem,
        otherwise its positioning methods won't work.
        """
    short_name = "Movable"  # shouldn't be used on its own

    def __init__(self):
        """ Basic properties for any scene objects
            positioning can be a bit difficult. There are:
            saved.algo_position = visualization algorithm provided position
            saved.adjustment = dragged somewhere
            .final_position = computed position + adjustment
            .current_position = real screen position, can be moving towards
            final position
            don't adjust final position directly, only change computed
            position and change
            adjustment to zero if necessary.
            always restore adjustment to zero when dealing with dynamic nodes.
             """
        super().__init__()
        self._initializing = True
        self.z = 0
        self._step = (0, 0, 0)
        self._current_position = (
        (random.random() * 150) - 75, (random.random() * 150) - 75, 0)
        self._target_position = (0, 0, 0)
        self._move_counter = 0
        self._use_easing = True
        self._fade_in_counter = 0
        self._fade_out_counter = 0
        self.use_physics = True
        self.after_move_function = None
        self.selectable = False
        self.draggable = False
        self.clickable = False
        self._hovering = False
        self.forced_movement = False
        self.algo_position = (0, 0, 0)
        self.adjustment = None
        self.fixed_position = None
        self.visible = True  # avoid isVisible for detecting if something is
        # folded away
        self.dyn_x = False
        self.dyn_y = False
        self.dyn_z = False
        self._initializing = False

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

    @property
    def use_fixed_position(self):
        """ Element ignores dynamic movement
        :return: bool
        """
        return self.fixed_position is not None

    # ## Not saved properties, but otherwise interesting

    @property
    def current_position(self):
        """ Returns Qt position as a triplet with z-dimension
        :return: tuple (x, y, z)"""
        return self._current_position

    @current_position.setter
    def current_position(self, value):
        """ Sets the QtObjects coordinates, and saves the z-dimension to
        separate variable
        :rtype : None
        :param value: tuple(x, y, z)
        """
        assert (len(value) == 3)
        self._current_position = value
        self.z = value[2]
        if isinstance(self, QtWidgets.QGraphicsItem):
            QtWidgets.QGraphicsItem.setPos(self, value[0], value[1])

    @property
    def use_adjustment(self):
        """ Should the relative adjustment counted into position or is the
        position absolute,
        because it is updated by dynamic algo and has to use fixed
        user-determined position.
        :return:
        """
        return self.adjustment and not (self.dyn_x and self.dyn_y)

    def set_fixed_position(self, value):
        """ Manual setter for fixed position, accepts tuples, triples or
        QPoint(F)s.
        :return:
        """
        if hasattr(value, 'x'):
            self.fixed_position = value.x(), value.y(), 0
        elif len(value) == 2:
            self.fixed_position = value[0], value[1], 0
        elif len(value) == 3:
            self.fixed_position = value

    @property
    def can_adjust_position(self):
        """Only those items that get their fixed position from algorithm can
        be adjusted.
        Dynamically moving items are just dragged around. Returns if the
        object gets both x and y
        coords from algorithm.
        :return: boolean
        """
        return not (self.dyn_x and self.dyn_y)

    def autoupdate_position(self, value):
        """ update position, callable by if_changed-hooks in properties.
        doesn't start anything if still initializing the object
        :param value:
        :return:
        """
        if not self._initializing:
            self.update_position()

    def update_position(self, instant=False):
        """ Compute new current_position and target_position
        :param instant: don't animate (for e.g. dragging)
        :return: None
        """
        if instant:
            self.current_position = tuple(self._target_position)
            self.stop_moving()
            return
        ct = self._target_position
        if self.use_fixed_position:
            self._target_position = self.fixed_position
        elif self.use_adjustment:
            self._target_position = add_xyz(self.algo_position, self.adjustment)
        else:
            self._target_position = self.algo_position
        if about_there(self._target_position, ct):
            if about_there(ct, self.current_position):
                self.stop_moving()
        else:
            if about_there(self._target_position, self.current_position):
                self.stop_moving()
            else:
                self.start_moving()

    def reset(self):
        """ Remove mode information, eg. hovering
        :return: None
        """
        self._hovering = False

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
                if hasattr(self, "hide"):
                    self.hide()
        return active

    def is_visible(self):
        """ Our own tracking of object visibility, not based on Qt's scene
        visibility.
        :return: bool
        """
        return self.visible

    # ## Movement ##############################################################

    def move(self, md):
        """ Do one frame of movement: either move towards target position or
        take a step according to algorithm
        :param md: movement data dict
        :return:
        """
        if self.use_fixed_position:
            self.current_position = self.fixed_position
            return False, False
        normalize = False
        # how to return to undoed state?

        if self.dyn_x and self.dyn_y:
            # dynamic movement only
            if self.use_physics and not ctrl.pressed:
                vel = ctrl.forest.visualization.calculate_movement(self)
                md['sum'] = add_xyz(vel, md['sum'])
                md['nodes'].append(self)
            normalize = True
        if not (self.dyn_x or self.dyn_y or self.dyn_z):
            # straight move to target
            if self._move_counter:
                if about_there(self.current_position, self._target_position):
                    self.stop_moving()
                    return False, False
                if self._use_easing:
                    vel = multiply_xyz(self._step, qt_prefs.easing_curve[
                        self._move_counter - 1])
                else:
                    vel = div_xyz(
                        sub_xyz(self._target_position, self.current_position),
                        self._move_counter)
                self._move_counter -= 1
                if not self._move_counter:
                    self.stop_moving()
            else:
                return False, False
        else:
            # combination of move to target and dynamic movement
            dvel = ctrl.forest.visualization.calculate_movement(self)
            if self._move_counter:
                if self._use_easing:  # step * easing_curve
                    pvel = multiply_xyz(self._step, qt_prefs.easing_curve[
                        self._move_counter - 1])
                else:  # (t - c) / move_counter
                    pvel = div_xyz(
                        sub_xyz(self._target_position, self.current_position),
                        self._move_counter)
                self._move_counter -= 1
                if not self._move_counter:
                    self.stop_moving()
            else:
                pvel = (0, 0, 0)
            if self.dyn_x:
                vx = dvel[0]
            else:
                vx = pvel[0]
            if self.dyn_y:
                vy = dvel[1]
            else:
                vy = pvel[1]
            if self.dyn_z:
                vz = dvel[2]
            else:
                vz = pvel[2]
            vel = vx, vy, vz

        self.current_position = add_xyz(self.current_position, vel)
        return abs(vel[0]) + abs(vel[1]) + abs(vel[2]) > 0.6, normalize

    def moving(self):
        """ Check if moving trajectory is on """
        return self._move_counter

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
        was_initializing = self._initializing
        self._initializing = True
        self.algo_position = tuple(pos)
        self._target_position = tuple(pos)
        self.adjustment = None
        self.current_position = tuple(pos)
        self._initializing = was_initializing

    def start_moving(self):
        """ Initiate moving animation for object.
        :return: None
        """
        if False and self._move_counter and self._move_counter < (
            prefs.move_frames or 20):
            # don't force animation to start again, redirect it instead,
            # unless we haven't yet moved
            self._use_easing = True
        else:
            self._use_easing = True
            self._move_counter = prefs.move_frames or 20
            self._step = sub_xyz(self._target_position, self.current_position)
        ctrl.graph_scene.item_moved()

    def stop_moving(self):
        """ Kill moving animation for this object.
        :return: None
        """
        amv = getattr(self, 'after_move_function', None)
        if amv:
            amv()
            self.after_move_function = None
        self._move_counter = 0

    # ## Selection ############################################################

    def is_selected(self):
        """Return the selection status of this object.
        :return: boolean
        """
        return ctrl.is_selected(self)

    # ## Dragging ############################################################

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

    # ### Locked to position

    def release(self):
        """ Item can be affected by computed positions """
        self.adjustment = None
        self.fixed_position = None

    def lock(self):
        """ Item cannot be moved to computed positions """
        # just having self.adjustment or self.fixed_position is enough to
        # lock it down
        assert (self.adjustment or self.fixed_position)

    def is_locked(self):
        """
        Returns if the item's position can be changed by algorithm, or if it
        is fixed to position.
        :return: boolean
        """
        return self.fixed_position or self.adjustment

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    algo_position = Saved("algo_position", if_changed=autoupdate_position)
    adjustment = Saved("adjustment", if_changed=autoupdate_position)
    fixed_position = Saved("fixed_position", if_changed=autoupdate_position)
    visible = Saved(
        "visible")  # avoid isVisible for detecting if something is folded away
    dyn_x = Saved("dyn_x")
    dyn_y = Saved("dyn_y")
    dyn_z = Saved("dyn_z")
