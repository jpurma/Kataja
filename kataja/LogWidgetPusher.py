
import logging
from PyQt5 import QtGui







class LogWidgetPusher(logging.Handler):

    def __init__(self, level=logging.DEBUG, root='kataja'):
        super().__init__(level=level)
        self.widget = None  # handler is set before any widgets are available
        self.backlog = []
        self.root = root

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
                self.widget.append('<font color="red">ERROR:'+record.getMessage()+'</font>')
            elif record.name != self.root:
                parts = record.name.split('.', 1)
                if len(parts) == 2:
                    modname = parts[1]
                else:
                    modname = record.name
                self.widget.append('<b>%s:%s:</b> %s' %
                                   (modname, record.levelname, record.getMessage()))
            else:
                self.widget.append('<b>%s:</b> %s' % (record.levelname, record.getMessage()))
            self.widget.moveCursor(QtGui.QTextCursor.End, QtGui.QTextCursor.MoveAnchor)
