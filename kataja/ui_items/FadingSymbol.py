# coding=utf-8
from PyQt5 import QtCore, QtWidgets
from kataja.UIItem import UIItem

from kataja.singletons import prefs
qbytes_opacity = QtCore.QByteArray()
qbytes_opacity.append("opacity")


class FadingSymbol(UIItem, QtWidgets.QGraphicsObject):
    """

    """

    def __init__(self, symbol, host, ui_manager, ui_key, place='bottom_right'):
        UIItem.__init__(self, ui_key, host)
        QtWidgets.QGraphicsObject.__init__(self)
        self.inner = QtWidgets.QGraphicsPixmapItem()
        self.inner.setParentItem(self)
        self.inner.setPixmap(symbol)
        self.place = place
        self.ui_manager = ui_manager
        self.update_position()
        self._fade_out_active = False
        self._fade_anim = None
        self.setZValue(72)
        self.show()
        self.setOpacity(1.0)
        # self.setBrush(colors.ui_support)

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. List of types is kept as comments in globals.py,
        but for performance reasons just hardcode it here.
        :return:
        """
        return 65652

    def update_position(self):
        # br = self.boundingRect()
        """


        """
        if self.place == 'bottom_right':
            w2 = self.inner.pixmap().width() / 2
            br = QtCore.QPointF(self.host.sceneBoundingRect().bottomRight() - QtCore.QPoint(w2, 0))
            self.setPos(br)

    def fade_out(self, s=600):
        """ Start fade out. The object exists until fade end.
        :return: None
        """
        self._fade_out_active = True
        if self._fade_anim:
            self._fade_anim.stop()
        self._fade_anim = QtCore.QPropertyAnimation(self, qbytes_opacity)
        self._fade_anim.setDuration(s)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0)
        self._fade_anim.setEasingCurve(QtCore.QEasingCurve.OutQuad)
        self._fade_anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
        self._fade_anim.finished.connect(self.fade_out_finished)

    def fade_out_finished(self):
        self.hide()
        self.ui_manager.remove_ui(self)
        self._fade_out_active = False

    def is_fading(self):
        """ Fade out is ongoing
        :return: bool
        """
        return self._fade_out_active

    def boundingRect(self):
        return self.inner.boundingRect()

    def paint(self, QPainter, QStyleOptionGraphicsItem, QWidget_widget=None):
        return



