from PyQt5 import QtCore

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs, prefs, classes
from kataja.ui_support.panel_utils import box_row
from kataja.ui_widgets.KatajaLabel import KatajaInfoLabel
from kataja.ui_widgets.SelectionBox import SelectionBox
from kataja.ui_widgets.buttons.EyeButton import EyeButton
from kataja.ui_widgets.buttons.PanelButton import PanelButton
from kataja.ui_widgets.panels.NodePanel import NodePanel
from kataja.ui_widgets.selection_boxes.ShapeSelector import ShapeSelector

__author__ = 'purma'


def banned_label_text_modes():
    if ctrl.doc_settings.get('syntactic_mode'):
        return [g.NODE_LABELS, g.NODE_LABELS_FOR_LEAVES]
    else:
        return []


class ConstituentPanel(NodePanel):
    """ Panel for editing how constituent nodes and edges are drawn. """

    def __init__(self, name, default_position='right', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the
        construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """

        NodePanel.__init__(self, name, g.CONSTITUENT_NODE, default_position, parent, folded)
        layout = self.vlayout
        widget = self.widget()

        hlayout = box_row(layout)
        hlayout.setSpacing(0)
        shape_buttons = [(qt_prefs.shape_icon_plain, 'set_no_frame_cn_shape'),
                         (qt_prefs.shape_icon_scope, 'set_scopebox_cn_shape'),
                         (qt_prefs.shape_icon_brackets, 'set_bracketed_cn_shape'),
                         (qt_prefs.shape_icon_box, 'set_box_cn_shape'),
                         (qt_prefs.shape_icon_card, 'set_card_cn_shape'),
                         (qt_prefs.features_locked_icon, 'set_feature_cn_shape')]
        for pixmap, action in shape_buttons:
            PanelButton(pixmap=pixmap, parent=widget, size=24, action=action).to_layout(hlayout)

        hlayout = box_row(layout)
        label = KatajaInfoLabel('Edge', tooltip=ctrl.ui.get_action('change_edge_shape').k_tooltip,
                                parent=widget)
        hlayout.addWidget(label)
        hlayout.addStretch(24)
        self.shape_selector = ShapeSelector(parent=widget,
                                            action='change_edge_shape_for_constituents',
                                            for_edge_type=g.CONSTITUENT_EDGE
                                            ).to_layout(hlayout, align=QtCore.Qt.AlignRight)
        self.edge_visible = EyeButton(action='toggle_constituent_edge_visibility',
                                      height=22,
                                      width=24
                                      ).to_layout(hlayout, align=QtCore.Qt.AlignRight)
        self.edge_options = PanelButton(parent=widget,
                                        pixmap=qt_prefs.settings_icon,
                                        action='open_line_options'
                                        ).to_layout(hlayout, align=QtCore.Qt.AlignRight)
        self.edge_options.data = g.CONSTITUENT_NODE

        hlayout = box_row(layout)
        data = prefs.get_display_choices('label_text_mode')
        data = [(choice, text) for (choice, text) in data]

        self.label_selector = SelectionBox(parent=widget, action='set_visible_label',
                                           data=data).to_layout(hlayout, with_label='Visible label')
        self.label_selector.setMaximumWidth(160)
        hlayout = box_row(layout)
        data = prefs.get_display_choices('linearization_mode')
        self.linearization_mode = SelectionBox(parent=widget, action='select_linearization_mode',
                                               data=data).to_layout(hlayout,
                                                                    with_label='Linearization')
        self.linearization_mode.setMaximumWidth(160)

        hlayout = box_row(layout)
        data = prefs.get_display_choices('trace_strategy')
        self.trace_selector = SelectionBox(parent=widget, action='select_trace_strategy',
                                           data=data).to_layout(hlayout,
                                                                with_label='Trace strategy')
        self.trace_selector.setMaximumWidth(160)

        self.finish_init()

    def syntactic_mode_changed(self):
        allowed = classes.ConstituentNode.allowed_label_text_modes()
        data = prefs.get_display_choices('label_text_mode')
        data = [(choice, text) for (choice, text) in data if choice
                in allowed]
        self.label_selector.rebuild_choices(data)

    def forest_changed(self):
        allowed = classes.ConstituentNode.allowed_label_text_modes()
        data = prefs.get_display_choices('label_text_mode')
        data = [(choice, text) for (choice, text) in data if choice
                in allowed]
        self.label_selector.rebuild_choices(data)
