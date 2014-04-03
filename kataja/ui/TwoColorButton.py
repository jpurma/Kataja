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

from kataja.ui.TwoColorIcon import TwoColorIconEngine
from PyQt5 import QtWidgets, QtGui


class TwoColorButton(QtWidgets.QPushButton):
    """ Buttons that change their color according to widget where they are """

    def __init__(self, bitmaps, text, parent):
        QtWidgets.QPushButton.__init__(self, text, parent)
        self.setAutoFillBackground(True)
        e = TwoColorIconEngine(bitmaps)
        i = QtGui.QIcon(e)
        self.setFlat(True)
        self.setIcon(i)


    #def paint(self, painter, **kwargs):        
    #    print 'using twocoloricon painter'
    #    return QtGui.QIcon.paint(self, painter, kwargs) 

    def paintEvent(self, event):
        #print 'got PaintEvent'
        #print self.icon(), self.iconSize(), type(self.icon())
        QtWidgets.QPushButton.paintEvent(self, event)
        


