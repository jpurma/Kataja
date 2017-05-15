
import logging
import queue

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


def capture_stdout(logger, outputter):
    logger.write_queue = queue.Queue()
    sys.stdout = WriteStream(logger.write_queue)
    logger.watcher_thread = QtCore.QThread()
    logger.my_receiver = MyReceiver(logger.write_queue)
    logger.my_receiver.mysignal.connect(outputter)
    logger.my_receiver.moveToThread(logger.watcher_thread)
    logger.watcher_thread.started.connect(logger.my_receiver.run)
    logger.watcher_thread.start()


class LogWidgetPusher(logging.Handler):

    def __init__(self, level=logging.DEBUG, root='kataja'):
        super().__init__(level=level)

        def store_everything(record):
            if not record.msg.strip():
                return False
            self.everything.append(record)
            if len(self.everything) > MAX_LOG_SIZE:
                self.everything = self.everything[1000:]
            return True

        self.widget = None  # handler is set before any widgets are available
        self.backlog = []
        self.everything = []
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

    def emit(self, record):
        """ This is handler's required emit implementation. Records it receives are already
        filtered to be at least minimal logging level.
        :param record:
        :return:
        """
        if self.widget is None:
            self.backlog.append(record)
        else:
            if record.levelno == logging.ERROR:
                tag = '<font color="red">'
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

            self.widget.append(tag + levelname + record.getMessage() + end_tag)
            self.widget.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
