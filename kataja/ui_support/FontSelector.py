from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtCore import QSize, pyqtProperty

import kataja.globals as g
from kataja.singletons import qt_prefs, ctrl
from kataja.ui_support.TableModelSelectionBox import TableModelSelectionBox
from saved.movables import Node


class FontDialogForSelector(QtWidgets.QFontDialog):
    """

    :param parent:
    :param role:
    :param initial_font:
    """

    def __init__(self, parent, initial_font):
        super().__init__(parent)
        self.setOption(QtWidgets.QFontDialog.NoButtons)
        self.setCurrentFont(initial_font)
        self.currentFontChanged.connect(parent.receive_font_from_dialog)
        self.show()


class FontSelector(TableModelSelectionBox):
    """

    :param parent:
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.setIconSize(QSize(64, 16))
        self.font_dialog = None
        # self.shape_selector.setView(view)
        self.selected_font = 'main_font'
        #font = qt_prefs.fonts[self.selected_font]
        #self.setFont(font)
        items = []
        for key, role in g.FONT_ROLES:
            font = qt_prefs.fonts[key]
            item = QtGui.QStandardItem(role)
            item.setData(key)
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
        self.setCurrentIndex(0)
        self.setModelColumn(0)
        self.update()

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

    def update_font_selector(self):
        font = qt_prefs.fonts[self.selected_font]
        item = self.find_list_item(self.selected_font)
        if item:
            item.setToolTip('%s, %spt' % (font.family(), font.pointSize()))
            item.setFont(font)
        else:
            self.add_font(self.selected_font, font)
            self.select_by_data(self.selected_font)

    def receive_font_from_dialog(self, font):
        qt_prefs.fonts[self.selected_font] = font
        self.update_font_selector()
        if ctrl.ui.scope_is_selection:
            for node in ctrl.selected:
                if isinstance(node, Node):
                    node.update_label()
        else:
            for node in ctrl.forest.nodes.values():
                node.update_label()
        ctrl.main.trigger_action('select_font_from_dialog')

    def start_font_dialog(self):
        font = qt_prefs.get_font(self.selected_font)
        if self.font_dialog:
            self.font_dialog.setCurrentFont(font)
        else:
            self.font_dialog = FontDialogForSelector(self, font)
        self.font_dialog.show()

    def update_font_dialog(self):
        self.font_dialog.setCurrentFont(qt_prefs.get_font(self.selected_font))
