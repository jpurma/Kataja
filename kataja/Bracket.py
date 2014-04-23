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

from PyQt5 import QtWidgets

# noinspection PyUnresolvedReferences
from PyQt5.QtCore import Qt
from kataja.Controller import ctrl
from kataja.Movable import Movable


class Bracket(Movable, QtWidgets.QGraphicsSimpleTextItem):
    """ Brackets are added as separate characters next to nodes. They are created dynamically and shouldn't be saved or loaded. """

    @staticmethod
    def create_key(host, left=True):
        """

        :param Movable host:
        :param boolean left:
        """


    def __init__(self, forest, host=None, left=True):
        """

        :param Forest forest:
        :param ConstituentNode host:
        :param boolean left:
        """
        QtWidgets.QGraphicsSimpleTextItem.__init__(self)
        Movable.__init__(self, forest)
        self.host = host
        self.setZValue(3)
        self.left = left
        if left:
            self.setText('[')
        else:
            self.setText(']')
        self.selectable = False
        self.draggable = False
        self.clickable = False
        self._hovering = False
        if left:
            self.key = 'lb_%s' % host.save_key
        else:
            self.key = 'rb_%s' % host.save_key

        intern(self.key)
        self.setBrush(self.host.color())
        self.update_position()
        self.setAcceptHoverEvents(True)
        self.setVisible(self.host.has_visible_brackets)

    def update_position(self):
        adjust = self.boundingRect().width()
        steps = 0
        if self.left:
            node = self.host
            left = self.host.left()
            while left:
                steps += 1
                node = left
                left = node.left()
            x, y, z = node.get_current_position()
            my_x = x + node.boundingRect().left() - steps * adjust
        else:
            node = self.host
            right = self.host.right()
            while right:
                steps += 1
                node = right
                right = node.right()
            x, y, z = node.get_current_position()
            my_x = x + node.boundingRect().right() + (steps - 1) * adjust
        my_y = y - self.boundingRect().height() / 2
        self.set_current_position((my_x, my_y, z))

    def __repr__(self):
        return '<bracket %s>' % self.key

    def hoverEnterEvent(self, event):
        if not self._hovering:
            self.host._hovering = True
            self.host.left_bracket._hovering = True
            self.host.right_bracket._hovering = True
            self.prepareGeometryChange()
            self.host.left_bracket.update()
            self.host.right_bracket.update()
            self.host.update()
        QtWidgets.QGraphicsSimpleTextItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        if self._hovering:
            self.host.left_bracket._hovering = False
            self.host.right_bracket._hovering = False
            self.host._hovering = False
            self.prepareGeometryChange()
            self.host.left_bracket.update()
            self.host.right_bracket.update()
            self.host.update()

    def click(self, event=None):
        """ Scene has decided that this node has been clicked """
        self._hovering = False
        self.host.click(event)


    def set_selection_status(self):
        pass

    def paint(self, painter, option, widget):
        """
        :param painter:Painter
        :param option:
        :param widget:
        """
        c = self.host.contextual_color()
        painter.setBrush(c)
        if self._hovering:
            painter.setPen(c)
            painter.drawRect(self.boundingRect())
            painter.setPen(Qt.NoPen)
        QtWidgets.QGraphicsSimpleTextItem.paint(self, painter, option, widget)



