# coding=utf-8
from PyQt5 import QtWidgets

from kataja.UIItem import UIWidget
from kataja.singletons import ctrl


class DragInfo(UIWidget, QtWidgets.QLabel):

    unique = True

    def __init__(self, host, parent):
        """ DragInfo is a simple text label located next to dragged node to show its relative 
        adjustment to computed position. It helps the user to understand relative nature of 
        object positioning. 
        :param host: node that is being dragged
        :param parent: parent widget where drag info will be placed
        """
        UIWidget.__init__(self, host=host)
        QtWidgets.QLabel.__init__(self, parent)
        self.setPalette(ctrl.cm.get_qt_palette_for_ui())
        self.par = parent
        self.update_position()
        self.setMinimumWidth(72)
        self.show()

    def update_value(self):
        if self.host.use_physics():
            x = '{:+}'.format(int(self.host.current_position[0]))
            y = '{:+}'.format(int(self.host.current_position[1]))
        else:
            x = '{:+}'.format(int(self.host.adjustment[0]))
            y = '{:+}'.format(int(self.host.adjustment[1]))
        self.setText('{:>4}, {:>4}'.format(x, y))

    def update_position(self):
        br = self.host.sceneBoundingRect().topRight()
        pos = self.par.mapFromScene(br)
        self.move(pos.x() + 8, pos.y() - 16)

