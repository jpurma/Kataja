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

import kataja.globals as g
from kataja.SavedField import SavedSynField
from kataja.globals import FEATURE_NODE
from kataja.singletons import ctrl, qt_prefs, classes
from kataja.saved.movables.Node import Node, as_html
from kataja.uniqueness_generator import next_available_type_id

color_map = {'tense': 0, 'order': 1, 'person': 2, 'number': 4, 'case': 6, 'unknown': 3}


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
                'assigned': dict(name='Assigned', input_type='checkbox',
                                 select_action='set_assigned_feature',
                                 tooltip="If feature is unassigned ('uFeature') "
                                         "it is looking for a value",
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

    def __init__(self, forest=None, syntactic_object=None):
        Node.__init__(self, syntactic_object=syntactic_object, forest=forest)
        self.repulsion = 0.25
        self._gravity = 2.5
        self.z_value = 60
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
        obj = classes.Feature(name=label)
        obj.after_init()
        return obj

    def compute_start_position(self, host):
        """ Makes features start at somewhat predictable position, if they are of common kinds of features.
        If not, then some random noise is added to prevent features sticking together
        :param host:
        """
        x, y = host.current_position
        k = self.syntactic_object.key
        if k in color_map:
            x += color_map[k]
            y += color_map[k]
        else:
            x += random.uniform(-4, 4)
            y += random.uniform(-4, 4)
        self.set_original_position((x, y))

    def name_with_u_prefix(self):
        return self.syntactic_object.name_with_u_prefix()

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

        parts = [self.name_with_u_prefix()]
        if self.syntactic_object.assigned:
            if self.value:
                parts.append(as_html(self.value))
            if self.family:
                parts.append(as_html(self.family))
        return ':'.join(parts), ''

    def compose_html_for_editing(self):
        """ This is used to build the html when quickediting a label. It should reduce the label
        into just one field value that is allowed to be edited, in constituentnode this is
        either label or display_label. This can be overridden in syntactic object by having
        'compose_html_for_editing' -method there. The method returns a tuple,
          (field_name, html).
        :return:
        """

        # Allow custom syntactic objects to override this
        if hasattr(self.syntactic_object, 'compose_html_for_editing'):
            return self.syntactic_object.compose_html_for_editing(self)

        return self.compose_html_for_viewing()

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



    def update_relations(self):
        for parent in self.get_parents(similar=False, visible=False):
            if parent.node_type == g.CONSTITUENT_NODE:
                if parent.is_visible():
                    self.locked_to_node = parent
                    break
                else:
                    self.locked_to_node = None
            elif parent.node_type == g.FEATURE_NODE:
                if self.locked_to_node == parent:
                    self.locked_to_node = None
        super().update_relations()

    def paint(self, painter, option, widget=None):
        """ Painting is sensitive to mouse/selection issues, but usually with
        :param painter:
        :param option:
        :param widget:
        nodes it is the label of the node that needs complex painting """
        if ctrl.pressed == self or self._hovering or ctrl.is_selected(self):
            painter.setPen(ctrl.cm.get('background1'))
            painter.setBrush(self.contextual_background())
            painter.drawRoundedRect(self.inner_rect, 5, 5)
        Node.paint(self, painter, option, widget)

    @property
    def contextual_color(self):
        """ Drawing color that is sensitive to node's state """
        if ctrl.pressed == self:
            return ctrl.cm.get('background1')
        elif self._hovering:
            return ctrl.cm.get('background1')
        elif ctrl.is_selected(self):
            return ctrl.cm.get('background1')
            # return ctrl.cm.selected(ctrl.cm.selection())
        else:
            if getattr(self.syntactic_object, 'unvalued', False):  # fixme: Temporary hack
                return ctrl.cm.get('accent1')
            else:
                return self.color

    def contextual_background(self):
        """ Background color that is sensitive to node's state """
        if ctrl.pressed == self:
            return ctrl.cm.active(ctrl.cm.selection())
        elif self._hovering:
            return ctrl.cm.hovering(ctrl.cm.selection())
        elif ctrl.is_selected(self):
            return ctrl.cm.selection()
            # return ctrl.cm.selected(ctrl.cm.selection())
        else:
            return qt_prefs.no_brush()

    def connect_in_syntax(self, edge):
        """ Implement this if connecting this node (using this edge) needs to be
         reflected in syntax. Remember to verify it already isn't there.
        :param edge:
        :return:
        """
        if edge.edge_type is not g.FEATURE_EDGE:  # fixme: include CHECKING_EDGE
            # We care only for constituent relations
            return
        assert edge.end is self
        s = edge.start
        if s and s.node_type == g.CONSTITUENT_NODE and s.syntactic_object:
            # Calling syntax!
            constituent = s.syntactic_object
            feature = self.syntactic_object
            if not constituent.has_feature(feature):
                constituent.add_feature(feature)
                print('have to add feature')
                raise hell

    def disconnect_in_syntax(self, edge):
        """ Implement this if disconnecting this node (using this edge) needs
        to be reflected in syntax. Remember to verify it already isn't there.
        :param edge:
        :return:
        """
        if edge.edge_type is not g.FEATURE_EDGE:  # fixme: include CHECKING_EDGE
            # We care only for constituent relations
            return
        assert edge.end is self
        s = edge.start
        if s and s.node_type == g.CONSTITUENT_NODE and s.syntactic_object:
            # Calling syntax!
            constituent = s.syntactic_object
            feature = self.syntactic_object
            if constituent.has_feature(feature):
                constituent.remove_feature(feature)

    def set_assigned(self, value):
        self.assigned = value

    def __str__(self):
        return 'feature %s' % self.syntactic_object

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    name = SavedSynField("name")
    assigned = SavedSynField("assigned")
    value = SavedSynField("value")
    family = SavedSynField("family")
