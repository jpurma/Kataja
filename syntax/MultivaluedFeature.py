# coding=utf-8
""" ConfigurableFeature aims to be general implementation for a (syntactic) Feature """
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

from syntax.BaseFeature import BaseFeature


class MultivaluedFeature(BaseFeature):
    """ MultivaluedFeatures can have list of values, otherwise see BaseFeature. It converts other
    iterables to list if given as values, and monads to list objects
    """

    def __init__(self, name='Feature', value=None, family=''):
        super().__init__()
        self.name = name
        if isinstance(value, (list, tuple, set)):
            self.value = list(value)
        else:
            self.value = [value]
        self.value = value
        self.family = family

    def has_value(self, prop):
        return prop in self.value or prop == self.value

    def add_value(self, val):
        if val not in self.value:
            self.poke('value')
            self.value.append(val)

    def remove_value(self, val):
        if val in self.value:
            self.poke('value')
            self.value.remove(val)

    def __repr__(self):
        return "MultivaluedFeature(name=%r, value=%r, family=%r)" % (self.name,
                                                                     self.value,
                                                                     self.family)

    def __str__(self):
        s = []
        if self.value in ('+', '-', '=', 'u'):
            s.append(self.value + str(self.name))
        else:
            s.append(str(self.name))
            s.append(str(self.value))
        if self.family:
            s.append(str(self.family))
        return ":".join(s)

