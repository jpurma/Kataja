from PyQt5 import QtWidgets

from kataja.UIItem import UIWidget


class KatajaSpinbox(QtWidgets.QSpinBox, UIWidget):

    def __init__(self, parent=None, range_min=0, range_max=0, suffix='', wrapping=False, **kwargs):
        QtWidgets.QSpinBox.__init__(self, parent=parent)
        UIWidget.__init__(self, **kwargs)
        spinbox = QtWidgets.QSpinBox()
        spinbox.setAccelerated(True)
        spinbox.setReadOnly(False)
        spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
        spinbox.setRange(range_min, range_max)
        spinbox.setSuffix(suffix)
        spinbox.setWrapping(wrapping)
        spinbox.setFixedWidth(50)
        #slabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def set_value(self, value):
        self.blockSignals(True)
        if self._cached_value != value:
            self.setValue(value)
            self._cached_value = value
        self.blockSignals(False)


class KatajaDecimalSpinbox(QtWidgets.QSpinBox, UIWidget):

    def __init__(self, parent=None, range_min=0, range_max=0, step=1.0, suffix='', wrapping=False,
                 **kwargs):
        QtWidgets.QSpinBox.__init__(self, parent=parent)
        UIWidget.__init__(self, **kwargs)
        spinbox = QtWidgets.QSpinBox()
        spinbox.setAccelerated(True)
        spinbox.setReadOnly(False)
        spinbox.setButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
        spinbox.setRange(range_min, range_max)
        spinbox.setSingleStep(step)
        spinbox.setSuffix(suffix)
        spinbox.setWrapping(wrapping)
        spinbox.setFixedWidth(58)
        #slabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)

    def set_value(self, value):
        self.blockSignals(True)
        if self._cached_value != value:
            self.setValue(value)
            self._cached_value = value
        self.blockSignals(False)
