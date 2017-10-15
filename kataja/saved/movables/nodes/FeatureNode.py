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

import itertools
from PyQt5 import QtGui, QtCore

import kataja.globals as g
from kataja.SavedField import SavedField
from kataja.globals import FEATURE_NODE
from kataja.singletons import ctrl, qt_prefs
from kataja.saved.movables.Node import Node
from kataja.uniqueness_generator import next_available_type_id
from kataja.EdgePath import TOP_SIDE, BOTTOM_SIDE, LEFT_SIDE, RIGHT_SIDE
from kataja.utils import to_tuple

color_map = {'tense': 'accent7',
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
             'c': 'accent7',
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
    display = True
    wraps = 'feature'

    editable = {'name': dict(name='Name', prefill='name',
                             tooltip='Name of the feature, used as identifier',
                             syntactic=True),
                'value': dict(name='Value',
                              prefill='value',
                              tooltip='Value given to this feature',
                              syntactic=True),
                'family': dict(name='Family', prefill='family',
                               tooltip='Several distinct features can be '
                                       'grouped under one family (e.g. '
                                       'phi-features)',
                               syntactic=True)
                }

    default_style = {'fancy': {'color_id': 'accent2', 'font_id': g.SMALL_CAPS, 'font-size': 9,
                               'visible': True},
                     'plain': {'color_id': 'accent2', 'font_id': g.SMALL_CAPS, 'font-size': 9,
                               'visible': True}}

    default_edge = g.FEATURE_EDGE

    def __init__(self, label='', value='', family=''):
        Node.__init__(self)
        self.name = label
        self.value = value
        self.family = family
        self.repulsion = 0.25
        self._gravity = 3.0
        self.z_value = 60
        self.fshape = 2
        self.setZValue(self.z_value)

        # implement color() to map one of the d['rainbow_%'] colors here. Or if bw mode is on, then something else.

    @staticmethod
    def create_synobj(label, forest):
        """ FeatureNodes are wrappers for Features. Exact
        implementation/class of feature is defined in ctrl.
        :return:
        """
        if not label:
            label = 'Feature'
        obj = ctrl.syntax.Feature(name=label)
        obj.after_init()
        return obj

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

    def compose_html_for_viewing(self):
        """ This method builds the html to display in label. For convenience, syntactic objects
        can override this (going against the containment logic) by having their own
        'compose_html_for_viewing' -method. This is so that it is easier to create custom
        implementations for constituents without requiring custom constituentnodes.

        Note that synobj's compose_html_for_viewing receives the node object as parameter,
        so you can replicate the behavior below and add your own to it.
        :return:
        """

        # Allow custom syntactic objects to override this
        if hasattr(self.syntactic_object, 'compose_html_for_viewing'):
            return self.syntactic_object.compose_html_for_viewing(self)
        return str(self), ''

    def compose_html_for_editing(self):
        """ This is used to build the html when quickediting a label. It should reduce the label
        into just one field value that is allowed to be edited, in constituentnode this is
        either label synobj's label. This can be overridden in syntactic object by having
        'compose_html_for_editing' -method there. The method returns a tuple,
          (field_name, html).
        :return:
        """

        # Allow custom syntactic objects to override this
        if hasattr(self.syntactic_object, 'compose_html_for_editing'):
            return self.syntactic_object.compose_html_for_editing(self)

        return 'name', self.compose_html_for_viewing()[0]

    def parse_quick_edit(self, text):
        """ This is an optional method for node to parse quick edit information into multiple
        fields. Usually nodes do without this: quickediting only changes one field at a time and
        interpretation is straightforward. E.g. features can have more complex parsing.
        :param text:
        :return:
        """
        if hasattr(self.syntactic_object, 'parse_quick_edit'):
            return self.syntactic_object.parse_quick_edit(self, text)
        parts = text.split(':')
        name = ''
        value = ''
        family = ''
        if len(parts) >= 3:
            name, value, family = parts
        elif len(parts) == 2:
            name, value = parts
        elif len(parts) == 1:
            name = parts[0]
        if len(name) > 1 and name.startswith('u') and name[1].isupper():
            name = name[1:]
        self.name = name
        self.value = value
        self.family = family

    def hidden_in_triangle(self):
        """ If features are folded into triangle, they are always hidden. 
        :return: 
        """
        return bool(self.triangle_stack)

    def my_checking_feature(self):
        for edge in self.edges_up:
            if edge.edge_type == g.CHECKING_EDGE:
                return edge.start

    def update_relations(self, parents, shape=None, position=None, checking_mode=None):
        """ Cluster features according to feature_positioning -setting or release them to be
        positioned according to visualisation.
        'locked_to_node' is the essential attribute in here. For features it should have two 
        kinds of values or None: 
        1: locked to parent constituent node -- this is used to arrange features neatly below node.
        2: locked to another feature -- this is used to show feature checking
        the third option shouldn't happen:
        3: locked to triangle host like constituent nodes are locked to triangle host 
        
        :param parents: list where we collect parent objects that need to position their children
        :param shape:
        :param position:
        :param checking_mode:
        :return:
        """

        if shape is None:
            shape = ctrl.settings.get('node_shape')
        if position is None:
            position = ctrl.settings.get('feature_positioning')
        if checking_mode is None:
            checking_mode = ctrl.settings.get('feature_check_display')
        checked_by = self.my_checking_feature()
        # First see if feature should be attached to another feature
        locked_to_another_feature = False
        if checked_by and self.is_visible():
            if checking_mode == g.NO_CHECKING_EDGE:
                for parent in self.get_parents(similar=False, visible=True):
                    if parent.node_type == g.CONSTITUENT_NODE:
                        parents.append(parent)
                if self.locked_to_node == checked_by:
                    self.release_from_locked_position()
                edge = self.get_edge_to(checked_by, g.CHECKING_EDGE)
                edge.hide()

            elif checking_mode == g.PUT_CHECKED_TOGETHER:
                locked_to_another_feature = True
                if self.locked_to_node != checked_by:
                    x = checked_by.future_children_bounding_rect().right() - \
                        self.future_children_bounding_rect().x() - 8
                    self.lock_to_node(checked_by, move_to=(x, 0))
                    for parent in self.get_parents(similar=False, visible=True):
                        if parent.node_type == g.CONSTITUENT_NODE:
                            parents.append(parent)
            elif checking_mode == g.SHOW_CHECKING_EDGE and self.locked_to_node == checked_by:
                for parent in self.get_parents(similar=False, visible=True):
                    if parent.node_type == g.CONSTITUENT_NODE:
                        parents.append(parent)
                self.release_from_locked_position()
        # Then see if it should be fixed to its parent constituent node
        if not locked_to_another_feature:
            if position or shape == g.CARD:
                for parent in self.get_parents(similar=False, visible=False):
                    if parent.node_type == g.CONSTITUENT_NODE:
                        if parent.is_visible():
                            self.lock_to_node(parent)
                            parents.append(parent)
                            break
                        else:
                            self.release_from_locked_position()
                    #elif parent.node_type == g.FEATURE_NODE:
                    #    if self.locked_to_node == parent:
                    #        self.release_from_locked_position()
            else:
                self.release_from_locked_position()

    def is_needy(self):
        if self.syntactic_object:
            return self.syntactic_object.is_needy()
        else:
            # These are defaults
            return (not self.value) or self.value == 'u' or self.value == '=' or self.value == '-'

    def valuing(self):
        if self.syntactic_object:
            return not (self.syntactic_object.unvalued() or self.syntactic_object.checked_by)
        else:
            return self.value != 'u' and self.value != '=' and self.value != '-'

    def can_satisfy(self):
        if self.syntactic_object:
            return self.syntactic_object.can_satisfy()
        else:
            return self.value and self.value != 'u' and self.value != '=' and self.value != '-'

    def is_satisfied(self):
        if self.syntactic_object:
            return self.syntactic_object.checked_by
        else:
            return ('u' in self.value or '=' in self.value) and '✓' in self.value

    def satisfies(self):
        if self.syntactic_object:
            return self.syntactic_object.checks
        else:
            return '✓' in self.value and not ('u' in self.value or '=' in self.value)

    def update_bounding_rect(self):
        """ Override Node's update_bounding_rect because FeatureNodes have special shapes that 
        need to be accounted in their bounding rect
        :return:
        """
        lbw = FeatureNode.width
        lbh = FeatureNode.height
        lbx = 0
        lby = 0
        x_offset = 0
        y_offset = 0
        if self._label_visible and self.label_object:
            l = self.label_object
            lbr = l.boundingRect()
            lbw = max((lbr.width(), lbw))
            lbh = max((lbr.height(), lbh))
            lbx = l.x()
            lby = l.y()
            x_offset = l.x_offset
            y_offset = l.y_offset
        self.label_rect = QtCore.QRectF(lbx, lby, lbw, lbh)
        if 1 < self.fshape < 4:
            lbw += 4
        elif self.fshape == 4:
            lbw += 6
        if x_offset or y_offset:
            x = x_offset
            y = y_offset
        else:
            x = lbw / -2
            y = lbh / -2
        self.inner_rect = QtCore.QRectF(x, y, lbw, lbh)
        w4 = (lbw - 2) / 4.0
        w2 = (lbw - 2) / 2.0
        h2 = (lbh - 2) / 2.0
        y_max = y + lbh - 4
        x_max = x + lbw
        self._magnets = [(x, y), (x + w4, y), (x + w2, y), (x + w2 + w4, y), (x_max, -y),
                         (x, y + h2), (x_max, y + h2),
                         (x, y_max), (x + w4, y_max), (x + w2, y_max),
                         (x + w2 + w4, y_max), (x_max, y_max)]
        self.width = lbw
        self.height = lbh

        expanding_rect = self.inner_rect
        for child in self.childItems():
            if isinstance(child, Node):
                c_br = QtCore.QRectF(child.future_children_bounding_rect())
                ox = c_br.left()
                oy = c_br.top()
                x, y = child.target_position
                c_br.moveTo(x + ox, y + oy)
                expanding_rect = expanding_rect.united(c_br)
        self._cached_child_rect = expanding_rect
        if ctrl.ui.selection_group and self in ctrl.ui.selection_group.selection:
            ctrl.ui.selection_group.update_shape()
        return self.inner_rect

    def paint(self, painter, option, widget=None):
        """ FeatureNodes can have shapes that suggest which features can value each other.
        :param painter:
        :param option:
        :param widget:
        """

        if self.fshape:
            #painter.setPen(ctrl.cm.get('background1'))
            #b = self.contextual_background()
            #painter.setBrush(b)
            painter.setPen(QtCore.Qt.NoPen)
            if self.fshape == 1:  # solid rect
                painter.drawRect(self.inner_rect)
            elif self.fshape > 1:  # square, triangular or round knob
                base_shape = self.inner_rect.adjusted(4, 0, 0, 0)
                knob_at_left = self.valuing()
                hole_at_right = self.is_needy() or self.is_satisfied()
                if not hole_at_right:
                    base_shape.adjust(0, 0, -4, 0)

                path = QtGui.QPainterPath(base_shape.topLeft())
                path.lineTo(base_shape.topRight())
                mid = base_shape.height() / 2
                x, y = to_tuple(base_shape.topRight())
                if hole_at_right:
                    if self.fshape == 2:  # triangle
                        path.lineTo(x, y + mid - 4)
                        path.lineTo(x - 4, y + mid)
                        path.lineTo(x, y + mid + 4)
                        path.lineTo(x, y + mid + mid)
                    elif self.fshape == 3:  # square
                        path.lineTo(x, y + mid - 4)
                        path.lineTo(x - 4, y + mid - 4)
                        path.lineTo(x - 4, y + mid + 4)
                        path.lineTo(x, y + mid + 4)
                        path.lineTo(x, y + mid + mid)
                    elif self.fshape == 4:  # roundish
                        path.lineTo(x, y + mid - 2)
                        path.cubicTo(x - 3, y + mid - 2, x - 3, y + mid - 6, x - 6, y + mid)
                        path.cubicTo(x - 3, y + mid + 6, x - 3, y + mid + 2, x, y + mid + 2)
                        path.lineTo(x, y + mid + mid)
                else:
                    path.quadTo(x + 8, y + mid, x, y + mid + mid)
                path.lineTo(base_shape.bottomLeft())
                x, y = to_tuple(base_shape.topLeft())
                if knob_at_left:
                    if self.fshape == 2:  # triangle
                        path.lineTo(x, y + mid + 4)
                        path.lineTo(x - 4, y + mid)
                        path.lineTo(x, y + mid - 4)
                        path.lineTo(x, y)
                    elif self.fshape == 3:  # square
                        path.lineTo(x, y + mid + 4)
                        path.lineTo(x - 4, y + mid + 4)
                        path.lineTo(x - 4, y + mid - 4)
                        path.lineTo(x, y + mid - 4)
                        path.lineTo(x, y)
                    elif self.fshape == 4:  # roundish
                        path.lineTo(x, y + mid + 2)
                        path.cubicTo(x - 3, y + mid + 2, x - 3, y + mid + 6, x - 6, y + mid)
                        path.cubicTo(x - 3, y + mid - 6, x - 3, y + mid - 2, x, y + mid - 2)
                        path.lineTo(x, y)
                else:
                    path.quadTo(x - 8, y + mid, x, y)
                painter.fillPath(path, self.contextual_background())
                painter.setPen(self.contextual_color())
        else:
            Node.paint(self, painter, option, widget)

    @staticmethod
    def get_color_for(feature_name):
        if feature_name in ctrl.forest.semantics_manager.colors:
            return ctrl.forest.semantics_manager.colors[feature_name]
        else:
            return 'accent7'

    def get_color_id(self):
        """
        :return:
        """
        if 'color_id' in self.settings:
            return self.settings['color_id']
        elif self.name in ctrl.forest.semantics_manager.colors:
            return ctrl.forest.semantics_manager.colors[self.name]
        elif self.name:
            c_id = ord(self.name[0]) % 8 + 1
            return 'accent' + str(c_id)
        else:
            return ctrl.settings.get_node_setting('color_id', node=self)

    def contextual_color(self):
        """ Drawing color that is sensitive to node's state """
        if self.fshape:
            return ctrl.cm.get('background1')
        else:
            if 'color_id' in self.settings:
                c = ctrl.cm.get(self.settings['color_id'])
            elif self.name in ctrl.forest.semantics_manager.colors:
                c = ctrl.cm.get(
                    ctrl.forest.semantics_manager.colors[self.name])
            elif self.name:
                c_id = ord(self.name[0]) % 8 + 1
                c = ctrl.cm.get('accent' + str(c_id))
            if ctrl.pressed == self:
                return ctrl.cm.active(c)
            elif self.drag_data or self._hovering:
                return ctrl.cm.hovering(c)
            elif ctrl.is_selected(self):
                return ctrl.cm.active(c)
                #return ctrl.cm.selection()

    def contextual_background(self):
        """ Background color that is sensitive to node's state """
        if self.fshape:
            if 'color_id' in self.settings:
                c = ctrl.cm.get(self.settings['color_id'])
            elif self.name in ctrl.forest.semantics_manager.colors:
                c = ctrl.cm.get(
                    ctrl.forest.semantics_manager.colors[self.name])
            elif self.name:
                c_id = ord(self.name[0]) % 8 + 1
                c = ctrl.cm.get('accent' + str(c_id))
            if ctrl.pressed == self:
                return ctrl.cm.active(c)
            elif self.drag_data or self._hovering:
                return ctrl.cm.hovering(c)
            elif ctrl.is_selected(self):
                return ctrl.cm.active(c)
            else:
                return c
        else:
            if ctrl.pressed == self:
                return ctrl.cm.active(ctrl.cm.selection())
            elif self.drag_data or self._hovering:
                return ctrl.cm.hovering(ctrl.cm.selection())
            elif ctrl.is_selected(self):
                return ctrl.cm.selection()
            else:
                return qt_prefs.no_brush

    def special_connection_point(self, sx, sy, ex, ey, start=False, edge_type=''):
        if edge_type == g.FEATURE_EDGE: # not used atm.
            f_align = ctrl.settings.get('feature_positioning')
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
        elif edge_type == g.CHECKING_EDGE:
            br = self.boundingRect()
            left, top, right, bottom = (int(x * .8) for x in br.getCoords())
            if start:
                return (sx + right, sy), RIGHT_SIDE
            else:
                return (ex + left, ey), LEFT_SIDE

    def __str__(self):
        if self.syntactic_object:
            return str(self.syntactic_object)
        s = []
        signs = ('+', '-', '=', 'u', '✓')
        if self.value and (len(self.value) == 1 and self.value in signs or len(self.value) == 2 and self.value[1] in signs):
            s.append(self.value + str(self.name))
        elif self.value or self.family:
            s.append(str(self.name))
            s.append(str(self.value))
            if self.family:
                s.append(str(self.family))
        else:
            s.append(str(self.name))
        return ":".join(s)

    def get_edge_start_symbol(self):
        if self.satisfies():
            return 4
        elif self.is_satisfied():
            return 3
        elif self.is_needy():
            return 2
        elif self.can_satisfy():
            return 5
        else:
            return 0

    def update_tooltip(self) -> None:
        """ Hovering status tip """
        tt_style = f'<tt style="background:{ctrl.cm.paper2().name()};">%s</tt>'
        ui_style = f'<strong style="color:{ctrl.cm.ui().name()};">%s</tt>'

        lines = []
        lines.append("<strong>Feature:</strong>")
        lines.append(f" name: {self.name} value: {self.value} ")
        if self.family:
            lines.append(f"family: {self.family}")
        lines.append("")
        lines.append(f"<i>uid: {self.uid}</i>")
        lines.append(f"synobj: {self.syntactic_object}")
        lines.append("")
        if self.selected:
            lines.append(ui_style % 'Click to edit text, drag to move')
        else:
            lines.append(ui_style % 'Click to select, drag to move')

        self.k_tooltip = '<br/>'.join(lines)

    def get_host(self):
        for parent in self.get_parents(of_type=g.CONSTITUENT_NODE):
            return parent

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    name = SavedField("name")
    value = SavedField("value")
    family = SavedField("family")
