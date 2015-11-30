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


import math

import kataja.globals as g
from kataja.singletons import prefs
from kataja.utils import caller
from kataja.visualizations.BaseVisualization import BaseVisualization


class Layer:

    def __init__(self, focus, parent, vis):
        self.vis = vis
        self.focus = focus
        self.parent = parent
        self.size = 0
        self.x = 0
        self.y = 0
        self.angle = 0
        self.layers = []
        self.rect = None
        self.attempts = 0
        self.max_attempts = 2

    def expand(self):
        if self.attempts > self.max_attempts:
            return False
        self.attempts += 1
        self.size += 1
        self.x += math.cos(self.angle) * self.vis.edge
        self.y += math.sin(self.angle) * self.vis.edge
        self.rect = self.focus.inner_rect.translated(self.x, self.y)
        if not self.has_room(self.rect):
            return False
        self.focus.move_to(self.x, self.y, 0, valign=g.TOP_ROW)
        self.add_area()
        return True

    def add_area(self):
        key = self.focus.save_key
        self.vis.areas[key] = self.rect

    def remove_areas(self):
        key = self.focus.save_key
        if key in self.vis.areas:
            del self.vis.areas[key]
        for layer in self.layers:
            layer.remove_areas()

    def should_be_drawn(self):
        if not self.parent:
            return True
        if not self.parent.rect:
            return False
        return self.vis.should_we_draw(self.focus, self.parent.focus)

    def someone_must_expand(self):
        can_expand = self.expand()
        if can_expand:
            self.vis.draw_layer(self)
            return True
        elif self.parent:
            print('..... tried to expand ten times retracing to parent from %s ' % self.focus)
            self.remove_areas()
            self.parent.someone_must_expand()
            return False

    def try_to_draw(self, n, n_of_children):
        if self.parent:
            if n_of_children > 1:
                angle_step = ((2 * math.pi) / (self.vis.sides / 2)) / (n_of_children - 1)
                base_angle = self.parent.angle + (math.pi / (self.vis.sides / 2))
                self.angle = base_angle - (n * angle_step)
            else:
                self.angle = self.parent.angle
            xstep = math.cos(self.angle) * self.vis.edge
            ystep = math.sin(self.angle) * self.vis.edge
            self.x = self.parent.x + xstep
            self.y = self.parent.y + ystep
            self.rect = self.focus.inner_rect.translated(self.x, self.y)
            while self.rect.intersects(self.parent.rect):
                self.x += xstep
                self.y += ystep
                self.rect = self.focus.inner_rect.translated(self.x, self.y)
            if not self.has_room(self.rect):
                return False
        else:
            self.x = self.vis.start_x
            self.y = 0
            self.rect = self.focus.inner_rect.translated(self.x, self.y)
            if not self.has_room(self.rect):
                return False
            self.angle = math.pi / 2
        self.focus.move_to(self.x, self.y, 0, valign=g.TOP_ROW)
        self.add_area()
        return True

    def has_room(self, new_area):
        """

        :param new_area:
        :return:
        """
        for area in self.vis.areas.values():
            if area != new_area and new_area.intersects(area):
                return False
        return True


class SpirallingTree(BaseVisualization):
    """ Visualization that draws branches, starting from top and left.
    Each branching creates 120° angle, so trees are drawn in something resembling a hex grid.
    Each branch takes the space it needs, and may force next branch drawing to further down and
    right. """
    name = 'Spiralling trees'

    def __init__(self):
        print('init')
        BaseVisualization.__init__(self)
        self.forest = None
        self._hits = {}
        self._max_hits = {}
        self._directed = False
        self.drawn = {}
        self.areas = {}
        self.start_x = 0
        self.iterations = 0
        self.edge = 0
        self.sides = 12

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        self._hits = {}
        self._max_hits = {}
        if reset:
            self.forest.settings.bracket_style = g.NO_BRACKETS
            self.forest.settings.show_constituent_edges = True
            self.set_vis_data('rotation', 0)
            for node in self.forest.visible_nodes():
                self.reset_node(node)

    def reset_node(self, node):
        """

        :param node:
        """
        super().reset_node(node)
        if node.node_type == g.CONSTITUENT_NODE:
            node.physics_x = False
            node.physics_y = False
            node.physics_z = False

    @caller
    def reselect(self):
        """ if there are different modes for one visualization, rotating between different modes
        is triggered here. """
        self.set_vis_data('rotation', self.get_vis_data('rotation') - 1)

    def draw_layer(self, layer):
        ch = list(layer.focus.get_visible_children())
        #ch.reverse()
        self.iterations += 1
        if self.iterations > 100:
            return False
        layer.layers = []
        success = True
        for i, child_node in enumerate(ch):
            child_layer = Layer(child_node, parent=layer, vis=self)
            if child_layer.should_be_drawn():
                success = child_layer.try_to_draw(i, len(ch))
                if not success:
                    layer.someone_must_expand()
                    return False
            layer.layers.append(child_layer)
        for child in layer.layers:
            success = self.draw_layer(child)
            if not success: # avoid ghosts of recursion
                break
        return success


    def draw(self):
        """

        :return:
        """
        self.start_x = 0
        self.areas = {}
        self.iterations = 0

        self.edge = math.hypot(prefs.edge_width, prefs.edge_height) * 2
        new_rotation, self.traces_to_draw = self._compute_traces_to_draw(
                self.get_vis_data('rotation'))
        self.set_vis_data('rotation', new_rotation)

        for tree in self.forest:
            layer = Layer(tree.top, parent=None, vis=self)
            success = layer.try_to_draw(0, 1)
            while not success:
                self.start_x += 100
                success = layer.try_to_draw(0, 1)
            self.draw_layer(layer)
