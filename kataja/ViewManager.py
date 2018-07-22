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

import math

import PyQt5.QtCore as QtCore
from kataja.singletons import ctrl, prefs
from kataja.globals import ViewUpdateReason
from itertools import chain

class ViewManager:
    """ ViewportManager is responsible for deciding what part of the GraphScene should
    be displayed to GraphView and when it should be updated. In Qt GraphScene and
    GraphView should do that on their own, but it seems that the logic is getting too
    complicated and error prone, so keep it all here.
    """

    def __init__(self):
        self.view = None
        self.scene = None
        self.target_scale = 0
        self._scale_factor = 1.0
        self._fit_scale = 1.0
        self._zoomd = (0, 0, 0, 0)
        self._target_rect = QtCore.QRectF(-300, -300, 300, 300)
        self.zoom_timer = QtCore.QBasicTimer()
        self.did_manual_zoom = False
        self.auto_zoom = True
        self.predictive = False
        self._cached_visible_rect = None

        # self.zoom_anim = None
        # self._last_rect = self._target_rect

    def late_init(self, graph_scene, graph_view):
        self.view = graph_view
        self.scene = graph_scene

    # def scale_step(self, r):
    #     ox, oy, ow, oh = self._zoom_rect
    #     dx, dy, dw, dh = self._zoomd
    #     nr = QtCore.QRectF(ox + r * dx, oy + r * dy, ow + r * dw, oh + r * dh)
    #     self._last_rect = nr
    #     self.fitInView(nr, 1)
    #     self._fit_scale = self.transform().m11()
    #     ctrl.call_watchers(self, 'viewport_changed')
    #
    # def scale_finished(self):
    #     self.zoom_anim = None
    #     self._last_rect = self._target_rect
    #
    # # deprecated, doesn't work smoothly enough
    # def slow_fit_to_view(self, target_rect):
    #     """ Fit the current scene into view, snugly.
    #     :param target_rect: scene rect that contains all of the items we want to fit into view.
    #     """
    #     sr = self.sceneRect()
    #     # extend the logical scene if necessary
    #     if target_rect.right() > sr.right() or target_rect.bottom() > sr.bottom():
    #         self.setSceneRect(sr + QtCore.QMarginsF(0, 0, 500, 500))
    #     if target_rect.left() < sr.left() or target_rect.top() < sr.top():
    #         self.setSceneRect(sr + QtCore.QMarginsF(500, 500, 0, 0))
    #     scr = self._last_rect.getRect()
    #     scx, scy, scw, sch = scr
    #     grx, gry, grw, grh = target_rect.getRect()
    #     block = 30
    #     grx = int(grx / block) * block
    #     gry = int(gry / block) * block
    #     grw = int(grw / block) * block + block
    #     grh = int(grh / block) * block + block
    #     dx = grx - scx
    #     dy = gry - scy
    #     dw = grw - scw
    #     dh = grh - sch
    #     if not (dx or dy or dw or dh):
    #         return
    #     if self.zoom_anim:
    #         print("stop ongoing zoom anim!")
    #         self.zoom_anim.stop()
    #     print("starting zoom anim")
    #     self._zoom_rect = scr
    #     self._target_rect = QtCore.QRect(*target_rect.getRect()) #QtCore.QRect(grx, gry, grw, grh)
    #     self._zoomd = dx, dy, dw, dh
    #     self.zoom_anim = QtCore.QTimeLine(200, self)
    #     self.zoom_anim.setUpdateInterval(5)
    #     self.zoom_anim.setCurveShape(QtCore.QTimeLine.EaseInOutCurve)
    #     self.zoom_anim.valueChanged.connect(self.scale_step)
    #     self.zoom_anim.finished.connect(self.scale_finished)
    #     self.zoom_anim.start()
    #     #self.setSceneRect(larger_rect)
    #     #self.fitInView(target_rect, 1)
    #     #self._fit_scale = self.transform().m11()
    #     #ctrl.call_watchers(self, 'viewport_changed')

    # @time_me
    def _fit_to_view(self, target_rect):
        """ Fit the current scene into view, snugly
        :param target_rect: scene rect that contains all of the items we want to fit into view.
        """
        self._cached_visible_rect = target_rect
        sr = self.view.sceneRect()
        # if self.zoom_anim:
        #    self.zoom_anim.stop()
        # expand the logical scene rect when necessary
        if target_rect.right() > sr.right():
            print('expanding right')
            self.view.setSceneRect(sr + QtCore.QMarginsF(0, 0, 500, 0))
        if target_rect.bottom() > sr.bottom():
            print('expanding bottom')
            self.view.setSceneRect(sr + QtCore.QMarginsF(0, 0, 0, 500))
        if target_rect.left() < sr.left():
            print('expanding left')
            self.view.setSceneRect(sr + QtCore.QMarginsF(500, 0, 0, 0))
        if target_rect.top() < sr.top():
            print('expanding top')
            self.view.setSceneRect(sr + QtCore.QMarginsF(0, 500, 0, 0))
        self.view.fitInView(target_rect, 1)
        self._fit_scale = self.view.transform().m11()
        ctrl.call_watchers(self, 'viewport_moved')

    def scale_view_by(self, delta):
        """

        :param delta:
        :return:
        """
        if delta < 1.0 and self._scale_factor == 0.3:
            return self._scale_factor
        elif delta > 1.0 and self._scale_factor == 9.0:
            return self._scale_factor
        factor = self.view.transform().scale(delta, delta).m11()
        if factor < 0.3:
            factor = 0.3
        elif factor > 9.0:
            factor = 9.0
        self.view.resetTransform()
        self.view.scale(factor, factor)
        ctrl.call_watchers(self, 'viewport_moved')
        return factor

    def zoom_by_angle(self, pointer_pos, y_angle):
        """
        """
        view_center = self.view.mapToScene(self.view.viewport().rect().center())
        delta = math.pow(2.0, -y_angle / 360.0)
        if delta != 1.0:
            self.zoom_timer.start(1000, self.view)
            self._scale_factor = self.scale_view_by(delta)
            if prefs.zoom_to_center:
                if ctrl.selected:
                    if ctrl.single_selection():
                        self.view.centerOn(ctrl.selected[0].sceneBoundingRect().center())
                    else:
                        br = QtCore.QRectF()
                        for item in ctrl.selected:
                            br |= item.sceneBoundingRect()
                        self.view.centerOn(br.center())
                else:
                    self.view.centerOn(view_center)
            elif delta > 1:
                change = (pointer_pos - view_center) * (delta - 1)  # * 0.5
                self.view.centerOn(view_center + change)
            else:
                self.view.centerOn(view_center)
            if prefs.auto_pan_select:
                # Toggle pan mode if we are zoomed in
                self.view.set_selection_mode(self.view.transform().m11() > self._fit_scale)

        # self._last_rect = self.mapToScene(self.rect()).boundingRect()
        self.did_manual_zoom = True

    def _new_visible_rect(self):
        #print('cached view rect: ', self._cached_visible_rect)
        vr = self._calculate_visible_rect() + self.margins()
        #print('new visible rect: ', vr)
        if (not self._cached_visible_rect) or vr != self._cached_visible_rect:
            self._cached_visible_rect = vr
            #print('recalculated view rect: ', vr)
            return vr

    def fit_to_window(self):
        """ Fit all visible items to view window. """
        self.did_manual_zoom = False
        vr = self._new_visible_rect()
        if not vr:
            return
        self._fit_to_view(vr)

    def fit_if_expanding(self):
        """ Refit to viewport if new graph is larger than previous """
        vr = self._new_visible_rect()
        if not vr:
            return
        cvr = self._cached_visible_rect
        zooming_out = (vr.left() < cvr.left() or
                       vr.top() < cvr.top() or
                       vr.right() > cvr.right() or
                       vr.bottom() > cvr.bottom())
        if zooming_out:
            self._fit_to_view(vr)

    @staticmethod
    def margins():
        mw = prefs.edge_width
        mh = prefs.edge_height
        return QtCore.QMarginsF(mw, mh * 2, mw, mh)

    def update_viewport(self, reason):
        if reason == ViewUpdateReason.ANIMATION_STEP:
            if self.auto_zoom and not (self.predictive or self.did_manual_zoom):
                self.fit_to_window()
        elif reason == ViewUpdateReason.MANUAL_ZOOM:
            #print('------ MANUAL_ZOOM')
            self.set_auto_zoom(False)

        elif reason == ViewUpdateReason.ACTION_FINISHED:
            #print('------ ACTION_FINISHED')
            if self.auto_zoom:
                self.fit_to_window()
        elif reason == ViewUpdateReason.FIT_IN_TRIGGERED:
            #print('------ FIT_IN_TRIGGERED')
            self.fit_to_window()
        elif reason == ViewUpdateReason.MAJOR_REDRAW:
            #print('------ MAJOR_REDRAW')
            if self.auto_zoom:
                self.fit_to_window()
        elif reason == ViewUpdateReason.NEW_FOREST:
            #print('------ NEW_FOREST')
            self.set_auto_zoom(True)
            self.fit_to_window()

    def center(self):
        if self._cached_visible_rect:
            return self._cached_visible_rect.center()
        return self._calculate_visible_rect().center()

    # def fit_to_window_if_needed(self):
    #     if not (self.match_final_derivation_size or
    #             self.manual_zoom or
    #             ctrl.dragged_focus):
    #         self.fit_to_window()

    def set_auto_zoom(self, value):
        if self.auto_zoom != value:
            self.auto_zoom = value
            action = ctrl.ui.get_action('auto_zoom')
            if action:
                action.update_action()

    @staticmethod
    def _calculate_visible_rect():
        """ Counts all visible items in scene and returns QRectF object
         that contains all of them """
        min_width = 200
        min_height = 100
        rect_top = 6000
        rect_bottom = -6000
        rect_left = 6000
        rect_right = -6000
        empty = True
        use_current_position = ctrl.forest.free_movers
        for node in ctrl.forest.nodes.values():
            if not node:
                continue
            if (not use_current_position) and node.parentItem():
                continue
            if not node.isVisible():
                continue
            if node.is_fading_out:
                continue
            empty = False
            left, top, right, bottom = node.scene_rect_coordinates(use_current_position)
            #if left < rect_left:
            #    leftmost = node
            #if right > rect_right:
            #    rightmost = node
            #if top < rect_top:
            #    topmost = node
            #if bottom > rect_bottom:
            #    bottommost = node
            rect_left = left if left < rect_left else rect_left
            rect_right = right if right > rect_right else rect_right
            rect_top = top if top < rect_top else rect_top
            rect_bottom = bottom if bottom > rect_bottom else rect_bottom
        if empty:
            return QtCore.QRectF(0, 0, 320, 240)
        #print('use_current_position:', use_current_position)
        #print('leftmost:', leftmost, leftmost.scene_rect_coordinates(use_current_position))
        #print('rightmost:', rightmost, rightmost.scene_rect_coordinates(use_current_position))
        #print('topmost:', topmost, topmost.scene_rect_coordinates(use_current_position))
        #print('bottommost:', bottommost, bottommost.scene_rect_coordinates(use_current_position))
        sm = ctrl.forest.semantics_manager
        if sm.visible:
            for item in sm.all_items:
                left, top, right, bottom = item.sceneBoundingRect().getCoords()
                rect_left = left if left < rect_left else rect_left
                rect_right = right if right > rect_right else rect_right
                rect_top = top if top < rect_top else rect_top
                rect_bottom = bottom if bottom > rect_bottom else rect_bottom
        #print('finally: ', rect_left, rect_top, rect_right, rect_bottom)
        width = rect_right - rect_left
        if width < min_width:
            rect_left -= (min_width - width) / 2
            width = min_width
        height = rect_bottom - rect_top
        if height < min_height:
            rect_top -= (min_height - height) / 2
            height = min_height
        #print('rect: ', rect_left, rect_top, width, height)
        r = QtCore.QRectF(rect_left, rect_top, width, height)
        return r

    @staticmethod
    def print_rect():
        """ A more expensive version of visible_rect, also includes curves of edges. Too slow for
        realtime resizing, but when printing you don't want any edges to be clipped.
        :return:
        """
        f = ctrl.forest
        total = QtCore.QRectF()
        for item in chain(f.nodes.values(), f.groups.values(), f.edges.values(), f.semantics_manager.all_items):
            if not item.isVisible():
                continue
            total |= item.sceneBoundingRect()
        if not total:
            total = QtCore.QRectF(0, 0, 320, 240)
        else:
            total.adjust(-5, -5, 15, 10)
        return total
