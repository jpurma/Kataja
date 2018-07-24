import code
import sys

from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.singletons import log, ctrl, qt_prefs
from kataja.ui_widgets.Panel import Panel
from kataja.ui_widgets.SelectionBox import SelectionBox
from kataja.ui_widgets.buttons.PanelButton import PanelButton


class CommandPrompt(QtWidgets.QLineEdit):

    def __init__(self, parent, prompt: QtWidgets.QLabel):
        QtWidgets.QLineEdit.__init__(self, '', parent=parent)
        self.returnPressed.connect(self.return_pressed)
        #self.cursorPositionChanged.connect(self.cursor_moved)
        self.setMinimumWidth(250)
        self.incomplete_command = []
        self.ii = None
        self.prompt = prompt
        self.update_actions()

    def update_actions(self):
        commands = ctrl.ui.get_actions_as_python_commands()
        commands.update({'ctrl': ctrl, 'g': g})
        self.ii = code.InteractiveInterpreter(locals=commands)

    def return_pressed(self):
        text = self.text()
        log.info('>>> ' + text)
        line = text.lstrip('>. ')
        incomplete = False
        log.log_handler.add_to_command_backlog(line)
        if self.incomplete_command:
            self.incomplete_command.append(line)
            source = '\n'.join(self.incomplete_command)
        else:
            source = line
        try:
            incomplete = self.ii.runsource(source)
        except:
            log.error(sys.exc_info())
        if incomplete:
            if not self.incomplete_command:
                self.incomplete_command = [line]
            else:
                self.incomplete_command.append(source)
            self.prompt.setText(' ...')
        else:
            self.incomplete_command = []
            self.prompt.setText(' >>>')
        self.setText('')

    def cursor_moved(self, old, new):
        if new < 3:
            self.setCursorPosition(3)

    def focusInEvent(self, event):
        ctrl.ui_focus = self
        return super().focusInEvent(event)

    def focusOutEvent(self, event):
        if ctrl.ui_focus is self:
            ctrl.ui_focus = None
        return super().focusOutEvent(event)

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_Up:
            text = log.log_handler.get_previous_command()
            self.setText(text)
            self.setCursorPosition(len(text))
        elif event.key() == QtCore.Qt.Key_Down:
            text = log.log_handler.get_next_command()
            self.setText(text)
            self.setCursorPosition(len(text))
        else:
            return super().keyPressEvent(event)


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
        titlewidget = self.titleBarWidget()
        tlayout = titlewidget.layout()
        label = QtWidgets.QLabel('Python command:', parent=titlewidget)
        tlayout.addWidget(label)
        self.prompt_label = QtWidgets.QLabel(' >>>', parent=titlewidget)
        tlayout.addWidget(self.prompt_label)
        self.command_prompt = CommandPrompt(titlewidget, self.prompt_label)
        self.prompt_label.setBuddy(self.command_prompt)
        ctrl.ui.command_prompt = self.command_prompt
        tlayout.addWidget(self.command_prompt)
        levels = [(50, 'CRITICAL'), (40, 'ERROR'), (30, 'WARNING'), (20, 'INFO'), (10, 'DEBUG')]
        tlayout.addStretch(2)

        label = QtWidgets.QLabel('log level:', parent=titlewidget)
        tlayout.addWidget(label)
        log_levels = SelectionBox(parent=titlewidget, data=levels,
                                  action='set_log_level', mini=True).to_layout(tlayout)
        log_levels.setMinimumWidth(72)
        clear_log = PanelButton(parent=titlewidget, text='clear',
                                action='clear_log').to_layout(tlayout)
        clear_log.setMaximumHeight(20)

        self.log_browser = QtWidgets.QTextBrowser()
        self.vlayout.setContentsMargins(0, 0, 0, 0)
        self.vlayout.addWidget(self.log_browser)
        self.log_browser.setMinimumHeight(48)
        self.log_browser.preferred_size = QtCore.QSize(940, 64)
        f = qt_prefs.get_font(g.CONSOLE_FONT)
        ss = f'font-family: "{f.family()}"; font-size: {f.pointSize()}px;'
        self.log_browser.setStyleSheet(ss)
        self.command_prompt.setStyleSheet(ss)
        self.prompt_label.setStyleSheet(ss)
        self.log_browser.setAutoFillBackground(True)
        self.log_browser.sizeHint = self.sizeHint
        self.log_browser.setFocusPolicy(QtCore.Qt.NoFocus)
        self.resize_grip = QtWidgets.QSizeGrip(self)
        self.resize_grip.hide()
        self.setAllowedAreas(QtCore.Qt.TopDockWidgetArea | QtCore.Qt.BottomDockWidgetArea)
        self.vlayout.addWidget(self.resize_grip, 0, QtCore.Qt.AlignRight)
        self.preferred_size = self.log_browser.preferred_size
        self.finish_init()
        log.log_handler.set_widget(self.log_browser)

    def sizeHint(self):
        if self.isFloating():
            return QtCore.QSize(480, 640)
        else:
            return self.preferred_size

    def report_top_level(self, floating):
        super().report_top_level(floating)
        if floating:
            self.resize(QtCore.QSize(480, 480))

    def closeEvent(self, event):
        self.watcher_thread.quit()

    def append_text(self, text):
        if text.strip():
            self.log_browser.append(text.rstrip())
            self.log_browser.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)

    def append_error(self, errortext):
        self.log_browser.append(errortext.rstrip())
        self.log_browser.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)

    def rebuild_log(self):
        min_level = ctrl.settings.get('log_level', level=g.PREFS)
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
