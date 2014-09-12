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

# class TwoColorIcon(QtGui.QIcon):
#     """ Icons that change their color according to widget where they are """
#
#     def paint(self, painter, **kwargs):
#         """
#
#         :param painter:
#         :param kwargs:
#         :return:
#         """
#         print('using twocoloricon painter')
#         return QtGui.QIcon.paint(self, painter, kwargs)
import kataja.debug as debug


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
        #self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum))
        self.panel = panel
        self.preferred_size = QtCore.QSize(220, 22)
        self.setBackgroundRole(QtGui.QPalette.Base)
        self.setAutoFillBackground(True)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(0)
        layout.minimumSize = self.sizeHint
        close_button = QtWidgets.QPushButton("x")
        close_button.setMaximumWidth(16)
        self.panel.ui_manager.connect_button_to_action(close_button, panel.get_visibility_action())
        layout.addWidget(close_button)
        debug.ui("Setting minimumSize for UIpanel to ", self.preferred_size)
        self.setMinimumSize(self.preferred_size)
        self.folded = False
        self.fold_button = QtWidgets.QPushButton("-")
        self.fold_button.setMaximumWidth(16)
        self.panel.ui_manager.connect_button_to_action(self.fold_button, panel.get_fold_action())
        self.pin_button = QtWidgets.QPushButton("p")
        self.pin_button.setMaximumWidth(16)
        self.panel.ui_manager.connect_button_to_action(self.pin_button, panel.get_pin_action())
        layout.addWidget(self.pin_button)

        self.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.fold_button)
        layout.addSpacing(8)
        layout.addWidget(QtWidgets.QLabel(name))
        self.setLayout(layout)

    def toggle_fold(self, caller):
        self.folded = not self.folded
        self.panel.set_folded(self.folded)
        if self.folded:
            self.fold_button.setText('+')
            self.fold_button.setStatusTip("Expand this panel")

        else:
            self.fold_button.setText('-')
            self.fold_button.setStatusTip("Minimize this panel")

    def sizeHint(self):
        return self.preferred_size

    def pin_to_dock(self):
        self.panel.pin_to_dock()


class UIPanel(QtWidgets.QDockWidget):
    """ UI windows that can be docked to main window or separated.
    Gives some extra control and helper methods on QDockWidget. """

    def __init__(self, name, key, default_position='bottom', parent=None, ui_manager=None, folded=False):
        """

        :param name:
        :param default_position:
        :param parent:
        """
        QtWidgets.QDockWidget.__init__(self, name, parent=parent)
        #self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))
        self.folded = folded
        self.name = name
        self._id = key
        self.ui_manager = ui_manager
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
        self.dockLocationChanged.connect(self.report_dock_location)
        self.topLevelChanged.connect(self.report_top_level)
        self.setContentsMargins(0, 0, 0, 0)
        title_widget = PanelTitle(name, self)
        self.setTitleBarWidget(title_widget)
        self.report_top_level(self.isFloating())


    def finish_init(self):
        self.set_folded(self.folded)
    # def dockLocationChanged(self, area):
    # print 'UIPanel %s docked: %s' % (self, area)

    # def topLevelChanged(self, floating):
    # print 'UIPanel %s floating: %s' % (self, floating)

    def get_visibility_action(self):
        return self.ui_manager.qt_actions['toggle_panel_%s' % self._id]

    def get_fold_action(self):
        return self.ui_manager.qt_actions['toggle_fold_panel_%s' % self._id]

    def get_pin_action(self):
        return self.ui_manager.qt_actions['pin_panel_%s' % self._id]


    def set_folded(self, folded):
        self.folded = folded
        debug.ui('Titlebar size:', self.titleBarWidget().size())
        debug.ui('Inner widget size:', self.widget().size())
        debug.ui('Before fold: ', self.size())
        if folded:
            self.widget().hide()
        else:
            self.widget().show()
        self.setFixedSize(self.sizeHint())
        self.updateGeometry()
        debug.ui('After fold: ', self.size())

    def pin_to_dock(self):
        self.setFloating(False)


    def report_dock_location(self, area):
        """

        :param area:
        """
        debug.ui('UIPanel %s docked: %s' % (self, area))

    def report_top_level(self, floating):
        """

        :param floating:
        """
        if floating:
            if hasattr(self, 'preferred_size'):
                self.resize(self.preferred_size)
            self.titleBarWidget().pin_button.show()
        else:
            self.titleBarWidget().pin_button.hide()
        debug.ui('UIPanel %s floating: %s' % (self, floating))

    def update_field(self, field_key, field, value):
        """

        :param field_key:
        :param field:
        :param value:
        """
        field.setText(value)

    def baseSize(self):
        debug.ui("Asking for UIPanel baseSize")
        return QtWidgets.QDockWidget.baseSize(self)

    def minimumSize(self):
        debug.ui("Asking for UIPanel minimumSize")
        return QtWidgets.QDockWidget.minimumSize(self)

    def minimumWidth(self):
        debug.ui("Asking for UIPanel minimumWidth")
        return QtWidgets.QDockWidget.minimumWidth(self)

    def minimumHeight(self):
        debug.ui("Asking for UIPanel minimumHeight")
        return QtWidgets.QDockWidget.minimumHeight(self)

    def maximumSize(self):
        debug.ui("Asking for UIPanel maximumSize")
        return QtWidgets.QDockWidget.maximumSize(self)

    def maximumWidth(self):
        debug.ui("Asking for UIPanel maximumWidth")
        return QtWidgets.QDockWidget.maximumWidth(self)

    def maximumHeight(self):
        debug.ui("Asking for UIPanel maximumHeight")
        return QtWidgets.QDockWidget.maximumHeight(self)

    def minimumSizeHint(self):
        debug.ui("Asking for UIPanel minimumSizeHint")
        if self.folded:
            return self.titleBarWidget().sizeHint()
        else:
            ws = self.widget().sizeHint()
            ts = self.titleBarWidget().sizeHint()
            return QtCore.QSize(max((ws.width(), ts.width())), ws.height()+ts.height())

    def sizeHint(self):
        debug.ui("Asking for UIPanel sizeHint")
        if self.folded:
            return self.titleBarWidget().sizeHint()
        else:
            ws = self.widget().sizeHint()
            ts = self.titleBarWidget().sizeHint()
            return QtCore.QSize(max((ws.width(), ts.width())), ws.height()+ts.height())

    def sizePolicy(self):
        debug.ui("Asking for UIPanel sizePolicy")
        return QtWidgets.QDockWidget.sizePolicy(self)


    def setMinimumSize(self, *__args):
        debug.ui("called setMinimumSize, ", str(__args))
        return QtWidgets.QDockWidget.setMinimumSize(self, *__args)

NONE = 0
FLAG = 1
CIRCLE = 2



