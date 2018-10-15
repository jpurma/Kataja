from PyQt5 import QtWidgets

from kataja.singletons import ctrl, classes, qt_prefs
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.buttons.EyeButton import EyeButton
from kataja.ui_widgets.buttons.PanelButton import PanelButton
from kataja.ui_widgets.selection_boxes.ColorSelector import ColorSelector
from kataja.ui_widgets.selection_boxes.FontSelector import FontSelector

__author__ = 'purma'


class NodePanel(Panel):
    """ Panel for editing how edges and nodes are drawn. """

    def __init__(self, name, node_type, default_position='right', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the
        construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """

        Panel.__init__(self, name, default_position, parent, folded)
        ctrl.main.palette_changed.connect(self.update_colors)
        self.setMaximumWidth(220)
        self.node_type = node_type
        node_type_name = classes.node_info[node_type]['name'].lower()
        color_key = ctrl.ui.get_active_node_setting('color_key', node_type=node_type)

        action_name = 'add_%s_node' % node_type_name
        self.add_button = PanelButton(parent=self, pixmap=qt_prefs.add_icon,
                                      action=action_name, size=20,
                                      color_key=color_key)
        self.add_button.data = node_type
        self.prefix_for_title(self.add_button)

        self.node_type_visible = EyeButton(action='toggle_%s_visibility' % node_type_name,
                                           height=20, width=26)
        self.push_to_title(self.node_type_visible)

        self.font_selector = FontSelector(parent=self,
                                          action='select_%s_font' % node_type_name)
        self.push_to_title(self.font_selector)

        self.node_color_selector = ColorSelector(parent=self,
                                                 action='change_%s_color' % node_type_name)
        self.push_to_title(self.node_color_selector)

        f = ctrl.ui.get_active_node_setting('font_id', node_type=node_type)
        self.update_title_font(f)

        container = self.widget()
        container.setContentsMargins(0, 0, 0, 0)
        self.vlayout.setContentsMargins(4, 4, 4, 8)
        container.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        self.finish_init()

    def update_colors(self):
        color_key = ctrl.ui.get_active_node_setting('color_key', node_type=self.node_type)
        if color_key:
            self.font_selector.set_color(color_key)
            self.node_color_selector.set_color(color_key)
        self.add_button.update_colors(color_key=color_key)

    def update_title_font(self, font_key):
        self.title_widget.update_font(font_key)

    # @time_me
    def update_scope_selector_options(self):
        """ Redraw scope selector, show only scopes that are used in this
        forest """
        pass
