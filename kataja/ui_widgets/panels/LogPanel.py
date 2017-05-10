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
        self.line_edit = QtWidgets.QLineEdit('>>> ', parent=titlewidget)
        self.line_edit.returnPressed.connect(self.return_pressed)
        self.line_edit.setMinimumWidth(250)
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
        self.inner.setAutoFillBackground(True)
        self.inner.sizeHint = self.sizeHint
        self.inner.setFocusPolicy(QtCore.Qt.NoFocus)
        self.resize_grip = QtWidgets.QSizeGrip(self)
        self.resize_grip.hide()
        self.setAllowedAreas(QtCore.Qt.TopDockWidgetArea | QtCore.Qt.BottomDockWidgetArea)
        self.watchlist = ['ui_font_changed']
        self.incomplete_command = []

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
        self.ii = code.InteractiveInterpreter(locals={'ctrl': ctrl, 'g': g})
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

    def return_pressed(self):
        text = self.line_edit.text()
        print(text)
        line = text.lstrip('>. ')
        incomplete = False
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
            self.line_edit.setText('... ')
        else:
            self.incomplete_command = []
            self.line_edit.setText('>>> ')


    def closeEvent(self, event):
        self.watcher_thread.stop()

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
