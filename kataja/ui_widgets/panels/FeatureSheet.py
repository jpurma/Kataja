from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs, prefs, classes
from kataja.ui_support.panel_utils import box_row, icon_button, shape_selector, selector, \
    mini_button
from kataja.ui_widgets.OverlayButton import PanelButton
from kataja.ui_widgets.Panel import Panel
from kataja.ui_support.DraggableNodeFrame import DraggableNodeFrame

__author__ = 'purma'


class FeatureSheet(QtWidgets.QWidget):
    """ Sheet for additional controls for this node type.

    Widgets inside sheet should update themselves through their KatajaActions. They are so deep
    inside other widgets that I wouldn't like to have traversing updates from surface into them,
     or hardcode direct updates to them. """

    def __init__(self, parent=None):
        """
        All of the panel constructors follow the same format so that the
        construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        QtWidgets.QWidget.__init__(self, parent=parent)
        ui = ctrl.ui
        self.setMaximumWidth(220)
        self.setBackgroundRole(QtGui.QPalette.AlternateBase)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(4, 0, 4, 8)
        self.setLayout(layout)

        hlayout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel('Checking')
        hlayout.addWidget(label)
        w = 32
        b1 = PanelButton(pixmap=qt_prefs.features_apart_icon, parent=self, size=24)
        b1.setFixedWidth(w)
        ctrl.ui.connect_element_to_action(b1, 'set_features_apart')
        hlayout.addWidget(b1)
        b2 = PanelButton(pixmap=qt_prefs.features_locked_icon, parent=self, size=24)
        b2.setFixedWidth(w)
        ctrl.ui.connect_element_to_action(b2, 'set_features_locked')
        hlayout.addWidget(b2)
        b3 = PanelButton(pixmap=qt_prefs.features_connected_icon, parent=self, size=24)
        b3.setFixedWidth(w)
        ctrl.ui.connect_element_to_action(b3, 'set_features_connected')
        hlayout.addWidget(b3)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel('Arrangement')
        hlayout.addWidget(label)
        w = 32
        b1 = PanelButton(pixmap=qt_prefs.feature_row_icon, parent=self, size=24)
        b1.setFixedWidth(w)
        ctrl.ui.connect_element_to_action(b1, 'set_features_as_row')
        hlayout.addWidget(b1)
        b2 = PanelButton(pixmap=qt_prefs.feature_column_icon, parent=self, size=24)
        b2.setFixedWidth(w)
        ctrl.ui.connect_element_to_action(b2, 'set_features_as_column')
        hlayout.addWidget(b2)
        b3 = PanelButton(pixmap=qt_prefs.feature_2_columns_icon, parent=self, size=24)
        b3.setFixedWidth(w)
        ctrl.ui.connect_element_to_action(b3, 'set_features_as_2_columns')
        hlayout.addWidget(b3)
        b4 = PanelButton(pixmap=qt_prefs.feature_hanging_icon, parent=self, size=24)
        b4.setFixedWidth(w)
        ctrl.ui.connect_element_to_action(b4, 'set_features_hanging')
        hlayout.addWidget(b4)
        layout.addLayout(hlayout)


        hlayout = box_row(layout)
        label = QtWidgets.QLabel('Edge', parent=self)
        hlayout.addWidget(label)
        hlayout.addStretch(24)
        self.shape_selector = shape_selector(ui, self, hlayout,
                                             action='change_edge_shape',
                                             label='')
        self.edge_options = icon_button(ui, self, hlayout,
                                        icon=qt_prefs.settings_icon,
                                        text='More edge options',
                                        action='open_line_options',
                                        align=QtCore.Qt.AlignRight)
        self.edge_options.data = g.FEATURE_NODE

