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
        ui_s.setColor(QtGui.QPalette.Text, ctrl.cm.secondary())
        smaller_font = qt_prefs.get_font(g.MAIN_FONT)
        big_font = QtGui.QFont(smaller_font)
        big_font.setPointSize(big_font.pointSize() * 2)
        tt = 'Label used in syntactic computations, plain string. Visible in <i>syntactic mode</i> ' \
             'or if <i>Displayed label</i> is empty.'
        title = 'Syntactic label'
        self.synlabel = KatajaLineEdit(self, tooltip=tt, font=big_font, prefill='label',
                                       on_edit=self.synlabel_edited,
                                       on_finish=self.synlabel_finished,
                                       on_return=self.synlabel_finished)
        make_label(title, self, layout, tt, self.synlabel, ui_s)
        self.synlabel.setPalette(ui_p)
        layout.addWidget(self.synlabel)

        tt = 'Optional index for announcing link between multiple instances.'
        title = 'Index'
        self.index = KatajaLineEdit(self, tooltip=tt, font=big_font, prefill='i',
                                    on_finish=self.index_finished
                                    ).to_layout(layout, with_label=title, label_first=True)
        self.index.setPalette(ui_p)
        self.index.setMaximumWidth(20)

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
        self.index.setText(node.index or '')

    def triangle_enabled(self):
        node = self.host
        if not node:
            return False
        elif not node.triangle_stack:
            return True
        elif node.triangle_stack[-1] == node:
            return True
        return False

    def synlabel_edited(self, *args, **kwargs):
        # print('synlabel edited')
        # print(args, kwargs)
        pass

    def synlabel_finished(self):
        text = self.synlabel.text()
        self.host.parse_edited_label('node label', text)
        ctrl.forest.forest_edited()
        self.update_fields()

    def index_finished(self):
        text = self.index.text()
        self.host.parse_edited_label('index', text)
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
