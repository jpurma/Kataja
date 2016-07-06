from PyQt5 import QtWidgets, QtGui, QtCore
from kataja.ui_support.ColorSelector import ColorSelector

import kataja.globals as g
from kataja.singletons import qt_prefs
from kataja.ui_support.ExpandingLineEdit import ExpandingLineEdit
from kataja.ui_widgets.UIEmbed import UIEmbed
from kataja.ui_widgets.embeds.NodeEditEmbed import make_label

__author__ = 'purma'


class GroupLabelEmbed(UIEmbed):
    def __init__(self, parent, edge):
        UIEmbed.__init__(self, parent, edge, 'Highlight a group of nodes')
        self.marker = None
        ui = self.ui_manager
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.top_row_layout)  # close-button from UIEmbed
        smaller_font = qt_prefs.get_font(g.ITALIC_FONT)
        big_font = QtGui.QFont(smaller_font)
        big_font.setPointSize(big_font.pointSize() * 2)
        self.input_line_edit = ExpandingLineEdit(self,
                                                 big_font=big_font,
                                                 smaller_font=smaller_font,
                                                 prefill='label')
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.input_line_edit)
        label = make_label('Name for the group (optional)',
                           parent=self,
                           layout=hlayout,
                           tooltip='Group of nodes can be singled out and named, e.g. as phases',
                           buddy=self.input_line_edit)
        layout.addLayout(hlayout)
        hlayout = QtWidgets.QHBoxLayout()
        self.color_select = ColorSelector(self)
        ui.connect_element_to_action(self.color_select, 'change_group_color')
        hlayout.addWidget(self.color_select, 1, QtCore.Qt.AlignRight)
        label = make_label('Color',
                           parent=self,
                           layout=hlayout,
                           tooltip='Select color for highlight',
                           buddy=self.color_select,
                           align=QtCore.Qt.AlignLeft)
        self.fill_checkbox = QtWidgets.QCheckBox()
        ui.connect_element_to_action(self.fill_checkbox, 'change_group_fill')
        hlayout.addWidget(self.fill_checkbox, 1, QtCore.Qt.AlignRight)
        label = make_label('Fill',
                           parent=self,
                           layout=hlayout,
                           tooltip="Group area is marked with translucent color",
                           buddy=self.fill_checkbox,
                           align=QtCore.Qt.AlignLeft)
        self.outline_checkbox = QtWidgets.QCheckBox()
        ui.connect_element_to_action(self.outline_checkbox, 'change_group_outline')
        hlayout.addWidget(self.outline_checkbox, 1, QtCore.Qt.AlignRight)
        label = make_label('Outline',
                           parent=self,
                           layout=hlayout,
                           tooltip="Group is marked by line drawn around it",
                           buddy=self.outline_checkbox,
                           align=QtCore.Qt.AlignLeft)

        self.include_children_checkbox = QtWidgets.QCheckBox()
        ui.connect_element_to_action(self.include_children_checkbox, 'change_group_children')
        hlayout.addWidget(self.include_children_checkbox, 1, QtCore.Qt.AlignRight)
        label = make_label('Include children',
                           parent=self,
                           layout=hlayout,
                           tooltip="Automatically add child nodes to group's scope",
                           buddy=self.include_children_checkbox,
                           align=QtCore.Qt.AlignLeft)
        self.allow_overlap_checkbox = QtWidgets.QCheckBox()
        ui.connect_element_to_action(self.allow_overlap_checkbox, 'change_group_overlaps')
        hlayout.addWidget(self.allow_overlap_checkbox, 1, QtCore.Qt.AlignRight)
        label = make_label('Allow groups to overlap',
                           parent=self,
                           layout=hlayout,
                           tooltip="Can group include members of other group. If not, lower group "
                                   "has priority",
                           buddy=self.allow_overlap_checkbox,
                           align=QtCore.Qt.AlignLeft)

        layout.addLayout(hlayout)
        hlayout = QtWidgets.QHBoxLayout()
        self.delete_button = QtWidgets.QPushButton("Delete")  # U+21A9 &#8617;
        self.delete_button.setMaximumWidth(60)
        ui.connect_element_to_action(self.delete_button, 'delete_group')

        hlayout.addWidget(self.delete_button)
        self.enter_button = QtWidgets.QPushButton("Keep ↩")  # U+21A9 &#8617;
        self.enter_button.setMaximumWidth(60)
        ui.connect_element_to_action(self.enter_button, 'save_group_changes')

        hlayout.addWidget(self.enter_button)
        layout.addLayout(hlayout)
        self.setLayout(layout)
        #self.assumed_width = 200
        #self.assumed_height = 37
        self.update_position()
        self.setEnabled(True)

    def update_fields(self):
        """

        :return:
        """
        a = self.host
        self.allow_overlap_checkbox.setChecked(a.allow_overlap)
        self.include_children_checkbox.setChecked(a.include_children)
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
        super().update_embed(focus_point=focus_point)

    def update_position(self, focus_point=None):
        super().update_position(focus_point=focus_point)

