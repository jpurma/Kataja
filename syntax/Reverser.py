# -*- coding: UTF-8 -*-
""" Testing a weird reversibility hypothesis I have """
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


from random import randint, choice
import sys

log_level = 4


def log(message, importance=3):
    """

    :param message:
    :param importance:
    """
    if importance >= log_level:
        print(message)


class Node:
    """
    A constituent
    """

    def __init__(self, id, left=None, right=None, features=None):
        """ Nodes are constituents """
        if not features:
            features = []
        self.label = id
        self.left = left
        self.right = right
        self._plus_features = set()
        self._neutral_features = set()
        self._minus_features = set()
        for f in features:
            self.addFeature(f)

    def __repr__(self):
        if self.left or self.right:
            return '[.' + self.printFeatures() + ' ' + str(self.left) + ' ' + str(self.right) + ' ]'
        else:
            return self.printFeatures() + ':' + self.label

    # ## Nondestructive merge & inheritance


    def merge(self, other):
        """ This node (left) merged to another node (right), and a new node is returned
        :param other:
        """
        new_node = Node(self.label, self, other)
        return new_node

    def getSignedFeatures(self):
        """ Return features as a simple list where features have their signs added to them """
        return ['+' + x for x in self._plus_features] + ['-' + x for x in self._minus_features] + ['=' + x for x in
                                                                                                   self._neutral_features]

    def get_features(self):
        """ compute what features this Node has inherited -- nondestructive version """
        # for any element that is result of a merge, these are empty sets!
        my_plusses = self._plus_features.copy()
        my_minuses = self._minus_features.copy()
        my_neutrals = self._neutral_features.copy()
        # all features are inherited, but there are few rules of when
        # elements remove each other

        if self.left:
            pl_l, min_l, neut_l = self.left.get_features()
        else:
            pl_l, min_l, neut_l = set(), set(), set()
        if self.right:
            pl_r, min_r, neut_r = self.right.get_features()
        else:
            pl_r, min_r, neut_r = set(), set(), set()
        # include following rules of feature removal:
        # M('+','=') => ''
        removable = pl_l & neut_r
        if removable:
            pl_l -= removable
            neut_r -= removable
        # M('+','-') => ''
        removable = pl_l & min_r
        if removable:
            pl_l -= removable
            min_r -= removable
        # M('=','-') => '='
        if neut_l & min_r:
            min_r -= neut_l & min_r
        # unification of both sets
        pl = pl_l | pl_r | my_plusses
        mi = min_l | min_r | my_minuses
        neut = neut_l | neut_r | my_neutrals
        return pl, mi, neut

    # ## Destructive merge -- merge that eats the features that justified the merge
    # this has a result that the same element cannot be merged many time for same reasons


    def mergeD(self, other):
        # merge needs to do more work now. It removes features from merged elements.
        # Watch out you don't do any trial merges before the actual one!
        """

        :param other:
        :return:
        """
        new_node = Node(self.label, self, other)
        pl_l, min_l, neut_l = self.get_features()
        pl_r, min_r, neut_r = other.get_features()
        # include following rules of feature removal:
        # M('+','=') => ''
        removable = pl_l & neut_r
        if removable:
            pl_l -= removable
            neut_r -= removable
        # M('+','-') => ''
        removable = pl_l & min_r
        if removable:
            pl_l -= removable
            min_r -= removable
        # M('=','-') => '='
        if neut_l & min_r:
            min_r -= neut_l & min_r

        new_node._plus_features = pl_l | pl_r
        new_node._minus_features = min_l | min_r
        new_node._neutral_features = neut_l | neut_r

        # put features back to their place
        self._plus_features = pl_l
        self._minus_features = min_l
        self._neutral_features = neut_l
        other._plus_features = pl_r
        other._minus_features = min_r
        other._neutral_features = neut_r
        return new_node

    def get_featuresD(self):
        # this can be simple now that merge is so complex
        """


        :return:
        """
        return self._plus_features, self._minus_features, self._neutral_features

    # switch to destructive merge. comment these lines to turn off
    merge = mergeD
    get_features = get_featuresD

    def getPosFeatures(self):
        """


        :return:
        """
        return self.get_features()[0]

    def getNegFeatures(self):
        """


        :return:
        """
        return self.get_features()[1]

    def getNeutralFeatures(self):
        """


        :return:
        """
        return self.get_features()[2]

    def printFeatures(self):
        """


        :return:
        """
        plusses, minuses, neutrals = self.get_features()
        s = ''
        if plusses:
            s = '+' + ('+'.join(plusses))
        if neutrals:
            s += '=' + ('='.join(neutrals))
        if minuses:
            s += '-' + ('-'.join(minuses))
        return s

    def clearFeatures(self):
        """ remove all features. probably in order to try with another set of features. """
        self._plus_features = set()
        self._neutral_features = set()
        self._minus_features = set()

    def addFeature(self, feature):
        """

        :param feature:
        """
        if feature.startswith('+'):
            self._plus_features.add(feature[1:])
        elif feature.startswith('-'):
            self._minus_features.add(feature[1:])
        elif feature.startswith('='):
            self._neutral_features.add(feature[1:])

    def removeFeature(self, feature):
        """

        :param feature:
        """
        if feature.startswith('+'):
            self._plus_features.discard(feature[1:])
        elif feature.startswith('-'):
            self._minus_features.discard(feature[1:])
        elif feature.startswith('='):
            self._neutral_features.discard(feature[1:])


    def match(self, needy, strict=False):
        """

        :param needy:
        :param strict:
        :return:
        """
        if self == needy:  # heuristic rule, not founded on theory
            return False
        if not needy:
            return False
        # returns set of those features that both share

        if strict:
            # only +x can satisfy -x, and +x-x cannot satisfy -x in any case.
            # (if +x-x would be allowed, element with this combination could be endlessly merged to itself)
            # (or make sure that +x-x cannot be created or it cannot be formed as a result of other merges)
            return needy.getNegFeatures() & (self.getPosFeatures() - self.getNegFeatures())
        else:
            # either +x or =x can satisfy -x
            return needy.getNegFeatures() & (self.getPosFeatures() | self.getNeutralFeatures())

    def findMatchFor(self, needy):
        """

        :param needy:
        :return:
        """
        m = self.match(needy)  # , strict=True)
        if m:
            return self
        if self.left:
            m = self.left.findMatchFor(needy)
            if m:
                return self.left
        if self.right:
            m = self.right.findMatchFor(needy)
            if m:
                return self.right
        return None

    def isParentOf(self, node):
        """

        :param node:
        :return:
        """

        def _find(n, target):
            if n == target:
                return True
            if n.left and _find(n.left, target):
                return True
            if n.right and _find(n.right, target):
                return True
            return False

        return _find(self, node)

    def copy(self):
        """


        :return:
        """
        new = Node(self.label)
        if self.left:
            new.left = self.left.copy()
        if self.right:
            new.right = self.right.copy()
        new._plus_features = self._plus_features.copy()
        new._neutral_features = self._neutral_features.copy()
        new._minus_features = self._minus_features.copy()
        return new


def Merge(node1, node2):
    """

    :param node1:
    :param node2:
    :return:
    """
    if hasattr(node1, 'merge'):
        return node1.merge(node2)
    else:
        return Node(node1.label, node1, node2)


def pause():
    """ Checks if q is pressed to quit. """
    N = input('')
    if N == 'q':
        sys.exit()


class Parser:
    """
    Parser to turn string into constituents and start pushing them into system.
    """

    def __init__(self):
        self.trees_n = 3
        self.rounds = 5000
        self.trees = self.trees_n * [None]
        self.lexicon = {}
        self.lexicon_history = {}  # not used yet
        self.features = list('abcd')  # defghij')
        self.text = ''
        self.results = []
        self.max_features = 3


    def randomly_assign_all_features(self, n=3):
        """

        :param n:
        """
        for item in list(self.lexicon.values()):
            item.clearFeatures()
            for c in range(0, n):
                feature = None
                while (
                        not feature) or feature in item._plus_features or feature in item._minus_features or feature in item._neutral_features:
                    feature = self.features[randint(0, len(self.features) - 1)]
                polarity = '-=+'[randint(0, 2)]
                item.addFeature(polarity + feature)
        print('Lexicon:', end=' ')
        print(self.lexicon)


    def adjust_one_feature(self, words):
        """ This forces a single random mutation in the lexicon
        :param words:
        """
        word = choice(words)
        node = self.lexicon[word]
        features = node.getSignedFeatures()
        pos = randint(0, self.max_features - 1)
        if pos < len(features):
            node.removeFeature(features[pos])
        feature = None
        while (
                not feature) or feature in node._plus_features or feature in node._minus_features or feature in node._neutral_features:
            feature = self.features[randint(0, len(self.features) - 1)]
        polarity = '-=+'[randint(0, 2)]
        node.addFeature(polarity + feature)
        self.lexicon[word] = node
        print('Lexicon:', end=' ')
        print(self.lexicon)


    def addNode(self, node):
        """

        :param node:
        :return:
        """
        for i, tree in enumerate(self.trees):
            if not tree:
                print(node, 'fills empty position')
                self.trees[i] = node
                return True
            if node.match(tree):
                print('%s merged to [%s]' % (node, i))
                merged = Merge(node, tree)
                self.trees[i] = merged
                return True
        print("couldn't add node")
        return False

    def repair(self):
        # try merging top elements to each other
        """


        :return:
        """
        print('doing repairs...', end=' ')
        for i, left in enumerate(self.trees):
            if not left:
                continue
            for j, right in enumerate(self.trees):
                if (not right) or i == j:
                    continue
                if left.match(right):
                    print('unifying merge, [%s] to [%s]' % (i, j))
                    merged = Merge(left, right)
                    self.trees[j] = merged
                    self.trees[i] = None
                    return True
        # try merging deeper elements to each other
        for i, left in enumerate(self.trees):
            if not left:
                continue
            for j, right in enumerate(self.trees):
                node = left.findMatchFor(right)
                if node and node != left and node.get_features() != right.get_features():
                    if j == i:
                        print('internal merge, %s to %s' % (node, right))
                    else:
                        print('crossing merge, %s to %s' % (node, right))
                    merged = Merge(node, right)
                    self.trees[j] = merged
                    # print merged
                    # pause()
                    return True
        print('None')

    def parse(self, original_feed):
        """

        :param original_feed:
        """
        crash = True
        c = 0
        repair_all = True
        J_for_these_features = 0
        involved_words = []

        while crash and c < self.rounds:
            feed = list(original_feed)
            while feed:
                text = feed.pop(0)
                print('***************************')
                print(text)
                self.text = text
                stack = text.split()
                stack.reverse()
                # this is a mutable copy where words can be popped out.
                involved_words = []
                while stack:
                    # prepare new node
                    word = stack.pop()
                    if word in self.lexicon:
                        node = self.lexicon[word].copy()
                    else:
                        node = Node(word)
                        self.lexicon[word] = node
                    involved_words.append(word)  # this is useful list if the sentence crashes
                    # print '** adding new node: %s' % node
                    # merge it to somewhere
                    crash = False
                    success = self.addNode(node)
                    print(self.trees)

                    # there are two possibilities:
                    # 1. repair only when necessary (and clean at end)
                    if not repair_all:
                        while not success:
                            print("can't merge, trying to repair.")
                            repair_is_success = self.repair()
                            print(self.trees)
                            if not repair_is_success:
                                print('Repairs failed.')
                                crash = True
                                break
                            success = self.addNode(node)
                            print(self.trees)
                    # 2. repair all that can be repaired
                    if repair_all:
                        if not success:
                            crash = True
                            break
                        while self.repair():
                            print('repaired:', self.trees)
                            # endless recursion
                            if len(str(self.trees)) > 600:
                                print('Endless recursion, aborting.')
                                crash = True
                                break

                    if crash:
                        break
                if not crash:
                    if not repair_all:
                        print('trying final repairs')
                        while self.repair():
                            print('final repairs:', self.trees)
                            # endless recursion
                            if len(str(self.trees)) > 600:
                                print('Endless recursion, aborting.')
                                crash = True
                                break

                if not crash:
                    if self.linearize() != self.text:
                        print("linearization doesn't match with original:")
                        crash = True
                        # else:

                        # pause()
                if not crash:
                    not_empty = 0
                    for tree in self.trees:
                        if tree and tree.getNegFeatures() or tree and tree.getPosFeatures():
                            print('too many features left:' + tree.printFeatures())
                            crash = True
                            break
                        if tree:
                            not_empty += 1
                    if not_empty > 1:
                        crash = True
                if crash:
                    break
                else:
                    print('**** SUCCESS! ****', c)
                    print(self.linearize())
                    self.results.append(self.trees)
                    for i, tree in enumerate(self.trees):
                        print('[%s]: %s' % (i, tree))
                    J_for_these_features += 1

                    # pause()
            if crash:
                c += 1
                print(self.linearize())
                # pause()
                print('** Round %s **' % c)
                self.trees = self.trees_n * [None]
                J_for_these_features += 1

                # Crash has occured, now try to adjust features.

                # Stupid way: randomly create a new set of features
                # self.randomly_assign_all_features()
                # self.results=[]

                # Better way:
                # try small improvements -- adjust only one feature
                # later we can try adjusting features that have low confidence, but now just adjust one
                self.adjust_one_feature(involved_words)
                self.results = []
                pause()

        print('** Finished at round %s **' % c)
        print(self.linearize())
        print(self.results)
        print(self.lexicon)
        print('done.')

    def linearize(self):
        """


        :return:
        """
        words = []

        def spell_out(node):
            """

            :param node:
            :return:
            """
            if not node:
                return
            if node.left:
                spell_out(node.left)
            if node.right:
                spell_out(node.right)
            if (not node.left) and (not node.right):
                if node.label not in words:
                    words.append(node.label)

        for tree in self.trees:
            spell_out(tree)
        return ' '.join(words)


P = Parser()

feed = ['Jukka juoksee', 'Jukka juoksee kotiin', 'kotiin Jukka juoksee', 'asum me ko han', 'Jukka näkee Pekan',
        'Pekan näkee Jukka', 'Pekka juoksee kotiin', 'Jukka heittää palloa', 'Pallo lentää koriin']

P.parse(feed[0:2])


