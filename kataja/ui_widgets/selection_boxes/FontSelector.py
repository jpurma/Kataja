from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QSize

import kataja.globals as g
from kataja.saved.movables.Node import Node
from kataja.singletons import qt_prefs, ctrl
from kataja.ui_widgets.selection_boxes.TableModelSelectionBox import TableModelSelectionBox

stylesheet = """
QComboBox {
    background: transparent;
    border: 1px solid transparent;
}
QComboBox:hover {
    background: transparent;
    border: 1px solid %(current)s;
}

QComboBox::drop-down {
    border: 1px solid transparent;
}

QComboBox::down-arrow {
    image: url(resources/icons/text_format24.png);
    width: 16px;
    height: 16px;
}


"""


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

    def __init__(self, **kwargs):
        TableModelSelectionBox.__init__(self, **kwargs)
        self.setMaximumWidth(20)
        self.setMinimumWidth(20)
        # self.setIconSize(QSize(92, 16))
        self.font_dialog = None
        # self.shape_selector.setView(view)
        self.selected_font = 'main_font'
        self.old_index = 0
        self.old_text = ''
        # self.setAutoFillBackground(False)
        self.setStyleSheet(stylesheet % {
            'current': 'transparent'
        })
        font = qt_prefs.fonts[self.selected_font]
        self.setFont(font)
        items = []
        for key, role in g.FONT_ROLES:
            font = qt_prefs.fonts[key]
            item = QtGui.QStandardItem(role)
            item.setData(key)
            item.setFont(font)
            item.setBackground(ctrl.cm.paper())
            item.setSizeHint(QSize(64, 16))  # →
            font_button = QtGui.QStandardItem(': %s, %spt' % (font.family(), font.pointSize()))
            font_button.setData('font_picker::' + key)
            if ctrl.main.use_tooltips:
                item.setToolTip('Use font associated with this role')
                font_button.setToolTip(
                    "Replace '%s, %spt' for '%s'" % (font.family(), font.pointSize(), role))
            font_button.setFont(font)
            font_button.setSizeHint(QSize(112, 16))
            items.append((item, font_button))
        model = self.model()
        model.clear()
        model.setRowCount(len(items))
        for r, item_tuple in enumerate(items):
            item, font_button = item_tuple
            model.setItem(r, 0, item)
            model.setItem(r, 1, font_button)

        view = QtWidgets.QTableView()
        view.horizontalHeader().hide()
        view.verticalHeader().hide()
        view.setCornerButtonEnabled(False)
        view.setModel(model)
        view.resizeColumnsToContents()
        view.setMinimumWidth(178)
        self.setView(view)
        self.setCurrentIndex(0)
        self.setModelColumn(0)
        self.update()

    def update_font_selector(self):
        font = qt_prefs.fonts[self.selected_font]
        item = None
        font_item = None
        model = self.model()
        for j in range(0, model.rowCount()):
            item = model.item(j, 0)
            if item and item.data() == self.selected_font:
                font_item = model.item(j, 1)
                break
        if item and font_item:
            item.setFont(font)
            font_item.setFont(font)
            if ctrl.main.use_tooltips:
                item.setToolTip('Use font associated with this role')
                font_item.setToolTip(
                    "Replace '%s, %spt' for '%s'" % (font.family(), font.pointSize(), item.text()))
        self.select_by_data(self.selected_font)

    def receive_font_from_dialog(self, font):
        qt_prefs.fonts[self.selected_font] = font
        self.update_font_selector()
        if ctrl.ui.scope_is_selection:
            for node in ctrl.get_selected_nodes():
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

    def set_color(self, color_key):
        self.setStyleSheet(stylesheet % {
            'current': ctrl.cm.get(color_key).name()
        })

    def set_dialog_font(self, font):
        if self.font_dialog:
            self.font_dialog.setCurrentFont(font)

    def select_by_data(self, data):
        """ Override TableModelSelectionBox to include setFont and avoiding selecting font_dialog
        triggers.
        :param data:
        """
        if data.startswith('font_picker::'):
            data = data.split('::')[1]

        item = self.find_list_item(data)
        if item:
            self.setCurrentIndex(item.row())
            self.setModelColumn(item.column())

            self.selected_font = data
            font = qt_prefs.get_font(data)
            self.setFont(font)
            if ctrl.main.use_tooltips:
                self.setToolTip(f"{item.text()}: {font.family()}, {font.pointSize()}pt")
        else:
            print("couldn't find data %s from selector model" % data)
