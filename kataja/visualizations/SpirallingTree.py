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
from kataja.Visualization import BaseVisualization
from kataja.singletons import prefs, log
from kataja.utils import caller


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
        self.max_attempts = 4

    def expand(self):
        if self.attempts > self.max_attempts:
            return False
        if not self.has_room(self.rect):  # don't push through a node
            return False
        self.attempts += 1
        self.size += 1
        self.x += math.cos(self.angle) * self.vis.edge
        self.y += math.sin(self.angle) * self.vis.edge
        self.rect = self.focus.inner_rect.translated(self.x, self.y)
        if not self.has_room(self.rect):
            return False
        self.focus.move_to(self.x, self.y, valign=g.TOP)
        self.add_area()
        return True

    def add_area(self):
        key = self.focus.uid
        self.vis.areas[key] = self.rect

    def remove_areas(self):
        key = self.focus.uid
        if key in self.vis.areas:
            del self.vis.areas[key]
        if self in self.vis.waiting_list:
            self.vis.waiting_list.remove(self)
        for layer in self.layers:
            layer.remove_areas()

    def try_to_draw(self, n, n_of_children):
        if self.parent:
            if n_of_children > 1:
                if self.vis.sides == 3:
                    angle_step = ((2 * math.pi) / 3)
                    self.angle = self.parent.angle + math.pi - ((n + 1) * angle_step)
                elif self.vis.sides:
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
        self.focus.move_to(self.x, self.y, valign=g.TOP)
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
    banned_node_shapes = (g.BRACKETED, g.SCOPEBOX)

    def __init__(self):
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
        self.sides = 3
        self.use_gravity = False

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        self._hits = {}
        self._max_hits = {}
        self.validate_node_shapes()
        if reset:
            self.sides = 3
            self.set_data('rotation', 0)
            self.reset_nodes()

    def reset_node(self, node):
        """

        :param node:
        """
        super().reset_node(node)
        if node.node_type == g.CONSTITUENT_NODE:
            node.physics_x = False
            node.physics_y = False

    def has_free_movers(self):
        for node in self.forest.nodes.values():
            if node.isVisible() and (node.physics_x or node.physics_y):
                return True
        return True

    @caller
    def reselect(self):
        """ if there are different modes for one visualization, rotating between different modes
        is triggered here. """
        self.set_data('rotation', self.get_data('rotation') - 1)

    def prepare_draw(self):
        new_rotation = self.forest.compute_traces_to_draw(self.get_data('rotation'))
        self.set_data('rotation', new_rotation)

    def draw_tree(self, tree_top, sides=0):
        """

        :return:
        """
        self.start_x = 0
        self.areas = {}
        self.iterations = 0
        self.waiting_list = []

        self.edge = math.hypot(prefs.edge_width, prefs.edge_height) * 2

        def select_layer(layer, sides):
            # ch.reverse()
            self.iterations += 1
            if self.iterations > 500:
                print("Reached 500 iterations, quit trying")
                return None
            if not layer.focus.is_triangle_host():
                ch = [x for x in layer.focus.get_children(similar=True, visible=True) if
                      not x.locked_to_node]
                layer.layers = []
                for i, child_node in enumerate(ch):
                    if self.forest.should_we_draw(child_node, layer.focus):
                        child_layer = Layer(child_node, parent=layer, vis=self)
                        success = child_layer.try_to_draw(i, len(ch))
                        if not success:
                            child_layer.remove_areas()
                            expanded_layer = someone_must_expand(layer, sides)
                            return expanded_layer
                        layer.layers.append(child_layer)
                        self.waiting_list.append(child_layer)
                for child in layer.layers:
                    if child in self.waiting_list:
                        self.waiting_list.remove(child)
                        return child
            while layer.parent:
                layer = layer.parent
                if self.waiting_list:
                    return self.waiting_list.pop(0)

        def someone_must_expand(layer, sides):
            can_expand = layer.expand()
            if can_expand:
                return layer
            elif layer.parent:
                layer.remove_areas()
                return someone_must_expand(layer.parent, sides)
            else:
                sides += 1
                self.draw_tree(tree_top, sides=sides)

        for node in tree_top.get_sorted_nodes():
            if node.is_triangle_host():
                continue
            my_sides = len([x for x in node.get_children(visible=True, similar=True) if
                            not x.locked_to_node]) + 1
            if my_sides > sides:
                sides = my_sides

        my_layer = Layer(tree_top, parent=None, vis=self)
        success = my_layer.try_to_draw(0, 1)
        while not success:
            self.start_x += 100
            success = my_layer.try_to_draw(0, 1)
        while my_layer:
            my_layer = select_layer(my_layer, sides)
