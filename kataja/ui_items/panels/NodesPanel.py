from PyQt5 import QtWidgets, QtCore, QtGui

from kataja.singletons import qt_prefs, ctrl, prefs
from ui_items.Panel import Panel
from ui_items.panels import icon_button, label

__author__ = 'purma'


class DraggableNodeFrame(QtWidgets.QFrame):
    def __init__(self, key, name, parent=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.setBackgroundRole(QtGui.QPalette.AlternateBase)
        self.setAutoFillBackground(True)

        if ctrl.forest:
            settings = ctrl.fs.node_info()
        else:
            settings = prefs.nodes
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        color_key = settings[key]['color']
        self.key = key
        self.setPalette(ctrl.cm.palette_from_key(color_key))
        self.setFont(qt_prefs.font(settings[key]['font']))
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
        settings = ctrl.fs.node_info(self.key)
        self.setPalette(ctrl.cm.palette_from_key(settings['color']))
        self.add_button.update_colors()
        self.setFont(qt_prefs.font(settings['font']))

    def mousePressEvent(self, event):
        self.add_button.setDown(True)
        data = QtCore.QMimeData()
        data.setText('kataja:new_node:%s' % self.key)
        drag = QtGui.QDrag(self)
        drag.setMimeData(data)
        drag.exec_(QtCore.Qt.CopyAction)
        self.add_button.setDown(False)
        QtWidgets.QFrame.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        self.add_button.setDown(False)
        ctrl.ui.set_scope(self.key)
        ctrl.deselect_objects()
        ctrl.call_watchers(self, 'scope_changed')
        QtWidgets.QFrame.mouseReleaseEvent(self, event)


class NodesPanel(Panel):
    """ Switch between trees or derivation steps """

    def __init__(self, name, key, default_position='bottom', parent=None, ui_manager=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_manager: pass a dictionary where buttons from this panel will be added
        """
        Panel.__init__(self, name, key, default_position, parent, ui_manager, folded)
        inner = QtWidgets.QWidget()
        inner.setMinimumWidth(160)
        #inner.setMinimumHeight(120)
        #inner.setMaximumHeight(150)
        #inner.preferred_size = QtCore.QSize(220, 120)

        layout = QtWidgets.QVBoxLayout()
        self.node_frames = {}

        for key in prefs.node_types_order:
            nd = prefs.nodes[key]
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
        pass

    def update_colors(self):
        """
        :return: update node type labels with current palette
        """
        for frame in self.node_frames.values():
            frame.update_colors()
