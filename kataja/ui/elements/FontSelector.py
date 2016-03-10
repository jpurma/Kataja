from PyQt5 import QtGui
from PyQt5.QtCore import QSize

import kataja.globals as g
from kataja.singletons import qt_prefs, ctrl
from kataja.ui.elements.TableModelComboBox import TableModelComboBox


class FontSelector(TableModelComboBox):
    """

    :param parent:
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setIconSize(QSize(64, 16))
        # self.shape_selector.setView(view)
        items = []
        for key, role in g.FONT_ROLES:
            font = qt_prefs.fonts[key]
            item = QtGui.QStandardItem(role)
            item.setData(key)
            print(key, item.data())
            if ctrl.main.use_tooltips:
                item.setToolTip('%s, %spt' % (font.family(), font.pointSize()))
            item.setFont(font)
            item.setSizeHint(QSize(64, 16))
            items.append(item)
        model = self.model()
        model.setRowCount(len(items))
        for r, item in enumerate(items):
            model.setItem(r, 0, item)
        self.view().setModel(model)
        print(self.currentIndex(), self.currentData(), self.currentText(), self.itemData(0))
        print(self.model())
        self.setCurrentIndex(0)
        self.setModelColumn(0)
        print(self.currentData(), self.currentIndex())

    def add_font(self, font_id, font):
        """

        :param font_id:
        :param font:
        """
        item = QtGui.QStandardItem(font_id)
        item.setData(font_id)
        if ctrl.main.use_tooltips:
            item.setToolTip('%s, %spt' % (font.family(), font.pointSize()))
        item.setFont(font)
        item.setSizeHint(QSize(64, 16))
        self.model().appendRow(item)