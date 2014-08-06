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

from PyQt5 import QtCore, QtWidgets

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
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(0)
        layout.minimumSize = self.sizeHint
        close_button = QtWidgets.QPushButton("x")
        close_button.setMaximumWidth(16)
        close_action = panel.toggleViewAction()
        close_button.clicked.connect(close_action.trigger)
        layout.addWidget(close_button)
        self.setMinimumSize(self.preferred_size)
        self.folded = False
        self.fold_button = QtWidgets.QPushButton("-")
        self.fold_button.setMaximumWidth(16)
        self.fold_button.clicked.connect(self.toggle_fold)
        layout.addWidget(self.fold_button)
        layout.addSpacing(8)
        layout.addWidget(QtWidgets.QLabel(name))
        self.setLayout(layout)

    def toggle_fold(self, caller):
        self.folded = not self.folded
        self.panel.set_folded(self.folded)
        if self.folded:
            self.fold_button.setText('+')
        else:
            self.fold_button.setText('-')

    def sizeHint(self):
        return self.preferred_size



class UIPanel(QtWidgets.QDockWidget):
    """ UI windows that can be docked to main window or separated.
    Gives some extra control and helper methods on QDockWidget. """

    def __init__(self, name, default_position='bottom', parent=None, ui_manager=None, folded=False):
        """

        :param name:
        :param default_position:
        :param parent:
        """
        QtWidgets.QDockWidget.__init__(self, name, parent=parent)
        self.setSizePolicy(QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed))
        self.folded = folded
        self.name = name
        self.ui_manager = ui_manager
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
        title_widget = PanelTitle(name, self)
        self.setTitleBarWidget(title_widget)


    def finish_init(self):
        self.set_folded(self.folded)

    # def dockLocationChanged(self, area):
    # print 'UIPanel %s docked: %s' % (self, area)

    # def topLevelChanged(self, floating):
    # print 'UIPanel %s floating: %s' % (self, floating)

    def set_folded(self, folded):
        self.folded = folded
        if folded:
            self.widget().hide()
        else:
            self.widget().show()
        self.updateGeometry()


    def report_dock_location(self, area):
        """

        :param area:
        """
        print('UIPanel %s docked: %s' % (self, area))

    def report_top_level(self, floating):
        """

        :param floating:
        """
        if floating and hasattr(self, 'preferred_size'):
            w, h = self.preferred_size
            self.resize(w, h)
        print('UIPanel %s floating: %s' % (self, floating))

    def update_field(self, field_key, field, value):
        """

        :param field_key:
        :param field:
        :param value:
        """
        field.setText(value)

    def sizeHint(self):
        print("Asking for UIPanel sizeHint")
        if self.folded:
            return self.titleBarWidget().sizeHint()
        else:
            ws = self.widget().sizeHint()
            ts = self.titleBarWidget().sizeHint()
            return QtCore.QSize(max((ws.width, ts.width)), ws.height()+ts.height())


NONE = 0
FLAG = 1
CIRCLE = 2



