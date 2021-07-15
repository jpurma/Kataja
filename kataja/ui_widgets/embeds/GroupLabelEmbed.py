from PyQt6 import QtGui, QtCore

import kataja.globals as g
from kataja.singletons import qt_prefs, ctrl
from kataja.ui_support.panel_utils import box_row
from kataja.ui_widgets.ExpandingLineEdit import ExpandingLineEdit
from kataja.ui_widgets.KatajaCheckBox import KatajaCheckBox
from kataja.ui_widgets.PushButtonBase import PushButtonBase
from kataja.ui_widgets.UIEmbed import UIEmbed
from kataja.ui_widgets.selection_boxes.ColorSelector import ColorSelector

__author__ = 'purma'


class GroupLabelEmbed(UIEmbed):
    def __init__(self, parent, group):
        UIEmbed.__init__(self, parent, group, 'Highlight a group of nodes')
        layout = self.vlayout
        self.marker = None
        smaller_font = qt_prefs.get_font(g.ITALIC_FONT)
        big_font = QtGui.QFont(smaller_font)
        big_font.setPointSize(big_font.pointSize() * 2)
        hlayout = box_row(layout)
        tt = 'Group of nodes can be singled out and named, e.g. as phases'
        self.input_line_edit = ExpandingLineEdit(self, big_font=big_font,
                                                 smaller_font=smaller_font,
                                                 prefill='label', tooltip=tt
                                                 ).to_layout(hlayout,
                                                             with_label=
                                                             'Name for the group (optional)')
        hlayout = box_row(layout)
        self.color_select = ColorSelector(parent=self, host=group, action='change_group_color',
                                          tooltip='Select color for highlight'
                                          ).to_layout(hlayout, with_label='Color')
        self.fill_checkbox = KatajaCheckBox(self, host=group, action='change_group_fill',
                                            tooltip="Group area is marked with translucent color"
                                            ).to_layout(hlayout, with_label='Fill')
        self.outline_checkbox = KatajaCheckBox(self, host=group, action='change_group_outline',
                                               tooltip="Group is marked by line drawn around it"
                                               ).to_layout(hlayout, with_label='Outline')
        hlayout = box_row(layout)
        self.delete_button = PushButtonBase(self, host=group, text="Delete",
                                            action='delete_group').to_layout(hlayout)
        self.delete_button.setMaximumWidth(60)
        hlayout.addStretch(0)
        self.enter_button = PushButtonBase(self, host=group, text="Keep ↩",
                                           action='save_group_changes').to_layout(hlayout)
        # U+21A9 &#8617;
        self.enter_button.setMaximumWidth(60)
        # self.assumed_width = 200
        # self.assumed_height = 37
        self.setMinimumSize(QtCore.QSize(365, 120))
        self.updateGeometry()
        self.update_position()
        self.setEnabled(True)

    def update_fields(self):
        a = self.host
        self.input_line_edit.setText(a.get_label_text())
        self.outline_checkbox.setChecked(a.outline)
        self.fill_checkbox.setChecked(a.fill)
        s = self.color_select
        s.model().selected_color = a.color_key
        s.select_by_data(a.color_key)
        s.update()
        super().update_fields()

    def focus_to_main(self):
        self.input_line_edit.setFocus()

    def update_embed(self, focus_point=None):
        if self.host:
            p = QtGui.QPalette()
            p.setColor(QtGui.QPalette.Text, self.host.color)
            self.input_line_edit.setPalette(p)
        super().update_embed()

    def update_position(self, focus_point=None):
        focus_point = self.host.position_for_buttons()
        if self.moved_by_hand:
            return
        self.update_size()
        point_in_view = ctrl.graph_view.mapFromScene(focus_point)
        self.move(point_in_view.x() - (self.width() / 2), point_in_view.y() + 24)
        self.updateGeometry()
