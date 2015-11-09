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

from kataja.singletons import prefs
from kataja.utils import caller
from kataja.visualizations.BaseVisualization import BaseVisualization
import kataja.globals as g


class LeftFirstHexTree(BaseVisualization):
    """ Visualization that draws branches, starting from top and left.
    Each branching creates 120° angle, so trees are drawn in something resembling a hex grid.
    Each branch takes the space it needs, and may force next branch drawing to further down and right. """
    name = 'Hexagonal trees'

    def __init__(self):
        BaseVisualization.__init__(self)
        self.forest = None
        self._hits = {}
        self._max_hits = {}
        self._directed = True
        self._indentation = 0
        self.drawn = {}
        self.areas = {}
        self.start_x = 0
        self.iterations = 0
        self.edge = 0
        self.traces_to_draw = []
        self.counter = 0
        self.postponed_list = []



    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        print('preparing LeftFirstHexTree')
        self.forest = forest
        self._hits = {}
        self._max_hits = {}
        self._indentation = 0
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
        """ if there are different modes for one visualization, rotating between different modes is triggered here. """
        self.set_vis_data('rotation', self.get_vis_data('rotation') - 1)


    def draw(self):

        """


        :return:
        """

        def has_room(new_area):
            """

            :param new_area:
            :return:
            """
            for area in self.areas.values():
                if new_area.intersects(area):
                    return False
            return True

        def redraw_node(node):
            """

            :param node:
            :return:
            """
            self.iterations += 1
            del self.areas[node.save_key]
            d = self.drawn[node.save_key]
            d['size'] += 1
            allow_crossing = False
            d['x'] += math.cos(d['angle']) * self.edge
            d['y'] += math.sin(d['angle']) * self.edge
            d['rect'] = node.inner_rect.translated(d['x'], d['y'])
            if has_room(d['rect']):
                self.areas[node.save_key] = d['rect']
            elif d['parent']:
                return redraw_node(d['parent'])
            else:
                self.areas[node.save_key] = d['rect']
                allow_crossing = True
            node.move_to(d['x'], d['y'], 0)

            ch = list(node.get_visible_children())
            for i, child in enumerate(ch):
                draw_node(child, node, child_n=i, of_children=len(ch),
                          allow_crossing=allow_crossing)

        def draw_node(node, parent, child_n=0, of_children=0, allow_crossing=False):
            """

            :param node:
            :param parent:
            :param is_left:
            :param allow_crossing:
            :return:
            """
            if not self.should_we_draw(node, parent):
                return

            if self.iterations > 100:
                allow_crossing = True

            if parent:
                p = self.drawn[parent.save_key]
                if of_children > 1:
                    angle_step = ((2 * math.pi) / 3) / (of_children - 1)
                    base_angle = p['angle'] + (math.pi / 3)
                    angle = base_angle - (child_n * angle_step)
                else:
                    angle = p['angle']
                x = p['x'] + math.cos(angle) * self.edge
                y = p['y'] + math.sin(angle) * self.edge
                translated_rect = node.inner_rect.translated(x, y)
                if not has_room(translated_rect):
                    if allow_crossing:
                        while not has_room(translated_rect):
                            x += math.cos(angle) * self.edge
                            y += math.sin(angle) * self.edge
                            translated_rect = node.inner_rect.translated(x, y)
                    else:
                        return redraw_node(parent)
            else:
                x = self.start_x
                y = 0
                translated_rect = node.inner_rect.translated(x, y)
                while not has_room(translated_rect):
                    self.start_x += prefs.edge_width * 2
                    x = self.start_x
                    translated_rect = node.inner_rect.translated(x, y)
                angle = math.pi / 2
            node.move_to(x, y, 0)
            self.areas[node.save_key] = translated_rect
            self.drawn[node.save_key] = {'node': node, 'rect': translated_rect, 'x': x, 'y': y,
                                         'angle': angle, 'child_n': child_n,
                                         'of_children': of_children, 'size': 1, 'parent': parent}

            ch = list(node.get_visible_children())
            for i, child in enumerate(ch):
                draw_node(child, node, child_n=i, of_children=len(ch),
                          allow_crossing=allow_crossing)
            return

        self.drawn = {}
        self.areas = {}
        self.start_x = 0
        self.iterations = 0

        self.edge = math.hypot(prefs.edge_width, prefs.edge_height) * 2
        new_rotation, self.traces_to_draw = self._compute_traces_to_draw(
            self.get_vis_data('rotation'))
        self.set_vis_data('rotation', new_rotation)


        x = 0

        for tree in self.forest:
            draw_node(tree.top, None, allow_crossing=False)
            self.start_x += 100
