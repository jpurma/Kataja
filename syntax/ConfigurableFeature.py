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

from kataja.Saved import Savable

class Feature(Savable):
    """
    >>> a=Feature('nom','case','deletable')
    >>> a.get()
    u'nom'
    >>> a.iss('case')
    True
    >>> a.iss('phon')
    False
    >>> a.iss('nom')
    True
    >>> a.iss('+')
    False
    >>> a.add('+')
    >>> a
    nom:case:deletable:+
    >>> print a
    nom:case:deletable:+
    >>> a.remove('+')
    >>> print a
    nom:case:deletable
    >>> b=Feature('nom:case:deletable')
    >>> a==b
    True
    >>> b.remove('case')
    >>> a==b
    False
    >>> a!=b
    True
    """

    def __init__(self, key=None, value=None, values=None):
        Savable.__init__(self)
        if key and not (value or values): # e.g. 'nom:case:deletable'
            values = key.split(':')
            key = values.pop(0)
        elif not key:
            key = "AnonymousFeature"
        self.saved.fkey = key
        if values:
            self.saved.values = values
        elif value:
            self.saved.values = [value]
        else:
            self.values = []


    @property
    def label(self):
        return self.saved.fkey

    @property
    def key(self):
        """


        :return:
        """
        return self.saved.fkey

    @key.setter
    def key(self, value):
        """

        :param value:
        """
        self.saved.fkey = value

    @property
    def value(self):
        """


        :return:
        """
        if self.saved.values:
            return self.saved.values[0]
        else:
            return None

    @value.setter
    def value(self, value):
        """

        :param value:
        """
        self.saved.values = [value]

    @property
    def values(self):
        """


        :return:
        """
        return self.saved.values

    @values.setter
    def values(self, value):
        """

        :param value:
        """
        if isinstance(value, list):
            self.saved.values = value
        else:
            self.saved.values = [value]

    def get(self):
        """


        :return:
        """
        return self.key

    def get_value_string(self):
        """


        :return:
        """
        return ', '.join(self.values)

    def add(self, prop):
        """

        :param prop:
        """
        if not prop in self.values:
            self.values.append(prop)


    def iss(self, prop):
        """

        :param prop:
        :return:
        """
        return prop == self.key or prop in self.values

    def remove(self, prop):
        """

        :param prop:
        :raise KeyError:
        """
        if prop in self.values:
            self.values.remove(prop)
        else:
            raise KeyError

    def __repr__(self):
        return ":".join([self.key] + self.values)

    def __str__(self):
        return ":".join([self.key] + self.values)

    def save(self):
        """


        :return:
        """
        return self.__repr__()

    def reconnect(self, d):
        """

        :param d:
        """
        pass


if __name__ == "__main__":
    import doctest

    doctest.testmod(exclude_empty=True)
