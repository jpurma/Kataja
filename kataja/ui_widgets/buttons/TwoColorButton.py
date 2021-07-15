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

from PyQt6 import QtGui, QtCore

from kataja.singletons import ctrl
from kataja.ui_widgets.PushButtonBase import PushButtonBase


class TwoColorIconEngine(QtGui.QIconEngine):
    """ An icon that is drawn from two binary pixmaps with colors provided by the app environment.
        The benefit is that the icons can adjust their colors based on the environment and with two colors
        there are more possibilities for making the icons pretty.
    """

    def __init__(self, bitmaps=None):
        QtGui.QIconEngine.__init__(self)
        self.mono = True
        self.bitmap = None
        self.filter1 = None
        self.filter2 = None
        self.mask = None
        if bitmaps:
            self.addPixmap(bitmaps)

    def pixmap(self, QSize, QIcon_Mode=None, QIcon_State=None):
        pm = QtGui.QIconEngine.pixmap(self, QSize, QIcon_Mode, QIcon_State)
        if self.mask:
            pm.setMask(QtGui.QBitmap(self.mask.scaled(QSize, QtCore.Qt.AspectRatioMode.KeepAspectRatio)))
        return pm

    def addPixmap(self, bitmaps, **kwargs):
        """ Overrides addPixmap, allowing tuple of bitmaps as an input to provide all necessary
        color layers.
        :type bitmaps: filename, tuple of bitmaps or instance of QPixmap
        :param kwargs: not used
        """
        if isinstance(bitmaps, str):
            bitmaps = QtGui.QPixmap(bitmaps)

        if isinstance(bitmaps, tuple):
            self.mono = False
            self.bitmap = bitmaps[0]
            self.filter1 = bitmaps[1]
            self.filter2 = bitmaps[2]
            self.mask = self.bitmap.mask()

        elif isinstance(bitmaps, QtGui.QPixmap):
            self.mono = True
            self.bitmap = bitmaps
            self.filter1 = None
            self.filter2 = None
            self.mask = self.bitmap.mask()

    # @time_me
    def paint(self, painter, rect, mode: QtGui.QIcon.Mode, state: QtGui.QIcon.State):
        """

        :param painter:
        :param rect:
        :param mode:
        :param state:
        """
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        c = ctrl.cm.ui()
        if mode == QtGui.QIcon.Mode.Normal:
            painter.setPen(c)
        elif mode == QtGui.QIcon.Mode.Disabled:
            painter.setPen(ctrl.cm.inactive(c))
        elif mode == QtGui.QIcon.Mode.Selected:
            painter.setPen(ctrl.cm.hovering(c))
        elif mode == QtGui.QIcon.Mode.Active:
            painter.setPen(ctrl.cm.active(c))
        else:
            painter.setPen(c)
            print('Weird button mode: ', mode)
        #
        # print(painter.backgroundMode(), painter.background(), QtCore.Qt.OpaqueMode, QtCore.Qt.GlobalColor.NoPenMode)
        #

        if self.mono:
            painter.drawPixmap(rect, self.mask)
        else:
            painter.drawPixmap(rect, self.filter1)
            painter.setPen(c.darker())
            painter.drawPixmap(rect, self.filter2)


class TwoColorButton(PushButtonBase):
    """ Buttons that change their color according to widget where they are.
        Currently this is not doing anything special that can't be done by setting
        TwoColorIconEngine for normal button,
        but let's keep this in case we need to deliver palette updates to icon engines.
     """

    def __init__(self, bitmaps=None, **kwargs):
        PushButtonBase.__init__(self, **kwargs)
        if bitmaps:
            e = TwoColorIconEngine(bitmaps)
            i = QtGui.QIcon(e)
            self.setIcon(i)
