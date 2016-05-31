from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QSize
from kataja.ui_support.TableModelSelectionBox import TableModelSelectionBox
from kataja.singletons import ctrl
from kataja.ui_support.LineColorIcon import LineColorIcon


class ColorSelector(TableModelSelectionBox):
    """

    :param parent:
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setIconSize(QSize(16, 16))
        self.setMinimumWidth(40)
        self.setMaximumWidth(40)
        colors = []
        model = self.model()
        for c in ctrl.cm.color_keys + ctrl.cm.custom_colors:
            item = QtGui.QStandardItem(LineColorIcon(c, model), '')
            item.setData(c)
            item.setSizeHint(QSize(22, 20))
            colors.append(item)
        view = QtWidgets.QTableView()

        # add_icon = QtGui.QIcon()
        # add_icon.fromTheme("list-add")
        # add_item = QtGui.QStandardItem('+')
        # add_item.setTextAlignment(QtCore.Qt.AlignCenter)
        # add_item.setSizeHint(QSize(22, 20))
        self.table = [colors[0:5] + colors[21:24], colors[5:13], colors[13:21],
                      colors[24:31]]  # + [add_item]
        model.clear()
        # model.setRowCount(8)
        # model.setColumnCount(4)
        model.selected_color = 'content1'
        model.default_color = 'content1'
        for c, column in enumerate(self.table):
            for r, item in enumerate(column):
                model.setItem(r, c, item)
        view.horizontalHeader().hide()
        view.verticalHeader().hide()
        view.setCornerButtonEnabled(False)
        view.setModel(self.model())
        view.resizeColumnsToContents()
        cw = view.columnWidth(0)
        view.setMinimumWidth(self.model().columnCount() * cw)
        self.setView(view)

    def select_by_data(self, data):
        """
        :param data:
        """
        super().select_by_data(data)
        self.model().selected_color = data
