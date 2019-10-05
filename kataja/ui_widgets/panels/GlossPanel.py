from PyQt5 import QtCore

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_support.panel_utils import box_row
from kataja.ui_widgets.KatajaLabel import KatajaInfoLabel
from kataja.ui_widgets.buttons.EyeButton import EyeButton
from kataja.ui_widgets.buttons.PanelButton import PanelButton
from kataja.ui_widgets.panels.NodePanel import NodePanel
from kataja.ui_widgets.selection_boxes.ShapeSelector import ShapeSelector

__author__ = 'purma'


class GlossPanel(NodePanel):
    """ Panel for editing how feature nodes and edges are drawn. """

    def __init__(self, name, default_position='right', parent=None, folded=True):
        """
        All of the panel constructors follow the same format so that the
        construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """

        NodePanel.__init__(self, name, g.GLOSS_NODE, default_position, parent, folded)
        hlayout = box_row(self.vlayout)
        widget = self.widget()
        label = KatajaInfoLabel('Edge',
                                tooltip=ctrl.ui.get_action('change_edge_shape').k_tooltip,
                                parent=widget)
        hlayout.addWidget(label)

        hlayout.addStretch(24)
        self.shape_selector = ShapeSelector(parent=widget,
                                            action='change_edge_shape_for_glosses',
                                            for_edge_type=g.GLOSS_EDGE
                                            ).to_layout(hlayout, align=QtCore.Qt.AlignRight)
        self.edge_visible = EyeButton(action='toggle_gloss_edge_visibility', height=22,
                                      width=24).to_layout(hlayout, align=QtCore.Qt.AlignRight)
        self.edge_options = PanelButton(parent=widget,
                                        pixmap=qt_prefs.settings_icon,
                                        action='open_line_options',
                                        ).to_layout(hlayout, align=QtCore.Qt.AlignRight)
        self.edge_options.data = self.node_type
        self.finish_init()
