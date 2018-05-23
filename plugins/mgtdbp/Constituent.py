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
    from syntax.BaseConstituent import BaseConstituent
except ImportError:
    BaseConstituent = None


class Constituent(BaseConstituent or object):
    def __init__(self, label='', features=None, parts=None, path=None, movers=None,
                 lex_key=None, parent_lex_key=None):
        """ Constituents
        :param label:
        :param features:
        :param parts:
        :param path:
        """
        if BaseConstituent:
            super().__init__(label, parts=parts, features=features)
        else:
            self.label = label
            self.features = list(features) if features else []
            self.parts = parts or []
        self.lex_key = lex_key
        # parent_lex_key is only used to map constituents back to mgtdbp lexical entries.
        # Mgtdbp lexical nodes have separate node for word root and each of its features,
        # [LexNode(word='kitty', feats=[], key='n1'), LexNode(word='', feats=[N, =A], key='n0')]
        # whereas Constituent combines the last of the features and the word root into one node:
        # Constituent(label='kitty', features=[N, =A], lex_key='n1', parent_lex_key='n0')
        # Now we need constituent to still keep keys for both, so that we can show which
        # lex entries are involved in it.
        self.parent_lex_key = parent_lex_key
        self.path = path or []
        self.movers = movers or {}

    def find_closest_available(self, fname, fsign):
        for feat in self.features:
            if (feat.name == fname and feat.sign == fsign and not
                    (getattr(feat, 'checks', None) or getattr(feat, 'checked_by', None))):
                return self, feat
        for part in self.parts:
            found, found_f = part.find_closest_available(fname, fsign)
            if found:
                return found, found_f
        return None, None

    def to_dtree(self):
        """ This is print out tree that aims to be identical with output from original mgtdbp-dev
        :param t:
        :return:
        """
        if self.parts:
            return [self.label] + [p.to_dtree() for p in self.parts]
        elif self.label:
            return [self.label], [f.mgtdbp_tuple() for f in self.features]
        else:
            return [], [f.mgtdbp_tuple() for f in self.features]

    def to_tree(self):
        """ This is print out that tries to remain true for constituent information
        :param t:
        :return:
        """
        if self.label == '*':
            return ['*::%s' % ', '.join([str(f) for f in self.features])] + \
                   [p.to_tree() for p in self.parts]
        elif self.label == 'o':
            return ['o::%s' % ', '.join([str(f) for f in self.features])] + \
                   [self.parts[0].to_tree()]
        else:  # put [] around the word so that we get identical output with original mghtdbp-dev
            if self.label and self.features:
                return [self.label] + self.features
            elif self.parts:
                return ''.join([p.to_tree() for p in self.parts])
            else:
                return [''] + self.features

    def __repr__(self):
        return 'Constituent(label=%r, features=%r, parts=%r, path=%r, movers=%r. lex_key=%r)' % (
            self.label, self.features, self.parts, self.path, self.movers, self.lex_key
        )
