#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#############################################################################
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

from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui, QtWidgets

class UIView(QtWidgets.QGraphicsView):
    """ UI layer contains Graph layer  (GraphView) """

    def __init__(self, main = None, ui_scene = None):
        """ UIView contains UIManager, which contains GraphView (content_view),
        which contains GraphScene where all graph items are. """
        QtWidgets.QGraphicsView.__init__(self, main)
        self.main = main
        self.ui_scene = ui_scene
        self.setScene(ui_scene)
        # why this is still taking mouse move events?
        # self.setMouseTracking(False)
        self.setCacheMode(QtWidgets.QGraphicsView.CacheBackground)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        #self.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.TextAntialiasing)
        # QtGui.QPainter.SmoothPixmapTransform

    def resizeEvent(self, event):
        """ Full screen mode causes resize event to happen here, but not in 
        graph scene item """
        self.main.graph_view.resize(event.size())
        self.ui_scene.resize_ui(event.size())
        QtWidgets.QGraphicsView.resizeEvent(self, event)
