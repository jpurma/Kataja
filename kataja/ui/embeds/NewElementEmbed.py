from PyQt5 import QtWidgets, QtGui, QtCore
from kataja.ui.embeds.UIEmbed import UIEmbed
from kataja.singletons import qt_prefs, ctrl
from kataja.utils import print_transform
from kataja.ui.DrawnIconEngine import DrawnIconEngine
import kataja.globals as g

__author__ = 'purma'


class ArrowIcon(QtGui.QIcon):
    def __init__(self):
        QtGui.QIcon.__init__(self, DrawnIconEngine(self.paint_method, self))

    @staticmethod
    def paint_method(painter, rect, color=None):
        w = rect.width()
        h = rect.height()
        path = QtGui.QPainterPath(QtCore.QPointF(0, h - 4))
        path.lineTo(w, 4)
        p = painter.pen()
        p.setWidthF(1.5)
        painter.setPen(p)
        painter.drawPath(path)
        d = (h - 8.0) / w
        path = QtGui.QPainterPath(QtCore.QPointF(w, 4))
        path.lineTo(w - 10,  8 + (10 * d))
        path.lineTo(w - 8,  4 + (8 * d))
        path.lineTo(w - 12,  12 * d)
        painter.fillPath(path, color)

    def paint_settings(self):
        return {'color':ctrl.cm.d['accent4']}


class DividerIcon(QtGui.QIcon):
    def __init__(self):
        QtGui.QIcon.__init__(self, DrawnIconEngine(self.paint_method, self))

    @staticmethod
    def paint_method(painter, rect, color=None):
        w = rect.width()
        h = rect.height()
        path = QtGui.QPainterPath(QtCore.QPointF(0, h - 4))
        path.cubicTo(10, h - 10 , w - 10, 10, w, 4)
        p = painter.pen()
        p.setWidthF(2)
        p.setStyle(QtCore.Qt.DashLine)
        painter.setPen(p)
        painter.drawPath(path)

    def paint_settings(self):
        return {'color':ctrl.cm.d['accent5']}



class MarkerStartPoint(QtWidgets.QGraphicsItem):
    def __init__(self, parent):
        QtWidgets.QGraphicsItem.__init__(self, parent)
        self.setCursor(QtCore.Qt.CrossCursor)
        self.setAcceptHoverEvents(True)
        self.draggable = True
        self.clickable = False


    def paint(self, painter, options, QWidget_widget=None):
        p = QtGui.QPen(ctrl.cm.ui())
        p.setWidthF(0.5)
        painter.setPen(p)
        painter.drawRect(-2, -2, 4, 4)

    def boundingRect(self):
        return QtCore.QRectF(-2, -2, 4, 4)

    def drag(self, event):
        self.parentItem().update_position(event.scenePos())

    def drop_to(self, x, y):
        pass

class NewElementMarker(QtWidgets.QGraphicsItem):
    """ Element marker is line drawn to graphics scene pointing from place where new element should go to
    embedded widget.

    :param parent:
    :param ui_manager:
    :param scenePos:
    """

    def __init__(self, scenePos, embed):
        QtWidgets.QGraphicsItem.__init__(self)
        self.start_point = None
        self.end_point = None
        self.embed = embed
        self.update_position(scenePos=scenePos)
        self.start_point_cp = MarkerStartPoint(self)
        self.start_point_cp.show()
        self.draggable = False # MarkerStartPoint is draggable, not this
        self.clickable = False


    def paint(self, painter, options, QWidget_widget=None):
        p = QtGui.QPen(ctrl.cm.ui())
        p.setWidthF(0.5)
        painter.setPen(p)
        painter.drawLine(QtCore.QPoint(0, 0), self.end_point)
        painter.drawRect(self.end_point.x() - 2, self.end_point.y() - 2, 4, 4)

    def boundingRect(self):
        return QtCore.QRectF(self.start_point, self.end_point)

    def update_position(self, scenePos=None):
        self.prepareGeometryChange()
        if scenePos:
            self.start_point = scenePos
        magnet, type = self.embed.magnet()
        end_pos = self.embed.pos() + magnet
        if type in [4, 5, 6, 8]:
            end_pos -= QtCore.QPoint(0, 20)
        elif type in [1, 3]:
            end_pos += QtCore.QPoint(0, 20)
        elif type in [2, 7]:
            end_pos += QtCore.QPoint(20, 0)
        v = self.embed.parentWidget()
        self.setPos(self.start_point)
        self.end_point = self.mapFromScene(v.mapToScene(end_pos)).toPoint()



class NewElementEmbed(UIEmbed):

    def __init__(self, parent, ui_manager, scenePos):
        UIEmbed.__init__(self, parent, ui_manager, scenePos)
        self.marker = None
        layout = QtWidgets.QVBoxLayout()
        self.new_arrow_button = QtWidgets.QPushButton(" &Arrow")
        self.top_row_layout.addWidget(self.new_arrow_button)
        self.new_arrow_button.setIconSize(QtCore.QSize(40, 16))
        self.new_arrow_button.setIcon(ArrowIcon())
        ui_manager.connect_element_to_action(self.new_arrow_button, 'new_arrow')
        self.new_divider_button = QtWidgets.QPushButton(" &Divider")
        self.new_divider_button.setIconSize(QtCore.QSize(40, 16))
        self.new_divider_button.setIcon(DividerIcon())
        self.top_row_layout.addWidget(self.new_divider_button)
        ui_manager.connect_element_to_action(self.new_divider_button, 'new_divider')
        layout.addLayout(self.top_row_layout)
        layout.addSpacing(12)
        self.input_line_edit = QtWidgets.QLineEdit(self)
        f = QtGui.QFont(qt_prefs.font)
        f.setPointSize(f.pointSize()*2)
        self.input_line_edit.setFont(f)
        layout.addWidget(self.input_line_edit)
        hlayout = QtWidgets.QHBoxLayout()
        self.input_action_selector = QtWidgets.QComboBox(self)
        for item in [g.GUESS_FROM_INPUT, g.ADD_CONSTITUENT, g.ADD_FEATURE, g.ADD_GLOSS, g.ADD_TEXT_BOX]:
            self.input_action_selector.addItem(item, userData=item) # first item here can be translated
        hlayout.addWidget(self.input_action_selector)
        self.enter_button = QtWidgets.QPushButton("↩") # U+21A9 &#8617;
        self.enter_button.setMaximumWidth(20)
        ui_manager.connect_element_to_action(self.enter_button, 'new_element_enter_text')

        hlayout.addWidget(self.enter_button)
        layout.addLayout(hlayout)
        self.setLayout(layout)
        self.assumed_width = 200
        self.assumed_height = 117

    def mouseMoveEvent(self, event):
        self.move(self.mapToParent(event.pos()) - self._drag_diff)
        self.marker.update_position()

    def focus_to_main(self):
        self.input_line_edit.setFocus()

    def close(self):
        self.input_line_edit.setText('')
        UIEmbed.close(self)


# line = new QFrame(w);
#     line->setObjectName(QString::fromUtf8("line"));
#     line->setGeometry(QRect(320, 150, 118, 3));
#     line->setFrameShape(QFrame::HLine);
#     line->setFrameShadow(QFrame::Sunken);
