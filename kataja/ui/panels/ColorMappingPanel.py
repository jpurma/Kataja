from PyQt5 import QtWidgets

from kataja.singletons import prefs, ctrl
from kataja.ui.panels.ColorWheelPanel import ColorWheelInner
from kataja.ui.panels import UIPanel


__author__ = 'purma'


class ColorMappingPanel(UIPanel):
    """

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
        inner = QtWidgets.QWidget(self)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)

        label_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        button_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        self.preferred_size = (200, 220)
        selector = QtWidgets.QComboBox(self)
        ui_buttons['color_mode'] = selector

        selector.addItems([c['name'] for c in prefs.color_modes.values()])
        selector.activated.connect(self.change_color_mode)
        self.mode_select = selector
        # selector.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        layout.addWidget(selector)
        hlayout = QtWidgets.QHBoxLayout()
        color_name = QtWidgets.QLabel(ctrl.cm.get_color_name(ctrl.cm.hsv), self)
        color_name.setFixedWidth(120)
        color_name.setSizePolicy(label_policy)
        self.color_name = color_name
        hlayout.addWidget(color_name)
        add_color_button = QtWidgets.QPushButton('+', self)
        add_color_button.setFixedWidth(20)
        add_color_button.setSizePolicy(label_policy)
        add_color_button.clicked.connect(self.remember_color)
        hlayout.addWidget(add_color_button)
        layout.addLayout(hlayout)

        color_wheel = ColorWheelInner(inner)
        color_wheel.setFixedSize(160, 148)
        layout.addWidget(color_wheel)
        # layout.setRowMinimumHeight(0, color_wheel.height())
        h_spinner = QtWidgets.QSpinBox(self)
        h_spinner.setRange(0, 255)
        h_spinner.valueChanged.connect(self.h_changed)
        h_spinner.setAccelerated(True)
        h_spinner.setWrapping(True)
        self.h_spinner = h_spinner
        h_label = QtWidgets.QLabel('&H:', self)
        h_label.setBuddy(h_spinner)
        h_label.setSizePolicy(label_policy)
        s_spinner = QtWidgets.QSpinBox(self)
        s_spinner.setRange(0, 255)
        s_spinner.valueChanged.connect(self.s_changed)
        s_label = QtWidgets.QLabel('&S:', self)
        s_label.setBuddy(s_spinner)
        s_label.setSizePolicy(label_policy)
        s_spinner.setAccelerated(True)
        self.s_spinner = s_spinner
        v_spinner = QtWidgets.QSpinBox(self)
        v_spinner.setRange(0, 255)
        v_spinner.valueChanged.connect(self.v_changed)
        v_label = QtWidgets.QLabel('&V:', self)
        v_label.setBuddy(v_spinner)
        v_label.setSizePolicy(label_policy)
        v_spinner.setAccelerated(True)
        self.v_spinner = v_spinner
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(h_label)
        hlayout.addWidget(h_spinner)
        hlayout.addWidget(s_label)
        hlayout.addWidget(s_spinner)
        hlayout.addWidget(v_label)
        hlayout.addWidget(v_spinner)
        layout.addLayout(hlayout)
        inner.setLayout(layout)
        self.setWidget(inner)
        self.show()