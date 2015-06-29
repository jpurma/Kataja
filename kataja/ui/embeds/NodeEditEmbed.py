
__author__ = 'purma'

from PyQt5 import QtWidgets, QtGui, QtCore

from kataja.parser.LatexToINode import parse_field
from kataja.ui.embeds.UIEmbed import UIEmbed, EmbeddedLineEdit
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

        ui_p = QtGui.QPalette()
        ui_p.setColor(QtGui.QPalette.Text, ctrl.cm.ui())

        ui_s = QtGui.QPalette()
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
            field = None
            if itype == 'text':
                width = d.get('width', 140)
                field = EmbeddedLineEdit(self, tip=tt, font=f, prefill=prefill)
                field.setMaximumWidth(width)
                if syntactic:
                    field.setPalette(ui_s)
            if field:
                align = d.get('align', 'newline')
                if align == 'newline':
                    if hlayout:
                        layout.addLayout(hlayout)
                    hlayout = QtWidgets.QHBoxLayout()
                hlayout.addWidget(field)
                self.fields[field_name] = field
                ui_name = d.get('name', field_name)
                if syntactic:
                    palette = ui_s
                else:
                    palette = ui_p
                label = make_label(ui_name, self, hlayout, tt, field, palette)
                hlayout.addWidget(label)
        if hlayout:
            layout.addLayout(hlayout)

        self.enter_button = QtWidgets.QPushButton("↩")  # U+21A9 &#8617;
        self.enter_button.setMaximumWidth(20)
        self.enter_button.setParent(self)
        ui_manager.connect_element_to_action(self.enter_button, 'finish_editing_node')
        layout.addWidget(self.enter_button)
        self.update_fields()
        self.update_position()

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

    def sizeHint(self):
        base = QtWidgets.QWidget.sizeHint(self)
        return base + QtCore.QSize(40, 0)

    def after_close(self):
        """ Try to remove this embed after closing
        :return:
        """
        self.ui_manager.remove_edit_embed(self)

    def update_position(self):
        sx, sy, sz = self.host.current_position
        self.update_embed(scenePos = QtCore.QPointF(sx, sy))

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
            else:
                raise NotImplementedError
            if 'setter' in d:
                getattr(self.host, d['setter'])(value)
            else:
                setattr(self.host, field_name, value)
        self.host.update_label()

    def update_embed(self, scenePos=None):
        """ Update position and field values for embed.
        :param scenePos:
        """
        if self.host:
            self.update_fields()
            scene_pos = self.host.pos()
            UIEmbed.update_embed(self, scenePos=scene_pos)

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
        self.fields[ed['field_order'][0]].setFocus()

    def close(self):
        UIEmbed.close(self)
