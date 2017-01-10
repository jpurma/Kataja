from PyQt5 import QtWidgets, QtGui

from kataja.globals import UI_FONT
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_widgets.Panel import Panel

from kataja.ui_support.panel_utils import text_button

__author__ = 'purma'


class HelpPanel(Panel):
    """ Panel for showing help and instructions """
    default_text = """
    <h3>Welcome to Kataja!</h3>
    Try these:<br/>
    <b>1-9, 0</b> - different visualisations, press again for alternatives<br/>
    <b>b</b> - switch between ways to show nodes<br/>
    <b>l</b> - switch between label visibility<br/>
    <b>f</b> - switch between feature visibility<br/>
    <b>v</b> - switch between views provided by syntax/plugin<br/>
    <b>t</b> - switch between multidomination / traces<br/>
    """

    def __init__(self, name, default_position='bottom', parent=None, folded=False):
        """
        All of the panel constructors follow the same format so that the construction can be automated.
        :param name: Title of the panel and the key for accessing it
        :param default_position: 'bottom', 'right'...
        :param parent: self.main
        :param ui_manager: pass a dictionary where buttons from this panel will be added
        """
        Panel.__init__(self, name, default_position, parent, folded)
        inner = QtWidgets.QWidget()
        inner.setContentsMargins(4, 4, 4, 4)
        self.setContentsMargins(0, 0, 0, 0)
        layout = QtWidgets.QVBoxLayout()
        self.browser = QtWidgets.QTextBrowser()
        layout.setContentsMargins(0, 0, 0, 0)
        self.browser.setContentsMargins(0, 0, 0, 0)
        f = qt_prefs.get_font(UI_FONT)
        point_size = f.pointSize()
        if point_size < 14:
            point_size = 12
        self.browser.setStyleSheet('font-size: %spx;' % point_size)
        self.browser.setMinimumWidth(200)
        self.browser.setFrameStyle(QtWidgets.QFrame.NoFrame)
        p = self.browser.palette()
        p.setColor(QtGui.QPalette.Base, ctrl.cm.transparent)
        self.browser.setPalette(p)
        layout.addWidget(self.browser)
        inner.setLayout(layout)
        self.setWidget(inner)
        self.watchlist = ['ui_font_changed']
        self.set_text(HelpPanel.default_text)
        self.finish_init()
        ctrl.graph_view.activateWindow()
        ctrl.graph_view.setFocus()

    def set_text(self, text):
        self.browser.setHtml(text)

    def text(self):
        return self.browser.toHtml()

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
            f = qt_prefs.get_font(UI_FONT)
            point_size = f.pointSize()
            if point_size < 14:
                point_size = 12
            self.browser.setStyleSheet('font-size: %spx;' % point_size)

