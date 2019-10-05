# coding=utf-8
from PyQt5 import QtWidgets, QtCore

from kataja.singletons import ctrl, qt_prefs, prefs
from kataja.ui_widgets.KatajaButtonGroup import KatajaButtonGroup
from kataja.ui_widgets.buttons.OverlayButton import TopRowButton, VisButton
from kataja.ui_widgets.buttons.TwoStateIconButton import TwoStateIconButton
from kataja.visualizations.available import VISUALIZATIONS


class TopBarButtons(QtWidgets.QFrame):
    def __init__(self, parent, ui):
        # noinspection PyArgumentList
        QtWidgets.QFrame.__init__(self, parent=parent)
        layout = QtWidgets.QHBoxLayout()
        self.show()

        # Left side
        self.play_button = TwoStateIconButton(ui_key='play_button',
                                              parent=self,
                                              pixmap0=qt_prefs.pause_pixmap,
                                              pixmap1=qt_prefs.play_pixmap,
                                              size=36,
                                              action='play_animations').to_layout(layout)

        self.record_button = TwoStateIconButton(ui_key='record_button',
                                                parent=self,
                                                pixmap0=qt_prefs.record_pixmap,
                                                pixmap1=qt_prefs.stop_pixmap,
                                                color0=ctrl.cm.red,
                                                color1=ctrl.cm.red,
                                                size=24,
                                                action='toggle_recording').to_layout(layout)

        layout.addStretch(0)

        view_label = QtWidgets.QLabel("Visualisation:")
        # noinspection PyArgumentList
        layout.addWidget(view_label)

        default_vis = prefs.visualization
        self.vis_buttons = KatajaButtonGroup(parent=self)
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
                                pixmap=qt_prefs.pan_icon, action='toggle_pan_mode').to_layout(
            layout)
        pan_mode.setCheckable(True)

        select_mode = TopRowButton(ui_key='select_mode', parent=self, pixmap=qt_prefs.cursor_icon,
                                   size=(24, 24), action='toggle_select_mode').to_layout(layout)
        select_mode.setCheckable(True)

        full_screen = TopRowButton(ui_key='full_screen', parent=self, size=(24, 24),
                                   pixmap=qt_prefs.full_icon, action='fullscreen_mode',
                                   ).to_layout(layout)

        automatic_zoom = TopRowButton(ui_key='auto_zoom', parent=self, size=(24, 24),
                                      pixmap=qt_prefs.autozoom_icon,
                                      action='auto_zoom', ).to_layout(layout)

        fit_to_screen = TopRowButton(ui_key='fit_to_screen', parent=self, size=(24, 24),
                                     pixmap=qt_prefs.center_focus_icon,
                                     action='zoom_to_fit', ).to_layout(layout)

        layout.setContentsMargins(2, 0, 2, 0)
        self.setLayout(layout)
        self.setMinimumHeight(36)
        self.update_position()

    def sizeHint(self):
        return QtCore.QSize(self.parentWidget().width() - 4, 28)

    def update_position(self):
        """ Make sure that float buttons are on graph view's top right corner
        :return:
        """
        self.resize(self.sizeHint())
        self.move(4, 2)
        # self.show()

    def left_edge_of_right_buttons(self):
        return self.camera.x()
