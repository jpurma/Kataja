from PyQt5 import QtWidgets, QtCore
from kataja.singletons import ctrl

__author__ = 'purma'


class UIEmbed(QtWidgets.QWidget):
    """ UIEmbeds are UI elements that are drawn on the main graphics view: they are contextual panels that need more
    UI-capabilities like focus, selection and text editing than would be practical to do with GraphicsItems.
    The benefits of UIEmbeds are that these do not scale with graphicsitems, and these are styled automatically from
    palette, as long as they get updated properly. These are also not counted in GraphicsScene, so these won't cause
    additional code there.

    UIEmbed implements the basic functions of all embeds: showing them, updating their positions, close buttons,
    updating colors. The approach is similar to UIPanels.

    :param parent:
    :param ui_manager:
    :param scenePos:
    """

    def __init__(self, parent, ui_manager, scenePos):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui_manager = ui_manager
        self.setPalette(ctrl.cm.get_qt_palette_for_ui())
        self._drag_diff = None

        self.top_row_layout = QtWidgets.QHBoxLayout()
        close_button = QtWidgets.QPushButton("x")
        close_button.setMaximumWidth(16)
        ui_manager.connect_element_to_action(close_button, 'close_embed')

        self.top_row_layout.addWidget(close_button)
        self.assumed_width = 200
        self.assumed_height = 100
        self._magnet = QtCore.QPoint(0, 0), 1

        # Remember to add top_row_layout to your layout

        # Remember Johnny fucking Marr

    def update_embed(self, scenePos=None):

        self.setPalette(ctrl.cm.get_qt_palette_for_ui())
        if scenePos:
            h = self.height()
            w = self.width()
            if h < 100:
                h = self.assumed_height
            if w < 100:
                w = self.assumed_width
            view_pos = self.parent().mapFromScene(scenePos)
            vw = self.parent().width()
            vh = self.parent().height()
            x = view_pos.x()
            y = view_pos.y()
            p = 0
            if x + w > vw:
                if y + h > vh:
                    magnet = QtCore.QPoint(w, h), 8
                else:
                    magnet = QtCore.QPoint(w, 0), 3
            elif y + (h/2) > vh:
                if x + (w/2) > vw:
                    magnet = QtCore.QPoint(w, h), 8
                elif x - (w/2) < 0:
                    magnet = QtCore.QPoint(0, h), 6
                else:
                    magnet = QtCore.QPoint(w/2, h), 7
            elif y - (h/2) < 0:
                if x + (w/2) > vw:
                    magnet = QtCore.QPoint(w, 0), 3
                elif x - (w/2) < 0:
                    magnet = QtCore.QPoint(0, 0), 1
                else:
                    magnet = QtCore.QPoint(w/2, 0), 2
            else:
                magnet = QtCore.QPoint(0, h/2), 4
            self._magnet = magnet
            self.move(view_pos - magnet[0])

    def magnet(self):
        return self._magnet

    def update_color(self):
        self.setPalette(ctrl.cm.get_qt_palette_for_ui())

    def wake_up(self):
        self.show()
        self.raise_()
        self.focus_to_main()

    def focus_to_main(self):
        pass


    def mousePressEvent(self, event):
        self._drag_diff = event.pos()

    def mouseMoveEvent(self, event):
        self.move(self.mapToParent(event.pos()) - self._drag_diff)

