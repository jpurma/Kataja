from PyQt5 import QtWidgets

from kataja.visualizations.available import VISUALIZATIONS
from kataja.ui.panels.UIPanel import UIPanel


__author__ = 'purma'


class VisualizationPanel(UIPanel):
    """ Switch visualizations and their adjust their settings """

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
        layout = QtWidgets.QGridLayout()

        selector = QtWidgets.QComboBox(self)
        ui_manager.ui_buttons['visualization_selector'] = selector
        selector.addItems(['%s (%s)' % (key, item.shortcut) for key, item in VISUALIZATIONS.items()])
        ui_manager.connect_selector_to_action(selector, 'change_visualization')
        selector.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToContents)
        layout.addWidget(selector, 1, 0)
        layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        inner.setLayout(layout)
        self.setWidget(inner)
        self.widget().setAutoFillBackground(True)
        self.finish_init()

    def update_field(self, field_key, field, value):
        """

        :param field_key:
        :param field:
        :param value:
        """
        if field_key == 'visualization_selector':
            index = list(VISUALIZATIONS.keys()).index(value)
            field.setCurrentIndex(index)

