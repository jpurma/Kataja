from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs, classes
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.buttons.PanelButton import PanelButton

__author__ = 'purma'


class DraggableMergeFrame(QtWidgets.QFrame):
    def __init__(self, parent=None):
        QtWidgets.QFrame.__init__(self, parent)
        self.setBackgroundRole(QtGui.QPalette.AlternateBase)
        self.setAutoFillBackground(True)
        hlayout = QtWidgets.QHBoxLayout()
        hlayout.setContentsMargins(0, 0, 0, 0)
        self.setMaximumHeight(48)
        self.setMinimumHeight(24)
        color_key = ctrl.settings.get_node_setting('color_key', node_type=g.CONSTITUENT_NODE,
                                                   level=ctrl.ui.active_scope)
        self.add_button = PanelButton(parent=self, icon=qt_prefs.add_icon, text='Add merge',
                                      action='add_merge', size=24, color_key=color_key).to_layout(
            hlayout)
        self.label = QtWidgets.QLabel('Merge -----------')
        hlayout.addWidget(self.label)
        self.setLayout(hlayout)

    def update_colors(self):
        color_key = ctrl.settings.get_node_setting('color_key', node_type=g.CONSTITUENT_NODE,
                                                   level=ctrl.ui.active_scope)
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


class MergePanel(Panel):
    """ Panel for editing how edges and nodes are drawn. """

    def __init__(self, name, default_position='right', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the
        construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        Panel.__init__(self, name, default_position, parent, folded)
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.watchlist = ['selection_changed', 'forest_changed', 'palette_changed']
        self.setMaximumWidth(220)
        self.frame = DraggableMergeFrame(parent=self)
        self.vlayout.addWidget(self.frame)
        self.finish_init()

    def update_selection(self):
        """ Called after ctrl.selection has changed. Prepare panel to use
        selection as scope
        :return:
        """
        # self.frame.update_frame()

    def update_colors(self):
        self.frame.update_colors()

    # @time_me
    def update_scope_selector_options(self):
        """ Redraw scope selector, show only scopes that are used in this
        forest """
        pass

    def showEvent(self, event):
        """ Panel may have missed signals to update its contents when it was hidden: update all
        that signals would update.
        :param event:
        :return:
        """
        self.update_selection()
        super().showEvent(event)

    def watch_alerted(self, obj, signal, field_name, value):
        """ Receives alerts from signals that this object has chosen to
        listen. These signals are declared in 'self.watchlist'.

         This method will try to sort out the received signals and act
         accordingly.

        :param obj: the object causing the alarm
        :param signal: identifier for type of the alarm
        :param field_name: name of the field of the object causing the alarm
        :param value: value given to the field
        :return:
        """
        if signal == 'selection_changed':
            self.update_selection()
        elif signal == 'forest_changed':
            self.update_selection()
        elif signal == 'palette_changed':
            self.update_colors()
