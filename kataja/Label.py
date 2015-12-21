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
        self.triangle_height = 0
        self.triangle_y = 0
        self.setDocument(LabelDocument())
        self.resizable = False
        self.line_length = 0

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
        if self.line_length:
            self.setTextWidth(200)
        else:
            self.setTextWidth(doc.idealWidth())
        l = doc.lineCount()
        inner_size = doc.size()
        ih = inner_size.height()
        iw = inner_size.width()
        h2 = ih / 2.0
        self.top_y = -h2
        self.bottom_y = h2
        if l <= 1:
            self.top_row_y = 0
            self.bottom_row_y = 0
        else:
            avg_line_height = (ih - 3) / float(l)
            half_height = avg_line_height / 2
            if 'triangle' in doc.lines:
                top_row_found = False
                triangle_found = False
                for i, line in enumerate(doc.lines):
                    if (not top_row_found) and line == 'triangle':
                        if i < 2:
                            self.top_row_y = self.top_y + half_height
                        else:
                            self.top_row_y = self.top_y + (i * avg_line_height) + half_height
                        top_row_found = True
                    if (not triangle_found) and line == 'triangle':
                        self.triangle_y = self.top_y + (i * avg_line_height) + 2
                        triangle_found = True
                    elif triangle_found and line != 'triangle':
                        self.bottom_row_y = self.top_y + (i * avg_line_height) + half_height
                        break
                self.triangle_height = (avg_line_height * 2) - 4
                self.triangle_is_present = True
            else:
                top_row = doc.lines[0]
                self.top_row_y = self.top_y + half_height + 3
                bottom_row_found = False
                for i, line in enumerate(doc.lines):
                    if line != top_row:
                        self.bottom_row_y = self.top_y + (i * avg_line_height) + half_height
                        bottom_row_found = True
                        break
                if not bottom_row_found:
                    self.bottom_row_y = self.top_row_y
                self.triangle_is_present = False
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
