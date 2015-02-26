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
from kataja.Saved import Savable


# Verified 8.4. 2013
class Movable(Savable):
    """ Movable objects have support for smooth movement from one point to another with
        set_target_position, and fade_in and fade_out. Once set, the animation derivation_steps are
        triggered by timerEvent in GraphScene.

        Class using Movable has to inherit also some kind of QtGraphicsItem,
        otherwise its positioning methods won't work.
        """

    def __init__(self):
        """ Basic properties for any scene objects
            positioning can be a bit difficult. There are:
            saved.computed_position = visualization algorithm provided position
            saved.adjustment = dragged somewhere
            .final_position = computed position + adjustment
            .current_position = real screen position, can be moving towards final position
            don't adjust final position directly, only change computed position and change
            adjustment to zero if necessary.
            always return adjustment to zero when dealing with dynamic nodes.
             """
        super().__init__()
        self.z = 0
        self.saved.computed_position = (0, 0, 0)
        self.saved.adjustment = None
        self.saved.visible = True  # avoid isVisible for detecting if something is folded away
        self.saved.bind_x = False
        self.saved.bind_y = False
        self.saved.bind_z = False
        self.saved.locked_to_position = False

        self._x_step, self._y_step, self._z_step = 0, 0, 0
        self._current_position = ((random.random() * 150) - 75, (random.random() * 150) - 75, 0)
        self.final_position = (
            0, 0, 0)  # Return computed final position, which is computed position based on visualization algorithm
        # + user-made adjustments
        self._move_counter = 0
        self._use_easing = True
        self._fade_in_counter = 0
        self._fade_out_counter = 0
        self.after_move_function = None
        self.selectable = False
        self.draggable = False
        self.clickable = False
        self._hovering = False

    @property
    def computed_position(self):
        """
        Return the computed position, which was set by visualization algorithm.
        :return: tuple (x, y, z)
        """
        return self.saved.computed_position

    @computed_position.setter
    def computed_position(self, value):
        """
        Set the computed position of this item. This is usually called by visualization algorithm.
        :param value: tuple (x, y, z)
        """
        x, y, z = value
        self.saved.computed_position = value
        if self.can_adjust_position() and self.saved.adjustment:
            ax, ay, az = self.saved.adjustment
            self.final_position = (x + ax, y + ay, z + az)
        else:
            # print 'dont use adjustment'
            self.final_position = tuple(self.saved.computed_position)
        if self.should_move():  # (not self.moving()) and
            self.start_moving()

    @property
    def adjustment(self):
        """Return adjustments, which are user-made fine tuning to objects computed coordinates.
        :return: tuple (dx, dy, dz)"""
        return self.saved.adjustment

    @adjustment.setter
    def adjustment(self, value):
        """
        Set adjustments, which are user-made fine tuning to objects computed coordinates.
        :param adj_pos: tuple (dx, dy, dz):
        """
        self.saved.adjustment = value
        if self.can_adjust_position() and value:
            ax, ay, az = value
            x, y, z = self.computed_position
            self.final_position = (x + ax, y + ay, z + az)

    @property
    def visible(self):
        return self.saved.visible

    @visible.setter
    def visible(self, value):
        self.saved.visible = value

    @property
    def bind_x(self):
        return self.saved.bind_x

    @bind_x.setter
    def bind_x(self, value):
        self.saved.bind_x = value

    @property
    def bind_y(self):
        return self.saved.bind_y

    @bind_y.setter
    def bind_y(self, value):
        self.saved.bind_y = value

    @property
    def bind_z(self):
        return self.saved.bind_z

    @bind_z.setter
    def bind_z(self, value):
        self.saved.bind_z = value

    @property
    def locked_to_position(self):
        return self.saved.locked_to_position

    @locked_to_position.setter
    def locked_to_position(self, value):
        self.saved.locked_to_position = value

    ### Not saved properties, but otherwise interesting

    @property
    def current_position(self):
        """ Returns Qt position as a triplet with z-dimension
        :return: tuple (x, y, z)"""
        return self._current_position

    @current_position.setter
    def current_position(self, value):
        """ Sets the QtObjects coordinates, and saves the z-dimension to separate variable
        :rtype : None
        :param value: tuple(x, y, z)
        """
        assert (len(value) == 3)
        self._current_position = value
        self.z = value[2]
        if isinstance(self, QtWidgets.QGraphicsItem):
            QtWidgets.QGraphicsItem.setPos(self, value[0], value[1])


    def reset(self):
        """
        Remove mode information, eg. hovering
        """
        self._hovering = False

    # ## Opacity ##############################################################

    def is_fading_away(self):
        """
        Fade animation is ongoing or just finished
        :return: Boolean
        """
        if self._fade_out_counter:
            return True
        if hasattr(self, "isVisible"):
            return not self.isVisible()
        return False

    def fade_in(self):
        """ Simple fade effect. The object exists already when fade starts. """
        print('fade in called for ', self)
        if hasattr(self, "setOpacity"):
            self.setOpacity(0)
        if hasattr(self, "show"):
            self.show()
        self._fade_in_counter = 10
        self._fade_out_counter = 0

    def fade_out(self):
        """ Start fade out. The object exists until fade end. """
        self._fade_out_counter = 10
        self._fade_in_counter = 0

    def is_fading(self):
        """
        Either fade in or fade out is ongoing
        :return:boolean
        """
        return self._fade_in_counter or self._fade_out_counter

    def adjust_opacity(self):
        """ Takes one step in fading trajectory or finishes fading """
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
        """
        Our own tracking of object visibility, not based on Qt's scene visibility.
        :return: boolean
        """
        return self.visible

    # ## Movement ##############################################################

    def move_towards_target_position(self, bind_all=False):
        """ Takes one step in movement trajectory or finishes movement. Returns true if the movement is still
        continuing, false if it has stopped.
        :return: boolean """
        # if self.locked_to_position:
        # return False
        if not self._move_counter:
            return False
        px, py, pz = self.current_position
        tx, ty, tz = self.final_position
        if abs(px - tx) < .1 and abs(py - ty) < .1 and abs(pz - tz) < .1:
            self.stop_moving()
            return False
        x_step, y_step, z_step = 0, 0, 0
        if self._use_easing:
            if bind_all:
                x_step = self._x_step * qt_prefs.easing_curve[self._move_counter - 1]
                y_step = self._y_step * qt_prefs.easing_curve[self._move_counter - 1]
                z_step = self._z_step * qt_prefs.easing_curve[self._move_counter - 1]
            else:
                if self.bind_x:
                    x_step = self._x_step * qt_prefs.easing_curve[self._move_counter - 1]
                if self.bind_y:
                    y_step = self._y_step * qt_prefs.easing_curve[self._move_counter - 1]
                if self.bind_z:
                    z_step = self._z_step * qt_prefs.easing_curve[self._move_counter - 1]
        else:
            if bind_all:
                x_step = (px - tx) / self._move_counter
                y_step = (py - ty) / self._move_counter
                z_step = (pz - tz) / self._move_counter
            else:
                if self.bind_x:
                    x_step = (px - tx) / self._move_counter
                if self.bind_y:
                    y_step = (py - ty) / self._move_counter
                if self.bind_z:
                    z_step = (pz - tz) / self._move_counter
        self._move_counter -= 1
        self.current_position = (px - x_step, py - y_step, pz - z_step)
        if not self._move_counter:
            self.stop_moving()
            # print 'stopping because move counter: ', self
            return True

        return True

    def moving(self):
        """ Check if moving trajectory is on """
        return self._move_counter

    def should_move(self):
        """
        Returns true if the item is not yet where it should be.
        :return: boolean
        """
        return self.final_position != self.current_position


    def set_original_position(self, pos):
        """ Sets both current position and computed position to same place,
        use when first adding items to scene to prevent them wandering from afar
        :param pos: tuple (x, y, z)
        """
        if isinstance(pos, (QtCore.QPoint, QtCore.QPointF)):
            pos = pos.x(), pos.y(), 0
        self.computed_position = tuple(pos)
        self.final_position = tuple(pos)
        self.adjustment = None
        self.current_position = tuple(pos)


    def start_moving(self):
        """
        Initiate moving animation for object.
        """
        x, y, z = self.final_position
        sx, sy, sz = self.current_position
        # print 'item %s starts moving from (%s %s %s) to (%s %s %s)' % (self, sx,sy,sz,x,y,z)
        if self._move_counter:  # don't force animation to start again, redirect it instead
            self._use_easing = False
        else:
            self._use_easing = True
            self._move_counter = prefs.move_frames or 20
        self._x_step, self._y_step, self._z_step = sx - x, sy - y, sz - z

    def stop_moving(self):
        """
        Kill moving animation for this object.
        """
        if self.after_move_function:
            self.after_move_function()
            self.after_move_function = None
        self._move_counter = 0

    def can_adjust_position(self):
        """
        Only those items that get their fixed position from algorithm can be adjusted. Dynamically moving items are just
        dragged around. Returns if the object gets both x and y coords from algorithm.
        :return: boolean
        """
        return self.bind_x and self.bind_y

    def reset_adjustment(self):
        """
        Remove adjustments from this object.
        """
        self.adjustment = None
        self.final_position = tuple(self.computed_position)


    # ## Selection ############################################################

    def is_selected(self):
        """
        Return the selection status of this object.
        :return: boolean
        """
        return ctrl.is_selected(self)

    # ## Dragging ############################################################

    def drop_to(self, x, y, recipient=None):
        """
        This item is dropped to screen coordinates. Evaluate if there are sensitive objects (TouchAreas) there and if
        there are, call their 'drop'-method with self as argument.
        :param recipient:
        :param x: int or float
        :param y: int or float
        """
        print('movable drop to')
        # closest_ma = None
        # for ma in ctrl.main.ui_manager.touch_areas:  # @UndefinedVariable
        # if ma.sceneBoundingRect().contains(x, y):
        # closest_ma = ma
        # break
        # if closest_ma:
        # closest_ma.drop(self)
        # print('dropped to:', closest_ma)
        # # ctrl.scene.fit_to_window()

    ### Existence ############################################################

    def update_visibility(self, **kwargs):
        """ Simplest case of update_visibility.
        Forces item to be visible, mainly for debugging purposes.
        This will be overridden for more complex objects
        :param kwargs: dict of arguments, which are ignored
        """
        if hasattr(self, "isVisible") and hasattr(self, "show"):
            if not self.isVisible():
                print('Forcing %s to be visible' % self)
                self.show()

    #### Locked to position

    def release(self):
        """ Item can be affected by computed positions """
        self.locked_to_position = False

    def lock(self):
        """ Item cannot be moved to computed positions """
        self.locked_to_position = True

    def is_locked(self):
        """
        Returns if the item's position can be changed by algorithm, or if it is fixed to position.
        :return: boolean
        """
        return self.locked_to_position

        #### Restoring after load / undo #########################################


