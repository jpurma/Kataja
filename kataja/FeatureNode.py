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
from kataja.BaseModel import Synobj
from kataja.globals import FEATURE_EDGE, FEATURE_NODE
from kataja.Node import Node
from kataja.singletons import ctrl, qt_prefs
from kataja.parser.INodes import IFeatureNode
import kataja.globals as g


color_map = {'tense': 0, 'order': 1, 'person': 2, 'number': 4, 'case': 6, 'unknown': 3}


class FeatureNode(Node):
    """
    Node to express a feature of a constituent
    """
    width = 20
    height = 20
    default_edge_type = FEATURE_EDGE
    node_type = FEATURE_NODE
    short_name = "FN"

    default_style = {'color': 'accent2', 'font': g.SMALL_CAPS, 'font-size': 9,
                     'edge': g.FEATURE_EDGE}

    default_edge = {'id': g.FEATURE_EDGE, 'shape_name': 'cubic', 'color': 'accent2', 'pull': .40,
                    'visible': True, 'arrowhead_at_start': False, 'arrowhead_at_end': False,
                    'labeled': False}


    def __init__(self, feature=None):
        Node.__init__(self, syntactic_object=feature)
        self._gravity = 1

    def after_init(self):
        """ After_init is called in 2nd step in process of creating objects:
            1st wave creates the objects and calls __init__, and then iterates through and sets the values.
            2nd wave calls after_inits for all created objects. Now they can properly refer to each other and know their
                values.
        :return: None
        """
        self.update_label()
        self.update_bounding_rect()
        self.update_visibility()
        self.announce_creation()
        ctrl.forest.store(self)

    @property
    def as_inode(self):
        """
        :return: INodes or str or tuple of them
        """
        if self._inode_changed:
            self._inode = IFeatureNode(key=self.key, value=self.value, family=self.family)
            self._inode_changed = False
        return self._inode

    # implement color() to map one of the d['rainbow_%'] colors here. Or if bw mode is on, then something else.

    def compute_start_position(self, host):
        """ Makes features start at somewhat predictable position, if they are of common kinds of features.
        If not, then some random noise is added to prevent features sticking together
        :param host:
        """
        x, y, z = host.current_position
        k = self.syntactic_object.key
        if k in color_map:
            x += color_map[k]
            y += color_map[k]
        else:
            x += random.uniform(-4, 4)
            y += random.uniform(-4, 4)
        self.set_original_position((x, y, z))

    def update_label(self):
        """

        :return:
        """
        Node.update_label(self)
        self._label_complex.show()


    # def get_html_for_label(self):
    #     """ This should be overridden if there are alternative displays for label """
    #     f = self.syntactic_object
    #     if not f:
    #         return 'orphaned feature node'
    #     if f.key in color_map:
    #         return str(f.get_value_string())
    #     else:
    #         return str(f)
    #         # u'%s:%s' % (self.syntactic_object.key, self.syntactic_object.get_value_string())

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

    def __str__(self):
        return 'feature %s' % self.syntactic_object

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    key = Synobj("key", if_changed=Node.alert_inode)
    value = Synobj("value", if_changed=Node.alert_inode)
    family = Synobj("family", if_changed=Node.alert_inode)
