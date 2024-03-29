from PyQt6 import QtWidgets, QtCore

from kataja.ui_widgets.SelectionBox import SelectionBox
from kataja.ui_widgets.selection_boxes.TableModelSelectionBox import TableModelSelectionBox

__author__ = 'purma'


class KnobDial(QtWidgets.QWidget):

    def __init__(self, ui_manager, parent, layout, label='', suffix='', action=''):
        # noinspection PyArgumentList
        QtWidgets.QWidget.__init__(self, parent)
        hlayout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel(label, self)
        # noinspection PyArgumentList
        hlayout.addWidget(self.label)
        self.dial = QtWidgets.QDial(self)
        self.dial.setFixedSize(28, 28)
        self.dial.setWrapping(True)
        self.dial.setRange(-180, 180)
        # noinspection PyArgumentList
        hlayout.addWidget(self.dial)
        self.spinbox = QtWidgets.QSpinBox(self)
        self.spinbox.setAccelerated(True)
        self.spinbox.setReadOnly(False)
        self.spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.spinbox.setRange(0, 360)
        self.spinbox.setSuffix(suffix)
        self.spinbox.setWrapping(True)
        self.spinbox.setFixedWidth(50)
        self.label.setBuddy(self.spinbox)
        # noinspection PyArgumentList
        hlayout.addWidget(self.spinbox)
        self.setLayout(hlayout)
        ui_manager.connect_element_to_action(self, action)
        layout.addWidget(self)


def label(panel, layout, text=''):
    slabel = QtWidgets.QLabel(text, panel)
    layout.addWidget(slabel)
    return slabel


def knob(ui_manager, panel, layout, label='', range_min=-180, range_max=180, action='', suffix='',
         wrapping=True):
    """

    :param ui_manager:
    :param panel:
    :param layout:
    :param label:
    :param range_min:
    :param range_max:
    :param action:
    :param suffix:
    :param wrapping:
    :return:
    """
    slabel = QtWidgets.QLabel(label, panel)
    slabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
    dial = QtWidgets.QDial()
    dial.setFixedSize(28, 28)
    dial.setWrapping(wrapping)
    dial.setRange(range_min, range_max)
    slabel.setBuddy(dial)
    dial.k_buddy = slabel
    ui_manager.connect_element_to_action(dial, action)
    layout.addWidget(slabel)
    layout.addWidget(dial)
    return dial


def box_row(container):
    hlayout = QtWidgets.QHBoxLayout()
    hlayout.setContentsMargins(0, 0, 0, 0)
    if isinstance(container, QtWidgets.QLayout):
        container.addLayout(hlayout)
    elif container:
        container.setLayout(hlayout)
    return hlayout


def set_value(field, value):
    """ Utility method to set value for various kinds of fields with their own typical ways for
    setting the value. Also some efficiency savings from caching the previous value for quick
    comparison to decide if the setting is even necessary.
    :param field:
    :param value:
    """
    field.blockSignals(True)
    old_v = getattr(field, 'cached_value', None)
    if old_v != value:
        if isinstance(field, TableModelSelectionBox):
            field.select_by_data(value)
        elif isinstance(field, SelectionBox):
            field.setCurrentIndex(value)
        elif isinstance(field, QtWidgets.QCheckBox):
            field.setChecked(value)
        elif isinstance(field, QtWidgets.QAbstractButton):
            field.setChecked(value)
        field.cached_value = value
    field.blockSignals(False)
