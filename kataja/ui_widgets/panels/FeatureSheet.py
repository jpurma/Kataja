from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_support.panel_utils import box_row
from kataja.ui_widgets.buttons.PanelButton import PanelButton
from kataja.ui_widgets.selection_boxes.ShapeSelector import ShapeSelector
from kataja.ui_widgets.KatajaLabel import KatajaInfoLabel

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
        label = KatajaInfoLabel('Checking',
                                tooltip='How the checking relation is displayed',
                                parent=self)
        hlayout.addWidget(label)
        w = 32
        b1 = PanelButton(pixmap=qt_prefs.features_apart_icon, parent=self, size=24,
                         action='set_features_apart').to_layout(hlayout)
        b1.setFixedWidth(w)
        b2 = PanelButton(pixmap=qt_prefs.features_locked_icon, parent=self, size=24,
                         action='set_features_locked').to_layout(hlayout)
        b2.setFixedWidth(w)
        b3 = PanelButton(pixmap=qt_prefs.features_connected_icon, parent=self, size=24,
                         action='set_features_connected').to_layout(hlayout)
        b3.setFixedWidth(w)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        label = KatajaInfoLabel('Arrangement',
                                tooltip='How features are arranged around the constituent',
                                parent=self)
        hlayout.addWidget(label)
        w = 32
        b1 = PanelButton(pixmap=qt_prefs.feature_row_icon, parent=self, size=24,
                         action='set_features_as_row').to_layout(hlayout)
        b1.setFixedWidth(w)
        b2 = PanelButton(pixmap=qt_prefs.feature_column_icon, parent=self, size=24,
                         action='set_features_as_column').to_layout(hlayout)
        b2.setFixedWidth(w)
        b3 = PanelButton(pixmap=qt_prefs.feature_2_columns_icon, parent=self, size=24,
                         action='set_features_as_2_columns').to_layout(hlayout)
        b3.setFixedWidth(w)
        b4 = PanelButton(pixmap=qt_prefs.feature_hanging_icon, parent=self, size=24,
                         action='set_features_hanging').to_layout(hlayout)
        b4.setFixedWidth(w)
        layout.addLayout(hlayout)

        hlayout = box_row(layout)
        label = KatajaInfoLabel('Edge',
                                tooltip=ctrl.ui.get_action('change_edge_shape').k_tooltip,
                                parent=self)
        hlayout.addWidget(label)
        hlayout.addStretch(24)
        self.shape_selector = ShapeSelector(parent=self,
                                            action='change_edge_shape_for_features',
                                            for_edge_type=g.FEATURE_EDGE
                                            ).to_layout(hlayout)
        self.edge_options = PanelButton(parent=self,
                                        pixmap=qt_prefs.settings_icon,
                                        action='open_line_options',
                                        ).to_layout(hlayout, align=QtCore.Qt.AlignRight)
        self.edge_options.data = g.FEATURE_NODE

