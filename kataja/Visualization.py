# -*- coding: UTF-8 -*-
# ############################################################################
#
# *** Kataja - Biolinguistic BaseVisualization tool ***
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
import random

from kataja.utils import caller, time_me
import kataja.globals as g
import sys

from kataja.singletons import ctrl

LEFT = 1
NO_ALIGN = 0
RIGHT = 2


class BaseVisualization:
    """ Base class for different 'drawTree' implementations """
    name = 'BaseVisualization base class'
    banned_node_shapes = ()
    hide_edges_if_nodes_overlap = True

    def __init__(self):
        """ This is called once when building Kataja. Set up properties for this kind of 
        visualization. vis_data can be used to store states of visualization: when restoring a visualization, vis_data is the only stored data that can be used. """
        self.forest = None
        self._directed = False
        self._hits = {}
        self._max_hits = {}
        self.use_gravity = True
        self._stored_top_node_positions = []
        self.traces_to_draw = {}

    def prepare(self, forest, reset=True):
        """ If loading a state, don't reset.
        :param forest:Forest
        :param reset:boolean
        """
        self.forest = forest
        self._directed = False
        self._hits = {}
        self._max_hits = {}
        if reset:
            self.reset_nodes()
        self.validate_node_shapes()

    def prepare_draw(self):
        """ This is called every time before visualisation is drawn, a place to do preparations that
        matter for all forest and not single trees.
        :return:
        """
        pass

    def validate_node_shapes(self):
        ls = ctrl.settings.get('label_shape')
        if ls in self.banned_node_shapes:
            ls = 0
            while ls in self.banned_node_shapes:
                ls += 1
            ctrl.settings.set('label_shape', ls, level=g.FOREST)
            self.forest.update_label_shapes()

    def reset_nodes(self):
        for node in self.forest.visible_nodes():
            self.reset_node(node)

    def say_my_name(self):
        """
        :return: name of the visualization e.g. Heisenberg
        """
        return self.__class__.name

    def set_data(self, key, value):
        """ Sets (Saved) visualization data. Basically does the necessary poking
        so visualization algorithms don't have to bother with that.
        :param key: key in vis_data
        :param value: new value
        :return:
        """
        old_value = self.forest.vis_data.get(key, None)
        if old_value is None:
            self.forest.poke("vis_data")
            self.forest.vis_data[key] = value
        elif old_value != value:
            self.forest.poke("vis_data")
            self.forest.vis_data[key] = value

    def get_data(self, key, null=0):
        """ Gets visualization saved within the forest.
        :param key: key in vis_data
        :param null: what to return for missing value
        :return:
        """
        return self.forest.vis_data.get(key, null)

    def reset_node(self, node):
        """

        :param node:
        """
        node.physics_x = True
        node.physics_y = True
        node.adjustment = (0, 0)
        node.use_adjustment = False
        node.locked = False
        #node.update_label()
        node.update_visibility()
        node.magnet_mapper = None

    def prepare_to_normalise(self, tree):
        """ Store the current tree top node position so that the new arrangement can keep that
        point fixed during change.
        :return:
        """
        def find_old_node(node):
            if node.unmoved or node.locked_to_node:
                children = node.get_children(visible=True, similar=True, reverse=True)
                for child in children:
                    f = find_old_node(child)
                    if f:
                        return f
            elif tree.top.physics_x or tree.top.physics_y:
                return node.current_position
            else:
                return node.target_position
        found = find_old_node(tree.top)
        if not found:
            found = (0, 0)
        self._stored_top_node_positions.append(found)

    def draw_tree(self, tree):
        """ Subclasses implement this """
        pass

    def normalise_to_origo(self, tree):
        if tree not in self.forest.trees:
            return
        top_x, top_y = tree.top.target_position
        for node in tree.sorted_nodes:
            if node.locked_to_node:
                continue
            elif node.physics_x and node.physics_y:
                continue
            pass
            node.target_position = node.target_position[0] - top_x, node.target_position[1] - top_y
            node.start_moving()  # restart moving since we shifted the end point
        tree.tree_changed = True

    def normalise_movers_to_top(self, tree):
        if tree not in self.forest.trees:
            return
        i = self.forest.trees.index(tree)
        old = self._stored_top_node_positions[i]
        new = tree.top.target_position
        dx = old[0] - new[0]
        dy = old[1] - new[1]
        for node in tree.sorted_nodes:
            if node.locked_to_node:
                continue
            elif node.physics_x and node.physics_y:
                continue
            node.target_position = node.target_position[0] + dx, node.target_position[1] + dy
            if node.target_position != node.current_position:
                node.start_moving()  # restart moving since we shifted the end point
        tree.tree_changed = True

    # def reset(self):
    # """ Not sure if this should be used at all, it is confusing in its purpose """
    # #print '*** Reset visualization (base) ***'
    # if not self.forest:
    # return

    # for node in ctrl.scene.visible_nodes(self.forest):
    # node.reset()
    # node.update_label()
    # vis = node.is_visible()
    # node.update_visibility(show_edges = True, scope = 0)
    # if node.is_visible() != vis:
    # print 'V node hidden: ', node

    @caller
    def reselect(self):
        """ if there are different modes for one visualization, rotating between different modes 
        is triggered here. 
        
        Default is to randomly jiggle all dynamically placed nodes.
        """
        for node in self.forest.nodes.values():
            if node.use_physics():
                x, y = node.current_position
                node.current_position = x + random.randint(-20, 20), y + random.randint(-20, 20)

    def calculate_movement(self, node: 'Node', other_nodes: list):
        """

        :param node:
        :param other_nodes:
        :return:
        """
        cbr = node.future_children_bounding_rect()
        node_x, node_y = self.centered_node_position(node, cbr)
        x_vel = 0
        y_vel = 0
        alpha = 0.4
        # attract
        cbr_w = cbr.width()
        cbr_h = cbr.height()

        # Sum up all forces pushing this item away.
        for other in other_nodes:
            other_cbr = other.future_children_bounding_rect()
            other_x, other_y = self.centered_node_position(other, other_cbr)
            dist_x, dist_y = node_x - other_x, node_y - other_y
            dist = math.hypot(dist_x, dist_y)
            if dist == 0:
                node_x += 5
                continue
            safe_zone = max(other_cbr.width() + cbr_w, other_cbr.height() +
                            cbr_h) / 2

            if dist == safe_zone:
                pushing_force = 0.1
            elif dist < safe_zone:
                required_dist = abs(dist - safe_zone)
                pushing_force = required_dist / (dist * dist * alpha)
            else:
                continue
            x_vel += pushing_force * dist_x
            y_vel += pushing_force * dist_y

        total_edges = 0
        edges = []
        for e in node.get_edges_up_with_children():
            other = e.start
            while other.locked_to_node:
                other = other.locked_to_node
            if other is node:
                continue
            total_edges += 1
            edges.append((other, e.pull))
        for e in node.get_edges_down_with_children():
            other = e.end
            while other.locked_to_node:
                other = other.locked_to_node
            if other is node:
                continue
            total_edges += 1
            edges.append((other, e.pull))

        for other, edge_pull in edges:
            other_cbr = other.future_children_bounding_rect()
            other_x, other_y = self.centered_node_position(other, other_cbr)
            dist_x, dist_y = node_x - other_x, node_y - other_y
            dist = math.hypot(dist_x, dist_y)
            radius = max(other_cbr.width() + cbr_w, other_cbr.height() +
                      cbr_h)
            if dist != 0 and dist - radius > 0:
                pulling_force = ((dist - radius) * edge_pull * alpha) / dist
                x_vel -= dist_x * pulling_force
                y_vel -= dist_y * pulling_force
            else:
                x_vel += 1

        if not total_edges:
            # pull to center (0, 0)
            x_vel += node_x * -0.009
            y_vel += node_y * -0.009
            # elif (not down) and self.use_gravity:
        elif self.use_gravity:
            y_vel += node._gravity * 2

        return round(x_vel), round(y_vel)

    # def calculateFeatureMovement(self, feat, node):
    # """ Create a cloud of features around the node """
    # xvel = 0.0
    # yvel = 0.0
    # pull=.24
    #     node_x,node_y,node_z=feat.current_position
    #     sx,sy,sz=node.current_position
    #     for item in ctrl.scene.visible_nodes(self.forest):
    #         item_x,item_y,iz=item.current_position
    #         dist_x=int(node_x-item_x)
    #         dist_y=int(node_y-item_y)
    #         dist=math.hypot(dist_x,dist_y)
    #         if dist and dist<100:
    #             l= item.force/(dist*dist)
    #             xvel+=dist_x*l
    #             yvel+=dist_y*l

    #     for item in node.features:
    #         if item is feat: continue
    #         item_x,item_y,iz=item.current_position
    #         dist_x=int(node_x-item_x)
    #         dist_y=int(node_y-item_y)
    #         dist=math.hypot(dist_x,dist_y)
    #         if dist and dist<100:
    #             l= (item.force*2)/(dist*dist)
    #             xvel+=dist_x*l
    #             yvel+=dist_y*l
    #     # gravity
    #     #yvel+=0.6

    #     # Now subtract node's pull.
    #     bx,by= sx-node_x, sy-node_y
    #     dist=math.hypot(bx,by)
    #     if dist>20:
    #         ang=math.atan2(by,bx)
    #         fx=math.cos(ang)*(dist-15)
    #         fy=math.sin(ang)*(dist-15)
    #         xvel+=fx*pull
    #         yvel+=fy*pull

    #     for b in feat.targets:
    #         bbx,bby,bbz=b.current_position
    #         edge_length_x,edge_length_y=bbx-node_x, bby-node_y
    #         xvel+=edge_length_x*pull*.2
    #         yvel+=edge_length_y*pull*.4
    #     return (xvel, yvel, 0)

    def show_edges_for(self, node):
        """ Allow visualizations to override edge visibility. Edges are downward constituent edges of given node.
        :param node: Node to check -- don't need to be used if the result is always the same.
        :return:
        """
        return True

    def centered_node_position(self, node, cbr):
        """ Return coordinates for center of current node. Nodes, especially with children 
        included, are often offset in such way that we shouldn't use bounding_rect's 0,
        0 for their center point.
        
        :param cbr: bounding_rect of node, includes children. QRect or QRectF
        :return: 
        """
        px, py = node.current_position
        cp = cbr.center()
        px += cp.x()
        py += cp.y()
        return px, py



