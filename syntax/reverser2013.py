# coding=utf-8
""" Testing a weird reversibility hypothesis I have, part 2 """
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


class Constituent:
    """
    Constituent where Merge is an ability of a constituent.
    """

    def __init__(self, id, left=None, right=None):
        id = id.replace(' ', '_')
        self.id = id
        self.left = left
        self.right = right

    def __str__(self):
        if self.left and self.right:
            return '[%s %s]' % (self.left, self.right)
        else:
            return self.id

    def __unicode__(self):
        if self.left and self.right:
            return '[%s %s]' % (self.left.__unicode__(), self.right.__unicode__())
        else:
            return self.id

    def merge(self, other):
        """

        :param other:
        :return:
        """
        new = Constituent(other.id, left=other, right=self)
        return new

    def find(self, label):

        """

        :param label:
        :return:
        """
        if self.id == label:
            return self
        if self.left:
            found = self.left.find(label)
            if found:
                return found
        if self.right:
            found = self.right.find(label)
            if found:
                return found
        return None


    def iterate(self):
        """


        :return:
        """
        result_list = []

        def recursive_walk(item):
            """

            :param item:
            """
            if item:
                result_list.append(item)
                recursive_walk(item.left)
                recursive_walk(item.right)

        recursive_walk(self)
        return result_list

    def linearize(self):
        """


        :return:
        """
        found = []
        for node in self.iterate():
            if node.id in found:
                continue
            else:
                found.append(node.id)
        return ' '.join(found)


tree = None
history = []

c = input('-->').strip()
while c:
    if c == 'u':
        if tree:
            tree = tree.right
            history.pop()
    elif c == 'h':
        print(history)
    else:
        history.append(c)
        if tree:
            C = tree.find(c)
        else:
            C = None
        if C:
            tree = tree.merge(C)
        else:
            new = Constituent(c)
            if tree:
                tree = tree.merge(new)
            else:
                tree = new
    print(tree)
    if tree:
        print(tree.linearize())
    c = input('-->').strip()
print(tree)
