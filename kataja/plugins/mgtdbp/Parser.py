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

import heapq
import time

try:
    from kataja.plugins.mgtdbp.Constituent import Constituent
    from kataja.plugins.mgtdbp.Feature import Feature
    from kataja.plugins.mgtdbp.LexNode import LexNode
    from kataja.singletons import running_environment
    from kataja.plugins.mgtdbp.Output import DerivationPrinter, write_lexicon_graph_json

    in_kataja = True
except ImportError:
    in_kataja = False
    from Constituent import Constituent
    from Feature import Feature
    from LexNode import LexNode
    from Output import DerivationPrinter, write_lexicon_graph_json

    running_environment = None

OUTFILE = 'parser_output.txt'
COMPARISON_FILE = 'original_mgtdbp_output.txt'


def fix_path(filename):
    if (not in_kataja) or filename.startswith('/'):
        return filename
    return running_environment.plugins_path + '/mgtdbp/' + filename


def add_left_child(i):
    return i + [0]


def add_right_child(i):
    return i + [1]


def same_as(d, remove='', add=None):
    new = d.copy()
    if remove:
        del new[remove]
    if add:
        new[add[0]] = add[1]
    return new


def load_grammar_from_file(filename):
    f = open(fix_path(filename))
    grammar_str = f.read()
    f.close()
    return load_grammar(grammar_str)


def load_grammar(g=''):
    lex_trees = {}
    lines = g.splitlines()
    n_count = 0

    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            continue
        if '::' not in line:
            continue
        word, features = line.rsplit('::', 1)
        rev_feats = [Feature.from_string(fstr) for fstr in reversed(features.split())]
        key_feat, *rest = rev_feats
        if key_feat.name not in lex_trees:
            lex_trees[key_feat.name] = LexNode(key=f'n{n_count}', feat=key_feat)
            n_count += 1
        branch = lex_trees[key_feat.name]
        for feat in rest:
            found = False
            node = None
            for node in branch.parts:
                if node.feat == feat:
                    found = True
                    break
            if found:
                branch = node
            else:
                node = LexNode(key=f'n{n_count}', feat=feat)
                n_count += 1
                branch.parts.append(node)
                branch = node

        branch.parts.append(LexNode(key=f'n{n_count}', word=word))
        n_count += 1
    return lex_trees


class Cat:
    def __init__(self, node=None, movers=None, index=None, moving=None, checked=None, path=None):
        self.node = node
        self.index = index or []
        self.movers = movers or {}
        # ------ dt ------
        self.moving = moving or {}
        self.checked = checked or []
        self.path = path or []
        self.min_index = []
        self.update_min_index()

    def update_min_index(self):
        # Indexed categories are sorted by min_index, which is the smallest filled mover position
        self.min_index = min([self.index] + [x.index for x in self.movers.values()])

    def __repr__(self):
        parts = []
        if self.node:
            parts.append('node=%r' % self.node)
        if self.index:
            parts.append('index=%r' % self.index)
        if self.movers:
            parts.append('movers=%r' % self.movers)
        if self.moving:
            parts.append('moving=%r' % self.moving)
        if self.checked:
            parts.append('checked=%r' % self.checked)
        if self.path:
            parts.append('path=%r' % self.path)
        return 'Cat(%s)' % ', '.join(parts)

    def __bool__(self):
        return bool(self.node)

    # It is a bit faster, but not necessary to offer all comparison operators:
    def __lt__(self, other):
        return self.min_index.__lt__(other.min_index)

    def __gt__(self, other):
        return self.min_index.__gt__(other.min_index)

    def __le__(self, other):
        return self.min_index.__le__(other.min_index)

    def __ge__(self, other):
        return self.min_index.__ge__(other.min_index)

    def __eq__(self, other):
        return self.min_index.__eq__(other.min_index)

    def __ne__(self, other):
        return self.min_index.__ne__(other.min_index)


class Expansion:
    def __init__(self, msg='', part1=None, part2=None, word=None, word_parent=None):
        self.msg = msg
        self.part1 = part1
        self.part2 = part2
        self.word = word
        self.word_parent = word_parent

    def __repr__(self):
        return 'Expansion(msg=%r, part1=%r, part2=%r)' % (self.msg, self.part1, self.part2)


class Parse:
    def __init__(self, probability, input_words, cat_queue, tree, msg, prev):
        self.probability = probability
        self.input_words = input_words
        self.cat_queue = cat_queue
        self.tree = tree
        self.msg = msg
        self.prev = prev
        self.count = 0  # this is used for id by Output and set by Output.

    def __lt__(self, other):
        return self.probability.__lt__(other.probability)

    def __gt__(self, other):
        return self.probability.__gt__(other.probability)

    def __le__(self, other):
        return self.probability.__le__(other.probability)

    def __ge__(self, other):
        return self.probability.__ge__(other.probability)

    def __eq__(self, other):
        return self.probability.__eq__(other.probability)

    def __ne__(self, other):
        return self.probability.__ne__(other.probability)


class Mover:
    def __init__(self, node=None, index=None):
        self.node = node
        self.index = index or []

    def __repr__(self):
        return 'Mover(node=%r, index=%r)' % (self.node, self.index)


class Parser:
    def __init__(self, lex_items, min_p=0.0001, forest=None, syntax_connection=None, outfile=None):
        if isinstance(lex_items, str):
            if len(lex_items.splitlines()) < 2:
                self.lex_trees = load_grammar_from_file(filename=lex_items)
            else:
                self.lex_trees = load_grammar(lex_items)
        elif isinstance(lex_items, dict):
            self.lex_trees = lex_items
        else:
            raise ValueError
        self.printer = DerivationPrinter(forest, outfile)
        self.printer.print_lexicon(self.lex_trees)
        self.syntax_connection = syntax_connection
        self.min_probability = min_p
        self.outfile = outfile
        self.active_category = None
        self.active_parse = None
        self.word = ''
        self.expansions = []
        self.derivation_queue = []
        self.kataja_lex_tree = None
        self.c = 0

    def step_info(self):
        mover_keys = ', '.join(['-' + x for x in self.active_category.movers.keys()]) or None
        sen_str = ' '.join(self.active_parse.input_words)
        return f"{sen_str}\nStep {self.c}, exp. {len(self.expansions) + 1}, movers: {mover_keys}\n"

    def find_matching_subtree(self, node, target):
        for tree in node.parts:
            if tree.feat and tree.feat.name == target.feat.name:
                return tree

    # merge a (non-moving) complement
    def merge1(self, target, leaves):
        """ backtrack external_merge(head, complement) """
        parent = self.active_category

        # This is an external merge of a new constituent, where the first constituent has
        # features (=X ... Y) and the other constituent (X ...). The result of merge has category Y,
        # meaning that Y is the head category.
        # Because we already have the result, we'll get Y from there.
        # The checked feature =X is the current active_feature, the feature we want to get rid of.
        X = target.feat.name
        Y = parent.node.feat

        head = Cat(node=LexNode(key=target.key, feat=target.feat, parts=leaves),
                   index=add_left_child(parent.index),
                   checked=parent.checked + [Feature(X, '=')],
                   path=add_left_child(parent.path))
        # If there are any free movers, they have to go to the complement. Head won't have
        # any use for them.
        comp_source = self.lex_trees.get(X, LexNode())
        complement = Cat(node=comp_source,
                         index=add_right_child(parent.index),
                         checked=[Feature(X, '')],
                         movers=same_as(parent.movers),
                         moving=same_as(parent.moving),
                         path=add_right_child(parent.path))

        msg = self.step_info()
        msg += f"Having (✓{X} {Y}... ) and lexicon match ...{X}\n"
        msg += f"assume external merge1((LI:: ={X} ... {Y} ...), ({X} ...))\n"
        msg += f"head = merge(head, complement)"

        self.expansions.append(Expansion(msg, head, complement))

    # merge an adjunct to the right
    def merge1b(self, target, leaves):
        """ backtrack external_merge(head, complement) """
        print('doing merge1b')
        parent = self.active_category

        head = Cat(node=LexNode(key=target.key, feat=target.feat, parts=leaves),
                   index=add_left_child(parent.index),
                   checked=parent.checked + [Feature(target.feat.name, '≈')],
                   path=add_left_child(parent.path))

        # Movers are from complement
        adj_source = self.lex_trees.get(target.feat.name, LexNode())
        adjunct = Cat(node=adj_source,
                      index=add_right_child(parent.index),
                      checked=[],
                      movers=same_as(parent.movers),
                      moving=same_as(parent.moving),
                      path=add_right_child(parent.path))

        self.expansions.append(Expansion('Merge 1b', head, adjunct))

    # merge a (non-moving) specifier
    def merge2(self, target, nodes):
        """ backtrack external_merge(specifier, head) """
        parent = self.active_category
        X = target.feat.name
        Y = parent.node.feat

        # specifier may have brought movers
        specifier = Cat(node=LexNode(key=target.key, feat=target.feat, parts=nodes),
                        index=add_right_child(parent.index),
                        movers=parent.movers,
                        moving=parent.moving,
                        checked=parent.checked + [Feature(X, '=')],
                        path=add_left_child(parent.path))

        # no movers from head
        prev_head = self.lex_trees.get(X, Cat())
        head = Cat(node=prev_head,
                   index=add_left_child(parent.index),
                   checked=[Feature(X, '')],
                   path=add_right_child(parent.path))

        msg = self.step_info()
        msg += f"Having (✓{X} {Y}... ) and lexicon match ...{X}\n"
        msg += f"assume external merge2((... ={X} {Y}), ({X} ...))\n"
        msg += f"head = merge(specifier, head)"
        self.expansions.append(Expansion(msg, specifier, head))

    # merge a (moving) complement
    def merge3(self, target, leaves):
        """ backtrack internal_merge(head, moved_complement) """
        parent = self.active_category
        for mover_name, mover in parent.movers.items():
            matching_subtree = self.find_matching_subtree(mover.node, target)
            if matching_subtree:
                X = target.feat.name
                Y = parent.node.feat
                Z = mover_name

                # head is a leaf, movers are not from there
                head = Cat(node=LexNode(key=target.key, feat=target.feat, parts=leaves),
                           index=parent.index,
                           movers={},
                           checked=parent.checked + [Feature(X, '=')],
                           path=add_left_child(parent.path))

                complement = Cat(node=matching_subtree,
                                 movers=same_as(parent.movers, remove=Z),
                                 index=mover.index,
                                 moving=same_as(parent.moving, remove=Z),
                                 checked=parent.moving[Z] + [Feature(X, '')],
                                 path=add_right_child(parent.path)
                                 )

                msg = self.step_info()
                msg += f"Having (✓{X} {Y}... )\n"
                msg += f"assume internal merge3((LI:: ={X} ... {Y}), ({X} ...-{Z} ...))\n"
                msg += f"head = merge(head, moved complement)"

                self.expansions.append(Expansion(msg, head, complement))

    # merge a (moving) specifier
    def merge4(self, target, heads):
        """ backtrack internal_merge(head, moved_specifier) """
        parent = self.active_category
        for mover_name, mover in parent.movers.items():
            matching_subtree = self.find_matching_subtree(mover.node, target)
            if matching_subtree:
                X = target.feat.name
                Y = parent.node.feat
                Z = mover_name

                heads = Cat(node=LexNode(key=target.key, feat=target.feat, parts=heads),
                            index=parent.index,
                            movers=same_as(parent.movers, remove=Z),
                            moving=same_as(parent.moving, remove=Z),
                            checked=parent.checked + [Feature(X, '=')],
                            path=add_left_child(parent.path))

                # movers passed to complement
                checked = parent.moving[Z] + [Feature(X, '')]
                complement = Cat(node=matching_subtree,
                                 index=mover.index,
                                 checked=checked,
                                 path=add_right_child(parent.path))
                msg = self.step_info()
                msg += f"Having (✓{X} {Y}... )\n"
                msg += f"assume internal merge4(... ={X} ... {Y}), ({X} ...-{Z} ...))\n"
                msg += f"head = merge(moved specifier, head)"

                self.expansions.append(Expansion(msg, heads, complement))

    def move1(self, target):
        parent = self.active_category
        X = target.feat.name
        Y = parent.node.feat

        mover_model = self.lex_trees[X]
        mover = (X, Mover(node=mover_model, index=add_left_child(parent.index)))
        moving = (X, [Feature(X, '-')])
        head = Cat(node=target,
                   index=add_right_child(parent.index),
                   movers=same_as(parent.movers, add=mover),
                   moving=same_as(parent.moving, add=moving),
                   path=add_left_child(parent.path),
                   checked=parent.checked + [Feature(X, '+')])

        msg = self.step_info()
        msg += f'Move1: having (+{X} {Y}...) assume mover -{X}'
        self.expansions.append(Expansion(msg, head))

    def move2(self, target):
        parent = self.active_category
        X = target.feat.name
        for mover_name, mover in parent.movers.items():
            matching_subtree = self.find_matching_subtree(mover.node, target)
            if matching_subtree:
                if X == mover_name or X not in parent.movers:  # SMC
                    mover = (X, Mover(node=matching_subtree, index=mover.index))
                    moving = (X, parent.moving[mover_name] + [Feature(X, '-')])

                    head = Cat(node=target,
                               index=parent.index,
                               movers=same_as(parent.movers, remove=mover_name, add=mover),
                               moving=same_as(parent.moving, remove=mover_name, add=moving),
                               checked=parent.checked + [Feature(X, '+')],
                               path=add_left_child(parent.path))

                    msg = self.step_info()
                    msg += f'Move2: having (+{X} +{mover_name}...) assume mover -{X}'
                    self.expansions.append(Expansion(msg, head))

    def create_expansions(self):
        for target in self.active_category.node.parts:
            if target.feat:
                if target.feat.sign == '=':  # feature 'sel', selects
                    leaves = [n for n in target.parts if not n.parts]
                    branches = [n for n in target.parts if n.parts]
                    if leaves:
                        self.merge1(target, leaves)
                        self.merge3(target, leaves)
                    if branches:
                        self.merge2(target, branches)
                        self.merge4(target, branches)
                elif target.feat.sign == '+':  # feature 'pos', triggers movement
                    if target.feat.name not in self.active_category.movers:  # SMC
                        self.move1(target)
                    self.move2(target)
                elif target.feat.sign == '≈':  # adjunct, selects but doesn't remove selected
                    leaves = [n for n in target.parts if not n.parts]
                    if leaves:
                        self.merge1b(target, leaves)
                elif target.feat.sign == '>':  # insert
                    pass
                else:
                    print('cannot handle active feature:', target.feat)
                    raise RuntimeError('create_expansions')
            else:  # the next node is a string node
                if (not self.expansions) and (target.word == '∅' or target.word == self.word):
                    word = Cat(target,
                               checked=self.active_category.checked,
                               path=self.active_category.path)
                    msg = self.step_info()
                    msg += f"Lexicon scan found ({target.word or '∅'}:: "
                    msg += f"...{self.active_category.node.feat})"
                    # print('creating word expansion: word %s (%s), parent %s' % (
                    #      target.word, target.key, self.active_category.node))
                    self.expansions.append(
                        Expansion(msg,
                                  word=word,
                                  word_parent=self.active_category.node.key))

    def insert_new_parses(self, new_p):
        parse = self.active_parse
        # print()
        # print('*** Adding new parses: ', len(self.expansions), new_p)
        for exp in self.expansions:
            if exp.word:  # ic is result of scan
                word_cat = exp.word
                new_tree = parse.tree + [
                    Constituent(word_cat.node.word,
                                features=list(reversed(word_cat.checked)),
                                path=list(word_cat.path),
                                movers=word_cat.movers,
                                lex_key=word_cat.node.key,
                                parent_lex_key=exp.word_parent)]
                cut = 1 if parse.input_words and word_cat.node.word == parse.input_words[0] else 0
                new_parse = Parse(parse.probability, parse.input_words[cut:],
                                  parse.cat_queue, new_tree, exp.msg, self.active_parse)
            else:  # merge or move
                part1 = exp.part1
                cat_queue = list(parse.cat_queue)
                heapq.heappush(cat_queue, part1)
                new_tree = parse.tree + [
                    Constituent(path=list(part1.path),
                                features=list(reversed(part1.checked)),
                                movers=part1.movers,
                                lex_key=part1.node.key)]
                if exp.part2:  # merge
                    part2 = exp.part2
                    heapq.heappush(cat_queue, part2)
                    new_tree.append(
                        Constituent(path=list(part2.path),
                                    features=list(reversed(part2.checked)),
                                    movers=part2.movers,
                                    lex_key=part2.node.key))
                new_parse = Parse(new_p, list(parse.input_words), cat_queue,
                                  new_tree, exp.msg, self.active_parse)
            heapq.heappush(self.derivation_queue, new_parse)

    def derive(self, partial_results=False):
        self.c = 0
        while len(self.derivation_queue) > 0 and self.c < 300:
            self.active_parse = heapq.heappop(self.derivation_queue)
            self.c += 1
            print('# of parses in beam=' + str(
                len(self.derivation_queue) + 1) + ', p(best parse)=' + str(
                (-1 * self.active_parse.probability)))
            if not (self.active_parse.cat_queue or self.active_parse.input_words):
                print('parse found')
                return
            elif self.active_parse.cat_queue:
                # expand best parses
                self.active_category = heapq.heappop(self.active_parse.cat_queue)
                self.word = self.active_parse.input_words[0] if self.active_parse.input_words else ''

                self.expansions = []
                self.create_expansions()
                if self.expansions:
                    new_prob = self.active_parse.probability / len(self.expansions)
                    if new_prob < self.min_probability:
                        self.insert_new_parses(new_prob)
                        # print(self.active_parse.msg)
                        if partial_results:
                            self.printer.show_results(self.active_parse)
                    else:
                        print('improbable parses discarded')
        print('no parse found')
        print('c = ', self.c)

    def parse(self, input_words, start='C', lex=''):  #
        if lex:
            self.lex_trees = load_grammar(lex)
        if not input_words:
            return
        start_node = self.lex_trees[start]  # initial head
        start_cat = Cat(start_node, checked=[Feature(start, '')])
        # derivation
        cat_queue = [start_cat]
        heapq.heapify(cat_queue)  # modifed EA

        self.derivation_queue = [Parse(  # List of parse states
            -1.0,  # parse probability, lower is better (negated), used for sorting
            input_words,  # remaining sentence
            list(cat_queue),  # list of prediction states at this point
            [Constituent(lex_key='center')],  # built tree at this point
            ' '.join(input_words),  # output message
            None  # for backtracking, there is no previous parse
        )]
        heapq.heapify(self.derivation_queue)

        t0 = time.time()
        self.derive(partial_results=in_kataja)
        prev = self.active_parse
        c = 0
        while prev:
            prev = prev.prev
            c += 1
        print(f'{c} steps required, ignoring missteps.')
        t1 = time.time()
        self.printer.compile_results(self.active_parse, ' '.join(input_words))
        print(str(t1 - t0) + "seconds")


# with mgxx, p=0.000000001 is small enough for: a b b b b a b b b b
# with mg0, p=0.0001 is small enough for:
# which king says which queen knows which king says which wine the queen prefers

sentences = [
    ('mg2.txt', 'N', 'wine'),
    ('mg2.txt', 'D', 'the wine'),
    ('mg2.txt', 'V', 'prefers the wine'),
    ('mg2.txt', 'C', 'prefers the wine'),
    ('mg2.txt', 'C', 'knows prefers the wine'),
    ('mg2.txt', 'C', 'says prefers the wine'),
    ('mg2.txt', 'C', 'knows says knows prefers the wine'),
    ('mg1.txt', 'C', 'the queen prefers the wine'),
    ('mg1.txt', 'C', 'the king knows the queen prefers the wine'),
    ('mg0.txt', 'C', 'which wine the queen prefers'),
    ('mg0.txt', 'C', 'which wine prefers the wine'),
    ('mg0.txt', 'C', 'the king knows which wine the queen prefers'),
    ('mg0.txt', 'C', 'the king knows which queen prefers the wine'),
    ('mg0.txt', 'C', 'which queen says the king knows which wine the queen prefers'),
    ('mgxx.txt', 'T', 'a a')
    # ('mg3.txt', 'C', 'the senator that blip attack the reporter')
]
# ('mg3.txt', 'C', 'the reporter that the senator attack -ed admit -ed the error')]

if __name__ == '__main__':
    write_file = open(OUTFILE, 'w') if OUTFILE else None
    prev_file = ''

    for gfile, start, sen in sentences:
        p = Parser(lex_items=gfile, min_p=0.0001, outfile=write_file)
        p.parse(sen.split(), start)
        if gfile != prev_file:  # don't write same file multiple times
            write_lexicon_graph_json(p.lex_trees, gfile)
            prev_file = gfile

    if write_file is not None:
        write_file.close()
        if COMPARISON_FILE:
            a = open(OUTFILE, 'r')
            b = open(COMPARISON_FILE, 'r')
            a_str = a.read()
            b_str = b.read()
            assert a_str == b_str
