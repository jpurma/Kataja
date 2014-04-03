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


from ConfigParser import ConfigParser
from random import randint, choice
import re

from syntax.ConfigurableConstituent import ConfigurableConstituent
from syntax.ConfigurableFeature import Feature
from syntax.utils import load_lexicon, save_lexicon, time_me


DEFAULT = """

[Computational System]

external_merge_method = set_merge
internal_merge_method = set_merge
after_merge = None

[Lexicon]

lexicon_path= testlexicon.txt


[Constituents]

constituent= ConfigurableConstituent

[Features]

feature= ConfigurableFeature

"""


class ConfigurableUG:
    """ Configurable UG has lots of possible axioms and definitions and UG uses a partial set of these """

    def __init__(self, config_path='kataja.cfg'):
        self.config = ConfigParser()
        # self.config.readfp(io.BytesIO(DEFAULT))
        self.config.read(config_path)
        # self.Constituent=constituent
        # self.Feature=feature
        # self.lexicon=load_lexicon(lexicon, constituent, feature)
        # self.structure=None

        self.dominates = self.undefined


    def undefined(self, *args, **kw):
        print 'Undefined function called'

    # ## Definitions for edges, operations and conditions from Carnie 2010

    # ## DOMINANCE

    def set_based_dominance(self, dom, sub):
        """ Simple dominance, 'dominance is essentially a containment edge' (Carnie 2010, p. 29) """
        return sub in dom

    dominates = set_based_dominance

    def properly_dominates(self, dom, sub):
        return self.dominates(dom, sub) and dom != sub

    def is_root_node(self, A, structure):
        """ (5a) Root node: the node that dominates everything, but is dominated by nothing except itself (Carnie 2010, p. 29) """
        for B in structure:
            if not self.dominates(A, B):
                return False
            if B != A and self.dominates(B, A):
                return False
        return True

    def is_terminal_node(self, A, structure):
        """ (5b) Terminal node: A node that dominates nothing except itself. (Carnie 2010, p. 30) """
        for B in structure:
            if A != B and self.dominates(A, B):
                return False
        return True

    def is_non_terminal_node(self, node, structure):
        """ (5c) Non-terminal node: A node that dominates something except itself. (Carnie 2010, p. 30) """
        for B in structure:
            if node != B and self.dominates(node, B):
                return True
        return False


    # ## Dominance Axioms

    def check_dominance_axioms(self, structure):
        print 'Reflexivity Axiom:', self.reflexivity_axiom(structure)
        print 'Single Root Axiom:', self.single_root_axiom(structure)
        print 'Dominance Transitivity Axiom:', self.dominance_transitivity_axiom(structure)
        print 'Dominance Antisymmetry Axiom:', self.dominance_antisymmetry_axiom(structure)
        print 'No Multiple Mothers Axiom:', self.no_multiple_mothers_axiom(structure)

    def reflexivity_axiom(self, structure):
        """ (A1) all:x belonging to N, x dominates x. (Carnie 2010, p. 31) """
        for node in structure:
            if not self.dominates(node, node):
                return False
        return True


    def single_root_axiom(self, structure):
        """ (A2) exists:x, all:y belonging to N that x dominates y. (Carnie 2010, p. 31) """
        for node in list(structure):
            found = False
            for other_node in structure:
                if self.dominates(other_node, node):
                    found = True
            if not found:
                return True
        return False

    def dominance_transitivity_axiom(self, structure):
        """ (A3) all: x,y,z belonging to N: (x dominates y) & (y dominates z) -> (x dominates z) (Carnie 2010, p. 33)"""
        for x in structure:
            ys = [y for y in structure if self.dominates(x, y)]
            zetas = []
            for y in ys:
                for z in structure:
                    if self.dominates(y, z):
                        zetas.append(z)
            for obj in zetas:
                if not self.dominates(x, obj):
                    return False
        return True

    def dominance_antisymmetry_axiom(self, structure):
        """ (A4) all: x,y belonging to N: (x dominates y) & (y dominates x) -> (x = y) (Carnie 2010, p. 31)"""
        for x in structure:
            dominated = [y for y in structure if self.dominates(x, y)]
            ys = [y for y in dominated if self.dominates(y, x)]
            for y in ys:
                if x != y:
                    return False
        return True


    def no_multiple_mothers_axiom(self, structure):
        """ (A5) all: x,y,z belonging to N: (x dominates y) & (y dominates z) -> (x dominates y) or (y dominates x) (Carnie 2010, p. 34)"""
        for z in structure:
            for y in structure:
                if self.dominates(y, z):
                    for x in structure:
                        if self.dominates(x, z):
                            if not (self.dominates(x, y) or self.dominates(y, x)):
                                return False
        return True

    # Immediate dominance

    def immediate_dominance_carnie(self, x, z, structure):
        """ (12) Node A immediately dominates node B if there is no Intervening node G that is properly dominated by A and properly dominates B. (In other words, A is the first node that dominates B.) (Carnie 2010, p. 35)
            all x,z: not exists y, where x prop.dominates y and y prop.dominates z
            """
        # fix, not based on Carnie:
        if not self.dominates(x, z):
            return False
        for y in structure:
            if y == x or y == z:
                continue
            if self.properly_dominates(x, y) and self.properly_dominates(y, z):
                return False
        # I'm not sure if this is correct, what if x and z don't have any dominance edge?
        return True

    def immediate_dominance_pullum_scholz(self, x, y, structure):
        """ (x dominates y) & (x!=y) & not exists z:[(x dominates z) & (z dominates y) & (x!=z) & (z!=y) ] (Carnie 2010, p. 35)"""
        if x == y:
            return False
        for z in structure:
            if (x != z) and (z != y) and self.dominates(x, z) and self.dominates(z, y):
                return False
        return True


    immediate_dominance = immediate_dominance_carnie

    def is_mother(self, A, B, structure):
        """ (13 a) Mother: A is the mother of B iff A immediately dominates B. (Carnie 2010, p. 35) """
        return self.immediate_dominance(A, B, structure)

    def is_daughter(self, B, A, structure):
        """ (13 b) Daughter: B is the daughter of A iff B is immediately dominated by A. (Carnie 2010, p. 35) """
        return self.immediate_dominance(A, B, structure)

    def is_sister(self, A, B, structure):
        """ (14) A is a sister of B if there is a C, such that C immediately dominates both A and B (Carnie 2010, p. 35)"""
        # hmm, this allows A to be sister of A
        for C in structure:
            if self.immediate_dominance(C, A, structure) and self.immediate_dominance(C, B, structure):
                return True
        return False

    def is_sister_chomsky(self, A, B, structure):
        """ ...Chomsky (1986b) gives a much broader description of sisterhood, where sisters include all material dominated by a single phrasal node (instead of a single edgeing node) (Carnie 2010, p. 35)"""
        # needs to be checked, I'm not sure if this is correct
        for C in structure:
            if (self.immediate_dominance(C, A, structure) and self.dominates(C, B)) or (
                self.dominates(C, A) and self.immediate_dominance(C, B, structure)):
                return True
        return False

    # Exhaustive dominance

    def exhaustive_dominance(self, A, nodes, structure):
        """ Node A exhaustively dominates a set of terminal nodes {b, c, ...d}, provided it dominates all the members of the set (so that there is not member of the set that is not dominated by A) and there is no terminal node g dominated by A that is not a member of the set. (Carnie 2010, p. 36)"""
        for B in nodes:
            if not self.dominates(A, B):
                return False
        for g in structure:
            if g != A and g not in nodes:
                if self.dominates(A, g):
                    return False
        return True

    def constituent_set(self, A, structure):
        """ A set of nodes exhaustively dominated by a single node (Carnie 2010, p. 37)"""
        nodes = [B for B in structure if self.dominates(A, B)]
        assert self.exhaustive_dominance(A, nodes, structure)
        return nodes

    # ## PRECEDENCE

    def is_left_edge(self, A, B, parent):
        """ This assumes only that parent has an ordering method that returns iterable results """
        left_found = False
        right_found = False
        left_index = 0
        right_index = 0
        for i, N in enumerate(parent.ordered_children()):
            if N is A:
                left_found = True
                left_index = i
            elif N is B:
                right_found = True
                right_index = i
        return left_found and right_found and left_index < right_index

    def sister_precedence(self, A, B, structure):
        """ (24) Node A sister-precedes node B if and only if both are immediately dominated by the same node M, and A emerges from a edge from M that is left of the edge over B (Carnie 2010, p. 40)"""
        for M in structure:
            if self.immediate_dominance(M, A, structure) and self.immediate_dominance(M, B,
                                                                                      structure) and self.is_left_edge(
                    A, B, M):
                return True
        return False

    def precedence(self, A, B, structure):
        """ (25) Node A precedes node B if and only if:
        (i) neither A dominates B nor B dominates A and
        (ii) some node E dominating A sister-precedes some node F dominating B (because domination is reflexive, E may equal A and F may equal B, but they need not do so.) (Carnie 2010, p. 40)
        """
        if self.dominates(A, B) or self.dominates(B, A):
            return False
        Es = [E for E in structure if self.dominates(E, A)]
        Fs = [F for F in structure if self.dominates(F, B)]
        for E in Es:
            for F in Fs:
                if self.sister_precedence(E, F, structure):
                    return True
        return False

    def immediate_precedence(self, A, B, structure):
        """(27) A immediately precedes B if A precedes B and there is no node G that follows A but precedes B. (Carnie 2010, p. 41) """
        if not self.precedence(A, B):
            return False
        for G in structure:
            if G is A or G is B:
                continue
            if self.precedence(A, G) and self.precedence(G, B):
                return False
        return True

    precedes = precedence


    # ## Precedence axioms

    def check_precedence_axioms(self, structure):
        print 'Precedence Transitivity Axiom: ', self.precedence_transitivity_axiom(structure)
        print 'Precedence Asymmetry Axiom: ', self.precedence_asymmetry_axiom(structure)
        print 'Precedence Irreflexivity Axiom: ', self.precedence_irreflexivity_axiom(structure)
        print 'Precedence Exclusivity Axiom: ', self.precedence_exclusivity_axiom(structure)
        print 'Precedence Non-tangling Axiom: ', self.precedence_non_tangling_axiom(structure)

    def precedence_transitivity_axiom(self, structure):
        """ (A6) P is transitive: for all x,y,z in N [(x precedes y) & (y precedes z) -> (x precedes z)]  (Carnie 2010, p. 42)"""
        for x in structure:
            for y in structure:
                for z in structure:
                    if self.precedes(x, y, structure) and self.precedes(y, z, structure):
                        if not self.precedes(x, z):
                            return False
        return True

    def precedence_asymmetry_axiom(self, structure):
        """ (A7) P is asymmetric: for all x,y in N [(( x precedes y) -> not (y precedes x))]
        (Carnie 2010, p. 43)"""
        for x in structure:
            for y in structure:
                if self.precedes(x, y, structure):
                    if self.precedes(y, x, structure):
                        return False
        return True

    def precedence_irreflexivity_axiom(self, structure):
        """ (T1) P is irreflexive: for all x in N [ not x precedes x] (Carnie 2010, p.43) """
        for x in structure:
            if self.precedes(x, x, structure):
                return False
        return True

    def precedence_exclusivity_axiom(self, structure):
        """ (A8) for all x,y in N [ (x precedes y) or (y precedes x) -> not ((x dominates y) or (y dominates x))] (Carnie 2010, p. 43)"""
        for x in structure:
            for y in structure:
                if self.precedes(x, y, structure) or self.precedes(y, x, structure):
                    if self.dominates(x, y) or self.dominates(y, x):
                        return False
        return True

    def precedence_non_tangling_axiom(self, structure):
        """ (A9) for all w,x,y,z in N [ ((w precedes x) and (w dominates y) and (x dominates z) -> (y precedes z))] (Carnie 2010, p. 43)"""

        for w in structure:
            for x in structure:
                if self.precedes(w, x, structure):
                    for y in structure:
                        if self.dominates(w, y):
                            for z in structure:
                                if self.dominates(x, z):
                                    if not self.precedes(y, z, structure):
                                        return False
        return True


    # ## C-Command and Government

    def command(self, A, B, structure):
        """ Command: Node A commands B, if the first S (Sentence) node dominating A also dominates B. (Carnie 2010, p. 47)
            let's not implement this. S-nodes do not exist anymore and defining the first dominating S-node would be pain.
        """
        pass

    def kommand(self, A, B, structure):
        """ Kommand: Node A kommands B, if the first cyclic node (S or NP) dominating A also dominates B. (Carnie 2010, p. 49)
            same thing as with command. No sense to implement as S and NP are not that meaningful
        """
        pass

    def c_command(self, A, B, structure):
        """ (23) C-command: Node A c-commands node B if every node properly dominating A also properly dominates B, and neither A nor B dominate the other. (Carnie 2010, p. 54) """
        if self.dominates(A, B) or self.dominates(B, A):
            return False
        for g in structure:
            if self.properly_dominates(g, A):
                if not self.properly_dominates(g, B):
                    return False
        return True

    def symmetric_c_command(self, A, B, structure):
        """ (17) A symmetrically c-commands B, if A c-commands B and B c-commands A. (Carnie 2010, p. 52) """
        return self.c_command(A, B, structure) and self.c_command(B, A, structure)

    def asymmetric_c_command(self, A, B, structure):
        """ (18) A asymmetrically c-commands B, if A c-commands B but B does not c-command A. (Carnie 2010, p. 52) """
        return self.c_command(A, B, structure) and not self.c_command(B, A, structure)

    def path(self, start, end, structure):
        """ Let a path P (in tree T) be a sequence of nodes (A_0,... A_i, A_i+1, ... A_n) such that:
        (a) all ij, n >= i, j >= 0, A_i = A_j -> i = j.
        (b) all i, n > i >= 0, A_i immediately dominates A_i+1 or A_i+1 immediately dominates A_i.

        expensive to implement in this way. Better to implement unambiguous path only, as it is used in Kayne's definition.
        """
        pass

    def unambiguous_path(self, start, end, structure):
        """ An unambiguous path T is a path P = (A_0,..., A_i, A_i+1, ... A_n) such that all i, n>i>=0:
        (a) if A_i immediately dominates A_i+1, then A_i immediately dominates no node in T other than A_i+1, with the exception of A_i-1;
        (b) if A_i is immediately dominated by A_i+1, then A_i is immediately dominated by no node in T other than A_i+1.
        """
        P = [end]
        turning_points = []
        for n in structure:
            if self.dominates(n, start) and self.dominates(n, end):
                turning_points.append(n)
        if not turning_points:
            return []
        latest = end
        # going up:
        while latest not in turning_points:
            candidates = []
            for n in structure:
                if self.immediately_dominates(n, latest, structure):
                    candidates.append(n)
            if len(candidates) > 1 or len(candidates) == 0:
                return []  # ambiguous, node has more than one parent
            latest = candidates[0]
            P.append(latest)
        if latest == start:
            return P
        # first step down:
        candidates = []
        for n in structure:
            if self.immediately_dominates(latest, n) and n not in P:
                candidates.append(n)
        if len(candidates) > 1:
            return []  # ambiguous, more than one possible children
        latest = candidates[0]
        P.append(latest)

        # ## Here is an interesting possibility: that 'turning point' allows node to have two daughters, because the other is already included in path. In Kayne's definition this is a special case, but it could be generalized.
        generalized_exclude_path_members = False
        while latest is not start:
            candidates = []
            for n in structure:
                if generalized_exclude_path_members:
                    if self.immediately_dominates(latest, n) and (n not in P):
                        candidates.append(n)
                else:
                    if self.immediately_dominates(latest, n):
                        candidates.append(n)
            if len(candidates) > 1 or len(candidates) == 0:
                return []  # ambiguous, more than one possible children
            latest = candidates[0]
            P.append(latest)
        return P

    def minimal_factorization(self, target, structure):
        """ {F, E, B} provides the minimal factorization of the phrase-marker with respect to G. That is, there is no other set of nodes that is smaller than ... {F, E, B} which when unioned with G provides a complete non-redundant constituent analysis of the phrase marker. (Chametzky (2000:45), according to Carnie 2010, p. 58)

        This is tricky, but I think equivalent can be done by taking all target's dominating nodes and taking the other node involved than the one that is in dominating nodes or the target node.
        """
        dominators = []
        for n in structure:
            if self.properly_dominates(n, target):
                dominators.append(n)
        other_sisters = dominators + [target]
        factors = []
        for mother in dominators:
            for s in structure:
                if s not in other_sisters and self.is_daughter(s, mother, structure):
                    factors.append(s)
        return factors

    def m_command(self, A, B, structure):
        """ (30) M-command: Node A c-commands node B if every maximal category (XP) node properly dominating A also dominates B and neither A nor B dominate the other. (Carnie 2010, p.59)
            This requires recognition of maximal category. I'm not sure if that will be implemented.
        """
        if self.dominates(A, B) or self.dominates(B, A):
            return False

        for n in structure:
            if self.is_maximal_category(n, structure) and self.properly_dominates(n, A):
                if not self.dominates(n, B):
                    return False
        return True

    # Parker and Pullum (1990): Command edges through minimal upper bound

    def upper_bounds(self, a, P, structure):
        """ (35) The set of upper bounds for a with respect to property P (written UB(a, P)) is given by UB(a, P) = { b | b properly_dominates a & P(b) } (Carnie 2010, p.61)"""

        result_set = set()
        for b in structure:
            if self.properly_dominates(b, a) and P(b, structure):
                result_set.add(b)
        return result_set

    def minimal_upper_bound(self, a, P, structure):
        """ (36) MUB(a, P) = { b | b belongs_to UB(a, P) & all x [ (x belongs_to UB(a, P) & b dominates x) -> (b = x)]} (Carnie 2010, p.61)"""

        UB = list(self.upper_bounds(self, a, P, structure))
        result_set = set()

        for b in UB:
            candidate = True
            for x in UB:
                if b != x and self.dominates(b, x):
                    candidate = False
            if candidate:
                result_set.add(b)
        return result_set

    def general_command_edge(self, a, P, structure):
        """ (37) C_P = { <a, b>: all x [(x belongs to MUB(a, P)) -> x dominates b ] } (Carnie 2010, p.61)

            returns the c-command domain: all of the nodes that can be b.
        """

        MUB = self.minimal_upper_bound(a, P, structure)
        result_set = set()

        for x in MUB:
            for b in structure:
                if b in result_set:
                    continue
                if self.dominates(x, b):
                    result_set.add(b)
        return b

    def barker_pullum_s_command(self, A, structure):
        """ S-command is the command edge C_P1, where P1 is given by: P1 = { a | LABEL(a)=S } (Carnie 2010, p.61)
        """

        def P1(a, structure):
            return a.node_type_label() == 'S'

        return self.general_command_edge(A, P1, structure)

    def barker_pullum_k_command(self, A, structure):
        """ K-command is the command edge C_P3, where P3 is given by: P3 = { a | LABEL(a) belongs to {S,NP} } (Carnie 2010, p.61)
        """

        def P3(a, structure):
            return a.node_type_label() in ['S', 'NP']

        return self.general_command_edge(A, P3, structure)

    def barker_pullum_m_command(self, A, structure):
        """ M-command is the command edge C_P4, where P4 is given by: P4 = { a | LABEL(a) belongs to MAX } (Carnie 2010, p.61)
        """

        def P4(a, structure):
            return self.is_maximal_category(a, structure)

        return self.general_command_edge(A, P4, structure)


    def barker_pullum_c_command(self, A, structure):
        """ C-command is the command edge C_P5, where P5 is given by: P5 = { a | exists xy [ x != y & M(a,x) & M(a, y)]} (Carnie 2010, p.62)

        I'm using is_mother instead of Barker and Pullum's definition of M: they are equivalent
        """

        def P5(a, structure):
            found = set()
            # if we go through structure and find (at least) two daughters, the condition is satisfied.
            for x in structure:
                if self.is_mother(a, x, structure):
                    found.add(a)
                    if len(found) == 2:
                        return True
            return False

        return self.general_command_edge(A, P5, structure)


    def immediate_dominance_c_command(self, A, structure):
        """ C-command is the command edge C_P6, where P6 is given by: P6 = N (N the set of nodes)  (Carnie 2010, p.62)
        I'm using P:s as function that checks if something is part of the set, Carnie uses P as a set. So P6 = N means that everything goes.
        """

        def P6(a, structure):
            return a in structure

        return self.general_command_edge(A, P6, structure)


    def governs(self, A, B, structure):
        """ (45) Government: A governs B iff
        a) A c-commands B;
        b) There is no X, such that A c-commands X and X asymmetrically c-commands B. (Carnie 2010, p. 63)
        """
        if not self.c_command(A, B, structure):
            return False
        for X in structure:
            if X != A:
                if self.c_command(A, X, structure) and self.asymmetric_c_command(X, B, structure):
                    return False

                ##### Bare phrase structure, preliminaries


    def projection_path_bottom_up(self, bottom, structure):
        """ (2) Pi is a projection path if Pi is a sequence of nodes N = (n_1, ... n_n)
        (a) for all i, n_i immediately dominates n_i+1;
        (b) all n_i have the same set of features;
        (c) the bar level of n_i is equal to or greater then the bar level of n_i+1.
        (Carnie 2010 p.137)

        Give projection path that starts from node 'bottom'
        """
        matching_nodes = [n for n in structure if n.get_features() == bottom.get_features() and n is not bottom]
        path = [bottom]
        found = True
        while found:
            found = False
            niplus1 = path[0]
            for ni in matching_nodes:
                if self.immediately_dominates(ni, niplus1, structure):
                    if self.bar_level(ni, structure) >= self.bar_level(niplus1, structure):
                        path.insert(0, ni)
                        found = True
                        break
        # this will behave strangely with multidominated structures
        return path

    def projection_path_top_down(self, top, structure):
        """ (2) Pi is a projection path if Pi is a sequence of nodes N = (n_1, ... n_n)
        (a) for all i, n_i immediately dominates n_i+1;
        (b) all n_i have the same set of features;
        (c) the bar level of n_i is equal to or greater then the bar level of n_i+1.
        (Carnie 2010 p.137)

        Give projection path that starts from node 'top'
        """
        matching_nodes = [n for n in structure if n.get_features() == top.get_features() and n is not top]
        path = [top]
        found = True
        while found:
            found = False
            niminus1 = path[-1]
            for ni in matching_nodes:
                if self.immediately_dominates(niminus1, ni, structure):
                    if self.bar_level(niminus1, structure) >= self.bar_level(ni, structure):
                        path.append(ni)
                        found = True
                        break
        # this will behave strangely with multidominated structures
        return path

    def maximal_projection_node(self, path):
        """ (4) n_i is the maximal projection node of a projection path Pi = (n_1, ..., n_n) iff i=1  (Carnie 2010 p.137) """
        return path[0]

    def project_alpha(self, word, structure):
        """ (6) Project Alpha: A word of syntactic category X is dominated by an uninterrupted sequence of X nodes. (Carnie 2010 p.138)

            These chains give (for me unintuitive) order [X_max ,..., X_0]
        """
        found = True
        path = [word]
        while found:
            last = path[-1]
            for n in structure:
                if n.syntactic_category() == word.syntactic_category() and self.immediately_dominates(n, last,
                                                                                                      structure) and n is not last:
                    found = True
                    path.append(n)
        path.reverse()
        return path  # [X_max, ... , X ]

    def projection_chain(self, X, structure):
        """ (7) Projection Chain of X = an uninterrupted sequence of projections of X (Carnie 2010, p. 138)
            The chain can go to both directions from X, if X is assumed to be a node.
            These chains give (for me unintuitive) order [X_max ,..., X_0]
        """
        path = self.project_alpha(X, structure)  # this is the upper part of path, from X_max to X
        found = True
        while found:
            last = path[-1]
            for n in structure:
                if n.syntactic_category() == X.syntactic_category() and self.immediately_dominates(last, n,
                                                                                                   structure) and n is not last:
                    found = True
                    path.append(n)
        return path

    def maximal_projection_speas(self, X, structure):
        """ (8) Maximal projection: X = XP if for all G, dominating X, G!=X (Carnie 2010, p. 138)

        This is Speas's original version, which is a bit broken. There is revised version that will be used as a standard, as domination can happen over distances.
        """
        for G in structure:
            if G.syntactic_category() == X.syntactic_category() and self.dominates(G, X):
                return False
        return True

    def maximal_projection(self, X, structure):
        """ (9) Maximal Projection (revised): X = XP if each G, immediately dominating X, the head of G != the head of X. (Carnie 2010, p. 138)"""

        for G in structure:
            if G.head() == X.head() and self.immediately_dominates(G, X, structure):
                return False
        return True


    def asymmetric_immediate_dominance_c_command(self, A, structure):
        """ Used for Kayne's LCA: Some node A only c-commands B if the node immediately dominating A, dominates (not necessarily immediately) B. (Carnie 2010, p. 146) Add asymmetry, and return all suitable targets. """
        results = set()
        for B in structure:
            if A is B:
                continue
            if self.dominates(A, B) or self.dominates(B, A):
                continue
            for p in structure:
                if self.immediately_dominates(p, A, structure) and self.dominates(p,
                                                                                  B) and not self.immediately_dominates(
                        p, B):
                    results.add(p)


    def linear_correspondence_axiom(self, structure):
        """ (24) Linear Correspondence Axiom: d(A) is a linear ordering of T.
        ok, this is difficult.
        T is a set of terminals in a structure.
        A is a set of asymmetric c-command edges in a structure. Each edge is a pair, where <command, commanded>
        d(A) is an image of A, where each edge is described by their corresponding terminals.
            Carnie is a bit unspecific with this, I cannot say what should be done when there are several terminals dominated by a node. It seems that they are omitted from d(A), so I do so.
        """

        def get_terminals(x):
            terminals = []
            for t in structure:
                if self.dominates(x, t) and self.is_terminal_node(t, structure):
                    terminals.append(t)
            return terminals


        T = set()
        for t in structure:
            if self.is_terminal_node(t, structure):
                T.add(t)

        A = set()
        for a in structure:
            seconds = self.asymmetric_immediate_dominance_c_command(A, structure)
            for s in seconds:
                A.add((a, s))

        dA = set()
        for (a, b) in A:
            at = get_terminals(a)
            if len(at) > 1:
                continue
            bt = get_terminals(b)
            if len(bt) > 1:
                continue
            dA.add((at[0], bt[0]))

        # now we have sorted pairs of terminals. now these need to be sorted into one list, and check if there are unresolved orderings.

        def sort_func(x, y):
            for first, second in dA:
                if first == x and second == y:
                    return -1
                elif first == y and second == x:
                    return 1
            print "failed to sort '%s' and '%s'" % (x, y)
            raise ValueError

        try:
            result = sorted(T, sort_func)
        except ValueError:
            result = []
        return result


    def excludes(self, X, Y, structure):
        """ (32) X excludes Y iff no segment of X dominates Y.
        (Carnie 2010, p. 152)
        I am now assuming that segment is identified by the same syntactic category and there is a domination edgeship between segments
            not sure if it should be immediate domination
        """
        segments = [z for z in structure if
                    X.syntactic_category() == z.syntactic_category() and self.dominates(z, X) or self.dominates(X, z)]
        for s in segments:
            if self.dominates(s, Y):
                return False
        return True


    def excluding_c_command(self, A, B, structure):
        """ (31) A c-commands B iff
        (a) A and B are categories;
        (b) A excludes B;
        (c) every category that dominates A dominates B.
        (Carnie 2010, p. 152)
        """
        if not A.syntactic_category() or B.syntactic_category():
            return False
        if not self.excludes(A, B, structure):
            return False
        for s in structure:
            if s.syntactic_category():
                if self.dominates(s, A):
                    if not self.dominates(s, B):
                        return False
        return True


    ##### Bare phrase structure, Merge and other important parts

    def set_merge(self, alpha, beta):
        """(40) Merge:
        Applied to two objects alpha & beta, Merge forms a new object delta.
        Example: delta = {gamma, {alpha, beta}}

        gamma here is the label of constituent delta.
        """

        delta = self.constituent()
        delta.setChildren(set([alpha, beta]))
        try:
            gamma = self.head_is_label([alpha, beta])
            delta.setLabel(gamma)
        except ValueError:
            print 'Labeling problem'
        return delta


    def head_is_label(self, candidates):
        """ Chomsky's minimalist labeling function: head projects: one that is head is label. """
        found = None
        for c in candidates:
            if c.isHead():
                if not found:
                    found = c
                else:
                    raise ValueError  # ambiguous labeling: two heads
        if not c:
            raise ValueError
        else:
            return c

    def first_is_label(self, candidates):
        """ Labeling based on ordered pairs """
        if candidates:
            return candidates[0]
        else:
            raise ValueError

    def ordered_pair_merge(self, alpha, beta):
        """ simplified merge based on ordered pairs: <alpha, beta>"""
        delta = self.constituent()
        delta.setChildren([alpha, beta])
        delta.setLabel(alpha)

    def pair_merge(self, alpha, beta):
        """ Chomsky's pair merge for adjunctions """
        delta = self.constituent()
        delta.setChildren([alpha, beta])
        gamma = self.head_is_label([alpha, beta])
        delta.setLabel((gamma, gamma))
        return delta

    def bare_phrase_lca(self, structure):
        equals = []

        def sorting_function(x, y):
            xy = self.c_command(x, y, structure)
            yx = self.c_command(y, x, structure)
            if xy and yx:
                equals.append((x, y))
                return 0
            elif xy:
                return -1
            elif yx:
                return 1
            return 0

        T = [n for n in structure if self.is_terminal(n, structure)]
        T.sort(sorting_function)
        # make sure that if elements are symmetrically commanded at least another of them is silent anyways
        for x, y in equals:
            if not (self.isSilent(x, structure) or self.isSilent(y, structure)):
                raise ValueError
        return T


    def feature_check(self, left, right):
        matches = []
        selects = []
        for key, f_left in left.features.iteritems():
            if key in right.features.iterkeys():
                f_right = right.features[key]
                if (f_left.value == '-' and f_right.value == '+') or (f_left.value == '+' and f_right.value == '-'):
                    matches.append(key)
                if (f_left.value == '=' and f_right.value == '+') or (f_left.value == '+' and f_right.value == '='):
                    selects.append(key)
        return matches, selects

    def Merge(self, left, right):
        id = left.label
        # remove index (_i, _j ...) from Merged id so that indexing won't get broken
        res = re.search(r'[^\\]_\{(.*)\}', id) or re.search(r'[^\\]_(.)', id)
        if res:
            id = id[:id.rindex('_')]
        new = self.Constituent(id, left, right)
        if not (left and right):
            return new

        # this is experiment on case, old code commented below
        # new.left_features=left.features.items()
        # new.right_features=right.features.items()
        # new.features=left.features.copy()
        # new.features.update(right.features)
        # matches, selects=self.feature_check(left, right)
        # for key in matches+selects:
        #     del new.features[key]
        return new

    def CCommands(self, A, B, context):
        """ C-Command edge needs the root constituent of the tree as a context, as
            my implementation of UG tries to do without constituents having access to their parents """
        closest_parents = _closest_parents(A, context, parent_list=[])
        # if 'closest_parent' for B is found within (other edge of) closest_parent, B sure is dominated by it.
        for parent in closest_parents:
            if B in parent:
                return True
        return False

    def getChildren(self, A):
        """ Returns immediate children of this element, [left, right] or [] if no children """
        children = []
        if A.left:
            children.append(A.left)
        if A.right:
            children.append(A.right)
        return children

    def getCCommanded(self, A, context):
        """ Returns elements c-commanded by this element """
        closest_parents = _closest_parents(A, context, parent_list=[])
        result = []
        for p in closest_parents:
            if p.left == A:
                result.append(p.right)
            else:
                result.append(p.left)
        return result

    def getAsymmetricCCommanded(self, A, context):
        """ Returns first elements c-commanded by this element that do not c-command this element """
        result = []

        def _downward(item, A, result):
            if item.left:
                if not self.CCommands(item.left, A, context):
                    result.append(item.left)
                else:
                    result = _downward(item.left, A, result)
            if item.right:
                if not self.CCommands(item.right, A, context):
                    result.append(item.right)
                else:
                    result = _downward(item.right, A, result)
            return result

        ccommanded = self.getCCommanded(A, context)
        for item in ccommanded:
            result = _downward(item, A, result)
        return result

    def parse(self, sentence, silent=False):
        if not isinstance(sentence, list):
            sentence = [word.lower() for word in sentence.split()]
        for word in sentence:
            try:
                constituent = self.lexicon[word].copy()
            except KeyError:
                raise "Word '%s' missing from the lexicon" % word
            self.structure = self.Merge(constituent, self.structure)
        if not silent: print 'Finished: %s' % self.structure
        return self.structure


    def Linearize(self, structure):
        def _lin(node, s):
            if node.left:
                _lin(node.left, s)
            if node.right:
                _lin(node.right, s)
            if not (node.left or node.right) and node not in s:
                s.append(node)
            return s

        return _lin(structure, [])


    @time_me
    def CLinearize(self, structure):
        """ Bare phrase structure linearization. Like Kayne's, but allows ambiguous cases to exist. It is assumed that phonology deals with them, usually by having null element in ambiguous pair. """
        # returns asymmetric c-command status between two elements
        def _asymmetric_c(A, B):
            AC = self.CCommands(A, B, structure)
            BC = self.CCommands(B, A, structure)
            if AC and BC:
                return None
            elif AC:
                return (A, B)
            elif BC:
                return (B, A)
            else:
                return None

        # build a list of terminals
        def _lin(node, s):
            if node.left:
                _lin(node.left, s)
            if node.right:
                _lin(node.right, s)
            if not (node.left or node.right) and node not in s:
                s.append(node)
            return s

        # first create a list (or set or whatever) of terminal nodes.
        terminals = _lin(structure, [])
        # create pairs of asymmetric c-commands
        if not terminals:
            return []
        t2 = list(terminals)
        pairs = []
        for a in list(t2):
            for b in t2:
                if a != b:
                    c = _asymmetric_c(a, b)
                    if c:
                        pairs.append(c)
            t2.pop(0)
        linear = []
        t2 = list(terminals)
        for item in list(t2):
            found = False
            for (a, b) in pairs:
                if b == item:
                    found = True
            if not found:
                for (a, b) in list(pairs):
                    if a == item:
                        pairs.remove((a, b))
                        found = True
                if found:
                    linear.append(item)

        print linear
        return linear


def _closest_parents(A, context, is_not=None, parent_list=[]):
    if context.left == A or context.right == A:
        parent_list.append(context)
    if context.left and not context.left == is_not:
        parent_list = _closest_parents(A, context.left, is_not=is_not, parent_list=parent_list)
    if context.right and not context.right == is_not:
        parent_list = _closest_parents(A, context.right, is_not=is_not, parent_list=parent_list)
    return parent_list


