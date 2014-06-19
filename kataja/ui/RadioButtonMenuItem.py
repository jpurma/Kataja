# coding=utf-8
# #######################################################
from PyQt5 import QtGui

from kataja.ui.CheckBox import CheckBox
from kataja.ui.MenuItem import MenuItem


class RadioButtonMenuItem(MenuItem):
    """

    """

    def __init__(self, parent, action):
        # menu item size should be size of the menu text + some.
        MenuItem.__init__(self, parent, action)
        self.checkbox = CheckBox(self, marker='\u21A9')
        self.checkbox.addToIndex()
        self.checked = action.get('checked', False)

    def boundingRect(self):
        """


        :return:
        """
        return MenuItem.boundingRect(self).adjusted(-8, -4, 13, 0)

    def shape(self):
        """


        :return:
        """
        path = QtGui.QPainterPath()
        path.addRect(MenuItem.boundingRect(self).adjusted(5, 0, 0, 0))
        return path

    def selectOption(self):
        """


        """
        self._parent_menu.selected_radio_menu(self)
