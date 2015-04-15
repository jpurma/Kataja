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
from kataja.singletons import ctrl
import kataja.globals as g
from utils import time_me


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
        # self.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        # self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        # self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        # self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        # self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)

        # if ctrl.move_tool:
        self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
        # elif ctrl.selection_tool:
        # self.setDragMode(QtGui.QGraphicsView.RubberBandDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # self.setViewportUpdateMode(QtWidgets.QGraphicsView.BoundingRectViewportUpdate)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        # self.setViewportUpdateMode(QtWidgets.QGraphicsView.NoViewportUpdate)
        self.setFocusPolicy(QtCore.Qt.NoFocus)
        self.setMouseTracking(False)
        #self.setAcceptDrops(True)
        # self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
        self.target_scale = 0
        self._scale_factor = 1.0
        self._target_rect = QtCore.QRectF(-300, -300, 300, 300)
        self.zoom_timer = QtCore.QBasicTimer()

    # def drawBackground(self, painter, rect):
    # painter.fillRect(rect, colors.paper)
    #@time_me
    def instant_fit_to_view(self, target_rect):
        """ Fit the current scene into view, snugly
        :param target_rect: scene rect that contains all of the items we want to fit into view.
        """
        self.setSceneRect(target_rect)
        self.fitInView(target_rect, 1)
        #new_scale = min((self.width() / target_rect.width(), self.height() / target_rect.height()))
        #self.target_scale = new_scale
        #self.resetTransform()
        #self.scale(self.target_scale, self.target_scale)
        self.main.ui_manager.update_positions()

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
        self.main.ui_manager.update_positions()
        return factor

    # ## WINDOW ###

    def resizeEvent(self, event):
        """

        :param event:
        """
        QtWidgets.QGraphicsView.resizeEvent(self, event)
        if hasattr(self.main, 'ui_manager'):
            self.main.ui_manager.update_positions()

    # ######### MOUSE ##############

    def mouseReleaseEvent(self, event):
        """

        :param event:
        """
        print("mouseReleaseEvent")
        QtWidgets.QGraphicsView.mouseReleaseEvent(self, event)

    def mouseMoveEvent(self, event):
        """

        :param event:
        """
        QtWidgets.QGraphicsView.mouseMoveEvent(self, event)

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
            if delta > 1:
                change = (pointer_pos - view_center) * (delta - 1) * 0.5
                self.centerOn(view_center + change)
            else:
                self.centerOn(view_center)
        self.graph_scene._manual_zoom = True

        # QtWidgets.QGraphicsView.wheelEvent(self, event)

    # def event(self, ev):
    # if ev.type() == QtCore.QEvent.Gesture:
    # print ev, ev.type()
    # elif ev.type() == QtCore.QEvent.Wheel:
    # print 'wheel!'
    #             print ev.pixelDelta().y()
    #             wel = QtGui.QWheelEvent(ev) #.QWheelEvent(ev)
    #             print wel.angleDelta().y()
    #         elif ev.type() == QtCore.QEvent.GraphicsSceneWheel:
    #             print 'gs wheel!'
    #
    #         return QtWidgets.QGraphicsView.event(self, ev)

    # def leaveEvent(self, event):
    #     # ctrl.scene.kill_dragging()
    #     """
    #
    #     :param event:
    #     """
    #     QtWidgets.QGraphicsView.leaveEvent(self, event)
    #
    # def enterEvent(self, event):
    #     # ctrl.scene.kill_dragging()
    #     """
    #
    #     :param event:
    #     """
    #     QtWidgets.QGraphicsView.enterEvent(self, event)
    #
