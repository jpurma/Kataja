from PyQt5 import QtWidgets

from kataja.UIItem import UIWidget


class KatajaSpinbox(QtWidgets.QSpinBox, UIWidget):
    continuous_action_slot = 'valueChanged'
    action_slot = 'editingFinished'

    def __init__(self, parent=None, range_min=0, range_max=0, suffix='', wrapping=False, **kwargs):
        QtWidgets.QSpinBox.__init__(self, parent=parent)
        UIWidget.__init__(self, **kwargs)
        self.setAccelerated(True)
        self.setReadOnly(False)
        self.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
        self.setRange(range_min, range_max)
        self.setSuffix(suffix)
        self.setWrapping(wrapping)
        self.setFixedWidth(50)
        # slabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def set_value(self, value):
        self.blockSignals(True)
        if self._cached_value != value:
            self.setValue(value)
            self._cached_value = value
        self.blockSignals(False)

    def set_displayed_value(self, value):
        self.set_value(value)


class KatajaDecimalSpinbox(QtWidgets.QDoubleSpinBox, UIWidget):
    continuous_action_slot = 'valueChanged'
    action_slot = 'editingFinished'

    def __init__(self, parent=None, range_min=0, range_max=0, step=1.0, suffix='', wrapping=False,
                 **kwargs):
        QtWidgets.QDoubleSpinBox.__init__(self, parent=parent)
        UIWidget.__init__(self, **kwargs)
        self.setAccelerated(True)
        self.setReadOnly(False)
        self.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
        self.setRange(range_min, range_max)
        self.setSingleStep(step)
        self.setSuffix(suffix)
        self.setWrapping(wrapping)
        self.setFixedWidth(58)
        # slabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def set_value(self, value):
        self.blockSignals(True)
        if self._cached_value != value:
            self.setValue(value)
            self._cached_value = value
        self.blockSignals(False)

    def set_displayed_value(self, value):
        self.set_value(value)
