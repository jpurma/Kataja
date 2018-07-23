from PyQt5 import QtWidgets, QtGui, QtCore

from kataja.globals import UI_FONT
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_widgets.Panel import Panel

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
        inner = self.widget()
        inner.setContentsMargins(4, 4, 4, 4)
        layout = self.vlayout
        self.browser = QtWidgets.QTextBrowser()
        layout.setContentsMargins(0, 0, 0, 0)
        self.browser.setContentsMargins(0, 0, 0, 0)
        self.browser.setMinimumWidth(200)
        self.browser.setFrameStyle(QtWidgets.QFrame.NoFrame)
        p = self.browser.palette()
        p.setColor(QtGui.QPalette.Base, QtCore.Qt.transparent)
        self.browser.setPalette(p)
        layout.addWidget(self.browser)
        self.set_text(HelpPanel.default_text)
        self.finish_init()
        ctrl.graph_view.activateWindow()
        ctrl.graph_view.setFocus()

    def set_text(self, text):
        self.browser.setHtml(text)

    def text(self):
        return self.browser.toHtml()

