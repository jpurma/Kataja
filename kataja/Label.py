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

from PyQt5.QtCore import QPointF as Pf
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets
from kataja.parser.LatexToINode import ITextNode, ICommandNode

# ctrl = Controller object, gives accessa to other modules

class LabelDocument(QtGui.QTextDocument):
    """ This extends QTextDocument with ability to read INodes (intermediary nodes) and turn them into QTextDocuments
     RTF presentation """

    def __init__(self):
        QtGui.QTextDocument.__init__(self)

    def run_command(self, command, cursor):
        """
        :param command: latex command that may be translated to rtf formatting commands.
        :param cursor: here we write.
        :param doc: document, required for fetching e.g. font info.
        :return:
        """
        if command == 'emph':
            c = QtGui.QTextCharFormat()
            c.setFontItalic(True)
            cursor.mergeCharFormat(c)
        elif command == '^':
            #c = QtGui.QTextCharFormat()
            c = QtGui.QTextCharFormat()
            c.setVerticalAlignment(QtGui.QTextCharFormat.AlignSuperScript)
            cursor.mergeCharFormat(c)
        elif command == '_':
            c = QtGui.QTextCharFormat()
            c.setVerticalAlignment(QtGui.QTextCharFormat.AlignSubScript)
            c.setFontItalic(True)
            cursor.mergeCharFormat(c)

        #print('got command: %s' % command)


    def write_node_to_document(self, n, cursor):
        """ Recursive node writer. Stores the current charformat, so when the end of formatting scope is reached,
        we can return to previous format.
        :param n: node
        :param cursor: cursor in document, this is the point where we write
        :return:
        """
        if not n:
            return
        old_format = None
        if isinstance(n, ICommandNode) and n.command:
            old_format = QtGui.QTextCharFormat(cursor.charFormat())
            self.run_command(n.command, cursor)
        for part in n.parts:
            if isinstance(part, ITextNode): # ITextNode includes also ICommandNodes and IConstituentNodes
                self.write_node_to_document(part, cursor)
            else:
                cursor.insertText(part)
        if old_format:
            cursor.setCharFormat(old_format)


    def parse_inodes(self, inodes):
        """ Does what it says.
        :param inodes: Node or nodes to be translated. If there are several, linebreak is added between them """
        self.clear()
        cursor = QtGui.QTextCursor(self)
        if isinstance(inodes, tuple) or isinstance(inodes, list):
            for node in inodes:
                self.write_node_to_document(node, cursor)
                cursor.insertText('\n')
        else:
            self.write_node_to_document(inodes, cursor)


class Label(QtWidgets.QGraphicsTextItem):
    """ Labels are names of nodes. Node itself handles all the logic of
    deciding what to show in label, label only calls nodes method to ask for
    text. """

    def __init__(self, parent=None, scene=None):
        """ Give node as parent. Label asks it to produce text to show here """
        QtWidgets.QGraphicsTextItem.__init__(self, parent)
        # self.setTextInteractionFlags(Qt.TextEditable) # .TextInteractionFlag.
        self._source_text = ''
        self._host = parent
        self._ellipse = None
        self._doc = None
        self._hovering = False
        self.y_offset = 0
        self.selectable = False
        self.draggable = False
        self.clickable = False
        self.total_height = 0
        self.setDocument(LabelDocument())

    def get_raw(self):
        return self._host.raw_label_text

    def get_inodes(self):
        return self._host.label_inodes

    def get_plaintext(self):
        """


        :return:
        """
        return self._doc.toPlainText()

    def is_empty(self):
        """


        :return:
        """
        return not bool(self._source_text)

    def update_label(self):
        """ Asks for node/host to give text and update if changed """
        self.setFont(self._host.font)
        raw = self.get_raw()
        if raw:
            if raw != self._source_text:
                self.document().parse_inodes(self.get_inodes())
                self.prepareGeometryChange()
        brect = self.boundingRect()
        self.total_height = brect.height() + self.y_offset
        self.setPos(brect.width() / -2.0, (self.total_height / -2.0) + self.y_offset)
        self._ellipse = QtGui.QPainterPath()
        self._ellipse.addEllipse(Pf(0, self.y_offset), brect.width() / 2, brect.height() / 2)

    def paint(self, painter, option, widget):
        """ Painting is sensitive to mouse/selection issues, but usually with
        :param painter:
        :param option:
        :param widget:
        nodes it is the label of the node that needs complex painting """
        self.setDefaultTextColor(self._host.contextual_color())
        QtWidgets.QGraphicsTextItem.paint(self, painter, option, widget)
