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
        self.top_y = 0
        self.top_row_y = 0
        self.bottom_row_y = 0
        self.bottom_y = 0
        self.triangle_is_present = False
        self.triangle_height = 20
        self.triangle_y = 0
        self.setDocument(LabelDocument())

    def update_label(self, font, inode):
        """ Asks for node/host to give text and update if changed
        :param font: provide font to use for label document
        :param inode: provide inode to parse to label document
        """
        doc = self.document()
        self.setFont(font)
        self.prepareGeometryChange()
        self.setTextWidth(-1)
        INodeToLabelDocument.parse_inode(inode, doc)
        self.setTextWidth(doc.idealWidth())
        l = doc.lineCount()
        print(doc.lines)
        inner_size = doc.size()
        ih = inner_size.height()
        iw = inner_size.width()
        h2 = ih / 2.0
        self.top_y = -h2
        if l > 1:
            if self.triangle_is_present:
                avg_line_height = (ih - self.triangle_height - 3) / float(l)
                ah = (self.triangle_height + avg_line_height) / 2
                self.top_row_y = -ah
                self.bottom_row_y = ah
            else:
                avg_line_height = (ih - 3) / float(l)
                ah = avg_line_height / 2
                self.top_row_y = -ah
                self.bottom_row_y = ah
        else:
            avg_line_height = ih
            self.top_row_y = 0
            self.bottom_row_y = 0
        self.triangle_y = self.top_row_y + avg_line_height
        #print(self.top_row_y, self.bottom_row_y)
        self.bottom_y = h2
        self.setPos(iw / -2.0, self.top_y)


    def is_empty(self):
        """ Turning this node into label would result in an empty label.
        :return: bool
        """
        return not self._host.as_inode()


    def get_top_row_y(self):
        return self.top_row_y

    def get_bottom_row_y(self):
        return self.bottom_row_y


    def paint(self, painter, option, widget):
        """ Painting is sensitive to mouse/selection issues, but usually with
        nodes it is the label of the node that needs complex painting
        :param painter:
        :param option:
        :param widget:
        """
        self.setDefaultTextColor(self._host.contextual_color)
        QtWidgets.QGraphicsTextItem.paint(self, painter, option, widget)
