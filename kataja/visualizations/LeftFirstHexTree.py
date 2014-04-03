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


import math

from kataja.ConstituentNode import ConstituentNode
from kataja.Controller import prefs
from kataja.FeatureNode import FeatureNode
from kataja.utils import caller
from kataja.visualizations.BaseVisualization import BaseVisualization
from kataja.visualizations.Grid import Grid
from kataja.GlossNode import GlossNode


class LeftFirstHexTree(BaseVisualization):
    """ Visualization that draws branches, starting from top and left. Each branching creates 120° angle, so trees are drawn in something resembling a hex grid. Each branch takes the space it needs, and may force next branch drawing to further down and right. """
    name = 'Hexagonal tree'

    def __init__(self):
        self.forest = None
        self._hits = {}
        self._max_hits = {}
        self._directed = True
        self._indentation = 0

    def prepare(self, forest, loading=False):
        print 'preparing LeftFirstHexTree'
        self.forest = forest
        self._hits = {}
        self._max_hits = {}
        self.forest.settings.bracket_style(0)
        self.forest.settings.show_constituent_edges = True
        if not loading:
            self.forest.vis_data = {'name': self.__class__.name, 'rotation': 0}
        self._indentation = 0
        for node in self.forest.visible_nodes():
            self.reset_node(node)

    def reset_node(self, node):
        node.locked_to_position = False
        node.reset_adjustment()
        node.update_label()
        if isinstance(node, ConstituentNode):
            node.bind_x = True
            node.bind_y = True
            node.update_visibility(show_edges=True, scope=0, brackets=self.forest.settings.bracket_style())
        elif isinstance(node, FeatureNode) or isinstance(node, GlossNode):
            node.bind_x = False
            node.bind_y = False


    @caller
    def reselect(self):
        """ if there are different modes for one visualization, rotating between different modes is triggered here. """
        self.forest.vis_data['rotation'] -= 1

    def drawNot(self):

        def find_last(node, parent, is_left=False):
            right = node.right()
            if right and self.should_we_draw(right, node):
                return find_last(right, node, is_left=False)
            left = node.left()
            if left and self.should_we_draw(left, node):
                return find_last(left, node, is_left=True)
            return node, parent, is_left

        def has_room(new_area):
            for area in self.areas.values():
                if new_area.intersects(area):
                    return False
            return True

        def redraw_node(node):
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
            node.set_computed_position((d['x'], d['y'], 0))
            left = node.left()
            if left:
                draw_node(left, node, is_left=True, allow_crossing=allow_crossing)
            right = node.right()
            if right:
                draw_node(right, node, is_left=False, allow_crossing=allow_crossing)

        def draw_node_old(node, parent, is_left=False, allow_crossing=False):
            if not self.should_we_draw(node, parent):
                return

            right = node.right()
            if right and self.should_we_draw(right, node):
                draw_node(right, node, is_left=False, allow_crossing=allow_crossing)
            left = node.left()
            if left and self.should_we_draw(left, node):
                draw_node(left, node, is_left=True, allow_crossing=allow_crossing)

            if self.iterations > 100:
                print self.iterations
                allow_crossing = True

            if parent:
                p = self.drawn[parent.save_key]
                angle = p['angle']
                if is_left:
                    angle += (math.pi / 3)
                else:
                    angle -= (math.pi / 3)
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
            node.set_computed_position((x, y, 0))
            self.areas[node.save_key] = translated_rect
            self.drawn[node.save_key] = {'node': node, 'rect': translated_rect, 'x': x, 'y': y, 'angle': angle,
                                         'is_left': is_left, 'size': 1, 'parent': parent}

            return

        self.nodes = {}
        self.node_list = []

        def prepare_nodes(node, parent, is_left=False, angle=math.pi / 2):
            d = {'parent': parent, 'is_left': is_left, 'x': 0, 'y': 0, 'angle': angle, 'placed': False, 'size': 1,
                 'rect': None, 'node': node, 'i': self.counter, 'left': None, 'right': None}
            left = node.left()
            if left and self.should_we_draw(left, node):
                d['left'] = left
            right = node.right()
            if right and self.should_we_draw(right, node):
                d['right'] = right
            self.counter += 1
            self.nodes[node.save_key] = d
            self.node_list.append(node)
            if d['left']:
                prepare_nodes(left, node, is_left=True, angle=angle + (math.pi / 3))
            if d['right']:
                prepare_nodes(right, node, is_left=False, angle=angle - (math.pi / 3))


        def draw_node(node, is_first=False):
            d = self.nodes[node.save_key]
            right = d['right']
            left = d['left']
            parent = d['parent']
            if right and self.nodes[right.save_key]['placed']:
                print 'using right as reference'
                data = self.nodes[right.save_key]
                dx = -math.cos(d['angle']) * self.edge
                dy = -math.sin(d['angle']) * self.edge
            elif left and self.nodes[left.save_key]['placed']:
                print '*****using left as reference'
                data = self.nodes[left.save_key]
                dx = -math.cos(d['angle']) * self.edge
                dy = -math.sin(d['angle']) * self.edge
            elif parent and self.nodes[parent.save_key]['placed']:
                print 'using parent as reference'
                data = self.nodes[parent.save_key]
                dx = math.cos(d['angle']) * self.edge
                dy = math.sin(d['angle']) * self.edge
            elif is_first:
                print 'using nothing as reference'
                dx = 0
                dy = 0
                data = d
            else:
                print 'postponing this'
                return False
            print math.degrees(d['angle']), dx, dy
            d['x'] = data['x'] + dx
            d['y'] = data['y'] + dy
            d['placed'] = True
            d['rect'] = node.inner_rect.translated(d['x'], d['y'])
            node.set_computed_position((d['x'], d['y'], 0))
            return True


        self.areas = {}
        self.start_x = 0

        self.edge = math.hypot(prefs.edge_width, prefs.edge_height) * 2
        self.forest.vis_data['rotation'], self.traces_to_draw = self._compute_traces_to_draw(
            self.forest.vis_data['rotation'])

        for root in self.forest:
            self.counter = 0
            prepare_nodes(root, None)
            self.postponed_list = []
            is_first = True
            while self.node_list or self.postponed_list:
                last = self.node_list.pop()
                print 'drawing node ', last
                placed = draw_node(last, is_first=is_first)
                is_first = False
                if not placed:
                    self.postponed_list.append(last)
                elif self.postponed_list:
                    repairing = True
                    while repairing and self.postponed_list:
                        repair = self.postponed_list.pop()
                        repairing = draw_node(repair)
                        if not repairing:
                            self.postponed_list.append(repair)


    def draw(self):

        def has_room(new_area):
            for area in self.areas.values():
                if new_area.intersects(area):
                    return False
            return True

        def redraw_node(node):
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
            node.set_computed_position((d['x'], d['y'], 0))
            left = node.left()
            if left:
                draw_node(left, node, is_left=True, allow_crossing=allow_crossing)
            right = node.right()
            if right:
                draw_node(right, node, is_left=False, allow_crossing=allow_crossing)

        def draw_node(node, parent, is_left=False, allow_crossing=False):
            if not self.should_we_draw(node, parent):
                return

            if self.iterations > 100:
                print self.iterations
                allow_crossing = True

            if parent:
                p = self.drawn[parent.save_key]
                angle = p['angle']
                if is_left:
                    angle += (math.pi / 3)
                else:
                    angle -= (math.pi / 3)
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
            node.set_computed_position((x, y, 0))
            self.areas[node.save_key] = translated_rect
            self.drawn[node.save_key] = {'node': node, 'rect': translated_rect, 'x': x, 'y': y, 'angle': angle,
                                         'is_left': is_left, 'size': 1, 'parent': parent}

            left = node.left()
            if left:
                draw_node(left, node, is_left=True, allow_crossing=allow_crossing)
            right = node.right()
            if right:
                draw_node(right, node, is_left=False, allow_crossing=allow_crossing)
            return

        self.drawn = {}
        self.areas = {}
        self.start_x = 0
        self.iterations = 0

        self.edge = math.hypot(prefs.edge_width, prefs.edge_height) * 2
        self.forest.vis_data['rotation'], self.traces_to_draw = self._compute_traces_to_draw(
            self.forest.vis_data['rotation'])

        x = 0

        for root in self.forest:
            draw_node(root, None, allow_crossing=False)
            self.start_x += 100
