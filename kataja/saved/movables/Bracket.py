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

from PyQt5 import QtWidgets

# noinspection PyUnresolvedReferences
from PyQt5.QtCore import Qt
from kataja.saved.Movable import Movable
from kataja.singletons import ctrl
from kataja.uniqueness_generator import next_available_type_id


class Bracket(Movable):
    """ Brackets are added as separate characters next to nodes. They are
    created dynamically and shouldn't be saved or loaded. """

    __qt_type_id__ = next_available_type_id()


    def __init__(self, forest=None, host=None, left=True):
        """

        :param Forest forest:
        :param ConstituentNode host:
        :param boolean left:
        """
        super().__init__(forest=forest)
        self.inner = QtWidgets.QGraphicsSimpleTextItem(self)
        self.inner.setParentItem(self)
        self.host = host
        self.setZValue(10)
        self.left = left
        if left:
            self.inner.setText('[')
        else:
            self.inner.setText(']')
        self.selectable = False
        self.draggable = False
        self.clickable = False
        self._hovering = False
        if left:
            self.key = 'lb_%s' % host.uid
        else:
            self.key = 'rb_%s' % host.uid

        self.inner.setBrush(self.host.color)
        self.update_position()
        self.setAcceptHoverEvents(True)
        self.inner.setVisible(True)
        self.fade_in()

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

    def update_position(self):
        """


        """
        adjust = self.boundingRect().width()
        if self.left:
            depth, leftmost = self.forest.bracket_manager.find_leftmost(
                self.host)
            x, y = leftmost.current_scene_position
            my_x = x + leftmost.boundingRect().left() - depth * adjust
        else:
            depth, rightmost = self.forest.bracket_manager.find_rightmost(
                self.host)
            x, y = rightmost.current_scene_position
            my_x = x + rightmost.boundingRect().right() + (depth - 1) * adjust
        my_y = y - self.boundingRect().height() / 2
        self.current_position = my_x, my_y

    def __repr__(self):
        return '<bracket %s>' % self.key

    @property
    def hovering(self):
        return self._hovering

    @hovering.setter
    def hovering(self, value):
        """ Toggle hovering effects and internal bookkeeping
        :param value: bool
        :return:
        """
        if value and not self._hovering:
            self._hovering = True
            self.prepareGeometryChange()
            self.update()
            self.setZValue(150)
        elif (not value) and self._hovering:
            self._hovering = False
            self.prepareGeometryChange()
            self.setZValue(10)
            self.update()

    def hoverEnterEvent(self, event):
        """ Hovering over a bracket is same as hovering over the host
        constituent
        :param event: mouse event
        """
        self.host.hovering = True
        QtWidgets.QGraphicsSimpleTextItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """ Hovering over a bracket is same as hovering over the host
        constituent
        :param event: mouse event
        """
        self.host.hovering = False
        QtWidgets.QGraphicsSimpleTextItem.hoverLeaveEvent(self, event)

    def select(self, event=None, multi=False):
        """ Scene has decided that this node has been clicked
        :param event:
        """
        self._hovering = False
        self.host.select(event)

    def update_selection_status(self):
        """


        """
        pass

    def boundingRect(self):
        return self.inner.boundingRect()

    def paint(self, painter, option, widget):
        """
        :param painter:Painter
        :param option:
        :param widget:
        """
        c = self.host.contextual_color
        painter.setBrush(c)
        if self.hovering:
            painter.setPen(c)
            painter.drawRect(self.boundingRect())
            painter.setPen(Qt.NoPen)
