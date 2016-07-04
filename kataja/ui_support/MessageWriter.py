# coding=utf-8
# #######################################################

from PyQt5 import QtGui


class MessageWriter:
    """ Abstract message log, contents are reflected to Log panel if such is present. """

    def __init__(self):
        self._messages = []
        self.display_widget = None

    def attach_display_widget(self, display_widget):
        """ Re-attach messagewriter to display_widget. Empty the display widget and write
        all messages there.
        :param display_widget: QTextEdit instance
        :return:
        """
        self.display_widget = display_widget
        self.display_widget.setPlainText('\n'.join(self._messages))

    def add_feedback_from_command(self, cmd):
        """

        :param cmd:
        """
        self.add('>>>' + cmd)

    def add(self, msg):
        """

        :param msg:
        """
        if self.display_widget:
            self.display_widget.append(msg)
        self._messages.append(msg)

    def write(self, m):
        self.add(m.rstrip())

    def flush(self):
        pass

class ErrorWriter:
    """ Abstract message log, contents are reflected to Log panel if such is present. """

    def __init__(self):
        self._messages = []
        self.display_widget = None
        self.old_color = None
        self.color = QtGui.QColor(211, 0, 0)

    def attach_display_widget(self, display_widget):
        """ Re-attach messagewriter to display_widget. Empty the display widget and write
        all messages there.
        :param display_widget: QTextEdit instance
        :return:
        """
        self.display_widget = display_widget

    def write(self, m):
        msg = m.rstrip()
        if self.display_widget:
            self.old_color = self.display_widget.textColor()
            self.display_widget.setTextColor(self.color)
            self.display_widget.append(msg)
            self.display_widget.setTextColor(self.old_color)
        self._messages.append(msg)

    def flush(self):
        pass
