from PyQt5 import QtWidgets, QtCore

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.SelectionBox import SelectionBox
from kataja.ui_widgets.PushButtonBase import PushButtonBase
from kataja.ui_widgets.buttons.TwoColorButton import TwoColorButton
from kataja.ui_support.panel_utils import box_row

__author__ = 'purma'


def color_theme_fragment(panel, layout):
    hlayout = box_row(layout)
    f = qt_prefs.get_font(g.MAIN_FONT)
    panel.selector = SelectionBox(parent=panel, action='set_active_color_theme').to_layout(hlayout)
    panel.selector.setMaximumWidth(120)
    panel.selector_items = ctrl.cm.list_available_themes()
    panel.selector.add_items(panel.selector_items)

    panel.randomise = RandomiseButton(parent=panel, text='', size=(40, 20),
                                      action='randomise_palette'
                                      ).to_layout(hlayout, align=QtCore.Qt.AlignRight)

    panel.remove_theme = TwoColorButton(parent=panel, text='Remove', action='remove_color_theme',
                                        ).to_layout(hlayout, align=QtCore.Qt.AlignRight)
    panel.remove_theme.hide()

    panel.store_favorite = UnicodeIconButton(parent=panel, text='★', size=(26, 20),
                                             action='remember_palette'
                                             ).to_layout(hlayout, align=QtCore.Qt.AlignRight)
    panel.store_favorite.setStyleSheet(
        'font-family: "%s"; font-size: %spx;' % (f.family(), f.pointSize()))
    panel.store_favorite.setEnabled(False)


class UnicodeIconButton(PushButtonBase):
    """ PushButton that uses unicode characters as its icons. The main
    stylesheet assigns a well-equipped and larger font face for this class, and this requires
    that there exists a separate class for styling, but otherwise it is just a button base class.
    """
    pass


class RandomiseButton(UnicodeIconButton):

    def set_displayed_value(self, value):
        """ Instead of changing value, reflect value in button text."""
        self.setText(value)


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
        widget = self.widget()
        widget.setMinimumWidth(160)
        widget.setMaximumWidth(220)
        widget.setMaximumHeight(60)
        self.watchlist = ['color_themes_changed', 'palette_changed']
        color_theme_fragment(self, self.vlayout)
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

