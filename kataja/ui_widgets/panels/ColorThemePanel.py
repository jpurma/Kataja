from PyQt6 import QtCore

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_support.panel_utils import box_row
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.PushButtonBase import PushButtonBase
from kataja.ui_widgets.SelectionBox import SelectionBox
from kataja.ui_widgets.buttons.TwoColorButton import TwoColorButton

__author__ = 'purma'


def color_theme_fragment(panel, inner, layout):
    hlayout = box_row(layout)
    f = qt_prefs.get_font(g.MAIN_FONT)
    panel.selector = SelectionBox(parent=inner, action='set_active_color_theme').to_layout(hlayout)
    panel.selector.setMaximumWidth(120)
    panel.selector_items = ctrl.cm.list_available_themes()
    panel.selector.add_items(panel.selector_items)

    panel.randomise = RandomiseButton(parent=inner, text='', size=(40, 20),
                                      action='randomise_palette'
                                      ).to_layout(hlayout, align=QtCore.Qt.AlignmentFlag.AlignRight)

    panel.remove_theme = TwoColorButton(parent=inner, text='Remove', action='remove_color_theme',
                                        ).to_layout(hlayout, align=QtCore.Qt.AlignmentFlag.AlignRight)
    panel.remove_theme.hide()

    panel.store_favorite = UnicodeIconButton(parent=inner, text='★', size=(26, 20),
                                             action='remember_palette'
                                             ).to_layout(hlayout, align=QtCore.Qt.AlignmentFlag.AlignRight)
    panel.store_favorite.setStyleSheet(
        'font-family: "%s"; font-size: %spx;' % (f.family(), f.pointSize()))
    panel.store_favorite.setEnabled(False)
    panel.store_favorite.setMaximumWidth(26)


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
        self.preferred_size = QtCore.QSize(220, 48)
        ctrl.main.palette_changed.connect(self.update_available_themes)
        ctrl.main.color_themes_changed.connect(self.update_available_themes)
        color_theme_fragment(self, self.widget(), self.vlayout)
        self.selector_items = None
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
