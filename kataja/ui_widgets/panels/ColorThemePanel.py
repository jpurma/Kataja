from PyQt5 import QtWidgets, QtCore

from kataja.singletons import ctrl, qt_prefs
from kataja.ui_widgets.Panel import Panel
import kataja.globals as g
from kataja.ui_support.SelectionBox import SelectionBox
import random

__author__ = 'purma'

dice = ['⚀', '⚁', '⚂', '⚃', '⚄', '⚅']


class RandomiseButton(QtWidgets.QPushButton):

    def __init__(self):
        QtWidgets.QPushButton.__init__(self)
        self.reroll()
        f = qt_prefs.get_font(g.MAIN_FONT)
        self.setStyleSheet('font-family: "%s"; font-size: %spx;' % (f.family(), f.pointSize()))
        self.setFixedSize(40, 20)
        self.setEnabled(False)

    def reroll(self):
        self.setText(random.choice(dice) + random.choice(dice))

class ColorPanel(Panel):
    """
        ⚀	U+2680	&#9856;
        ⚁	U+2681	&#9857;
        ⚂	U+2682	&#9858;
        ⚃	U+2683	&#9859;
        ⚄	U+2684	&#9860;
        ⚅	U+2685	&#9861;
        ★  U+2605  &#9733;
    """

    def __init__(self, name, default_position='float', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        Panel.__init__(self, name, default_position, parent, folded)
        layout = QtWidgets.QVBoxLayout()
        widget = QtWidgets.QWidget(self)
        widget.setMinimumWidth(160)
        widget.setMaximumWidth(220)
        widget.setMaximumHeight(60)
        self.watchlist = ['color_themes_changed']
        hlayout = QtWidgets.QHBoxLayout()
        f = qt_prefs.get_font(g.MAIN_FONT)

        self.selector = SelectionBox(self)
        self.selector_items = ctrl.cm.list_available_themes()
        self.selector.add_items(self.selector_items)
        self.ui_manager.connect_element_to_action(self.selector, 'set_color_theme')
        hlayout.addWidget(self.selector)
        self.randomise = RandomiseButton()
        ctrl.ui.connect_element_to_action(self.randomise,
                                          'randomise_palette')
        hlayout.addWidget(self.randomise, 1, QtCore.Qt.AlignRight)
        self.store_favorite = QtWidgets.QPushButton('★')
        self.store_favorite.setStyleSheet('font-family: "%s"; font-size: %spx;' % (f.family(),
                                                                                   f.pointSize()))
        self.store_favorite.setFixedSize(26, 20)
        self.store_favorite.setEnabled(False)
        ctrl.ui.connect_element_to_action(self.store_favorite,
                                          'remember_palette')
        hlayout.addWidget(self.store_favorite, 1, QtCore.Qt.AlignRight)

        layout.addLayout(hlayout)
        widget.setLayout(layout)

        self.setWidget(widget)
        self.finish_init()

    def update_available_themes(self):
        themes = ctrl.cm.list_available_themes()
        if self.selector_items != themes:
            self.selector_items = themes
            self.selector.clear()
            self.selector.add_items(self.selector_items)
            self.selector.select_by_data(ctrl.cm.theme_key)

    def showEvent(self, event):
        """ Panel may have missed signals to update its contents when it was hidden: update all
        that signals would update.
        :param event:
        :return:
        """
        self.update_available_themes()
        super().showEvent(event)

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
        if signal == 'color_themes_changed':
            print('colorthemepanel updates available themes')
            self.update_available_themes()

