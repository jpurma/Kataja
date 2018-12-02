from PyQt5 import QtWidgets, QtCore

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.SelectionBox import SelectionBox
from kataja.ui_widgets.buttons.PanelButton import PanelButton
from kataja.ui_support.panel_utils import box_row

__author__ = 'purma'


class SyntaxPanel(Panel):
    """ Switch between trees or derivation steps """

    def __init__(self, name, default_position='bottom', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_manager: pass a dictionary where buttons from this panel will be added
        """
        Panel.__init__(self, name, default_position, parent, folded)
        inner = self.widget()
        self.preferred_size = QtCore.QSize(220, 40)
        inner.setAutoFillBackground(True)

        layout = self.vlayout
        hlayout = box_row(layout)

        self.selector = SelectionBox(inner, action='set_visualization').to_layout(hlayout)
        for key, item in []:
            self.selector.addItem('%s (%s)' % (key, item.shortcut), key)

        self.toggle_options = PanelButton(pixmap=qt_prefs.settings_pixmap,
                                          tooltip='Visualization settings',
                                          parent=inner, size=20,
                                          action='toggle_panel_%s' % g.VIS_OPTIONS
                                          ).to_layout(hlayout, align=QtCore.Qt.AlignRight)
        self.toggle_options.setFixedSize(26, 26)
        self.toggle_options.setCheckable(True)
        ctrl.main.forest_changed.connect(self.update_treeset_counter)
        self.finish_init()

    def update_treeset_counter(self):
        keeper = ctrl.document
        if keeper is not None:
            display_index = keeper.current_index + 1
            max_index = len(keeper.forests)
            self.treeset_counter.setText('%s/%s' % (display_index, max_index))
