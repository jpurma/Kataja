
import logging
from PyQt5 import QtGui


class LogWidgetPusher(logging.Handler):

    def __init__(self, level=logging.DEBUG):
        super().__init__(level=level)
        self.widget = None  # handler is set before any widgets are available
        self.backlog = []
        self._old_color = None
        self.error_color = QtGui.QColor(211, 0, 0)

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
                self._old_color = self.widget.textColor()
                self.widget.setTextColor(self.error_color)
                self.widget.append('%s: %s' % (record.levelname, record.getMessage()))
                self.widget.setTextColor(self._old_color)
            else:
                self.widget.append('%s: %s' % (record.levelname, record.getMessage()))
            self.widget.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
