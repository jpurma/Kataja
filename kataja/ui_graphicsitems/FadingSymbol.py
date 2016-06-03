# coding=utf-8
from PyQt5 import QtCore, QtWidgets
from kataja.UIItem import UIGraphicsItem

from kataja.singletons import prefs
from kataja.uniqueness_generator import next_available_type_id

qbytes_opacity = QtCore.QByteArray()
qbytes_opacity.append("opacity")


class FadingSymbol(UIGraphicsItem, QtWidgets.QGraphicsObject):
    """

    """
    __qt_type_id__ = next_available_type_id()

    def __init__(self, symbol, host, place='bottom_right'):
        UIGraphicsItem.__init__(self, host=host)
        QtWidgets.QGraphicsObject.__init__(self)
        self.inner = QtWidgets.QGraphicsPixmapItem()
        self.inner.setParentItem(self)
        self.inner.setPixmap(symbol)
        self.place = place
        self.update_position()
        self._fade_anim = None
        self.setZValue(72)
        self.show()
        self.setOpacity(1.0)
        # self.setBrush(colors.ui_support)

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

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
        self.is_fading_out = True
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
        self.is_fading_out = False


    def boundingRect(self):
        return self.inner.boundingRect()

    def paint(self, QPainter, QStyleOptionGraphicsItem, QWidget_widget=None):
        return



