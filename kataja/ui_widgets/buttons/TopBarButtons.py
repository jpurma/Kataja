# coding=utf-8
from PyQt5 import QtWidgets, QtCore
from kataja.ui_widgets.buttons.OverlayButton import TopRowButton, VisButton

import kataja.globals as g
from kataja.singletons import ctrl, qt_prefs
from kataja.visualizations.available import VISUALIZATIONS
from kataja.ui_widgets.buttons.TwoStateIconButton import TwoStateIconButton
from kataja.ui_widgets.buttons.TwoStateButton import TwoStateButton


class TopBarButtons(QtWidgets.QFrame):

    def __init__(self, parent, ui):
        QtWidgets.QFrame.__init__(self, parent=parent)
        layout = QtWidgets.QHBoxLayout()
        self.show()

        # Left side
        self.play_button = TwoStateIconButton(ui_key='play_button', parent=self,
                                              pixmap0=qt_prefs.play_pixmap,
                                              pixmap1=qt_prefs.pause_pixmap,
                                              size=36,
                                              action='play_animations',
                                              ).to_layout(layout)

        self.edit_mode_button = TwoStateButton(ui_key='edit_mode_label', parent=self,
                                               text0='Free drawing',
                                               text1='Visualisation',
                                               action='switch_edit_mode').to_layout(layout)
        layout.addStretch(0)

        # Center side
        self.view_mode_button = TwoStateButton(ui_key='view_mode_label', parent=self,
                                               text0='Show all layers',
                                               text1='Show only syntactic layer',
                                               pixmap0=qt_prefs.eye_pixmap,
                                               action='switch_view_mode').to_layout(layout)

        layout.addStretch(0)

        view_label = QtWidgets.QLabel("Visualisation:")
        layout.addWidget(view_label)

        default_vis = ctrl.settings.get('visualization', level=g.PREFS)
        self.vis_buttons = QtWidgets.QButtonGroup(parent=self)
        for vkey, vis in VISUALIZATIONS.items():
            shortcut = vis.shortcut
            if shortcut:
                vis_button = VisButton(ui_key=f'vis_button_{shortcut}', parent=self, text=shortcut,
                                       size=(16, 24), subtype=vkey, shortcut=shortcut,
                                       tooltip=vis.name).to_layout(layout)
                self.vis_buttons.addButton(vis_button)
                vis_button.setChecked(vkey == default_vis)
        ui.connect_element_to_action(self.vis_buttons, 'set_visualization')
        layout.addStretch(0)

        # Right side

        self.camera = TopRowButton(ui_key='print_button', parent=self, pixmap=qt_prefs.camera_icon,
                                   size=(24, 24), action='print_pdf').to_layout(layout)

        undo = TopRowButton(ui_key='undo_button', parent=self, pixmap=qt_prefs.undo_icon,
                            action='undo').to_layout(layout)

        redo = TopRowButton(ui_key='redo_button', parent=self, pixmap=qt_prefs.redo_icon,
                            action='redo').to_layout(layout)

        pan_mode = TopRowButton(ui_key='pan_mode', parent=self, size=(24, 24),
                                pixmap=qt_prefs.pan_icon,
                                action='toggle_pan_mode').to_layout(layout)
        pan_mode.setCheckable(True)

        select_mode = TopRowButton(ui_key='select_mode', parent=self, pixmap=qt_prefs.cursor_icon,
                                   size=(24, 24), action='toggle_select_mode').to_layout(layout)
        select_mode.setCheckable(True)

        fit_to_screen = TopRowButton(ui_key='fit_to_screen', parent=self, size=(24, 24),
                                     pixmap=qt_prefs.center_focus_icon, action='zoom_to_fit',
                                     ).to_layout(layout)
        # draw_method=drawn_icons.fit_to_screen)

        full_screen = TopRowButton(ui_key='full_screen', parent=self, size=(24, 24),
                                   pixmap=qt_prefs.full_icon, action='fullscreen_mode',
                                   ).to_layout(layout)
        # draw_method=drawn_icons.fit_to_screen)

        layout.setContentsMargins(2, 0, 2, 0)
        self.setLayout(layout)
        self.setMinimumHeight(36)
        self.update_position()

    def sizeHint(self):
        return QtCore.QSize(self.parentWidget().width()-4, 28)

    def update_position(self):
        """ Make sure that float buttons are on graph view's top right corner
        :return:
        """
        self.resize(self.sizeHint())
        self.move(4, 2)
        #self.show()

    def left_edge_of_right_buttons(self):
        return self.camera.x()
