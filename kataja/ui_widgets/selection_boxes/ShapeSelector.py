from PyQt5 import QtCore, QtGui

from kataja.Shapes import SHAPE_PRESETS
from kataja.singletons import ctrl
from kataja.ui_widgets.selection_boxes.TableModelSelectionBox import TableModelSelectionBox


class LineStyleIcon(QtGui.QIcon):
    def __init__(self, shape_key, size):
        super().__init__()
        self.shape_key = shape_key
        self.size_hint = size
        self.compose_icon()

    def compose_icon(self):
        c = ctrl.cm.get('content1')  # fixme! color should be appropriate for edge_type
        size = self.size_hint

        hidp = ctrl.main.devicePixelRatio()
        isize = QtCore.QSize(size.width() * hidp, size.height() * hidp)

        image = QtGui.QImage(
            isize, QtGui.QImage.Format_ARGB32_Premultiplied)
        image.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(c)
        SHAPE_PRESETS[self.shape_key].icon_path(painter, image.rect(), c)
        painter.end()
        self.addPixmap(QtGui.QPixmap.fromImage(image))


class ShapeSelector(TableModelSelectionBox):
    def __init__(self, **kwargs):
        TableModelSelectionBox.__init__(self, **kwargs)
        self.setIconSize(QtCore.QSize(64, 16))
        items = []
        self.icons = []

        for lt in SHAPE_PRESETS.keys():
            icon = LineStyleIcon(lt, self.iconSize())
            self.icons.append(icon)
            item = QtGui.QStandardItem(icon, '')
            item.setData(lt)
            if ctrl.main.use_tooltips:
                item.setToolTip(lt)
            item.setSizeHint(self.iconSize())
            items.append(item)
        model = self.model()
        model.setRowCount(len(items))
        for r, item in enumerate(items):
            model.setItem(r, 0, item)
        self.view().setModel(model)

    def update_colors(self):
        m = self.model()
        for i in range(0, m.rowCount()):
            item = m.item(i, 0)
            icon = self.icons[i]
            icon.compose_icon()
            item.setIcon(icon)

    def showEvent(self, event):
        ctrl.add_watcher(self, 'active_edge_color_changed')
        ctrl.add_watcher(self, 'palette_changed')
        ctrl.add_watcher(self, 'scope_changed')
        super().showEvent(event)

    def hideEvent(self, event):
        ctrl.remove_from_watch(self)
        super().hideEvent(event)

    def watch_alerted(self, *kw, **kwargs):
        self.update_colors()


