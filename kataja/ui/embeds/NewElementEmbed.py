from PyQt5 import QtWidgets, QtGui, QtCore
from kataja.ui.embeds.UIEmbed import UIEmbed
from kataja.singletons import qt_prefs, ctrl
from kataja.utils import print_transform

__author__ = 'purma'


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


    def paint(self, painter, options, QWidget_widget=None):
        p = QtGui.QPen(ctrl.cm.ui())
        p.setWidthF(0.5)
        painter.setPen(p)
        painter.drawLine(self.start_point, self.end_point)

    def boundingRect(self):
        return QtCore.QRectF(self.start_point, self.end_point)

    def update_position(self, scenePos=None):
        self.prepareGeometryChange()
        if scenePos:
            self.start_point = scenePos
        end_pos = QtCore.QPoint(self.embed.x(), self.embed.y() + self.embed.height() / 2)
        v = self.embed.parentWidget()
        self.end_point = v.mapToScene(end_pos)



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
