# coding=utf-8
# ############################################################################
#
# *** Kataja - Biolinguistic Visualization tool ***
#
# Copyright 2013 Jukka Purma
#
# This file is part of Kataja.
#
# Kataja is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Kataja is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kataja.  If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################

from PyQt5 import QtCore, QtWidgets, QtGui

from kataja.singletons import ctrl, qt_prefs
from kataja.ui_support.panel_utils import mini_icon_button, label
from kataja.UIItem import UIWidget


# Hey! This is only the top row title, not the actual UIPanel(DockWidget)! It is down below.

class PanelTitle(QtWidgets.QWidget):
    """ Widget for displaying panel title and control buttons in a concise form """

    def __init__(self, name, panel):
        """

        :param name:
        :param parent:
        :param use_title:
        :return:
        """
        QtWidgets.QWidget.__init__(self, parent=panel)
        # self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum))
        self.panel = panel
        self.preferred_size = QtCore.QSize(220, 22)
        self._watched = False
        self.setBackgroundRole(QtGui.QPalette.Base)
        self.setAutoFillBackground(True)
        self.setMinimumSize(self.preferred_size)
        self.setContentsMargins(0, 0, 0, 0)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(0)
        layout.minimumSize = self.sizeHint
        ui = self.panel.ui_manager

        mini_icon_button(ui, self, layout,
                         icon=qt_prefs.close_icon,
                         text='Close panel',
                         action='toggle_panel_' + self.panel.ui_type)

        self.pin_button = mini_icon_button(ui, self, layout,
                                           icon=qt_prefs.pin_drop_icon,
                                           text='Dock this panel',
                                           action='pin_panel')
        self.fold_button = mini_icon_button(ui, self, layout,
                                            icon=qt_prefs.fold_icon,
                                            text='Minimize this panel',
                                            action='toggle_fold_panel')
        layout.addSpacing(8)
        self.title = label(self, layout, name)
        self.setLayout(layout)

    def update_fold(self, folded):
        if folded:
            self.fold_button.setIcon(QtGui.QIcon(qt_prefs.more_icon))
            self.fold_button.setStatusTip("Expand this panel")
        else:
            self.fold_button.setIcon(QtGui.QIcon(qt_prefs.fold_icon))
            self.fold_button.setStatusTip("Minimize this panel")

    def sizeHint(self):
        return self.preferred_size

    def pin_to_dock(self):
        self.panel.pin_to_dock()


class Panel(UIWidget, QtWidgets.QDockWidget):
    """ UI windows that can be docked to main window or separated.
    Gives some extra control and helper methods on QDockWidget. """
    permanent_ui = True
    unique = True

    def __init__(self, name, default_position='bottom', parent=None, ui_manager=None, folded=False):
        """

        :param name:
        :param default_position:
        :param parent:
        """
        UIWidget.__init__(self)
        QtWidgets.QDockWidget.__init__(self, name, parent=parent)
        # self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))
        self.ui_type == 'Panel'
        self.folded = folded
        self.name = name
        self._watched = False
        self._last_position = None
        self.resize_grip = None
        self.watchlist = []
        self.default_position = default_position

        if default_position == 'bottom':
            parent.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self)
        elif default_position == 'top':
            parent.addDockWidget(QtCore.Qt.TopDockWidgetArea, self)
        elif default_position == 'left':
            parent.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self)
        elif default_position == 'right':
            parent.addDockWidget(QtCore.Qt.RightDockWidgetArea, self)
        elif default_position == 'float':
            parent.addDockWidget(QtCore.Qt.RightDockWidgetArea, self)
            self.setFloating(True)
            self.move(self.initial_position())
        self.dockLocationChanged.connect(self.report_dock_location)
        self.topLevelChanged.connect(self.report_top_level)
        self.setContentsMargins(0, 0, 0, 0)
        title_widget = PanelTitle(name, self)
        self.setTitleBarWidget(title_widget)
        self.report_top_level(self.isFloating())

    def finish_init(self):
        """ Do initializations that need to be done after the subclass __init__
        has completed. e.g. hide this from view, which can have odd results
        for measurements for elements and layouts if it is called before
        setting them up. Subclass __init__:s must call finish_init at the end!
        :return:
        """
        self.set_folded(self.folded)

    # def dockLocationChanged(self, area):
    # print 'UIPanel %s docked: %s' % (self, area)

    # def topLevelChanged(self, floating):
    # print 'UIPanel %s floating: %s' % (self, floating)

    def get_visibility_action(self):
        return self.ui_manager.qt_actions['toggle_panel_%s' % self.ui_key]

    def update_panel(self):
        """ Implement if general update everything is needed
        :return:
        """
        pass

    def set_title(self, title):
        self.titleBarWidget().title.setText(title)

    def update_colors(self):
        """ Implement if trickier color update than palette change is needed
        :return:
        """
        pass

    def set_folded(self, folded):
        self.folded = folded
        self.titleBarWidget().update_fold(folded)
        if folded:
            self.widget().hide()
        else:
            self.widget().show()
        self.resize(self.sizeHint())
        # self.setFixedSize(self.sizeHint())
        self.updateGeometry()

    def pin_to_dock(self):
        self.setFloating(False)

    def report_dock_location(self, area):
        """

        :param area:
        """


    def report_top_level(self, floating):
        """

        :param floating:
        """
        if floating:
            if hasattr(self, 'preferred_size'):
                self.resize(self.preferred_size)
            self.titleBarWidget().pin_button.show()
            if self.resize_grip:
                self.resize_grip.show()
        else:
            self.titleBarWidget().pin_button.hide()
            if self.resize_grip:
                self.resize_grip.hide()

    def update_field(self, field_key, field, value):
        """

        :param field_key:
        :param field:
        :param value:
        """
        field.setText(value)



    def minimumSizeHint(self):
        if self.folded:
            return self.titleBarWidget().sizeHint()
        else:
            ws = self.widget().sizeHint()
            ts = self.titleBarWidget().sizeHint()
            return QtCore.QSize(max((ws.width(), ts.width())), ws.height() + ts.height())

    def sizeHint(self):
        """


        :return:
        """
        if self.folded:
            return self.titleBarWidget().sizeHint()
        elif self.widget():
            ws = self.widget().sizeHint()
            ts = self.titleBarWidget().sizeHint()
            return QtCore.QSize(max((ws.width(), ts.width())), ws.height() + ts.height())
        else:
            return QtCore.QSize(100, 100)

    def initial_position(self):
        """


        :return:
        """
        return QtCore.QPoint(ctrl.main.x() / ctrl.main.devicePixelRatio() + ctrl.main.width(),
                             ctrl.main.y() / ctrl.main.devicePixelRatio())

    def watch_alerted(self, obj, signal, field_name, value):
        """ Receives alerts from signals that this object has chosen to listen. These signals
         are declared in 'self.watchlist'.

         This method will try to sort out the received signals and act accordingly.

        :param obj: the object causing the alarm
        :param signal: identifier for type of the alarm
        :param field_name: name of the field of the object causing the alarm
        :param value: value given to the field
        :return:
        """
        print('watch alerted: ', obj, signal, field_name, value)

    def showEvent(self, QShowEvent):
        """

        :param QShowEvent:
        """
        if self.isFloating():
            self.move(self.initial_position())
        if not self._watched:
            for signal in self.watchlist:
                ctrl.add_watcher(signal, self)
            self._watched = True
        QtWidgets.QDockWidget.showEvent(self, QShowEvent)

    def closeEvent(self, QCloseEvent):
        """

        :param QCloseEvent:
        :return:
        """
        ctrl.remove_from_watch(self)
        self._watched = False
        QtWidgets.QDockWidget.closeEvent(self, QCloseEvent)

NONE = 0
FLAG = 1
CIRCLE = 2



