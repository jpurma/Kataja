from PyQt5 import QtWidgets, QtGui, QtCore
from kataja.singletons import ctrl

__author__ = 'purma'


class ColorBox(QtWidgets.QPushButton):
    """
        Rectangular solid button for displaying a color. Clicking it should open system's color selector.
    """

    def __init__(self, color_id, color_name):
        """

        :param color:
        :param color_name:
        """
        QtWidgets.QPushButton.__init__(self)
        self.color_id = color_id
        self.color_name = color_name
        self.setFlat(True)

    def paintEvent(self, event):
        """

        :param event:
        """
        painter = QtGui.QPainter(self)
        c = getattr(ctrl.cm, self.color_id)
        if c and callable(c):
            c = c()
            if not c:
                print('Color method %s returns None' % self.color_id)
            else:
                painter.setBrush(c)
                if self.color_id == 'background1':
                    painter.setPen(ctrl.cm.drawing())
                else:
                    painter.setPen(c)
                painter.drawRect(QtCore.QRect(0, 0, 40, 20))
                painter.drawText(48, 12, self.color_name)
        else:
            print("Color method %s is missing" % self.color_id)

    def sizeHint(self):
        return QtCore.QSize(160, 22)