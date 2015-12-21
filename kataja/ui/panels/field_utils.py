from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QSize

import kataja.globals as g
from kataja.ui.OverlayButton import OverlayButton
from kataja.utils import time_me
from kataja.ui.elements.TableModelComboBox import TableModelComboBox

__author__ = 'purma'


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
    button = OverlayButton(None, key, icon, role, text, parent=parent,
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


