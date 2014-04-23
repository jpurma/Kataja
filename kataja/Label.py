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

from PyQt5.QtCore import QPointF as Pf
import PyQt5.QtGui as QtGui
import PyQt5.QtWidgets as QtWidgets

# ctrl = Controller object, gives accessa to other modules


class Label(QtWidgets.QGraphicsTextItem):
    """ Labels are names of nodes. Node itself handles all the logic of
    deciding what to show in label, label only calls nodes method to ask for
    text. """

    def __init__(self, parent=None, scene=None):
        """ Give node as parent. Label asks it to produce text to show here """
        QtWidgets.QGraphicsTextItem.__init__(self, parent)
        # self.setTextInteractionFlags(Qt.TextEditable) # .TextInteractionFlag.
        self._source_text = ''
        self._get_host_text = None
        self._set_host_text = None
        self._host = parent
        self._ellipse = None
        self._doc = None
        # self.setFont(self._host.label_font)
        # self.setDefaultTextColor(self._host.color)
        self._hovering = False
        self.selectable = False
        self.draggable = False
        self.clickable = False

    def set_get_method(self, getter):
        """ Assign method that is used to get text for label """
        self._get_host_text = getter

    def get_plaintext(self):
        return self._doc.toPlainText()

    def set_set_method(self, setter):
        """ Assign method that is called when label is edited """
        self._set_host_text = setter

    def is_empty(self):
        return not bool(self._source_text)

    def update_label(self):
        """ Asks for node/host to give text and update if changed """
        #self.setDefaultTextColor(self._host.color())
        self.setFont(self._host.label_font)
        new_source_text = self._get_host_text()
        if new_source_text == self._source_text:
            return False
        self._source_text = new_source_text
        self.prepareGeometryChange()
        if self._doc:
            self._doc.clear()
        else:
            self._doc = QtGui.QTextDocument()
            # self._doc.setUseDesignMetrics(True)
            self._doc.contentsChanged = self._set_host_text
            self.setDocument(self._doc)
        self._doc.setHtml(self._source_text)
        brect = self.boundingRect()
        self.setPos(brect.width() / -2.0, brect.height() / -2.0)
        self._ellipse = QtGui.QPainterPath()
        self._ellipse.addEllipse(Pf(0, 0), brect.width() / 2, brect.height() / 2)
        return True

    def update_position(self, br=None):
        brect = br or self.boundingRect()
        self.setPos(brect.width() / -2.0, brect.height() / -2.0)

    def paint(self, painter, option, widget):
        """ Painting is sensitive to mouse/selection issues, but usually with
        nodes it is the label of the node that needs complex painting """
        self.setDefaultTextColor(self._host.contextual_color())
        QtWidgets.QGraphicsTextItem.paint(self, painter, option, widget)
