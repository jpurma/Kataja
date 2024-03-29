# coding=utf-8
from PyQt6 import QtWidgets, QtCore

from kataja.singletons import ctrl
from kataja.ui_widgets.KatajaLabel import KatajaBuddyLabel
from kataja.uniqueness_generator import next_available_ui_key


qbytes_opacity = QtCore.QByteArray("opacity".encode())


class UIItem:
    """ UI Items are items that are tracked by UIManager. UIManager can fetch UIItems for
    updating, e.g. change palette colors or update field values.  UI Items can also announce
    signals that they will receive, these signals can be sent by any object.
    """
    permanent_ui = False
    unique = False
    can_fade = True
    scene_item = False
    is_widget = False
    selection_independent = False

    def __init__(self, host=None, ui_key=None, role=None, tooltip=''):
        if ui_key:
            self.ui_key = ui_key
        elif self.unique:
            self.ui_key = self.__class__.__name__
        else:
            self.ui_key = next_available_ui_key()
        self.k_action = None
        self.ui_type = self.__class__.__name__
        self.ui_manager = ctrl.ui
        self.role = role  # optional way to identify if cannot be distinguished w. class
        self.host = host
        self.priority = 10
        self.k_tooltip = tooltip
        self.is_fading_in = False
        self.is_fading_out = False
        self._fade_in_anim = None
        self._fade_out_anim = None
        self._opacity_effect = None
        self._disable_effect = False
        self._hovering = False

    def update_position(self):
        pass

    def after_close(self):
        pass

    def after_appear(self):
        pass

    def prepare_opacity_effect(self):
        self._opacity_effect = QtWidgets.QGraphicsOpacityEffect()
        self._opacity_effect.setEnabled(False)
        self.setGraphicsEffect(self._opacity_effect)

    def prepare_fade_in_effect(self):
        self._fade_in_anim = QtCore.QPropertyAnimation(self._opacity_effect, qbytes_opacity)
        self._fade_in_anim.setStartValue(0.0)
        self._fade_in_anim.setEndValue(1.0)
        self._fade_in_anim.setEasingCurve(QtCore.QEasingCurve.InQuad)
        self._fade_in_anim.finished.connect(self.fade_in_finished)

    def fade_in_finished(self):
        self.is_fading_in = False
        self._fade_in_anim = None
        self._opacity_effect.setEnabled(False)

    def show(self):
        if self.isVisible():
            print('unnecessary show for UIItem: ', self)
        else:
            s = super()
            if hasattr(s, 'show'):
                s.show()

    def fade_in(self, s=150):
        """ Simple fade effect. The object exists already when fade starts.
        There are two ways to do fade, one for QGraphicsItems and one for QWidgets
        :return: None
        :param s: speed in ms
        """
        if self.is_fading_in:
            return
        self.show()
        if not self.can_fade:
            return
        self.is_fading_in = True
        if not self._opacity_effect:
            self.prepare_opacity_effect()
        if not self._fade_in_anim:
            self.prepare_fade_in_effect()
        self._opacity_effect.setEnabled(True)
        self._fade_in_anim.setDuration(s)
        self._fade_in_anim.start(QtCore.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def prepare_fade_out_effect(self):
        self._fade_out_anim = QtCore.QPropertyAnimation(self._opacity_effect, qbytes_opacity)
        self._fade_out_anim.setStartValue(1.0)
        self._fade_out_anim.setEndValue(0.0)
        self._fade_out_anim.setEasingCurve(QtCore.QEasingCurve.Type.OutQuad)
        self._fade_out_anim.finished.connect(self.fade_out_finished)

    def fade_out_finished(self):
        self.hide()
        self.is_fading_out = False
        self._fade_out_anim = None
        self.after_close()

    def fade_out(self, s=150):
        """ Start fade out. The object exists until fade end.
        :return: None
        """
        if not self.isVisible():
            return
        if self.is_fading_out:
            return
        self.is_fading_out = True
        if not self._opacity_effect:
            self.prepare_opacity_effect()
        if not self._fade_out_anim:
            self.prepare_fade_out_effect()
        self._opacity_effect.setEnabled(True)
        if self.is_fading_in:
            self._fade_in_anim.stop()
        self._fade_out_anim.setDuration(s)
        self._fade_out_anim.start(QtCore.QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)


class UIGraphicsItem(UIItem):
    """ UIGraphicsItems are UIItems that will inherit QGraphicsItem. So they must deal with
    scene, and they are not necessarily QObjects.
    """
    can_fade = True
    is_widget = False
    scene_item = True

    def fade_out_finished(self):
        UIItem.fade_out_finished(self)
        ctrl.ui.remove_from_scene(self)

    def hoverEnterEvent(self, event):
        self._hovering = True
        ctrl.ui.show_help(self, event)

    @staticmethod
    def hoverMoveEvent(event):
        ctrl.ui.move_help(event)

    def hoverLeaveEvent(self, event):
        self._hovering = False
        ctrl.ui.hide_help(self, event)


class UIWidget(UIItem):
    """ UIWidgets have to inherit QWidget at some point. """
    can_fade = True
    is_widget = True
    scene_item = False
    mouse_tracking = False

    def __init__(self, action='', **kwargs):
        UIItem.__init__(self, **kwargs)
        self.k_buddy = None
        self._cached_value = None
        if action:
            ctrl.ui.connect_element_to_action(self, action)

    def to_layout(self, layout, align=None, with_label=None, label_first=True):
        """ Because widgets cannot be reliably put to layout in their __init__-methods,
        to ease the layout process, we can use javascript-style (constructor).to_layout(...)
        combination.
        :param layout:
        :param align:
        :param with_label: str, create a label from given string
        :param label_first: by default label is put first, but sometimes it is better after widget
        :return: self, so that this can be used with constructors
        """
        labelw = None
        if with_label:
            labelw = KatajaBuddyLabel(text=with_label, buddy=self)
            self.k_buddy = labelw
            if label_first:
                layout.addWidget(labelw)
        if align:
            layout.addWidget(self, alignment=align)
        else:
            layout.addWidget(self)
        if with_label and not label_first:
            layout.addWidget(labelw)
        return self

    def prepare_opacity_effect(self):
        self._opacity_effect = QtWidgets.QGraphicsOpacityEffect(self)
        self._opacity_effect.setEnabled(False)
        self.setGraphicsEffect(self._opacity_effect)

    def fade_out_finished(self):
        UIItem.fade_out_finished(self)
        self.close()

    def enterEvent(self, event):
        self._hovering = True
        ctrl.ui.show_help(self, event)

    def mouseMoveEvent(self, event):
        ctrl.ui.move_help(event)

    def leaveEvent(self, event):
        self._hovering = False
        ctrl.ui.hide_help(self, event)
