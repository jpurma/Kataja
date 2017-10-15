from PyQt5 import QtWidgets, QtCore

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_support.panel_utils import box_row
from kataja.ui_widgets.KatajaLabel import KatajaInfoLabel
from kataja.ui_widgets.buttons.EyeButton import EyeButton
from kataja.ui_widgets.buttons.PanelButton import PanelButton
from kataja.ui_widgets.panels.NodePanel import NodePanel
from kataja.ui_widgets.selection_boxes.ShapeSelector import ShapeSelector

__author__ = 'purma'


class FeaturePanel(NodePanel):
    """ Panel for editing how feature nodes and edges are drawn. """

    def __init__(self, name, default_position='right', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the
        construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """

        NodePanel.__init__(self, name, g.FEATURE_NODE, default_position, parent, folded,
                           foldable=True)
        widget = self.widget()
        layout = widget.layout()

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
                                            ).to_layout(hlayout, align=QtCore.Qt.AlignRight)
        self.edge_visible = EyeButton(action='toggle_feature_edge_visibility', height=22,
                                      width=24).to_layout(hlayout, align=QtCore.Qt.AlignRight)
        self.edge_options = PanelButton(parent=self,
                                        pixmap=qt_prefs.settings_icon,
                                        action='open_line_options',
                                        ).to_layout(hlayout, align=QtCore.Qt.AlignRight)
        self.edge_options.data = g.FEATURE_NODE
        self.finish_init()

