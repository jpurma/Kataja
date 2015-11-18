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

import kataja.globals as g


class Grid:
    """ 2-dimensional grid to help drawing nodes and avoiding overlaps """

    def __init__(self):
        self.rows = []
        self.x_adjustment = 0
        self.y_adjustment = 0
        self.width = 0
        self.height = 0

    def __str__(self):
        rowlist = []
        for column in self.rows:
            collist = []
            for item in column:
                if item.node_type == g.CONSTITUENT_NODE:
                    collist.append(item.label or 'Placeholder')
                else:
                    collist.append(str(item))
            rowlist.append(', '.join(collist))
        return '\n'.join(rowlist)

    def ascii_dump(self):
        """
        Give an ascii presentation of the grid for debugging.
        """
        for row in self.rows:
            s = []
            for item in row:
                if hasattr(item, 'node_type'):
                    s.append('O')
                elif isinstance(item, int) and item == 1:
                    s.append('|')
                else:
                    s.append('.')
            print(''.join(s))
        print('starting coords (%s, %s)' % (-self.x_adjustment, -self.y_adjustment))

    def get(self, x, y):
        """ Get object in grid at given coords. None if empty.
        :param x: int
        :param y: int
        """
        x += self.x_adjustment
        y += self.y_adjustment
        if x < 0 or y < 0:
            return None
        if x > self.width - 1 or y > self.height - 1:
            return None
        else:
            return self.rows[y][x]

    def set(self, x, y, item, w=1, h=1, left=0, top=0, raw=False):
        """
        Put object into grid into coords x,y. If object should take several slots, use w and h to give its size.
        The grid is expanded to fit the object.
        :param x: int
        :param y: int
        :param item: node
        :param w: int
        :param h: int
        :param left: int
        :param top: int
        :param raw: bool -- if raw is True, don't use adjustments.
        :return: x_a, y_a -- if they were negative when given, this is the adjustment required
        """
        if raw:
            assert x >= 0 and y >= 0
        else:
            x += self.x_adjustment
            y += self.y_adjustment
        while x < 0:
            self.insert_column()
            x += 1
            self.x_adjustment += 1
        while y < 0:
            self.insert_row()
            y += 1
            self.y_adjustment += 1

        if w > 1 or h > 1:
            if left or top:
                l = x + left
                u = y + top
            else:
                w2 = (w - 1) // 2
                h2 = (h - 1) // 2
                l = x - w2
                u = y - h2
            if l < 0:
                x -= l
                l = 0
            if u < 0:
                y -= u
                u = 0
            for ny in range(u, u + h + 1):
                for nx in range(l, l + w + 1):
                    self.set(nx, ny, 1)
            self.set(x, y, item)
        else:
            #print('drawing point to ', x, y)
            while x > self.width - 1:
                for row in self.rows:
                    row.append(0)
                self.width += 1
            while y > self.height - 1:
                new_row = [0] * self.width
                self.rows.append(new_row)
                self.height += 1
            try:
                old_item = self.rows[y][x]
                if old_item and hasattr(old_item, 'node_type'):
                    print('*** prevented overwriting node in grid (%s, %s)' % (x, y))
                    self.ascii_dump()
                    print('** --- please fix the cause ---')
                else:
                    self.rows[y][x] = item
            except IndexError:
                print('catched index error')
                print(self.rows, len(self.rows), y, x)
            assert len(self.rows[y]) == self.width
            assert len(self.rows) == self.height

    def row(self, y):
        """
        Return one row from the grid, normalized from possible negative indices
        :param y:
        :return:
        """
        y += self.y_adjustment
        if y < self.height:
            return self.rows[y]
        else:
            return []

    def raw_row(self, y):
        """
        Return one row from the grid, using raw indices starting from 0
        :param y:
        :return:
        """
        if y < self.height:
            return self.rows[y]
        else:
            return []

    def find_in_grid(self, item_to_find):
        """
        Return coordinates of item in grid as a tuple. -1, -1 if not found
        :param item_to_find:
        :return:
        """
        for y, row in enumerate(self.rows):
            for x, item in enumerate(row):
                if item is item_to_find:
                    return x, y
        return -1, -1

    def last_filled_column(self, y):
        """
        Return index of last column that is not empty.
        :param y:
        :return:
        """
        row = self.raw_row(y)
        found = -1
        for i, item in enumerate(row):
            if item:
                found = i
        return found - self.x_adjustment

    def first_filled_column(self, y):
        """
        Return index of first column that is not empty.
        :param y:
        :return:
        """
        row = self.raw_row(y)
        for i, item in enumerate(row):
            if item:
                return i - self.x_adjustment
        return None

    def insert_row(self):
        """
        Add one row to the grid.
        """
        row = self.width * [0]
        self.height += 1
        self.rows.insert(0, row)

    def insert_column(self):
        """ Add one column to left ( each row has an empty slot at index 0)
        :return:
        """
        for row in self.rows:
            row.insert(0, 0)
        self.width += 1

    @staticmethod
    def pixelated_path(start_x, start_y, end_x, end_y):
        """ Return the grid blocks that are crossed in the line between start and end. start and end blocks are omitted.
        :param start_x:
        :param start_y:
        :param end_x:
        :param end_y:
        :return:
        """
        used = {(start_x, start_y), (end_x, end_y)}
        path = []
        dx = end_x - start_x
        dy = end_y - start_y
        if dx == 0: # simple case, line straight up or down, but handled separately to avoid division by zero
            if dy < 0:
                step = -1
            else:
                step = 1
            for y in range(0, dy, step):
                p = start_x, start_y + y
                if p not in used:
                    path.append(p)
                    used.add(p)
            return path

        d = float(dy) / float(dx)
        if abs(dx) > abs(dy):
            if dx < 0:
                step = -1
            else:
                step = 1
            for x in range(0, dx, step):
                p = start_x + x, start_y + int(d * x)
                if p not in used:
                    path.append(p)
                    used.add(p)
        else:
            if dy < 0:
                step = -1
            else:
                step = 1
            for y in range(0, dy, step):
                p = start_x + int(y / d), start_y + y
                if p not in used:
                    path.append(p)
                    used.add(p)
        return path

    def is_path_blocked(self, path):
        """ Try to draw a line in grid from start to end (omitting start and end). If the path is empty, fill them
         with marker and return None, if it is occupied, return True
        :return: bool - True if there are already objects in path
        """
        for x, y in path:
            if self.get(x, y):
                return True
        return False

    def fill_path(self, path, marker=1):
        """ Draws the line in grid given by path. Marker can be given as parameter, we usually use 1 for a line part.
        :param path:
        :param marker:
        :return:
        """
        for x, y in path:
            self.set(x, y, marker)

    def merge_grids(self, right_grid, extra_padding=0):
        if right_grid and not self:
            self.rows = right_grid.rows
            self.x_adjustment = right_grid.x_adjustment
            self.y_adjustment = right_grid.y_adjustment
            self.width = right_grid.width
            self.height = right_grid.height
            return
        elif self and not right_grid:
            return
        paddings = []
        # actual merging of grids begins with calculating the closest fit for two grids
        for row_n, right_side_row in enumerate(right_grid):
            # measuring where the right border of the left grid should be.
            left_side_occupied = self.last_filled_column(row_n) + 1
            # measuring where the left border of the right grid should be
            right_side_margin = right_grid.first_filled_column(row_n)
            if right_side_margin is None:
                paddings.append(0)
            else:
                paddings.append(left_side_occupied - right_side_margin)
        if paddings:
            padding = max(paddings) + extra_padding
        else:
            padding = extra_padding
        for row_n, right_row in enumerate(right_grid):
            for col_n, right_row_node in enumerate(right_row):
                if right_row_node:
                    self.set(col_n + padding, row_n, right_row_node, raw=True)

    def __iter__(self):
        return self.rows.__iter__()

    def __len__(self):
        return len(self.rows)

# def _closestDistance(nodeA, nodeB,Ax,Ay):
# nodeAx=Ax or nodeA.pos_tuple[0]
# nodeAy=Ay or nodeA.pos_tuple[1]
# nodeBx=nodeB.pos_tuple[0]
#    nodeBy=nodeB.pos_tuple[1]
#    dist_x=nodeAx-nodeBx
#    dist_y=nodeAy-nodeBy
#    if abs(dist_x)>abs(dist_y):
#        if nodeAx<nodeBx: # node A is left to node B
#            if nodeAx+nodeA.magnets[1]<nodeBx+nodeB.magnets[3]:  # node A's right border is left to node B
#                magnetAx=nodeA.magnets[1] # right
#                magnetBx=nodeB.magnets[3] # left
#            elif nodeAx<nodeBx+nodeB.magnets[3]:
#                magnetAx=0
#                magnetBx=nodeB.magnets[3] # left
#            else: # node B is inside of node A, but at its right side
#                magnetAx=0
#                magnetBx=0
#        else: # node A is right to node B
#            if nodeAx+nodeA.magnets[3]>nodeBx+nodeB.magnets[1]: # node A's left border is right to node B
#                magnetAx=nodeA.magnets[3] # left
#                magnetBx=nodeB.magnets[1] # right
#            elif nodeAx>nodeBx+nodeB.magnets[1]:
#                magnetAx=0
#                magnetBx=nodeB.magnets[1] # left
#            else: # node B is inside of node A, but at its left side
#                magnetAx=0
#                magnetBx=0 # right
#        dist_x=(nodeAx+magnetAx)-(nodeBx+magnetBx)
#    else:
#        if nodeAy<nodeBy: # node A is on top of node B
#            if nodeAy+nodeA.magnets[2]<nodeBy+nodeB.magnets[0]: # if node A's bottom is on top to node B
#                magnetAy=nodeA.magnets[2] # down
#                magnetBy=nodeB.magnets[0] # up
#            elif nodeAy<nodeBy+nodeB.magnets[0]:
#                magnetAy=0
#                magnetBy=nodeB.magnets[0] # up
#            else: # node B is inside of node A, at the top side of it
#                magnetAy=0
#                magnetBy=0 # up
#        else:
#            if nodeAy+nodeA.magnets[0]>nodeBy+nodeB.magnets[2]: # if node A's top is below nodeB
#                magnetAy=nodeA.magnets[0] # up
#                magnetBy=nodeB.magnets[2] # down
#            elif nodeAy>nodeBy+nodeB.magnets[2]: # if node A's top is below nodeB
#                magnetAy=0
#                magnetBy=nodeB.magnets[2] # down
#            else: # node B is inside of node A, at the bottom half of it
#                magnetAy=0
#                magnetBy=0 # down
#        dist_y=(nodeAy+magnetAy)-(nodeBy+magnetBy)
#    return dist_x, dist_y
