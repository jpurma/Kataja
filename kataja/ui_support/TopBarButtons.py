# coding=utf-8
from PyQt5 import QtWidgets, QtCore, QtGui

from kataja.singletons import ctrl, qt_prefs
from kataja.ui_items.OverlayButton import TopRowButton
from kataja.ui_items.ModeLabel import ModeLabel


class TopBarButtons(QtWidgets.QFrame):

    def __init__(self, parent, ui):
        QtWidgets.QFrame.__init__(self, parent=parent)
        layout = QtWidgets.QHBoxLayout()
        self.show()
        self._left_buttons = []
        self._right_buttons = []

        # Left side
        self._edit_mode_button = ModeLabel('Free drawing mode', ui_key='edit_mode_label',
                                           parent=self)
        layout.addWidget(self._edit_mode_button)
        ui.add_ui(self._edit_mode_button)
        self._left_buttons.append(self._edit_mode_button)
        ui.connect_element_to_action(self._edit_mode_button, 'switch_edit_mode')

        self._view_mode_button = ModeLabel('Show all objects', ui_key='view_mode_label',
                                           parent=self)
        layout.addWidget(self._view_mode_button)
        ui.add_ui(self._view_mode_button)
        self._left_buttons.append(self._view_mode_button)
        ui.connect_element_to_action(self._view_mode_button, 'switch_view_mode')

        layout.addStretch(0)
        # Right side

        camera = TopRowButton('print_button', parent=self, tooltip='Print to file',
                              pixmap=qt_prefs.camera_icon, size=(24, 24))

        ui.add_button(camera, action='print_pdf')
        self._right_buttons.append(camera)
        layout.addWidget(camera)

        undo = TopRowButton('undo_button', parent=self, tooltip='Undo last action',
                            pixmap=qt_prefs.undo_icon)

        ui.add_button(undo, action='undo')
        self._right_buttons.append(undo)
        layout.addWidget(undo)

        redo = TopRowButton('redo_button', parent=self, tooltip='Redo action',
                            pixmap=qt_prefs.redo_icon)

        ui.add_button(redo, action='redo')
        self._right_buttons.append(redo)
        layout.addWidget(redo)

        pan_around = TopRowButton('pan_around', parent=self, tooltip='Move mode', size=(24, 24),
                                  pixmap=qt_prefs.pan_icon)  # draw_method=drawn_icons.pan_around

        ui.add_button(pan_around, action='toggle_pan_mode')
        pan_around.setCheckable(True)
        layout.addWidget(pan_around)
        self._right_buttons.append(pan_around)

        select_mode = TopRowButton('select_mode', parent=self, tooltip='Move mode',
                                   pixmap=qt_prefs.select_all_icon,
                                   size=(24, 24))  # draw_method=drawn_icons.select_mode
        select_mode.setCheckable(True)
        ui.add_button(select_mode, action='toggle_select_mode')
        layout.addWidget(select_mode)

        self._right_buttons.append(select_mode)


        fit_to_screen = TopRowButton('fit_to_screen', parent=self,
                                     tooltip='Fit to screen', size=(24, 24),
                                     pixmap=qt_prefs.full_icon)
        # draw_method=drawn_icons.fit_to_screen)
        ui.add_button(fit_to_screen, action='zoom_to_fit')
        layout.addWidget(fit_to_screen)
        self._right_buttons.append(fit_to_screen)



        layout.setContentsMargins(2, 0, 2, 0)
        self.setLayout(layout)
        self.setMinimumHeight(28)
        min_width = 0
        for item in self._left_buttons + self._right_buttons:
            min_width += item.width()
            min_width += 4
        min_width += 10
        self.update_position()

    def sizeHint(self):
        return QtCore.QSize(self.parentWidget().width()-4, 28)

    def update_position(self):
        """ Make sure that float buttons are on graph view's top right corner
        :return:
        """
        self.resize(self.sizeHint())
        self.move(4, 2)
        self.show()
