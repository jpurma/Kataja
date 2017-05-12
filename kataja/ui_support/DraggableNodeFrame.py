from PyQt5 import QtWidgets, QtCore, QtGui

from kataja.singletons import qt_prefs, ctrl, prefs, classes
from kataja.ui_support.panel_utils import icon_button, label, mini_button, font_selector, \
    color_selector, mini_icon_button, modal_icon_button
import kataja.globals as g

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
        self.setPalette(ctrl.cm.palette_from_key(color_key))
        self.add_button = icon_button(ctrl.ui, self, hlayout,
                                      icon=qt_prefs.add_icon,
                                      text='Add ' + node_type_name,
                                      action='add_%s_node' % node_type_name,
                                      size=24,
                                      color_key=color_key)
        self.add_button.data = key

        self.fold_button = modal_icon_button(ctrl.ui, 'fold_%s_sheet' % node_type_name,
                                             self, hlayout,
                                             pixmap0=qt_prefs.fold_pixmap,
                                             pixmap1=qt_prefs.more_pixmap,
                                             action='fold_node_sheet',
                                             size=12)
                                             #align=QtCore.Qt.AlignRight)
        self.fold_button.data = key

        self.label = QtWidgets.QLabel(name, self)
        hlayout.addWidget(self.label)
        hlayout.addStretch(8)

        self.font_selector = font_selector(ctrl.ui, self, hlayout,
                                           action='select_%s_font' % node_type_name,
                                           label='', flat=True,
                                           align=QtCore.Qt.AlignRight
                                           )
        self.node_color_selector = color_selector(ctrl.ui, self, hlayout,
                                                  action='change_%s_color' % node_type_name,
                                                  role='node',
                                                  label='',
                                                  align=QtCore.Qt.AlignRight)

        self.setLayout(hlayout)
        f = ctrl.settings.active_nodes('font_id', of_type=key, level=ctrl.ui.active_scope)
        self.update_font(f)

    def update_colors(self):
        color_key = ctrl.settings.get_node_setting('color_id', node_type=self.key,
                                                   level=ctrl.ui.active_scope)
        if color_key:
            self.setPalette(ctrl.cm.palette_from_key(color_key))
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
        self.label.setStyleSheet(ss % {'font_size': f.pointSize(), 'font': f.family()})

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
            drag.setHotSpot(QtCore.QPoint(qt_prefs.leaf_pixmap.width() / 2,
                            qt_prefs.leaf_pixmap.height() / 2))
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
