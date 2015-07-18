from PyQt5 import QtWidgets, QtCore, QtGui

from kataja.singletons import ctrl
from kataja.ui.panels.SymbolPanel import open_symbol_data

__author__ = 'purma'





class EmbeddedTextarea(QtWidgets.QPlainTextEdit):
    def __init__(self, parent, tip='', font=None, prefill=''):
        QtWidgets.QPlainTextEdit.__init__(self, parent)
        if tip:
            self.setToolTip(tip)
            self.setStatusTip(tip)
        if font:
            self.setFont(font)
        if prefill:
            self.setPlaceholderText(prefill)
        self.setAcceptDrops(True)
        #self.setDragEnabled(True)

    def dragEnterEvent(self, event):
        """ Announce support for regular ascii drops and drops of characters from symbolpanel.
        :param event: QDragEnterEvent
        :return:
        """
        if event.mimeData().hasFormat(
                "application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            return QtWidgets.QPlainTextEdit.dragEnterEvent(self, event)

    def dropEvent(self, event):
        """ Support regular ascii drops and drops of characters from symbolpanel.
        :param event: QDropEvent
        :return:
        """
        if event.mimeData().hasFormat(
                "application/x-qabstractitemmodeldatalist"):
            data = open_symbol_data(event.mimeData())
            if data and 'char' in data:
                self.insert(data['char'])
                event.acceptProposedAction()
        else:
            return QtWidgets.QPlainTextEdit.dropEvent(self, event)

    def update_visual(self, **kw):
        if 'palette' in kw:
            self.setPalette(kw['palette'])
        if 'font' in kw:
            self.setFont(kw['font'])
        if 'text' in kw:
            self.setText(kw['text'])


class EmbeddedLineEdit(QtWidgets.QLineEdit):
    def __init__(self, parent, tip='', font=None, prefill=''):
        QtWidgets.QLineEdit.__init__(self, parent)
        if tip:
            self.setToolTip(tip)
            self.setStatusTip(tip)
        if font:
            self.setFont(font)
        if prefill:
            self.setPlaceholderText(prefill)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)

    def dragEnterEvent(self, event):
        """ Announce support for regular ascii drops and drops of characters from symbolpanel.
        :param event: QDragEnterEvent
        :return:
        """
        if event.mimeData().hasFormat(
                "application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            return QtWidgets.QLineEdit.dragEnterEvent(self, event)

    def dropEvent(self, event):
        """ Support regular ascii drops and drops of characters from symbolpanel.
        :param event: QDropEvent
        :return:
        """
        if event.mimeData().hasFormat(
                "application/x-qabstractitemmodeldatalist"):
            data = open_symbol_data(event.mimeData())
            if data and 'char' in data:
                self.insert(data['char'])
                event.acceptProposedAction()
        else:
            return QtWidgets.QLineEdit.dropEvent(self, event)

    def update_visual(self, **kw):
        if 'palette' in kw:
            self.setPalette(kw['palette'])
        if 'font' in kw:
            self.setFont(kw['font'])
        if 'text' in kw:
            self.setText(kw['text'])


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
    :param scenePos:
    """

    def __init__(self, parent, ui_manager, ui_key, host):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui_key = ui_key
        self.host = host
        self.ui_manager = ui_manager
        self._palette = None
        self.update_color()
        self._drag_diff = None

        self.top_row_layout = QtWidgets.QHBoxLayout()
        close_button = QtWidgets.QPushButton("x")
        close_button.setMaximumWidth(16)
        ui_manager.connect_element_to_action(close_button, 'close_embed')

        self.top_row_layout.addWidget(close_button)
        self.top_row_layout.setAlignment(QtCore.Qt.AlignLeft)
        self.assumed_width = 200
        self.assumed_height = 100
        self._magnet = QtCore.QPoint(0, 0), 1
        self._effect = QtWidgets.QGraphicsBlurEffect(self)
        self._effect.setBlurHints(QtWidgets.QGraphicsBlurEffect.AnimationHint)
        self._timeline = QtCore.QTimeLine(150, self)
        self._timeline.setFrameRange(50, 0)
        self._timeline.frameChanged[int].connect(self.update_frame)
        self._timeline.finished.connect(self.finished_effect_animation)
        self.setGraphicsEffect(self._effect)
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QtGui.QPalette.Window)

        # Remember to add top_row_layout to your layout

        # Remember Johnny fucking Marr

    def update_embed(self, scenePos=None):
        self.update_color()
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

            # Magnet placement:
            # 1---2---3
            # |       |
            # 4       5
            # |       |
            # 6---7---8
            #
            if x + w > vw:
                if y + h > vh:
                    magnet = QtCore.QPoint(w, h), 8
                else:
                    magnet = QtCore.QPoint(w, 0), 3
            elif y + (h / 2) > vh:
                if x + (w / 2) > vw:
                    magnet = QtCore.QPoint(w, h), 8
                elif x - (w / 2) < 0:
                    magnet = QtCore.QPoint(0, h), 6
                else:
                    magnet = QtCore.QPoint(w / 2, h), 7
            elif y - (h / 2) < 0:
                if x + (w / 2) > vw:
                    magnet = QtCore.QPoint(w, 0), 3
                elif x - (w / 2) < 0:
                    magnet = QtCore.QPoint(0, 0), 1
                else:
                    magnet = QtCore.QPoint(w / 2, 0), 2
            else:
                magnet = QtCore.QPoint(0, h / 2), 4
            self._magnet = magnet
            self.move(view_pos - magnet[0])
            self.updateGeometry()

    def magnet(self):
        return self._magnet

    def update_frame(self, frame):
        self._effect.setBlurRadius(frame)
        self.update()

    def finished_effect_animation(self):
        self._effect.setEnabled(False)
        if self._timeline.direction() == QtCore.QTimeLine.Backward:
            self.hide()
            self.close()
            ctrl.graph_scene.update()
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
            self._effect.setBlurRadius(self._timeline.startFrame())
            self._effect.setEnabled(True)
            self._timeline.setDirection(QtCore.QTimeLine.Forward)
            self._timeline.start()
            self.show()
        self.raise_()
        self.focus_to_main()

    def blur_away(self):
        if self.isVisible():
            self._effect.setBlurRadius(self._timeline.endFrame())
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
