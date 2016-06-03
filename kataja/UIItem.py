# coding=utf-8
from kataja.singletons import ctrl
from kataja.uniqueness_generator import next_available_ui_key
from PyQt5 import QtWidgets, QtCore

qbytes_opacity = QtCore.QByteArray()
qbytes_opacity.append("opacity")


class UIItem:
    """ UI Items are items that are tracked by UIManager. UIManager can fetch UIItems for
    updating, e.g. change palette colors or update field values.  UI Items can also announce
    signals that they will receive, these signals can be sent by any object.
    """
    permanent_ui = False
    unique = False

    def __init__(self, host=None, ui_key=None, role=None):
        if ui_key:
            self.ui_key = ui_key
        elif self.unique:
            self.ui_key = self.__class__.__name__
        else:
            self.ui_key = next_available_ui_key()
        self.ui_type = self.__class__.__name__
        self.ui_manager = ctrl.ui
        self.role = role  # optional way to identify if cannot be distinguished w. class
        self.host = host
        self.watchlist = []
        self.is_fading_in = False
        self.is_fading_out = False
        self._fade_anim = None
        self._effect = None
        self._disable_effect = False

    def watch_alerted(self, obj, signal, field_name, value):
        pass

    def update_position(self):
        pass

    def update_colors(self):
        pass

    def can_fade(self):
        return isinstance(self, (QtWidgets.QWidget, QtWidgets.QGraphicsObject))

    def fade_in(self, s=300):
        """ Simple fade effect. The object exists already when fade starts.
        There are two ways to do fade, one for QGraphicsItems and one for QWidgets
        :return: None
        :param s: speed in ms
        """
        if self.is_fading_in:
            return
        self.is_fading_in = True
        self.show()
        if isinstance(self, QtWidgets.QGraphicsItem):
            if self.is_fading_out:
                self._fade_anim.stop()
            self._fade_anim = QtCore.QPropertyAnimation(self, qbytes_opacity)
            self._fade_anim.setDuration(s)
            self._fade_anim.setStartValue(0.0)
            self._fade_anim.setEndValue(1.0)
            self._fade_anim.setEasingCurve(QtCore.QEasingCurve.InQuad)
            self._fade_anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
            self._fade_anim.finished.connect(self.fade_in_finished)
        elif isinstance(self, QtWidgets.QWidget):
            if not self._effect:
                self.prepare_widget_effect()
            self._effect.setOpacity(self._timeline.startFrame() / 100.0)
            self._effect.setEnabled(True)
            self._timeline.setDirection(QtCore.QTimeLine.Forward)
            self._timeline.start()

    def prepare_widget_effect(self):
        self._effect = QtWidgets.QGraphicsOpacityEffect(self)
        self._timeline = QtCore.QTimeLine(80, self)
        self._timeline.setFrameRange(0, 100)
        self._timeline.frameChanged[int].connect(self.update_frame)
        self._timeline.finished.connect(self.finished_effect_animation)
        self._effect.setEnabled(False)
        # it seems that opacityeffect and QTextEdit doesn't work well together
        self.setGraphicsEffect(self._effect)

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
        if isinstance(self, QtWidgets.QGraphicsItem):
            if self.is_fading_in:
                self._fade_anim.stop()
            self._fade_anim = QtCore.QPropertyAnimation(self, qbytes_opacity)
            self._fade_anim.setDuration(s)
            self._fade_anim.setStartValue(1.0)
            self._fade_anim.setEndValue(0)
            self._fade_anim.setEasingCurve(QtCore.QEasingCurve.OutQuad)
            self._fade_anim.start(QtCore.QAbstractAnimation.DeleteWhenStopped)
            self._fade_anim.finished.connect(self.fade_out_finished)
        elif isinstance(self, QtWidgets.QWidget):
            if not self._effect:
                self.prepare_widget_effect()
            self._effect.setOpacity(self._timeline.endFrame()/100.0)
            self._effect.setEnabled(True)
            self._timeline.setDirection(QtCore.QTimeLine.Backward)
            self._timeline.start()

    def fade_out_finished(self):
        self.visible = False
        self.is_fading_out = False
        if isinstance(self, QtWidgets.QGraphicsItem):
            ctrl.ui.remove_from_scene(self)
        else:
            self.hide()
        self.after_close()

    def update_frame(self, frame):
        self._effect.setOpacity(frame/100.0)
        self._effect.update()
        self._effect.updateBoundingRect()

    def finished_effect_animation(self):
        self._effect.setEnabled(False)
        if self._timeline.direction() == QtCore.QTimeLine.Backward:
            self.fade_out_finished()
        else:
            self.after_appear()

    def after_close(self):
        pass

    def after_appear(self):
        pass