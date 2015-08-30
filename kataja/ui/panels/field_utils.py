from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import QSize

from kataja.ui.ColorSwatchIconEngine import ColorSwatchIconEngine
import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs
from kataja.utils import time_me
from kataja.ui.OverlayButton import OverlayButton
from kataja.ui.panels.SymbolPanel import open_symbol_data

__author__ = 'purma'


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


class MyColorDialog(QtWidgets.QColorDialog):
    """

    :param parent:
    :param role:
    :param initial_color:
    """

    def __init__(self, parent, role, initial_color):
        super().__init__(parent)
        self.setOption(QtWidgets.QColorDialog.NoButtons)
        # self.setOption(QtWidgets.QColorDialog.DontUseNativeDialog)
        self.setOption(QtWidgets.QColorDialog.ShowAlphaChannel)
        for i, key in enumerate(ctrl.cm.color_keys):
            self.setStandardColor(i, ctrl.cm.get(key))
        self.setCurrentColor(ctrl.cm.get(initial_color))
        self.currentColorChanged.connect(self.color_adjusted)
        self.role = role
        self.show()

    def color_adjusted(self, color):
        """

        :param color:
        """
        panel = self.parent()
        if panel:
            panel.update_color_for_role(self.role, color)
        ctrl.main.action_finished()


class MyFontDialog(QtWidgets.QFontDialog):
    """

    :param parent:
    :param role:
    :param initial_font:
    """

    def __init__(self, parent, role, initial_font):
        super().__init__(parent)
        self.setOption(QtWidgets.QFontDialog.NoButtons)
        self.setCurrentFont(qt_prefs.font(initial_font))
        self.currentFontChanged.connect(self.font_changed)
        self.role = role
        self.font_key = initial_font
        self.show()

    def font_changed(self, font):
        """

        :param font:
        """
        panel = self.parent()
        font_id = panel.cached_font_id
        font_id = ctrl.ui.create_or_set_font(font_id, font)
        panel.update_font_for_role(self.role, font_id)
        ctrl.main.action_finished()


class LineColorIcon(QtGui.QIcon):
    """

    :param color_id:
    :param model:
    """

    def __init__(self, color_id, model):
        QtGui.QIcon.__init__(self, ColorSwatchIconEngine(color_id, model))


class ColorSelector(TableModelComboBox):
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

    def select_data(self, data):
        """

        :param data:
        :raise hell:
        """
        item = self.find_item(data)
        if item:
            self.setCurrentIndex(item.row())
            self.setModelColumn(item.column())
            self.model().selected_color = data
        else:
            raise hell


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
            item.setToolTip('%s, %spt' % (font.family(), font.pointSize()))
            item.setFont(font)
            item.setSizeHint(QSize(64, 16))
            items.append(item)
        model = self.model()
        model.setRowCount(len(items))
        for r, item in enumerate(items):
            model.setItem(r, 0, item)
        self.view().setModel(model)

    def add_font(self, font_id, font):
        """

        :param font_id:
        :param font:
        """
        item = QtGui.QStandardItem(font_id)
        item.setData(font_id)
        item.setToolTip('%s, %spt' % (font.family(), font.pointSize()))
        item.setFont(font)
        item.setSizeHint(QSize(64, 16))
        self.model().appendRow(item)


def label(panel, layout, text, x=-1, y=-1):
    """

    :param panel:
    :param layout:
    :param text:
    :return:
    """
    slabel = QtWidgets.QLabel(text, panel)
    if x != -1:
        layout.addWidget(slabel, y, x)
    else:
        layout.addWidget(slabel)
    return slabel


def spinbox(ui_manager, panel, layout, label, range_min, range_max, action):
    """

    :param ui_manager:
    :param panel:
    :param layout:
    :param label:
    :param range_min:
    :param range_max:
    :param action:
    :return:
    """
    slabel = QtWidgets.QLabel(label, panel)
    slabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
    spinbox = QtWidgets.QSpinBox()
    spinbox.ambiguous = False
    spinbox.setRange(range_min, range_max)
    ui_manager.connect_element_to_action(spinbox, action)
    slabel.setBuddy(spinbox)
    layout.addWidget(slabel)
    layout.addWidget(spinbox)
    return spinbox


def decimal_spinbox(ui_manager, panel, layout, label, range_min, range_max, step, action):
    """

    :param ui_manager:
    :param panel:
    :param layout:
    :param label:
    :param range_min:
    :param range_max:
    :param step:
    :param action:
    :return:
    """
    slabel = QtWidgets.QLabel(label, panel)
    spinbox = QtWidgets.QDoubleSpinBox()
    spinbox.setRange(range_min, range_max)
    spinbox.setSingleStep(step)
    spinbox.ambiguous = False
    ui_manager.connect_element_to_action(spinbox, action)
    slabel.setBuddy(spinbox)
    layout.addWidget(slabel)
    layout.addWidget(spinbox)
    return spinbox


def text_button(ui_manager, layout, text, action, x=-1, y=-1, checkable=False):
    """

    :param ui_manager:
    :param layout:
    :param text:
    :param action:
    :return:
    """
    button = QtWidgets.QPushButton(text)
    button.setMaximumHeight(20)
    button.ambiguous = False
    button.setCheckable(checkable)
    ui_manager.connect_element_to_action(button, action)
    if x != -1:
        layout.addWidget(button, y, x)
    else:
        layout.addWidget(button)
    return button


def mini_button(ui_manager, layout, text, action, x=-1, y=-1, checkable=False):
    """

    :param ui_manager:
    :param layout:
    :param text:
    :param action:
    :return:
    """
    button = QtWidgets.QPushButton(text)
    button.setMinimumSize(QSize(40, 20))
    button.setMaximumSize(QSize(40, 20))
    button.ambiguous = False
    button.setCheckable(checkable)
    ui_manager.connect_element_to_action(button, action)
    if x != -1:
        layout.addWidget(button, y, x)
    else:
        layout.addWidget(button)
    return button


def icon_text_button(ui_manager, layout, parent, role, key, text, action, size=None, icon=None,
                     draw_method=None):
    """

    :param ui_manager:
    :param layout:
    :param parent:
    :param role:
    :param key:
    :param text:
    :param action:
    :param size:
    :param icon:
    :param draw_method:
    :return:
    """
    button = OverlayButton(icon, None, role, key, text, parent=parent,
                           size=size or QtCore.QSize(48, 24), draw_method=draw_method)
    button.setText(text)
    ui_manager.connect_element_to_action(button, action)
    layout.addWidget(button)
    return button


def font_button(ui_manager, layout, font, action):
    """

    :param ui_manager:
    :param layout:
    :param font:
    :param action:
    :return:
    """
    button = QtWidgets.QPushButton(font.family())
    button.setFont(font)
    button.setMinimumSize(QSize(130, 24))
    button.setMaximumSize(QSize(130, 24))
    button.ambiguous = False
    ui_manager.connect_element_to_action(button, action)
    layout.addWidget(button)
    return button


def mini_selector(ui_manager, panel, layout, data, action):
    """

    :param ui_manager:
    :param panel:
    :param layout:
    :param data:
    :param action:
    :return:
    """
    selector = QtWidgets.QComboBox(panel)
    selector.addItems(['pt', '%'])
    i = 0
    selector.addItems([text for text, value in data])
    for text, value in data:
        selector.setItemData(i, value)
        i += 1
    selector.ambiguous = False
    selector.setItemData(1, 'relative')
    selector.setMinimumSize(QSize(40, 20))
    selector.setMaximumSize(QSize(40, 20))
    ui_manager.connect_element_to_action(selector, action)
    layout.addWidget(selector)
    return selector


def checkbox(ui_manager, panel, layout, label, action, x=-1, y=-1):
    """

    :param ui_manager:
    :param panel:
    :param layout:
    :param label:
    :param action:
    :return:
    """
    slabel = QtWidgets.QLabel(label, panel)
    scheckbox = QtWidgets.QCheckBox()
    ui_manager.connect_element_to_action(scheckbox, action)
    scheckbox.ambiguous = False
    if x > -1:
        layout.addWidget(slabel, y, x)
        layout.addWidget(scheckbox, y, x + 1)
    else:
        layout.addWidget(slabel)
        layout.addWidget(scheckbox)
    slabel.setBuddy(scheckbox)
    return scheckbox


def box_row(container):
    """

    :param container:
    :return:
    """
    hlayout = QtWidgets.QHBoxLayout()
    hlayout.setContentsMargins(0, 0, 0, 0)
    if isinstance(container, QtWidgets.QLayout):
        container.addLayout(hlayout)
    elif container:
        container.setLayout(hlayout)
    return hlayout


def set_value(field, value, conflict=False, enabled=True):
    # print('set_value: %s value: %s conflict: %s enabled: %s ' % (field,
    # value, conflict, enabled))
    """

    :param field:
    :param value:
    :param conflict:
    :param enabled:
    """
    field.blockSignals(True)
    old_v = getattr(field, 'cached_value', None)
    field.setEnabled(enabled)
    if old_v != value and enabled:
        if isinstance(field, QtWidgets.QSpinBox):
            field.setValue(value)
        elif isinstance(field, TableModelComboBox):
            field.select_data(value)
        elif isinstance(field, QtWidgets.QComboBox):
            field.setCurrentIndex(value)
        elif isinstance(field, QtWidgets.QCheckBox):
            field.setChecked(value)
        elif isinstance(field, QtWidgets.QAbstractButton):
            field.setChecked(value)
        if conflict and not field.ambiguous:
            add_and_select_ambiguous_marker(field)
        elif field.ambiguous and not conflict:
            remove_ambiguous_marker(field)
        field.cached_value = value
    field.update()
    field.blockSignals(False)


@time_me
def add_and_select_ambiguous_marker(element):
    """

    :param element:
    """
    if isinstance(element, TableModelComboBox):
        element.add_and_select_ambiguous_marker()
    elif isinstance(element, QtWidgets.QComboBox):
        i = find_list_item(g.AMBIGUOUS_VALUES, element)
        if i == -1:
            element.insertItem(0, '---', g.AMBIGUOUS_VALUES)
            element.setCurrentIndex(0)
        else:
            element.setCurrentIndex(i)
    elif isinstance(element, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
        element.setSuffix(' (?)')
    element.ambiguous = True


@time_me
def remove_ambiguous_marker(element):
    """

    :param element:
    """
    if isinstance(element, TableModelComboBox):
        element.remove_ambiguous_marker()
    elif isinstance(element, QtWidgets.QComboBox):
        i = find_list_item(g.AMBIGUOUS_VALUES, element)
        if i > -1:
            element.removeItem(i)
    elif isinstance(element, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
        element.setSuffix('')
    element.ambiguous = False


def find_list_item(data, selector):
    """ Helper method to check the index of data item in list
    :param data: data to match
    :param selector: QComboBox instance
    :return: -1 if not found, index if found
    """
    if isinstance(selector, TableModelComboBox):
        return selector.find_item(data)
    return selector.findData(data)


def remove_list_item(data, selector):
    """ Helper method to remove items from combo boxes
    :param data: list item's data has to match this
    :param selector: QComboBox instance
    """
    i = find_list_item(data, selector)
    if i != -1:
        selector.removeItem(i)
    return i


class EmbeddedTextarea(QtWidgets.QPlainTextEdit):
    """

    :param parent:
    :param tip:
    :param font:
    :param prefill:
    """

    def __init__(self, parent, tip='', font=None, prefill=''):
        QtWidgets.QPlainTextEdit.__init__(self, parent)
        if tip:
            self.setToolTip(tip)
            self.setStatusTip(tip)
            self.setToolTipDuration(2000)
        if font:
            self.setFont(font)
        if prefill:
            self.setPlaceholderText(prefill)
        self.setAcceptDrops(True)
        # self.setDragEnabled(True)

    def dragEnterEvent(self, event):
        """ Announce support for regular ascii drops and drops of characters
        from symbolpanel.
        :param event: QDragEnterEvent
        :return:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            return QtWidgets.QPlainTextEdit.dragEnterEvent(self, event)

    def dropEvent(self, event):
        """ Support regular ascii drops and drops of characters from
        symbolpanel.
        :param event: QDropEvent
        :return:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            data = open_symbol_data(event.mimeData())
            if data and 'char' in data:
                self.insert(data['char'])
                event.acceptProposedAction()
        else:
            return QtWidgets.QPlainTextEdit.dropEvent(self, event)

    def update_visual(self, **kw):
        """

        :param kw:
        """
        if 'palette' in kw:
            self.setPalette(kw['palette'])
        if 'font' in kw:
            self.setFont(kw['font'])
        if 'text' in kw:
            self.setText(kw['text'])


class EmbeddedLineEdit(QtWidgets.QLineEdit):
    """

    :param parent:
    :param tip:
    :param font:
    :param prefill:
    """

    def __init__(self, parent, tip='', font=None, prefill=''):
        QtWidgets.QLineEdit.__init__(self, parent)
        if tip:
            self.setToolTip(tip)
            self.setStatusTip(tip)
            self.setToolTipDuration(2000)
        if font:
            self.setFont(font)
        if prefill:
            self.setPlaceholderText(prefill)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)

    def dragEnterEvent(self, event):
        """ Announce support for regular ascii drops and drops of characters
        from symbolpanel.
        :param event: QDragEnterEvent
        :return:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            return QtWidgets.QLineEdit.dragEnterEvent(self, event)

    def dropEvent(self, event):
        """ Support regular ascii drops and drops of characters from
        symbolpanel.
        :param event: QDropEvent
        :return:
        """
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            data = open_symbol_data(event.mimeData())
            if data and 'char' in data:
                self.insert(data['char'])
                event.acceptProposedAction()
        else:
            return QtWidgets.QLineEdit.dropEvent(self, event)

    def update_visual(self, **kw):
        """

        :param kw:
        """
        if 'palette' in kw:
            self.setPalette(kw['palette'])
        if 'font' in kw:
            self.setFont(kw['font'])
        if 'text' in kw:
            self.setText(kw['text'])


class EmbeddedMultibutton(QtWidgets.QFrame):
    """

    :param parent:
    :param tip:
    :param options:
    """

    def __init__(self, parent, options=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.setAutoFillBackground(False)
        self.bgroup = QtWidgets.QButtonGroup(self)
        self.bgroup.setExclusive(True)
        self.layout = QtWidgets.QHBoxLayout()
        self.update_selections(options)
        self.setLayout(self.layout)

    def update_selections(self, options):
        """ Redraw all buttons
        :param options: iterable of (text, value, is_checked, disabled,
        tooltip) -dictionaries
        :return:
        """
        new_values = set([od['value'] for od in options])
        old_values = set([button.my_value for button in self.bgroup.buttons()])

        # clear old buttons
        for button in self.bgroup.buttons():
            if button.my_value not in new_values:
                self.bgroup.removeButton(button)
                self.layout.removeWidget(button)
                button.destroy()
            else:  # update old button
                for od in options:
                    if od['value'] == button.my_value:
                        button.setChecked(od['is_checked'])
                        button.setToolTip(od['tooltip'])
                        button.setToolTipDuration(2000)
                        button.setStatusTip(od['tooltip'])

                        button.setEnabled(od['enabled'])
                        break
        # create new buttons
        for od in options:
            v = od['value']
            if v not in old_values:
                button = QtWidgets.QPushButton(od['text'])
                button.setCheckable(True)
                button.my_value = v
                button.setChecked(od['is_checked'])
                button.setToolTip(od['tooltip'])
                button.setStatusTip(od['tooltip'])
                button.setToolTipDuration(2000)
                button.setEnabled(od['enabled'])
                self.bgroup.addButton(button)
                self.layout.addWidget(button)
                s = ":disabled {text-decoration: line-through; color: gray;}"
                button.setStyleSheet(s)
