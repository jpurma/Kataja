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


class GraphView(QtWidgets.QGraphicsView):
    """ GraphView holds both the viewport into the graph and the QGraphicsScene-object,
    that holds the actual index of graphical objects to be displayed.
    In this case nodes, edges and graphical elements.

    UI-elements are kept in separate scene and separate view.
    """

    def __init__(self, main=None, graph_view=None, graph_scene=None):
        QtWidgets.QGraphicsView.__init__(self)
        self.main = main
        self.graph_scene = graph_scene
        self.setScene(graph_scene)
        self.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        # self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        # self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        # self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        # self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.BoundingRectViewportUpdate)
        self.setOptimizationFlag(QtWidgets.QGraphicsView.DontAdjustForAntialiasing)
        # self.setViewportUpdateMode(QtWidgets.QGraphicsView.SmartViewportUpdate)
        # self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        # self.setViewportUpdateMode(QtWidgets.QGraphicsView.NoViewportUpdate)
        self.setMouseTracking(False)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        # self.setAcceptDrops(True)
        # self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
        self.target_scale = 0
        self.latest_mpe = None

        self._suppressed_drag_mode = self.dragMode()

        self.selection_mode = True
        self._scale_factor = 1.0
        self._fit_scale = 1.0
        self._target_rect = QtCore.QRectF(-300, -300, 300, 300)
        self.zoom_timer = QtCore.QBasicTimer()
        # self.zoom_anim = None
        # self._last_rect = self._target_rect
        self._zoomd = (0, 0, 0, 0)
        self.setSceneRect(-500, -500, 1000, 1000)

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
        sr = self.sceneRect()
        # if self.zoom_anim:
        #    self.zoom_anim.stop()
        if target_rect.right() > sr.right() or target_rect.bottom() > sr.bottom():
            self.setSceneRect(sr + QtCore.QMarginsF(0, 0, 500, 500))
        if target_rect.left() < sr.left() or target_rect.top() < sr.top():
            self.setSceneRect(sr + QtCore.QMarginsF(500, 500, 0, 0))
        self.fitInView(target_rect, 1)
        self._fit_scale = self.transform().m11()
        ctrl.call_watchers(self, 'viewport_changed')

    def scrollContentsBy(self, x, y):
        ctrl.call_watchers(self, 'viewport_changed')
        QtWidgets.QGraphicsView.scrollContentsBy(self, x, y)

    def scale_view_by(self, delta):
        """

        :param delta:
        :return:
        """
        if delta < 1.0 and self._scale_factor == 0.3:
            return self._scale_factor
        elif delta > 1.0 and self._scale_factor == 9.0:
            return self._scale_factor
        factor = self.transform().scale(delta, delta).m11()
        if factor < 0.3:
            factor = 0.3
        elif factor > 9.0:
            factor = 9.0
        self.resetTransform()
        self.scale(factor, factor)
        ctrl.call_watchers(self, 'viewport_changed')
        return factor

    # ## WINDOW ###

    def resizeEvent(self, event):
        """

        :param event:
        """
        QtWidgets.QGraphicsView.resizeEvent(self, event)
        # self._last_rect = self.mapToScene(self.rect()).boundingRect()
        ctrl.call_watchers(self, 'viewport_changed')

    # ######### MOUSE ##############

    def mousePressEvent(self, event):
        """ Here we have a workaround for clicking labels and having editing cursor appear to
        that specific position. We always store last mousePressEvent while they are still events
        and if we have a mousePressEvent that gets used to open the quick editing for label, replay
         it on an interactive QGraphicsTextEdit to let text cursor to jump to pressed location.
        :param event:
        :return:
        """
        self.latest_mpe = event
        self.setFocus(QtCore.Qt.MouseFocusReason)
        QtWidgets.QGraphicsView.mousePressEvent(self, event)

    def replay_mouse_press(self):
        print('replaying mousepressevent')
        self.mousePressEvent(self.latest_mpe)

    def timerEvent(self, event):
        self.zoom_timer.stop()

    def wheelEvent(self, event):
        """

        :param event:
        """
        view_center = self.mapToScene(self.viewport().rect().center())
        pointer_pos = event.pos()
        delta = math.pow(2.0, -event.angleDelta().y() / 360.0)
        if delta != 1.0:
            self.zoom_timer.start(1000, self)
            self._scale_factor = self.scale_view_by(delta)
            if prefs.zoom_to_center:
                if ctrl.selected:
                    if ctrl.single_selection():
                        self.centerOn(ctrl.selected[0].sceneBoundingRect().center())
                    else:
                        br = QtCore.QRectF()
                        for item in ctrl.selected:
                            br = br.united(item.sceneBoundingRect())
                        self.centerOn(br.center())
                else:
                    self.centerOn(view_center)
            elif delta > 1:
                change = (pointer_pos - view_center) * (delta - 1)  # * 0.5
                self.centerOn(view_center + change)
            else:
                self.centerOn(view_center)
            if prefs.auto_pan_select:
                if self.transform().m11() > self._fit_scale:
                    if self.selection_mode:
                        self.set_selection_mode(False)  # Pan mode
                else:
                    if not self.selection_mode:
                        self.set_selection_mode(True)  # Select mode

        # self._last_rect = self.mapToScene(self.rect()).boundingRect()
        self.graph_scene._manual_zoom = True

    def set_selection_mode(self, selection_mode):
        if selection_mode:
            self.selection_mode = True
            self.setDragMode(QtWidgets.QGraphicsView.RubberBandDrag)
        else:
            self.selection_mode = False
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        self._suppressed_drag_mode = self.dragMode()

    def toggle_suppress_drag(self, suppress):
        """ ScrollHandDrag or RubberBandDrag shouldn't register if we are dragging one object
        (GraphScene handles that). This method allows to suppress these drag modes temporarily.
         :param suppress: if true, switch to NoDrag, otherwise restore mode suitable to zoom level
         """
        if suppress:
            self._suppressed_drag_mode = self.dragMode()
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        else:
            self.setDragMode(self._suppressed_drag_mode)
