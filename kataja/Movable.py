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
from kataja.BaseModel import BaseModel

class MovableModel(BaseModel):
    def __init__(self, host):
        super().__init__(host)
        self.computed_position = (0, 0, 0)
        self.adjustment = None
        self.visible = True  # avoid isVisible for detecting if something is folded away
        self.bind_x = False
        self.bind_y = False
        self.bind_z = False
        self.locked_to_position = False



# Verified 8.4. 2013
class Movable:
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
            don't adjustment final position directly, only change computed position and change
            adjustment to zero if necessary.
            always return adjustment to zero when dealing with dynamic nodes.
             """
        if not hasattr(self, 'model'):
            self.model = MovableModel(self)
        self.z = 0
        self._x_step, self._y_step, self._z_step = 0, 0, 0
        self._current_position = ((random.random() * 150) - 75, (random.random() * 150) - 75, 0)
        self.final_position = (
            0, 0, 0)  # Return computed final position, which is computed position based on visualization algorithm
        # + user-made adjustments
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

    @property
    def save_key(self):
        """ Return the save_key from the model. It is a property from BaseModel.
        :return: str
        """
        return self.model.save_key

    def after_model_update(self, updated_fields):
        """ This is called after the item's model has been updated, to run the side-effects of various
        setters in an order that makes sense.
        :param updated_fields: list of names of fields that have been updated.
        :return: None
        """
        if 'computed_position' in updated_fields:
            self._computed_position_updated(self.computed_position)
        if 'adjustment' in updated_fields:
            self._adjustment_updated(self.adjustment)

    @property
    def computed_position(self):
        """ Return the computed position, which was set by visualization algorithm.
        :return: tuple (x, y, z)
        """
        return self.model.computed_position

    @computed_position.setter
    def computed_position(self, value):
        """ Set the computed position of this item. This is usually called by visualization algorithm.
        :param value: tuple (x, y, z)
        """
        if self.model.touch('computed_position', value):
            self.model.computed_position = value
            self._computed_position_updated(value)

    def _computed_position_updated(self, value):
        """ This is for updating consequences of changes in computed position.
        It is called by setter above, and also when undo/redo sets a value for computed position
        :param value: tuple (dx, dy, dz)
        :return: None
        """
        x, y, z = value
        print('computed position updated')
        if self.can_adjust_position() and self.model.adjustment:
            ax, ay, az = self.model.adjustment
            self.final_position = (x + ax, y + ay, z + az)
        else:
            self.final_position = tuple(self.model.computed_position)
        if self.should_move():
            self.start_moving()
            print('start moving')

    @property
    def adjustment(self):
        """Return adjustments, which are user-made fine tuning to objects computed coordinates.
        :return: tuple (dx, dy, dz)"""
        return self.model.adjustment

    @adjustment.setter
    def adjustment(self, value):
        """ Set adjustments, which are user-made fine tuning to objects computed coordinates.
        :param value: tuple (dx, dy, dz)
        """
        if self.model.touch('adjustment', value):
            self.model.adjustment = value
            self._adjustment_updated(value)

    def _adjustment_updated(self, value):
        """ This is called by setter, and also when undo restores a previous value
        :param value: tuple (dx, dy, dz)
        :return: None
        """
        if value:
            ax, ay, az = value
            x, y, z = self.computed_position
            self.final_position = (x + ax, y + ay, z + az)
        else:
            self.final_position = tuple(self.computed_position)
        if self.should_move():
            self.start_moving()

    @property
    def visible(self):
        """ Is the element toggled visible/invisible by user decision.
        :return: bool
        """
        return self.model.visible

    @visible.setter
    def visible(self, value):
        """ Is the element toggled visible/invisible by user decision.
        :param value: bool
        """
        if self.model.touch('visible', value):
            self.model.visible = value

    @property
    def bind_x(self):
        """ Dynamic movement is ignored for x-dimension
        :return: bool
        """
        return self.model.bind_x

    @bind_x.setter
    def bind_x(self, value):
        """ Dynamic movement is ignored for x-dimension
        :param value: bool
        """
        if self.model.touch('bind_x', value):
            self.model.bind_x = value

    @property
    def bind_y(self):
        """ Dynamic movement is ignored for y-dimension
        :return: bool
        """
        return self.model.bind_y

    @bind_y.setter
    def bind_y(self, value):
        """ Dynamic movement is ignored for y-dimension
        :param value: bool
        """
        if self.model.touch('bind_y', value):
            self.model.bind_y = value

    @property
    def bind_z(self):
        """ Dynamic movement is ignored for z-dimension
        :return: bool
        """
        return self.model.bind_z

    @bind_z.setter
    def bind_z(self, value):
        """ Dynamic movement is ignored for z-dimension
        :param value: bool
        """
        if self.model.touch('bind_z', value):
            self.model.bind_z = value

    @property
    def locked_to_position(self):
        """ Element ignores dynamic movement
        :return: bool
        """
        return self.model.locked_to_position

    @locked_to_position.setter
    def locked_to_position(self, value):
        """ Element ignores dynamic movement
        :param value: bool
        """
        if self.model.touch('locked_to_position', value):
            self.model.locked_to_position = value

    # ## Not saved properties, but otherwise interesting

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
        :return: None
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
        """ Our own tracking of object visibility, not based on Qt's scene visibility.
        :return: bool
        """
        return self.visible

    # ## Movement ##############################################################

    def move_towards_target_position(self, force_move=False):
        """ Takes one step in movement trajectory or finishes movement. Returns true if the movement is still
        continuing, false if it has stopped.
        :param force_move: bool -- ignore the bind_xyz -status and just move it
        :return: bool -- did we move?
        """
        if not self._move_counter:
            return False
        px, py, pz = self.current_position
        tx, ty, tz = self.final_position
        if abs(px - tx) < .1 and abs(py - ty) < .1 and abs(pz - tz) < .1:
            self.stop_moving()
            return False
        x_step, y_step, z_step = 0, 0, 0
        if self._use_easing:
            if force_move:
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
            if force_move:
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
        """ Initiate moving animation for object.
        :return: None
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
        """ Kill moving animation for this object.
        :return: None
        """
        amv = getattr(self, 'after_move_function', None)
        if amv:
            amv()
            self.after_move_function = None
        self._move_counter = 0

    def can_adjust_position(self):
        """Only those items that get their fixed position from algorithm can be adjusted.
        Dynamically moving items are just dragged around. Returns if the object gets both x and y
        coords from algorithm.
        :return: boolean
        """
        return self.bind_x and self.bind_y

    def reset_adjustment(self):
        """ Remove adjustments from this object.
        :return: None
        """
        self.adjustment = None
        self.final_position = tuple(self.computed_position)

    # ## Selection ############################################################

    def is_selected(self):
        """Return the selection status of this object.
        :return: boolean
        """
        return ctrl.is_selected(self)

    # ## Dragging ############################################################

    def drop_to(self, x, y, recipient=None):
        """
        This item is dropped to screen coordinates. Evaluate if there are sensitive objects (TouchAreas) there and if
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
                print('Forcing %s to be visible' % self)
                self.show()

    # ### Locked to position

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
