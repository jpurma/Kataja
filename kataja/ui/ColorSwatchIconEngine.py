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

from PyQt5 import QtGui

from kataja.singletons import ctrl

class ColorSwatchIconEngine(QtGui.QIconEngine):
    """ An icon which you can provide a method to draw on the icon """

    def __init__(self, color_key):
        """
        :param paint_method: a compatible drawing method
        :param owner: an object that is queried for settings for paint_method
        :return:
        """
        QtGui.QIconEngine.__init__(self)
        self.color_key = color_key

    #@caller
    def paint(self, painter, rect, mode, state):
        """

        :param painter:
        :param rect:
        :param mode:
        :param state:
        """
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.fillRect(rect, ctrl.cm.get('background1'))
        c = ctrl.cm.get(self.color_key)
        painter.setPen(c.darker())
        painter.setBrush(c)
        painter.drawRoundedRect(rect, 2, 2)
        #painter.fillRect(rect, ctrl.cm.get(self.color_key))


