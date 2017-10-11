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
from kataja.utils import colored_image


class EyeButton(PanelButton):
    """ This is a special kind of button where checked -state shows eye icon and not checked is
    an empty rectangle. Hovering over button shows eye, darker.

    """

    def __init__(self, width=32, height=26, **kwargs):
        self.checked_icon = None
        self.pixmap1 = qt_prefs.eye_pixmap
        PanelButton.__init__(self, qt_prefs.closed_eye_pixmap, size=height - 2, **kwargs)
        self.setFixedSize(QtCore.QSize(width, height))
        self.value = False
        self.setCheckable(True)

    def compose_icon(self):
        """ Redraw the image to be used as a basis for icon, this is necessary
        to update the overlay color.
        :return:
        """
        c = ctrl.cm.get(self.color_key)
        image = colored_image(c, self.base_image)
        checked_image = colored_image(c, self.pixmap1)
        self.normal_icon = QtGui.QIcon(QtGui.QPixmap().fromImage(image))
        self.checked_icon = QtGui.QIcon(QtGui.QPixmap().fromImage(checked_image))
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
        self.setIcon(self.checked_icon if self.isChecked() else self.normal_icon)
