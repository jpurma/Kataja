from PyQt5 import QtWidgets, QtCore

from kataja.singletons import ctrl, qt_prefs
from kataja.ui_widgets.Panel import Panel
import kataja.globals as g
from kataja.ui_support.SelectionBox import SelectionBox
import random

from kataja.ui_support.TwoColorButton import TwoColorButton

__author__ = 'purma'



def color_theme_fragment(panel, layout):
    hlayout = QtWidgets.QHBoxLayout()
    f = qt_prefs.get_font(g.MAIN_FONT)
    panel.selector = SelectionBox(panel)
    panel.selector.setMaximumWidth(120)
    panel.selector_items = ctrl.cm.list_available_themes()
    panel.selector.add_items(panel.selector_items)
    panel.ui_manager.connect_element_to_action(panel.selector, 'set_active_color_theme')
    hlayout.addWidget(panel.selector)

    panel.randomise = UnicodeIconButton('')
    panel.randomise.setFixedSize(40, 20)
    ctrl.ui.connect_element_to_action(panel.randomise, 'randomise_palette')
    hlayout.addWidget(panel.randomise, 1, QtCore.Qt.AlignRight)

    panel.remove_theme = TwoColorButton('Remove')
    #panel.remove_theme.setFixedSize(40, 20)
    ctrl.ui.connect_element_to_action(panel.remove_theme, 'remove_color_theme')
    panel.remove_theme.hide()
    hlayout.addWidget(panel.remove_theme, 1, QtCore.Qt.AlignRight)

    panel.store_favorite = UnicodeIconButton('★')
    panel.store_favorite.setStyleSheet(
        'font-family: "%s"; font-size: %spx;' % (f.family(), f.pointSize()))
    panel.store_favorite.setFixedSize(26, 20)
    panel.store_favorite.setEnabled(False)
    ctrl.ui.connect_element_to_action(panel.store_favorite, 'remember_palette')
    hlayout.addWidget(panel.store_favorite, 1, QtCore.Qt.AlignRight)
    layout.addLayout(hlayout)


class UnicodeIconButton(QtWidgets.QPushButton):
    """ PushButton that uses unicode characters as its icons. This requires that the main
    stylesheet assigns a well-equipped and larger font face for this class.
    """
    def __init__(self, text):
        QtWidgets.QPushButton.__init__(self, text=text)


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
        self.watchlist = ['color_themes_changed', 'palette_changed']
        color_theme_fragment(self, layout)
        widget.setLayout(layout)

        self.setWidget(widget)
        self.finish_init()

    def update_available_themes(self):
        themes = ctrl.cm.list_available_themes()
        key = ctrl.cm.theme_key
        if self.selector_items != themes:
            self.selector_items = themes
            self.selector.clear()
            self.selector.add_items(self.selector_items)
            self.selector.select_by_data(key)
        if key in ctrl.cm.custom_themes:
            self.randomise.hide()
            self.store_favorite.hide()
            self.remove_theme.show()
        else:
            self.remove_theme.hide()
            self.randomise.show()
            self.store_favorite.show()

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
            self.update_available_themes()
        elif signal == 'palette_changed':
            self.update_available_themes()

