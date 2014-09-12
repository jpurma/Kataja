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

from PyQt5 import QtWidgets, QtGui

from kataja.ui.TwoColorIconEngine import TwoColorIconEngine


class TwoColorButton(QtWidgets.QPushButton):
    """ Buttons that change their color according to widget where they are.
        Currently this is not doing anything special that can't be done by setting TwoColorIconEngine for normal button,
        but let's keep this in case we need to deliver palette updates to icon engines.
     """

    def __init__(self, bitmaps, text, parent):
        QtWidgets.QPushButton.__init__(self, parent)
        self.setText(text)
        self.setAutoFillBackground(False)
        e = TwoColorIconEngine(bitmaps)
        i = QtGui.QIcon(e)
        #self.setFlat(False)
        self.setIcon(i)


    def setDefaultAction(self, action):
        stored_icon = self.icon()
        #QtWidgets.QToolButton.setDefaultAction(self, action)
        self.setIcon(stored_icon)
