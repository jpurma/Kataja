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


class Image(Movable, QtWidgets.QGraphicsPixmapItem):

    def __init__(self, img, box=QtCore.QRectF(0, 0, 480, 400), forest=None):
        pixmap = QtGui.QPixmap(img)
        # pixmap=pixmap.scaledToHeight(int(box.height()))
        QtWidgets.QGraphicsPixmapItem.__init__(self, pixmap)
        Movable.__init__(self, forest=forest)
        self.setFlag(QtWidgets.QGraphicsRectItem.ItemIsMovable)
        self.setTransformationMode(QtCore.Qt.SmoothTransformation)
        # self.setPos(pixmap.width()*-.5, pixmap.height()*-.5)
