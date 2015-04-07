# coding=utf-8
""" ConfigurableConstituent tries to be theory-editable constituent, whose behaviour can be adjusted
in very specific manner. Configuration is stored in UG-instance.config -dict and can be changed from outside. """

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
from kataja.BaseModel import BaseModel

from syntax.ConfigurableFeature import Feature

class ConfigurableConstituent(BaseModel):
    """

    :param cid:
    :param config:
    """

    def __init__(self, cid='', config=None):
        """ BaseConstituent is a default constituent used in syntax.
        It is Savable, which means that the actual values are stored in separate object that is easily dumped to file.
        Extending this needs to take account if new fields should also be treated as savable, e.g. put them into
        .model. and make necessary property and setter.
         """
        BaseModel.__init__(self)
        self.config = config
        self.implicit_order = False
        if config:
            if 'implicit_order' in config:
                self.implicit_order = config['implicit_order']

        self.model.features = {}
        self.model.sourcestring = source or cid
        self.model.label = cid
        self.model.alias = ''
        self.model.parts = []
        self.model.gloss = ''
        self.model.index = ''

    def __str__(self):
        if self.index:
            return '%s_%s' % (self.label, self.index)
        else:
            return str(self.label)

    @property
    def features(self):
        """


        :return:
        """
        return self.model.features

    @features.setter
    def features(self, value):
        """
        :param value:
        """
        if value:
            for key, feature in value.items():
                if key == 'label':
                    self.label = feature.value
                elif key == 'index':
                    self.index = feature.value
                else:
                    self.model.features[key] = feature
        else:
            self.model.features = {}

    @property
    def sourcestring(self):
        """


        :return:
        """
        return self.model.sourcestring

    @sourcestring.setter
    def sourcestring(self, value):
        """

        :param value:
        """
        self.model.sourcestring = value

    @property
    def label(self):
        """


        :return:
        """
        return self.model.label

    @label.setter
    def label(self, value):
        """

        :param value:
        """
        if value is None:
            self.model.label = ''
        else:
            self.model.label = value

    @property
    def alias(self):
        """


        :return:
        """
        return self.model.alias

    @alias.setter
    def alias(self, value):
        """

        :param value:
        """
        if value is None:
            self.model.alias = ''
        else:
            self.model.alias = value

    @property
    def left(self):
        """


        :return:
        """
        if self.model.parts:
            return self.model.parts[0]
        else:
            return None

    @left.setter
    def left(self, value):
        """

        :param value:
        """
        if not self.model.parts:
            self.model.parts = [value]
        else:
            self.model.parts[0] = value

    @property
    def right(self):
        """


        :return:
        """
        if self.model.parts and len(self.model.parts) > 1:
            return self.model.parts[1]
        else:
            return None

    @right.setter
    def right(self, value):
        """

        :param value:
        """
        if self.model.parts:
            if len(self.model.parts) > 1:
                self.model.parts[1] = value
            else:
                self.model.parts.append(value)
        else:
            self.model.parts = [None, value]

    @property
    def gloss(self):
        """


        :return:
        """
        return self.model.gloss

    @gloss.setter
    def gloss(self, value):
        """

        :param value:
        """
        if value is None:
            self.model.gloss = ''
        else:
            self.model.gloss = value

    @property
    def index(self):
        """


        :return:
        """
        return self.model.index

    @index.setter
    def index(self, value):
        """

        :param value:
        """
        if value is None:
            self.model.index = ''
        else:
            self.model.index = value


    def __repr__(self):
        if self.is_leaf():
            if self.index:
                return 'Constituent(id=%s, index=%s)' % (self.label, self.index)
            else:
                return 'Constituent(id=%s)' % self.label
        else:
            if self.index:
                return "[.%s %s %s ]" % (self.index, self.left, self.right)
            else:
                return "[ %s %s ]" % (self.left, self.right)


    def __contains__(self, C):
        if self == C:
            return True
        if self.left:
            if self.left.__contains__(C):
                return True
        if self.right:
            if self.right.__contains__(C):
                return True
        else:
            return False


    def print_tree(self):
        """


        :return:
        """
        return self.__repr__()
        #
        # if self.is_leaf():
        #     if self.index:
        #         return '%s_%s' % (self.label, self.index)
        #     else:
        #         return self.label
        # else:
        #     if self.left:
        #         l = self.left.print_tree()
        #     else:
        #         l = '*0*'
        #     if self.right:
        #         r = self.right.print_tree()
        #     else:
        #         r = '*0*'
        #     if self.index:
        #         i = '.%s' % self.index
        #     else:
        #         i = ''
        #     return "[%s %s %s ]" % (i, l, r)



    def get_feature(self, key):
        """

        :param key:
        :return:
        """
        f = self.features.get(key, None)
        if f:
            return f.get()
        return None

    def has_feature(self, key):
        """

        :param key:
        :return:
        """
        if isinstance(key, Feature):
            return key in list(self.features.values())
        return key in list(self.features.keys())


    def set_feature(self, key, value):
        """

        :param key:
        :param value:
        """
        print('set_feature called in constituent')
        if isinstance(value, Feature):
            self.features[key] = value
        else:
            f = self.features.get(key, None)
            if f:
                f.set(value)
            else:
                f = Feature(key, value)
            self.features[key] = f


    def del_feature(self, key):
        """

        :param key:
        """
        if isinstance(key, Feature):
            key = key.key
        if hasattr(self.features, key):
            del self.features[key]

    def is_leaf(self):
        """


        :return:
        """
        return not (self.left or self.right)

    def copy(self):
        """


        :return:
        """
        if self.left:
            left = self.left.copy()
        else:
            left = None
        if self.right:
            right = self.right.copy()
        else:
            right = None
        new = self.__class__(self.label, left, right)
        for key, value in self.features.items():
            new.set_feature(key, value)
        return new
