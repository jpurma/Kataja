from PyQt5 import QtWidgets, QtGui, QtCore

from kataja.ui.embeds.UIEmbed import UIEmbed
from kataja.ui.drawn_icons import arrow, divider
from kataja.singletons import qt_prefs, ctrl, prefs
import kataja.globals as g
from kataja.ui.panels.field_utils import icon_text_button, EmbeddedLineEdit, box_row, \
    ExpandingLineEdit
from kataja.shapes import draw_arrow_shape_from_points

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
        pi = self.parentItem()
        if pi:
            pi.set_dragged(True)
            pi.update_position(event.scenePos())

    def drop_to(self, x, y, recipient=None):
        pass


class NewElementMarker(QtWidgets.QGraphicsItem):
    """ Element marker is line drawn to graphics scene pointing from place where new element
    should go to
    embedded widget.

    :param parent:
    :param ui_manager:
    :param scene_pos:
    """

    def __init__(self, scene_pos, embed, ui_key):
        QtWidgets.QGraphicsItem.__init__(self)
        self.ui_key = ui_key
        self.host = None
        self.start_point = None
        self.end_point = None
        self.embed = embed
        self.update_position(scene_pos=scene_pos)
        self.start_point_cp = MarkerStartPoint(self)
        self.start_point_cp.show()
        self.draggable = False  # MarkerStartPoint is draggable, not this
        self.clickable = False
        self.dragged = False

    def paint(self, painter, options, QWidget_widget=None):
        p = QtGui.QPen(ctrl.cm.ui())
        p.setWidthF(0.5)
        painter.setPen(p)
        if self.dragged:
            draw_arrow_shape_from_points(painter, self.end_point.x(), self.end_point.y(), 0, 0, 10)
        else:
            painter.drawLine(QtCore.QPoint(0, 0), self.end_point)
        painter.drawRect(self.end_point.x() - 2, self.end_point.y() - 2, 4, 4)

    def boundingRect(self):
        return QtCore.QRectF(self.start_point, self.end_point)

    def set_dragged(self, value):
        if self.dragged and value:
            return
        elif value:
            self.dragged = True
            self.embed.marker_dragged()

    def update_position(self, scene_pos=None):
        self.prepareGeometryChange()
        if scene_pos:
            self.start_point = scene_pos
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
        UIEmbed.__init__(self, parent, ui_manager, ui_key, None, 'Create new node')
        self.marker = None
        self.manual_node_change = False
        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(self.top_row_layout)
        hlayout = box_row(layout)
        self.new_arrow_button = icon_text_button(ui_manager, hlayout, self, '', '',
                                                 " &Arrow", 'new_arrow', size=QtCore.QSize(48, 20),
                                                 draw_method=arrow)
        self.divider_button = icon_text_button(ui_manager, hlayout, self, '', '',
                                               " &Divider", 'new_divider',
                                               size=QtCore.QSize(48, 20), draw_method=divider)
        self.new_arrow_button.setFlat(False)
        self.divider_button.setFlat(False)
        self.new_arrow_button.hide()
        self.divider_button.hide()
        tt = 'Text for new node'
        smaller_font = qt_prefs.font(g.MAIN_FONT)
        big_font = QtGui.QFont(smaller_font)
        big_font.setPointSize(big_font.pointSize() * 2)
        self.input_line_edit = ExpandingLineEdit(self,
                                                 tip=tt,
                                                 big_font=big_font,
                                                 smaller_font=smaller_font,
                                                 prefill='label')
        layout.addWidget(self.input_line_edit)
        hlayout = QtWidgets.QHBoxLayout()
        self.node_type_selector = QtWidgets.QComboBox(self)
        self.node_type_selector.currentIndexChanged.connect(self.changed_node_type)

        node_types = [('Guess from input', g.GUESS_FROM_INPUT)]
        for key in prefs.node_types_order:
            # we have dedicated buttons for arrows and dividers
            #if key not in (g.ARROW, g.DIVIDER):
            nd = prefs.nodes[key]
            node_types.append(('New %s' % nd['name'].lower(), key))
        node_types.append(('New arrow', g.ARROW))
        node_types.append(('New divider', g.DIVIDER))
        for i, (name, value) in enumerate(node_types):
            self.node_type_selector.addItem(name)
            self.node_type_selector.setItemData(i, value, 256)
            # 'name' can be translated if necessary
        hlayout.addWidget(self.node_type_selector)
        self.enter_button = QtWidgets.QPushButton("Create ↩")  # U+21A9 &#8617;
        ui_manager.connect_element_to_action(self.enter_button, 'create_new_node_from_text')

        hlayout.addWidget(self.enter_button)
        layout.addLayout(hlayout)
        self.setLayout(layout)
        self.assumed_width = 200
        self.assumed_height = 117

    def mouseMoveEvent(self, event):
        self.move(self.mapToParent(event.pos()) - self._drag_diff)
        if self.marker:
            self.marker.update_position()
            self.marker.set_dragged(True)
        QtWidgets.QWidget.mouseMoveEvent(self, event)

    def changed_node_type(self, *args):
        print('toggle toggle')
        self.manual_node_change = True

    def focus_to_main(self):
        self.input_line_edit.setFocus(QtCore.Qt.PopupFocusReason)

    def marker_dragged(self):
        if not self.manual_node_change:
            self.embed.set_node_type(g.ARROW)

    def update_size(self):
        self.setMinimumSize(self.layout().minimumSize())

    def close(self):
        self.input_line_edit.reset()
        UIEmbed.close(self)

    def finished_effect_animation(self):
        UIEmbed.finished_effect_animation(self)
        if self._timeline.direction() == QtCore.QTimeLine.Backward and self.marker:
            ctrl.ui.clean_up_creation_dialog()

    def get_marker_points(self):
        p1 = self.marker.pos()
        p2 = self.marker.mapToScene(self.marker.end_point)
        return p1, p2

    def set_node_type(self, value):
        self.node_type_selector.setCurrentIndex(self.node_type_selector.findData(value, role=256))

