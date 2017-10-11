from PyQt5 import QtWidgets, QtCore, QtGui

from kataja.singletons import qt_prefs, ctrl, classes
from kataja.ui_widgets.buttons.TwoStateIconButton import TwoStateIconButton
from kataja.ui_widgets.selection_boxes.ColorSelector import ColorSelector
from kataja.ui_widgets.selection_boxes.FontSelector import FontSelector
from kataja.ui_widgets.buttons.PanelButton import PanelButton
from kataja.ui_widgets.buttons.EyeButton import EyeButton

__author__ = 'purma'

ss = """font-family: "%(font)s"; font-size: %(font_size)spx;"""


class DraggableNodeFrame(QtWidgets.QFrame):
    def __init__(self, key, name, parent=None, folded=False):
        QtWidgets.QFrame.__init__(self, parent)
        self.setBackgroundRole(QtGui.QPalette.AlternateBase)
        self.setContentsMargins(0, 0, 0, 0)
        self.setAutoFillBackground(True)
        self.sheet = None
        node_type_name = name.lower()
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 8, 0)
        self.setMaximumHeight(32)
        color_key = ctrl.settings.get_node_setting('color_id', node_type=key,
                                                   level=ctrl.ui.active_scope)

        self.key = key
        self.folded = folded
        self.add_button = PanelButton(parent=self, pixmap=qt_prefs.add_icon,
                                      action='add_%s_node' % node_type_name, size=24,
                                      color_key=color_key).to_layout(hlayout)
        self.add_button.data = key

        self.fold_button = TwoStateIconButton(ui_key='fold_%s_sheet' % node_type_name, parent=self,
                                              pixmap0=qt_prefs.fold_pixmap,
                                              pixmap1=qt_prefs.more_pixmap,
                                              action='fold_node_sheet', size=12).to_layout(hlayout)
        self.fold_button.data = key

        self.label = QtWidgets.QLabel(name, self)
        hlayout.addWidget(self.label)
        hlayout.addStretch(8)

        self.node_type_visible = EyeButton(action='toggle_%s_visibility' % node_type_name, height=22,
                                           width=26).to_layout(hlayout)

        self.font_selector = FontSelector(parent=self,
                                          action='select_%s_font' % node_type_name, ).to_layout(
            hlayout, align=QtCore.Qt.AlignRight)

        self.node_color_selector = ColorSelector(parent=self,
                                                 action='change_%s_color' % node_type_name,
                                                 ).to_layout(
            hlayout, align=QtCore.Qt.AlignRight)

        self.setLayout(hlayout)
        f = ctrl.settings.get_node_setting('font_id', node_type=key)
        self.update_font(f)

    def update_colors(self):
        color_key = ctrl.settings.get_node_setting('color_id', node_type=self.key,
                                                   level=ctrl.ui.active_scope)
        if color_key:
            self.font_selector.set_color(color_key)
            self.node_color_selector.set_color(color_key)
        self.add_button.update_colors(color_key=color_key)

    def update_frame(self):
        node_class = classes.nodes.get(self.key, None)
        if ctrl.free_drawing_mode:
            value = bool(node_class)
        else:
            value = node_class and not node_class.is_syntactic
        if value and ctrl.settings.get('syntactic_mode'):
            value = node_class.is_syntactic
        self.setEnabled(value)

    def update_font(self, font_key):
        f = qt_prefs.get_font(font_key)
        self.label.setStyleSheet(ss % {
            'font_size': f.pointSize(),
            'font': f.family()
        })

    def set_folded(self, value):
        self.folded = value
        if self.sheet:
            if value:
                self.sheet.hide()
            else:
                self.sheet.show()

    def mousePressEvent(self, event):
        if self.isEnabled():
            self.add_button.setDown(True)
            data = QtCore.QMimeData()
            data.setText('kataja:new_node:%s' % self.key)
            drag = QtGui.QDrag(self)
            drag.setPixmap(qt_prefs.leaf_pixmap)
            drag.setHotSpot(QtCore.QPoint(int(qt_prefs.leaf_pixmap.width() / 2),
                                          int(qt_prefs.leaf_pixmap.height() / 2)))
            drag.setMimeData(data)
            drag.exec_(QtCore.Qt.CopyAction)
            self.add_button.setDown(False)
        QtWidgets.QFrame.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        if self.isEnabled():
            self.add_button.setDown(False)
            ctrl.ui.set_scope(self.key)
            ctrl.deselect_objects()
            ctrl.call_watchers(self, 'scope_changed')
        QtWidgets.QFrame.mouseReleaseEvent(self, event)
