from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QStandardItem, QIcon

from kataja.shapes import SHAPE_PRESETS
from kataja.singletons import ctrl
from kataja.ui_support.TableModelSelectionBox import TableModelSelectionBox
from kataja.utils import time_me


def find_panel(parent):
    if hasattr(parent, 'pin_to_dock'):
        return parent
    else:
        return find_panel(parent.parent())


class ShapeSelector(TableModelSelectionBox):
    def __init__(self, parent):
        super().__init__(parent)
        self.setIconSize(QSize(48, 16))
        self.panel = find_panel(parent)
        items = []
        self.icons = []

        for lt in SHAPE_PRESETS.keys():
            icon = LineStyleIcon(lt, self.panel, self.iconSize())
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


class LineStyleIcon(QIcon):
    def __init__(self, shape_key, panel, size):
        super().__init__()
        self.shape_key = shape_key
        self.panel = panel
        self.size_hint = size
        self.compose_icon()

    def compose_icon(self):
        draw_method = SHAPE_PRESETS[self.shape_key]['icon']
        c = ctrl.cm.get(self.panel.cached_edge_color or 'content1')
        size = self.size_hint

        hidp = self.panel.devicePixelRatio()
        isize = QtCore.QSize(size.width() * hidp, size.height() * hidp)

        image = QtGui.QImage(
            isize, QtGui.QImage.Format_ARGB32_Premultiplied)
        image.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(image)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(c)
        draw_method(painter, image.rect(), c)
        painter.end()
        self.addPixmap(QtGui.QPixmap.fromImage(image))
