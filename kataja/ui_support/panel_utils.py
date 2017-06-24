from PyQt5 import QtWidgets, QtCore
from kataja.ui_widgets.SelectionBox import SelectionBox
from kataja.ui_widgets.selection_boxes.TableModelSelectionBox import TableModelSelectionBox

__author__ = 'purma'


class KnobDial(QtWidgets.QWidget):

    def __init__(self, ui_manager, parent, layout, label='', suffix='', action=''):
        QtWidgets.QWidget.__init__(self, parent)
        hlayout = QtWidgets.QHBoxLayout()
        self.label = QtWidgets.QLabel(label, self)
        hlayout.addWidget(self.label)
        self.dial = QtWidgets.QDial(self)
        self.dial.setFixedSize(28, 28)
        self.dial.setWrapping(True)
        self.dial.setRange(-180, 180)
        hlayout.addWidget(self.dial)
        self.spinbox = QtWidgets.QSpinBox(self)
        self.spinbox.setAccelerated(True)
        self.spinbox.setReadOnly(False)
        self.spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
        self.spinbox.setRange(0, 360)
        self.spinbox.setSuffix(suffix)
        self.spinbox.setWrapping(True)
        self.spinbox.setFixedWidth(50)
        self.label.setBuddy(self.spinbox)
        hlayout.addWidget(self.spinbox)
        self.setLayout(hlayout)
        ui_manager.connect_element_to_action(self, action)
        layout.addWidget(self)


def find_panel(parent):
    if hasattr(parent, 'pin_to_dock'):
        return parent
    else:
        return find_panel(parent.parent())


def label(panel, layout, text='', x=-1, y=-1):
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


def spinbox(ui_manager, panel, layout, label='', range_min=0, range_max=0, action='', suffix='',
            wrapping=False):
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
    spinbox.setAccelerated(True)
    spinbox.setReadOnly(False)
    spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
    spinbox.setRange(range_min, range_max)
    spinbox.setSuffix(suffix)
    spinbox.setWrapping(wrapping)
    spinbox.setFixedWidth(50)
    slabel.setBuddy(spinbox)
    spinbox.k_buddy = slabel
    ui_manager.connect_element_to_action(spinbox, action)
    layout.addWidget(slabel)
    layout.addWidget(spinbox)
    return spinbox


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
    slabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
    dial = QtWidgets.QDial()
    dial.setFixedSize(28, 28)
    dial.setWrapping(wrapping)
    dial.setRange(range_min, range_max)
    slabel.setBuddy(dial)
    dial.k_buddy = slabel
    ui_manager.connect_element_to_action(dial, action)
    layout.addWidget(slabel)
    layout.addWidget(dial)
    return spinbox


def decimal_spinbox(ui_manager, panel, layout, label='', range_min=0, range_max=0, step=0,
                    action='', suffix=''):
    """

    :param ui_manager:
    :param panel:
    :param layout:
    :param label:
    :param range_min:
    :param range_max:
    :param step:
    :param action:
    :param suffix:
    :return:
    """
    slabel = QtWidgets.QLabel(label, panel)
    spinbox = QtWidgets.QDoubleSpinBox()
    spinbox.setAccelerated(True)
    spinbox.setReadOnly(False)
    spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
    spinbox.setRange(range_min, range_max)
    spinbox.setSingleStep(step)
    spinbox.setSuffix(suffix)
    spinbox.setFixedWidth(58)
    slabel.setBuddy(spinbox)
    spinbox.k_buddy = slabel
    ui_manager.connect_element_to_action(spinbox, action)
    layout.addWidget(slabel)
    layout.addWidget(spinbox)
    return spinbox


def checkbox(ui_manager, parent, layout, label='', action='', x=-1, y=-1):
    """

    :param ui_manager:
    :param parent:
    :param layout:
    :param label:
    :param action:
    :return:
    """
    slabel = QtWidgets.QLabel(label, parent)
    scheckbox = QtWidgets.QCheckBox()
    if x > -1:
        layout.addWidget(slabel, y, x)
        layout.addWidget(scheckbox, y, x + 1)
    else:
        layout.addWidget(slabel)
        layout.addWidget(scheckbox)
    slabel.setBuddy(scheckbox)
    scheckbox.k_buddy = slabel
    ui_manager.connect_element_to_action(scheckbox, action)
    return scheckbox


def radiobutton(ui_manager, parent, layout, label='', action='', x=-1, y=-1, group=None):
    """

    :param ui_manager:
    :param panel:
    :param layout:
    :param label:
    :param action:
    :return:
    """
    slabel = QtWidgets.QLabel(label, parent)
    sradio = QtWidgets.QRadioButton()
    if x > -1:
        layout.addWidget(slabel, y, x)
        layout.addWidget(sradio, y, x + 1)
    else:
        layout.addWidget(slabel)
        layout.addWidget(sradio)
    if group:
        group.addButton(sradio)
    slabel.setBuddy(sradio)
    sradio.k_buddy = slabel
    ui_manager.connect_element_to_action(sradio, action)
    return sradio


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
        if isinstance(field, QtWidgets.QSpinBox):
            field.setValue(value)
        elif isinstance(field, TableModelSelectionBox):
            field.select_by_data(value)
        elif isinstance(field, SelectionBox):
            field.setCurrentIndex(value)
        elif isinstance(field, QtWidgets.QCheckBox):
            field.setChecked(value)
        elif isinstance(field, QtWidgets.QAbstractButton):
            field.setChecked(value)
        field.cached_value = value
    field.blockSignals(False)




