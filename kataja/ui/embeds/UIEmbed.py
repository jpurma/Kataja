from PyQt5 import QtWidgets
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
        closebutton = QtWidgets.QPushButton("x")
        closebutton.setMaximumWidth(16)
        self.top_row_layout.addWidget(closebutton)

        # Remember to add top_row_layout to your layout


    def update_embed(self, scenePos=None):

        self.setPalette(ctrl.cm.get_qt_palette_for_ui())
        if scenePos:
            view_pos = self.parent().mapFromScene(scenePos)
            self.move(view_pos.x(), view_pos.y() - self.height() / 2)

    def update_color(self):
        self.setPalette(ctrl.cm.get_qt_palette_for_ui())

    def wake_up(self):
        self.show()
        self.raise_()

    def mousePressEvent(self, event):
        self._drag_diff = event.pos()

    def mouseMoveEvent(self, event):
        self.move(self.mapToParent(event.pos()) - self._drag_diff)

