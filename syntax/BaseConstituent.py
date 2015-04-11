# coding=utf-8
""" BaseConstituent is a default constituent used in syntax.
It uses getters and setters so that other compatible implementations can be built using the same interface.
It is a primary datatype, needs to support saving and loading. """
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
# from copy import deepcopy


class BaseConstituentModel(BaseModel):
    """ BaseConstituentModel holds the data of BaseConstituent in a form that can be saved and restored easily.
    """
    def __init__(self, host):
        super().__init__(host)
        self.features = {}
        self.sourcestring = ''
        self.label = ''
        self.alias = ''
        self.parts = []
        self.gloss = ''
        self.index = ''


class BaseConstituent:
    """ BaseConstituent is a default constituent used in syntax.
    It uses getters and setters so that other compatible implementations can be built using the same interface.
    It is a primary datatype, needs to support saving and loading. """

    def __init__(self, label='', left=None, right=None, source=''):
        """ BaseConstituent is a default constituent used in syntax.
        It is Savable, which means that the actual values are stored in separate object that is easily dumped to file.
        Extending this needs to take account if new fields should also be treated as savable, e.g. put them into
        .model. and make necessary property and setter.
         """
        if not hasattr(self, 'model'):
            self.model = BaseConstituentModel(self)
        self.model.sourcestring = source or label
        self.model.label = label
        if left:
            self.model.parts.append(left)
        if right:
            self.model.parts.append(right)

    def __str__(self):
        if self.index:
            return '%s_%s' % (self.label, self.index)
        else:
            return str(self.label)

    @property
    def save_key(self):
        """ Return the save_key from the model. It is a property from BaseModel.
        :return: str
        """
        return self.model.save_key

    @property
    def features(self):
        """ Features are a dict with probably Features as values, but values can be also simpler stuff, strings etc.
        :return: dict of features
        """
        return self.model.features

    @features.setter
    def features(self, value):
        """ If given features include 'label' or 'index', put them to their right place, otherwise update with
        new values. If and empty value is given, set features to empty.
        :param value: dict of features
        """
        if value:
            self.model.poke('features')
            for key, feature in value.items():
                if key == 'label':
                    self.label = feature.value
                elif key == 'index':
                    self.index = feature.value
                else:
                    self.model.features[key] = feature
        else:
            if self.model.features:
                self.model.poke('features')
            self.model.features = {}

    @property
    def sourcestring(self):
        """ Sourcestring is provided if the constituent is created by parsing some text. Maybe unnecessary.
        :return:
        """
        return self.model.sourcestring

    @sourcestring.setter
    def sourcestring(self, value):
        """ Sourcestring is provided if the constituent is created by parsing some text. Maybe unnecessary.
        :param value: str
        """
        if self.model.touch('sourcestring', value):
            self.model.sourcestring = value

    @property
    def label(self):
        """ This is the syntactic label for the Constituent. It can be used for matching/computation purposes.
        :return: str or ITextNode
        """
        return self.model.label

    @label.setter
    def label(self, value):
        """ This is the syntactic label for the Constituent. It can be used for matching/computation purposes.
        :param value: str or ITextNode
        """
        if self.model.touch('label', value):
            if value is None:
                self.model.label = ''
            else:
                self.model.label = value

    @property
    def alias(self):
        """ This is an alias, a syntactically inert label used for readability (think XP, X', X^0 in Minimalism)
        :return: str or ITextNode
        """
        return self.model.alias

    @alias.setter
    def alias(self, value):
        """ This is an alias, a syntactically inert label used for readability (think XP, X', X^0 in Minimalism)
        :param value: str or ITextNode
        """
        if self.model.touch('alias', value):
            if value is None:
                self.model.alias = ''
            else:
                self.model.alias = value

    @property
    def left(self):
        """ This is the left child -- to be used only if syntactic theory can make such distinction locally in
        constituent itself. Another option is to do the ordering as a result of derivation, and then you will
        probably need to call some UG -ordering method.
        :return: BaseConstituent instance or None
        """
        if self.model.parts:
            return self.model.parts[0]
        else:
            return None

    @left.setter
    def left(self, value):
        """ This is the left child -- to be used only if syntactic theory can make such distinction locally in
        constituent itself. Another option is to do the ordering as a result of derivation, and then you will
        probably need to call some UG -ordering method.
        :param value: BaseConstituent instance or None
        """
        if not self.model.parts:
            self.model.poke('parts')
            self.model.parts = [value]
        elif self.model.parts[0] != value:
            self.model.poke('parts')
            self.model.parts[0] = value

    @property
    def right(self):
        """ This is the right child -- to be used only if syntactic theory can make such distinction locally in
        constituent itself. Another option is to do the ordering as a result of derivation, and then you will
        probably need to call some UG -ordering method.
        :return: BaseConstituent instance or None
        """
        if self.model.parts and len(self.model.parts) > 1:
            return self.model.parts[1]
        else:
            return None

    @right.setter
    def right(self, value):
        """ This is the right child -- to be used only if syntactic theory can make such distinction locally in
        constituent itself. Another option is to do the ordering as a result of derivation, and then you will
        probably need to call some UG -ordering method.
        :param value: BaseConstituent instance or None
        """
        if self.model.parts:
            if len(self.model.parts) > 1:
                if self.model.parts[1] == value:
                    return
                self.model.poke('parts')
                self.model.parts[1] = value
            else:
                self.model.poke('parts')
                self.model.parts.append(value)
        else:
            self.model.poke('parts')
            self.model.parts = [None, value]

    @property
    def parts(self):
        """ Parts are the constituents of the constituent (its children). In some syntactic theories they may be
        ordered, in others they are unordered set, and they may be strictly binary, or the amount of constituent may
         be undecided. They are anyways implemented as ordered list with no limits on length. It is up to UG to treat
          them as binary tree or empty.
        :return: list of constituents
        """
        return self.model.parts

    @parts.setter
    def parts(self, value):
        """ Parts are the constituents of the constituent (its children). In some syntactic theories they may be
        ordered, in others they are unordered set, and they may be strictly binary, or the amount of constituent may
         be undecided. They are anyways implemented as ordered list with no limits on length. It is up to UG to treat
          them as binary tree or empty.
        :param value: list of constituents
        :return: None
        """
        if self.model.touch('parts', value):
            self.model.parts = value

    @property
    def gloss(self):
        """ Gloss text is the translation for this constituent, just a syntactically inert string. Wonder what it
        does here?
        :return: str or ITextNode
        """
        return self.model.gloss

    @gloss.setter
    def gloss(self, value):
        """ Gloss text is the translation for this constituent, just a syntactically inert string. Wonder what it
        does here?
        :param value: str or ITextNode
        """
        if value is None:
            value = ''
        if self.model.touch('gloss', value):
            self.model.gloss = value

    @property
    def index(self):
        """ Index is the small letter to indicate which constituents are the same or have some kind of historical
        connection (e.g. X and trace of X would have the same index)
        :return: str
        """
        return self.model.index

    @index.setter
    def index(self, value):
        """ Index is the small letter to indicate which constituents are the same or have some kind of historical
        connection (e.g. X and trace of X would have the same index)
        :param value: str
        """
        if value is None:
            value = ''
        if self.model.touch('index', value):
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

    def __contains__(self, c):
        if self == c:
            return True
        if self.left:
            if self.left.__contains__(c):
                return True
        if self.right:
            if self.right.__contains__(c):
                return True
        else:
            return False

    def print_tree(self):
        """ Bracket tree representation of the constituent structure. Now it is same as str(self).
        :return: str
        """
        return self.__repr__()

    def get_feature(self, key):
        """ Gets the local feature (within this constituent, not of its children) with key 'key'
        :param key: string for identifying feature type
        :return: feature object
        """
        f = self.features.get(key, None)
        return f

    def has_feature(self, key):
        """ Check the existence of feature within this constituent
        :param key: string for identifying feature type or Feature instance
        :return: bool
        """
        if isinstance(key, Feature):
            return key in list(self.features.values())
        return key in list(self.features.keys())

    def set_feature(self, key, value, family=''):
        """ Set constituent to have a certain feature. If the value given is Feature instance, then it is used,
        otherwise a new Feature is created or existing one modified.
        :param key: str, the key for finding the feature
        :param value:
        :param family: string, optional. If new feature belongs to a certain feature family, e.g. phi features.
        """
        if isinstance(value, Feature):
            self.model.poke('features')
            self.features[key] = value
        else:
            f = self.features.get(key, None)
            if f:
                f.set(value)
            else:
                f = Feature(key, value)
                self.model.poke('features')
            self.features[key] = f

    def del_feature(self, key):
        """ Remove feature from a constituent. It's not satisfied, it is just gone.
        :param key: str, the key for finding the feature or for convenience, a feature instance to be removed
        """
        if isinstance(key, Feature):
            key = key.key
        if hasattr(self.features, key):
            self.model.poke('features')
            del self.features[key]

    def is_leaf(self):
        """ Check if the constituent is leaf constituent (no children) or inside a tree (has children).
        :return: bool
        """
        return not self.parts

    def copy(self):
        """ Make a deep copy of constituent. Useful for picking constituents from Lexicon.
        :return: BaseConstituent
        """
        new_parts = []
        for part in self.parts:
            new = part.copy()
            new_parts.append(new)
        nc = self.__class__(self.label)
        nc.sourcestring = self.sourcestring
        nc.alias = self.alias
        nc.gloss = self.gloss
        nc.index = self.index
        for key, value in self.features.items():
            nc.set_feature(key, value)
        nc.parts = new_parts
        return nc
