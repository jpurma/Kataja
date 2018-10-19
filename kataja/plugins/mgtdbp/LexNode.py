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


class LexNode:
    def __init__(self, key=None, feat=None, word=None, parts=None):
        self.key = key
        self.feat = feat
        self.word = word
        self.parts = parts or []

    def __repr__(self):
        parts = ['key=%r' % self.key]
        if self.feat:
            parts.append('feat=%r' % self.feat)
        if self.word:
            parts.append('word=%r' % self.word)
        if self.parts:
            parts.append('parts=%r' % self.parts)
        return 'LexNode(%s)' % ', '.join(parts)
