
from PyQt5 import QtWidgets, QtGui, QtCore

from kataja.parser.LatexToINode import parse_field
from kataja.ui.embeds.UIEmbed import UIEmbed
from kataja.ui.elements.EmbeddedTextarea import EmbeddedTextarea
from kataja.ui.elements.ExpandingLineEdit import ExpandingLineEdit
from kataja.ui.elements.EmbeddedLineEdit import EmbeddedLineEdit
from kataja.ui.elements.EmbeddedMultibutton import EmbeddedMultibutton
from kataja.singletons import prefs, qt_prefs, ctrl
from kataja.parser import INodeToLatex
import kataja.globals as g
from kataja.ui.elements.ResizeHandle import ResizeHandle


def make_label(text, parent=None, layout=None, tooltip='', buddy=None, palette=None):
    label = QtWidgets.QLabel(text, parent=parent)
    label.setPalette(palette)
    label.setFont(qt_prefs.font(g.UI_FONT))
    label.setBuddy(buddy)
    label.setStatusTip(tooltip)
    if ctrl.main.use_tooltips:
        label.setToolTip(tooltip)
    layout.addWidget(label)
    return label


class NodeEditEmbed(UIEmbed):
    """ Node edit embed creates editable elements based on templates provided by Node subclass.
    It allows easy UI generation for user-customized syntactic elements or Kataja Nodes.

    :param parent: QWidget where this editor lives, QGraphicsView of some sort
    :param ui_manager: UIManager instance that manages this editor
    :param ui_key: unique, but predictable key for accessing this editor
    :param node: node that is to be associated with this editor
    """

    def __init__(self, parent, ui_manager, ui_key, node):
        nname = prefs.nodes[node.node_type]['name'].lower()
        UIEmbed.__init__(self, parent, ui_manager, ui_key, node, 'Edit ' + nname)
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.top_row_layout)
        layout.addSpacing(4)
        ui_p = self._palette
        ui_s = QtGui.QPalette(ui_p)
        ui_s.setColor(QtGui.QPalette.Text, ctrl.cm.secondary())
        smaller_font = qt_prefs.font(g.MAIN_FONT)
        big_font = QtGui.QFont(smaller_font)
        big_font.setPointSize(big_font.pointSize() * 2)

        ed = node.get_editing_template()
        field_order = ed['field_order']
        self.fields = {}
        self.resize_target = None
        hlayout = None

        # Generate edit elements based on data, expand this as necessary
        for field_name in field_order:
            d = ed[field_name]
            if d.get('hidden', False):
                continue
            tt = d.get('tooltip', '')
            itype = d.get('input_type', 'text')
            prefill = d.get('prefill', '')
            syntactic = d.get('syntactic', False)
            check_before = d.get('check_before', None)
            if check_before:
                func = getattr(self.host, check_before, None) or getattr(self.host.syntactic_object,
                    check_before, None)
                if func:
                    if not func():
                        # func is something like 'can_be_projection(self)'
                        continue
            if itype == 'text':
                width = d.get('width', 140)
                field = EmbeddedLineEdit(self, tip=tt, font=big_font, prefill=prefill)
                field.setMaximumWidth(width)
                if syntactic:
                    field.setPalette(ui_s)
            elif itype == 'textarea':
                self.disable_effect = True
                fm = QtGui.QFontMetrics(smaller_font)
                char_width = fm.maxWidth()
                field = EmbeddedTextarea(self, tip=tt, font=smaller_font, prefill=prefill)
                nc = node.label_object
                if nc.line_length > 0:
                    field.setFixedWidth(nc.line_length * char_width)
                else:
                    # if line_length is not defined, estimate it
                    w = nc.document().idealWidth()
                    line_length = w / nc.char_width
                    field.setFixedWidth(max(200, line_length * char_width))
                self.resize_target = field
                if syntactic:
                    field.setPalette(ui_s)
            elif itype == 'expandingtext':
                field = ExpandingLineEdit(self,
                                          tip=tt,
                                          big_font=big_font,
                                          smaller_font=smaller_font,
                                          prefill=prefill)
                #field.setMaximumWidth(width)
                if syntactic:
                    field.setPalette(ui_s)
            elif itype == 'multibutton':
                width = d.get('width', 200)
                op_func = d.get('option_function')
                op_func = getattr(self.host, op_func, None) or getattr(self.syntactic_object,
                                                                       op_func, None)
                field = EmbeddedMultibutton(self, options=op_func())
                field.setMaximumWidth(width)
                action = d.get('select_action')
                if action:
                    ui_manager.connect_element_to_action(field, action)

                if syntactic:
                    field.setPalette(ui_s)
                else:
                    field.setPalette(ui_p)
            else:
                raise NotImplementedError
            align = d.get('align', 'newline')
            if align == 'newline':
                # new hlayout means new line, but before starting a new hlayout,
                # end the previous one.
                if hlayout:
                    layout.addLayout(hlayout)
                hlayout = QtWidgets.QHBoxLayout()
            hlayout.addWidget(field)
            self.fields[field_name] = field
            ui_name = d.get('name', field_name)
            if ui_name:
                if syntactic:
                    palette = ui_s
                else:
                    palette = ui_p
                make_label(ui_name, self, hlayout, tt, field, palette)
        if hlayout:
            layout.addLayout(hlayout)
        hlayout = QtWidgets.QHBoxLayout()
        self.enter_button = QtWidgets.QPushButton("↩")  # U+21A9 &#8617;
        self.enter_button.setMaximumWidth(20)
        self.enter_button.setParent(self)
        ui_manager.connect_element_to_action(self.enter_button, 'finish_editing_node')
        hlayout.addWidget(self.enter_button)
        if self.resize_target:
            self.resize_handle = ResizeHandle(self, self.resize_target)
            hlayout.addWidget(self.resize_handle, 0, QtCore.Qt.AlignRight)
        layout.addLayout(hlayout)
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
        ed = self.host.get_editing_template()
        for field_name, field in self.fields.items():
            d = ed[field_name]
            if 'getter' in d:
                value = getattr(self.host, d['getter'])()
            else:
                value = getattr(self.host, field_name, '')
            itype = d.get('input_type', 'text')
            if itype in ['text', 'textarea', 'expandingtext']:
                parsed = INodeToLatex.parse_inode_for_field(value)
                field.setText(parsed)
            elif itype == 'multibutton':
                op_func = d.get('option_function')
                op_func = getattr(self.host, op_func, None) or getattr(self.syntactic_object,
                                                                       op_func, None)
                field.update_selections(op_func())

    def after_close(self):
        """ Try to remove this embed after closing
        :return:
        """
        self.ui_manager.remove_edit_embed(self)

    def submit_values(self):
        """ Submit field values back to object based on template
        :return:
        """
        ed = self.host.get_editing_template()
        for field_name, field in self.fields.items():
            d = ed[field_name]
            itype = d.get('input_type', 'text')
            if itype in ['text', 'textarea', 'expandingtext']:
                value = parse_field(field.text())
            elif itype == 'multibutton':
                # buttons take action immediately when clicked
                continue
            else:
                raise NotImplementedError
            if 'setter' in d:
                getattr(self.host, d['setter'])(value)
            else:
                setattr(self.host, field_name, value)
        self.host.update_label()

    def mouseMoveEvent(self, event):
        self.move(self.mapToParent(event.pos()) - self._drag_diff)
        QtWidgets.QWidget.mouseMoveEvent(self, event)

    def focus_to_main(self):
        """ Find the main element to focus in this embed.
        :return:
        """
        # look for explicit focus in template definitions.
        ed = self.host.get_editing_template()
        for key, data in ed.items():
            if 'focus' in data and data['focus']:
                self.fields[key].setFocus()
                return
        # default to first field in field order
        if self.fields:
            self.fields[ed['field_order'][0]].setFocus()
