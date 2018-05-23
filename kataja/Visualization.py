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


def centered_node_position(node, cbr):
    """ Return coordinates for center of current node. Nodes, especially with children
    included, are often offset in such way that we shouldn't use bounding_rect's 0,
    0 for their center point.

    :param cbr: bounding_rect of node, includes children. QRect or QRectF
    :return:
    """
    px, py = node.current_position
    cp = cbr.center()
    return px + cp.x(), py + cp.y()


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
        self.gravity = 2.0
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
        ls = ctrl.settings.get('node_shape')
        if ls in self.banned_node_shapes:
            ls = 0
            while ls in self.banned_node_shapes:
                ls += 1
            ctrl.settings.set('node_shape', ls, level=g.FOREST)
            self.forest.update_node_shapes()

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

    def draw_tree(self, tree_top):
        """ Subclasses implement this """
        pass

    def estimate_overlap_and_shift_tree(self, left_trees, right_tree):
        right_edges = []
        left_nodes = set()
        for left_tree in left_trees:
            for node in left_tree.get_sorted_nodes():
                if node.locked_to_node:
                    continue
                elif node.physics_x and node.physics_y:
                    continue
                left_nodes.add(node)
                br = node.boundingRect()
                tx, ty = node.target_position
                right = br.x() + br.width() + tx
                top = br.y() + ty
                right_edges.append((top, right, top + br.height()))

        left_edges = []
        nodes_to_move = []
        for node in right_tree.get_sorted_nodes():
            if node.locked_to_node:
                continue
            elif node.physics_x and node.physics_y:
                continue
            elif node in left_nodes:
                continue
            br = node.boundingRect()
            tx, ty = node.target_position
            left = br.x() + tx
            top = br.y() + ty
            left_edges.append((top, left, top + br.height()))
            nodes_to_move.append(node)

        dist = 0
        for lt, left, lb in left_edges:
            for rt, right, rb in right_edges:
                if rt > lb:
                    break
                if right > left + dist and ((rt < lt < rb) or (rt < lb < rb) or (lt < rt < lb) or
                        (lt < rb < lb)):
                    dist = right - left

        dist += 30
        for node in nodes_to_move:
            node.target_position = node.target_position[0] + dist, node.target_position[1]
            node.start_moving()

    def normalise_all(self, shift_x=0, shift_y=0):
        print('normalisation shifts: ', shift_x, shift_y)
        free_movers = False
        for node in self.forest.nodes.values():
            if node.locked_to_node:
                continue
            elif node.use_physics():
                free_movers = True
                continue
            node.target_position = (node.target_position[0] + shift_x,
                                    node.target_position[1] + shift_y)
            node.start_moving()  # restart moving since we moved the goal
        return free_movers

    def normalise_to_origo(self, tree_top, shift_x=0, shift_y=0):
        if tree_top not in self.forest.trees:
            return
        top_x, top_y = tree_top.target_position
        for node in tree_top.get_sorted_nodes():
            if node.locked_to_node:
                continue
            elif node.physics_x and node.physics_y:
                continue
            node.target_position = ((node.target_position[0] - top_x) + shift_x,
                                    (node.target_position[1] - top_y) + shift_y)
            node.start_moving()  # restart moving since we shifted the end point

    def normalise_movers_to_top(self, tree_top):
        if tree_top not in self.forest.trees:
            return
        i = self.forest.trees.index(tree_top)
        old = self._stored_top_node_positions[i]
        new = tree_top.target_position
        dx = old[0] - new[0]
        dy = old[1] - new[1]
        for node in tree_top.get_sorted_nodes():
            if node.locked_to_node:
                continue
            elif node.physics_x and node.physics_y:
                continue
            node.target_position = node.target_position[0] + dx, node.target_position[1] + dy
            if node.target_position != node.current_position:
                node.start_moving()  # restart moving since we shifted the end point

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

    def edge_pull(self, node, node_x, node_y, pull_factor=.7):
        # attract
        cbr = node.future_children_bounding_rect()
        cbr_w = cbr.width()
        cbr_h = cbr.height()
        x_vel = 0
        y_vel = 0

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
            other_x, other_y = centered_node_position(other, other_cbr)
            dist_x, dist_y = node_x - other_x, node_y - other_y
            dist = math.hypot(dist_x, dist_y)
            radius = (other_cbr.width() + cbr_w + other_cbr.height() + cbr_h) / 4
            if dist != 0 and dist - radius > 0:
                pulling_force = ((dist - radius) * edge_pull * pull_factor) / dist
                x_vel -= dist_x * pulling_force
                y_vel -= dist_y * pulling_force
            else:
                x_vel += 1

        if not total_edges:
            # pull to center (0, 0)
            x_vel += node_x * -0.009
            y_vel += node_y * -0.009
        return x_vel, y_vel

    def elliptic_repulsion(self, node, node_x, node_y, other_nodes: list, inner_repulsion=.5,
                           outer_repulsion=4, min_push=1, max_push=4):

        # Sum up all forces pushing this item away.
        xvel = 0.0
        yvel = 0.0
        fbr = node.future_children_bounding_rect()
        my_w = fbr.width() / 2
        my_h = fbr.height() / 2
        my_w2 = my_w * my_w
        my_h2 = my_h * my_h
        my_wh = my_w * my_h
        # ( * 16 ) is there so that inner_repulsion and outer_repulsion can be given similar values
        outer_repulsion *= 16

        for other in other_nodes:
            if other is node:
                continue
            fbr_other = other.future_children_bounding_rect()
            other_w = fbr_other.width() / 2
            other_h = fbr_other.height() / 2
            other_x, other_y = other.node_center_position()
            dist_x, dist_y = node_x - other_x, node_y - other_y
            if dist_x == 0 and dist_y == 0:
                xvel += (random.random() * 4) - 2
                yvel += (random.random() * 4) - 2
                return xvel, yvel
            elif dist_x == 0:
                force_ratio = (my_h / my_w + other_h / other_w) / 2
                dist = abs(dist_y)
                gap = dist - my_h - other_h
            elif dist_y == 0:
                force_ratio = 1
                dist = abs(dist_x)
                gap = dist - my_w - other_w
            else:
                g = dist_y / dist_x
                g2 = g * g
                x1 = my_wh / math.sqrt(my_h2 + g2 * my_w2)
                y1 = g * x1
                d1 = math.hypot(x1, y1)
                force_ratio1 = d1 / my_w

                x2 = (other_w * other_h) / math.sqrt(other_h * other_h + g2 * other_w * other_w)
                y2 = g * x2
                d2 = math.hypot(x2, y2)
                force_ratio2 = d2 / other_w
                dist = math.hypot(dist_x, dist_y)
                gap = dist - d2 - d1
                force_ratio = (force_ratio1 + force_ratio2) / 2

            x_component = dist_x / dist
            y_component = dist_y / dist
            if gap <= 0:
                repulsion = min(max(min_push, inner_repulsion * force_ratio * -gap), max_push)
                xvel += repulsion * x_component
                yvel += repulsion * y_component
            else:
                repulsion = (force_ratio * outer_repulsion) / gap
                xvel += repulsion * x_component
                yvel += repulsion * y_component

        return xvel, yvel


    @staticmethod
    def shape_aware_repulsion(node, other_nodes: list, inner_repulsion=.5, outer_repulsion=.5):

        # Sum up all forces pushing this item away.
        xvel = 0.0
        yvel = 0.0
        fbr = node.future_children_bounding_rect()
        my_w = fbr.width()
        my_h = fbr.height()
        node_x, node_y = node.node_center_position()
        # ( * 16 ) is there so that inner_repulsion and outer_repulsion can be given similar values
        outer_repulsion *= 16

        for other in other_nodes:
            if other is node:
                continue
            fbr_other = other.future_children_bounding_rect()
            other_w = fbr_other.width()
            other_h = fbr_other.height()
            minimum_dx = .5 * (my_w + other_w)
            minimum_dy = .5 * (my_h + other_h)
            other_x, other_y = other.node_center_position()
            dist_x, dist_y = int(node_x - other_x), int(node_y - other_y)
            overlap_y = minimum_dy - abs(dist_y)
            overlap_x = minimum_dx - abs(dist_x)
            if dist_x == 0 and dist_y == 0:
                xvel += (random.random() * 4) - 2
                yvel += (random.random() * 4) - 2
            elif overlap_x > 0 and overlap_y > 0:
                if overlap_x > overlap_y:
                    xvel += math.copysign(1.0, dist_x) * inner_repulsion * overlap_x
                else:
                    yvel += math.copysign(1.0, dist_y) * inner_repulsion * overlap_y
            else:
                dist = math.hypot(dist_x - minimum_dx, dist_y - minimum_dy)
                #a = minimum_dy / minimum_dx
                a = other_w / other_h
                repulsion = outer_repulsion / dist
                x_component = dist_x / dist
                y_component = dist_y / dist
                xvel += repulsion * x_component
                yvel += repulsion * y_component * a

        return xvel, yvel

    def feature_sliding(self, node, x_push, y_push):
        if node.node_type == g.FEATURE_NODE:
            if x_push > 0:
                x_push = 0
            if y_push < 0:
                y_push = 0
        return x_push, y_push

    def gravity_force(self, node, is_alone):
        if is_alone:
            return 0, self.gravity
        return 0, 0

    def speed_noise(self, node, x_vel, y_vel):
        if abs(x_vel) > 3:
            y_vel += (random.random() * -4) + 2
        if abs(y_vel) > 3:
            x_vel += (random.random() * -4) + 2
        return x_vel, y_vel

    def calculate_movement(self, node: 'Node', other_nodes: list, heat: float):
        """ Base force-directed graph calculation for nodes that are free to float around,
        not given positions by visualisation algo.
        :param node:
        :param other_nodes:
        :return:
        """
        cbr = node.future_children_bounding_rect()
        node_x, node_y = centered_node_position(node, cbr)

        # Sum up edges pulling nodes together
        x_pull, y_pull = self.edge_pull(node, node_x, node_y)
        # Add a bit of random shuffle if moving fast to prevent lockups

        # Sum up all forces pushing this item away.
        x_push, y_push = self.elliptic_repulsion(node, node_x, node_y, other_nodes)

        # Let feature nodes slide through constituents on their way down -- prevent pushing up
        x_push, y_push = self.feature_sliding(node, x_push, y_push)
        if y_push < 0:
            y_push = 0

        # Add gravity (set it 0 to disable it), but don't let unconnected nodes fall of the screen
        gx, gy = self.gravity_force(node, bool(x_pull or y_pull))

        x_vel = (x_pull + x_push) * heat + gx
        y_vel = (y_pull + y_push) * heat + gy

        # Add random shuffle for high-energy situations
        x_vel, y_vel = self.speed_noise(node, x_vel, y_vel)
        return x_vel, y_vel

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




