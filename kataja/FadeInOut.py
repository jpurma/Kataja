

from PyQt5 import QtCore
from kataja.singletons import ctrl, prefs

qbytes_opacity = QtCore.QByteArray()
qbytes_opacity.append("opacity")


class FadeInOut:
    """ Provides fade in/out capabilities for graphics items. Inherit this class.
    """

    def __init__(self):
        self._fade_in_anim = None
        self._fade_out_anim = None
        self.is_fading_in = False
        self.is_fading_out = False

    def fade_in(self, s=150):
        """ Simple fade effect. The object exists already when fade starts.
        :return: None
        :param s: speed in ms
        """
        if self.is_fading_in:
            return
        self.is_fading_in = True
        if not self.isVisible():
            self.show()
        if self.is_fading_out:
            self.is_fading_out = False
            self._fade_out_anim.stop()
        self._fade_in_anim = QtCore.QPropertyAnimation(self, qbytes_opacity)
        self._fade_in_anim.setDuration(s)
        self._fade_in_anim.setStartValue(0.0)
        self._fade_in_anim.setEndValue(1.0)
        self._fade_in_anim.setEasingCurve(QtCore.QEasingCurve.InQuad)
        self._fade_in_anim.finished.connect(self.fade_in_finished)
        self._fade_in_anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    def fade_in_finished(self):
        self.is_fading_in = False

    def fade_out(self, s=150):
        """ Start fade out. The object exists until fade end.
        :return: None
        """
        if not self.isVisible():
            return
        if self.is_fading_out:
            return
        self.is_fading_out = True
        if self.is_fading_in:
            self.is_fading_in = False
            self._fade_in_anim.stop()
        self._fade_out_anim = QtCore.QPropertyAnimation(self, qbytes_opacity)
        self._fade_out_anim.setDuration(s)
        self._fade_out_anim.setStartValue(1.0)
        self._fade_out_anim.setEndValue(0)
        self._fade_out_anim.setEasingCurve(QtCore.QEasingCurve.OutQuad)
        self._fade_out_anim.finished.connect(self.fade_out_finished)
        self._fade_out_anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    def fade_out_and_delete(self, s=150):
        """ Start fade out. The object exists until fade end.
        :return: None
        """
        if self.is_fading_out:
            self._fade_out_anim.finished.disconnect()
            self._fade_out_anim.finished.connect(self.fade_out_finished_delete)
            if self.is_fading_in:
                self.is_fading_in = False
                self._fade_in_anim.stop()
            return
        if not self.isVisible():
            self.fade_out_finished_delete()
            return
        self.is_fading_out = True
        if self.is_fading_in:
            self.is_fading_in = False
            self._fade_in_anim.stop()
        self._fade_out_anim = QtCore.QPropertyAnimation(self, qbytes_opacity)
        self._fade_out_anim.setDuration(s)
        self._fade_out_anim.setStartValue(1.0)
        self._fade_out_anim.setEndValue(0)
        self._fade_out_anim.setEasingCurve(QtCore.QEasingCurve.OutQuad)
        self._fade_out_anim.finished.connect(self.fade_out_finished_delete)
        self._fade_out_anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)

    def fade_out_finished_delete(self):
        self.is_fading_out = False
        self.hide()
        if hasattr(self, 'forest'):
            self.forest.remove_from_scene(self, fade_out=False)

    def fade_out_finished(self):
        self.is_fading_out = False
        self.hide()
