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

class DrawnIconEngine(QtGui.QIconEngine):
    """ An icon which you can provide a method to draw on the icon """

    def __init__(self, paint_method, owner):
        """
        :param paint_method: a compatible drawing method
        :param owner: an object that is queried for settings for paint_method
        :return:
        """
        QtGui.QIconEngine.__init__(self)
        self.paint_method = paint_method
        self.owner = owner

    #@caller
    def paint(self, painter, rect, mode, state):
        """

        :param painter:
        :param rect:
        :param mode:
        :param state:
        """
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        settings = self.owner.paint_settings()
        c = settings['color']
        p = ctrl.cm.paper2()
        if mode == 0:  # normal
            painter.setPen(c)
            painter.fillRect(rect, p)
        elif mode == 1:  # disabled
            painter.setPen(ctrl.cm.inactive(c))
            painter.fillRect(rect, ctrl.cm.inactive(p))
        elif mode == 2:  # hovering
            painter.setPen(ctrl.cm.hovering(c))
            painter.fillRect(rect, ctrl.cm.hovering(p))
        elif mode == 3:  # selected
            painter.setPen(ctrl.cm.active(c))
            painter.fillRect(rect, ctrl.cm.active(p))
        else:
            painter.setPen(c)
            painter.fillRect(rect, p)
            print('Weird button mode: ', mode)

        self.paint_method(painter, rect, **settings)


