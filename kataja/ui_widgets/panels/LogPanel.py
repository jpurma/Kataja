import queue
import sys
import code

from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.singletons import log, ctrl, qt_prefs
from kataja.ui_widgets.Panel import Panel


class WriteStream:
    """ This splits stdout to print to both original stdout (sys.__stdout__) and to
    thread-protected queue, where Qt log window can safely pop it.
    """

    def __init__(self, queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)
        sys.__stdout__.write(text)

    def flush(self):
        pass

class MyReceiver(QtCore.QObject):
    mysignal = QtCore.pyqtSignal(str)

    def __init__(self, queue, *args, **kwargs):
        QtCore.QObject.__init__(self, *args, **kwargs)
        self.queue = queue

    @QtCore.pyqtSlot()
    def run(self):
        while True:
            text = self.queue.get()
            self.mysignal.emit(text)


class CommandPrompt(QtWidgets.QLineEdit):

    def __init__(self, parent, prompt: QtWidgets.QLabel):
        QtWidgets.QLineEdit.__init__(self, '', parent=parent)
        self.returnPressed.connect(self.return_pressed)
        #self.cursorPositionChanged.connect(self.cursor_moved)
        self.setMinimumWidth(250)
        self.incomplete_command = []
        self.backlog = []
        self.backlog_position = 0
        self.ii = None
        self.prompt = prompt
        self.update_actions()

    def update_actions(self):
        commands = ctrl.ui.get_actions_as_python_commands()
        commands.update({'ctrl': ctrl, 'g': g})
        self.ii = code.InteractiveInterpreter(locals=commands)

    def return_pressed(self):
        text = self.text()
        print('>>> ' + text)
        line = text.lstrip('>. ')
        incomplete = False
        self.backlog.append(line)
        self.backlog_position = len(self.backlog) - 1
        if self.incomplete_command:
            self.incomplete_command.append(line)
            source = '\n'.join(self.incomplete_command)
        else:
            source = line
        try:
            incomplete = self.ii.runsource(source)
        except:
            log.error(sys.exc_info())
            print(sys.exc_info())
        if incomplete:
            if not self.incomplete_command:
                self.incomplete_command = [line]
            else:
                self.incomplete_command.append(source)
            self.prompt.setText(' ...')
        else:
            self.incomplete_command = []
            self.prompt.setText(' >>>')

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
            self.backlog_position -= 1
            if self.backlog_position < 0:
                self.backlog_position = 0
            if self.backlog:
                text = self.backlog[self.backlog_position]
                self.setText(text)
                self.setCursorPosition(len(text))
        elif event.key() == QtCore.Qt.Key_Down:
            if self.backlog_position < len(self.backlog) - 1:
                self.backlog_position += 1
                text = self.backlog[self.backlog_position]
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
        self.line_edit = CommandPrompt(titlewidget, self.prompt_label)
        self.prompt_label.setBuddy(self.line_edit)
        ctrl.ui.command_prompt = self.line_edit
        tlayout.addWidget(self.line_edit)
        label = QtWidgets.QLabel('show stdout:', parent=titlewidget)
        self.stdout = QtWidgets.QCheckBox(parent=titlewidget)
        label.setBuddy(self.stdout)
        ctrl.ui.connect_element_to_action(self.stdout, 'show_stdout_in_log')
        tlayout.addStretch(1)
        tlayout.addWidget(label)
        tlayout.addWidget(self.stdout)
        tlayout.addStretch(1)

        self.inner = QtWidgets.QTextBrowser()
        layout = QtWidgets.QVBoxLayout()
        self.inner.setMinimumHeight(48)
        self.inner.preferred_size = QtCore.QSize(940, 64)
        f = qt_prefs.get_font(g.CONSOLE_FONT)
        ss = f'font-family: "{f.family()}"; font-size: {f.pointSize()}px;'
        self.inner.setStyleSheet(ss)
        self.line_edit.setStyleSheet(ss)
        self.prompt_label.setStyleSheet(ss)
        self.inner.setAutoFillBackground(True)
        self.inner.sizeHint = self.sizeHint
        self.inner.setFocusPolicy(QtCore.Qt.NoFocus)
        self.resize_grip = QtWidgets.QSizeGrip(self)
        self.resize_grip.hide()
        self.setAllowedAreas(QtCore.Qt.TopDockWidgetArea | QtCore.Qt.BottomDockWidgetArea)
        self.watchlist = ['ui_font_changed']

        # Direct stdout here
        self.write_queue = queue.Queue()
        sys.stdout = WriteStream(self.write_queue)
        self.watcher_thread = QtCore.QThread()
        self.my_receiver = MyReceiver(self.write_queue)
        self.my_receiver.mysignal.connect(self.append_text)
        self.my_receiver.moveToThread(self.watcher_thread)
        self.watcher_thread.started.connect(self.my_receiver.run)
        self.watcher_thread.start()

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
