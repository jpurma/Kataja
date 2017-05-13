from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs, prefs, classes
from kataja.ui_support.panel_utils import box_row, icon_button, shape_selector, selector, \
    mini_button
from kataja.ui_widgets.OverlayButton import PanelButton
from kataja.ui_widgets.Panel import Panel
from kataja.ui_support.DraggableNodeFrame import DraggableNodeFrame

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
        ui = ctrl.ui
        self.setMaximumWidth(220)
        self.setBackgroundRole(QtGui.QPalette.AlternateBase)
        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(4, 0, 4, 8)
        self.setLayout(layout)

        hlayout = box_row(layout)
        label = QtWidgets.QLabel('Shape')
        hlayout.addWidget(label)
        w = 32
        b1 = PanelButton(pixmap=qt_prefs.shape_icon_plain, parent=self, size=24)
        b1.setFixedWidth(w)
        b1.setCheckable(True)
        ctrl.ui.connect_element_to_action(b1, 'set_no_frame_node_shape')
        hlayout.addWidget(b1)
        b2 = PanelButton(pixmap=qt_prefs.shape_icon_scope, parent=self, size=24)
        b2.setFixedWidth(w)
        b2.setCheckable(True)
        ctrl.ui.connect_element_to_action(b2, 'set_scopebox_node_shape')
        hlayout.addWidget(b2)
        b3 = PanelButton(pixmap=qt_prefs.shape_icon_brackets, parent=self, size=24)
        b3.setFixedWidth(w)
        b3.setCheckable(True)
        ctrl.ui.connect_element_to_action(b3, 'set_bracketed_node_shape')
        hlayout.addWidget(b3)
        b4 = PanelButton(pixmap=qt_prefs.shape_icon_box, parent=self, size=24)
        b4.setFixedWidth(w)
        b4.setCheckable(True)
        ctrl.ui.connect_element_to_action(b4, 'set_box_node_shape')
        hlayout.addWidget(b4)
        b5 = PanelButton(pixmap=qt_prefs.shape_icon_card, parent=self, size=24)
        b5.setFixedWidth(w)
        b5.setCheckable(True)
        ctrl.ui.connect_element_to_action(b5, 'set_card_node_shape')
        hlayout.addWidget(b5)
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
        self.edge_options.data = g.CONSTITUENT_NODE

        hlayout = box_row(layout)
        data = prefs.get_display_choices('label_text_mode')
        self.label_selector = selector(ui, self, hlayout,
                                       action='toggle_label_text_mode',
                                       label='Labeling strategy',
                                       data=data)
        hlayout = box_row(layout)
        data = prefs.get_display_choices('projection_style')
        self.projection_selector = selector(ui, self, hlayout,
                                            action='select_projection_style',
                                            label='Projection style',
                                            data=data)

        hlayout = box_row(layout)
        data = prefs.get_display_choices('trace_strategy')
        self.trace_selector = selector(ui, self, hlayout,
                                       action='select_trace_strategy',
                                       label='Trace strategy',
                                       data=data)

