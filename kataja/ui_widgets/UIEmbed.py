from PyQt5 import QtWidgets, QtCore, QtGui

from kataja.KatajaAction import KatajaAction
from kataja.UIItem import UIWidget
from kataja.singletons import ctrl, qt_prefs, prefs
from kataja.ui_widgets.buttons.PanelButton import PanelButton
from kataja.uniqueness_generator import next_available_type_id

__author__ = 'purma'


class EmbedAction(KatajaAction):

    def __init__(self):
        super().__init__()
        self.embed = None

    def on_connect(self, ui_item):
        def find_embed_widget(widget):
            if isinstance(widget, UIEmbed):
                return widget
            elif widget:
                return find_embed_widget(widget.parentWidget())

        self.embed = find_embed_widget(ui_item.parentWidget())


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
    """
    __qt_type_id__ = next_available_type_id()
    unique = True

    def __init__(self, parent, host, text):
        UIWidget.__init__(self, host=host)
        # noinspection PyArgumentList
        QtWidgets.QWidget.__init__(self, parent)
        self._palette = None
        self.update_colors()
        self._drag_diff = None
        self.moved_by_hand = False
        self.vlayout = QtWidgets.QVBoxLayout()

        self.top_row_layout = QtWidgets.QHBoxLayout()
        # close_button = QtWidgets.QPushButton("x")
        close_button = PanelButton(pixmap=qt_prefs.close_icon, parent=self, size=12,
                                   color_key='content1')
        close_button.setMaximumWidth(16)
        self.ui_manager.connect_element_to_action(close_button, 'close_embed')
        # noinspection PyArgumentList
        self.top_row_layout.addWidget(close_button)
        self.top_row_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.top_row_layout.addSpacing(8)
        self.top_title = QtWidgets.QLabel(text)
        # noinspection PyArgumentList
        self.top_row_layout.addWidget(self.top_title)
        self.assumed_width = 300
        self.assumed_height = 100
        self._magnet = QtCore.QPoint(0, 0), 1
        # Effect will be disabled if QTextEdit is used.
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QtGui.QPalette.Window)
        self.hide()
        self.vlayout.addLayout(self.top_row_layout)  # close-button from UIEmbed
        self.vlayout.addSpacing(4)
        self.setLayout(self.vlayout)

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
        pass

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
        self.update_size()
        ew = prefs.edge_width
        eh = prefs.edge_height
        view = ctrl.graph_view
        my_rect = self.geometry()
        w = my_rect.width()
        h = my_rect.height()
        view_rect = view.geometry()
        scene_br = None
        if self.host:
            scene_br = self.host.sceneBoundingRect()
            scene_br.adjust(-ew, -eh, ew, eh)
        elif focus_point:
            scene_br = QtCore.QRectF(-ew, -eh, ew * 2, eh * 2)
            scene_br.moveCenter(focus_point.toPoint())
        node_rect = view.mapFromScene(scene_br).boundingRect()

        # do nothing if we already have a good enough position. For user it is better if the
        # panel stays in place than if it jumps around.
        if view_rect.contains(my_rect, proper=True) and not node_rect.intersects(my_rect):
            # print('do nothing: ', my_rect, view_rect, node_rect)
            return

        ncy = node_rect.center().y()

        if node_rect.right() + w < view_rect.right():
            if node_rect.right() + w + 50 < view_rect.right():
                x = node_rect.right() + 50
            else:
                x = view_rect.right() - w
        else:
            if node_rect.left() - w - 50 > 4:
                x = node_rect.left() - w - 50
            else:
                x = 4
        if ncy - h / 2 > 25 and ncy + h / 2 < view_rect.height():
            y = ncy - h / 2
        else:
            y = h / 2 - node_rect.height() / 2

        print('updating embed position, ', x, y)
        self.move(x, y)
        self.updateGeometry()

    def magnet(self):
        return self._magnet

    def update_colors(self):
        key = None
        if self.host and hasattr(self.host, 'get_color_key'):
            key = self.host.get_color_key()
        if key:
            self._palette = ctrl.cm.get_accent_palette(key)
            self.setPalette(self._palette)

    def wake_up(self):
        self.fade_in()
        self.raise_()
        self.focus_to_main()

    def focus_to_main(self):
        pass

    def mousePressEvent(self, event):
        self._drag_diff = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_diff:
            print(self.mapToParent(event.pos()) - self._drag_diff, self.geometry())
            self.move(self.mapToParent(event.pos()) - self._drag_diff)
            self.moved_by_hand = True
        QtWidgets.QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        self._drag_diff = None
        super().mouseReleaseEvent(event)

    def event(self, e):
        if e.type() == QtCore.QEvent.PaletteChange:
            self.update_colors()
        return QtWidgets.QWidget.event(self, e)
