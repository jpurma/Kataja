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
from PyQt5 import QtGui, QtCore

import kataja.globals as g
from kataja.SavedField import SavedField
from kataja.globals import FEATURE_NODE
from kataja.singletons import ctrl, qt_prefs
from kataja.saved.movables.Node import Node
from kataja.uniqueness_generator import next_available_type_id
from kataja.saved.Edge import TOP_SIDE, BOTTOM_SIDE, LEFT_SIDE, RIGHT_SIDE
from kataja.utils import to_tuple

color_map = {'tense': 'accent0',
             'order': 'accent1',
             'person': 'accent2',
             'number': 'accent4',
             'case': 'accent6',
             'unknown': 'accent3',
             'N': 'accent1',
             'D': 'accent2',
             'V': 'accent3',
             'T': 'accent4',
             'C': 'accent7',
             'wh': 'accent6'
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

    default_style = {'fancy': {'color_id': 'accent2', 'font_id': g.SMALL_CAPS, 'font-size': 9},
                     'plain': {'color_id': 'accent2', 'font_id': g.SMALL_CAPS, 'font-size': 9}}

    default_edge = g.FEATURE_EDGE

    def __init__(self, label='', value='', family=''):
        Node.__init__(self)
        self.name = label
        self.value = value
        self.family = family
        self.repulsion = 0.25
        self._gravity = 2.5
        self.z_value = 60
        self.fshape = 3
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

    def update_relations(self, parents, shape=None, position=None):
        """ Cluster features according to feature_positioning -setting or release them to be
        positioned according to visualisation.
        :param parents: list where we collect parent objects that need to position their children
        :return:
        """

        if shape is None:
            shape = ctrl.settings.get('label_shape')
        if position is None:
            position = ctrl.settings.get('feature_positioning')
        if position or shape == g.CARD:
            for parent in self.get_parents(similar=False, visible=False):
                if parent.node_type == g.CONSTITUENT_NODE:
                    if parent.is_visible():
                        self.lock_to_node(parent)
                        parents.append(parent)
                        break
                    else:
                        self.release_from_locked_position()
                elif parent.node_type == g.FEATURE_NODE:
                    if self.locked_to_node == parent:
                        self.release_from_locked_position()
        else:
            self.release_from_locked_position()

    def unassigned(self):
        if self.syntactic_object:
            return self.syntactic_object.is_unassigned()
        else:
            return (not self.value) or self.value == 'u' or self.value == '='

    def can_assign(self):
        if self.syntactic_object:
            return self.syntactic_object.can_assign()
        else:
            return self.value and self.value != 'u' and self.value != '='


    def paint(self, painter, option, widget=None):
        """ Painting is sensitive to mouse/selection issues, but usually with
        :param painter:
        :param option:
        :param widget:
        nodes it is the label of the node that needs complex painting """
        #if ctrl.pressed == self or self._hovering or ctrl.is_selected(self):
        #    painter.setPen(ctrl.cm.get('background1'))
        #    painter.setBrush(self.contextual_background())
        #    #painter.drawRoundedRect(self.inner_rect, 5, 5)

        if self.fshape:
            #painter.setPen(ctrl.cm.get('background1'))
            #b = self.contextual_background()
            #painter.setBrush(b)
            painter.setPen(QtCore.Qt.NoPen)
            if self.fshape == 1:  # solid rect
                painter.drawRect(self.inner_rect)
            elif self.fshape > 1:  # square, triangular or round knob
                base_shape = self.inner_rect.adjusted(4, 0, 2, 0)
                knob_at_left = self.can_assign()
                hole_at_right = self.unassigned()
                if not hole_at_right:
                    base_shape.adjust(0, 0, -4, 0)

                path = QtGui.QPainterPath(base_shape.topLeft())
                path.lineTo(base_shape.topRight())
                mid = base_shape.height() / 2
                x, y = to_tuple(base_shape.topRight())
                if hole_at_right:
                    if self.fshape == 1:  # triangle
                        path.lineTo(x, y + mid - 4)
                        path.lineTo(x - 4, y + mid)
                        path.lineTo(x, y + mid + 4)
                        path.lineTo(x, y + mid + mid)
                    elif self.fshape == 2:  # square
                        path.lineTo(x, y + mid - 4)
                        path.lineTo(x - 4, y + mid - 4)
                        path.lineTo(x - 4, y + mid + 4)
                        path.lineTo(x, y + mid + 4)
                        path.lineTo(x, y + mid + mid)
                    elif self.fshape == 3:  # roundish
                        path.lineTo(x, y + mid - 2)
                        path.cubicTo(x - 3, y + mid - 2, x - 3, y + mid - 6, x - 6, y + mid)
                        path.cubicTo(x - 3, y + mid + 6, x - 3, y + mid + 2, x, y + mid + 2)
                        path.lineTo(x, y + mid + mid)
                else:
                    path.quadTo(x + 8, y + mid, x, y + mid + mid)
                path.lineTo(base_shape.bottomLeft())
                x, y = to_tuple(base_shape.topLeft())
                if knob_at_left:
                    if self.fshape == 1:  # triangle
                        path.lineTo(x, y + mid + 4)
                        path.lineTo(x - 4, y + mid)
                        path.lineTo(x, y + mid - 4)
                        path.lineTo(x, y)
                    elif self.fshape == 2:  # square
                        path.lineTo(x, y + mid + 4)
                        path.lineTo(x - 4, y + mid + 4)
                        path.lineTo(x - 4, y + mid - 4)
                        path.lineTo(x, y + mid - 4)
                        path.lineTo(x, y)
                    elif self.fshape == 3:  # roundish
                        path.lineTo(x, y + mid + 2)
                        path.cubicTo(x - 3, y + mid + 2, x - 3, y + mid + 6, x - 6, y + mid)
                        path.cubicTo(x - 3, y + mid - 6, x - 3, y + mid - 2, x, y + mid - 2)
                        path.lineTo(x, y)
                else:
                    path.quadTo(x - 8, y + mid, x, y)
                painter.fillPath(path, self.contextual_background())
                painter.setPen(self.contextual_color)
        else:
            Node.paint(self, painter, option, widget)


    def get_color_id(self):
        """
        :return:
        """
        return ctrl.settings.get_node_setting('color_id', node=self)

    @property
    def contextual_color(self):
        """ Drawing color that is sensitive to node's state """
        if self.fshape:
            return ctrl.cm.get('background1')
        else:
            if 'color_id' in self.settings:
                c = ctrl.cm.get(self.settings['color_id'])
            elif self.name in color_map:
                c = ctrl.cm.get(color_map[self.name])
            elif self.unassigned():
                c = ctrl.cm.get('accent1')
            else:
                print('feature name "%s" missing default color' % self.name)
                c = self.color
            if ctrl.pressed == self:
                return ctrl.cm.active(c)
            elif self.drag_data:
                return ctrl.cm.hovering(c)
            elif self._hovering:
                return ctrl.cm.hovering(c)
            elif ctrl.is_selected(self):
                return ctrl.cm.selection()
                #return ctrl.cm.selection()

    def contextual_background(self):
        """ Background color that is sensitive to node's state """
        if self.fshape:
            if 'color_id' in self.settings:
                c = ctrl.cm.get(self.settings['color_id'])
            elif self.name in color_map:
                c = ctrl.cm.get(color_map[self.name])
            elif self.unassigned():
                c = ctrl.cm.get('accent1')
            else:
                print('feature name "%s" missing default color' % self.name)
                c = self.color
            if ctrl.pressed == self:
                return ctrl.cm.active(c)
            elif self.drag_data:
                return ctrl.cm.hovering(c)
            elif self._hovering:
                return ctrl.cm.hovering(c)
            elif ctrl.is_selected(self):
                return ctrl.cm.selection()
            else:
                return c
        else:
            if ctrl.pressed == self:
                return ctrl.cm.active(ctrl.cm.selection())
            elif self.drag_data:
                return ctrl.cm.hovering(ctrl.cm.selection())
            elif self._hovering:
                return ctrl.cm.hovering(ctrl.cm.selection())
            elif ctrl.is_selected(self):
                return ctrl.cm.selection()
            else:
                return qt_prefs.no_brush

    def special_connection_point(self, sx, sy, ex, ey, start=False):
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

    def __str__(self):
        if self.syntactic_object:
            return str(self.syntactic_object)
        s = []
        signs = ('+', '-', '=', 'u', '✓')
        if self.value and (len(self.value) == 1 and self.value in signs or \
           len(self.value) == 2 and self.value[1] in signs):
            s.append(self.value + str(self.name))
        elif self.value or self.family:
            s.append(str(self.name))
            s.append(str(self.value))
            if self.family:
                s.append(str(self.family))
        else:
            s.append(str(self.name))
        return ":".join(s)

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    name = SavedField("name")
    value = SavedField("value")
    family = SavedField("family")
