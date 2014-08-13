import math
from PyQt5 import QtWidgets, QtGui
from kataja.singletons import prefs, ctrl
from kataja.ui.UIPanel import UIPanel, FLAG, CIRCLE
from kataja.utils import to_tuple

__author__ = 'purma'


class ColorPanel(UIPanel):
    """

    """

    def __init__(self, name, default_position='right', parent=None, ui_buttons=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_buttons: pass a dictionary where buttons from this panel will be added
        """
        UIPanel.__init__(self, name, default_position, parent, folded)
        # ### Color wheel
        layout = QtWidgets.QVBoxLayout()
        widget = QtWidgets.QWidget(self)
        # color_wheel_layout.setContentsMargins(4, 4, 4, 4)

        label_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        button_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.MinimumExpanding)
        selector = QtWidgets.QComboBox(self)
        ui_buttons['color_mode'] = selector

        selector.addItems([c['name'] for c in prefs.color_modes.values()])
        selector.activated.connect(self.change_color_mode)
        self.mode_select = selector
        layout.addWidget(selector)
        layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        widget.setLayout(layout)

        self.setWidget(widget)
        self.finish_init()



    def change_color_mode(self, mode):
        """

        :param mode:
        """
        mode_key = list(prefs.color_modes.keys())[mode]
        print('changing color mode to:', mode, mode_key)
        ctrl.main.change_color_mode(mode_key)

    def create_theme_from_color(self, hsv):
        cm = ctrl.cm
        color_key = str(hsv)
        if color_key not in prefs.color_modes:
            prefs.add_color_mode(color_key, hsv, cm)
            color_item = prefs.color_modes[color_key]
            self.mode_select.addItem(color_item['name'])
            self.mode_select.setCurrentIndex(self.mode_select.count() - 1)
        return color_key


    def update_colors(self):
        """


        """
        self._updating = False

