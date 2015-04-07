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
from kataja.shapes import SHAPE_PRESETS
from kataja.BaseModel import BaseModel
from kataja.singletons import prefs

ONLY_LEAF_LABELS = 0
ALL_LABELS = 1
ALIASES = 2

class ForestSettingsModel(BaseModel):

    def __init__(self, host):
        super().__init__(host)
        # ## General settings for Forest
        self.label_style = None
        self.uses_multidomination = None
        self.traces_are_grouped_together = None
        self.shows_constituent_edges = None
        self.shows_merge_order = None
        self.shows_select_order = None
        self.draw_features = None
        self.hsv = None
        self.color_mode = None
        self.last_key_colors = {}
        self.bracket_style = None
        # ## Edges - take edge type as argument ###########################
        self.edge_types = {}
        # ## Nodes - take node type as argument ###########################
        self.node_types = {}

class ForestSettings:
    """ Settings specific for this forest -- a level between global preferences and settings specific for object. """
    saved_fields = 'all'
    saved_fields_ignore = 'prefs'
    # saved_fields_ignore_None = True

    """ Settings that affect trees in one forest in a form that can be easily pickled """

    def __init__(self):
        if not hasattr(self, 'model'):
            self.model = ForestSettingsModel(self)

    @property
    def save_key(self):
        """ Return the save_key from the model. It is a property from BaseModel.
        :return: str
        """
        return self.model.save_key

    @property
    def label_style(self):
        """
        :return:
        """
        if self.model.label_style is None:
            return prefs.default_label_style
        else:
            return self.model.label_style

    @label_style.setter
    def label_style(self, value):
        """
        :param value: """
        self.model.label_style = value


    @property
    def uses_multidomination(self):
        """
        :return:
        """
        if self.model.uses_multidomination is None:
            return prefs.default_use_multidomination
        else:
            return self.model.uses_multidomination

    @uses_multidomination.setter
    def uses_multidomination(self, value):
        """
        :param value: """
        self.model.uses_multidomination = value


    @property
    def traces_are_grouped_together(self):
        """
        :return:
        """
        if self.model.traces_are_grouped_together is None:
            return prefs.default_traces_are_grouped_together
        else:
            return self.model.traces_are_grouped_together

    @traces_are_grouped_together.setter
    def traces_are_grouped_together(self, value):
        """
        :param value: """
        self.model.traces_are_grouped_together = value


    @property
    def shows_constituent_edges(self):
        """
        :return:
        """
        if self.model.shows_constituent_edges is None:
            return prefs.default_shows_constituent_edges
        else:
            return self.model.shows_constituent_edges

    @shows_constituent_edges.setter
    def shows_constituent_edges(self, value):
        """
        :param value: """
        self.model.shows_constituent_edges = value

    @property
    def shows_merge_order(self):
        """
        :return:
        """
        if self.model.shows_merge_order is None:
            return prefs.default_shows_merge_order
        else:
            return self.model.shows_merge_order

    @shows_merge_order.setter
    def shows_merge_order(self, value):
        """
        :param value: """
        self.model.shows_merge_order = value

    @property
    def shows_select_order(self):
        """
        :return:
        """
        if self.model.shows_select_order is None:
            return prefs.default_shows_select_order
        else:
            return self.model.shows_select_order

    @shows_select_order.setter
    def shows_select_order(self, value):
        """
        :param value: """
        self.model.shows_select_order = value

    @property
    def draw_features(self):
        """
        :return:
        """
        if self.model.draw_features is None:
            return prefs.default_draw_features
        else:
            return self.model.draw_features

    @draw_features.setter
    def draw_features(self, value):
        """
        :param value: """
        self.model.draw_features = value

    @property
    def hsv(self):
        """
        :return:
        """
        if self.model.hsv is None:
            return prefs.default_hsv
        else:
            return self.model.hsv

    @hsv.setter
    def hsv(self, value):
        """
        :param value: """
        self.model.hsv = value

    @property
    def bracket_style(self):
        """ :return: """
        if self.model.bracket_style is None:
            return prefs.default_bracket_style
        else:
            return self.model.bracket_style

    @bracket_style.setter
    def bracket_style(self, value):
        """
        :param value:  """
        self.model.bracket_style = value

    def last_key_color_for_mode(self, mode_key, value=None):
        """

        :param mode_key:
        :param value:
        :return:
        """
        if value is None:
            return self.model.last_key_colors.get(mode_key, None)
        else:
            self.model.last_key_colors[mode_key] = value

    @property
    def color_mode(self):
        """ :return: """
        if self.model.color_mode is None:
            return prefs.color_mode
        else:
            return self.model.color_mode

    @color_mode.setter
    def color_mode(self, value=None):
        """
        :param value:"""
        self.model.color_mode = value


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
        if not edge_type:
            return
        local_edge_settings = self.model.edge_types.get(edge_type)
        if value is None:
            if local_edge_settings is None or local_edge_settings.get(key, None) is None:
                return prefs.edges[edge_type].get(key, None)
            else:
                return local_edge_settings[key]
        else:
            if local_edge_settings is None:
                self.model.edge_types[edge_type] = {key: value}
            else:
                local_edge_settings[key] = value

    def edge_shape_settings(self, edge_type, key=None, value=None, shape_name=None):
        """ Return the settings dict for certain edge type: often this defaults to edge_shape settings, but it can be
        overridden for each edge_type and eventually for each edge.
        With key, you can get one edge setting, with value you can set the edge setting.
        :param edge_type:
        :param key:
        :param value:
        :return:
        """
        if not edge_type:
            return
        if not shape_name:
            shape_name = self.edge_type_settings(edge_type, 'shape_name')

        local_edge_type = self.model.edge_types.get(edge_type, None)
        if local_edge_type:
            shape_args = local_edge_type.get('shape_args', None)
        else:
            shape_args = None

        if shape_args is None:
            shape_defaults = SHAPE_PRESETS[shape_name]
            if key is None:  # the whole dict is asked
                return shape_defaults  # .copy()
            elif value is None:  # get single setting
                return shape_defaults.get(key, None)
            elif value == DELETE:
                pass
            else:  # set single setting
                if not local_edge_type:
                    local_edge_type = {}
                    self.model.edge_types[edge_type] = local_edge_type
                local_edge_type['shape_args'] = shape_defaults.copy()
                local_edge_type['shape_args'][key] = value
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
            else:  # set single setting
                shape_args[key] = value

    # ## Nodes - all require edge type as argument, value is stored in dict ###########

    # Node types
    # ABSTRACT_NODE = 0
    # CONSTITUENT_NODE = 1
    # FEATURE_NODE = 2
    # ATTRIBUTE_NODE = 3
    # GLOSS_NODE = 4
    # PROPERTY_NODE = 5

    def node_settings(self, node_type=None, key=None, value=None):
        """ Getter/setter for settings related to various types of nodes. 
        If not found here, value is searched from preferences. 
        If called with value, the value is set here and it overrides 
        the preference setting.
        :param node_type:
        :param key:
        :param value:
        """
        if not node_type:
            # Return settings for all node types
            settings = {}
            settings.update(prefs.nodes)
            settings.update(self.model.node_types)
            return settings
        elif not key:
            # Return all settings of certain node type
            settings = {}
            settings.update(prefs.nodes[node_type])
            settings.update(self.model.node_types.get(node_type, {}))
            return settings
        local_node_settings = self.model.node_types.get(node_type, None)
        if value is None:
            if local_node_settings is None or local_node_settings.get(key) is None:
                return prefs.nodes[node_type][key]
            else:
                return local_node_settings[key]
        else:
            if local_node_settings is None:
                self.model.node_types[node_type] = {key: value}
            else:
                local_node_settings[key] = value


class ForestRulesModel(BaseModel):

    def __init__(self, host):
        super().__init__(host)
        self.allow_multidomination = None
        self.only_binary_branching = None
        self.projection = None
        self.projected_inherits_labels = None


class ForestRules(BaseModel):
    """ Rules that affect trees in one forest in a form that can be easily pickled """

    def __init__(self):
        if not hasattr(self, 'model'):
            self.model = ForestRulesModel(self)

    @property
    def save_key(self):
        """ Return the save_key from the model. It is a property from BaseModel.
        :return: str
        """
        return self.model.save_key

    @property
    def allow_multidomination(self, value=None):
        """
        :param value:
        :return:
        """
        if self.model.allow_multidomination is None:
            return prefs.rules_allow_multidomination
        else:
            return self.model.allow_multidomination

    @allow_multidomination.setter
    def allow_multidomination(self, value=None):
        """
        :param value:
        :return:
        """
        self.model.allow_multidomination = value


    @property
    def only_binary_branching(self, value=None):
        """
        :param value:
        :return:
        """
        if self.model.only_binary_branching is None:
            return prefs.rules_only_binary_branching
        else:
            return self.model.only_binary_branching

    @only_binary_branching.setter
    def only_binary_branching(self, value=None):
        """

        :param value:
        :return:
        """
        self.model.only_binary_branching = value

    @property
    def projection(self, value=None):
        """
        :param value:
        :return:
        """
        if self.model.projection is None:
            return prefs.rules_projection
        else:
            return self.model.projection

    @projection.setter
    def projection(self, value=None):
        """
        :param value:
        :return:
        """
        self.model.projection = value


    @property
    def projected_inherits_labels(self):
        """
        :return:
        """
        if self.model.projected_inherits_labels is None:
            return prefs.rules_projected_inherits_labels
        else:
            return self.model.projected_inherits_labels

    @projected_inherits_labels.setter
    def projected_inherits_labels(self, value=None):
        """
        :param value:
        :return:
        """
        self.model.projected_inherits_labels = value

