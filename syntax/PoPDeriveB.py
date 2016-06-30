#######################################################
###Derivation Generator - Problems of Projection Version
## Rewriting Jason Ginsburg's computer model for PoP,
# http://www.osaka-kyoiku.ac.jp/~jginsbur/MinimalistModeling.html
# Jukka Purma
#########################################################

import re
import string
import sys
import time

ALL_HEADS = {'v*', 'C', 'v', 'n', 'the', 'a', "D", "in"}
HEADS = {'v*', 'v', 'C', 'n', 'v~', "D", "D_Top", "in"}
DET_HEADS = {'the', 'a', "D"}
PHASE_HEADS = {"v*", "C", "C_Q", "that", "C_Null", "C_Top", "in"}
THETA_ASSIGNERS = {"v*", "vUnerg", 'v', 'v_be'}
SHARED_FEAT_LABELS = {"Phi", "Q", "Top", "Per"}
TENSE_ELEMS = {'PRES', 'PAST'}
PHI_FEATS = {"iPerson:", "iNumber:", "iGender:"}
OTHER_FTS = {'ThetaAgr', 'EF', 'MergeF', 'ExplMerge', 'NoProject'}
SHARED_LABELS = {"Phi", "Q", "Top"}
ADJUNCT_LABELS = {"P_in"}
NUM_PATTERN = r'[0-9]+'

COUNTED_FEATURES = {'uPerson', 'uNumber', 'uGender', 'Case:Nom', 'Case:Acc', 'Case:Dat', 'Root',
                    'uCase', 'uCase', 'iTop', 'uScp', 'iQ'}
COUNTED_PHI_FEATURES = {'iPerson:', 'iNumber:', 'iGender:'}

LEXICON = {
    'v*': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Acc'},
    'C': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Nom'},
    'P_in': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Dat'},
    'that': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'iC', 'Case:Nom'},
    'C_Q': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Nom', 'uQ', 'iScp', 'iC'},
    'C_Top': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Nom', 'uTop', 'iScp', 'iC'},
    'C_Null': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Nom', 'Delete', 'iC'},
    # LI name is "C"
    'v': {'MergeF', 'Head', 'iv'}, 'v_be': {'MergeF', 'iv', 'Root'},
    'vUnerg': {'MergeF', 'iv', 'Root'}, 'v~': {'MergeF', 'ThetaAgr'},
    'n_Top': {'iPerson:', 'iNumber:', 'iGender:', 'MergeF', 'uCase', 'iTheta', 'Head', 'iN', 'iD',
              'iTop', 'uScp'},
    'n': {'iPerson:', 'iNumber:', 'iGender:', 'MergeF', 'uCase', 'iTheta', 'Head', 'iN'},
    # +'iD' for Japanese
    'n_Expl': {'uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'iN'},  # LI name is "n"
    'there': {'MergeF', 'ThetaAgr'}, 'the': {'MergeF', 'Head', 'uPhi', 'iD'},
    'a': {'MergeF', 'Head', 'uPhi', 'iD'}, 'D': {'MergeF', 'Head', 'uPhi', 'iD'},
    'Q': {'MergeF', 'Head', 'uPhi', 'iQ', 'uScp'},
    'which': {'MergeF', 'Head', 'uPhi', 'iQ', 'uScp'}, 'root': {'MergeF', 'Root'},
}


class Stack:

    def __init__(self):
        self.main_stack = []
        self.sub_stack = []
        self.sub_stream = False
        self.ctr = 0

    def is_main(self):
        return not self.sub_stream

    def is_sub(self):
        return self.sub_stream

    def start_sub_stream(self):
        self.sub_stack = []
        self.sub_stream = True

    def end_sub_stream(self):
        self.sub_stream = False
        self.sub_stack = []

    def append(self, item, force_main=False):
        if force_main or not self.sub_stream:
            if item not in self.main_stack:
                self.main_stack.append(item)
        else:
            if item not in self.sub_stack:
                self.sub_stack.append(item)

    def cut_to(self, item):
        if self.sub_stream:
            self.sub_stack = self.sub_stack[self.sub_stack.index(item):]
        else:
            self.main_stack = self.main_stack[self.main_stack.index(item):]

    def replace(self, old_chunk, new_chunk, main_only=False):
        if main_only or not self.sub_stream:
            stack = self.main_stack
        else:
            stack = self.sub_stack
        new_list = []
        for item in stack:
            if isinstance(old_chunk, Constituent):
                if old_chunk == item:
                    item = new_chunk
                else:
                    item.recursive_replace_constituent(old_chunk, new_chunk)
            elif isinstance(old_chunk, FeatureSet):
                item.recursive_replace_feature_set(old_chunk, new_chunk)
            elif isinstance(old_chunk, (str, Feature)):
                item.recursive_replace_feature(old_chunk, new_chunk)
            new_list.append(item)
        if main_only or not self.sub_stream:
            self.main_stack = new_list
        else:
            self.sub_stack = new_list

    def __contains__(self, item):
        if self.sub_stream:
            return item in self.main_stack
        else:
            return item in self.sub_stack

    def __iter__(self):
        self.ctr = 0
        return self

    def __next__(self):
        self.ctr += 1
        if self.sub_stream:
            if self.ctr >= len(self.sub_stack):
                raise StopIteration
            else:
                return self.sub_stack[self.ctr]
        else:
            if self.ctr >= len(self.main_stack):
                raise StopIteration
            else:
                return self.main_stack[self.ctr]

    def __len__(self):
        if self.sub_stream:
            return len(self.sub_stack)
        else:
            return len(self.main_stack)

    def __getitem__(self, item):
        if self.sub_stream:
            return self.sub_stack[item]
        else:
            return self.main_stack[item]


class FeatureSet(set):

    def contains(self, other):
        """ Alternative for hash-based containment """
        for item in self:
            if other == item:
                return True

    def has_part(self, *fparts):
        """ Find 
        :param fparts: 
        :return: 
        """
        for fpart in fparts:
            found = False
            for f in self:
                if fpart in f:
                    found = True
                    break
            if not found:
                return False
        return True

    def get_by_part(self, fpart):
        for f in self:
            if fpart in f:
                return f

    def copy(self):
        return FeatureSet(set.copy(self))

    def __repr__(self):
        #return 'FS'+repr(sorted(self))
        return repr(sorted(self))


class Constituent:  # collections.UserList):

    def __init__(self, label='', part1=None, part2=None, features=None):
        self.label = label
        self.part1 = part1
        self.part2 = part2
        self.features = FeatureSet()
        if features:
            for f in features:
                if isinstance(f, str):
                    self.features.add(Feature(f))
                elif isinstance(f, Feature):
                    self.features.add(f)

    def __repr__(self):
        parts = [self.label]
        if self.part1:
            parts.append(self.part1)
        if self.part2:
            parts.append(self.part2)
        if self.features:
            parts.append(self.features)
        return repr(parts)

    def __eq__(self, other):
        if not isinstance(other, Constituent):
            return False
        elif self.label != other.label:
            return False
        elif self.part1 != other.part1:
            return False
        elif self.part2 != other.part2:
            return False
        elif self.features != other.features:
            return False
        else:
            return True

    def __hash__(self):
        return hash(repr(self))

    def labelstring(self):
        if self.part1 and self.part2:
            return '[%s %s %s]' % (self.label, self.part1.labelstring(), self.part2.labelstring())
        else:
            return self.label

    def is_leaf(self):
        return not (self.part1 and self.part2)

    def get_head(self):
        if self.part1 and self.part1.label == self.label:
            return self.part1.get_head()
        elif self.part2 and self.part2.label == self.label:
            return self.part2.get_head()
        else:
            return self

    def shared_features(self, other):
        my_feats = self.get_head_features()
        other_feats = other.get_head_features()
        return FeatureSet(my_feats & other_feats)

    def add_feature(self, feat):
        if not isinstance(feat, Feature):
            feat = Feature(feat)
        self.features.add(feat)

    def remove_feature(self, feat):
        self.features.remove(feat)

    def replace_feature(self, old, new):
        if old in self.features:
            self.features.remove(old)
            self.features.add(new)

    def replace_feature_by_name(self, old_name, new):
        found = None
        for item in self.features:
            if item.name == old_name:
                found = item
                break
        if found is not None:
            self.features.remove(found)
            self.features.add(new)
        else:
            print('couldnt find ', old_name, self)

    def is_unlabeled(self):
        return self.label == '_'

    def is_labeled(self):
        return self.label != '_'

    def copy(self):
        if self.part1 and self.part2:
            return Constituent(label=self.label, part1=self.part1.copy(), part2=self.part2.copy())
        elif self.features:
            return Constituent(label=self.label, features=FeatureSet(self.features))
        else:
            raise TypeError

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

    def get_head_features(self):
        # if self.language == "Japanese":
        #    return self.get_head_features_head_final(merged)
        if self.is_leaf():
            return self.features
        if self.is_unlabeled():
            return self.part1.recursive_get_features()
        elif self.part2.is_unlabeled():
            f = self.part1.recursive_get_features()
            if f:
                return f
        return self.recursive_get_features()

    def recursive_get_features(self):
        if self.is_leaf():
            return self.features
        head = self.label
        if self.part1.label == head:
            return self.part1.get_head_features()
        if self.part2.label == head:
            return self.part2.get_head_features()
        if head in SHARED_FEAT_LABELS:
            elem1_feats = self.part1.get_head_features()
            elem2_feats = self.part2.get_head_features()
            shared_feats = FeatureSet(elem1_feats & elem2_feats)
            if shared_feats:
                return shared_feats
        if "Phi" in head:
            head_features = self.part1.get_head_features()
            return head_features
        assert False

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
        elif isinstance(old_chunk, FeatureSet):
            self.recursive_replace_feature_set(old_chunk, new_chunk)
        elif isinstance(old_chunk, Feature):
            self.recursive_replace_feature(old_chunk, new_chunk)
        else:
            raise TypeError

    def recursive_replace_label(self, old_label, new_label):
        if self.part1:
            self.part1.recursive_replace_label(old_label, new_label)
        if self.part2:
            self.part2.recursive_replace_label(old_label, new_label)
        if self.label == old_label:
            self.label = new_label

    def recursive_replace_feature_set(self, old, new):
        for item in new:
            if not isinstance(item, Feature):
                print(new)
                raise TypeError
        if self.part1:
            self.part1.recursive_replace_feature_set(old, new)
        if self.part2:
            self.part2.recursive_replace_feature_set(old, new)
        if old == self.features:
            self.features = new

    def recursive_replace_feature(self, old, new):
        if new and not isinstance(new, Feature):
            print(new)
            raise TypeError
        if self.part1:
            self.part1.recursive_replace_feature(old, new)
        if self.part2:
            self.part2.recursive_replace_feature(old, new)
        if old in self.features:
            self.features.remove(old)
            if new:
                self.features.add(new)

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


class Feature:
    def __init__(self, namestring='', counter=0, name='', value='', unvalued=False,
                 ifeature=False):
        if namestring:
            if namestring.startswith('u'):
                namestring = namestring[1:]
                self.unvalued = True
                self.ifeature = False
            elif namestring.startswith('i'):
                namestring = namestring[1:]
                self.unvalued = False
                self.ifeature = True
            else:
                self.unvalued = False
                self.ifeature = False
            digits = ''
            digit_count = 0
            for char in reversed(namestring):
                if char.isdigit():
                    digits = char + digits
                    digit_count += 1
                else:
                    break
            if digit_count:
                self.counter = int(digits)
                namestring = namestring[:-digit_count]
            else:
                self.counter = 0
            self.name, part, self.value = namestring.partition(':')
        else:
            self.name = name
            self.counter = counter
            self.value = value
            self.unvalued = unvalued
            self.ifeature = ifeature

    def __repr__(self):
        parts = []
        if self.ifeature:
            parts.append('i')
        elif self.unvalued:
            parts.append('u')
        parts.append(self.name)
        if self.value:
            parts.append(':' + self.value)
        if self.counter:
            parts.append(str(self.counter))
        #return "'"+''.join(parts)+"'"
        return ''.join(parts)


    def __eq__(self, o):
        if isinstance(o, Feature):
            return self.counter == o.counter and self.name == o.name and \
                   self.value == o.value and self.unvalued == o.unvalued and \
                   self.ifeature == o.ifeature
        elif isinstance(o, str):
            return str(self) == o
        else:
            return False

    def __lt__(self, other):
        return repr(self) < repr(other)

    def __gt__(self, other):
        return repr(self) > repr(other)

    def __hash__(self):
        return hash(str(self))

    def __contains__(self, item):
        if isinstance(item, Feature):
            if item.name != self.name:
                return False
            if item.ifeature and not self.ifeature:
                return False
            if item.value and self.value != item.value:
                return False
            if item.unvalued and not self.unvalued:
                return False
            return True
        else:
            return item in str(self)

    def copy(self):
        return Feature(counter=self.counter, name=self.name, value=self.value,
                       unvalued=self.unvalued, ifeature=self.ifeature)


class Generate:
    def __init__(self, inputlines):

        start = 1  # 1
        finish = 10  # 11
        self.output = []  # List of all (important) steps in the derivation
        self.phi_counter = 0
        self.feature_counter = 0
        self.stack = None
        self.merge_counter = 0
        self.inheritance_counter = 0
        self.transfer_counter = 0
        self.feature_check_counter = 0
        self.lookforward_so = None
        self.language = ""
        self.over_counter = 0
        self.dumpfile = None

        for line in inputlines:
            if "Japanese" in line:
                self.language = "Japanese"
            elif "English" in line:
                self.language = "English"
            sentence, lbracket, target_str = line.partition('[')
            if not (sentence and lbracket and target_str):
                continue
            sentence = sentence.strip()
            sentence_number = sentence[0]

            if sentence_number.isdigit():
                sentence = sentence[2:]  # remove number and the space after it
                sentence_number = int(sentence_number)
                if sentence_number >= finish:
                    break
                elif sentence_number < start:
                    continue
                target_example = eval(lbracket + target_str)
                self.out(sentence_number, sentence, target_example)
                self.generate_derivation(target_example)
                self.out("MRGOperations", self.merge_counter)
                self.out("FTInheritanceOp", self.inheritance_counter)
                self.out("FTCheckOp", self.feature_check_counter)

    def out(self, first, second, third=None):
        if third is None:
            self.output.append((str(first), str(second)))
        else:
            self.output.append((str(first), str(second), str(third)))

    def dump_to_file(self, data, i):
        if not self.dumpfile:
            self.dumpfile = open('test_dataC.log', 'w')
        self.dumpfile.write('---------- %s ----------\n' % i)
        self.dumpfile.write(str(data))
        self.dumpfile.write('\n')

    def generate_derivation(self, target_example):
        """

        :param target_example:
        :return:
        """
        def merge_so(my_so, spine):
            if isinstance(my_so, list):
                return self.merge_substream(my_so, spine)
            else:
                return self.merge_so(my_so, spine)

        self.stack = Stack()
        self.phi_counter = 0
        self.feature_counter = 0
        self.merge_counter = 0
        self.inheritance_counter = 0
        self.transfer_counter = 0
        self.feature_check_counter = 0
        self.lookforward_so = None
        so = None
        selected = None
        while target_example:
            self.lookforward_so = target_example.pop()
            if so:
                selected = merge_so(so, selected)
            so = self.lookforward_so
        self.lookforward_so = None
        selected = merge_so(so, selected)
        if selected.is_unlabeled():
            self.label_if_necessary(selected)
            self.out("Crash(Unlabeled)", selected)
            sys.exit()

        self.out("Transfer", selected)

    def merge_substream(self, synobjlist, spine):
        """ Switch into substream (phrase within sentence) and build that before
        merging the whole thing into main spine.
        :param synobjlist: list of lexicon keys
        :param spine: main structure of merged objects
        :return: spine
        """
        print('merge_substream')
        print('>>>>>  starting substream')
        self.stack.start_sub_stream()
        self.out("SubStream", True)
        substream_spine = None
        while synobjlist:
            substream_spine = self.merge_so(synobjlist.pop(), substream_spine)
        self.stack.end_sub_stream()
        print('<<<<<  ended substream')
        # merge substream back to main stream:
        self.out("MainStream", True)
        self.out("merge", "merge " + spine.label + " + " + substream_spine.label)
        return self.merge(spine, substream_spine)

    def merge_so(self, synobj, spine):
        """ Select new item and merge it into structure
        :param synobj: lexicon key for synobj
        :param spine: main structure of merged objects
        :return: spine
        """
        print('merge_so')
        if not spine:
            return self.get_lexem(synobj)
        else:
            x = self.get_lexem(synobj)
            self.out("merge", "merge " + x.label + " + " + spine.label)
            spine = self.merge(x, spine)
            print('finished merge: ', spine)
            #self.dump_to_file(spine, self.over_counter)
            print('----------------- ', self.over_counter)
            self.over_counter += 1
            return spine

    def merge(self, x, y):
        """ Merge two objects and trigger all the complications...
        :param x: so
        :param y: so
        :return: merged
        """
        print('merge')
        external_merge = "MergeF" in x.get_head_features()
        # push to stack if unlabeled or if it has uFs
        self.stack.append(x)
        self.stack.append(y)
        x, y, feats_passed, remerge = self.check_features(x, y)

        label_giver = None
        other = None
        label_info = None
        x_feats = x.get_head_features()
        y_feats = y.get_head_features()
        # Determine label
        # Head-feature gives immediately label, once
        print('determine_label')
        if "Head" in x_feats and "Head" not in y_feats:
            new_x_feats = FeatureSet({f for f in x_feats if f != "Head"})
            label_giver = self.replace_features(x, x_feats, new_x_feats)
            other = y
            label_info = "Head"
        elif y.label in ADJUNCT_LABELS:
            # Assume that label is X
            label_giver = x
            other = y

        if label_giver:
            # Head merge
            self.merge_counter += 1
            if self.language == "Japanese":
                merged = Constituent(label=label_giver.label, part1=other, part2=label_giver)
            else:
                merged = Constituent(label=label_giver.label, part1=label_giver, part2=other)
                # !!! Unlabeled move !
                merged = self.unlabeled_move(merged)
                if feats_passed:
                    if label_info == "Head":
                        self.out("Label(Head)", merged)

            if remerge:
                # check_features of RemergedElement??
                # Find Shared Feats
                merged = self.remerge_back(merged, remerge)
        else:
            # Check if adjunct
            self.merge_counter += 1
            # ordering doesn't matter, but this makes things easier
            x_is_head = None
            if "v" in x.label:
                if self.language == "Japanese":
                    if y.label.startswith("n"):
                        x_is_head = False
                elif y.label.startswith("D"):
                    x_is_head = False
                elif y.label.startswith("Q"):
                    x_is_head = False
            elif "C" in x.label:
                if self.language == "Japanese":
                    x_is_head = True
                else:
                    x_is_head = False
            elif "P_in" in x.label:
                x_is_head = False
            if x_is_head is None:
                if external_merge:
                    if self.language == "Japanese":
                        x_is_head = False
                    else:
                        x_is_head = True
                else:
                    if self.language == "Japanese":
                        x_is_head = True
                    else:
                        x_is_head = False
            if x_is_head:
                merged = Constituent(label="_", part1=x, part2=y)
            else:
                merged = Constituent(label="_", part1=y, part2=x)

            self.out("Label(None)", str(merged))
            # If unlabled - then remerge next available element with phi-features
            merged = self.unlabeled_move(merged)
                # See if there are any uFs in x_feats
        # if merged.is_labeled():
        #     merged_feats = merged.get_head_features()
        #     unvalued_features = []
        #     for f in merged_feats:
        #         if f.unvalued and f.name != "Case" and f.name != "Scp":
        #             goal = Feature(name=f.name, value=f.value, unvalued=False, ifeature=True)
        #             unvalued_features.append(goal)
        #
        #     if unvalued_features:
        #         found = False
        #         # Search stack for element with a matching goal
        #         if self.stack.is_sub():
        #             self.out("Crash(Unchecked Feature)", str(merged))
        #             sys.exit()
        #         # It looks like Model10 never reaches inside this:
        #         # for current in reversed(self.stack):
        #         #     if current.is_labeled():
        #         #         current_feats = current.get_head_features()
        #         #         for f in current_feats:
        #         #             for goal in unvalued_features:
        #         #                 if goal in f:
        #         #                     found = True
        #         #                     merge_data = "merge (Feature Check) %s + %s" % \
        #         #                                  (merged.label, current.label)
        #         #                     self.out("Merge", merge_data)
        #         #                     # though there are many possible triggers (arriving
        #         #                     # at indeterminate order) they all create the same
        #         #                     # merge
        #         #                     merged = self.merge(merged, current)
        #         #                     break
        #         #             if found:
        #         #                 break
        #         #         if found:
        #         #             break
        #         if not found:
        #             self.out("Crash(Unchecked Feature)", str(merged))
        #             sys.exit()
        if merged.label in PHASE_HEADS:
            merged = self.transfer_check(merged)
        return merged

    def remerge_back(self, merged, remerge):
        print('remerge_back')
        shared_feats = merged.shared_features(remerge)
        if shared_feats.has_part("iQ"):
            label = "Q"
        elif shared_feats.has_part("iTop"):
            label = "Top"
        else:
            print("SharedFeats", shared_feats)
            print("Merged", merged)
            print("Remerge", remerge)
            print("Can't Determine Label 5555")
            sys.exit()
        remerge_feats = remerge.get_head_features()
        new_remerge_feats = FeatureSet(remerge_feats)
        new_remerge_feats.add(Feature(name="Copy"))

        if self.stack.is_sub():
            print("Remerging in in substream999999")
            sys.exit()
        merged.replace_within(remerge_feats, new_remerge_feats)
        self.stack.replace(remerge_feats, new_remerge_feats)
        self.out("merge", "merge (for labeling) " + merged.label + " + " + remerge.label)
        merged = Constituent(label=label, part1=remerge, part2=merged)
        self.merge_counter += 1
        self.out("Label(SharedFeats)", str(merged))
        merged = self.label_if_necessary(merged)
        return merged

    def transfer_check(self, merged):
        """
        Transfer
        a) The complement of a phase head is transferred.
        b) A derivation is transferred when all operations are completed
        :param merged:
        :return: merged
        """
        print('transfer_check')
        # ##### Dephase because T inherits phasehood ##### #
        if self.stack.is_main() and merged.label == "v*" and self.language != "Japanese":
            success = self.dephase_and_transfer(merged)
            if success:
                return success

        if merged.label in PHASE_HEADS:  # This is last resort
            merged_feats = merged.get_head_features()
            transfer = None

            if "Delete" in merged_feats:  # Dephase because C is deleted
                transfer = self.dephase_deleted_c(merged)
                remerge = None
                if self.stack.is_main():
                    merged, remerge = self.remerge_if_can(merged, dephase=True)
                self.out("Transfer", transfer)  # Transfer actually does nothing.
                print('******** Transfer ********')
                self.stack.main_stack = []
                if remerge:
                    self.stack.append(remerge, force_main=True)
                if self.stack.is_sub():
                    self.stack.append(merged, force_main=True)
                return merged

            # check Stack if unvalued igned features are present
            remerge = None
            if self.stack.is_main():
                merged, remerge = self.remerge_if_can(merged)

            # Transfer a complement of a phase head
            if merged.is_unlabeled() or "Phi" in merged.label:
                target_label = merged.part2.label
            else:
                target_label = merged.label
            prev = None
            for next_item in reversed(self.stack):
                # Find next element in stack that lacks this label
                if next_item.label != target_label and prev and prev.label == target_label:
                    transfer = next_item
                    break
                prev = next_item
            self.out("Transfer", transfer)  # Transfer actually does nothing.
            print('******** Transfer ********')
            self.stack.main_stack = []
            if remerge:
                self.stack.append(remerge, force_main=True)
        if self.stack.is_sub():
            self.stack.append(merged, force_main=True)
        return merged

    def dephase_and_transfer(self, merged):
        """Dephasing
        a) A verbal root remerges with the local v* (when present) and phasehood
         is transferred to the verbal root.
        :param merged:
        :return: merged
        """
        print('dephase_and_transfer')
        # Find closest Root
        for current in reversed(self.stack):
            if any(x.name == "Root" for x in current.get_head_features()):
                # Transfer the complement of v
                if current.is_unlabeled():
                    raise hell
                remerge = current.copy()
                transfer = remerge.part2
                self.stack.cut_to(current)
                # Dephasing takes the head of the merged structure
                new_label = remerge.label + "+" + merged.label
                if merged.part1.label == merged.label:
                    target = merged.part1.copy()
                    target.label = new_label
                    merged = Constituent(label=new_label, part1=target, part2=merged.part2)
                else:
                    merged = merged.copy()
                    merged.label = new_label
                self.out("Dephase v", merged)
                self.out("Transfer", transfer)
                # Check to see if Remerge results in labeling
                if self.stack.is_sub():
                    self.stack.append(merged, force_main=True)
                else:
                    for current in reversed(self.stack):
                        if remerge == current.part1 and current.is_unlabeled():
                            print("Relabel", current)
                            sys.exit()
                return merged

    def dephase_deleted_c(self, merged):
        """ Dephase
            b) Deletion of C transfers phasehood to T.
        """
        print('dephase_deleted_c')
        transfer = None
        merged_feats = merged.get_head_features()
        spec = merged.part1
        spec_feats = spec.get_head_features()
        if spec_feats != merged_feats and "Delete" not in spec_feats:
            merged = Constituent(label=merged.label, part1=spec, part2=merged.part2.part2)
            # Core Head needs to be deleted
        else:
            merged = merged.part2
        self.out("Dephase(DeleteC)", merged)
        target_label = merged.label
        # Transfer phasehood to T and transfer complement
        if merged.is_unlabeled() or "Phi" in target_label:
            target_label = merged.part2.label
        prev = None
        for next_item in reversed(self.stack):
            # Find next element in stack that lacks this label
            if next_item.label != target_label and prev and prev.label == target_label:
                transfer = next_item
                break
            prev = next_item
        return transfer

    def remerge_if_can(self, merged, dephase=False):
        print('remerge_if_can')
        outer = reversed(self.stack.main_stack)
        inner = reversed(self.stack.main_stack)

        for current in outer:
            if current.label != merged.label and "Phi" not in current.label:
                current_feats = current.get_head_features()
                if any([x.unvalued for x in current_feats]):
                    # if Current is already Merged to element that shares features with
                    # phase head, then Remerge isn't possible
                    # Find complement of Current
                    # See if complement shares features with phase head
                    for inner_current in inner:
                        complement = None
                        if current == inner_current.part1:
                            complement = inner_current.part2
                        elif current == inner_current.part2:
                            complement = inner_current.part1
                        if complement:
                            shared_feats = merged.shared_features(complement)
                            if shared_feats:
                                if not dephase:
                                    self.out("merge", """
            Remerge of %s blocked by Remerge Condition (shared features)
            """ % current.label)
                            else:
                                remerge = current.copy()
                                merged = Constituent(label="_", part1=remerge, part2=merged)
                                remerge_feats = remerge.get_head_features()
                                new_remerge_feats = remerge_feats.copy()
                                new_remerge_feats.add(Feature(name="Copy"))
                                remerge.replace_within(remerge_feats, new_remerge_feats)
                                self.out("merge",
                                         "merge (due to uF) %s + %s" % (remerge.label,
                                                                        merged.label))
                                self.out("Label(Head)", merged)
                                return merged, remerge
                            return merged, None
        return merged, None

    def unlabeled_move(self, merged):
        print('unlabeled_move')

        # I don't like this next move, looking forward to decide on current cycle:
        if self.lookforward_so:
            if merged.part1.label in THETA_ASSIGNERS:  # External merge blocks internal merge
                if isinstance(self.lookforward_so, list):  # not yet turned to constituent
                    first = self.lookforward_so[0]
                    if first in DET_HEADS or first == "n_Expl":
                        return merged
        if self.stack.is_main():
            self.stack.append(merged)
        # Move an element within an unlabeled Merged Structure

        # find element in stack with phi-features and raise if possible
        remerge = None
        if merged.is_unlabeled():
            head = merged.part1
            head_feats = head.get_head_features()
            if self.language == "English":
                if head_feats.has_part("iD", "iPerson"):
                    # There's already a DP with phi-features here, so no need to merge
                    # another DP with Phi
                    return merged
                elif head_feats.has_part("iQ", "iPerson"):
                    # There's already a DP with phi-features here, so no need to merge
                    # another DP with Phi
                    return merged
            ###Try looking into complement
            comp = merged.part2
            if comp.is_unlabeled():
                locus = comp.part1
                locus_features = locus.get_head_features()
                if locus_features.has_part("iN", "uPerson") or \
                        locus_features.has_part("iQ", "iPerson") or \
                        locus_features.has_part("iD", "iPerson"):
                    remerge = locus
            elif "Phi" in comp.label:
                locus = comp.part1
                locus_features = locus.get_head_features()
            else:
                locus = comp
                locus_features = locus.get_head_features()
                if locus_features.has_part("iN"):
                    remerge = locus
            if not remerge:
                if locus_features.has_part("iD", "iPerson") or \
                        locus_features.has_part("iQ", "iPerson"):
                    remerge = locus
        if remerge:
            merged = self.remerge(merged, remerge)
        else:
            merged = self.label_if_necessary(merged)
        return merged

    def remerge(self, merged, remerge):
        print('remerge (attempting to remerge)')
        if self.stack.is_sub():
            print("Do in substream999999")
            sys.exit()
        new_remerge = remerge.copy()
        remerge_feats = remerge.get_head_features()
        new_remerge_feats = remerge_feats.copy()
        new_remerge_feats.add(Feature(name="Copy"))
        new_remerge.replace_within(remerge_feats, new_remerge_feats)
        merged.replace_within(remerge, new_remerge)  # brr, brrrr, brrrr
        self.stack.replace(remerge, new_remerge)
        self.out("merge", "merge (for labeling) " + remerge.label + " + " + merged.label)
        if merged.part1.label == "vUnerg":
            sys.exit()

        merged = self.label_if_necessary(merged)
        # Find new MergedLabel
        new_merged = Constituent(label=merged.label, part1=remerge, part2=merged)
        self.stack.append(remerge)
        self.stack.append(new_merged)
        new_merged = self.label_if_necessary(new_merged)
        if new_merged.is_unlabeled():
            self.out("Label(None)", new_merged)
        else:
            self.out("Label(SharedFeats)", new_merged)
            print("Label via shared FEatures2", new_merged)
            print("\n")
        # this only changes label for current and its copies. current is the immediate parent
        # of remerged item. fixme: make it shorter when the problems are gone
        ctr = len(self.stack)
        while ctr:
            ctr -= 1
            current = self.stack[ctr]
            #for current in reversed(self.stack):
            if remerge != current and remerge in current:
                current_feats = current.get_head_features()
                if not current_feats.has_part("Root"):
                    if current.part1 == remerge:
                        new_label = current.part2.label
                    elif current.part2 == remerge:
                        new_label = current.part1.label
                    else:
                        new_label = current.label
                    new_current = Constituent(label=new_label, part1=current.part1,
                                              part2=current.part2)
                    if current != new_merged:
                        new_merged.replace_within(current, new_current)
                    self.stack.replace(current, new_current)  # verify if needed
                    break
        self.stack.append(new_merged)
        return new_merged

    def label_if_necessary(self, merged, can_return_false=False):
        """

        :param merged:
        :return:
        """
        print('label_if_necessary')
        labeled = False
        if not self.stack:
            return False
        ctr = 0
        while ctr < len(self.stack):
            current = self.stack[ctr]
            if current.is_unlabeled():
                new_label = self.labeling_function(current.part1, current.part2)
                if new_label is not False:

                    new_merged = Constituent(label=new_label, part1=current.part1, part2=current.part2)
                    if current == merged:
                        merged = new_merged
                    elif current in merged:
                        merged.replace_within(current, new_merged)
                    else:
                        print("Error: there is an unlabeled stack item that is not found in merged")
                        print("main_stack: ", self.stack.is_main())
                        print('-------------------------------------')
                        print("Merged:", merged)
                        print('-------------------------------------')
                        print("Current:", current)
                        print('-------------------------------------')
                        print(merged == current)
                        print("New Merged:", new_merged)
                        #for i, item in enumerate(self.stack):
                        #    print(i, item)
                        print("Current:", current.labelstring())
                        assert(False)
                        #sys.exit()

                    if self.stack.is_main():
                        self.stack.replace(current, new_merged)  # verify
                    labeled = True
                    #assert(not merged.is_unlabeled())
            ctr += 1
        if merged.is_unlabeled():
            assert not self.labeling_function(merged.part1, merged.part2)
        if can_return_false and not labeled:
            return False
        else:
            return merged

    def labeling_function(self, x, y):
        """ Compute label for SO that merges x, y
        :param x: Constituent
        :param y: Constituent
        :return: label string or False
        """
        print('labeling_function')
        # print('merged on labeling_function: ', merged)
        # for i, item in enumerate(self.stack):
        #    print('stack item %s on labeling_function: %s' % (i, item))
        # print('sub stream stack on labeling_function: ', self.sub_stream_stack)

        if x.is_unlabeled():
            elem1_feats = x.part1.get_head_features()
        else:
            elem1_feats = x.get_head_features()
        if y.is_unlabeled():
            elem2_feats = y.part1.get_head_features()
        else:
            elem2_feats = y.get_head_features()
        if not (elem1_feats and elem2_feats):
            print('1: no elem1 and elem2 features')
            return False
        if x.is_unlabeled() and y.is_unlabeled():
            print('2: both are unlabeled')
            return False
        if elem1_feats.has_part("Root"):  # weak
            if elem1_feats.has_part("iPerson", "iNumber", "iGender"):
                if self.language == "Japanese":
                    new_label = y.label
                else:
                    new_label = x.label
                self.out("Label(Strengthened)", new_label)
                print('3: iPerson, iNumber or iGender')
                return new_label
            elif elem1_feats.has_part("iPerson"):
                print("elem1 has only iPerson of phi")
                print("Merged", x, y)
                sys.exit()
        if "Copy" in elem1_feats:
            if "Copy" not in elem2_feats:
                if elem2_feats.has_part("Root") or elem1_feats.has_part("Root"):  # weak
                    if elem2_feats.has_part("iPerson", "iNumber", "iGender"):
                        self.out("Label(Move)", y.label)
                        print('5: elem1 is Copy, either is Root and elem 2 has phi-features')
                        # print(new_merged)
                        return y.label
                else:
                    self.out("Label(Move)", y.label)
                    print('6: elem1 is Copy, 2 is not, neither is Root')
                    return y.label
        elif "Copy" in elem2_feats:
            # weak if Root
            if elem1_feats.has_part("Root", "iPerson", "iNumber", "iGender"):
                self.out("Label(Move)", x.label)
                print('7: elem2 is Copy, elem1 is Root and phi')
                return x.label
        shared_feats = FeatureSet(elem1_feats & elem2_feats)
        if not shared_feats:
            # Check for strengthened element
            print('8: no shared feats (return False)')
            return False
        person_f = shared_feats.get_by_part("iPerson")
        if person_f:
            if shared_feats.has_part("iNumber", "iGender"):
                if self.language == "Japanese":
                    self.out("Label(Strengthened)", y.label)
                    print('9a: shares phi-features, japanese')
                    return y.label
                else:
                    new_label = "Phi%s" % person_f.counter or ''
                    self.out("Label(SharedFeats)", new_label)
                    print('9b: shares phi-features (strengthen)', new_label)
                    return new_label
            else:
                self.out("Label(SharedFeats)", "Per")
                print('10: shares iPerson, make a "Per"-constituent')
                return "Per"
        print('11: nothing matched')
        return False

    # def get_head_features_head_final(self, merged):
    #     """ I'm not putting much effort to fix this, it should be refactored anyways,
    # one method for
    #      both head final and head first languages
    #     :param merged:
    #     :return:
    #     !fixme: later
    #     """
    #
    #     def get_head(mrged):
    #         # this will find the head of a Merged syntactic object. The head is a string,
    #         # and shouldn't have any brackets
    #         for i, li in enumerate(mrged):
    #             if not isinstance(li, list):
    #                 if i != 0:
    #                     print('not first: ', i, mrged)
    #                 return li
    #         print("Error: No Head found")
    #         sys.exit()
    #
    #     if "kiPerson" in str(merged):
    #         print("error")
    #         print("Merged", merged)
    #         sys.exit()
    #
    #     if merged.features:
    #         return merged.features
    #     if merged.is_unlabeled():
    #         head = get_head(merged.part2)
    #     else:
    #         head = get_head(merged)
    #     ctr = len(merged) - 1
    #     cont = True
    #     while cont:
    #         current = merged[ctr]
    #         current_head = current[0]
    #         if current_head == head:
    #             head_feats = self.get_head_features_head_final(current)
    #             return head_feats
    #         if len(current) == 2:
    #             if type(current[-1]) == list:
    #                 head_feats = current[-1]
    #                 return head_feats
    #         else:
    #             list_pres = False
    #             for f in current:
    #                 if type(f) == list:
    #                     list_pres = True
    #             if not list_pres:
    #                 head_feats = current
    #                 return current
    #         ctr -= 1
    #         if ctr < 0:
    #             print("Error")
    #             print("Can't find head feats")
    #             sys.exit()

    def get_lexem(self, synobj):
        """

        :param synobj:
        :return:
        """
        print('get_lexem')
        # "MergeF" is a feature that is deleted upon Merged
        # used to keep track of whether or not an element has undergone first MErge
        # can distinguish an X (simple) from an XP (complex)

        # put elements with uFs right onto the stack
        features0 = list(LEXICON.get(synobj, LEXICON['root']))
        if any((f in COUNTED_FEATURES for f in features0)):
            self.feature_counter += 1
        if any((f in COUNTED_PHI_FEATURES for f in features0)):
            self.phi_counter += 1
        features = FeatureSet()
        for feat in features0:
            if feat in COUNTED_FEATURES:
                features.add(feat + str(self.feature_counter))
            elif feat in COUNTED_PHI_FEATURES:
                features.add(feat + str(self.phi_counter))
            else:
                features.add(feat)
        if synobj == 'C_Null':
            synobj = 'C'
        elif synobj == 'n_Expl':
            synobj = 'n'
        return Constituent(label=synobj, features=features)

    def get_head_features(self, x, y):
        """

        :param x:
        :param y:
        :return:
        """
        if x.is_unlabeled():
            x_feats = x.part1.get_head_features()
        else:
            x_feats = x.get_head_features()
        if y.is_unlabeled():
            y_feats = y.part1.get_head_features()
        elif y.label in SHARED_LABELS:
            if y.is_leaf():
                y_feats = y.get_head_features()
            else:
                y_feats = y.part1.get_head_features()
        elif y.part2 and y.part2.is_unlabeled():
            print("problem")
            print("Y", y)
            sys.exit()
        else:
            y_feats = y.get_head_features()
        return x_feats, y_feats

    def check_features(self, x, y):
        print('check_features')
        # If X has uPhi, then uPhi are passed down the tree until they are checked
        x_feats, y_feats = self.get_head_features(x, y)

        # Which is head?
        current_label = ''
        x_head = "Head" in x_feats
        y_head = "Head" in y_feats
        if x_head and y_head:
            print("Both are heads:", x_feats, y_feats)
            print("Figure out label")
            print("%%%%")
            sys.exit()
        elif x_head:
            current_label = x.label
        elif y_head:
            current_label = y.label
        if current_label:
            if self.language == "Japanese":
                self.out("Label(Head)", "label= %s part1= %s part2= %s" % (current_label, y, x))
            else:
                self.out("Label(Head)", "label= %s part1= %s part2= %s" % (current_label, x, y))
        inherit = False
        unvalued_phis = FeatureSet()
        for f in x_feats:
            if f.name in ["Person", "Number", "Gender"] and f.unvalued:
                unvalued_phis.add(f)
            elif f.name == "Case" and not f.unvalued:
                unvalued_phis.add(f)
        if len(unvalued_phis) >= 3 or x.label in PHASE_HEADS:
            inherit = x
        if not inherit:
            for f in y_feats:
                if f.name in ["Person", "Number", "Gender"] and f.unvalued:
                    unvalued_phis.add(f)
                elif f.name == "Case" and not f.unvalued:
                    unvalued_phis.add(f)
            if len(unvalued_phis) >= 3:
                inherit = y
        if not inherit:
            x, y, remerge = self.feature_checking_function(x, y)
            return x, y, False, remerge

        # pass feats down the tree
        passed_items = set()
        feats_passed = False
        prev_label = False  # block feature passage to nominal
        if self.stack.is_main():
            temp_stack = list(self.stack.main_stack)
        else:
            temp_stack = list(self.stack.sub_stack)
        while temp_stack:
            current = temp_stack.pop()
            if current == x:
                continue
            elif prev_label == "n" or current in passed_items:
                prev_label = current.label
                continue
            prev_label = current.label
            current_feats = current.get_head_features()
            if current_feats.has_part("Root"):
                go_on = True
                for item in ["uPerson", "iPerson", "iD", "iN"]:
                    if current_feats.has_part(item):
                        go_on = False
                        break
                if go_on:
                    passed_items.add(current)
                    if current.is_labeled():
                        other_label = current.label
                    else:
                        if current.part1.is_labeled():
                            if self.language == "Japanese":
                                other_label = current.part2.label
                            else:
                                other_label = current.part1.label
                        elif current.part2.is_labeled():
                            if self.language == "Japanese":
                                other_label = current.part1.label
                            else:
                                other_label = current.part2.label
                        else:
                            print("error - can't find label9999")
                            sys.exit()
                    new_feats = FeatureSet(current_feats | unvalued_phis)
                    new_current = self.replace_features(current, current_feats, new_feats)
                    self.out("PassFs", "Pass Features " + inherit.label + " to " + other_label)
                    self.out("FeaturesPassed", unvalued_phis)
                    self.inheritance_counter += 1
                    y.replace_within(current, new_current)
                    feats_passed = True
        x, y, remerge = self.feature_checking_function(x, y)
        y = self.label_if_necessary(y)
        return x, y, feats_passed, remerge

    def replace_features(self, elem, old_feats, new_feats):
        """

        :param elem:
        :param old_feats:
        :param new_feats:
        :return:
        """
        print('replace_features', old_feats, new_feats)
        elem.replace_within(old_feats, new_feats)
        self.stack.replace(old_feats, new_feats)
        return elem

    def feature_checking_function(self, x, y):
        """

        :param x:
        :param y:
        :return:
        """

        def make_checking_pairs(unvalued_features, probe_feats):
            unvalued = FeatureSet({x for x in probe_feats if x.unvalued})
            chkd = []
            for unvalued_feature in unvalued:
                for u_goal in unvalued_features.copy():
                    if u_goal.name == unvalued_feature.name and u_goal.ifeature:
                        chkd.append((unvalued_feature, u_goal))
            return chkd

        print('feature_checking_function')
        if self.stack.is_main() and not self.stack:
            print('quick escape! ', type(x), type(y))
            return x, y, None
        x_feats, y_feats = self.get_head_features(x, y)
        checked_feats = FeatureSet()
        # XFeats probe
        if "MergeF" in x_feats:
            new_x_feats = FeatureSet({f for f in x_feats if f.name != "MergeF"})
            x = self.replace_features(x, x_feats, new_x_feats)
            x_feats = new_x_feats
        unvalued_phi = bool(x_feats.has_part("uPerson", "uNumber", "uGender"))
        unvalued_features = FeatureSet({f for f in x_feats if f.unvalued or
                (f.name == "Case" and unvalued_phi) or
                (f.name == "Scp" and f.ifeature)})
        if not unvalued_features:
            return x, y, None
        ###########################
        temp_stack = list(self.stack)
        remerge = None
        new_x_feats = FeatureSet()
        unvalued_feature_stack = sorted(unvalued_features.copy())
        while unvalued_feature_stack:
            uf = unvalued_feature_stack.pop()
            temp_stack = list(self.stack)
            while temp_stack:
                stack_top = temp_stack.pop()
                if stack_top == x:
                    stack_top = temp_stack.pop()
                feat_checked = False
                goal = Feature(name=uf.name, ifeature=True, value=uf.value)
                if "Phi" in stack_top.label:
                    # Don't look at the features of an element with shared phi-features
                    # This is maybe an imperfection
                    top_feats = FeatureSet()
                else:
                    top_feats = stack_top.get_head_features()
                if top_feats is None:
                    sys.exit()
                uf_present = False
                # This can match only two unvalued, but uf:s can also be iScp:s or Cases
                if uf.unvalued:
                    utop_feats = FeatureSet({feat for feat in top_feats if feat.unvalued})
                    for top_feat in utop_feats:
                        uf_present = True
                        if top_feat != uf and top_feat.name == uf.name: # both are unvalued
                            print('unification possible: %s -> %s' % (top_feat, uf))
                            top_feats.remove(top_feat)
                            top_feats.add(uf)
                            self.stack.replace(top_feat, uf)
                            stack_top.replace_within(top_feat, uf)
                            x.replace_within(top_feat, uf)
                            y.replace_within(top_feat, uf)
                            self.out("Unification", uf)
                if uf.name == "Q" or uf.name == "Top":
                    uf_present = True  # it doesn't matter if a potential goal has any uFs
                    # uFs aren't needed to be visible.
                if top_feats.has_part(goal):
                    labeled = stack_top.is_labeled()
                    if uf_present:
                        if not labeled:
                            pass
                        elif goal.name == "Top" and goal.ifeature:
                            top_chkd = make_checking_pairs(unvalued_features, top_feats)
                            for old_top_f, new_top_f in top_chkd:
                                stack_top.replace_within(old_top_f, new_top_f)
                                label = stack_top.part1.label
                                new_label = label + "-wa"
                                stack_top.replace_within(label, new_label, label=True)
                                # fixme: does label replacing work like this?
                                print('attempting to replace label in many constituents')
                                x.replace_within(old_top_f, new_top_f)
                                y.replace_within(old_top_f, new_top_f)
                                if old_top_f not in checked_feats:
                                    checked_feats.add(old_top_f)
                                if self.stack.is_sub():
                                    print("Check in substream999999")
                                    sys.exit()
                                self.stack.replace(old_top_f, new_top_f)

                            remerge = stack_top.copy()
                            # Add Copy to any copy in derivation
                            # REmove Copy from remerged version
                            remerge_feats = remerge.get_head_features()
                            if "Copy" in remerge_feats:
                                # RemoveCopy
                                copyless_features = FeatureSet({x for x in remerge_feats if x != "Copy"})
                                remerge.replace_within(remerge_feats, copyless_features)
                                # print(self.remerge)
                        elif "iQ" in goal:
                            top_chkd = make_checking_pairs(unvalued_features, top_feats)
                            for old_top_f, new_top_f in top_chkd:
                                stack_top.replace_within(old_top_f, new_top_f)
                                x.replace_within(old_top_f, new_top_f)
                                y.replace_within(old_top_f, new_top_f)
                                if old_top_f not in checked_feats:
                                    checked_feats.add(old_top_f)
                                if self.stack.is_sub():
                                    print("Check in substream999999")
                                    sys.exit()
                                self.stack.replace(old_top_f, new_top_f)

                            remerge = stack_top
                            # Add Copy to any copy in derivation
                            # REmove Copy from remerged version
                            remerge_feats = remerge.get_head_features()
                            if "Copy" in remerge_feats:
                                # RemoveCopy
                                copyless_features = FeatureSet({x for x in remerge_feats if x.name != "Copy"})
                                remerge.replace_within(remerge_feats, copyless_features)
                                print("self.Remerge111", remerge)
                                print("\n")
                                # Find highest instance in derivation and add "Copy"

                        # Remerge due to a need to share Q features
                        if labeled:
                            #print('goal in top feats, raise feature from top_f to uf')
                            for top_f in top_feats:
                                if goal in top_f:
                                    x.replace_within(uf, top_f)
                                    y.replace_within(uf, top_f)
                                    self.stack.replace(uf, top_f)
                            feat_checked = True
                            checked_feats.add(uf)
                            # Check uScp as a reflex of uQ checking
                elif uf.name == "Case" and uf.value:
                    checked_feats.add(uf)

                    x.replace_within(uf, None)
                    y.replace_within(uf, None)
                    self.stack.replace(uf, None, main_only=True)
                    #for i, item in enumerate(self.stack):
                    #    print(i, item)
                    #    print('')
                    #raise hell
                    if self.language == "Japanese":  # head final issue
                        pass  # uncomment and fix code below
                    #     if "uCase" in str(y):
                    #         y_str = str(y)
                    #         start = y_str.find("uCase")
                    #         temp_y_cont = True
                    #         end = start + 1
                    #         while temp_y_cont:
                    #             current_y = y_str[end]
                    #             if current_y == "'":
                    #                 temp_y_cont = False
                    #             end += 1
                    #         y_feat = y_str[start:end - 1]
                    #         y.replace_within(y_feat, f)
                    #         if not self.sub_stream:
                    #             self.replace(y_feat, f)
                    else:  # not Japanese (not head final)
                        for y_feat in y_feats:
                            if y_feat.name == "Case" and y_feat.unvalued:
                                y.replace_within(y_feat, uf)
                                self.stack.replace(y_feat, uf)
                    feat_checked = True
                elif uf.name == "Phi":
                    if top_feats.has_part("iPerson"):
                        new_x_feats = FeatureSet({x for x in x_feats if not (x.unvalued and x.name == "Phi")})
                        for top_f in top_feats:
                            if any({x in top_f for x in ["iPerson", "iNumber", "iGender", "uCase"]}):
                                new_x_feats.add(top_f)
                    x = self.replace_features(x, x_feats, new_x_feats)
                    x_feats = new_x_feats
                    self.out("PhiPassing", "uPhi")
                    feat_checked = True
                    self.inheritance_counter += 1
                if feat_checked:
                    break

        if checked_feats:
            self.out("CheckedFeatures", checked_feats)
            self.feature_check_counter += len(checked_feats)
        print('---check features func ends ---')
        return x, y, remerge



def start(input_data):
    f = open(input_data, 'r')
    input_data = f.readlines()
    f.close()
    t = time.time()
    print('*****')
    print('*****')
    print('*****')
    print('*MOD*')
    print('*****')
    print('*****')
    print('*****')
    print('*****')
    a = Generate(input_data)
    # ProduceOutput.ProduceFile(a.output, 'new/')
    print(time.time() - t)


# "../Languages/Japanese/DisWarn.txt"

start("./POP.txt")
