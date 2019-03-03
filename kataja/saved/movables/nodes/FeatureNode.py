# coding=utf-8
# ############################################################################
#
# *** Kataja - Biolinguistic Visualization tool ***
#
# Copyright 2013 Jukka Purma
#
# This file is part of Kataja.
#
# Kataja is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Kataja is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kataja.  If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################

import random
import string
from PyQt5 import QtGui, QtCore

import kataja.globals as g
from kataja.globals import FEATURE_NODE, EDGE_CAN_INSERT, EDGE_OPEN, EDGE_PLUGGED_IN, \
    EDGE_RECEIVING_NOW, CHECKING_EDGE, EDGE_RECEIVING_NOW_DOMINANT, EDGE_OPEN_DOMINANT
from kataja.singletons import ctrl
from kataja.saved.movables.Node import Node
from kataja.uniqueness_generator import next_available_type_id
from kataja.EdgePath import TOP_SIDE, BOTTOM_SIDE, LEFT_SIDE, RIGHT_SIDE
from kataja.utils import coords_as_str, to_tuple

color_map = {
    'tense': 'accent7',
    'order': 'accent1',
    'person': 'accent2',
    'number': 'accent4',
    'case': 'accent6',
    'unknown': 'accent3',
    'N': 'accent1',
    'D': 'accent2',
    'V': 'accent3',
    'T': 'accent4',
    'F': 'accent5',
    'C': 'accent7',
    'wh': 'accent6',
    'n': 'accent1',
    'd': 'accent2',
    'v': 'accent3',
    't': 'accent4',
    'p': 'accent5',
    'q': 'accent6',
    'c': 'accent7'
}


class FeatureNode(Node):
    """
    Node to express a feature of a constituent
    """
    __qt_type_id__ = next_available_type_id()
    width = 20
    height = 20
    node_type = FEATURE_NODE
    display_name = ('Feature', 'Features')
    class_name = "FN"
    display = True
    wraps = 'feature'

    quick_editable = False
    editable_fields = {'name': dict(name='Name', prefill='X',
                             tooltip='Name of the feature, used as identifier',
                                     syntactic=True),
                        'value': dict(name='Value',
                                      prefill='',
                                      tooltip='Value given to this feature',
                                      syntactic=True),
                        'sign': dict(name='Sign',
                                     prefill='',
                                     tooltip='Sign of this feature, e.g. +, -, u, =...'),
                        'family': dict(name='Family', prefill='',
                                       tooltip='Several distinct features can be '
                                               'grouped under one family (e.g. '
                                               'phi-features)',
                                       syntactic=True)
                      }

    default_style = {'fancy': {'color_key': 'accent2', 'font_id': g.SMALL_CAPS, 'font-size': 9,
                               'visible': True},
                     'plain': {'color_key': 'accent2', 'font_id': g.SMALL_CAPS, 'font-size': 9,
                               'visible': True}}

    default_edge = g.FEATURE_EDGE

    def __init__(self, label=None, forest=None):
        Node.__init__(self, forest=forest)
        self.repulsion = 0.25
        self._gravity = 3.0
        self.fshape = 2
        self.left_shape = 0
        self.right_shape = 0
        self.invert_colors = True

    @property
    def name(self):
        return self.syntactic_object.name

    @property
    def sign(self):
        return self.syntactic_object.sign

    @property
    def value(self):
        return self.syntactic_object.value

    @property
    def family(self):
        return self.syntactic_object.family

    @property
    def checks(self):
        f = self.syntactic_object.checks
        if f:
            return self.forest.get_node(f)

    @property
    def checked_by(self):
        f = self.syntactic_object.checked_by
        if f:
            return self.forest.get_node(f)

    def preferred_z_value(self):
        return 60

    def compute_start_position(self, host):
        """ Makes features start at somewhat predictable position, if they are of common kinds of features.
        If not, then some random noise is added to prevent features sticking together
        :param host:
        """
        x, y = host.current_position
        if self.name in color_map:
            x += color_map[self.name]
            y += color_map[self.name]
        else:
            x += random.uniform(-4, 4)
            y += random.uniform(-4, 4)
        self.set_original_position((x, y))

    def label_as_html(self):
        """ This method builds the html to display in label. For convenience, syntactic objects
        can override this (going against the containment logic) by having their own
        'label_as_html' -method. This is so that it is easier to create custom
        implementations for constituents without requiring custom constituentnodes.

        Note that synobj's label_as_html receives the node object as parameter,
        so you can replicate the behavior below and add your own to it.
        :return:
        """

        # Allow custom syntactic objects to override this
        if hasattr(self.syntactic_object, 'label_as_html'):
            return self.syntactic_object.label_as_html(self)
        return str(self.syntactic_object)

    def label_as_editable_html(self):
        """ This is used to build the html when quickediting a label. It should reduce the label
        into just one field value that is allowed to be edited, in constituentnode this is
        either label synobj's label. This can be overridden in syntactic object by having
        'label_as_editable_html' -method there. The method returns a tuple,
          (field_name, html).
        :return:
        """
        return 'label', ''

    def hidden_in_triangle(self):
        """ If features are folded into triangle, they are always hidden. 
        :return: 
        """
        return bool(self.triangle_stack)

    def my_checking_feature(self):
        f = self.syntactic_object.checked_by
        if f:
            return self.forest.get_node(f)

    def update_checking_display(self, shape, position, checking_mode):
        """ Cluster features according to feature_positioning -setting or release them to be
        positioned according to visualisation.
        'locked_to_node' is the essential attribute in here. For features it should have two 
        kinds of values or None: 
        1: locked to parent constituent node -- this is used to arrange features neatly below node.
        2: locked to another feature -- this is used to show feature checking
        the third option shouldn't happen:
        3: locked to triangle host like constituent nodes are locked to triangle host 
        
        :param shape:
        :param position:
        :param checking_mode:
        :return:
        """

        checked_by = self.my_checking_feature()
        # First see if feature should be attached to another feature
        locked_to_another_feature = False

        if checked_by and self.is_visible():
            if checking_mode == g.NO_CHECKING_EDGE:
                if self.locked_to_node == checked_by:
                    self.release_from_locked_position()
                edge = self.get_edge_to(checked_by, g.CHECKING_EDGE)
                if edge:
                    edge.hide()

            elif checking_mode == g.PUT_CHECKED_TOGETHER:
                locked_to_another_feature = True
                if self.locked_to_node != checked_by:
                    if 1 < checked_by.fshape < 4:
                        compensate = 8
                    elif checked_by.fshape == 4:
                        compensate = 8
                    else:
                        compensate = 4
                    x = checked_by.future_children_bounding_rect().right() - \
                        self.future_children_bounding_rect().x() - compensate
                    self.lock_to_node(checked_by, move_to=(x, 0))

            elif checking_mode == g.SHOW_CHECKING_EDGE and self.locked_to_node == checked_by:
                self.release_from_locked_position()

        # Then see if it should be fixed to its parent constituent node
        if not locked_to_another_feature:
            if position or shape == g.CARD:
                host = self.get_host()
                if host and host.is_visible():
                    self.lock_to_node(host)
                else:
                    self.release_from_locked_position()
            else:
                self.release_from_locked_position()

    def is_needy(self):
        return self.syntactic_object.is_needy()

    def is_valuing(self):
        return not (self.syntactic_object.unvalued() or self.syntactic_object.checked_by)

    def can_satisfy(self):
        return self.syntactic_object.can_satisfy()

    def is_satisfied(self):
        return self.syntactic_object.checked_by

    def satisfies(self):
        return self.syntactic_object.checks

    def get_edges_to_me(self):
        for edge in self.edges_up:
            if edge.alpha is self:
                return edge.chain_up([edge])
        return []

    def get_host(self):
        for parent in self.get_parents(of_type=g.CONSTITUENT_NODE):
            return parent

    def _calculate_inner_rect(self, extra_w=0, extra_h=0):
        label = self.label_object
        x_offset = 0
        y_offset = 0
        w = 0
        h = 0
        if self._label_visible:
            label_rect = label.boundingRect()
            w = label_rect.width()
            h = label_rect.height()
            x_offset = label.x_offset
            y_offset = label.y_offset
            self.label_rect = label_rect
        # offset is offset for the surrounding box around the text.
        if 1 < self.left_shape < 4:
            # plug at left, box is wider to left so box has to start more left
            w += 4
            x_offset -= 4
        elif -4 < self.left_shape < -1:
            # hole at left, box is wider to left so box has to start more left
            w += 4
            x_offset -= 4
        elif self.left_shape == 4:
            w += 8
            x_offset -= 4
        elif self.left_shape == -4:
            w += 8
            x_offset -= 8
        if 1 < self.right_shape < 4:
            w += 4
            x_offset += 2
        elif -4 < self.right_shape < -1:
            w += 4
            x_offset += 2
        elif self.right_shape == 4:
            w += 8
            x_offset += 6
        elif self.right_shape == -4:
            w += 8
            x_offset += 6
        if w < FeatureNode.width:
            w = FeatureNode.width
        if h < FeatureNode.height:
            h = FeatureNode.height

        if x_offset or y_offset:
            x = x_offset
            y = y_offset
        else:
            x = w / -2
            y = h / -2
        self.width = w
        self.height = h
        self._create_magnets(x, y, w, h)
        return QtCore.QRectF(x, y, w, h)

    @staticmethod
    def draw_feature_shape(painter, rect, left, right, color):

        def triangle(path, x, y, mid, dx=1, dy=1):
            path.lineTo(x, y + mid - 4 * dy)
            path.lineTo(x - 4 * dx, y + mid)
            path.lineTo(x, y + mid + 4 * dy)
            path.lineTo(x, y + mid + mid * dy)

        def square(path, x, y, mid, dx=1, dy=1):
            path.lineTo(x, y + mid - 4 * dy)
            path.lineTo(x - 4 * dx, y + mid - 4 * dy)
            path.lineTo(x - 4 * dx, y + mid + 4 * dy)
            path.lineTo(x, y + mid + 4 * dy)
            path.lineTo(x, y + mid + mid * dy)

        def roundish(path, x, y, mid, dx=1, dy=1):
            path.lineTo(x, y + mid - 2 * dy)
            path.cubicTo(x - 3 * dx, y + mid - 2 * dy, x - 3 * dx, y + mid - 6 * dy, x - 6 * dx, y + mid)
            path.cubicTo(x - 3 * dx, y + mid + 6 * dy, x - 3 * dx, y + mid + 2 * dy, x, y + mid + 2 * dy)
            path.lineTo(x, y + mid + mid * dy)

        old_pen = painter.pen()
        painter.setPen(QtCore.Qt.NoPen)
        if left or right:  # square, triangular or round knob
            base_shape = rect.adjusted(4, 0, -4, 0)
            if not right:
                base_shape.adjust(0, 0, -4, 0)
            path = QtGui.QPainterPath(base_shape.topLeft())
            path.lineTo(base_shape.topRight())
            mid = base_shape.height() / 2
            x, y = to_tuple(base_shape.topRight())
            if right == 2:  # triangle plug
                triangle(path, x, y, mid, -1, 1)
            elif right == -2:  # triangle hole
                triangle(path, x, y, mid, 1, 1)
            elif right == 3:  # square plug
                square(path, x, y, mid, -1, 1)
            elif right == -3:  # square hole
                square(path, x, y, mid, 1, 1)
            elif right == 4:  # roundish plug
                roundish(path, x, y, mid, -1, 1)
            elif right == -4:  # roundish hole
                roundish(path, x, y, mid, 1, 1)
            else:
                path.quadTo(x + 8, y + mid, x, y + mid + mid)
            path.lineTo(base_shape.bottomLeft())
            x, y = to_tuple(base_shape.topLeft())
            if left == 2:  # triangle plug
                triangle(path, x, y, mid, 1, -1)
            elif left == -2:  # triangle hole
                triangle(path, x, y, mid, -1, -1)
            elif left == 3:  # square plug
                square(path, x, y, mid, 1, -1)
            elif left == -3:  # square hole
                square(path, x, y, mid, -1, -1)
            elif left == 4:  # roundish plug
                roundish(path, x, y, mid, 1, -1)
            elif left == -4:  # roundish hole
                roundish(path, x, y, mid, -1, -1)
            else:
                path.quadTo(x - 8, y + mid, x, y)
            painter.fillPath(path, color)
            painter.drawPath(path)
        else:  # solid rect
            painter.drawRect(rect)
        painter.setPen(old_pen)

    def update_label(self):
        super().update_label()
        self.left_shape, self.right_shape = self.get_shape()

    def get_shape(self):
        if self.syntactic_object and hasattr(self.syntactic_object, 'get_shape'):
            return self.syntactic_object.get_shape()
        else:
            left = self.fshape if self.is_valuing() else 0
            right = self.fshape if self.is_needy() or self.is_satisfied() else 0
            return left, right

    def paint(self, painter, option, widget=None):
        """ FeatureNodes can have shapes that suggest which features can value each other.
        :param painter:
        :param option:
        :param widget:
        """
        if self.fshape:
            self.draw_feature_shape(painter, self.inner_rect, self.left_shape, self.right_shape,
                                    self.contextual_color())
        else:
            Node.paint(self, painter, option, widget)

    def get_color_for(self, feature_name):
        if feature_name in self.forest.semantics_manager.colors:
            return self.forest.semantics_manager.colors[feature_name]
        else:
            return 'accent7'

    def get_host_color(self):
        h = self.get_host()
        if h:
            return h.get_lexical_color()

    def get_color_key(self):
        """
        :return:
        """
        if 'color_key' in self._settings:
            ck = self.settings.get('color_key')
        elif hasattr(self.syntactic_object, 'get_color_key'):
            ck = self.syntactic_object.get_color_key()
        elif self.name in self.forest.semantics_manager.colors:
            ck = self.forest.semantics_manager.colors[self.name]
        elif self.name:
            if len(self.name) > 1 and self.name[0] == 'w' and self.name[1] in \
                    string.ascii_uppercase:
                ck = 'content2'
            else:
                c_id = ord(self.name[0]) % 8 + 1
                ck = 'accent' + str(c_id)
        else:
            ck = self.settings.get('color_key')
        if not ck.endswith('tr') and self.syntactic_object.is_inactive():
            ck += 'tr'
        return ck

    def get_special_connection_point(self, sx, sy, ex, ey, start=False, edge_type=''):
        if edge_type == g.FEATURE_EDGE: # not used atm.
            f_align = self.forest.settings.get('feature_positioning')
            br = self.boundingRect()
            left, top, right, bottom = (int(x * .8) for x in br.getCoords())
            if f_align == 0: # direct

                if start:
                    return (sx, sy), BOTTOM_SIDE
                else:
                    return (ex, ey), BOTTOM_SIDE
            elif f_align == 1: # vertical
                if start:
                    if sx < ex:
                        return (sx + right, sy), RIGHT_SIDE
                    else:
                        return (sx + left, sy), LEFT_SIDE
                else:
                    if sx < ex:
                        return (ex + left, ey), LEFT_SIDE
                    else:
                        return (ex + right, ey), RIGHT_SIDE
            elif f_align == 2:  # horizontal
                if start:
                    if sy < ey:
                        return (sx, sy + bottom), BOTTOM_SIDE
                    else:
                        return (sx, sy + top), TOP_SIDE
                else:
                    if sy <= ey:
                        return (ex, ey + top), TOP_SIDE
                    else:
                        return (ex, ey + bottom), BOTTOM_SIDE
            elif f_align == 3:  # card
                if start:
                    return (sx + right, sy), RIGHT_SIDE
                else:
                    return (ex + left, ey), LEFT_SIDE

            if start:
                return (sx, sy), 0
            else:
                return (ex, ey), 0
        elif edge_type == CHECKING_EDGE:
            br = self.boundingRect()
            left, top, right, bottom = (int(x * .8) for x in br.getCoords())
            shape_left, shape_right = self.get_shape()
            if start:
                if shape_left < 0:
                    return (sx + left + 4, sy), LEFT_SIDE  # hole on the left side
                elif shape_right < 0:
                    return (sx + right - 4, sy), RIGHT_SIDE  # hole on the right side
                elif sx < ex:
                    return (sx + right, sy), RIGHT_SIDE
                else:
                    return (sx + left, sy), LEFT_SIDE

            else:
                if shape_left < 0:
                    return (ex + left + 4, ey), LEFT_SIDE  # hole on the left side
                elif shape_right < 0:
                    return (ex + right - 4, ey), RIGHT_SIDE  # hole on the right side
                elif sx < ex:
                    return (ex + left, ey), LEFT_SIDE
                else:
                    return (ex + right, ey), RIGHT_SIDE

    def __str__(self):
        if self.syntactic_object:
            return str(self.syntactic_object)
        s = '✓' if self.checks or self.checked_by else ''
        s += self.sign
        fam = ':' + self.family if self.family else ''
        val = ':' + self.value if self.value else ''
        return s + str(self.name) + val + fam

    def get_edge_start_symbol(self):
        if self.satisfies():
            return EDGE_PLUGGED_IN
        elif self.is_satisfied():
            if self.sign == '=':
                return EDGE_RECEIVING_NOW_DOMINANT
            return EDGE_RECEIVING_NOW
        elif self.is_needy() and not self.syntactic_object.is_inactive():
            if self.sign == '=':
                return EDGE_OPEN_DOMINANT
            return EDGE_OPEN
        elif self.can_satisfy():
            return EDGE_CAN_INSERT
        else:
            return 0

    def compute_piece_width(self, width_function, left, right):
        w = width_function(str(self))
        w += 6
        if left:
            w += 8
        elif right:
            w += 6
        return w

    def update_tooltip(self) -> None:
        """ Hovering status tip """
        synobj = self.syntactic_object
        tt_style = f'<tt style="background:{ctrl.cm.paper2().name()};">%s</tt>'
        ui_style = f'<strong style="color:{ctrl.cm.ui().name()};">%s</tt>'

        lines = ["<strong>FeatureNode:</strong>",
                 f'uid: {tt_style % self.uid}',
                 f'target position: {coords_as_str(self.target_position)}']
        if self.use_adjustment:
            lines.append(f' adjusted position {coords_as_str(self.adjustment)}')

        lines.append("")
        lines.append(f"<strong>Syntactic object: {synobj.__class__.__name__}</strong>")
        lines.append(f"uid: {tt_style % synobj.uid}")
        lines.append(f"name: '{synobj.name}'")
        lines.append(f"sign: '{synobj.sign}'")
        lines.append(f"value: '{synobj.value}' ")
        if self.family:
            lines.append(f"family: '{synobj.family}'")
        host = self.get_host()
        if host:
            lines.append(f"belonging to: '{host}'")

        if synobj.checks:
            lines.append(f"checks: '{synobj.checks}' ({tt_style % synobj.checks.uid})")
        if synobj.checked_by:
            lines.append(f"checked by: '{synobj.checked_by}' "
                         f"({tt_style % synobj.checked_by.uid})")
        lines.append(f"active: {not synobj.is_inactive()}")

        lines.append("")
        if self.selected:
            lines.append(ui_style % 'Click to edit text, drag to move')
        else:
            lines.append(ui_style % 'Click to select, drag to move')

        self.k_tooltip = '<br/>'.join(lines)

    def _start_direct_hover(self):
        super()._start_direct_hover()
        ch = self.checks
        if ch:
            ch.hovering = True
        ch_by = self.checked_by
        if ch_by:
            ch_by.hovering = True
        for edge in self.get_edges_to_me():
            edge.hovering = True

    def _stop_direct_hover(self):
        super()._stop_direct_hover()
        ch = self.checks
        if ch:
            ch.hovering = False
        ch_by = self.checked_by
        if ch_by:
            ch_by.hovering = False
        for edge in self.get_edges_to_me():
            edge.hovering = False

    def hoverEnterEvent(self, event):
        """ When features are joined into one object, deliver hover effects to child if necessary.
        :param event:
        """
        if self.locked_to_node and self.locked_to_node._direct_hovering:
            self.locked_to_node.stop_hovering()
        self.start_hovering()
        if not ctrl.scene_moving:
            ctrl.ui.show_help(self, event)
        event.accept()

    def hoverLeaveEvent(self, event):
        """ Object needs to be updated
        :param event:
        """
        if self._direct_hovering:
            self.stop_hovering()
            ctrl.ui.hide_help(self, event)
        if self.locked_to_node and \
                self.locked_to_node.sceneBoundingRect().contains(event.scenePos()):
            self.locked_to_node.start_hovering()
            if not ctrl.scene_moving:
                ctrl.ui.show_help(self.locked_to_node, event)
        event.accept()
