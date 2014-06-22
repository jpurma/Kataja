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

from PyQt5 import QtWidgets

from kataja.singletons import prefs, qt_prefs, ctrl


# Verified 8.4. 2013
class Movable(object):
    """ Movable objects have support for smooth movement from one point to another with
        set_target_position, and fade_in and fade_out. Once set, the animation derivation_steps are
        triggered by timerEvent in GraphScene.

        Class using Movable has to inherit also some kind of QtGraphicsItem,
        otherwise its positioning methods won't work.
        """
    saved_fields = ['_computed_position', '_adjustment', '_final_position', '_current_position', '_visible', 'bind_x',
                    'bind_y', 'bind_z', 'locked_to_position', 'forest']

    def __init__(self, forest):
        """ Basic properties for any scene objects
        positioning can be a bit difficult. There are:
        ._computed_position = visualization algorithm provided position
        ._adjustment = dragged somewhere
        ._final_position = computed position + adjustment
        ._current_position = real screen position, can be moving towards final position
        don't adjust final position directly, only change computed position and change
        adjustment to zero if necessary.
        always return adjustment to zero when dealing with dynamic nodes.
         """
        self.z = 0
        if not forest:
            raise Exception("Forest is missing")

        self._computed_position = (0, 0, 0)
        self._adjustment = (0, 0, 0)
        self._final_position = (0, 0, 0)
        self._current_position = (0, 0, 0)

        self._x_step, self._y_step, self._z_step = 0, 0, 0

        self.set_current_position(((random.random() * 150) - 75, (random.random() * 150) - 75, 0))

        self._move_counter = 0
        self._use_easing = True
        self._fade_in_counter = 0
        self._fade_out_counter = 0
        self._visible = True  # avoid isVisible for detecting if something is folded away
        # isVisible seems to be false for objects not in visible area.
        self.bind_x = False
        self.bind_y = False
        self.bind_z = False
        self.locked_to_position = False
        self.after_move_function = None

        # Mouse/touch state  -- add here what methods should be implemented when these are true.
        self.selectable = False
        self.draggable = False
        self.clickable = False
        self._hovering = False

        self.forest = forest

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
        return self._visible

    # ## Movement ##############################################################

    def move_towards_target_position(self):
        """ Takes one step in movement trajectory or finishes movement. Returns true if the movement is still
        continuing, false if it has stopped.
        :return: boolean """
        # if self.locked_to_position:
        # return False
        if not self._move_counter:
            return False
        px, py, pz = self._current_position
        tx, ty, tz = self._final_position
        if abs(px - tx) < .1 and abs(py - ty) < .1 and abs(pz - tz) < .1:
            self.stop_moving()
            # print 'stopping because of no movement required: ', self
            return False
        x_step, y_step, z_step = 0, 0, 0
        if self._use_easing:
            if self.bind_x:
                x_step = self._x_step * qt_prefs.easing_curve[self._move_counter - 1]
            if self.bind_y:
                y_step = self._y_step * qt_prefs.easing_curve[self._move_counter - 1]
            if self.bind_z:
                z_step = self._z_step * qt_prefs.easing_curve[self._move_counter - 1]
        else:
            if self.bind_x:
                x_step = (px - tx) / self._move_counter
            if self.bind_y:
                y_step = (py - ty) / self._move_counter
            if self.bind_z:
                z_step = (pz - tz) / self._move_counter
        self._move_counter -= 1
        self.set_current_position((px - x_step, py - y_step, pz - z_step))
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
        return self._final_position != self._current_position

    def get_final_position(self):
        """
        Return computed final position, which is computed position based on visualization algorithm
        + user-made adjustments
        :return: tuple (x, y, z)
        """
        return self._final_position

    def set_original_position(self, pos):
        """ Sets both current position and computed position to same place,
        use when first adding items to scene to prevent them wandering from afar
        :param pos: tuple (x, y, z)
        """
        self._computed_position = pos
        self._final_position = pos
        self._adjustment = (0, 0, 0)
        self.set_current_position(pos)

    def get_computed_position(self):
        """
        Return the computed position, which was set by visualization algorithm.
        :return: tuple (x, y, z)
        """
        return self._computed_position

    def set_computed_position(self, pos):
        # print 'computed position set to %s, adjusted: %s ' % ( pos, self._adjustment)
        """
        Set the computed position of this item. This is usually called by visualization algorithm.
        :param pos: tuple (x, y, z)
        """
        x, y, z = pos
        self._computed_position = pos
        if self.can_adjust_position():
            ax, ay, az = self._adjustment
            self._final_position = (x + ax, y + ay, z + az)
        else:
            # print 'dont use adjustment'
            self._final_position = self._computed_position
        if self.should_move():  # (not self.moving()) and
            self.start_moving()

    def start_moving(self):
        """
        Initiate moving animation for object.
        """
        x, y, z = self._final_position
        sx, sy, sz = self._current_position
        # print 'item %s starts moving from (%s %s %s) to (%s %s %s)' % (self, sx,sy,sz,x,y,z)
        self._use_easing = True
        self._move_counter = prefs.move_frames
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

    def get_adjustment(self):
        """
        Return adjustments, which are user-made fine tuning to objects computed coordinates.
        :return: tuple (dx, dy, dz)
        """
        return self._adjustment

    def set_adjustment(self, adj_pos):
        """
        Set adjustments, which are user-made fine tuning to objects computed coordinates.
        :param adj_pos: tuple (dx, dy, dz):
        """
        self._adjustment = adj_pos
        if self.can_adjust_position():
            ax, ay, az = adj_pos
            x, y, z = self._computed_position
            self._final_position = (x + ax, y + ay, z + az)

    def reset_adjustment(self):
        """
        Remove adjustments from this object.
        """
        self._adjustment = (0, 0, 0)
        self._final_position = tuple(self._computed_position)

    def get_current_position(self):
        """ Returns Qt position as a triplet with z-dimension
        :return: tuple (x, y, z)"""
        return self._current_position

    def set_current_position(self, pos):
        """ Sets the QtObjects coordinates, and saves the z-dimension to separate variable
        :rtype : None
        :param pos: tuple(x, y, z)
        """
        assert (len(pos) == 3)
        self._current_position = pos
        self.z = pos[2]
        if isinstance(self, QtWidgets.QGraphicsItem):
            QtWidgets.QGraphicsItem.setPos(self, pos[0], pos[1])

    # ## Selection ############################################################

    def is_selected(self):
        """
        Return the selection status of this object.
        :return: boolean
        """
        return ctrl.is_selected(self)

    # ## Dragging ############################################################

    def drop_to(self, x, y):
        """
        This item is dropped to screen coordinates. Evaluate if there are sensitive objects (TouchAreas) there and if
        there are, call their 'drop'-method with self as argument.
        :param x: int or float
        :param y: int or float
        """
        print('movable drop to')
        closest_ma = None
        for ma in ctrl.main.ui_manager.touch_areas:  # @UndefinedVariable
            if ma.sceneBoundingRect().contains(x, y):
                closest_ma = ma
                break
        if closest_ma:
            closest_ma.drop(self)
            print('dropped to:', closest_ma)
            # ctrl.scene.fit_to_window()

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

    def after_restore(self, changes):
        """ Fix derived attributes. In dict 'changes' each changed attribute has tuple w. (old, new) values
        :param changes: dict
        """
        print(changes)
        if '_current_position' in changes:
            self.set_current_position(changes['_current_position'][1])
        if '_computed_position' in changes:
            self.set_computed_position(changes['_computed_position'][1])
