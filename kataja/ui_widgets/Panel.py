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

from kataja.UIItem import UIWidget
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_support.panel_utils import label
from kataja.ui_widgets.buttons.PanelButton import PanelButton
from kataja.ui_widgets.buttons.TwoStateIconButton import TwoStateIconButton
from kataja.KatajaAction import KatajaAction

ss = """font-family: "%(font)s"; font-size: %(font_size)spx;"""


class PanelAction(KatajaAction):

    def __init__(self):
        super().__init__()
        self.panel = None

    def on_connect(self, ui_item):
        def find_panel_widget(panel):
            if isinstance(panel, Panel):
                return panel
            elif panel:
                return find_panel_widget(panel.parentWidget())

        self.panel = find_panel_widget(ui_item.parentWidget())


class PanelTitle(QtWidgets.QWidget):
    """ Widget for displaying panel title and control buttons in a concise form """

    def __init__(self, name, panel, foldable=True):
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
        self.setBackgroundRole(QtGui.QPalette.Base)
        self.setAutoFillBackground(True)
        self.setMinimumSize(self.preferred_size)
        self.setContentsMargins(0, 0, 0, 0)
        layout = QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 2, 8, 2)
        layout.setSpacing(0)
        layout.minimumSize = self.sizeHint

        self.close_button = PanelButton(parent=self,
                                        pixmap=qt_prefs.close_icon,
                                        action='toggle_panel',
                                        size=12).to_layout(layout)
        self.close_button.setFixedWidth(16)
        self.close_button.data = panel.ui_key
        self.close_button.show()

        self.fold_button = TwoStateIconButton(ui_key='fold_%s_panel' % panel.name,
                                              parent=self,
                                              pixmap0=qt_prefs.fold_pixmap,
                                              pixmap1=qt_prefs.more_pixmap,
                                              action='toggle_fold_panel',
                                              size=12).to_layout(layout)
        self.fold_button.setEnabled(foldable)
        self.fold_button.setVisible(foldable)
        self.fold_button.data = panel.ui_key
        self.fold_button.setMaximumWidth(16)
        self.title = label(self, layout, name)
        self.label_index = layout.count() - 1
        layout.addStretch(12)
        self.setLayout(layout)

    def update_fold(self, folded):
        if folded:
            self.fold_button.setChecked(True)
        else:
            self.fold_button.setChecked(False)
        self.updateGeometry()

    def push_to_layout(self, widget):
        layout = self.layout()
        layout.addWidget(widget, alignment=QtCore.Qt.AlignRight)

    def add_before_label(self, widget):
        self.layout().insertWidget(self.label_index, widget)
        self.label_index += 1

    def sizeHint(self):
        return self.preferred_size

    def update_font(self, font_key):
        f = qt_prefs.get_font(font_key)
        self.title.setStyleSheet(ss % {
            'font_size': f.pointSize(),
            'font': f.family()
        })


class Panel(UIWidget, QtWidgets.QDockWidget):
    """ UI windows that can be docked to main window or separated.
    Gives some extra control and helper methods on QDockWidget. """
    permanent_ui = True
    unique = True

    def __init__(self, name, default_position='bottom', parent=None, folded=False, foldable=True):
        """

        :param name:
        :param default_position:
        :param parent:
        """
        UIWidget.__init__(self)
        QtWidgets.QDockWidget.__init__(self, name, parent=parent)
        self.folded = folded
        self.name = name
        self._last_position = None
        self.resize_grip = None
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
        self.title_widget = PanelTitle(name, self, foldable=foldable)
        self.setTitleBarWidget(self.title_widget)
        self.report_top_level(self.isFloating())
        inner = QtWidgets.QWidget(self)
        self.vlayout = QtWidgets.QVBoxLayout()
        inner.setLayout(self.vlayout)
        self.setWidget(inner)

    def finish_init(self):
        """ Do initializations that need to be done after the subclass __init__
        has completed. e.g. hide this from view, which can have odd results
        for measurements for elements and layouts if it is called before
        setting them up. Subclass __init__:s must call finish_init at the end!
        :return:
        """
        self.set_folded(self.folded)
        if self.isFloating():
            self.move(self.initial_position())

    # def dockLocationChanged(self, area):
    # print 'UIPanel %s docked: %s' % (self, area)

    # def topLevelChanged(self, floating):
    # print 'UIPanel %s floating: %s' % (self, floating)

    def push_to_title(self, widget):
        self.title_widget.push_to_layout(widget)

    def prefix_for_title(self, widget):
        self.title_widget.add_before_label(widget)

    def get_visibility_action(self):
        return self.ui_manager.actions['toggle_panel_%s' % self.ui_key]

    def update_panel(self):
        """ Implement if general update everything is needed
        :return:
        """
        pass

    def set_title(self, title):
        self.titleBarWidget().title.setText(title)

    def set_folded(self, folded):
        self.folded = folded
        self.titleBarWidget().update_fold(folded)
        widget = self.widget()
        if widget:
            if folded:
                widget.hide()
            else:
                widget.show()
        self.resize(self.sizeHint())
        # self.setFixedSize(self.sizeHint())
        self.updateGeometry()

    def report_dock_location(self, area):
        """

        :param area:
        """
        pass

    def report_top_level(self, floating):
        """

        :param floating:
        """
        if floating:
            if hasattr(self, 'preferred_size'):
                self.resize(self.preferred_size)
            if self.resize_grip:
                self.resize_grip.show()
        else:
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
        if self.folded or not self.widget():
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

    def initial_position(self, next_to=''):
        """


        :return:
        """
        self.update_panel()
        if next_to:
            dp = self.ui_manager.get_panel(next_to)
        else:
            dp = None
        if dp:
            pixel_ratio = dp.devicePixelRatio()
            p = dp.mapToGlobal(dp.pos())
            x = p.x()
            y = p.y()
            if pixel_ratio:
                x /= pixel_ratio
                y /= pixel_ratio
            if dp.isFloating():
                y += 20
            else:
                x += dp.width() + 40
        else:
            pixel_ratio = ctrl.main.devicePixelRatio()
            if pixel_ratio < 1:
                pixel_ratio = 1
            x = ctrl.main.x() / pixel_ratio + ctrl.main.width()
            y = max(40, ctrl.main.y() / pixel_ratio)
        w = self.width()
        h = self.height()
        screen_rect = ctrl.main.app.desktop().availableGeometry()
        if x + w > screen_rect.right():
            x = screen_rect.right() - w
        if y + h > screen_rect.bottom():
            y = screen_rect.bottom() - h
        return QtCore.QPoint(x, y)




