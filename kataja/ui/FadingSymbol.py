# coding=utf-8
from PyQt5 import QtCore, QtWidgets

from kataja.singletons import prefs


class FadingSymbol(QtWidgets.QGraphicsPixmapItem):
    """

    """

    def __init__(self, symbol, host, ui_manager, place='bottom_right'):
        QtWidgets.QGraphicsPixmapItem.__init__(self)
        self.setPixmap(symbol)
        self.host = host
        self.place = place
        self.ui_manager = ui_manager
        self.update_position()
        self._fade_out_counter = 0
        self.setZValue(72)
        # self.setBrush(colors.ui)

    def update_position(self):
        # br = self.boundingRect()
        """


        """
        if self.place == 'bottom_right':
            w2 = self.pixmap().width() / 2
            br = QtCore.QPointF(self.host.sceneBoundingRect().bottomRight() - QtCore.QPoint(w2, 0))
            self.setPos(br)

    def fade_out(self, speed='slow'):
        """

        :param speed:
        """
        if speed == 'slow':
            self._fade_out_counter = 30
        else:
            self._fade_out_counter = 15
        self._fade_step = 1.0 / self._fade_out_counter

        self._timer = QtCore.QTimer()
        self._timer.setInterval(1000 / prefs.FPS)
        self._timer.timeout.connect(self.timer_ticks)
        self._timer.start()

    def timer_ticks(self):
        """ Make sure that every timer lasts for only a certain amount of ticks and 
            call tick method or final method if this is the last tick. """
        if self._fade_out_counter:
            self._fade_out_counter -= 1
            op = self.opacity()
            op -= self._fade_step
            self.setOpacity(op)
        else:
            self.stop_timer()

    def stop_timer(self):
        """


        """
        self._timer.stop()
        self._timer = None
        self.hide()
        self.ui_manager.symbols.remove(self)
        self.ui_manager.remove_ui(self)



