# coding=utf-8
from PyQt5 import QtWidgets, QtGui

from kataja.UIItem import UIWidget
from kataja.singletons import qt_prefs
from ui_widgets.buttons.OverlayButton import OverlayButton


class QuickEditButton(OverlayButton):

    permanent_ui = True

    def __init__(self, size=24, color_key='accent3', **kwargs):
        super().__init__(color_key=color_key, **kwargs)
        if isinstance(size, tuple):
            self.setMinimumSize(size[0]+2, size[1])
            self.setMaximumSize(size[0]+2, size[1])
        else:
            self.setMinimumSize(size+2, size)
            self.setMaximumSize(size+2, size)


class QuickEditButtons(UIWidget, QtWidgets.QFrame):
    unique = True
    permanent_ui = True

    def __init__(self, parent=None, ui=None):
        UIWidget.__init__(self)
        QtWidgets.QFrame.__init__(self, parent=parent)
        layout = QtWidgets.QHBoxLayout()
        self.host_node = None  # find out if there are more benefits from connecting properly to
        # host -- now we use 'host_node' instead of host, because we don't want this to be
        # automatically destroyed with the host.
        self.doc = None
        self.show()
        self.current_format = QtGui.QTextCharFormat()
        self._left_buttons = []

        # Left align
        #self.italic_icon = icon('italic24.png')
        #self.bold_icon = icon('bold24.png')
        #self.strikethrough_icon = icon('strikethrough24.png')
        #self.underline_icon = icon('underline24.png')
        #self.subscript_icon = icon('align_bottom24.png')
        #self.superscript_icon = icon('align_top24.png')
        #self.left_align_icon = icon('align_left24.png')
        #self.center_align_icon = icon('align_center24.png')
        #self.right_align_icon = icon('align_right24.png')
        #self.remove_styles_icon = icon('no_format24.png')

        self.italic = QuickEditButton(action='italic_button', parent=self,
                                      tooltip='Italic - \\emph{...} - <i>...</i>)',
                                      pixmap=qt_prefs.italic_icon)
        ui.add_button(self.italic, action='toggle_italic')
        self.italic.setCheckable(True)
        self._left_buttons.append(self.italic)
        layout.addWidget(self.italic)

        self.bold = QuickEditButton(action='bold_button', parent=self,
                                    tooltip='Bold - \\textbf{...} - <b>...</b>)',
                                    pixmap=qt_prefs.bold_icon)
        ui.add_button(self.bold, action='toggle_bold')
        self.bold.setCheckable(True)
        self._left_buttons.append(self.bold)
        layout.addWidget(self.bold)

        self.underline = QuickEditButton(action='underline_button', parent=self,
                                         tooltip='Underline - \\emph{...} - <u>...</u>)',
                                         pixmap=qt_prefs.underline_icon)
        ui.add_button(self.underline, action='toggle_underline')
        self.underline.setCheckable(True)
        self._left_buttons.append(self.underline)
        layout.addWidget(self.underline)

        self.strikethrough = QuickEditButton(action='strikethrough_button', parent=self,
                                             tooltip='Strikethrough',
                                             pixmap=qt_prefs.strikethrough_icon)
        ui.add_button(self.strikethrough, action='toggle_strikethrough')
        self.strikethrough.setCheckable(True)
        self._left_buttons.append(self.strikethrough)
        layout.addWidget(self.strikethrough)

        self.subscript = QuickEditButton(action='subscript_button', parent=self,
                                         tooltip='Subscript - \\_{...} - <sub>...</sub>)',
                                         pixmap=qt_prefs.subscript_icon)
        ui.add_button(self.subscript, action='toggle_subscript')
        self.subscript.setCheckable(True)
        self._left_buttons.append(self.subscript)
        layout.addWidget(self.subscript)

        self.superscript = QuickEditButton(action='superscript_button', parent=self,
                                           tooltip='Superscript - \\_{...} - <sup>...</sup>)',
                                           pixmap=qt_prefs.superscript_icon)
        ui.add_button(self.superscript, action='toggle_superscript')
        self.superscript.setCheckable(True)
        self._left_buttons.append(self.superscript)
        layout.addWidget(self.superscript)

        self.no_style = QuickEditButton(action='no_style_button', parent=self,
                                        tooltip='Remove styles',
                                        pixmap=qt_prefs.remove_styles_icon)
        ui.add_button(self.no_style, action='remove_styles')
        self._left_buttons.append(self.no_style)
        layout.addWidget(self.no_style)

        layout.setContentsMargins(2, 0, 2, 0)
        self.setLayout(layout)
        self.setMinimumHeight(28)
        min_width = 0
        for item in self._left_buttons:
            min_width += item.width()
        self.setMinimumWidth(min_width)
        #self.update_position()

    def connect_to(self, node, doc):
        self.host_node = node
        self.doc = doc

    def update_position(self):
        """ Make sure that float buttons are on host node's top left corner
        :return:
        """
        sh = self.sizeHint()
        self.resize(sh)
        if self.host_node:
            scene_pos = self.host_node.scenePos()
            view_pos = self.parentWidget().mapFromScene(scene_pos)
            self.move(view_pos.x() - sh.width() / 2, 36)
        #self.move(ctrl.ui.top_bar_buttons.left_edge_of_right_buttons() - sh.width() - 8, 36)

    def update_formats(self, char_format):
        if char_format != self.current_format:
            font = char_format.font()
            self.bold.setChecked(font.bold())
            self.italic.setChecked(font.italic())
            self.underline.setChecked(font.underline())
            self.strikethrough.setChecked(font.strikeOut())
            self.superscript.setChecked(char_format.verticalAlignment() == 1)
            self.subscript.setChecked(char_format.verticalAlignment() == 2)
            self.current_format = char_format

    def update_values(self):
        if self.doc:
            self.update_formats(self.host_node.label_object.char_format())
