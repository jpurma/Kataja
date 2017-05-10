from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QStandardItem, QIcon

from kataja.Shapes import SHAPE_PRESETS
from kataja.singletons import ctrl
from kataja.ui_support.TableModelSelectionBox import TableModelSelectionBox


class LineStyleIcon(QIcon):
    def __init__(self, shape_key, size):
        super().__init__()
        self.shape_key = shape_key
        self.size_hint = size
        self.compose_icon()

    def compose_icon(self):
        c = ctrl.cm.get(ctrl.settings.cached_active_edge('color_id'))
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
    def __init__(self, parent):
        super().__init__(parent)
        self.setIconSize(QSize(64, 16))
        items = []
        self.icons = []

        for lt in SHAPE_PRESETS.keys():
            icon = LineStyleIcon(lt, self.iconSize())
            self.icons.append(icon)
            item = QStandardItem(icon, '')
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


