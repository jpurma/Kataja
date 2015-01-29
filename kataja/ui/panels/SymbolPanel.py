from PyQt5 import QtWidgets, QtCore

from kataja.ui.panels.UIPanel import UIPanel
from kataja.parser.latex_to_unicode import latex_to_unicode
from kataja.singletons import qt_prefs, ctrl
import kataja.globals as g
from utils import time_me

__author__ = 'purma'

table_names = ['greek', 'latin', 'combining', 'arrows', 'rest', 'cyrchar', 'ding', 'ElsevierGlyph', 'mathbb', 'mathbf',
               'mathbit', 'mathfrak', 'mathmit', 'mathscr', 'mathsfbfsl', 'mathsfbf', 'mathsfsl', 'mathsf',
               'mathslbb', 'mathsl', 'mathtt']

table_dict = {
    'greek': 'greek letters', 'latin': 'extended latin', 'combining': 'combining diacritics', 'arrows': 'arrows etc.', 'rest': 'miscallenous symbols', 'cyrchar': 'cyrillic', 'ding': 'dingbats', 'ElsevierGlyph': 'Elsevier Glyphs', 'mathbb': 'mathbb', 'mathbf': 'mathbf',
               'mathbit': 'mathbit', 'mathfrak': 'mathfrak', 'mathmit': 'mathmit', 'mathscr': 'mathscr', 'mathsfbfsl': 'mathsfbfsl', 'mathsfbf': 'mathsfbf', 'mathsfsl': 'mathsfsl', 'mathsf': 'mathsf',
               'mathslbb': 'mathslbb', 'mathsl': 'mathsl', 'mathtt': 'mathtt'
}


def open_symbol_data(mimedata):
    # strange fuckery required
    ba = mimedata.data("application/x-qabstractitemmodeldatalist")
    ds = QtCore.QDataStream(ba)
    data = {}
    while not ds.atEnd():
        row = ds.readInt32()
        column = ds.readInt32()
        map_items = ds.readInt32()
        for i in range(map_items):
            key = ds.readInt32()
            value = QtCore.QVariant()
            ds >> value
            data[key] = value.value()
    if 55 in data:
        return data[55]


class SymbolPanel(UIPanel):
    """
        Panel for rapid testing of various UI elements that otherwise may be hidden behind complex screens or logic.
    """

    def __init__(self, name, key, default_position='right', parent=None, ui_manager=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        inner = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        self.selector = QtWidgets.QComboBox()
        for item in table_names:
            self.selector.addItem(table_dict[item], item)
        self.selector.activated.connect(self.change_symbol_set)
        self.selector.setFocusPolicy(QtCore.Qt.TabFocus)

        layout.addWidget(self.selector)
        self.symlist = QtWidgets.QListWidget()
        self.symlist.setFixedWidth(200)
        self.symlist.setSpacing(8)
        self.symlist.setMouseTracking(True)
        self.symlist.setFocusPolicy(QtCore.Qt.NoFocus)
        self.symlist.setViewMode(QtWidgets.QListWidget.IconMode)
        self.symlist.setFont(qt_prefs.fonts[g.BIG_FONT])
        self.symlist.itemEntered.connect(self.item_entered)
        self.symlist.itemClicked.connect(self.item_clicked)
        layout.addWidget(self.symlist)
        self.info = QtWidgets.QLabel('')
        layout.addWidget(self.info)
        inner.setLayout(layout)
        self.tables = {}
        keys = list(latex_to_unicode.keys())
        for name in table_names:
            self.tables[name] = []
        keys.sort()
        for key in keys:
            char, description, table_key = latex_to_unicode[key]
            self.tables[table_key].append(key)
        self.prepare_symbols('greek')
        self.setWidget(inner)
        self.finish_init()

    def prepare_symbols(self, key):
        self.symlist.clear()
        for key in self.tables[key]:
            char, description, table = latex_to_unicode[key]
            command = '\\'+ key
            item = QtWidgets.QListWidgetItem(char)
            item.setToolTip(command)
            item.setData(55, {'char': char, 'description': description, 'command': command})
            self.symlist.addItem(item)

    def item_entered(self, item):
        self.info.setText(item.data(55)['description'])
        self.info.update()

    def item_clicked(self, item):
        """ Clicked on a symbol: launch activity that tries to insert it to focused text field
        :param item:
        :return:
        """
        print("Item clicked")
        focus = ctrl.get_focus_object() or ctrl.main.graph_view.focusWidget()
        if focus and isinstance(focus, QtWidgets.QLineEdit):
            focus.insert(item.data(55)['char'])
            focus.setFocus()



    def change_symbol_set(self):
        key = self.selector.currentData()
        self.prepare_symbols(key)
