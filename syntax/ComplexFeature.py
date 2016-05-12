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

from syntax.MultivaluedFeature import MultivaluedFeature
from syntax.BaseFeature import BaseFeature


class ComplexFeature(MultivaluedFeature):
    """ ComplexFeatures have list of values, where values can be other features. It converts
    other iterables to list if these are given as values, and monads to list objects
    """

    def has_value(self, prop):
        for item in self.value:
            if item == prop:
                return True
            if isinstance(item, BaseFeature) and item.has_value(prop):
                return True
        return False

    def __repr__(self):
        return "ComplexFeature(type=%r, value=%r, assigned=%r, family=%r)" % (self.type,
                                                                              self.value,
                                                                              self.assigned,
                                                                              self.family)
