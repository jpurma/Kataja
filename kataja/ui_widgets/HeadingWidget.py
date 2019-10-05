from PyQt5 import QtWidgets, QtCore

from kataja.UIItem import UIWidget
from kataja.singletons import qt_prefs
from kataja.ui_widgets.buttons.TwoStateIconButton import TwoStateIconButton
from kataja.uniqueness_generator import next_available_type_id

__author__ = 'purma'


class HeadingWidget(UIWidget, QtWidgets.QWidget):
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

    def __init__(self, parent):
        UIWidget.__init__(self)
        # noinspection PyArgumentList
        QtWidgets.QWidget.__init__(self, parent)
        self.text = ''
        self.folded = False
        self._drag_diff = None
        self.moved_by_hand = True
        layout = QtWidgets.QHBoxLayout()
        self.fold_button = TwoStateIconButton(parent=self,
                                              pixmap0=qt_prefs.fold_pixmap,
                                              pixmap1=qt_prefs.more_pixmap,
                                              action='toggle_heading',
                                              size=12).to_layout(layout)
        layout.setAlignment(QtCore.Qt.AlignLeft)
        layout.addSpacing(8)
        self.text_widget = QtWidgets.QLabel(self.text)
        # noinspection PyArgumentList
        layout.addWidget(self.text_widget)
        self.setLayout(layout)

    def set_text(self, text):
        self.text = text
        self.text_widget.setText(text)
        self.adjustSize()

    def set_folded(self, folded):
        if folded:
            self.text_widget.hide()
            self.adjustSize()
        else:
            self.text_widget.show()
            self.adjustSize()
        self.folded = folded

    def type(self):
        return self.__qt_type_id__

    def mousePressEvent(self, event):
        self._drag_diff = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_diff:
            self.move(self.mapToParent(event.pos()) - self._drag_diff)
            self.moved_by_hand = True
        QtWidgets.QWidget.mouseMoveEvent(self, event)

    def mouseReleaseEvent(self, event):
        self._drag_diff = None
        super().mouseReleaseEvent(event)
