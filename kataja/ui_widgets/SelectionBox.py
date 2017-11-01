from PyQt5 import QtWidgets, QtCore, QtGui

from kataja.UIItem import UIWidget
from kataja.singletons import ctrl


class SelectionBox(QtWidgets.QComboBox, UIWidget):
    action_slot = 'activated'

    def __init__(self, parent=None, data=None, action='', mini=False, **kwargs):
        QtWidgets.QComboBox.__init__(self, parent)
        UIWidget.__init__(self, **kwargs)
        self.uses_data = True
        if data is None:
            data = []
        self.add_items(data)
        if mini:
            self.setMinimumSize(QtCore.QSize(40, 20))
            self.setMaximumSize(QtCore.QSize(40, 20))
        if action:
            ctrl.ui.connect_element_to_action(self, action)
        #if data:
        #    self.disable_choice(data[0])

    def disable_choice(self, choice):
        index = self.findData(choice)
        m = self.model()
        item = m.item(index, 0)
        print(item)

    def rebuild_choices(self, data):
        current = self.currentData()
        self.add_items(data)
        self.select_by_data(current)

    def find_list_item(self, data):
        """ Helper method to check the index of data item in list
        :param data: data to match
        :return: -1 if not found, index if found
        """
        return self.findData(data)

    def remove_list_item(self, data):
        """ Helper method to remove items from combo boxes
        :param data: list item's data has to match this
        """
        i = self.find_list_item(data)
        if i != -1:
            self.removeItem(i)
        return i

    def add_items(self, values):
        self.uses_data = True
        self.clear()
        for value in values:
            if isinstance(value, tuple):
                data, text = value
                self.addItem(text, data)
            else:
                self.uses_data = False
                self.addItem(value)

    def set_displayed_value(self, value):
        if self.uses_data:
            self.select_by_data(value)
        else:
            self.select_by_text(value)

    def select_by_text(self, text):
        self.setCurrentText(text)

    def select_by_data(self, data):
        """
        :param data:
        """
        index = self.find_list_item(data)
        if index != -1:
            self.setCurrentIndex(index)
