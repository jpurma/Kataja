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
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
from PyQt5.QtCore import Qt
from kataja.singletons import ctrl, prefs
import kataja.globals as g
from kataja.utils import time_me


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
        self._suppressed_drag_mode = False
        self.manual_zoom = False
        self.match_final_derivation_size = False
        self._cached_visible_rect = None
        self.keep_updating = False
        self.selection_mode = True

        # self.zoom_anim = None
        # self._last_rect = self._target_rect

    def late_init(self, graph_scene, graph_view):
        self.view = graph_view
        self.scene = graph_scene
        self._suppressed_drag_mode = self.view.dragMode()

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
    def instant_fit_to_view(self, target_rect):
        """ Fit the current scene into view, snugly
        :param target_rect: scene rect that contains all of the items we want to fit into view.
        """
        sr = self.view.sceneRect()
        # if self.zoom_anim:
        #    self.zoom_anim.stop()
        if target_rect.right() > sr.right() or target_rect.bottom() > sr.bottom():
            self.view.setSceneRect(sr + QtCore.QMarginsF(0, 0, 500, 500))
        if target_rect.left() < sr.left() or target_rect.top() < sr.top():
            self.view.setSceneRect(sr + QtCore.QMarginsF(500, 500, 0, 0))
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
            self.zoom_timer.start(1000, self)
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
                if self.view.transform().m11() > self._fit_scale:
                    if self.selection_mode:
                        self.set_selection_mode(False)  # Pan mode
                else:
                    if not self.selection_mode:
                        self.set_selection_mode(True)  # Select mode

        # self._last_rect = self.mapToScene(self.rect()).boundingRect()
        self._manual_zoom = True

    def set_selection_mode(self, selection_mode):
        if selection_mode:
            self.selection_mode = True
            self.view.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        else:
            self.selection_mode = False
            self.view.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self._suppressed_drag_mode = self.view.dragMode()

    def toggle_suppress_drag(self, suppress):
        """ ScrollHandDrag or RubberBandDrag shouldn't register if we are dragging one object
        (GraphScene handles that). This method allows to suppress these drag modes temporarily.
         :param suppress: if true, switch to NoDrag, otherwise restore mode suitable to zoom level
         """
        if suppress:
            self._suppressed_drag_mode = self.view.dragMode()
            self.view.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        else:
            self.view.setDragMode(self._suppressed_drag_mode)

    def fit_to_window(self, force=False, zoom_in=True):
        """ Fit all visible items to view window. Resizing may be skipped if there are
        :param force: force resize
        :param zoom_in: do resize when it means that

        """
        mw = prefs.edge_width
        mh = prefs.edge_height
        margins = QtCore.QMarginsF(mw, mh * 2, mw, mh)
        use_current_positions = len(ctrl.forest.nodes) < 10
        vr = self.visible_rect(current=use_current_positions) + margins
        ctrl.forest.optimal_rect = vr
        if force or not self._cached_visible_rect:
            self.instant_fit_to_view(vr)
            self._cached_visible_rect = vr
            return
        if vr == self._cached_visible_rect:
            return
        zooming_out = (vr.width() > self._cached_visible_rect.width() or
                       vr.height() > self._cached_visible_rect.height())
        if zooming_out or (zoom_in and (self.keep_updating or prefs.auto_zoom)):
            self.instant_fit_to_view(vr)
            self._cached_visible_rect = vr

    def fit_to_window_if_needed(self):
        if not (self.match_final_derivation_size or
                self.manual_zoom or
                ctrl.dragged_focus):
            self.fit_to_window()

    @staticmethod
    def visible_rect(current=True):
        """ Counts all visible items in scene and returns QRectF object
         that contains all of them """
        min_width = 200
        min_height = 100
        rect_top = 6000
        rect_bottom = -6000
        rect_left = 6000
        rect_right = -6000
        empty = True
        for node in ctrl.forest.nodes.values():
            if not node:
                continue
            if node.parentItem():
                continue
            if not node.isVisible():
                continue
            empty = False
            left, top, right, bottom = node.scene_rect_coordinates(current)
            rect_left = left if left < rect_left else rect_left
            rect_right = right if right > rect_right else rect_right
            rect_top = top if top < rect_top else rect_top
            rect_bottom = bottom if bottom > rect_bottom else rect_bottom
        if empty:
            return QtCore.QRectF(0, 0, 320, 240)
        sm = ctrl.forest.semantics_manager
        if sm.visible:
            for item in sm.all_items:
                left, top, right, bottom = item.sceneBoundingRect().getCoords()
                rect_left = left if left < rect_left else rect_left
                rect_right = right if right > rect_right else rect_right
                rect_top = top if top < rect_top else rect_top
                rect_bottom = bottom if bottom > rect_bottom else rect_bottom
        width = rect_right - rect_left
        if width < min_width:
            rect_right -= (min_width - width) / 2
            width = min_width
        height = rect_bottom - rect_top
        if height < min_height:
            rect_top -= (min_height - height) / 2
            height = min_height
        return QtCore.QRectF(rect_left, rect_top, width, height)

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
