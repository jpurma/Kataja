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



class Feature:
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

    saved_fields = ['uid', 'key', 'values']

    def __init__(self, key, *args):
        self.uid = id(self)
        self.save_key = self.uid
        if (not args) and key:
            args = key.split(':')
            key = args.pop(0)
        elif not key:
            key = "AnonymousFeature"
        self.key = key
        self.values = []
        for value in args:
            self.values.append(value)

    def get(self):
        """


        :return:
        """
        return self.key

    def get_value(self):
        """


        :return:
        """
        if self.values:
            return self.values[0]
        else:
            return ''

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

    def set(self, values):
        """

        :param values:
        """
        if isinstance(values, list):
            self.values = values
        else:
            self.values = [values]

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
