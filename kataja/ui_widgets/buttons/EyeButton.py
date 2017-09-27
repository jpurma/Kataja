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

from kataja.ui_widgets.buttons.PanelButton import PanelButton
from kataja.singletons import ctrl, qt_prefs


class EyeButton(PanelButton):
    """ This is a special kind of button where checked -state shows eye icon and not checked is
    an empty rectangle. Hovering over button shows eye, darker.

    """

    def __init__(self, **kwargs):
        self.checked_icon = None
        self.hover_icon = None
        PanelButton.__init__(self, qt_prefs.eye_pixmap, size=24, **kwargs)
        self.setFixedSize(QtCore.QSize(32, 26))
        self.value = False
        self._hover = False
        self.setCheckable(True)

    def compose_icon(self):
        """ Redraw the image to be used as a basis for icon, this is necessary
        to update the overlay color.
        :return:
        """
        c = ctrl.cm.get(self.color_key)
        image = self.colored_image_from_base(c)
        image2 = self.colored_image_from_base(c.darker())
        pm1 = QtGui.QPixmap().fromImage(image)
        pm2 = QtGui.QPixmap().fromImage(image2)
        self.normal_icon = QtGui.QIcon(QtGui.QPixmap())
        self.checked_icon = QtGui.QIcon(pm1)
        self.hover_icon = QtGui.QIcon(pm2)
        if self.isChecked():
            self.setIcon(self.checked_icon)
        else:
            self.setIcon(self.normal_icon)

    def checkStateSet(self):
        super().checkStateSet()
        self.update_icon_mode()

    def nextCheckState(self):
        super().nextCheckState()
        self.update_icon_mode()

    def update_icon_mode(self):
        checked = self.isChecked()
        if self._hover:
            self.setIcon(self.hover_icon)
        elif checked:
            self.setIcon(self.checked_icon)
        else:
            self.setIcon(self.normal_icon)

    def enterEvent(self, e):
        self._hover = True
        self.update_icon_mode()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self.update_icon_mode()
        super().leaveEvent(e)
