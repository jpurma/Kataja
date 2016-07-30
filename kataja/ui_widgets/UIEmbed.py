from PyQt5 import QtWidgets, QtCore, QtGui

from kataja.UIItem import UIWidget
from kataja.singletons import ctrl, qt_prefs
from kataja.ui_widgets.OverlayButton import PanelButton
from kataja.uniqueness_generator import next_available_type_id
import kataja.globals as g

__author__ = 'purma'


class UIEmbed(UIWidget, QtWidgets.QWidget):
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
    __qt_type_id__ = next_available_type_id()
    unique = True

    def __init__(self, parent, host, text):
        UIWidget.__init__(self, host)
        QtWidgets.QWidget.__init__(self, parent)
        self._palette = None
        self.update_colors()
        self._drag_diff = None
        self.moved_by_hand = False

        self.top_row_layout = QtWidgets.QHBoxLayout()
        #close_button = QtWidgets.QPushButton("x")
        close_button = PanelButton(pixmap=qt_prefs.close_icon, tooltip='Close', parent=self,
                                   size=12, color_key='content1')
        close_button.setMaximumWidth(16)
        self.ui_manager.connect_element_to_action(close_button, 'close_embed')
        self.top_row_layout.addWidget(close_button)
        self.top_row_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.top_row_layout.addSpacing(8)
        self.top_title = QtWidgets.QLabel(text)
        self.top_row_layout.addWidget(self.top_title)
        self.assumed_width = 300
        self.assumed_height = 100
        self._magnet = QtCore.QPoint(0, 0), 1
        # Effect will be disabled if QTextEdit is used.
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QtGui.QPalette.Window)
        self.hide()
        # Remember to add top_row_layout to your layout

    def type(self):
        """ Qt's type identifier, custom QGraphicsItems should have different type ids if events
        need to differentiate between them. These are set when the program starts.
        :return:
        """
        return self.__qt_type_id__

    @property
    def graphic_item(self):
        """ if this _Widget_ has UI graphic items associated in scene, e.g. target reticles or so.
        :return:
        """
        return None

    def update_embed(self, focus_point=None):
        self.update_colors()
        self.update_fields()
        if focus_point:
            self.update_position(focus_point=focus_point)

    def update_size(self):
        self.setFixedSize(self.layout().minimumSize())

    def update_fields(self):
        """ Subclasses implement this if there are elements to update
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
        if self.moved_by_hand:
            return

        if not focus_point:
            if self.host:
                focus_point = self.host.scenePos()
            else:
                return

        view = self.parent()
        w = self.size().width()
        h = self.size().height()
        if h <= 100:
            h = self.assumed_height
        if w <= 100:
            w = self.assumed_width
        top_left = view.mapToScene(0, 0)
        bottom_right = view.mapToScene(QtCore.QPoint(w, h))
        size_in_scene = bottom_right - top_left
        w = size_in_scene.x()
        h = size_in_scene.y()
        vr = view.mapToScene(view.geometry()).boundingRect()
        view_top = vr.top()
        view_bottom = vr.bottom()
        view_left = vr.left()
        view_right = vr.right()
        if self.host:
            br = self.host.sceneBoundingRect()
            node_top = br.top()
            node_bottom = br.bottom()
            node_left = br.left()
            node_right = br.right()
        else:
            node_top = focus_point.y()
            node_bottom = focus_point.y()
            node_left = focus_point.x()
            node_right = focus_point.x()

        if node_top - view_top > view_bottom - node_bottom:
            # UP
            new_y = node_top - h
        else:
            # DOWN
            new_y = node_bottom

        # Possible positions
        #   xxx
        #      n
        #
        #   xxx
        #     n
        #
        #   xxx
        #    n
        #
        #   xxx
        #   n
        #
        #    xxx
        #   n

        new_lefts = [node_left - w, node_right - w, (node_right + node_left - w) / 2, node_left,
                     node_right]

        new_x = 0
        min_space = 1000000

        for new_left in new_lefts:
            if new_left < view_left or new_left + w > view_right:
                continue
            space = (new_left - view_left) ** 2 + (view_right - (new_left + w)) ** 2
            if space < min_space:
                min_space = space
                new_x = new_left

        new_pos = QtCore.QPoint(new_x, new_y)
        # Magnet placement:
        # 1---2---3
        # |+-----+|
        # 4|     |5
        # |+-----+|
        # 6---7---8
        #
        self.move(view.mapFromScene(new_pos))
        self.updateGeometry()

    def magnet(self):
        return self._magnet

    def update_colors(self):
        key = None
        if self.host and hasattr(self.host, 'get_color_id'):
            key = self.host.get_color_id()
        if key:
            self._palette = ctrl.cm.get_accent_palette(key)
        else:
            self._palette = ctrl.cm.get_qt_palette_for_ui()
        self.setPalette(self._palette)

    def wake_up(self):
        self.fade_in()
        self.raise_()
        self.focus_to_main()


    def focus_to_main(self):
        pass

    def mousePressEvent(self, event):
        self._drag_diff = event.pos()

    def mouseMoveEvent(self, event):
        self.move(self.mapToParent(event.pos()) - self._drag_diff)
        self.moved_by_hand = True
        QtWidgets.QWidget.mouseMoveEvent(self, event)

    def resizeEvent(self, event):
        QtWidgets.QWidget.resizeEvent(self, event)
