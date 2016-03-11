# coding=utf-8

from PyQt5 import QtWidgets
from kataja.singletons import qt_prefs, ctrl


class ErrorDialog(QtWidgets.QDialog):
    """ Dialog to show an error in operation """

    def __init__(self, parent, retry=True):

        QtWidgets.QDialog.__init__(self, parent)
        self.setModal(True)
        self.message = 'Apologies, but there was a plugin that failed to register:'
        self.error_text = ''
        self.error_traceback_text = ''

        layout = QtWidgets.QVBoxLayout()
        hlayout = QtWidgets.QHBoxLayout()
        self.message_widget = QtWidgets.QWidget(self)
        self.traceback_widget = QtWidgets.QTextBrowser(self)
        self.traceback_widget.setMinimumWidth(300)
        self.setWindowTitle(self.message)
        hlayout.addWidget(self.message_widget)
        hlayout.addWidget(self.traceback_widget)
        mlayout = QtWidgets.QVBoxLayout()
        #self.message_header_label = QtWidgets.QLabel('', self.message_widget)
        self.message_error_label = QtWidgets.QLabel(self.error_text, self.message_widget)
        #mlayout.addWidget(self.message_header_label)
        mlayout.addWidget(self.message_error_label)
        self.message_widget.setLayout(mlayout)
        layout.addLayout(hlayout)
        hlayout = QtWidgets.QHBoxLayout()
        self.retry_button = None
        if retry:
            self.retry_button = QtWidgets.QPushButton(self)
            self.retry_button.setText('Try again, I fixed it')
            self.retry_button.clicked.connect(self.accept)
            hlayout.addWidget(self.retry_button)
        self.pass_button = QtWidgets.QPushButton(self)
        self.pass_button.setText('Disable plugin and continue')
        self.pass_button.setDefault(True)
        self.pass_button.clicked.connect(self.reject)
        hlayout.addWidget(self.pass_button)
        layout.addLayout(hlayout)
        self.setLayout(layout)

    def set_traceback(self, text):
        self.traceback_widget.setText(text)

#    def set_message(self, text):
#        self.message_header_label.setText(text)

    def set_error(self, text):
        self.message_error_label.setText(text)

