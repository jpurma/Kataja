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

from PyQt5 import QtGui, QtCore

from kataja.singletons import ctrl


class TwoColorIcon(QtGui.QIcon):
    """ Icons that change their color according to widget where they are """

    #def paint(self, painter, **kwargs):        
    #    print 'using twocoloricon painter'
    #    return QtGui.QIcon.paint(self, painter, kwargs) 

    def __init__(self, filename):
        bitmap = QtGui.QBitmap(filename)
        e = TwoColorIconEngine(bitmap)
        QtGui.QIcon.__init__(self, e)


class TwoColorIconEngine(QtGui.QIconEngine):
    """

    """

    def __init__(self, bitmaps):
        print('*** initializing TwoColorIconEngine with bitmaps ', bitmaps)
        QtGui.QIconEngine.__init__(self)
        if bitmaps:
            self.addPixmap(bitmaps)

    def addPixmap(self, bitmaps):
        """

        :type bitmaps:
        """
        print('*** add pixmap called for engine ***')
        if isinstance(bitmaps, tuple):
            self.bitmaps = bitmaps
            self.bitmaps16 = [bitmap.scaled(16, 16, QtCore.Qt.KeepAspectRatio).mask() for bitmap in bitmaps]
            self.bitmaps32 = [bitmap.scaled(32, 32, QtCore.Qt.KeepAspectRatio).mask() for bitmap in bitmaps]

    #@caller
    def paint(self, painter, rect, mode, state):
        #painter.setCompositionMode(painter.CompositionMode_Source)
        #print 'composition: ', painter.compositionMode()
        #painter.setRenderHints(QtGui.QPainter.Antialiasing, False)
        #painter.setRenderHints(QtGui.QPainter.TextAntialiasing, False)
        #painter.setRenderHints(QtGui.QPainter.SmoothPixmapTransform, False)
        #painter.setRenderHints(QtGui.QPainter.HighQualityAntialiasing, False)
        #painter.setRenderHints(QtGui.QPainter.NonCosmeticDefaultPen, False)
        """

        :param painter:
        :param rect:
        :param mode:
        :param state:
        """
        w = rect.width()
        if w == 16:
            pxm, bmp1, bmp2 = self.bitmaps16
        elif w == 32:
            pxm, bmp1, bmp2 = self.bitmaps32
        else:
            pxm, bmp1, bmp2 = self.bitmaps
        c = ctrl.cm.text()
        if mode == 0:  # normal
            painter.setPen(c)
        elif mode == 1:  # disabled
            painter.setPen(ctrl.cm.inactive(c))
        elif mode == 2:  # hovering
            painter.setPen(ctrl.cm.hovering(c))
        elif mode == 3:  # selected
            painter.setPen(ctrl.cm.active(c))
        painter.fillRect(rect, ctrl.cm.paper())
        painter.drawPixmap(rect, pxm)


