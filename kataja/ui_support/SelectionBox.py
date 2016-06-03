from PyQt5 import QtWidgets


class SelectionBox(QtWidgets.QComboBox):

    def __init__(self, parent):
        QtWidgets.QComboBox.__init__(self, parent)
        self.uses_data = True

    def find_list_item(self, data):
        """ Helper method to check the index of data item in list
        :param data: data to match
        :param selector: QComboBox instance
        :return: -1 if not found, index if found
        """
        return self.findData(data)

    def remove_list_item(self, data):
        """ Helper method to remove items from combo boxes
        :param data: list item's data has to match this
        :param selector: QComboBox instance
        """
        i = self.find_list_item(data)
        if i != -1:
            self.removeItem(i)
        return i

    def add_items(self, values):
        self.uses_data = True
        self.clear()
        for text in values:
            if isinstance(text, tuple):
                text, data = text
                self.addItem(text, data)
            else:
                self.uses_data = False
                self.addItem(text)

    def select_by_text(self, text):
        self.setCurrentText(text)

    def select_by_data(self, data):
        """
        :param data:
        """
        index = self.find_list_item(data)
        #print('selecting data, data %s got index %s' % (data, index))
        self.setCurrentIndex(index)
