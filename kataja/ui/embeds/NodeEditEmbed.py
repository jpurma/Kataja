
__author__ = 'purma'

from PyQt5 import QtWidgets, QtGui, QtCore

from kataja.parser.LatexToINode import parse_field
from kataja.ui.embeds.UIEmbed import UIEmbed
from kataja.ui.panels.field_utils import EmbeddedTextarea, EmbeddedLineEdit, \
    EmbeddedMultibutton
from kataja.singletons import qt_prefs, ctrl
from kataja.parser import INodeToLatex
import kataja.globals as g


def make_label(text, parent=None, layout=None, tooltip='', buddy=None, palette=None):
    label = QtWidgets.QLabel(text, parent=parent)
    label.setPalette(palette)
    label.setFont(qt_prefs.font(g.UI_FONT))
    label.setBuddy(buddy)
    label.setStatusTip(tooltip)
    label.setToolTip(tooltip)
    layout.addWidget(label)
    return label


class NodeEditEmbed(UIEmbed):
    """ Node edit embed creates editable fields based on templates provided by Node subclass.
    It allows easy UI generation for user-customized syntactic elements or Kataja Nodes.

    :param parent:
    :param ui_manager:
    :param node:
    :param scene_pos:
    """

    def __init__(self, parent, ui_manager, ui_key, node):
        UIEmbed.__init__(self, parent, ui_manager, ui_key, node)
        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)
        layout.addLayout(self.top_row_layout)
        layout.addSpacing(4)
        ui_p = self._palette
        ui_s = QtGui.QPalette(ui_p)
        ui_s.setColor(QtGui.QPalette.Text, ctrl.cm.secondary())

        f = QtGui.QFont(qt_prefs.font(g.MAIN_FONT))
        f.setPointSize(f.pointSize() * 2)

        ed = node.get_editing_template()
        field_order = ed['field_order']
        self.fields = {}
        hlayout = None

        # Generate edit fields based on data, expand this as necessary
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
                func = getattr(self.host, check_before, None) or getattr(
                    self.host.syntactic_object, check_before, None)
                if func:
                    if not func():
                    # func is something like 'can_be_projection(self)'
                        continue
            if itype == 'text':
                width = d.get('width', 140)
                field = EmbeddedLineEdit(self, tip=tt, font=f, prefill=prefill)
                field.setMaximumWidth(width)
                if syntactic:
                    field.setPalette(ui_s)
            elif itype == 'textarea':
                width = d.get('width', 200)
                field = EmbeddedTextarea(self, tip=tt, font=f, prefill=prefill)
                field.setMaximumWidth(width)
                if syntactic:
                    field.setPalette(ui_s)
            elif itype == 'multibutton':
                width = d.get('width', 200)
                op_func = d.get('option_function')
                op_func = getattr(self.host, op_func, None) or \
                    getattr(self.syntactic_object, op_func, None)
                field = EmbeddedMultibutton(self, tip=tt, options=op_func())
                field.setMaximumWidth(width)
                action = d.get('select_action')
                if action:
                    ui_manager.connect_element_to_action(field, action)

                if syntactic:
                    field.setPalette(ui_s)
                #else:
                #    field.setPalette(ui_p)
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

        self.enter_button = QtWidgets.QPushButton("↩")  # U+21A9 &#8617;
        self.enter_button.setMaximumWidth(20)
        self.enter_button.setParent(self)
        ui_manager.connect_element_to_action(self.enter_button, 'finish_editing_node')
        layout.addWidget(self.enter_button)
        self.updateGeometry()
        self.update_embed()

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
            if itype == 'text':
                parsed = INodeToLatex.parse_inode_for_field(value)
                field.setText(parsed)
            if itype == 'textarea':
                parsed = INodeToLatex.parse_inode_for_field(value)
                field.setPlainText(parsed)
            if itype == 'multibutton':
                op_func = d.get('option_function')
                op_func = getattr(self.host, op_func, None) or \
                    getattr(self.syntactic_object, op_func, None)
                field.update_selections(op_func())

    def psizeHint(self):
        base = QtWidgets.QWidget.sizeHint(self)
        return base + QtCore.QSize(40, 0)

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
            if itype == 'text':
                value = parse_field(field.text())
            elif itype == 'textarea':
                value = parse_field(field.toPlainText())
            elif itype == 'multibutton':
                print('Implement submit_values for multibutton in '
                      'NodeEditEmbed')
                print(field.bgroup)
                value = ''
            else:
                raise NotImplementedError
            if 'setter' in d:
                getattr(self.host, d['setter'])(value)
            else:
                setattr(self.host, field_name, value)
        self.host.update_label()

    def mouseMoveEvent(self, event):
        self.move(self.mapToParent(event.pos()) - self._drag_diff)

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

    def close(self):
        UIEmbed.close(self)
