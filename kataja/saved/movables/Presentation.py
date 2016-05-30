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

from PyQt5 import QtCore, QtGui, QtWidgets

from kataja.saved.Movable import Movable


class TextArea(Movable, QtWidgets.QGraphicsTextItem):
    """

    """

    def __init__(self, text='', box=QtCore.QRectF(0, 0, 480, 400), forest=None):
        QtWidgets.QGraphicsTextItem.__init__(self)
        Movable.__init__(self, forest=forest)
        self.setFlag(QtWidgets.QGraphicsRectItem.ItemIsMovable)
        # self.setFlag(QtGui.QGraphicsRectItem.ItemIsSelectable)
        self.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        self.prepareGeometryChange()
        # self.setFont(qt_prefs.get_font)
        # self.setTextWidth(box.width())
        self.set_position(box.x(), box.y(), 0)
        self.host_tree = None
        if text:
            self.setPlainText(text)

    def left(self, **kw):
        """

        :param kw:
        :return:
        """
        return None

    def right(self, **kw):
        """

        :param kw:
        :return:
        """
        return None


class Image(Movable, QtWidgets.QGraphicsPixmapItem):
    """

    """

    def __init__(self, img, box=QtCore.QRectF(0, 0, 480, 400)):
        pixmap = QtGui.QPixmap(img)
        # pixmap=pixmap.scaledToHeight(int(box.height()))
        QtWidgets.QGraphicsPixmapItem.__init__(self, pixmap)
        Movable.__init__(self)
        self.setFlag(QtWidgets.QGraphicsRectItem.ItemIsMovable)
        self.setTransformationMode(QtCore.Qt.SmoothTransformation)
        # self.setPos(pixmap.width()*-.5, pixmap.height()*-.5)

    def left(self, **kw):
        """

        :param kw:
        :return:
        """
        return None

    def right(self, **kw):
        """

        :param kw:
        :return:
        """
        return None


other_types = {'TextArea': TextArea, 'Image': Image}


def GenerateOthers(object_type, data):
    """

    :param object_type:
    :param data:
    """
    other_types[object_type](data)


