'''
Created on 28.8.2013

@author: purma
'''
from PyQt5 import QtCore

from kataja.Controller import prefs, ctrl
from kataja.utils import to_tuple


class MovableUI(object):
    # Animation and movement of UI elements should be based on individual timers.
    # This way UI and actual animation are easier to keep separated and UI can be made
    # more responsive.

    # Only one animation per item is allowed.

    def __init__(self):
        # position
        self._target_position = to_tuple(self.pos())
        # timer related stuff
        self._timer = None
        self._ticks_left = 0
        self._ticks = 0
        self._tick_method = None
        self._final_method = None
        # opacity
        self._target_opacity = 1.0
        self._hovering = False

    # @time_me
    def set_timer(self, ticks, tick_method, final_method=None):
        """ Start a new timer that will last 'frames' ticks and call frame_method for every tick.
        final_method is called after the last tick. If there is an existing timer it is stopped first."""
        # stop existing timer
        if self._timer:
            if self._final_method:
                self._final_method()  # final method is probably cleanup method, and we should do that
            self._timer.stop()
            self._timer = None
        if ticks == 0:
            self._final_method = final_method
            self._tick_method = tick_method
            self._tick_method()
            self._final_method()

        # start a new timer
        self._timer = QtCore.QTimer()
        self._timer.setInterval(1000 / prefs.FPS)
        self._tick_method = tick_method
        self._final_method = final_method
        self._ticks_left = ticks
        self._ticks = ticks
        self._timer.timeout.connect(self.timer_ticks)
        self._timer.start()
        ctrl.main.ui_manager.ui_activity_marker.show()  # @UndefinedVariable


    def timer_ticks(self):
        """ Make sure that every timer lasts for only a certain amount of ticks and 
            call tick method or final method if this is the last tick. """
        if self._ticks_left:
            self._ticks_left -= 1
            if self._tick_method:
                self._tick_method()
        else:
            self.stop_timer()

    def stop_timer(self):
        ctrl.main.ui_manager.ui_activity_marker.hide()  # @UndefinedVariable
        self._timer.stop()
        self._timer = None
        if self._final_method:
            self._final_method()


    def move_towards_target_position(self, ticks_left=0, ticks=0):
        self.prepareGeometryChange()
        ticks_left = ticks_left or self._ticks_left
        ticks = ticks or self._ticks
        tx, ty = self._target_position
        if ticks_left:
            sx, sy = to_tuple(self.pos())
            x_step = (sx - tx) / ticks_left
            y_step = (sy - ty) / ticks_left
            self.setPos(sx - x_step, sy - y_step)
        else:
            self.setPos(tx, ty)

    def adjust_opacity(self, ticks_left=0, ticks=0):
        ticks_left = ticks_left or self._ticks_left
        ticks = ticks or self._ticks
        if ticks == ticks_left:
            pass
        elif ticks_left:
            step = (self._target_opacity - self.opacity()) / ticks_left
            self.setOpacity(self.opacity() + step)
        else:
            self.setOpacity(self._target_opacity)

    def moving(self):
        return self._timer and self._ticks_left

    def set_target_position(self, x, y):
        self._target_position = (x, y)
