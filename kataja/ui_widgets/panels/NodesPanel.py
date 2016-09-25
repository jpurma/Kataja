from PyQt5 import QtWidgets, QtCore, QtGui

from kataja.singletons import qt_prefs, ctrl, prefs, classes
from kataja.ui_widgets.Panel import Panel
from kataja.ui_support.panel_utils import icon_button, label
import kataja.globals as g

__author__ = 'purma'


class DraggableNodeFrame(QtWidgets.QFrame):
    def __init__(self, key, name, parent=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.setBackgroundRole(QtGui.QPalette.AlternateBase)
        self.setAutoFillBackground(True)

        if ctrl.forest:
            style = ctrl.fs.node_style(key)
        else:
            style = prefs.node_styles[key][prefs.style]
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        color_key = style['color']
        self.key = key
        self.setPalette(ctrl.cm.palette_from_key(color_key))
        self.setFont(qt_prefs.get_font(style['font']))
        self.add_button = icon_button(ctrl.ui, self, hlayout,
                                      icon=qt_prefs.add_icon,
                                      text='Add ' + name,
                                      action='add_node',
                                      size=24,
                                      color_key=color_key,
                                      tooltip_suffix=name)
        self.add_button.data = key
        self.label = label(self, hlayout, text=name)
        self.label.setBuddy(self.add_button)

        self.conf_button = icon_button(ctrl.ui, self, hlayout,
                                       icon=qt_prefs.settings_pixmap,
                                       text='Modify %s behavior' % name,
                                       size=20,
                                       align=QtCore.Qt.AlignRight)
        self.setLayout(hlayout)

    def update_colors(self):
        settings = ctrl.fs.node_style(self.key)
        self.setPalette(ctrl.cm.palette_from_key(settings['color']))
        self.add_button.update_colors()
        self.setFont(qt_prefs.get_font(settings['font']))

    def update_frame(self):
        node_class = classes.nodes.get(self.key, None)
        if ctrl.free_drawing_mode:
            value = bool(node_class)
        else:
            value = node_class and not node_class.is_syntactic
        if value and not prefs.show_all_mode:
            value = node_class.is_syntactic
        self.setEnabled(value)

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


class NodesPanel(Panel):
    """ Switch between trees or derivation steps """

    def __init__(self, name, default_position='bottom', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_manager: pass a dictionary where buttons from this panel will be added
        """
        Panel.__init__(self, name, default_position, parent, folded)
        inner = QtWidgets.QWidget()
        inner.setMinimumWidth(160)
        self.watchlist = ['forest_changed', 'view_mode_changed', 'edit_mode_changed']

        #inner.setMinimumHeight(120)
        #inner.setMaximumHeight(150)
        #inner.preferred_size = QtCore.QSize(220, 120)

        layout = QtWidgets.QVBoxLayout()
        self.node_frames = {}

        for key in classes.node_types_order:
            nd = classes.node_info[key]
            frame = DraggableNodeFrame(key, nd['name'], parent=inner)
            self.node_frames[key] = frame
            layout.addWidget(frame)

        layout.setContentsMargins(2, 4, 6, 2)

        inner.setLayout(layout)
        self.setWidget(inner)
        self.widget().setAutoFillBackground(True)
        self.finish_init()

    def update_panel(self):
        """ Panel update should be necessary when changing ctrl.selection or after the trees has otherwise changed.
        :return:
        """
        for frame in self.node_frames.values():
            frame.update_frame()

    def update_colors(self):
        """
        :return: update node type labels with current palette
        """
        for frame in self.node_frames.values():
            frame.update_colors()

    def watch_alerted(self, obj, signal, field_name, value):
        """ Receives alerts from signals that this object has chosen to
        listen. These signals
         are declared in 'self.watchlist'.

         This method will try to sort out the received signals and act
         accordingly.

        :param obj: the object causing the alarm
        :param signal: identifier for type of the alarm
        :param field_name: name of the field of the object causing the alarm
        :param value: value given to the field
        :return:
        """
        # print('StylePanel alerted: ', obj, signal, field_name, value)
        if signal == 'view_mode_changed' or signal == 'edit_mode_changed':
            self.update_panel()
        elif signal == 'forest_changed':
            self.update_panel()
