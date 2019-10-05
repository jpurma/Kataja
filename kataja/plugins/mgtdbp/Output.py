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
"""
   This is minimalist grammar top-down beam parser (mgtdbp), refactored from E. Stabler's original,
   see https://github.com/epstabler/mgtdb

   This file is a part of an effort to make an output-equivalent mgtdbp that can be used as a
   Kataja plugin. The code aims for readability and not efficiency: many tuples that the
   original operated with are handled in a more object-oriented manner. Also the parser creates
   constituents already during the parsing, which is bit wasteful compared to original.

   This file is based on https://github.com/epstabler/mgtdb/blob/master/python/python3/mgtdbp-dev.py
   mgtdbp-dev Modified for py3.1 compatibility by: Erik V Arrieta. || Last modified: 9/15/12
   mgtdbp-dev by Edward P. Stabler

Comments welcome: jukka.purma--at--gmail.com
"""

import json
from collections import defaultdict

try:
    from mgtdbp.Constituent import Constituent
    from mgtdbp.Feature import Feature
    from kataja.syntax.SyntaxState import SyntaxState
    from mgtdbp.LexNode import LexNode

    in_kataja = True
except ImportError:
    in_kataja = False
    from Constituent import Constituent
    from Feature import Feature
    from LexNode import LexNode

    SyntaxState = object

DISCARD_DEAD_ENDS = True


class DerivationPrinter:
    """ DerivationPrinter produces derivations as Kataja's DerivationSteps, as json for d3-based
    visualisations and derivation tree printout similar to original mgtdbp, to verify that the
    parser remains output-equivalent to original.
    """

    def __init__(self, forest, outfile=None):
        self.forest = forest
        self.parse_count = 0
        self.outfile = outfile
        self.derivation_steps = []
        self.parsed_file = 'parses.js'

    def show_results(self, active_parse):
        if self.forest:
            # if not self.kataja_lex_tree:
            #    self.kataja_lex_tree = self.prepare_kataja_lex_tree(self.lex_trees)
            ktree = self.build_kataja_tree_from_dnodes(active_parse.tree)
            syn_state = SyntaxState(tree_roots=[ktree],
                                    msg=active_parse.msg,
                                    state_id=self.parse_count)
            self.forest.add_step(syn_state)
        else:
            idtree = self.build_id_tree_from_dnodes(active_parse.tree)
            self.add_derivation_step(idtree)

            # print('dtree:', idtree.to_dtree())
        active_parse.count = self.parse_count
        self.parse_count += 1

    def add_derivation_step(self, idtree):
        edges = defaultdict(list)

        def add_child_edge(parent, node, word):
            if parent.lex_key == node.lex_key:
                return node.lex_key
            if node.parent_lex_key:
                d = {
                    'sign': 'l',
                    'target': node.parent_lex_key,
                    'label': word,
                    'help': 'c-child: %s child: %s' % (node.parent_lex_key, node.lex_key)
                }
                edges[node.lex_key].append(d)
                p_key = node.parent_lex_key
            else:
                p_key = node.lex_key

            d = {
                'sign': 'l',
                'target': parent.lex_key,
                'label': word,
                'help': 'parent: %s child: %s' % (parent.lex_key, p_key)
            }
            edges[p_key].append(d)
            return p_key

        def add_edge(node):
            if node.parent_lex_key:  # it's leaf
                word = node.lex_key
            else:
                word = None

            if node.label == '*':
                left, right = node.parts
                l_key = left.parent_lex_key or left.lex_key
                r_key = right.parent_lex_key or right.lex_key
                lstr = str((left.label, str(left.features[0]), l_key))
                rstr = str((right.label, str(right.features[0]), r_key))
                fl = left.features[0]
                if fl.sign == '=':
                    d = {
                        'sign': '+',
                        'target': r_key,
                        'label': r_key,
                        'help': 'agree: %s %s' % (rstr, lstr)
                    }
                    edges[l_key].append(d)

            if node.label == 'o':
                right = node.parts[0]
                r_key = right.parent_lex_key or right.lex_key
                rstr = str((right.label, str(right.features[0]), r_key))
                fl = right.features[0]
                if fl.sign == '+':
                    d = {
                        'sign': '-',
                        'target': r_key,
                        'label': r_key,
                        'help': 'move: %s' % rstr
                    }
                    edges[r_key].append(d)
                    if r_key != right.lex_key:
                        print('intermed. edge %s agrees w. %s' % (r_key, right.lex_key))
                        print(node)
                else:
                    print(fl)
                    sys.exit()

            for i, part in enumerate(node.parts):
                child_word = add_edge(part)
                add_child_edge(node, part, child_word)
                if node.features == part.features[1:] or len(node.parts) == 1:
                    word = child_word
            return word

        add_edge(idtree)
        if edges:
            self.derivation_steps.append(edges)

    def discard_dead_ends(self, active_parse):
        if active_parse.cat_queue or active_parse.input_words or not DISCARD_DEAD_ENDS:
            return
        good_ids = set()
        prev = active_parse
        while prev:
            good_ids.add(prev.count)
            prev = prev.prev
        all_ids = set(range(0, self.parse_count))
        bad_ids = all_ids - good_ids
        self.forest.remove_iterations(bad_ids)

    def compile_results(self, active_parse, sentence):
        if self.forest:
            self.discard_dead_ends(active_parse)
            idtree = self.build_kataja_tree_from_dnodes(active_parse.tree)
        else:
            idtree = self.build_id_tree_from_dnodes(active_parse.tree)
        self.show_results(active_parse)
        if not self.forest:
            f = open(self.parsed_file, 'w')
            f.write('var parses = ')
            json.dump([self.derivation_steps], f, ensure_ascii=False, indent=1)
            f.close()

        if self.outfile:
            self.outfile.write(sentence + '\n')
            self.outfile.write(str(idtree.to_dtree()) + '\n')
            self.outfile.write('\n')

    @staticmethod
    def build_id_tree_from_dnodes(dnodes):
        """ build the derivation tree that has parent as its root, and return it """
        build = {}
        top = None
        # print('build_id_tree_from_dnodes: ', dnodes)
        for node in dnodes:
            key = ''.join([str(p) for p in node.path])
            if key not in build:
                build[key] = node
            elif node.features or node.label:
                build[key] = node
            node.parts = []

        for key, node in build.items():
            if not node.path:
                top = node
                continue
            parent = build[key[:-1]]
            parent.parts.append(node)
            if len(parent.parts) == 2:
                parent.label = '*'  # parent.parts.sort()
            else:
                parent.label = 'o'
        assert len([node for node in build.values() if not node.path]) == 1
        assert top

        def not_circular(node, parents):
            if node in parents:
                print('circular node: ', node)
            for part in node.parts:
                not_circular(part, parents + [node])

        not_circular(top, [])
        return top

    @staticmethod
    def build_kataja_tree_from_dnodes(dnodes):
        """ build the derivation tree that has parent as its root, and return it """

        done = set()

        def fix_hosts(node, done):
            # since features are assumed top-down and then matched with lexical entries, it
            # is difficult to track unambiguously which assumed features belonged to which lexical
            # entries.
            #
            # However it is easy to fix feature hosts -- the if the feature is present and the
            # node is leaf, the leaf is the host
            #
            if node in done:
                return
            done.add(node)
            if node.parts:
                for part in node.parts:
                    fix_hosts(part, done)
            else:
                for feature in node.features:
                    feature.host = node

        def raise_constituents(node, movers):
            neither_is_leaf = True
            node.poke('lexical_heads')
            node.lexical_heads = []
            for part in node.parts:
                if part not in done:
                    done.add(part)
                    raise_constituents(part, movers)
                if not part.parts:
                    neither_is_leaf = False
            for feature in node.features:
                if feature.sign == '-' and not feature.checked_by:
                    movers[feature.name] = (feature, node)
            if len(node.parts) == 1:
                puller = node.parts[0].features[0]
                if puller.sign == '+' and puller.name in movers:
                    mover_feat, mover_node = movers[puller.name]
                    if mover_node is not node:
                        node.insert_part(mover_node, 0)
                        node.checked_features = (mover_feat, puller)
                        node.poke('lexical_heads')
                        node.lexical_heads = list(mover_node.lexical_heads)
                        puller.check(mover_feat)
                        del movers[puller.name]
                        node.label = '>'
                else:
                    print('weird puller:', puller)
            elif len(node.parts) == 2:
                node.poke('lexical_heads')
                node.lexical_heads = list(node.parts[0].lexical_heads)
                if neither_is_leaf:
                    node.label = '>'
                    node.parts = list(reversed(node.parts))
                else:
                    node.label = '<'
            else:
                node.poke('lexical_heads')
                node.lexical_heads = [node]
                if not node.label:
                    node.label = ' '.join([str(x) for x in node.inherited_features])

        build = {}
        top = None
        for node in dnodes:
            key = ''.join([str(p) for p in node.path])
            if key not in build:
                build[key] = node
            elif node.features or node.label:
                build[key] = node
            node.parts = []
            node.checked_features = []
            node.poke('lexical_heads')
            node.lexical_heads = []
            for feature in node.features:
                feature.checked_by = None
                feature.checks = None

        for key, node in build.items():
            if not node.path:
                assert not top
                top = node
                continue
            parent = build[key[:-1]]
            assert parent != node
            parent.add_part(node)
            if len(parent.parts) == 2:
                left, right = parent.parts
                left_f = left.features[0]
                right_f = right.features[0]
                parent.checked_features = (left_f, right_f)
                if left_f.sign == '':
                    left_f.check(right_f)
                else:
                    right_f.check(left_f)
        raise_constituents(top, {})
        fix_hosts(top, set())

        assert len([node for node in build.values() if not node.path]) == 1
        assert top
        return top

    @staticmethod
    def print_lexicon(lex_trees):
        s = []

        def walk_nodes(route, node):
            if node.parts:
                for part in node.parts:
                    walk_nodes(list(route) + ([str(node.feat)] if node.feat else []), part)
            else:
                s.append('%s:: %s' % (node.word, ' '.join(reversed(route))))

        for node in lex_trees.values():
            walk_nodes([], node)
        s.sort()
        return '\n'.join(s)


def prepare_kataja_lex_tree(lex_trees):
    def as_feature(node):
        feat = node.feat or Feature('√' + (node.word or ''))
        feat.parts = [as_feature(part) for part in node.parts]
        return feat

    features = [as_feature(node) for node in lex_trees.values()]
    root = Constituent('Lexicon', features=features)
    return root


def write_lexicon_graph_json(lex_trees, lex_file_name):
    filename = lex_file_name.rsplit('.', 1)[0] + '.js'
    nodes = []
    edges = []
    givers = defaultdict(list)
    takers = defaultdict(list)
    plusses = defaultdict(list)
    minuses = defaultdict(list)

    def as_json_node(node):
        group = 0
        if node.feat:
            if node.feat.sign == '=':
                takers[node.feat.name].append(node.key)
                group = 1
            elif node.feat.sign == '':
                group = 2
                givers[node.feat.name].append(node.key)
            elif node.feat.sign == '+':
                plusses[node.feat.name].append(node.key)
                group = 3
            elif node.feat.sign == '-':
                minuses[node.feat.name].append(node.key)
                group = 4
        n = {'id': node.key,
             'label': str(node.feat) if node.feat else node.word,
             'value': node.feat.name if node.feat else '',
             'sign': node.feat.sign if node.feat else None,
             'group': group
             }
        nodes.append(n)
        for part in node.parts:
            p_id = as_json_node(part)
            e = {
                'source': node.key,
                'target': p_id,
                'value': 1,
                'sign': 'l'
            }
            edges.append(e)
        return node.key

    root = LexNode(parts=list(lex_trees.values()), key='center')
    as_json_node(root)

    for key, items in givers.items():
        for source in items:
            for target in takers[key]:
                e = {
                    'source': source,
                    'target': target,
                    'value': 0.1,
                    'sign': '='
                }
                edges.append(e)
    for key, items in plusses.items():
        for source in items:
            for target in minuses[key]:
                e = {
                    'source': source,
                    'target': target,
                    'value': 3,
                    'sign': '-'
                }
                edges.append(e)
    d = {
        'nodes': nodes,
        'links': edges
    }
    f = open(filename, 'w')
    f.write('var graph = ')
    json.dump(d, f, ensure_ascii=False, indent=1)
    f.close()
