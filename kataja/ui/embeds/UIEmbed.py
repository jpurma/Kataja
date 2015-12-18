from PyQt5 import QtWidgets, QtCore, QtGui

from kataja.singletons import ctrl, qt_prefs
from kataja.ui.OverlayButton import PanelButton

__author__ = 'purma'


class UIEmbed(QtWidgets.QWidget):
    """ UIEmbeds are UI elements that are drawn on the main graphics view: they
    are contextual panels that need more UI-capabilities like focus, selection
    and text editing than would be practical to do with GraphicsItems.
    The benefits of UIEmbeds are that these do not scale with graphicsitems,
    and these are styled automatically from palette, as long as they get
    updated properly. These are also not counted in GraphicsScene, so these
    won't cause additional code there.

    UIEmbed implements the basic functions of all embeds: showing them,
    updating their positions, close buttons, updating colors. The approach is
    similar to UIPanels.

    :param parent:
    :param ui_manager:
    """

    def __init__(self, parent, ui_manager, ui_key, host, text):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui_key = ui_key
        self.host = host
        self.ui_manager = ui_manager
        self._palette = None
        self.update_color()
        self._drag_diff = None

        self.top_row_layout = QtWidgets.QHBoxLayout()
        #close_button = QtWidgets.QPushButton("x")
        close_button = PanelButton(qt_prefs.close_icon, text='Close', parent=self, size=12)
        close_button.setMaximumWidth(16)
        ui_manager.connect_element_to_action(close_button, 'close_embed')
        self.top_row_layout.addWidget(close_button)
        self.top_row_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.top_row_layout.addSpacing(8)
        self.top_title = QtWidgets.QLabel(text)
        self.top_row_layout.addWidget(self.top_title)
        self.assumed_width = 200
        self.assumed_height = 100
        self._magnet = QtCore.QPoint(0, 0), 1
        self._effect = QtWidgets.QGraphicsOpacityEffect(self)
        self._timeline = QtCore.QTimeLine(100, self)
        self._timeline.setFrameRange(0, 100)
        self._timeline.frameChanged[int].connect(self.update_frame)
        self._timeline.finished.connect(self.finished_effect_animation)
        self.setGraphicsEffect(self._effect)
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QtGui.QPalette.Window)

        # Remember to add top_row_layout to your layout

        # Remember Johnny fucking Marr

    def update_embed(self, focus_point=None):
        self.update_color()
        self.update_fields()
        self.update_position(focus_point=focus_point)

    def update_fields(self):
        """ Subclasses implement this if there are fields to update
        :return:
        """
        pass

    def margin_x(self):
        """ Margin around embed edit provides some empty space so that the focus point of embed
        is not occluded by the embed. e.g. if focus point=(0,0), with margins=(6,6) embed's top
        left corner would be at (6, 6) and point (0, 0) would still be visible.
        :return:
        """
        return 6

    def margin_y(self):
        """ Margin around embed edit provides some empty space so that the focus point of embed
        is not occluded by the embed. e.g. if focus point=(0,0), with margins=(6,6) embed's top
        left corner would be at (6, 6) and point (0, 0) would still be visible.
        :return:
        """
        return 6

    def update_position(self, focus_point=None):
        """ Position embedded editor to graphics view. The idea is that the embed edit shouldn't
        occlude the focus point (object being edited or the point on screen where new object will
        be created, but it should try to fit as whole into the graphics view. So this method
        computes which corner or edge of editor should be placed closest to focus point and moves
        the embed accordingly.
        :param focus_point:
        :return:
        """
        if not focus_point:
            if self.host:
                focus_point = self.host.scenePos()
            else:
                return
        h = self.height()
        w = self.width()
        if h < 100:
            h = self.assumed_height
        if w < 100:
            w = self.assumed_width
        view_pos = self.parent().mapFromScene(focus_point)
        vw = self.parent().width()
        vh = self.parent().height()
        x = view_pos.x()
        y = view_pos.y()
        # Magnet placement:
        # 1---2---3
        # |+-----+|
        # 4|     |5
        # |+-----+|
        # 6---7---8
        #
        margin_x = self.margin_x()
        margin_y = self.margin_y()

        w += margin_x
        h += margin_y

        if x + w > vw:
            if y + h > vh:
                magnet = QtCore.QPoint(w, h), 8
            else:
                magnet = QtCore.QPoint(w, margin_y), 3
        elif y + (h / 2) > vh:
            if x + (w / 2) > vw:
                magnet = QtCore.QPoint(w, h), 8
            elif x - (w / 2) < 0:
                magnet = QtCore.QPoint(-margin_x, h), 6
            else:
                magnet = QtCore.QPoint(w / 2, h), 7
        elif y - (h / 2) < 0:
            if x + (w / 2) > vw:
                magnet = QtCore.QPoint(w, -margin_y), 3
            elif x - (w / 2) < 0:
                magnet = QtCore.QPoint(-margin_x, -margin_y), 1
            else:
                magnet = QtCore.QPoint(w / 2, -margin_y), 2
        else:
            magnet = QtCore.QPoint(-margin_x, h / 2), 4
        self._magnet = magnet
        self.move(view_pos - magnet[0])
        self.updateGeometry()

    def magnet(self):
        return self._magnet

    def update_frame(self, frame):
        self._effect.setOpacity(frame/100.0)
        self._effect.update()
        self._effect.updateBoundingRect()

    def finished_effect_animation(self):
        self._effect.setEnabled(False)
        if self._timeline.direction() == QtCore.QTimeLine.Backward:
            self.hide()
            self.close()
            ctrl.graph_scene.update()
            ctrl.graph_view.update()
            self.after_close()
        else:
            self.after_appear()

    def after_appear(self):
        """ Customizable calls for refreshing widgets that have drawing problems recovering from blur effect.
        :return:
        """
        pass

    def after_close(self):
        """ Customizable call for removing the widget after the blur away effect is finished.
        :return:
        """
        pass

    def update_color(self):
        key = None
        if self.host and hasattr(self.host, 'get_color_id'):
            key = self.host.get_color_id()
        if key:
            self._palette = ctrl.cm.get_accent_palette(key)
        else:
            self._palette = ctrl.cm.get_qt_palette_for_ui()
        self.setPalette(self._palette)

    def wake_up(self):
        if not self.isVisible():
            self._effect.setOpacity(self._timeline.startFrame()/100.0)
            self._effect.setEnabled(True)
            self._timeline.setDirection(QtCore.QTimeLine.Forward)
            self._timeline.start()
            self.show()
            self.update_position() # size is computed properly only after
            # widget is visible
        self.raise_()
        self.focus_to_main()

    def blur_away(self):
        if self.isVisible():
            self._effect.setOpacity(self._timeline.endFrame()/100.0)
            self._effect.setEnabled(True)
            self._timeline.setDirection(QtCore.QTimeLine.Backward)
            self._timeline.start()
        else:
            self.close()

    def focus_to_main(self):
        pass

    def mousePressEvent(self, event):
        self._drag_diff = event.pos()

    def mouseMoveEvent(self, event):
        self.move(self.mapToParent(event.pos()) - self._drag_diff)
        QtWidgets.QWidget.mouseMoveEvent(self, event)
