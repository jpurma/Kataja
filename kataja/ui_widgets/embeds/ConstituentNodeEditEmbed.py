from PyQt5 import QtWidgets, QtGui, QtCore

import kataja.globals as g
from kataja.parser.INodes import as_editable_html
from kataja.singletons import qt_prefs, ctrl
from kataja.ui_support.ExpandingTextArea import ExpandingTextArea
from kataja.ui_widgets.KatajaButtonGroup import KatajaButtonGroup
from kataja.ui_widgets.KatajaLineEdit import KatajaLineEdit
from kataja.ui_widgets.ResizeHandle import ResizeHandle
from kataja.ui_widgets.UIEmbed import UIEmbed
from kataja.ui_widgets.buttons.EyeButton import EyeButton
from kataja.ui_widgets.buttons.ProjectionButtons import ProjectionButtons


def make_label(text, parent=None, layout=None, tooltip='', buddy=None, palette=None, align=None):
    label = QtWidgets.QLabel(text, parent=parent)
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

    :param parent: QWidget where this editor lives, QGraphicsView of some sort
    :param ui_manager: UIManager instance that manages this editor
    :param ui_key: unique, but predictable key for accessing this editor
    :param node: node that is to be associated with this editor
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

        tt = "Freeform label or text for node, has no effect for syntactic computation"
        title = 'User label'
        self.label = ExpandingTextArea(self, tooltip=tt, font=smaller_font, prefill='label',
                                       on_edit=self.label_edited, label=title,
                                       on_focus_out=self.label_finished)
        self.label.setPalette(ui_p)
        layout.addWidget(self.label)

        tt = "These are either XBar or Bare phrase structure labels that are updated " \
             "automatically based on projections."
        title = 'Generated label'
        self.autolabel = KatajaLineEdit(self, tooltip=tt, font=big_font, prefill='autolabel'
                                        ).to_layout(layout, with_label=title, label_first=True)
        self.autolabel.setReadOnly(True)

        tt = 'Optional index for announcing link between multiple instances.'
        title = 'Index'
        self.index = KatajaLineEdit(self, tooltip=tt, font=big_font, prefill='i',
                                    on_finish=self.index_finished
                                    ).to_layout(layout, with_label=title, label_first=True)
        self.index.setPalette(ui_p)
        self.index.setMaximumWidth(20)

        tt = 'Node can be projection from either or both of its children if those children are ' \
             'heads or projections from their children.'
        title = 'Projects from'
        self.projections = ProjectionButtons(self)
        self.projections.setMaximumWidth(200)
        layout.addWidget(self.projections)

        if not self.projections.empty:
            make_label(title, parent=self, layout=layout, tooltip=tt)
        self.ui_manager.connect_element_to_action(self.projections,
                                                  'set_projecting_node')
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
        self.label.setText(node.label)
        self.synlabel.setText(node.get_syntactic_label())
        self.autolabel.setText(as_editable_html(node.autolabel))
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
        #print('synlabel edited')
        #print(args, kwargs)
        pass

    def synlabel_finished(self):
        text = self.synlabel.text()
        self.host.parse_edited_label('syntactic label', text)
        ctrl.forest.forest_edited()
        self.update_fields()

    def label_edited(self, *args, **kwargs):
        pass

    def label_finished(self):
        text = self.label.inode_text()
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
        m = self.host.allowed_label_text_mode()
        if m == g.SYN_LABELS or m == g.SYN_LABELS_FOR_LEAVES:
            self.synlabel.setFocus()
        elif m == g.NODE_LABELS_FOR_LEAVES or m == g.NODE_LABELS:
            self.label.setFocus()
        elif m == g.XBAR_LABELS:
            self.autolabel.setFocus()



