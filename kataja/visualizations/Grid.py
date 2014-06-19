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

from kataja.ConstituentNode import ConstituentNode
from kataja.Node import Node


class Grid:
    """ 2-dimensional grid to help drawing """

    def __init__(self):
        self._rows = []
        self._width = 0
        self._height = 0

    def __str__(self):
        rowlist = []
        for column in self._rows:
            collist = []
            for item in column:
                if isinstance(item, ConstituentNode):
                    collist.append(item.syntactic_object.get_label())
                else:
                    collist.append(str(item))
            rowlist.append(', '.join(collist))
        return '\n'.join(rowlist)

    def ascii_dump(self):
        """


        """
        for row in self._rows:
            s = []
            for item in row:
                if isinstance(item, Node):
                    s.append('O')
                elif isinstance(item, int) and item == 1:
                    s.append('|')
                else:
                    s.append('.')
            print(''.join(s))


    def get(self, x, y):
        """



        :param x:
        :param y:
        :param int x:
        :param int y:
        """
        if x > self._width - 1 or y > self._height - 1:
            return None
        else:
            return self._rows[y][x]

    def set(self, x, y, item, w=1, h=1):
        """

        :param x:
        :param y:
        :param item:
        :param w:
        :param h:
        """
        if w > 1 or h > 1:
            l = x - (w - 1) / 2
            r = x + (w - 1) / 2
            u = y - (h - 1) / 2
            d = y + (h - 1) / 2
            if l < 0:
                r -= l
                x -= l
                l = 0
            if u < 0:
                d -= u
                y -= u
                u = 0
            for ny in range(u, d + 1):
                for nx in range(l, r + 1):
                    self.set(nx, ny, 1)
            self.set(x, y, item)
        else:
            while x > self._width - 1:
                for row in self._rows:
                    row.append(0)
                self._width += 1
            while y > self._height - 1:
                new_row = [0] * self._width
                self._rows.append(new_row)
                self._height += 1
            # print x, y
            try:
                self._rows[y][x] = item
            except IndexError:
                print('catched index error')
                print(self._rows, len(self._rows), y, x)
            assert len(self._rows[y]) == self._width
            assert len(self._rows) == self._height

    def row(self, y):
        """

        :param y:
        :return:
        """
        if y < self._height:
            return self._rows[y]
        else:
            return []

    def find_in_grid(self, item_to_find):
        """

        :param item_to_find:
        :return:
        """
        for y, row in enumerate(self._rows):
            for x, item in enumerate(row):
                if item is item_to_find:
                    return x, y
        return -1, -1


    def last_filled_column(self, y):
        """

        :param y:
        :return:
        """
        row = self.row(y)
        found = -1
        for i, item in enumerate(row):
            if item:
                found = i
        return found

    def first_filled_column(self, y):
        """

        :param y:
        :return:
        """
        row = self.row(y)
        for i, item in enumerate(row):
            if item:
                return i
        return -1

    def insert_row(self):
        """


        """
        row = self._width * [0]
        self._height += 1
        self._rows.insert(0, row)

    def __iter__(self):
        return self._rows.__iter__()

# def _closestDistance(nodeA, nodeB,Ax,Ay):
# nodeAx=Ax or nodeA.pos_tuple[0]
# nodeAy=Ay or nodeA.pos_tuple[1]
#    nodeBx=nodeB.pos_tuple[0]
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
