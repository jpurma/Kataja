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
    from kataja.SavedField import SavedField
    from syntax.BaseConstituent import BaseConstituent
    in_kataja = True
except ImportError:
    BaseConstituent = None
    in_kataja = False


class Constituent(BaseConstituent or object):
    nodecount = 0

    def __init__(self, label='', features=None, parts=None, lexical_heads=None):
        """ Constituents
        :param label:
        :param features:
        :param parts:
        :param path:
        """
        if BaseConstituent:
            super().__init__(label, parts=parts, features=features, lexical_heads=lexical_heads)
        else:
            self.label = label
            self.features = list(features) if features else []
            self.parts = parts or []
            self.inherited_features = self.features
            if features:
                for feature in features:
                    feature.host = self

        self.has_raised = False

    def __str__(self):
        if self.parts:
            return str(self.parts)
        else:
            return repr(self.label)

    def __repr__(self):
        return str(self)

    def get_features(self):
        if self.features:
            return self.features
        else:
            return self.inherited_features

    def restore(self, done):
        if self in done:
            return None
        done.add(self)
        if self.parts:
            new_parts = []
            for part in self.parts:
                child = part.restore(done)
                if child:
                    new_parts.append(child)
            if len(new_parts) == 1:
                return new_parts[0]
            return new_parts
        return self
