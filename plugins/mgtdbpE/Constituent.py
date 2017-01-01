try:
    from syntax.BaseConstituent import BaseConstituent
    from syntax.BaseFeature import BaseFeature as Feature
    from kataja.SavedField import SavedField
    in_kataja = True
except ImportError:
    from Feature import Feature
    in_kataja = False

class PlainConstituent:
    def __init__(self, label='', parts=None, uid='', features=None, head=None, **kw):
        """ BaseConstituent is a default constituent used in syntax.
        It is Savable, which means that the actual values are stored in separate object that is easily dumped to file.
        Extending this needs to take account if new elements should also be treated as savable, e.g. put them into
        . and make necessary property and setter.
         """
        super().__init__(**kw)
        self.label = label
        if head:
            self.heads = [head]
        else:
            self.heads = []
        self.features = features or []
        self.parts = parts or []
        self.secondary_label = ''


    def __str__(self):
        return str(self.label)

    def __repr__(self):
        if self.is_leaf():
            return 'Constituent(id=%s)' % self.label
        else:
            return "[ %s ]" % (' '.join((x.__repr__() for x in self.parts)))

    def __contains__(self, c):
        if self == c:
            return True
        for part in self.parts:
            if c in part:
                return True
        else:
            return False

    def get_feature(self, key):
        """ Gets the first local feature (within this constituent, not of its children) with key
        'key'
        :param key: string for identifying feature type
        :return: feature object
        """
        for f in self.features:
            if f.name == key:
                return f

    def get_secondary_label(self):
        """ Visualisation can switch between showing labels and some other information in label
        space. If you want to support this, have "support_secondary_labels = True"
        in SyntaxConnection and provide something from this getter.
        :return:
        """
        #return self.frozen_features
        return self.secondary_label


    def has_feature(self, key):
        """ Check the existence of feature within this constituent
        :param key: string for identifying feature type or Feature instance
        :return: bool
        """
        if isinstance(key, Feature):
            return key in self.features
        else:
            return bool(self.get_feature(key))

    def add_feature(self, feature):
        """ Add an existing Feature object to this constituent.
        :param feature:
        :return:
        """
        if isinstance(feature, Feature):
            self.features.append(feature)
        else:
            raise TypeError


    def set_feature(self, key, value, family=''):
        """ Set constituent to have a certain feature. If the value given is Feature
        instance, then it is used,
        otherwise a new Feature is created or existing one modified.
        :param key: str, the key for finding the feature
        :param value:
        :param family: string, optional. If new feature belongs to a certain feature family,
        e.g. phi features.
        """
        if isinstance(value, Feature):
            if value not in self.features:
                self.features.append(value)
        else:
            new_f = Feature(value=value, name=key)
            self.features.append(new_f)

    def remove_feature(self, name):
        """ Remove feature from a constituent. It's not satisfied, it is just gone.
        :param fname: str, the name for finding the feature or for convenience, a feature
        instance to be removed
        """
        if isinstance(name, Feature):
            if name in self.features:
                self.features.remove(name)
        else:
            for f in list(self.features):
                if f.name == name:
                    self.features.remove(f)

    def is_leaf(self):
        """ Check if the constituent is leaf constituent (no children) or inside a trees (has children).
        :return: bool
        """
        return not self.parts

    def ordered_parts(self):
        """ Tries to do linearization between two elements according to theory being used.
        Easiest, default case is to just store the parts as a list and return the list in its original order.
        This is difficult to justify theoretically, though.
        :return: len 2 list of ordered nodes, or empty list if cannot be ordered.
        """
        ordering_method = 1
        if ordering_method == 1:
            return list(self.parts)

    def copy(self):
        """ Make a deep copy of constituent. Useful for picking constituents from Lexicon.
        :return: BaseConstituent
        """
        new_parts = []
        for part in self.parts:
            new = part.copy()
            new_parts.append(new)
        new_features = self.features.copy()
        nc = self.__class__(label=self.label,
                            parts=new_parts,
                            features=new_features,
                            heads=self.heads)
        return nc

if not in_kataja:
    BaseConstituent = PlainConstituent


class Constituent(BaseConstituent):
    """ The main difference between mgtdbp Constituents and Kataja's BaseConstituents is that
    features are stored as lists instead of dicts. See footnote 1, p.3 in Stabler 2012, 'Two models
    of minimalist, incremental syntactic analysis'. The order of features is important in parsing
    (though Constituents are actually used only for displaying results, not in parsing itself)
    and -- more importantly -- one Constituent can have two counts for the same feature,
    e.g. =D =D. and we have to be able to present such constituents. """
    role = "Constituent"

    def __init__(self, label='', features=None, parts=None, index_str=None):
        super().__init__(label=label, parts=parts, features=features)
        self.label = label or []
        self.features = features or []
        self.parts = parts or []
        self.index_str = index_str
        self.secondary_label = ''
        self.touched = True  # flag to help remove nodes that don't belong to current parse

    def __repr__(self):
        return '[%r:%r, %r]' % (self.label, self.features, self.parts)

    def get_secondary_label(self):
        """ Visualisation can switch between showing labels and some other information in label
        space. If you want to support this, have "support_secondary_labels = True"
        in SyntaxConnection and provide something from this getter.
        :return:
        """
        #return self.frozen_features
        return self.secondary_label

    @staticmethod
    def build_from_dnodes(dnode, dnodes, terminals, dtrees, all_features=False):
        key = dnode.path
        c = dtrees.get(key, Constituent(index_str=key))
        if terminals and terminals[0].path == key:
            leaf = terminals.pop(0)
            c.label = ' '.join(leaf.label)
            c.features = list(reversed(leaf.features))
            c.secondary_label = ' '.join([str(f) for f in c.features])
            if dnode.features and dnode.features != leaf.features:
                print('dnode has features: ', dnode.features)
                print('leaf has features: ', leaf.features)
            c.parts = []
        elif dnodes and dnodes[0].path.startswith(key):
            parts = []
            child_dnode = dnodes.pop(0)
            child = Constituent.build_from_dnodes(child_dnode, dnodes, terminals, dtrees,
                                                  all_features=all_features)
            parts.append(child)
            if dnodes and dnodes[0].path.startswith(key):
                child_dnode = dnodes.pop(0)
                child = Constituent.build_from_dnodes(child_dnode, dnodes, terminals, dtrees,
                                                      all_features=all_features)
                parts.append(child)

            if all_features:
                c.features = list(reversed(dnode.features))
            else:
                c.features = []
            c.secondary_label = ' '.join([str(f) for f in c.features])
            if len(parts) > 1:
                c.label = '•'
            elif len(parts) == 1:
                c.label = '◦'
            else:
                c.label = ''
            c.parts = parts
        c.touched = True
        dtrees[key] = c
        return c

    def as_list_tree(self):
        if len(self.parts) == 2:
            return [self.label, self.parts[0].as_list_tree(), self.parts[1].as_list_tree()]
        elif len(self.parts) == 1:
            return [self.label, self.parts[0].as_list_tree()]
        elif self.features:
            if self.label:
                label = [self.label]
            else:
                label = []
            return label, [str(f) for f in self.features]

    @staticmethod
    def dnodes_to_dtree(dnodes, all_features=False, dtrees=None):
        if dtrees is None:
            dtrees = {}
        nonterms = []
        terms = []
        for dn in dnodes:
            if dn.terminal:
                terms.append(dn)
            else:
                nonterms.append(dn)
        terms.sort()
        nonterms.sort()
        root = nonterms.pop(0)
        for item in dtrees.values():
            item.touched = False
        dtree = Constituent.build_from_dnodes(root, nonterms, terms, dtrees,
                                              all_features=all_features)

        for key, item in list(dtrees.items()):
            if not item.touched:
                del dtrees[key]
        #dtree = Constituent()
        #dtree.build_from_dnodes(root.path, nonterms, terms, dtrees, all_features=all_features)
        if terms or nonterms:
            print('dnodes_to_dtree error: unused derivation steps')
            print('terms=' + str(terms))
            print('nonterms=' + str(nonterms))
        return dtree

    def __hash__(self):
        return hash(self.index_str)

    secondary_label = SavedField("secondary_label")