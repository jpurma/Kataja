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
        self._hovering = False
        self.y_offset = 0
        self.selectable = False
        self.draggable = False
        self.clickable = False

    @property
    def get_method(self):
        return self._get_host_text

    @get_method.setter
    def get_method(self, getter):
        """ Assign method that is used to get text for label
        :param getter:
        """
        self._get_host_text = getter

    @property
    def set_method(self):
        return self._set_host_text

    @set_method.setter
    def set_method(self, getter):
        """ Assign method that is used to get text for label
        :param getter:
        """
        self._set_host_text = getter

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
        #self.setDefaultTextColor(self._host.color())
        self.setFont(self._host.font)
        if self.get_method:
            new_source_text = self.get_method()
            if new_source_text != self._source_text:
                self._source_text = str(new_source_text)
                self.prepareGeometryChange()
                if self._doc:
                    self._doc.clear()
                else:
                    self._doc = QtGui.QTextDocument()
                    # self._doc.setUseDesignMetrics(True)
                    self._doc.contentsChanged = self.set_method
                    self.setDocument(self._doc)
                self._doc.setHtml(self._source_text)
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
