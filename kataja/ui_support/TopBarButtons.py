# coding=utf-8
from PyQt5 import QtWidgets
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_items.OverlayButton import TopRowButton


class TopBarButtons(QtWidgets.QFrame):

    def __init__(self, parent, ui):
        QtWidgets.QFrame.__init__(self, parent=parent)
        layout = QtWidgets.QHBoxLayout()
        self.show()
        self._float_buttons = []
        view = ctrl.graph_view

        camera = TopRowButton('print_button', parent=self, tooltip='Print to file',
                              pixmap=qt_prefs.camera_icon, size=(24, 24))

        ui.add_button(camera, action='print_pdf')
        self._float_buttons.append(camera)
        layout.addWidget(camera)

        undo = TopRowButton('undo_button', parent=self, tooltip='Undo last action',
                            pixmap=qt_prefs.undo_icon)

        ui.add_button(undo, action='undo')
        self._float_buttons.append(undo)
        layout.addWidget(undo)

        redo = TopRowButton('redo_button', parent=self, tooltip='Redo action',
                            pixmap=qt_prefs.redo_icon)

        ui.add_button(redo, action='redo')
        self._float_buttons.append(redo)
        layout.addWidget(redo)

        pan_around = TopRowButton('pan_around', parent=self, tooltip='Move mode', size=(24, 24),
                                  pixmap=qt_prefs.pan_icon)  # draw_method=drawn_icons.pan_around

        ui.add_button(pan_around, action='toggle_pan_mode')
        pan_around.setCheckable(True)
        layout.addWidget(pan_around)
        self._float_buttons.append(pan_around)

        select_mode = TopRowButton('select_mode', parent=self, tooltip='Move mode',
                                   pixmap=qt_prefs.select_all_icon,
                                   size=(24, 24))  # draw_method=drawn_icons.select_mode
        select_mode.setCheckable(True)
        ui.add_button(select_mode, action='toggle_select_mode')
        layout.addWidget(select_mode)

        self._float_buttons.append(select_mode)

        bones_mode = TopRowButton('bones_mode', parent=self,
                                  tooltip='Show only syntactic objects',
                                  pixmap=qt_prefs.eye_icon,
                                  size=(24, 24))
        bones_mode.setCheckable(True)
        bones_mode.setChecked(ui.qt_actions['toggle_bones_mode'].check_state())
        ui.add_button(bones_mode, action='toggle_bones_mode')
        layout.addWidget(bones_mode)
        self._float_buttons.append(bones_mode)

        fit_to_screen = TopRowButton('fit_to_screen', parent=self,
                                     tooltip='Fit to screen', size=(24, 24),
                                     pixmap=qt_prefs.full_icon)
        # draw_method=drawn_icons.fit_to_screen)
        ui.add_button(fit_to_screen, action='zoom_to_fit')
        layout.addWidget(fit_to_screen)
        self._float_buttons.append(fit_to_screen)



        layout.setContentsMargins(2, 0, 2, 0)
        self.setLayout(layout)
        self.setMinimumHeight(28)
        self.setMinimumWidth(len(self._float_buttons) * 28 + 4)
        self.update_position()


    def update_position(self):
        """ Make sure that float buttons are on graph view's top right corner
        :return:
        """
        right_x = self.parentWidget().width()
        w = len(self._float_buttons) * 28 + 4
        self.move(right_x - w - 4, 2)
        self.show()
