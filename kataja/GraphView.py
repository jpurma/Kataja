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

import PyQt6.QtCore as QtCore
import PyQt6.QtGui as QtGui
import PyQt6.QtWidgets as QtWidgets
from PyQt6.QtCore import Qt

from kataja.singletons import ctrl


class GraphView(QtWidgets.QGraphicsView):
    """ GraphView is the viewport into the graph and it holds the GraphScene, which
    has the actual map of graphical objects, and ViewManager, which has all the logic
    related to choosing what part of the scene GraphView should display.

    UI-elements are kept in separate scene and separate view.
    """

    def __init__(self, graph_scene):
        QtWidgets.QGraphicsView.__init__(self)
        self.setScene(graph_scene)
        self.setCacheMode(QtWidgets.QGraphicsView.CacheModeFlag.CacheBackground)
        self.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        # self.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
        # self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        # self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        # self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        # self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorViewCenter)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setResizeAnchor(QtWidgets.QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportUpdateMode(QtWidgets.QGraphicsView.ViewportUpdateMode.BoundingRectViewportUpdate)
        self.setOptimizationFlag(QtWidgets.QGraphicsView.OptimizationFlag.DontAdjustForAntialiasing)
        # self.setViewportUpdateMode(QtWidgets.QGraphicsView.SmartViewportUpdate)
        # self.setViewportUpdateMode(QtWidgets.QGraphicsView.FullViewportUpdate)
        # self.setViewportUpdateMode(QtWidgets.QGraphicsView.NoViewportUpdate)
        self.setMouseTracking(False)
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        # self.setAcceptDrops(True)
        # self.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
        self.latest_mpe = None
        self.setSceneRect(-500, -500, 1000, 1000)
        self.selection_mode = True
        self._suppressed_drag_mode = self.dragMode()

    def scrollContentsBy(self, x, y):
        QtWidgets.QGraphicsView.scrollContentsBy(self, x, y)
        ctrl.main.viewport_moved.emit()

    def resizeEvent(self, event):
        QtWidgets.QGraphicsView.resizeEvent(self, event)
        ctrl.main.viewport_resized.emit()

    def mousePressEvent(self, event):
        """ Here we have a workaround for clicking labels and having editing cursor appear to
        that specific position. We always store last mousePressEvent while they are still events
        and if we have a mousePressEvent that gets used to open the quick editing for label, replay
         it on an interactive QGraphicsTextEdit to let text cursor to jump to pressed location.
        :param event:
        :return:
        """
        self.latest_mpe = event
        self.setFocus(QtCore.Qt.FocusReason.MouseFocusReason)
        QtWidgets.QGraphicsView.mousePressEvent(self, event)

    def replay_mouse_press(self):
        print('replaying mousepressevent')
        self.mousePressEvent(self.latest_mpe)

    def wheelEvent(self, event):
        ctrl.view_manager.zoom_by_angle(event.position(), event.angleDelta().y())

    def toggle_suppress_drag(self, suppress):
        """ ScrollHandDrag or RubberBandDrag shouldn't register if we are dragging one object
        (GraphScene handles that). This method allows to suppress these drag modes temporarily.
         :param suppress: if true, switch to NoDrag, otherwise restore mode suitable to zoom level
         """
        if suppress:
            self._suppressed_drag_mode = self.dragMode()
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.NoDrag)
        else:
            self.setDragMode(self._suppressed_drag_mode)

    def set_selection_mode(self, selection_mode):
        if self.selection_mode == selection_mode:
            return
        if selection_mode:
            self.selection_mode = True
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.RubberBandDrag)
        else:
            self.selection_mode = False
            self.setDragMode(QtWidgets.QGraphicsView.DragMode.ScrollHandDrag)
        self._suppressed_drag_mode = self.dragMode()
