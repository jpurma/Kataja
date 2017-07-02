from PyQt5 import QtCore, QtWidgets

from kataja.singletons import qt_prefs


stylesheet = """font-size: 10pt; padding: 4px;"""

class FloatingTip(QtWidgets.QLabel):

    def __init__(self):
        QtWidgets.QWidget.__init__(self, None, QtCore.Qt.ToolTip)
        self.setText('')
        self.setStyleSheet(stylesheet)
        #self.setFont(qt_prefs.get_font('ui_font'))
        #self.setMinimumHeight(20)
        #self.setMinimumWidth(40)
        #self.setMaximumWidth(120)
        self.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Minimum)
        #self.setContentsMargins(2, 2, 2, 2)
        self.setWordWrap(True)
        self.item = None

    def set_item(self, item):
        if item is not self.item:
            self.item = item
            self.setText(item.k_tooltip)

    ##def enterEvent(self, event):
    #    self.show()

    def set_position(self, pos):
        if isinstance(pos, QtCore.QPointF):
            pos = pos.toPoint()
        self.move(pos)