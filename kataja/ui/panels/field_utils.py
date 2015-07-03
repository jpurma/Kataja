from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QSize
from kataja.ui.panels.UIPanel import UIPanel
import kataja.globals as g

__author__ = 'purma'


def label(panel, layout, text):
    slabel = QtWidgets.QLabel(text, panel)
    layout.addWidget(slabel)
    return slabel


def spinbox(ui_manager, panel, layout, label, range_min, range_max, action):
    slabel = QtWidgets.QLabel(label, panel)
    slabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
    spinbox = QtWidgets.QSpinBox()
    spinbox.setRange(range_min, range_max)
    ui_manager.connect_element_to_action(spinbox, action)
    slabel.setBuddy(spinbox)
    layout.addWidget(slabel)
    layout.addWidget(spinbox)
    return spinbox


def decimal_spinbox(ui_manager, panel, layout, label, range_min, range_max, step, action):
    slabel = QtWidgets.QLabel(label, panel)
    spinbox = QtWidgets.QDoubleSpinBox()
    spinbox.setRange(range_min, range_max)
    spinbox.setSingleStep(step)
    ui_manager.connect_element_to_action(spinbox, action)
    slabel.setBuddy(spinbox)
    layout.addWidget(slabel)
    layout.addWidget(spinbox)
    return spinbox


def mini_button(ui_manager, layout, text, action):
    button = QtWidgets.QPushButton(text)
    button.setMinimumSize(QSize(40, 20))
    button.setMaximumSize(QSize(40, 20))
    ui_manager.connect_element_to_action(button, action)
    layout.addWidget(button)
    return button


def mini_selector(ui_manager, panel, layout, data, action):
    selector = QtWidgets.QComboBox(panel)
    selector.addItems(['pt', '%'])
    i = 0
    selector.addItems([text for text, value in data])
    for text, value in data:
        selector.setItemData(i, value)
        i += 1
    selector.setItemData(1, 'relative')
    selector.setMinimumSize(QSize(40, 20))
    selector.setMaximumSize(QSize(40, 20))
    ui_manager.connect_element_to_action(selector, action)
    layout.addWidget(selector)
    return selector


def checkbox(ui_manager, panel, layout, label, action):
    slabel = QtWidgets.QLabel(label, panel)
    scheckbox = QtWidgets.QCheckBox()
    ui_manager.connect_element_to_action(scheckbox, action)

    slabel.setBuddy(scheckbox)
    layout.addWidget(slabel)
    layout.addWidget(scheckbox)
    return scheckbox


def box_row(container):
    hlayout = QtWidgets.QHBoxLayout()
    hlayout.setContentsMargins(0, 0, 0, 0)
    if isinstance(container, QtWidgets.QLayout):
        container.addLayout(hlayout)
    elif container:
        container.setLayout(hlayout)
    return hlayout

def set_value(field, value, conflict=False):
    field.blockSignals(True)
    if isinstance(field, QtWidgets.QSpinBox):
        field.setValue(value)
    elif isinstance(field, QtWidgets.QComboBox):
        field.setCurrentIndex(value)
    if conflict:
        add_and_select_ambiguous_marker(field)
    else:
        remove_ambiguous_marker(field)
    field.blockSignals(False)

def add_and_select_ambiguous_marker(element):
    if isinstance(element, QtWidgets.QComboBox):
        i = UIPanel.find_list_item(g.AMBIGUOUS_VALUES, element)
        if i == -1:
            element.insertItem(0, '---', g.AMBIGUOUS_VALUES)
            element.setCurrentIndex(0)
        else:
            element.setCurrentIndex(i)
    elif isinstance(element, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
        element.setSuffix(' (?)')

def remove_ambiguous_marker(element):
    if isinstance(element, QtWidgets.QComboBox):
        i = UIPanel.find_list_item(g.AMBIGUOUS_VALUES, element)
        if i > -1:
            element.removeItem(i)
    elif isinstance(element, (QtWidgets.QSpinBox, QtWidgets.QDoubleSpinBox)):
        element.setSuffix('')
