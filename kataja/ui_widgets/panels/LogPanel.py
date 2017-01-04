from PyQt5 import QtWidgets, QtCore

import kataja.globals as g
from kataja.singletons import qt_prefs
from kataja.ui_widgets.Panel import Panel
from kataja.singletons import ctrl, log


__author__ = 'purma'


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
        inner = QtWidgets.QTextBrowser()
        layout = QtWidgets.QVBoxLayout()
        inner.setMinimumHeight(48)
        inner.preferred_size = QtCore.QSize(940, 64)
        f = qt_prefs.get_font(g.CONSOLE_FONT)
        inner.setStyleSheet('font-family: "%s"; font-size: %spx;' % (f.family(), f.pointSize()))
        inner.setAutoFillBackground(True)
        inner.sizeHint = self.sizeHint
        inner.setFocusPolicy(QtCore.Qt.NoFocus)
        self.resize_grip = QtWidgets.QSizeGrip(self)
        self.resize_grip.hide()
        self.setAllowedAreas(QtCore.Qt.TopDockWidgetArea | QtCore.Qt.BottomDockWidgetArea)
        self.watchlist = ['ui_font_changed']

        layout.addWidget(self.resize_grip, 0, QtCore.Qt.AlignRight)
        inner.setLayout(layout)

        self.preferred_size = inner.preferred_size
        self.setWidget(inner)
        self.finish_init()
        log.log_handler.set_widget(inner)

    def sizeHint(self):
        if self.isFloating():
            return QtCore.QSize(480, 640)
        else:
            return self.preferred_size

    def report_top_level(self, floating):
        super().report_top_level(floating)
        if floating:
            self.resize(QtCore.QSize(480, 480))

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
