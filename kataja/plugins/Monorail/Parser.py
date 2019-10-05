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
    from kataja.plugins.Monorail.Constituent import Constituent
    from kataja.syntax.SyntaxState import SyntaxState
    from kataja.syntax.BaseFeature import BaseFeature as Feature
except ImportError:
    from Constituent import Constituent

    Feature = None
    SyntaxState = None

import random
import string

punctuation = '.,!?*'


def next_letter(char):
    return string.ascii_letters[string.ascii_letters.index(char) + 1]


# The first matching feature pair is returned (start to look from positive features at right).
def find_checked_features_1(left, right):
    checked_features = []
    for feat in right.inherited_features:
        if feat.used:
            continue
        if feat.sign == '' or feat.sign == '+':
            for feat_to_check in left.inherited_features:
                if feat_to_check.used:
                    continue
                if (feat_to_check.name == feat.name and
                        feat_to_check.sign and
                        feat_to_check.sign in '=-_≤'):
                    checked_features.append((feat_to_check, feat))
    return checked_features


# Strictly match features, match has to be from the first unused feature in both left and right
def find_checked_features_2(left, right):
    checked_features = []
    for feat in right.inherited_features:
        if feat.used:
            continue
        if feat.sign == '' or feat.sign == '+':
            for feat_to_check in left.inherited_features:
                if feat_to_check.used:
                    continue
                if (feat_to_check.name == feat.name and
                        feat_to_check.sign and
                        feat_to_check.sign in '=-_≤'):
                    checked_features.append((feat_to_check, feat))
                    continue
                break
        break
    return checked_features


# Strictly match positive features, the feature must be the first unused positive in the right
def find_checked_features_3(left, right):
    checked_features = []
    for feat in right.inherited_features:
        if feat.used:
            continue
        if feat.sign == '' or feat.sign == '+':
            found = False
            for feat_to_check in left.inherited_features:
                if feat_to_check.used:
                    continue
                if (feat_to_check.name == feat.name and
                        feat_to_check.sign and
                        feat_to_check.sign in '=-_≤'):
                    checked_features.append((feat_to_check, feat))
                    found = True
            print('tried to find match for ', feat, ' in ', left.inherited_features)
            if not found:
                break
    return checked_features


# Strictly match negative feature, the feature must be the first unused negative in the left
def find_checked_features_4(left, right):
    checked_features = []
    for feat in right.inherited_features:
        if feat.used:
            continue
        if feat.sign == '' or feat.sign == '+':
            for feat_to_check in left.inherited_features:
                if feat_to_check.used or feat_to_check.sign not in '=-_≤':
                    continue
                if feat_to_check.name == feat.name and feat_to_check.sign:
                    checked_features.append((feat_to_check, feat))
                else:
                    break
    return checked_features


def mark_used_1(feat_to_check, feat):
    if feat.sign == '':
        feat_to_check.used = True
    elif feat.sign == '+':
        feat_to_check.used = False

    if feat_to_check.sign == '=':
        feat.used = True
    elif feat_to_check.sign == '-':
        feat.used = True
    elif feat_to_check.sign == '≤':
        feat.used = True
    elif feat_to_check.sign == '_':
        feat.used = False
        # merged.parts = [right, left]
    else:
        raise ValueError


find_checked_features = find_checked_features_3
mark_used = mark_used_1


def inherit_features(head):
    new_feats = []
    for f in head.inherited_features:
        if f.used or f in new_feats:
            continue
        new_feats.append(f)
    return new_feats


def check_features(merged):
    left, right = merged.parts
    checked_features = find_checked_features(left, right)
    for feat_to_check, feat in checked_features:
        mark_used(feat_to_check, feat)
        feat.check(feat_to_check)
    merged.checked_features = checked_features


def deduce_head(merged):
    left, right = merged.parts
    head = None
    if merged.checked_features:
        for feat_to_check, feat in merged.checked_features:
            if feat_to_check.sign == '=' or feat_to_check.sign == '≤':
                head = left
            else:
                head = right
            if feat_to_check.sign == '≤':
                merged.parts = [right, left]
    else:
        if left.parts:
            head = right
        else:
            head = left
    merged.inherited_features = inherit_features(head)
    merged.lexical_heads = list(head.lexical_heads)


def merge(left, right):
    merged = Constituent(parts=[left, right])
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
    if not needy_node:
        return
    if not giving_node:
        return
    needy_head = needy_node.lexical_heads[0]
    giving_head = giving_node.lexical_heads[0]
    for feat in needy_head.features:
        if feat.is_needy() and not feat.used:
            available_needy_feat = feat
            available_giving_feat = None
            for ofeat in giving_head.features:
                if ofeat.name == available_needy_feat.name and ofeat.sign == '':
                    if ofeat.used:
                        available_needy_feat = None
                    available_giving_feat = ofeat
                    break
            if available_needy_feat and available_giving_feat:
                return available_needy_feat, available_giving_feat
            elif available_needy_feat:
                new_feature = Feature(name=available_needy_feat.name, sign='')
                giving_head.features.append(new_feature)
                new_feature.host = giving_head
                return available_needy_feat, new_feature
    combined = needy_head.features + giving_head.features
    fname = string.ascii_letters[max([string.ascii_letters.index(f.name[0]) for f in
                                      combined]) + 1] if combined else 'a'
    if needy_node.parts:
        if random.randint(1, 2) == 1:  # and False:
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


def deduce_lexicon_from_recipe(recipe, lexicon=None):
    # deduce features phase
    tree = None
    lexicon = lexicon or {}
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
                features = []
                node = Constituent(label=lexem, features=features)
                lexicon[lexem] = node
            tree = merge(node, tree or startnode())

    for node in lexicon.values():
        for feature in node.features:
            feature.reset()
    return lexicon


def fast_find_movable_1(node, excluded=None):
    # finds the uppermost external merged element and takes its sibling, e.g. the tree that EM
    # node was merged with.
    # probably not enough when there is a series of raises that should be done.
    if not excluded:
        excluded = node
    if node.parts:
        if node is not excluded:
            for part in node.parts:
                if not part.has_raised:
                    return node
        for part in node.parts:
            n = fast_find_movable_1(part, excluded=excluded)
            if n:
                return n
    return None


def fast_find_movable_2(node, excluded=None):
    # finds the uppermost external merged element and takes its sibling, e.g. the tree that EM
    # node was merged with.
    # probably not enough when there is a series of raises that should be done.
    if not excluded:
        excluded = node
    if node.parts:
        if node is not excluded:
            for part in node.parts:
                if not part.has_raised:
                    return node
        for part in node.parts:
            n = fast_find_movable_1(part, excluded=excluded)
            if n:
                return n
    return None


def fast_find_movable_3(node):
    # finds the uppermost external merged element and takes its sibling, e.g. the tree that EM
    # node was merged with.
    # probably not enough when there is a series of raises that should be done.
    if node.parts:
        left, right = node.parts
        if right.parts:
            return right.parts[0]
        return right
    return None


def fast_find_movable_4(node, excluded=None):
    # finds the uppermost external merged element and takes its sibling, e.g. the tree that EM
    # node was merged with.
    # probably not enough when there is a series of raises that should be done.
    if not excluded:
        excluded = node
    if node.parts:
        if node is not excluded and not (node.checked_features and node.has_raised):
            return node
        for part in node.parts:
            n = fast_find_movable_4(part, excluded=excluded)
            if n:
                return n
    return None


fast_find_movable = fast_find_movable_4


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
    c = Constituent(label='', features=[Feature(name='0', sign='')])
    c.has_raised = True
    return c


def parse_from_recipe(recipe, lexicon, forest):
    # build phase
    tree = None
    for lexem in recipe:
        if lexem == '|':
            node = fast_find_movable(tree)
            tree = merge(node, tree)
        else:
            node = lexicon[lexem].copy()
            tree = merge(node, tree or startnode())
        export_to_kataja(tree, lexem, fast_find_movable(tree), forest)
    return tree


def export_to_kataja(tree, message, focus, forest):
    if forest:
        syn_state = SyntaxState(tree_roots=[tree], msg=message,
                                state_id=Constituent.nodecount,
                                groups=[('', focus)] if focus else None)
        forest.add_step(syn_state)


def parse(sentence, lexicon, forest):
    tree = None
    for lexem in sentence:
        # External Merge
        if lexem in lexicon:
            node = lexicon[lexem].copy()
        else:
            node = Constituent(lexem)
            lexicon[lexem] = node.copy()
        tree = merge(node, tree or startnode())
        deduce_head(tree)
        raising_node = fast_find_movable(tree)
        export_to_kataja(tree, 'em: %s' % lexem, raising_node, forest)
        checking = find_checked_features(raising_node, tree) if raising_node else None
        # Do Internal Merges as long as possible
        while checking:
            tree = merge(raising_node, tree)
            check_features(tree)
            deduce_head(tree)
            raising_node.has_raised = True
            raising_node = fast_find_movable(tree)
            export_to_kataja(tree, 'internal merge, ' + str(checking), raising_node, forest)
            checking = find_checked_features(raising_node, tree) if raising_node else None
    return tree


def read_lexicon(lexdata):
    lex = {}
    if isinstance(lexdata, list):
        lines = lexdata
    else:
        lines = lexdata.splitlines()
    print('read_lexicon has lines: ', lines)

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


def load_lexicon(filename):
    f = open(filename)
    lines = f.readlines()
    print('loaded lexicon strings as lines: ', repr(lines))
    f.close()
    return read_lexicon(lines)
