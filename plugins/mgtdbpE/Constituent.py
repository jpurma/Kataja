try:
    from syntax.BaseConstituent import BaseConstituent
    from syntax.BaseFeature import BaseFeature as Feature
    from kataja.SavedField import SavedField
    in_kataja = True
except ImportError:
    from Feature import Feature
    BaseConstituent = object
    in_kataja = False


class Constituent(BaseConstituent):
    """ The main difference between mgtdbp Constituents and Kataja's BaseConstituents is that
    features are stored as lists instead of dicts. See footnote 1, p.3 in Stabler 2012, 'Two models
    of minimalist, incremental syntactic analysis'. The order of features is important in parsing
    (though Constituents are actually used only for displaying results, not in parsing itself)
    and -- more importantly -- one Constituent can have two counts for the same feature,
    e.g. =D =D. and we have to be able to present such constituents. """
    replaces = "ConfigurableConstituent"

    def __init__(self, label='', features=None, parts=None, index_str=None):
        if in_kataja:
            if features is not None:
                features = list(features)
            else:
                features = []
            if parts:
                super().__init__(label=label, parts=parts, features=features)
            else:
                super().__init__(label=label, features=features)

        self.label = label or []
        self.features = features or []
        self.parts = parts or []
        self.index_str = index_str
        self.touched = True  # flag to help remove nodes that don't belong to current parse

    def __repr__(self):
        return '[%r:%r, %r]' % (self.label, self.features, self.parts)

    @staticmethod
    def build_from_dnodes(dnode, dnodes, terminals, dtrees, all_features=False):
        key = dnode.path
        c = dtrees.get(key, Constituent(index_str=key))
        if terminals and terminals[0].path == key:
            leaf = terminals.pop(0)
            c.label = ' '.join(leaf.label)
            c.features = list(reversed(leaf.features))
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
            if len(parts) > 1:
                c.label = '*'
            elif len(parts) == 1:
                c.label = 'o'
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

    ### Reimplement feature handling interface from BaseConstituent, it has dict, we have list.

    def get_feature(self, key):
        """ Gets the local feature (within this constituent, not of its children) with key 'key'
        :param key: string for identifying feature type
        :return: feature object
        """
        for f in self.features:
            if f.name == key:
                return f

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
            self.poke('features')
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
                self.poke('features')
                self.features.append(value)
        else:
            self.poke('features')
            new_f = Feature(value=value, name=key)
            self.features.append(new_f)

    def remove_feature(self, name):
        """ Remove feature from a constituent. It's not satisfied, it is just gone.
        :param fname: str, the name for finding the feature or for convenience, a feature
        instance to be removed
        """
        if isinstance(name, Feature):
            if name in self.features:
                self.poke('features')
                self.features.remove(name)
        else:
            for f in list(self.features):
                if f.name == name:
                    self.poke('features')
                    self.features.remove(f)

    def __hash__(self):
        return hash(self.index_str)
