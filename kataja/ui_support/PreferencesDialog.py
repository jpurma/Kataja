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

from kataja.ui_support.SettingsFields import FieldBuilder
from kataja.singletons import prefs, qt_prefs, ctrl


class PreferencesDialog(QtWidgets.QDialog):
    """

    """

    def __init__(self, main):
        QtWidgets.QDialog.__init__(self, parent=None)  # separate window
        self.setWindowTitle('Preferences')
        self.main = main
        self.left_area = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout()
        self.listwidget = QtWidgets.QListWidget()
        self.listwidget.setMaximumWidth(150)
        left_layout.addWidget(self.listwidget)
        self.reset_button = QtWidgets.QPushButton('Reset to defaults')
        self.reset_button.clicked.connect(ctrl.main.reset_preferences)
        left_layout.addWidget(self.reset_button)
        self.left_area.setLayout(left_layout)

        self.stackwidget = QtWidgets.QStackedLayout()
        self.pages = {}

        for page in prefs._tab_order:
            self.listwidget.addItem(page)
            widget, layout = self.get_page(page)
            self.stackwidget.addWidget(widget)

        self.listwidget.currentRowChanged.connect(self.stackwidget.setCurrentIndex)
        self.listwidget.setCurrentRow(0)
        lo = QtWidgets.QHBoxLayout()
        lo.addWidget(self.left_area)
        lo.addLayout(self.stackwidget)
        self.setLayout(lo)
        self.fields = {}

        paged = {}
        for key, value in vars(prefs).items():
            if key.startswith('_'):
                continue
            d = getattr(prefs, '_%s_ui' % key, {})
            if not d:
                continue
            tab = d.get('tab', 'Advanced')
            order = d.get('order', 999)
            d['value'] = value
            if tab not in paged:
                paged[tab] = {
                    'ordered': []
                }
            paged[tab][key] = d
            ordered = paged[tab]['ordered']
            ordered.append((order, key))

        for tab, tabdata in paged.items():
            ordered = tabdata['ordered']
            ordered.sort()
            widget, layout = self.get_page(tab)
            for o, key in ordered:
                d = tabdata[key]
                f = FieldBuilder.build_field(key, d, self, layout)
                if f:
                    self.fields[key] = f

    def trigger_all_updates(self):
        """ When reseting to defaults, on_change -updaters are not triggered. This method
        collects all of them and runs them. Good luck!
        :return:
        """
        # Change this to read
        methods = set()
        for f in self.fields.values():
            m = getattr(f, 'on_change_method', None)
            if m and m != ctrl.main.redraw:
                methods.add(m)
        for method in methods:
            method()
        self.main.redraw()

    def get_page(self, key):
        if key in self.pages:
            return self.pages[key], self.pages[key].layout()
        new_page = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout()
        self.pages[key] = new_page
        new_page.setLayout(layout)
        return new_page, layout

    def update_pens(self):
        """


        """
        self.main.redraw()

    def dpi_changed(self, index):
        """

        :param index:
        """
        prefs.dpi = int(self.dpi_choices[index])
