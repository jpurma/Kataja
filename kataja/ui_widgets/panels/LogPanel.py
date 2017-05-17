import queue
import sys
import code

from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.singletons import log, ctrl, qt_prefs
from kataja.ui_widgets.Panel import Panel
from kataja.ui_support.panel_utils import text_button, selector, mini_button, mini_selector


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
        log_levels = mini_selector(ctrl.ui, titlewidget, tlayout, data=levels,
                                   action='set_log_level')
        log_levels.setMinimumWidth(72)
        clear_log = mini_button(ctrl.ui, titlewidget, tlayout, text='clear', action='clear_log')

        self.inner = QtWidgets.QTextBrowser()
        layout = QtWidgets.QVBoxLayout()
        self.inner.setMinimumHeight(48)
        self.inner.preferred_size = QtCore.QSize(940, 64)
        f = qt_prefs.get_font(g.CONSOLE_FONT)
        ss = f'font-family: "{f.family()}"; font-size: {f.pointSize()}px;'
        self.inner.setStyleSheet(ss)
        self.command_prompt.setStyleSheet(ss)
        self.prompt_label.setStyleSheet(ss)
        self.inner.setAutoFillBackground(True)
        self.inner.sizeHint = self.sizeHint
        self.inner.setFocusPolicy(QtCore.Qt.NoFocus)
        self.resize_grip = QtWidgets.QSizeGrip(self)
        self.resize_grip.hide()
        self.setAllowedAreas(QtCore.Qt.TopDockWidgetArea | QtCore.Qt.BottomDockWidgetArea)
        self.watchlist = ['ui_font_changed']

        layout.addWidget(self.resize_grip, 0, QtCore.Qt.AlignRight)
        self.inner.setLayout(layout)

        self.preferred_size = self.inner.preferred_size
        self.setWidget(self.inner)
        self.finish_init()
        log.log_handler.set_widget(self.inner)

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
            self.inner.append(text.rstrip())
            self.inner.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)

    def append_error(self, errortext):
        self.inner.append(errortext.rstrip())
        self.inner.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)

    def rebuild_log(self):
        min_level = ctrl.settings.get('log_level', level=g.PREFS)
        self.inner.clear()
        for handler in log.handlers:
            if hasattr(handler, 'everything'):
                for record in handler.everything:
                    if record.levelno >= min_level:
                        handler.emit(record)

    def clear_log(self):
        self.inner.clear()
        for handler in log.handlers:
            if hasattr(handler, 'everything'):
                handler.everything = []

    def watch_alerted(self, obj, signal, field_name, value):
        """ Receives alerts from signals that this object has chosen to listen. These signals
         are declared in 'self.watchlist'.

         This method will try to sort out the received signals and act accordingly.

        :param obj: the object causing the alarm
        :param signal: identifier for type of the alarm
        :param field_name: name of the field of the object causing the alarm
        :param value: value given to the field
        :return:
        """
        if signal == 'ui_font_changed':
            f = qt_prefs.get_font(g.CONSOLE_FONT)
            self.widget().setStyleSheet('font-family: "%s"; font-size: %spx;' % (f.family(),
                                                                                 f.pointSize()))
