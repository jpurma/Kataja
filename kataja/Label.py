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

from kataja.LabelDocument import LabelDocument
from kataja.parser import INodeToLabelDocument


class Label(QtWidgets.QGraphicsTextItem):
    """ Labels are names of nodes. Node itself handles all the logic of
    deciding what to show in label, label only calls nodes method to ask for
    text. """

    def __init__(self, parent=None):
        """ Give node as parent. Label asks it to produce text to show here """
        QtWidgets.QGraphicsTextItem.__init__(self, parent)
        self._host = parent
        self.y_offset = 0
        self.total_height = 0
        self.setDocument(LabelDocument())

    def update_label(self):
        """ Asks for node/host to give text and update if changed """
        doc = self.document()
        self.setFont(self._host.font)
        self.prepareGeometryChange()
        self.setTextWidth(-1)
        INodeToLabelDocument.parse_inode(self._host.as_inode, doc)
        self.setTextWidth(doc.idealWidth())
        brect = self.boundingRect()
        self.total_height = brect.height() + self.y_offset
        self.setPos(brect.width() / -2.0, (self.total_height / -2.0) + self.y_offset)

    def is_empty(self):
        """ Turning this node into label would result in an empty label.
        :return: bool
        """
        return not self._host.as_inode

    def paint(self, painter, option, widget):
        """ Painting is sensitive to mouse/selection issues, but usually with
        nodes it is the label of the node that needs complex painting
        :param painter:
        :param option:
        :param widget:
        """
        self.setDefaultTextColor(self._host.contextual_color)
        QtWidgets.QGraphicsTextItem.paint(self, painter, option, widget)
