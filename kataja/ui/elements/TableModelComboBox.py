from PyQt5 import QtWidgets, QtGui
from PyQt5.QtCore import QSize

import kataja.globals as g


class TableModelComboBox(QtWidgets.QComboBox):
    """

    :param args:
    :param kwargs:
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ambiguous = False

    def find_item(self, data):
        """ Return the item corresponding to this data
        :param data: data to match
        :return: None if not found, item itself if it is found
        """
        model = self.model()
        for i in range(0, model.columnCount()):
            for j in range(0, model.rowCount()):
                item = model.item(j, i)
                if item and item.data() == data:
                    return item
        return None

    def add_and_select_ambiguous_marker(self):
        """


        """
        item = self.find_item(g.AMBIGUOUS_VALUES)
        if item:
            self.setCurrentIndex(item.row())
            self.setModelColumn(item.column())
        else:
            row = []
            for i in range(0, self.model().rowCount()):
                item = QtGui.QStandardItem('---')
                item.setData(g.AMBIGUOUS_VALUES)
                item.setSizeHint(QSize(22, 20))
                row.append(item)
            self.model().insertRow(0, row)
            self.setCurrentIndex(0)
            self.setModelColumn(0)

    def remove_ambiguous_marker(self):
        """


        """
        item = self.find_item(g.AMBIGUOUS_VALUES)
        if item:
            self.model().removeRow(item.row())

    def select_data(self, data):
        """

        :param data:
        :raise hell:
        """
        item = self.find_item(data)
        if item:
            self.setCurrentIndex(item.row())
            self.setModelColumn(item.column())
        else:
            print("couldn't find data %s from selector model" % data)
            raise hell

    def currentData(self, **kwargs):
        """

        :param kwargs:
        :return:
        """
        i = self.view().currentIndex()
        item = self.model().itemFromIndex(i)
        if item:
            return item.data()
        else:
            return None