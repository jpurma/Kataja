from PyQt5 import QtWidgets, QtGui, QtCore

import kataja.globals as g
from kataja.parser.INodes import ITextNode, as_html, as_editable_html
from kataja.parser.LatexToINode import LatexFieldToINode
from kataja.singletons import qt_prefs, ctrl
from kataja.ui_support.EmbeddedLineEdit import EmbeddedLineEdit
from kataja.ui_support.EmbeddedMultibutton import EmbeddedMultibutton
from kataja.ui_support.ProjectionButtons import ProjectionButtons
from kataja.ui_support.EmbeddedRadiobutton import EmbeddedRadiobutton
from kataja.ui_support.EmbeddedTextarea import EmbeddedTextarea
from kataja.ui_support.ExpandingTextArea import ExpandingTextArea, PreviewLabel
from kataja.ui_widgets.UIEmbed import UIEmbed
from kataja.ui_widgets.ResizeHandle import ResizeHandle
from ui_widgets.OverlayButton import PanelButton


def make_label(text, parent=None, layout=None, tooltip='', buddy=None, palette=None, align=None):
    label = QtWidgets.QLabel(text, parent=parent)
    if palette:
        label.setPalette(palette)
    if buddy:
        label.setBuddy(buddy)
    label.setStatusTip(tooltip)
    if ctrl.main.use_tooltips:
        label.setToolTip(tooltip)
    if align:
        layout.addWidget(label, 1, align)
    else:
        layout.addWidget(label)
    return label


class EyeButton(PanelButton):
    """ This is a special kind of button where checked -state shows eye icon and not checked is
    an empty rectangle. Hovering over button shows eye, darker.

    """

    def __init__(self, key, tt):
        self.checked_icon = None
        self.hover_icon = None
        PanelButton.__init__(self, qt_prefs.eye_icon, size=24, tooltip=tt)
        self._hover = False
        self.setCheckable(True)

    def compose_icon(self):
        """ Redraw the image to be used as a basis for icon, this is necessary
        to update the overlay color.
        :return:
        """
        c = ctrl.cm.get(self.color_key)
        image = QtGui.QImage(self.base_image)
        painter = QtGui.QPainter(image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
        painter.fillRect(image.rect(), c)
        painter.end()
        image2 = QtGui.QImage(self.base_image)
        painter = QtGui.QPainter(image2)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
        painter.fillRect(image2.rect(), c.darker())
        painter.end()
        pm1 = QtGui.QPixmap().fromImage(image)
        pm2 = QtGui.QPixmap().fromImage(image2)
        empty = QtGui.QPixmap(24, 24)
        empty.fill(ctrl.cm.paper())
        self.normal_icon = QtGui.QIcon(empty)
        self.checked_icon = QtGui.QIcon(pm1)
        self.hover_icon = QtGui.QIcon(pm2)
        if self.isChecked():
            self.setIcon(self.checked_icon)
        else:
            self.setIcon(self.normal_icon)

    def checkStateSet(self):
        super().checkStateSet()
        self.update_icon_mode()

    def nextCheckState(self):
        super().nextCheckState()
        self.update_icon_mode()

    def update_icon_mode(self):
        down = self.isChecked()
        if self._hover and not down:
            self.setIcon(self.hover_icon)
        elif down:
            self.setIcon(self.checked_icon)
        else:
            self.setIcon(self.normal_icon)

    def enterEvent(self, e):
        self._hover = True
        self.update_icon_mode()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._hover = False
        self.update_icon_mode()
        super().leaveEvent(e)


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
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.top_row_layout)
        layout.addSpacing(4)
        ui_p = self._palette
        self.setPalette(ui_p)
        ui_s = QtGui.QPalette(ui_p)
        ui_s.setColor(QtGui.QPalette.Text, ctrl.cm.secondary())
        smaller_font = qt_prefs.get_font(g.MAIN_FONT)
        big_font = QtGui.QFont(smaller_font)
        big_font.setPointSize(big_font.pointSize() * 2)
        self.view_buttons = QtWidgets.QButtonGroup(self)
        self.view_buttons.setExclusive(True)

        self.synframebutton = EyeButton('synlabels', 'All nodes show their syntactic labels')
        self.synframebutton.setChecked(True)
        self.ui_manager.connect_element_to_action(self.synframebutton, 'set_synlabels_visible')
        self.view_buttons.addButton(self.synframebutton)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.synframebutton)
        vlayout = QtWidgets.QVBoxLayout()
        hlayout.addLayout(vlayout)
        tt = 'Label used in syntactic computations, plain string. Visible in <i>syntactic mode</i> ' \
             'or if <i>Displayed label</i> is empty.'
        title = 'Syntactic label'
        self.synlabel = EmbeddedLineEdit(self, tip=tt, font=big_font, prefill='label',
                                         on_edit=self.synlabel_edited,
                                         on_finish=self.synlabel_finished,
                                         on_return=self.synlabel_finished)
        make_label(title, self, vlayout, tt, self.synlabel, ui_s)
        self.synlabel.setPalette(ui_p)
        vlayout.addWidget(self.synlabel)
        layout.addLayout(hlayout)

        self.nodeframebutton = EyeButton('nodelabels', 'All nodes show their user-given labels')
        self.view_buttons.addButton(self.nodeframebutton)
        self.ui_manager.connect_element_to_action(self.nodeframebutton, 'set_node_labels_visible')
        tt = "Freeform label or text for node, has no effect for syntactic computation"
        title = 'User label'
        self.label = ExpandingTextArea(self, tip=tt, font=smaller_font, prefill='label',
                                       on_edit=self.label_edited, label=title,
                                       on_focus_out=self.label_finished)
        self.label.setPalette(ui_p)
        self.resize_target = self.label
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.nodeframebutton)
        hlayout.addWidget(self.label)
        layout.addLayout(hlayout)

        self.autoframebutton = EyeButton('autolabels', 'All nodes show their autogenerated x-bar '
                                                       'labels')
        self.ui_manager.connect_element_to_action(self.autoframebutton, 'set_autolabels_visible')
        self.view_buttons.addButton(self.autoframebutton)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.autoframebutton)
        vlayout = QtWidgets.QVBoxLayout()
        hlayout.addLayout(vlayout)
        tt = "These are either XBar or Bare phrase structure labels that are updated " \
             "automatically based on projections."
        title = 'Generated label'
        self.autolabel = EmbeddedLineEdit(self, tip=tt, font=big_font, prefill='autolabel')
        self.autolabel.setReadOnly(True)
        make_label(title, self, vlayout, tt, self.autolabel)
        vlayout.addWidget(self.autolabel)

        vlayout = QtWidgets.QVBoxLayout()
        tt = 'Optional index for announcing link between multiple instances.'
        title = 'Index'
        self.index = EmbeddedLineEdit(self, tip=tt, font=big_font, prefill='i',
                                      on_finish=self.index_finished)
        self.index.setPalette(ui_p)
        self.index.setMaximumWidth(20)
        make_label(title, self, vlayout, tt, self.index)
        vlayout.addWidget(self.index)
        hlayout.addLayout(vlayout)
        layout.addLayout(hlayout)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addSpacing(28)
        tt = 'Node can be projection from either or both of its children if those children are ' \
             'heads or projections from their children.'
        title = 'Projects from'
        self.projections = ProjectionButtons(self)
        self.projections.setMaximumWidth(200)

        vlayout = QtWidgets.QVBoxLayout()
        if not self.projections.empty:
            make_label(title, self, vlayout, tt)
        vlayout.addWidget(self.projections)
        hlayout.addLayout(vlayout)
        layout.addLayout(hlayout)
        self.ui_manager.connect_element_to_action(self.projections,
                                                  'set_projection_at_embed_ui',
                                                  connect_slot=self.projections.connect_slot)
        if self.resize_target:
            self.resize_handle = ResizeHandle(self, self.resize_target)
            layout.addWidget(self.resize_handle, 0, QtCore.Qt.AlignRight)
        self.setLayout(layout)
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
        print('update fields called for ConstituentNodeEditEmbed')
        node = self.host
        self.label.setText(node.label)
        print('label: ', repr(node.label))
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
        m = ctrl.settings.get('label_text_mode')
        if m == g.SYN_LABELS or m == g.SYN_LABELS_FOR_LEAVES:
            self.synlabel.setFocus()
        elif m == g.NODE_LABELS_FOR_LEAVES or m == g.NODE_LABELS:
            self.label.setFocus()
        elif m == g.XBAR_LABELS:
            self.autolabel.setFocus()



