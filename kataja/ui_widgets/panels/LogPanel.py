# import code
# import sys

from PyQt6 import QtWidgets, QtCore, QtGui

import kataja.globals as g
# from kataja.UIItem import UIWidget
# from kataja.singletons import ctrl
from kataja.singletons import log, qt_prefs, prefs
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.SelectionBox import SelectionBox
from kataja.ui_widgets.buttons.PanelButton import PanelButton


#
# class CommandPrompt(QtWidgets.QLineEdit):
#
#     def __init__(self, parent):
#         QtWidgets.QLineEdit.__init__(self, '', parent=parent)
#         self.setMinimumWidth(250)
#         self.show()
#
#     def focusInEvent(self, event):
#         ctrl.ui_focus = self
#         return super().focusInEvent(event)
#
#     def focusOutEvent(self, event):
#         if ctrl.ui_focus is self:
#             ctrl.ui_focus = None
#         return super().focusOutEvent(event)
#
#     def keyPressEvent(self, event: QtGui.QKeyEvent):
#         if event.key() == QtCore.Qt.Key_Up:
#             text = log.log_handler.get_previous_command()
#             self.setText(text)
#             self.setCursorPosition(len(text))
#         elif event.key() == QtCore.Qt.Key_Down:
#             text = log.log_handler.get_next_command()
#             self.setText(text)
#             self.setCursorPosition(len(text))
#         else:
#             return super().keyPressEvent(event)
#
#
# class CommandEdit(UIWidget, QtWidgets.QWidget):
#
#     def __init__(self, parent):
#         tip = """Run Kataja action or other python command.
# ↑/↓ browse previous commands."""
#         UIWidget.__init__(self, tooltip=tip)
#         QtWidgets.QWidget.__init__(self, parent=parent)
#         print('command edit got parent ', parent)
#         self.prompt_hint = QtWidgets.QLabel('>>>', parent=self)
#         self.command_prompt = CommandPrompt(self)
#         self.command_prompt.returnPressed.connect(self.return_pressed)
#         self.prompt_hint.setBuddy(self.command_prompt)
#         layout = QtWidgets.QHBoxLayout()
#         layout.setContentsMargins(0, 0, 0, 0)
#         layout.addWidget(self.prompt_hint)
#         layout.addWidget(self.command_prompt)
#         self.setMaximumHeight(20)
#         self.setLayout(layout)
#         self.incomplete_command = []
#         self.i_i = None
#         self.update_actions()
#         self.show()
#
#     def update_actions(self):
#         d = {'ctrl': ctrl, 'g': g}
#         for key, item in ctrl.ui.actions.items():
#             d[key] = item.manual_run
#         self.i_i = code.InteractiveInterpreter(locals=d)
#
#     def return_pressed(self):
#         text = self.command_prompt.text()
#         log.info('>>> ' + text)
#         line = text.lstrip('>. ')
#         incomplete = False
#         log.log_handler.add_to_command_backlog(line)
#         if self.incomplete_command:
#             self.incomplete_command.append(line)
#             source = '\n'.join(self.incomplete_command)
#         else:
#             source = line
#         try:
#             incomplete = self.i_i.runsource(source)
#         except:
#             log.error(sys.exc_info())
#         if incomplete:
#             if not self.incomplete_command:
#                 self.incomplete_command = [line]
#             else:
#                 self.incomplete_command.append(source)
#             self.prompt_hint.setText('...')
#         else:
#             self.incomplete_command = []
#             self.prompt_hint.setText('>>>')
#         self.command_prompt.setText('')
#


class LogPanel(Panel):
    """ Dump window """

    def __init__(self, name, default_position='bottom', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        """
        Panel.__init__(self, name, default_position, parent, folded)
        title_widget = self.titleBarWidget()
        tlayout = title_widget.layout()
        levels = [(50, 'CRITICAL'), (40, 'ERROR'), (30, 'WARNING'), (20, 'INFO'), (10, 'DEBUG')]
        tlayout.addStretch(2)

        # self.command_edit = CommandEdit(title_widget)
        # tlayout.addWidget(self.command_edit)
        # tlayout.addStretch(1)
        # self.command_edit.setStyleSheet(ss)

        log_levels = SelectionBox(parent=title_widget, data=levels,
                                  action='set_log_level', mini=True).to_layout(tlayout, with_label='log level:')
        log_levels.setMinimumWidth(72)
        clear_log = PanelButton(parent=title_widget, action='clear_log', pixmap=qt_prefs.trash_icon).to_layout(tlayout)
        clear_log.setFlat(False)
        clear_log.setMaximumHeight(20)
        widget = self.widget()
        self.preferred_floating_size = QtCore.QSize(480, 480)
        self.log_browser = QtWidgets.QTextBrowser(parent=widget)
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.addWidget(self.log_browser)
        self.preferred_size = QtCore.QSize(940, 160)
        f = qt_prefs.get_font(g.CONSOLE_FONT)
        ss = f'font-family: "{f.family()}"; font-size: {f.pointSize()}px;'
        self.log_browser.setStyleSheet(ss)
        self.log_browser.setAutoFillBackground(True)
        self.log_browser.setFocusPolicy(QtCore.Qt.FocusPolicy.NoFocus)
        self.resize_grip = QtWidgets.QSizeGrip(widget)
        self.resize_grip.hide()
        self.setAllowedAreas(QtCore.Qt.DockWidgetArea.TopDockWidgetArea | QtCore.Qt.DockWidgetArea.BottomDockWidgetArea)
        self.vlayout.addWidget(self.resize_grip, 0, QtCore.Qt.AlignmentFlag.AlignRight)
        self.finish_init()
        log.log_handler.set_widget(self.log_browser)

    def closeEvent(self, event):
        if getattr(log, 'watcher_thread', None):
            log.watcher_thread.quit()

    def append_text(self, text):
        if text.strip():
            self.log_browser.append(text.rstrip())
            self.log_browser.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)

    def append_error(self, errortext):
        self.log_browser.append(errortext.rstrip())
        self.log_browser.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)

    def rebuild_log(self):
        min_level = prefs.log_level
        self.log_browser.clear()
        for handler in log.handlers:
            if hasattr(handler, 'everything'):
                for record in handler.everything:
                    if record.levelno >= min_level:
                        handler.emit(record)

    def clear_log(self):
        self.log_browser.clear()
        for handler in log.handlers:
            if hasattr(handler, 'everything'):
                handler.everything = []
