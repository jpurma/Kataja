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
    from syntax.BaseFeature import BaseFeature
except ImportError:
    BaseFeature = None


class Feature(BaseFeature or object):
    def __init__(self, name='', sign=''):
        if BaseFeature:
            super().__init__(name=name, sign=sign)
        else:
            self.name = name
            self.sign = sign

    def mgtdbp_tuple(self):
        mymap = {
            '=': 'sel',
            '-': 'neg',
            '': 'cat',
            '+': 'pos',
            '≈': 'adj',
            '>': 'ins'
        }
        return mymap[self.sign], self.name

    def mgtdbp_str(self):
        return str((self.sign, self.name))

    def __str__(self):
        return self.sign + self.name

    def __repr__(self):
        return str((self.sign, self.name))

    def __eq__(self, other):
        return (other and
                getattr(other, 'name', None) == self.name and
                getattr(other, 'sign', None) == self.sign)

    @staticmethod
    def from_string(string):
        if not string:
            return None
        if string[0] in ['=', '-', '+', '≈', '>']:
            sign = string[0]
            name = string[1:]
        else:
            sign = ''
            name = string
        return Feature(name, sign)
