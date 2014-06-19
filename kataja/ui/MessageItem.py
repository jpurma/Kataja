# coding=utf-8
# #######################################################
from PyQt5 import QtCore, QtWidgets

from kataja.Controller import ctrl, prefs


class MessageItem(QtWidgets.QGraphicsTextItem):
    """ Floating messages at bottom of the screen """

    def __init__(self, msg, log_panel, ui_manager):
        QtWidgets.QGraphicsTextItem.__init__(self, msg)
        self._messages = [msg]
        self._msg_string = msg
        # self.setFont(qt_prefs.menu_font)
        self.setPlainText('\n' + self._msg_string)
        self.setDefaultTextColor(ctrl.cm().ui())
        self.adjustSize()
        self.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)
        self._widget = log_panel
        self.ui_manager = ui_manager
        if prefs.console_visible:
            self.show()
            self.display_messages()
        else:
            self.hide()

    def update_position(self):
        """


        """
        self.setPos(8, self.ui_manager.height() - self.boundingRect().height() - 12)
        self.setTextWidth(self.ui_manager.width() - 20)

    def update_color(self):
        """


        """
        self.setDefaultTextColor(ctrl.cm().ui())
        self.display_messages()

    def display_messages(self):
        """


        :return:
        """
        if not prefs.console_visible:
            return
        if self.ui_manager:
            self.update_position()
        self._msg_string = '\n'.join(self._messages[-4:])
        self.setPlainText(self._msg_string)
        if self.y() + self.boundingRect().height() + 12 > self.ui_manager.height():
            self.setPos(8, self.ui_manager.height() - self.boundingRect().height() - 12)

    def add_feedback_from_command(self, cmd):
        """

        :param cmd:
        """
        self._messages[-1] = '>>>' + cmd
        self.display_messages()

    def add(self, msg):
        """

        :param msg:
        """
        self._widget.append(msg)
        self._messages.append(msg)
        self.display_messages()

    def show_next_query(self):
        """


        """
        self._messages.append('>>>_')
        self.display_messages()
