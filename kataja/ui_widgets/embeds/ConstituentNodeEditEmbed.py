from PyQt6 import QtWidgets, QtGui

import kataja.globals as g
from kataja.singletons import qt_prefs, ctrl
from kataja.ui_widgets.KatajaLineEdit import KatajaLineEdit
from kataja.ui_widgets.UIEmbed import UIEmbed


def make_label(text, parent=None, layout=None, tooltip='', buddy=None, palette=None, align=None):
    label = QtWidgets.QLabel(text)
    label.setParent(parent)
    if palette:
        label.setPalette(palette)
    if buddy:
        label.setBuddy(buddy)
    label.k_tooltip = tooltip
    if align:
        layout.addWidget(label, 1, align)
    else:
        layout.addWidget(label)
    return label


class ConstituentNodeEditEmbed(UIEmbed):
    """ Node edit embed creates editable elements based on templates provided by Node subclass.
    It allows easy UI generation for user-customized syntactic elements or Kataja Nodes.
    """
    can_fade = False  # fade and textareas don't work well together

    def __init__(self, parent, node):
        nname = node.display_name[0].lower()
        UIEmbed.__init__(self, parent, node, 'Edit ' + nname)
        layout = self.vlayout
        ui_p = ctrl.cm.get_qt_palette_for_ui()
        self.setPalette(ui_p)
        ui_s = QtGui.QPalette(ui_p)
        ui_s.setColor(QtGui.QPalette.ColorRole.Text, ctrl.cm.secondary())
        ui_g = QtGui.QPalette(ui_p)
        ui_g.setColor(QtGui.QPalette.ColorRole.Text, ctrl.cm.get('accent5'))
        smaller_font = qt_prefs.get_font(g.MAIN_FONT)
        big_font = QtGui.QFont(smaller_font)
        big_font.setPointSize(big_font.pointSize() * 2)
        tt = 'Label used in syntactic computations, plain string. Visible in <i>syntactic mode</i> ' \
             'or if <i>Displayed label</i> is empty.'
        title = 'Syntactic label'
        self.synlabel = KatajaLineEdit(self, tooltip=tt, font=big_font, prefill='label')
        make_label(title, self, layout, tt, self.synlabel, ui_s)
        self.synlabel.setPalette(ui_p)
        layout.addWidget(self.synlabel)
        self.synlabel.setReadOnly(True)

        tt = 'Index to connect several copies of the same node in a tree.'
        title = 'Index'
        self.index = KatajaLineEdit(self, tooltip=tt, font=big_font, prefill='i'
                                    ).to_layout(layout, with_label=title, label_first=True)
        self.index.setReadOnly(True)
        self.index.setPalette(ui_p)
        self.index.setMaximumWidth(20)

        tt = 'Gloss is syntactically inert translation or explanation for the constituent'
        title = 'Gloss'
        self.gloss_label = KatajaLineEdit(self, tooltip=tt, font=big_font, prefill='gloss',
                                          on_finish=self.gloss_finished)
        self.gloss_label.setPalette(ui_g)
        make_label(title, self, layout, tt, self.gloss_label, ui_s)
        layout.addWidget(self.gloss_label)

        self.update_embed()
        self.update_position()
        self.hide()

    def margin_x(self):
        """ Try to keep all of the host node visible, not covered by this editor.
        :return:
        """
        return (self.host.boundingRect().width() / 2) + 12

    def margin_y(self):
        """ Try to keep all of the host node visible, not covered by this editor.
        :return:
        """
        return self.host.boundingRect().height() / 2

    def update_fields(self):
        """ Update field values on embed form based on template """
        node = self.host
        self.synlabel.setText(node.label)
        self.gloss_label.setText(node.gloss)
        self.index.setText(node.index or '')

    def gloss_finished(self):
        text = self.gloss_label.text()
        self.host.set_gloss(text)
        ctrl.forest.forest_edited()
        self.update_fields()

    def submit_values(self):
        """ Possibly called if assuming we are in NodeEditEmbed. All of the changes in
        ConstituentNodeEditEmbed should take effect immediately, so separate submit is not needed.
        :return:
        """
        self.host.update_label()

    def focus_to_main(self):
        """ Find the main element to focus in this embed.
        :return:
        """
        self.synlabel.setFocus()
