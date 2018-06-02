from PyQt5 import QtWidgets, QtGui, QtCore

import kataja.globals as g
from kataja.parser.INodes import as_html
from kataja.singletons import qt_prefs, ctrl
from kataja.ui_support.ExpandingTextArea import ExpandingTextArea, PreviewLabel
from kataja.ui_widgets.KatajaTextarea import KatajaTextarea
from kataja.ui_widgets.ResizeHandle import ResizeHandle
from kataja.ui_widgets.UIEmbed import UIEmbed
from kataja.ui_widgets.buttons.ProjectionButtons import ProjectionButtons
from kataja.ui_widgets.KatajaLineEdit import KatajaLineEdit
from kataja.ui_widgets.PushButtonBase import PushButtonBase
from kataja.ui_support.panel_utils import box_row


def make_label(text, parent=None, layout=None, tooltip='', buddy=None, palette=None, align=None):
    label = QtWidgets.QLabel(text, parent=parent)
    if palette:
        label.setPalette(palette)
    label.setBuddy(buddy)
    label.k_tooltip = tooltip
    if align:
        layout.addWidget(label, 1, align)
    else:
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
    can_fade = False  # fade and textareas don't work well together

    def __init__(self, parent, node):
        nname = node.display_name[0].lower()
        UIEmbed.__init__(self, parent, node, 'Edit ' + nname)
        self.setMinimumWidth(220)
        ui_p = self._palette
        ui_s = QtGui.QPalette(ui_p)
        ui_s.setColor(QtGui.QPalette.Text, ctrl.cm.secondary())
        smaller_font = qt_prefs.get_font(g.MAIN_FONT)
        big_font = QtGui.QFont(smaller_font)
        big_font.setPointSize(big_font.pointSize() * 2)
        ed = node.get_editing_template()
        sortable = [(item.get('order', 100), key) for key, item in ed.items()]
        sortable.sort()
        field_names = [key for order, key in sortable]
        self.fields = {}
        self.resize_target = None
        hlayout = None

        # Generate edit elements based on data, expand this as necessary
        for field_name in field_names:
            d = ed.get(field_name, {})
            # if d.get('hidden', False) or not self.host.check_conditions(d):
            #    continue
            tt = d.get('tooltip', '')
            itype = d.get('input_type', 'text')
            prefill = d.get('prefill', '')
            syntactic = d.get('syntactic', False)
            on_edit = d.get('on_edit', None)
            if on_edit and isinstance(on_edit, str):
                on_edit = getattr(node, on_edit, None)
            field_first = False
            if itype == 'text':
                width = d.get('width', 140)
                field = KatajaLineEdit(self, tooltip=tt, font=big_font, prefill=prefill,
                                       on_edit=on_edit)
                field.setMaximumWidth(width)
            elif itype == 'textarea':
                self._disable_effect = True
                template_width = d.get('width', 0)
                field = KatajaTextarea(self, tooltip=tt, font=smaller_font, prefill=prefill,
                                       on_edit=on_edit)
                max_w = 200
                if node.user_size:
                    w = node.user_size[0]
                elif template_width:
                    w = template_width
                else:
                    w = node.label_object.document().idealWidth()
                field.setFixedWidth(min(w, max_w))
                self.resize_target = field
            elif itype == 'expandingtext':
                field = ExpandingTextArea(self, tip=tt, font=smaller_font, prefill=prefill,
                                          on_edit=on_edit)
                template_width = d.get('width', 0)
                if template_width:
                    field.setFixedWidth(template_width)
                self.resize_target = field
            elif itype == 'projection_buttons':
                width = d.get('width', 200)
                field = ProjectionButtons(self)
                field.setMaximumWidth(width)
            elif itype == 'checkbox':
                field = QtWidgets.QCheckBox(self)
            elif itype == 'preview':
                field = PreviewLabel(self, tip=tt, font=smaller_font)
            elif itype == 'spinbox':
                field = QtWidgets.QSpinBox(self)
                field.setMinimum(d.get('min', -1))
                field.setMaximum(d.get('max', 4))
            else:
                raise NotImplementedError

            if field:
                action = d.get('select_action')
                if action:
                    self.ui_manager.connect_element_to_action(field, action)
                if syntactic:
                    field.setPalette(ui_s)
                else:
                    field.setPalette(ui_p)

            align = d.get('align', 'newline')
            if align == 'newline':
                # new hlayout means new line, but before starting a new hlayout,
                # end the previous one.
                hlayout = box_row(self.vlayout)
            self.fields[field_name] = field
            if field_first:
                hlayout.addWidget(field)
            ui_name = d.get('name', field_name)
            if ui_name:
                if syntactic:
                    palette = ui_s
                else:
                    palette = ui_p
                make_label(ui_name, self, hlayout, tt, field, palette)
            if not field_first:
                hlayout.addWidget(field)
        hlayout = box_row(self.vlayout)
        hlayout.addStretch(0)
        # U+21A9 &#8617;
        self.enter_button = PushButtonBase(parent=self, text="Keep ↩",
                                           action='finish_editing_node')
        hlayout.addWidget(self.enter_button, 0, QtCore.Qt.AlignRight)
        if self.resize_target:
            self.resize_handle = ResizeHandle(self, self.resize_target)
            hlayout.addWidget(self.resize_handle, 0, QtCore.Qt.AlignRight)
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
            d = ed.get(field_name, {})
            if 'getter' in d:
                value = getattr(self.host, d['getter'])()
            else:
                value = getattr(self.host, field_name, '')
            if 'enabler' in d:
                enabled = getattr(self.host, d['enabler'])()
                field.setEnabled(bool(enabled))
            itype = d.get('input_type', 'text')
            if itype == 'expandingtext':
                value = as_html(value)
                field.setText(value)
            elif itype == 'text' or itype == 'textarea':
                value = as_html(value)
                field.set_original(value)
                field.setText(value)
            elif itype == 'checkbox':
                field.setChecked(bool(value))
            elif itype == 'spinbox':
                if not isinstance(value, int):
                    if not value:
                        value = 0
                    else:
                        try:
                            value = int(value)
                        except TypeError:
                            value = int(d.get('prefill', 0))
                field.setValue(value)

    def submit_values(self):
        """ Submit field values back to object based on template
        :return:
        """
        ed = self.host.get_editing_template()
        for field_name, field in self.fields.items():
            d = ed.get(field_name, {})
            itype = d.get('input_type', 'text')
            if itype == 'text' or itype == 'textarea':
                value = field.text()
            elif itype == 'expandingtext':
                value = field.inode_text()
            elif itype in ['radiobutton', 'checkbox', 'preview', 'spinbox']:
                # buttons take action immediately when clicked and preview cannot be edited
                continue
            else:
                raise NotImplementedError
            if 'setter' in d:
                getattr(self.host, d['setter'])(value)
            else:
                setattr(self.host, field_name, value)
        self.host.update_label()

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
        # default to field that gets edited in quickedit
        if self.fields:
            print(self.fields)
            self.fields[self.host.compose_html_for_editing()[0]].setFocus()
