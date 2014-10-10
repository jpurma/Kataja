# -*- coding: UTF-8 -*-
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

from kataja.globals import *
from shapes import SHAPE_PRESETS

ONLY_LEAF_LABELS = 0
ALL_LABELS = 1
ALIASES = 2


class ForestSettings:
    """

    """
    saved_fields = 'all'
    saved_fields_ignore = 'prefs'
    # saved_fields_ignore_None = True

    """ Settings that affect trees in one forest in a form that can be easily pickled """

    def __init__(self, host, prefs):
        self.prefs = prefs
        if host:
            self.save_key = host.save_key + '_settings'
        # ## General settings for Forest
        self._label_style = None
        self._uses_multidomination = None
        self._traces_are_grouped_together = None
        self._show_constituent_edges = None
        self._show_merge_order = None
        self._show_select_order = None
        self._draw_features = None
        self._draw_width = None
        self._hsv = None
        self._color_mode = None
        self._last_key_colors = {}
        self._bracket_style = None
        # ## Edges - take edge type as argument ###########################
        self._edge_types = {CONSTITUENT_EDGE: {}, FEATURE_EDGE: {}, GLOSS_EDGE: {}, ARROW: {}, PROPERTY_EDGE: {},
                            ABSTRACT_EDGE: {}, ATTRIBUTE_EDGE: {}}
        # ## Nodes - take node type as argument ###########################
        self._node_types = {ABSTRACT_NODE: {}, CONSTITUENT_NODE: {}, FEATURE_NODE: {}, ATTRIBUTE_NODE: {},
                            PROPERTY_NODE: {}, GLOSS_NODE: {}}

    def after_restore(self, values=None):
        """

        :param values:
        :return:
        """
        if not values:
            values = {}
        return


    def label_style(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._label_style is None:
                return self.prefs.default_label_style
            else:
                return self._label_style
        else:
            self._label_style = value

    def uses_multidomination(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._uses_multidomination is None:
                return self.prefs.default_use_multidomination
            else:
                return self._uses_multidomination
        else:
            self._uses_multidomination = value

    def traces_are_grouped_together(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._traces_are_grouped_together is None:
                return self.prefs.default_traces_are_grouped_together
            else:
                return self._traces_are_grouped_together
        else:
            self._traces_are_grouped_together = value

    def shows_constituent_edges(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._show_constituent_edges is None:
                return self.prefs.default_show_constituent_edges
            else:
                return self._show_constituent_edges
        else:
            self._show_constituent_edges = value

    def shows_merge_order(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._show_merge_order is None:
                return self.prefs.default_show_merge_order
            else:
                return self._show_merge_order
        else:
            self._show_merge_order = value

    def shows_select_order(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._show_select_order is None:
                return self.prefs.default_show_select_order
            else:
                return self._show_select_order
        else:
            self._show_select_order = value

    def draw_features(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._draw_features is None:
                return self.prefs.default_draw_features
            else:
                return self._draw_features
        else:
            self._draw_features = value

    def draw_width(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._draw_width is None:
                return self.prefs.default_draw_width
            else:
                return self._draw_width
        else:
            self._draw_width = value

    def hsv(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._hsv is None:
                return self.prefs.default_hsv
            else:
                return self._hsv
        else:
            self._hsv = value

    def bracket_style(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._bracket_style is None:
                return self.prefs.default_bracket_style
            else:
                return self._bracket_style
        else:
            self._bracket_style = value

    def last_key_color_for_mode(self, mode_key, value=None):
        """

        :param mode_key:
        :param value:
        :return:
        """
        if value is None:
            return self._last_key_colors.get(mode_key, None)
        else:
            self._last_key_colors[mode_key] = value


    def color_mode(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._color_mode is None:
                return self.prefs.color_mode
            else:
                return self._color_mode
        else:
            self._color_mode = value

    # ## Edges - all require edge type as argument, value is stored in dict ###########

    def edge_type_settings(self, edge_type, key, value=None):
        """ Getter/setter for settings related to various types of edges. 
        If not found here, value is searched from preferences. 
        If called with value, the value is set here and it overrides 
        the preference setting.
        :param edge_type:
        :param key:
        :param value:
        """
        e = self._edge_types.get(edge_type)
        if value is None:
            if e is None or e.get(key, None) is None:
                return self.prefs.edges[edge_type].get(key, None)
            else:
                return e[key]
        else:
            if e is None:
                self._edge_types[edge_type] = {key: value}
            else:
                e[key] = value

    def edge_shape_settings(self, edge_type, key=None, value=None, shape_name=None):
        """ Return the settings dict for certain edge type: often this defaults to edge_shape settings, but it can be
        overridden for each edge_type and eventually for each edge.
        With key, you can get one edge setting, with value you can set the edge setting.
        :param edge_type:
        :param key:
        :param value:
        :return:
        """
        if not shape_name:
            shape_name = self.edge_type_settings(edge_type, 'shape_name')

        shape_args = self._edge_types.get(edge_type).get('shape_args', None)

        if shape_args is None:
            shape_defaults = SHAPE_PRESETS[shape_name]
            if key is None:  # the whole dict is asked
                return shape_defaults #.copy()
            elif value is None:  # get single setting
                return shape_defaults.get(key, None)
            elif value == DELETE:
                pass
            else:# set single setting
                self._edge_types[edge_type]['shape_args'] = shape_defaults.copy()
                self._edge_types[edge_type]['shape_args'][key] = value
        else:
            if key is None:  # the whole dict is asked
                return shape_args
            elif value is None:  # get single setting
                if shape_args.get(key, None) is None:  # get from original dict
                    shape_defaults = SHAPE_PRESETS[shape_name]
                    return shape_defaults.get(key, None)
                else:  # get from here
                    return shape_args[key]
            elif value == DELETE:
                if key in shape_args:
                    shape_defaults = SHAPE_PRESETS[self.edge_type_settings(edge_type, 'shape_name')]
                    if key in shape_defaults:
                        shape_args[key] = shape_defaults[key]
                    else:
                        del shape_args[key]
            else:# set single setting
                shape_args[key] = value

    # ## Nodes - all require edge type as argument, value is stored in dict ###########

    # Node types
    # ABSTRACT_NODE = 0
    # CONSTITUENT_NODE = 1
    # FEATURE_NODE = 2
    # ATTRIBUTE_NODE = 3
    # GLOSS_NODE = 4
    # PROPERTY_NODE = 5

    def node_settings(self, node_type, key, value=None):
        """ Getter/setter for settings related to various types of nodes. 
        If not found here, value is searched from preferences. 
        If called with value, the value is set here and it overrides 
        the preference setting.
        :param node_type:
        :param key:
        :param value:
        """
        e = self._node_types[node_type]
        if value is None:
            if e is None or e.get(key) is None:
                return self.prefs.nodes[node_type][key]
            else:
                return e[key]
        else:
            if e is None:
                self._node_types[node_type] = {key: value}
            else:
                e[key] = value


class ForestRules:
    """

    """
    saved_fields = 'all'
    saved_fields_ignore = 'prefs'
    # saved_fields_ignore_None = True

    """ Rules that affect trees in one forest in a form that can be easily pickled """

    def __init__(self, host, prefs):
        self.prefs = prefs
        if host:
            self.save_key = host.save_key + '_rules'
        self._allow_multidomination = None
        self._only_binary_branching = None
        self._projection = None
        self._projected_inherits_labels = None


    def allow_multidomination(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._allow_multidomination is None:
                return self.prefs.rules_allow_multidomination
            else:
                return self._allow_multidomination
        else:
            self._allow_multidomination = value

    def only_binary_branching(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._only_binary_branching is None:
                return self.prefs.rules_only_binary_branching
            else:
                return self._only_binary_branching
        else:
            self._only_binary_branching = value

    def projection(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._projection is None:
                return self.prefs.rules_projection
            else:
                return self._projection
        else:
            self._projection = value

    def projected_inherits_labels(self, value=None):
        """

        :param value:
        :return:
        """
        if value is None:
            if self._projected_inherits_labels is None:
                return self.prefs.rules_projected_inherits_labels
            else:
                return self._projected_inherits_labels
        else:
            self._projected_inherits_labels = value


    def after_restore(self, values=None):
        """

        :param values:
        :return:
        """
        if not values:
            values = {}
        return

