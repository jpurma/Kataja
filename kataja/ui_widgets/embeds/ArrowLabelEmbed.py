from PyQt6 import QtGui

import kataja.globals as g
from kataja.singletons import qt_prefs
from kataja.ui_support.panel_utils import box_row
from kataja.ui_widgets.KatajaLineEdit import KatajaLineEdit
from kataja.ui_widgets.PushButtonBase import PushButtonBase
from kataja.ui_widgets.UIEmbed import UIEmbed

__author__ = 'purma'


class ArrowLabelEmbed(UIEmbed):
    def __init__(self, parent, edge):
        """ ArrowLabelEmbed is for editing arrow labels, but it takes Arrow as its host,
        because there may be problems if the host item is not subclass of Saved. Use self.label
        to get access to edge.label_item.
        """
        UIEmbed.__init__(self, parent, edge, 'Edit edge text')
        self.marker = None
        self.label = edge.label_item
        layout = self.vlayout
        tt = 'Label for arrow'
        f = QtGui.QFont(qt_prefs.get_font(g.MAIN_FONT))
        f.setPointSize(f.pointSize() * 2)
        hlayout = box_row(layout)
        self.input_line_edit = KatajaLineEdit(self, tooltip=tt, font=f, prefill='label'
                                              ).to_layout(hlayout)
        # U+21A9 &#8617;
        self.enter_button = PushButtonBase(self, text="↩",
                                           action='edit_edge_label_enter_text'
                                           ).to_layout(hlayout)
        self.assumed_width = 200
        self.assumed_height = 37
        self.update_position()

    def focus_to_main(self):
        self.input_line_edit.setFocus()

    def update_embed(self, focus_point=None):
        if self.host:
            p = QtGui.QPalette()
            p.setColor(QtGui.QPalette.Text, self.host.color)
            self.label = self.host.label_item
            self.input_line_edit.setPalette(p)
            f = QtGui.QFont(self.label.get_font())
            f.setPointSize(f.pointSize() * 2)
            # self.input_line_edit.setFont(f)
        super().update_embed()

    def update_fields(self):
        self.input_line_edit.setText(self.label.label_text)
        super().update_fields()

    def update_position(self, focus_point=None):
        super().update_position(focus_point=self.label.scenePos())
