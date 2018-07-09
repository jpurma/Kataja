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

try:
    from Monorail.Constituent import Constituent
    from syntax.SyntaxState import SyntaxState
    from syntax.BaseFeature import BaseFeature as Feature
except ImportError:
    from Constituent import Constituent

import string
import random

punctuation = '.,!?*'


def next_letter(char):
    return string.ascii_letters[string.ascii_letters.index(char) + 1]


def find_checking_features(left, right):
    for feat in right.inherited_features:
        if feat.sign == '' and not feat.used:
            for feat_to_check in left.inherited_features:
                if ((not feat_to_check.used) and
                        feat_to_check.name == feat.name and
                        feat_to_check.sign and
                        feat_to_check.sign in '=-_'):
                    return feat_to_check, feat


def inherit_features(head, checked_features):
    new_feats = []
    for f in head.inherited_features:
        ##if f in checked_features:
        #    f.used = True
        if f.used or f in new_feats:
            continue
        new_feats.append(f)
    return new_feats


def merge(left, right):
    checking_features = find_checking_features(left, right)
    merged = Constituent(parts=[left, right])
    if checking_features:
        feat_to_check, feat = checking_features
        feat_to_check.used = True
        if feat_to_check.sign == '=':
            head = left
            feat.used = True
        elif feat_to_check.sign == '-':
            head = right
            feat.used = True
        elif feat_to_check.sign == '_':
            head = right
        else:
            raise ValueError
        feat.check(feat_to_check)
        merged.checked_features = (feat_to_check, feat)
    else:
        if left.parts:
            head = right
        else:
            head = left
    merged.inherited_features = inherit_features(head, merged.checked_features)
    merged.lexical_heads = list(head.lexical_heads)
    return merged


def remove_punctuation(inlist):
    if isinstance(inlist, list):
        left, right = inlist
        left = remove_punctuation(left)
        right = remove_punctuation(right)
        if left and right:
            return [left, right]
        else:
            return left or right
    elif inlist in punctuation:
        return ''
    else:
        return inlist


def list_to_monorail(lnode, spine, recipe):
    if isinstance(lnode, list):
        left = list_to_monorail(lnode[0], spine, recipe)
        right = list_to_monorail(lnode[1], left, recipe)
        merged = merge(left, right)
        recipe.append('|')
    elif spine:
        left = Constituent(label=lnode)
        recipe.append(lnode)
        merged = merge(left, spine)
    else:
        merged = Constituent(label=lnode)
        recipe.append(lnode)
    return merged


def come_up_with_a_reason(needy_node, giving_node):
    needy_head = needy_node.lexical_heads[0]
    giving_head = giving_node.lexical_heads[0]
    for feat in needy_head.features:
        if feat.name == 'e':
            continue
        if feat.is_needy() and not feat.used:
            available_needy_feat = feat
            available_giving_feat = None
            for feat in giving_head.features:
                if feat.name == available_needy_feat.name and feat.sign == '':
                    if feat.used:
                        available_needy_feat = None
                    available_giving_feat = feat
                    break
            if available_needy_feat and available_giving_feat:
                return available_needy_feat, available_giving_feat
            elif available_needy_feat:
                new_feature = Feature(name=available_needy_feat.name, sign='')
                giving_head.features.append(new_feature)
                new_feature.host = giving_head
                return available_needy_feat, new_feature
    fname = string.ascii_letters[max([string.ascii_letters.index(f.name[0]) for f in
                                      needy_head.features + giving_head.features]) + 1]
    if needy_node.parts:
        if random.randint(1, 2) == 1 and False:
            needy_f = Feature(fname, sign='=')
        else:
            needy_f = Feature(fname, sign='-')
    else:
        needy_f = Feature(fname, sign='=')
    giving_f = Feature(fname, sign='')
    needy_head.features.append(needy_f)
    needy_f.host = needy_head
    giving_head.features.append(giving_f)
    giving_f.host = giving_head
    needy_node.inherited_features.append(needy_f)
    giving_node.inherited_features.append(giving_f)
    return needy_f, giving_f


def deduce_lexicon_from_recipe(recipe):
    # deduce features phase
    tree = None
    lexicon = {}
    for lexem in recipe:
        if lexem == '|':
            node = fast_find_movable(tree)
            checked_feat, feat = come_up_with_a_reason(node, tree)
            # features have to be used in certain order:
            for old_feat in feat.host.features:
                if old_feat is feat:
                    break
                if old_feat.sign == '':
                    old_feat.used = True
            tree = merge(node, tree)
        else:
            if lexem in lexicon:
                node = lexicon[lexem]
                for feature in node.features:
                    feature.reset()
            else:
                features = [Feature('e', sign=''), Feature('e', sign='=')]
                node = Constituent(label=lexem, features=features)
                lexicon[lexem] = node
            if tree:
                tree = merge(node, tree)
            else:
                tree = merge(node, startnode())

    for node in lexicon.values():
        for feature in node.features:
            feature.reset()
    return lexicon


def fast_find_movable(node):
    if node.parts:
        left, right = node.parts
        if not left.edge: # and left.parts:
            right.edge = True
            return right
        return fast_find_movable(left)
    return None


def flatten(tree):
    sentence = []

    def _flat(treelist):
        if isinstance(treelist, list):
            for node in treelist:
                _flat(node)
        else:
            sentence.append(treelist)
    _flat(tree)
    return sentence


def startnode():
    return Constituent(label='', features=[Feature(name='e', sign='')])


def parse_from_recipe(recipe, lexicon, forest):
    # build phase
    tree = None
    for lexem in recipe:
        if lexem == '|':
            node = fast_find_movable(tree)
            tree = merge(node, tree)
        else:
            node = lexicon[lexem].copy()
            assert not node.checked_features
            for feat in node.features:
                assert not (feat.checked_by or feat.checks)
            if tree:
                tree = merge(node, tree)
            else:
                tree = merge(node, startnode())

            #lexicon[lexem] = node
        if forest:
            syn_state = SyntaxState(tree_roots=[tree], msg=lexem,
                                    iteration=Constituent.nodecount)
            forest.add_step(syn_state)
    return tree


def parse(sentence, lexicon, forest):
    tree = None
    for lexem in sentence:
        node = lexicon[lexem].copy()
        if tree:
            tree = merge(node, tree)
        else:
            tree = merge(node, startnode())

        raising = fast_find_movable(tree)
        if forest:
            syn_state = SyntaxState(tree_roots=[tree], msg=lexem,
                                    iteration=Constituent.nodecount,
                                    marked=[raising])
            forest.add_step(syn_state)
        if raising:
            checking = find_checking_features(raising, tree)
            while checking:
                tree = merge(raising, tree)
                raising = fast_find_movable(tree)
                if forest:
                    syn_state = SyntaxState(tree_roots=[tree],
                                            msg='internal merge, ' + str(checking),
                                            iteration=Constituent.nodecount,
                                            marked=[raising])
                    forest.add_step(syn_state)

                if raising:
                    checking = find_checking_features(raising, tree)
                else:
                    break
    return tree


def read_lexicon(lexdata):
    lex = {}
    lines = lexdata.splitlines()

    for line in lines:
        line = line.strip()
        if line.startswith('#'):
            continue
        if '::' not in line:
            continue
        lexem, features = line.rsplit('::', 1)
        lexem = lexem.strip()
        if lexem == '∅':
            lexem = ''
        features = [Feature.from_string(fstr) for fstr in features.split()]
        node = Constituent(label=lexem, features=features)
        lex[lexem] = node
    return lex
