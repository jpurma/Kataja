from PyQt5 import QtWidgets, QtGui, QtCore

from kataja.ui.embeds.UIEmbed import UIEmbed
from kataja.ui.drawn_icons import arrow, divider
from kataja.singletons import qt_prefs, ctrl, prefs
import kataja.globals as g
from kataja.ui.panels.field_utils import icon_text_button, EmbeddedLineEdit, box_row

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
    """ Element marker is line drawn to graphics scene pointing from place where new element
    should go to
    embedded widget.

    :param parent:
    :param ui_manager:
    :param scenePos:
    """

    def __init__(self, scenePos, embed, ui_key):
        QtWidgets.QGraphicsItem.__init__(self)
        self.ui_key = ui_key
        self.host = None
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
    def __init__(self, parent, ui_manager, ui_key):
        UIEmbed.__init__(self, parent, ui_manager, ui_key, None)
        self.marker = None
        outer_layout = QtWidgets.QVBoxLayout()
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addLayout(self.top_row_layout)
        inner_layout = QtWidgets.QVBoxLayout()
        outer_layout.addLayout(inner_layout)
        inner_layout.setContentsMargins(6, 0, 6, 6)
        hlayout = box_row(inner_layout)
        self.new_arrow_button = icon_text_button(ui_manager, hlayout, self, '', '',
                                                 " &Arrow", 'new_arrow', size=QtCore.QSize(48, 20),
                                                 draw_method=arrow)
        self.divider_button = icon_text_button(ui_manager, hlayout, self, '', '',
                                               " &Divider", 'new_divider',
                                               size=QtCore.QSize(48, 20), draw_method=divider)
        self.new_arrow_button.setFlat(False)
        self.divider_button.setFlat(False)
        tt = 'Text for new node'
        f = QtGui.QFont(qt_prefs.font(g.MAIN_FONT))
        f.setPointSize(f.pointSize() * 2)
        self.input_line_edit = EmbeddedLineEdit(self, tip=tt, font=f, prefill='label')
        inner_layout.addWidget(self.input_line_edit)
        hlayout = QtWidgets.QHBoxLayout()
        self.node_type_selector = QtWidgets.QComboBox(self)

        node_types = []
        for key in prefs.node_types_order:
            # we have dedicated buttons for arrows and dividers
            if key not in (g.ARROW, g.DIVIDER):
                nd = prefs.nodes[key]
                node_types.append(('New %s' % nd['name'].lower(), key))
        for name, value in node_types:
            self.node_type_selector.addItem(name, userData=value)
            # 'name' can be translated if necessary
        hlayout.addWidget(self.node_type_selector)
        self.enter_button = QtWidgets.QPushButton("Create ↩")  # U+21A9 &#8617;
        ui_manager.connect_element_to_action(self.enter_button, 'new_element_enter_text')

        hlayout.addWidget(self.enter_button)
        inner_layout.addLayout(hlayout)
        self.setLayout(outer_layout)
        self.assumed_width = 200
        self.assumed_height = 117

    def mouseMoveEvent(self, event):
        self.move(self.mapToParent(event.pos()) - self._drag_diff)
        if self.marker:
            self.marker.update_position()
        QtWidgets.QWidget.mouseMoveEvent(self, event)

    def focus_to_main(self):
        self.input_line_edit.setFocus()

    def close(self):
        self.input_line_edit.setText('')
        UIEmbed.close(self)

    def finished_effect_animation(self):
        UIEmbed.finished_effect_animation(self)
        if self._timeline.direction() == QtCore.QTimeLine.Backward and self.marker:
            ctrl.ui.clean_up_creation_dialog()

    def get_marker_points(self):
        p1 = self.marker.pos()
        p2 = self.marker.mapToScene(self.marker.end_point)
        return p1, p2

# line = new QFrame(w);
# line->setObjectName(QString::fromUtf8("line"));
# line->setGeometry(QRect(320, 150, 118, 3));
# line->setFrameShape(QFrame::HLine);
# line->setFrameShadow(QFrame::Sunken);
