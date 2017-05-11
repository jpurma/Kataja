# coding=utf-8
from PyQt5 import QtWidgets, QtCore, QtGui

from kataja.singletons import ctrl, qt_prefs, prefs
from kataja.ui_widgets.OverlayButton import TopRowButton, VisButton
from kataja.ui_widgets.ModeLabel import ModeLabel
from kataja.ui_widgets.ModalIconButton import ModalIconButton
from kataja.visualizations.available import VISUALIZATIONS


class TopBarButtons(QtWidgets.QFrame):

    def __init__(self, parent, ui):
        QtWidgets.QFrame.__init__(self, parent=parent)
        layout = QtWidgets.QHBoxLayout()
        self.show()

        # Left side
        self.play_button = ModalIconButton('play_button', parent=self,
                                           pixmap0=qt_prefs.play_pixmap,
                                           pixmap1=qt_prefs.pause_pixmap,
                                           size=(36, 36))

        ui.add_button(self.play_button, action='play_or_pause')
        layout.addWidget(self.play_button)

        self.edit_mode_button = ModeLabel(['Free drawing', 'Visualisation'],
                                          ui_key='edit_mode_label',
                                          parent=self)
        layout.addWidget(self.edit_mode_button)
        ui.add_ui(self.edit_mode_button)
        ui.connect_element_to_action(self.edit_mode_button, 'switch_edit_mode')

        layout.addStretch(0)

        # Center side

        self.view_mode_button = ModeLabel(['All objects', 'Syntactic only'],
                                          ui_key='view_mode_label',
                                          parent=self, icon=qt_prefs.eye_icon)
        layout.addWidget(self.view_mode_button)
        ui.add_ui(self.view_mode_button)
        ui.connect_element_to_action(self.view_mode_button, 'switch_view_mode')

        layout.addStretch(0)

        view_label = QtWidgets.QLabel("Visualisation:")
        layout.addWidget(view_label)

        self.vis_buttons = QtWidgets.QButtonGroup(parent=self)
        for vkey, vis in VISUALIZATIONS.items():
            shortcut = vis.shortcut
            if shortcut:
                vis_button = VisButton(f'vis_button_{shortcut}', parent=self, text=shortcut,
                                       size=(16, 24), subtype=vkey, shortcut=shortcut,
                                       tooltip=vis.name)
                self.vis_buttons.addButton(vis_button)
                layout.addWidget(vis_button)
        ui.connect_element_to_action(self.vis_buttons, 'set_visualization')
        layout.addStretch(0)

        # Right side

        self.camera = TopRowButton('print_button', parent=self, pixmap=qt_prefs.camera_icon,
                                   size=(24, 24))
        ui.add_button(self.camera, action='print_pdf')
        layout.addWidget(self.camera)

        undo = TopRowButton('undo_button', parent=self, pixmap=qt_prefs.undo_icon)
        ui.add_button(undo, action='undo')
        layout.addWidget(undo)

        redo = TopRowButton('redo_button', parent=self, pixmap=qt_prefs.redo_icon)
        ui.add_button(redo, action='redo')
        layout.addWidget(redo)

        pan_mode = TopRowButton('pan_mode', parent=self, tooltip='Move mode', size=(24, 24),
                                pixmap=qt_prefs.pan_icon)  # draw_method=drawn_icons.pan_around
        ui.add_button(pan_mode, action='toggle_pan_mode')
        pan_mode.setCheckable(True)
        layout.addWidget(pan_mode)

        select_mode = TopRowButton('select_mode', parent=self, pixmap=qt_prefs.cursor_icon,
                                   size=(24, 24))  # draw_method=drawn_icons.select_mode
        select_mode.setCheckable(True)
        ui.add_button(select_mode, action='toggle_select_mode')
        layout.addWidget(select_mode)

        fit_to_screen = TopRowButton('fit_to_screen', parent=self, size=(24, 24),
                                     pixmap=qt_prefs.center_focus_icon)
        # draw_method=drawn_icons.fit_to_screen)
        ui.add_button(fit_to_screen, action='zoom_to_fit')
        layout.addWidget(fit_to_screen)

        full_screen = TopRowButton('full_screen', parent=self, size=(24, 24),
                                    pixmap=qt_prefs.full_icon)
        # draw_method=drawn_icons.fit_to_screen)
        ui.add_button(full_screen, action='fullscreen_mode')
        layout.addWidget(full_screen)


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

