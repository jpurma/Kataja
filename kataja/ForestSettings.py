# -*- coding: UTF-8 -*-
#############################################################################
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
#############################################################################

from kataja.globals import CONSTITUENT_EDGE, FEATURE_EDGE, GLOSS_EDGE, ATTRIBUTE_EDGE


ONLY_LEAF_LABELS = 0
ALL_LABELS = 1
ALIASES = 2


class ForestSettings:
    saved_fields = 'all'
    saved_fields_ignore = 'prefs'
    #saved_fields_ignore_None = True

    """ Settings that affect trees in one forest in a form that can be easily pickled """

    def __init__(self, host, prefs):
        self.prefs = prefs
        if host:
            self.save_key = host.save_key + '_settings'
        ### General settings for Forest     
        self._label_style = None
        self._uses_multidomination = None 
        self._traces_are_grouped_together = None 
        self._show_constituent_edges = None
        self._show_merge_order = None
        self._show_select_order = None
        self._draw_features = None
        self._draw_width = None
        self._my_palettes = None
        self._hsv = None
        self._bracket_style = None
        ### Edges - take edge type as argument ###########################
        self._edge_color = None
        self._edge_uses_pen = None
        self._edge_pen = None
        self._edge_uses_brush = None
        self._edge_brush = None
        self._edge_shape_name = None
        self._edge_pull = None
        self._edge_visibility = None
        ### Nodes - take node type as argument ########################### 
        self._node_color = None


    def label_style(self, value = None):
        if value is None:
            if self._label_style is None:
                return self.prefs.default_label_style
            else:
                return self._label_style
        else:
            self._label_style = value

    def uses_multidomination(self, value = None):
        if value is None:
            if self._uses_multidomination is None:
                return self.prefs.default_use_multidomination
            else:
                return self._uses_multidomination
        else:
            self._uses_multidomination = value

    def traces_are_grouped_together(self, value = None):
        if value is None:
            if self._traces_are_grouped_together is None:
                return self.prefs.default_traces_are_grouped_together
            else:
                return self._traces_are_grouped_together
        else:
            self._traces_are_grouped_together = value

    def shows_constituent_edges(self, value = None):
        if value is None:
            if self._show_constituent_edges is None:
                return self.prefs.default_show_constituent_edges
            else:
                return self._show_constituent_edges
        else:
            self._show_constituent_edges = value

    def shows_merge_order(self, value = None):
        if value is None:
            if self._show_merge_order is None:
                return self.prefs.default_show_merge_order
            else:
                return self._show_merge_order
        else:
            self._show_merge_order = value

    def shows_select_order(self, value = None):
        if value is None:
            if self._show_select_order is None:
                return self.prefs.default_show_select_order
            else:
                return self._show_select_order
        else:
            self._show_select_order = value

    def draw_features(self, value = None):
        if value is None:
            if self._draw_features is None:
                return self.prefs.default_draw_features
            else:
                return self._draw_features
        else:
            self._draw_features = value

    def draw_width(self, value = None):
        if value is None:
            if self._draw_width is None:
                return self.prefs.default_draw_width
            else:
                return self._draw_width
        else:
            self._draw_width = value

    def my_palettes(self, value = None):
        if value is None:
            if self._my_palettes is None:
                return self.prefs.default_my_palettes
            else:
                return self._my_palettes
        else:
            self._my_palettes = value

    def hsv(self, value = None):
        if value is None:
            if self._hsv is None:
                return self.prefs.default_hsv
            else:
                return self._hsv
        else:
            self._hsv = value

    def bracket_style(self, value = None):
        if value is None:
            if self._bracket_style is None:
                return self.prefs.default_bracket_style
            else:
                return self._bracket_style
        else:
            self._bracket_style = value


    ### Edges - all require edge type as argument, value is stored in dict ###########

    def edge_color(self, edge_type, value = None):
        if value is None:
            if self._edge_color.get(edge_type) is None:
                return self.prefs.default_edge_color(edge_type)
            else:
                return self._edge_color.get(edge_type)
        else:
            if self._edge_color is None:
                self._edge_color= {edge_type : value}
            else:
                self._edge_color[edge_type] = value

    def edge_uses_pen(self, edge_type, value = None):
        if value is None:
            if self._edge_uses_pen.get(edge_type) is None:
                return self.prefs.default_edge_uses_pen(edge_type)
            else:
                return self._edge_uses_pen.get(edge_type)
        else:
            if self._edge_uses_pen is None:
                self._edge_uses_pen= {edge_type : value}
            else:
                self._edge_uses_pen[edge_type] = value

    def edge_pen(self, edge_type, value = None):
        if value is None:
            if self._edge_pen.get(edge_type) is None:
                return self.prefs.default_edge_pen(edge_type)
            else:
                return self._edge_pen.get(edge_type)
        else:
            if self._edge_pen is None:
                self._edge_pen= {edge_type : value}
            else:
                self._edge_pen[edge_type] = value

    def edge_uses_brush(self, edge_type, value = None):
        if value is None:
            if self._edge_uses_brush.get(edge_type) is None:
                return self.prefs.default_edge_uses_brush(edge_type)
            else:
                return self._edge_uses_brush.get(edge_type)
        else:
            if self._edge_uses_brush is None:
                self._edge_uses_brush = {edge_type : value}
            else:
                self._edge_uses_brush[edge_type] = value

    def edge_brush(self, edge_type, value = None):
        if value is None:
            if self._edge_brush.get(edge_type) is None:
                return self.prefs.default_edge_brush(edge_type)
            else:
                return self._edge_brush.get(edge_type)
        else:
            if self._edge_brush is None:
                self._edge_brush= {edge_type : value}
            else:
                self._edge_brush[edge_type] = value

    def edge_shape_name(self, edge_type, value = None):
        if value is None:
            if self._edge_shape_name.get(edge_type) is None:
                return self.prefs.default_edge_shape_name(edge_type)
            else:
                return self._edge_shape_name.get(edge_type)
        else:
            if self._edge_shape_name is None:
                self._edge_shape_name= {edge_type : value}
            else:
                self._edge_shape_name[edge_type] = value

    def edge_pull(self, edge_type, value = None):
        if value is None:
            if self._edge_pull.get(edge_type) is None:
                return self.prefs.default_edge_pull(edge_type)
            else:
                return self._edge_pull.get(edge_type)
        else:
            if self._edge_pull is None:
                self._edge_pull = {edge_type : value}
            else:
                self._edge_pull[edge_type] = value

    def edge_visibility(self, edge_type, value = None):
        if value is None:
            if self._edge_visibility.get(edge_type) is None:
                return self.prefs.default_edge_visibility(edge_type)
            else:
                return self._edge_visibility.get(edge_type)
        else:
            if self._edge_visibility is None:
                self._edge_visibility = {edge_type : value}
            else:
                self._edge_visibility[edge_type] = value


    def after_restore(self, values={}):
        return

class ForestRules:
    saved_fields = 'all'
    saved_fields_ignore = 'prefs'
    #saved_fields_ignore_None = True

    """ Rules that affect trees in one forest in a form that can be easily pickled """

    def __init__(self, host, prefs):
        self.prefs = prefs
        if host:
            self.save_key = host.save_key + '_rules'
        self._allow_multidomination = None
        self._only_binary_branching = None
        self._projection = None
        self._projected_inherits_labels = None


    def allow_multidomination(self, value = None):
        if value is None:
            if self._allow_multidomination is None:
                return self.prefs.rules_allow_multidomination
            else:
                return self._allow_multidomination
        else:
            self._allow_multidomination = value

    def only_binary_branching(self, value = None):
        if value is None:
            if self._only_binary_branching is None:
                return self.prefs.rules_only_binary_branching
            else:
                return self._only_binary_branching
        else:
            self._only_binary_branching = value

    def projection(self, value = None):
        if value is None:
            if self._projection is None:
                return self.prefs.rules_projection
            else:
                return self._projection
        else:
            self._projection = value

    def projected_inherits_labels(self, value = None):
        if value is None:
            if self._projected_inherits_labels is None:
                return self.prefs.rules_projected_inherits_labels
            else:
                return self._projected_inherits_labels
        else:
            self._projected_inherits_labels = value


    def after_restore(self, values={}):
        return

