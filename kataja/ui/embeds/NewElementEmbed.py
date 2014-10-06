from PyQt5 import QtWidgets, QtGui, QtCore
from kataja.ui.embeds.UIEmbed import UIEmbed
from kataja.singletons import qt_prefs, ctrl
from kataja.utils import print_transform

__author__ = 'purma'

class MarkerStartPoint(QtWidgets.QGraphicsItem):
    def __init__(self, parent):
        QtWidgets.QGraphicsItem.__init__(self, parent)
        self.setCursor(QtCore.Qt.CrossCursor)
        self.setAcceptHoverEvents(True)
        self.draggable = True


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
        end_pos = QtCore.QPoint(self.embed.x(), self.embed.y() + self.embed.height() / 2)
        v = self.embed.parentWidget()
        self.setPos(self.start_point)
        self.end_point = self.mapFromScene(v.mapToScene(end_pos)).toPoint()



class NewElementEmbed(UIEmbed):

    def __init__(self, parent, ui_manager, scenePos):
        UIEmbed.__init__(self, parent, ui_manager, scenePos)
        self.marker = None
        layout = QtWidgets.QVBoxLayout()
        self.new_arrow_button = QtWidgets.QPushButton("Arrow ->")
        self.top_row_layout.addWidget(self.new_arrow_button)
        self.new_divider_button = QtWidgets.QPushButton("Divider --")
        self.top_row_layout.addWidget(self.new_divider_button)
        layout.addLayout(self.top_row_layout)
        layout.addSpacing(12)
        self.input_line_edit = QtWidgets.QLineEdit(self)
        f = QtGui.QFont(qt_prefs.font)
        f.setPointSize(f.pointSize()*2)
        self.input_line_edit.setFont(f)
        layout.addWidget(self.input_line_edit)
        hlayout = QtWidgets.QHBoxLayout()
        self.input_action_selector = QtWidgets.QComboBox(self)
        self.input_action_selector.addItems(['guess from input', 'Constituent', 'Feature', 'Gloss', 'Text box'])
        hlayout.addWidget(self.input_action_selector)
        self.enter_button = QtWidgets.QPushButton("↩") # U+21A9 &#8617;
        self.enter_button.setMaximumWidth(20)
        hlayout.addWidget(self.enter_button)
        layout.addLayout(hlayout)
        self.setLayout(layout)

    def mouseMoveEvent(self, event):
        self.move(self.mapToParent(event.pos()) - self._drag_diff)
        self.marker.update_position()


# line = new QFrame(w);
#     line->setObjectName(QString::fromUtf8("line"));
#     line->setGeometry(QRect(320, 150, 118, 3));
#     line->setFrameShape(QFrame::HLine);
#     line->setFrameShadow(QFrame::Sunken);
