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
from kataja.BaseModel import BaseModel, Saved
from kataja.singletons import prefs

ONLY_LEAF_LABELS = 0
ALL_LABELS = 1
ALIASES = 2


class SavedSetting(Saved):
    """ Descriptor like Saved, but if getter doesn't find local version, takes one from preferences. """
#    def __init__(self, name, before_set=None, if_changed=None, after_get=None):
#        super().__init__(name, before_set=before_set, if_changed=if_changed)
#        self.after_get = after_get

    def __get__(self, obj: BaseModel, objtype=None):
        value = obj._saved[self.name]
        if value is None:
            return getattr(prefs, self.name)
        else:
            return value


class ForestSettings(BaseModel):
    """ Settings specific for this forest -- a level between global preferences and settings specific for object. """

    short_name = "FSettings"

    def __init__(self):
        super().__init__()
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
        self.use_projection = True
        self.use_xbar_aliases = True
        self.projection_highlighter = False
        self.projection_strong_lines = True
        self.projection_colorized = True
        self.show_leaf_labels = True
        self.show_leaf_aliases = True
        self.show_internal_labels = False
        self.show_internal_aliases = True
        # ## Edges - take edge type as argument ###########################
        self.edge_types = {}
        # ## Nodes - take node type as argument ###########################
        self.node_types = {}


    def last_key_color_for_mode(self, mode_key, value=None):
        """

        :param mode_key:
        :param value:
        :return:
        """
        if value is None:
            return self.last_key_colors.get(mode_key, None)
        else:
            self.last_key_colors[mode_key] = value

    # ## Edges - all require edge type as argument, value is stored in dict ###########

    def edge_type_for(self, node_type):
        """ Helper for easy access to edge_type
        :param node_type:
        :return:
        """
        return self.node_info(node_type, 'edge')

    def edge_info(self, edge_type, key):
        """ Getter for settings related to various types of edges.
        If not found here, value is searched from preferences. 
        :param edge_type:
        :param key:
        """
        local_edge_settings = self.edge_types.get(edge_type)
        if local_edge_settings is None or local_edge_settings.get(key, None) is None:
            return prefs.edges[edge_type].get(key, None)
        else:
            return local_edge_settings[key]

    def set_edge_info(self, edge_type, key, value):
        """ Setter for settings related to various types of edges.
        Values are set for forest.settings and override the preferences
        :param edge_type:
        :param key:
        :param value:
        """
        local_edge_settings = self.edge_types.get(edge_type)
        if local_edge_settings is None:
            self.edge_types[edge_type] = {key: value}
        else:
            local_edge_settings[key] = value


    def shape_for_edge(self, edge_type):
        """ Helper to get the shape name for given edge type.
        :return:
        """
        return self.edge_info(edge_type, 'shape_name')

    def reset_shape(self, edge_type, *keys):
        """ Delecte local (forest) modifications for edge shapes
        :param edge_type: edge_type we are resetting
        :param keys: strings of key names
        :return:
        """
        local_edge_type = self.edge_types.get(edge_type, None)
        if not local_edge_type:
            return
        shape_args = local_edge_type.get('shape_args', None)
        if not shape_args:
            return
        shape_defaults = SHAPE_PRESETS[self.edge_info(edge_type, 'shape_name')]
        for key in keys:
            if key in shape_args:
                if key in shape_defaults:
                    shape_args[key] = shape_defaults[key]
                else:
                    del shape_args[key]

    def shape_defaults(self, edge_type):
        shape_name = self.edge_info(edge_type, 'shape_name')
        return SHAPE_PRESETS[shape_name]

    def local_shape_args(self, edge_type):
        local_edge_type = self.edge_types.get(edge_type, None)
        if local_edge_type:
            return local_edge_type.get('shape_args', None)

    def shape_presets(self, shape_name):
        return SHAPE_PRESETS[shape_name]

    def shape_info(self, edge_type, key=None):
        """ Return the settings dict for certain edge type: often this defaults
        to edge_shape settings, but it can be
        overridden for each edge_type and eventually for each edge.
        With key, you can get one edge setting.
        :param edge_type:
        :param key:
        :return:
        """
        shape_args = self.local_shape_args(edge_type)
        if shape_args:
            if key: # get single setting
                if shape_args.get(key, None) is None:  # get from original dict
                    return self.shape_defaults(edge_type).get(key, None)
                else:  # get from here
                    return shape_args[key]
            else:  # the whole dict is asked
                return shape_args
        else:
            if key:  # get single setting
                return self.shape_defaults(edge_type).get(key, None)
            else:  # the whole dict is asked
                return self.shape_defaults(edge_type)  # .copy()

    def set_shape_info(self, edge_type, key, value):
        """ Set shape locally: each edge_type has its local settings,
        which includes dict shape_args, where all these are to be found.
        :param edge_type:
        :param key:
        :return:
        """
        shape_name = self.edge_info(edge_type, 'shape_name')

        local_edge_type = self.edge_types.get(edge_type, None)
        if not local_edge_type:
            local_edge_type = {}
            self.edge_types[edge_type] = local_edge_type
        shape_args = local_edge_type.get('shape_args', None)
        if not shape_args:
            shape_args = self.shape_defaults(edge_type).copy()
            local_edge_type['shape_args'] = shape_args
        shape_args[key] = value

    # ## Nodes - all require edge type as argument, value is stored in dict

    def node_info(self, node_type=None, key=None):
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
            settings.update(self.node_types)
            return settings
        elif not key:
            # Return all settings of certain node type
            settings = {}
            settings.update(prefs.nodes[node_type])
            settings.update(self.node_types.get(node_type, {}))
            return settings
        local_node_settings = self.node_types.get(node_type, None)
        if local_node_settings is None or local_node_settings.get(key) is None:
            return prefs.nodes[node_type][key]
        else:
            return local_node_settings[key]

    def set_node_info(self, node_type, key, value):
        """ Setter for settings related to various types of nodes.
        If not found here, value is searched from preferences.
        If called with value, the value is set here and it overrides
        the preference setting.
        This cannot be used to create new node_types. Only to locally modify
        existing settings
        :param node_type:
        :param key:
        :param value:
        """
        local_node_settings = self.node_types.get(node_type, None)
        if local_node_settings is None:
            self.node_types[node_type] = {key: value}
        else:
            local_node_settings[key] = value


    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    label_style = SavedSetting("label_style")
    uses_multidomination = SavedSetting("uses_multidomination")
    traces_are_grouped_together = SavedSetting("traces_are_grouped_together")
    shows_constituent_edges = SavedSetting("shows_constituent_edges")
    shows_merge_order = SavedSetting("shows_merge_order")
    shows_select_order = SavedSetting("shows_select_order")
    draw_features = SavedSetting("draw_features")
    hsv = SavedSetting("hsv")
    color_mode = SavedSetting("color_mode")
    bracket_style = SavedSetting("bracket_style")
    # these have dicts, they don't need SavedSetting check but special care in use
    last_key_colors = Saved("last_key_colors")
    edge_types = Saved("edge_types")
    node_types = Saved("node_types")


class ForestRules(BaseModel):
    """ Rules that affect trees in one forest in a form that can be easily pickled """

    short_name = "FRules"

    def __init__(self):
        super().__init__()
        self.allow_multidomination = None
        self.only_binary_branching = None
        self.projection = None
        self.projected_inherits_labels = None

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    allow_multidomination = SavedSetting("allow_multidomination")
    only_binary_branching = SavedSetting("only_binary_branching")
    projection = SavedSetting("projection")
    projected_inherits_labels = SavedSetting("projected_inherits_labels")
