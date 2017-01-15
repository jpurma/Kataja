
try:
    from PoP2.Lexicon import SHARED_FEAT_LABELS
    from PoP2.FeatureB import Feature
    from syntax.BaseConstituent import BaseConstituent as MyBaseClass
    from kataja.SavedField import SavedField
    in_kataja = True
except ImportError:
    # noinspection PyUnresolvedReferences,PyPackageRequirements
    from Lexicon import SHARED_FEAT_LABELS
    # noinspection PyUnresolvedReferences,PyPackageRequirements
    from FeatureB import Feature
    MyBaseClass = object
    in_kataja = False


def expanded_features(feat_list):
    alist = []
    for feat in feat_list:
        alist += feat.expand_linked_features()
    return alist


def find_shared_features(my_feats, other_feats):
    my_feats = expanded_features(my_feats)
    other_feats = expanded_features(other_feats)
    return [mf for mf in my_feats if mf in other_feats]


class Constituent(MyBaseClass):  # collections.UserList):

    role = "Constituent"

    def __init__(self, label='', part1=None, part2=None, features=None):
        if in_kataja:
            if features is not None:
                features = list(features)
            else:
                features = []
            if part1 and part2:
                super().__init__(label=label, parts=[part1, part2], features=features)
            else:
                super().__init__(label=label, features=features)
        self.label = label
        self.part1 = part1
        self.part2 = part2
        self.features = []
        self.stacked = False
        self.transfered = False
        if features:
            for f in features:
                if isinstance(f, str):
                    self.features.append(Feature(f))
                elif isinstance(f, Feature):
                    self.features.append(f) #.copy())

    def __repr__(self):
        parts = [self.label]
        if self.part1:
            parts.append(self.part1)
        if self.part2:
            parts.append(self.part2)
        if self.features:
            parts.append(sorted(list(self.features)))
        return repr(parts)

    def featureless_str(self):
        """ Used to replicate Model10 output
        :return:
        """
        if self.part1 and self.part2:
            return '[%s %s %s]' % (self.label, self.part1.featureless_str(), self.part2.featureless_str())
        else:
            return '[%s ]' % self.label

    def model10_string(self):
        parts = [self.label]
        if self.part1:
            parts.append(self.part1.model10_string())
        if self.part2:
            parts.append(self.part2.model10_string())
        if self.features:
            fs = []
            for item in list(expanded_features(self.features)):
                fs.append(repr(item))
            parts.append(fs)
        return parts

    def __str__(self):
        """ Override BaseConstituent's __str__
        :return:
        """
        return repr(self)

    def __hash__(self):
        return id(self)

    def labelstring(self):
        if self.part1 and self.part2:
            return '[%s %s %s]' % (self.label, self.part1.labelstring(), self.part2.labelstring())
        else:
            return self.label

    def is_leaf(self):
        return not (self.part1 and self.part2)

    def shared_features(self, other):
        my_feats = self.get_head_features()
        other_feats = other.get_head_features()
        return find_shared_features(my_feats, other_feats)

    def add_feature(self, feat):
        self.poke('features')
        if not isinstance(feat, Feature):
            feat = Feature(feat)
        self.features.append(feat)

    def remove_feature(self, feat):
        self.poke('features')
        self.features.remove(feat)

    def replace_feature(self, old, new):
        if old in self.features:
            self.poke('features')
            self.features.remove(old)
            self.features.append(new)

    def has_feature(self, key):
        """ Check the existence of feature within this constituent
        :param key: string for identifying feature type or Feature instance
        :return: bool
        """
        if isinstance(key, Feature):
            return key in self.features
        return key in self.features

    def replace_feature_by_name(self, old_name, new):
        found = None
        for item in self.features:
            if item.name == old_name:
                found = item
                break
        if found is not None:
            self.features.remove(found)
            self.features.append(new)
        else:
            print('couldnt find ', old_name, self)

    def ordered_parts(self):
        if self.part1 and self.part2:
            return [self.part1, self.part2]
        elif self.part1:
            return [self.part1]
        elif self.part2:
            return [self.part2]
        else:
            return []

    def ordered_features(self):
        return list(self.features)

    def is_unlabeled(self):
        return self.label == '_'

    def is_labeled(self):
        return self.label != '_'

    def copy(self):
        if self.part1 and self.part2:
            return Constituent(label=self.label, part1=self.part1.copy(), part2=self.part2.copy())
        elif self.features:
            return Constituent(label=self.label, features=self.features)
        else:
            raise TypeError

    def demote_to_copy(self):
        """ Turn this into a SO with "Copy" feature and return a new fresh version without the
        copy-feature.
        :return:
        """
        feature_giver = self.get_feature_giver()
        copy_feature = Feature("Copy")
        if copy_feature in feature_giver.features:
            feature_giver.features.remove(copy_feature)
        fresh = self.copy()
        feature_giver.features.append(copy_feature)
        return fresh

    def __contains__(self, item):
        if isinstance(item, Constituent):
            if self.part1 == item:
                return True
            elif self.part2 == item:
                return True
            if self.part1:
                if item in self.part1:
                    return True
            if self.part2:
                if item in self.part2:
                    return True
        elif isinstance(item, Feature):
            return item in self.features
        return False

    def tex_tree(self, stack):
        stacked = ''
        if self.stacked:
            stacked = '(S?)'
            for i, item in enumerate(reversed(stack)):
                if item is self:
                    stacked = '(S%s)' % i
                    break
        label = self.label.replace('_', '-')
        if self.part1 and self.part2:
            return '[.%s%s %s %s ]' % (label, stacked, self.part1.tex_tree(stack),
                                       self.part2.tex_tree(stack))
        else:
            return label + stacked

    def get_head(self, no_sharing=True):
        if self.is_leaf():
            return self
        if self.is_unlabeled():
            return self.part1.get_head()
        elif self.part2.is_unlabeled():
            f = self.part1.get_head()
            if f:
                return f
        if self.part1.label == self.label:
            return self.part1.get_head()
        elif self.part2.label == self.label:
            return self.part2.get_head()
        elif self.label in SHARED_FEAT_LABELS:
            if no_sharing:
                return self.part1.get_head(no_sharing=True)
            else:
                head1 = self.part1.get_head()
                head2 = self.part2.get_head()
                result = []
                if isinstance(head1, list):
                    result += head1
                else:
                    result.append(head1)
                if isinstance(head2, list):
                    result += head2
                else:
                    result.append(head2)
                return result
        if "Phi" in self.label:
            return self.part1.get_head()
        assert False

    def get_head_features(self, no_sharing=False, expanded=False):
        if no_sharing:
            head = self.get_head(no_sharing=True)
            if expanded:
                return expanded_features(head.features)
            else:
                return head.features
        else:
            head = self.get_head(no_sharing=False)
            if isinstance(head, list):
                shared_feats = find_shared_features(head[0].features, head[1].features)
                if shared_feats:
                    feats_list = shared_feats
                else:
                    head = self.get_head(no_sharing=True)
                    feats_list = head.features
            else:
                feats_list = head.features
            if expanded:
                return expanded_features(feats_list)
            else:
                return feats_list

    def get_feature_giver(self):
        return self.get_head(no_sharing=True)

    def replace_within(self, old_chunk, new_chunk, label=False):
        if self == old_chunk:
            self.label = new_chunk.label
            self.features = new_chunk.features
            self.part1 = new_chunk.part1
            self.part2 = new_chunk.part2
            return
        if label:
            self.recursive_replace_label(old_chunk, new_chunk)
        elif isinstance(old_chunk, Constituent):
            self.recursive_replace_constituent(old_chunk, new_chunk)
        elif isinstance(old_chunk, list):
            found = self.recursive_replace_feature_set(old_chunk, new_chunk)
        elif isinstance(old_chunk, Feature):
            found = self.recursive_replace_feature(old_chunk, new_chunk)
        else:
            raise TypeError

    def recursive_replace_label(self, old_label, new_label):
        if self.part1:
            self.part1.recursive_replace_label(old_label, new_label)
        if self.part2:
            self.part2.recursive_replace_label(old_label, new_label)
        if self.label == old_label:
            self.label = new_label

    def recursive_replace_feature_set(self, old, new, found=0):
        # print(type(old),old, type(new), new)
        for item in new:
            if not isinstance(item, Feature):
                print(new)
                raise TypeError
        if self.part1:
            found = self.part1.recursive_replace_feature_set(old, new, found)
        if self.part2:
            found = self.part2.recursive_replace_feature_set(old, new, found)
        if old == self.features:
            self.features = list(new)
            found += 1
        return found

    def recursive_replace_feature(self, old, new, found=0):
        if new and not isinstance(new, Feature):
            print(new)
            raise TypeError
        if self.part1:
            found = self.part1.recursive_replace_feature(old, new, found)
        if self.part2:
            found = self.part2.recursive_replace_feature(old, new, found)
        if old in self.features:
            found += 1
            self.features.remove(old)
            if new:
                self.features.append(new)
        return found

    def recursive_replace_constituent(self, old, new):
        assert(self != old)
        if self.part1:
            if self.part1 == old:
                self.part1 = new
            else:
                self.part1.recursive_replace_constituent(old, new)
        if self.part2:
            if self.part2 == old:
                self.part2 = new
            else:
                self.part2.recursive_replace_constituent(old, new)

    if in_kataja:
        part1 = SavedField("part1")
        part2 = SavedField("part2")
