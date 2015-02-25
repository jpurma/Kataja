from PyQt5 import QtWidgets, QtGui, QtCore

from kataja.ui.embeds.UIEmbed import UIEmbed
from kataja.ui.DrawnIcons import ArrowIcon, DividerIcon
from kataja.singletons import qt_prefs, ctrl, prefs
import kataja.globals as g


__author__ = 'purma'


class MarkerStartPoint(QtWidgets.QGraphicsItem):
    def __init__(self, parent):
        QtWidgets.QGraphicsItem.__init__(self, parent)
        self.setCursor(QtCore.Qt.CrossCursor)
        self.setAcceptHoverEvents(True)
        self.draggable = True
        self.clickable = False


    def paint(self, painter, options, QWidget_widget=None):
        if prefs.touch:
            p = QtGui.QPen(ctrl.cm.ui_tr())
            p.setWidth(2)
            painter.setPen(p)
            # b = ctrl.cm.ui_tr()
            # painter.setBrush(b)
            # painter.setPen(qt_prefs.no_pen)
            painter.drawEllipse(-6, -6, 12, 12)
        else:
            p = QtGui.QPen(ctrl.cm.ui())
            p.setWidthF(0.5)
            painter.setPen(p)
            painter.drawRect(-2, -2, 4, 4)

    def boundingRect(self):
        if prefs.touch:
            return QtCore.QRectF(-6, -6, 12, 12)
        else:
            return QtCore.QRectF(-2, -2, 4, 4)

    def drag(self, event):
        self.parentItem().update_position(event.scenePos())

    def drop_to(self, x, y, recipient=None):
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
        self.draggable = False  # MarkerStartPoint is draggable, not this
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
        if type in [6, 8]:
            end_pos -= QtCore.QPoint(0, 20)
        elif type in [1, 3, 4, 5]:
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
        f = QtGui.QFont(qt_prefs.font(g.MAIN_FONT))
        f.setPointSize(f.pointSize() * 2)
        self.input_line_edit.setFont(f)
        layout.addWidget(self.input_line_edit)
        hlayout = QtWidgets.QHBoxLayout()
        self.input_action_selector = QtWidgets.QComboBox(self)
        for item in [g.GUESS_FROM_INPUT, g.ADD_CONSTITUENT, g.ADD_FEATURE, g.ADD_GLOSS, g.ADD_TEXT_BOX]:
            self.input_action_selector.addItem(item, userData=item)  # first item here can be translated
        hlayout.addWidget(self.input_action_selector)
        self.enter_button = QtWidgets.QPushButton("↩")  # U+21A9 &#8617;
        self.enter_button.setMaximumWidth(20)
        ui_manager.connect_element_to_action(self.enter_button, 'new_element_enter_text')

        hlayout.addWidget(self.enter_button)
        layout.addLayout(hlayout)
        self.setLayout(layout)
        self.assumed_width = 200
        self.assumed_height = 117

    def mouseMoveEvent(self, event):
        self.move(self.mapToParent(event.pos()) - self._drag_diff)
        if self.marker:
            self.marker.update_position()

    def focus_to_main(self):
        self.input_line_edit.setFocus()

    def close(self):
        self.input_line_edit.setText('')
        UIEmbed.close(self)

    def finished_effect_animation(self):
        UIEmbed.finished_effect_animation(self)
        if self._timeline.direction() == QtCore.QTimeLine.Backward and self.marker:
            ctrl.ui.clean_up_creation_dialog()


# line = new QFrame(w);
# line->setObjectName(QString::fromUtf8("line"));
# line->setGeometry(QRect(320, 150, 118, 3));
# line->setFrameShape(QFrame::HLine);
# line->setFrameShadow(QFrame::Sunken);
