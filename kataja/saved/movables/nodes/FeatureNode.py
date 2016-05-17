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
from kataja.saved.movables.Node import Node
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
    name = ('Feature', 'Features')
    display = True
    wraps = 'feature'

    visible_in_label = ['fname', 'value', 'family']
    editable_in_label = ['fname', 'value', 'assigned', 'family']
    display_styles = {'fname': {'align': 'continue', 'getter': 'name_with_u_prefix',
                                'delimiter':':', 'syntactic': True},
                      'value': {'align': 'continue', 'syntactic': True},
                      'family': {'align': 'continue', 'syntactic': True}}
    editable = {'fname': dict(name='Name', prefill='name',
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

    default_style = {'fancy': {'color': 'accent2', 'font': g.SMALL_CAPS, 'font-size': 9},
                     'plain': {'color': 'accent2', 'font': g.SMALL_CAPS, 'font-size': 9}}

    default_edge = {'fancy': {'shape_name': 'cubic',
                              'color_id': 'accent2',
                              'pull': .40,
                              'visible': True,
                              'arrowhead_at_start': False,
                              'arrowhead_at_end': False,
                              'labeled': False},
                    'plain': {
                              'shape_name': 'linear',
                              'color_id': 'accent2',
                              'pull': .40,
                              'visible': True,
                              'arrowhead_at_start': False,
                              'arrowhead_at_end': False,
                              'labeled': False},
                    'id': g.FEATURE_EDGE,
                    'name_pl': 'Feature edges'
                    }

    def __init__(self, forest=None, syntactic_object=None):
        Node.__init__(self, syntactic_object=syntactic_object, forest=forest)
        self._gravity = 1

    # implement color() to map one of the d['rainbow_%'] colors here. Or if bw mode is on, then something else.

    @staticmethod
    def create_synobj(label, forest):
        """ FeatureNodes are wrappers for Features. Exact
        implementation/class of feature is defined in ctrl.
        :return:
        """
        if not label:
            label = 'Feature'
        obj = classes.Feature(fname=label)
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
        if edge.edge_type is not g.FEATURE_EDGE:
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

    def disconnect_in_syntax(self, edge):
        """ Implement this if disconnecting this node (using this edge) needs
        to be reflected in syntax. Remember to verify it already isn't there.
        :param edge:
        :return:
        """
        if edge.edge_type is not g.FEATURE_EDGE:
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

    fname = SavedSynField("fname")
    assigned = SavedSynField("assigned")
    value = SavedSynField("value")
    family = SavedSynField("family")
