from PyQt5 import QtWidgets, QtCore

from kataja.singletons import ctrl, qt_prefs
from kataja.ui_widgets.Panel import Panel
import kataja.globals as g
from kataja.ui_support.SelectionBox import SelectionBox

__author__ = 'purma'




class ColorPanel(Panel):
    """
        ⚀	U+2680	&#9856;
        ⚁	U+2681	&#9857;
        ⚂	U+2682	&#9858;
        ⚃	U+2683	&#9859;
        ⚄	U+2684	&#9860;
        ⚅	U+2685	&#9861;
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

        ocm = ctrl.cm.ordered_color_modes
        self.selector_items = [(c['name'], key) for key, c in ocm.items()]
        hlayout = QtWidgets.QHBoxLayout()

        self.selector = SelectionBox(self)
        self.selector.add_items(self.selector_items)
        self.ui_manager.connect_element_to_action(self.selector, 'set_color_mode')
        hlayout.addWidget(self.selector)
        self.randomize = QtWidgets.QPushButton('⚁⚅')
        self.randomize.setFont(qt_prefs.fonts[g.MAIN_FONT])
        self.randomize.setFixedSize(40, 20)
        self.randomize.setEnabled(False)
        ctrl.ui.connect_element_to_action(self.randomize,
                                          'randomize_palette')
        hlayout.addWidget(self.randomize, 1, QtCore.Qt.AlignRight)

        layout.addLayout(hlayout)
        widget.setLayout(layout)

        self.setWidget(widget)
        self.finish_init()

    def update_colors(self):
        """

        """
        ocm = ctrl.cm.ordered_color_modes
        current_color_modes = [(c['name'], key) for key, c in ocm.items()]
        if self.selector_items != current_color_modes:
            self.selector.clear()
            self.selector.add_items(current_color_modes)
            self.selector.select_by_text(ctrl.cm.current_color_mode)

