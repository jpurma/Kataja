import logging
import queue
from html import escape

import sys
from PyQt5 import QtGui, QtCore

MAX_LOG_SIZE = 20000


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


def capture_stdout(logger, outputter, ctrl):
    logger.write_queue = queue.Queue()
    ctrl.original_stdout = sys.stdout
    sys.stdout = WriteStream(logger.write_queue)
    logger.watcher_thread = QtCore.QThread()
    logger.my_receiver = MyReceiver(logger.write_queue)
    logger.my_receiver.mysignal.connect(outputter)
    logger.my_receiver.moveToThread(logger.watcher_thread)
    logger.watcher_thread.started.connect(logger.my_receiver.run)
    logger.watcher_thread.start()


def release_stdout(logger, ctrl):
    logger.watcher_thread.started.disconnect(logger.my_receiver.run)
    sys.stdout = ctrl.original_stdout


class LogWidgetPusher(logging.Handler):
    """ This receives all logging messages and emits them to available widget (QTextBrowser).
    Because this is in such central position, the handler also takes responsibility for
    storing internally all log messages, even those that are filtered due priority.

    In addition, LogWidgetPusher also keeps a special storage for kataja commands that have
     been run, as a list of strings.
    """

    def __init__(self, level=logging.DEBUG, root='kataja'):
        super().__init__(level=level)

        def store_everything(record):
            if not str(record.msg).strip():
                return False
            self.everything.append(record)
            if len(self.everything) > MAX_LOG_SIZE:
                self.everything = self.everything[1000:]
            return True

        self.widget = None  # handler is set before any widgets are available
        self.backlog = []
        self.everything = []
        self.command_backlog = []
        self.command_backlog_position = 0

        self.addFilter(store_everything)
        self.root = root
        # Direct stdout here

    def set_widget(self, widget):
        """ When widget is set while there are messages in backlog, push them all to widget
        :param widget: QTextBrowser, presumably. Needs to have 'append' defined
        :return:
        """
        self.widget = widget
        if widget:
            for record in self.backlog:
                self.handle(record)
            self.backlog = []

    def add_to_command_backlog(self, line):
        self.command_backlog.append(line)
        self.command_backlog_position = len(self.command_backlog) - 1

    def get_previous_command(self):
        self.command_backlog_position -= 1
        if self.command_backlog_position < 0:
            self.command_backlog_position = 0
        if self.command_backlog:
            return self.command_backlog[self.command_backlog_position]
        return ''

    def get_next_command(self):
        if self.command_backlog_position < len(self.command_backlog) - 1:
            self.command_backlog_position += 1
            return self.command_backlog[self.command_backlog_position]
        return ''

    def emit(self, record):
        """ This is handler's required emit implementation. Records it receives are already
        filtered to be at least minimal logging level.
        :param record:
        :return:
        """
        if self.widget is None:
            self.backlog.append(record)
        else:
            msg = record.getMessage()
            if record.levelno == logging.ERROR:
                tag = '<font color="#dc322f">'
                end_tag = '</font>'
            elif msg.startswith('>>>'):
                tag = '<font color="#2aa198">'
                end_tag = '</font>'
            else:
                tag = ''
                end_tag = ''
            if record.name != self.root:
                parts = record.name.split('.', 1)
                if len(parts) == 2:
                    modname = parts[1] + ': '
                else:
                    modname = record.name + ': '
            else:
                modname = ''
            if record.levelno == logging.DEBUG:
                levelname = modname
            else:
                levelname = f'<b>{modname}{record.levelname}:</b> '

            self.widget.append(tag + levelname + escape(msg) + end_tag)
            self.widget.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
