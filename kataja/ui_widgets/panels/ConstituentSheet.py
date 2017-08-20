from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs, prefs
from kataja.ui_support.panel_utils import box_row
from kataja.ui_widgets.SelectionBox import SelectionBox
from kataja.ui_widgets.buttons.PanelButton import PanelButton
from kataja.ui_widgets.selection_boxes.ShapeSelector import ShapeSelector
from kataja.ui_widgets.KatajaLabel import KatajaInfoLabel

__author__ = 'purma'


class ConstituentSheet(QtWidgets.QWidget):
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
        self.setMaximumWidth(220)
        self.setBackgroundRole(QtGui.QPalette.AlternateBase)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(4, 0, 4, 8)
        self.setLayout(layout)

        hlayout = box_row(layout)
        label = KatajaInfoLabel('Shape', tooltip='How constituent nodes are displayed', parent=self)
        hlayout.addWidget(label)
        w = 32
        b1 = PanelButton(pixmap=qt_prefs.shape_icon_plain, parent=self, size=24,
                         action='set_no_frame_node_shape').to_layout(hlayout)
        b1.setFixedWidth(w)
        b2 = PanelButton(pixmap=qt_prefs.shape_icon_scope, parent=self, size=24,
                         action='set_scopebox_node_shape').to_layout(hlayout)
        b2.setFixedWidth(w)
        b3 = PanelButton(pixmap=qt_prefs.shape_icon_brackets, parent=self, size=24,
                         action='set_bracketed_node_shape').to_layout(hlayout)
        b3.setFixedWidth(w)
        b4 = PanelButton(pixmap=qt_prefs.shape_icon_box, parent=self, size=24,
                         action='set_box_node_shape').to_layout(hlayout)
        b4.setFixedWidth(w)
        b5 = PanelButton(pixmap=qt_prefs.shape_icon_card, parent=self, size=24,
                         action='set_card_node_shape').to_layout(hlayout)
        b5.setFixedWidth(w)

        hlayout = box_row(layout)
        label = KatajaInfoLabel('Edge',
                                tooltip=ctrl.ui.get_action('change_edge_shape').k_tooltip,
                                parent=self)
        hlayout.addWidget(label)
        hlayout.addStretch(24)
        self.shape_selector = ShapeSelector(parent=self,
                                            action='change_edge_shape_for_constituents',
                                            for_edge_type=g.CONSTITUENT_EDGE
                                            ).to_layout(hlayout)
        self.edge_options = PanelButton(parent=self,
                                        pixmap=qt_prefs.settings_icon,
                                        action='open_line_options',
                                        ).to_layout(hlayout, align=QtCore.Qt.AlignRight)
        self.edge_options.data = g.CONSTITUENT_NODE

        hlayout = box_row(layout)
        data = prefs.get_display_choices('label_text_mode')
        self.label_selector = SelectionBox(parent=self,
                                           action='set_visible_label',
                                           data=data).to_layout(hlayout,
                                                                with_label='Visible label')
        hlayout = box_row(layout)
        data = prefs.get_display_choices('projection_style')
        self.projection_selector = SelectionBox(parent=self,
                                                action='select_projection_style',
                                                data=data).to_layout(hlayout,
                                                                     with_label='Projection style')


        hlayout = box_row(layout)
        data = prefs.get_display_choices('linearization_mode')
        self.linearization_mode = SelectionBox(parent=self,
                                               action='select_linearization_mode',
                                               data=data).to_layout(hlayout,
                                                                    with_label='Linearization')

        hlayout = box_row(layout)
        data = prefs.get_display_choices('trace_strategy')
        self.trace_selector = SelectionBox(parent=self,
                                           action='select_trace_strategy',
                                           data=data).to_layout(hlayout,
                                                                with_label='Trace strategy')
