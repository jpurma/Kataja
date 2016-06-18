#######################################################
###Derivation Generator - Problems of Projection Version
## Rewriting Jason Ginsburg's computer model for PoP,
# http://www.osaka-kyoiku.ac.jp/~jginsbur/MinimalistModeling.html
# Jukka Purma
#########################################################

import re, sys, ProduceOutput, time, copy, collections

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
    'v*': ['uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Acc'],
    'C': ['uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Nom'],
    'P_in': ['uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Dat'],
    'that': ['uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'iC', 'Case:Nom'],
    'C_Q': ['uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Nom', 'uQ', 'iScp', 'iC'],
    'C_Top': ['uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Nom', 'uTop', 'iScp', 'iC'],
    'C_Null': ['uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'Case:Nom', 'Delete', 'iC'],
    # LI name is "C"
    'v': ['MergeF', 'Head', 'iv'],
    'v_be': ['MergeF', 'iv', 'Root'],
    'vUnerg': ['MergeF', 'iv', 'Root'],
    'v~': ['MergeF', 'ThetaAgr'],
    'n_Top': ['iPerson:', 'iNumber:', 'iGender:', 'MergeF', 'uCase', 'iTheta', 'Head',
              'iN', 'iD', 'iTop', 'uScp'],
    'n': ['iPerson:', 'iNumber:', 'iGender:', 'MergeF', 'uCase', 'iTheta', 'Head', 'iN'],
    # +'iD' for Japanese
    'n_Expl': ['uPerson', 'uNumber', 'uGender', 'MergeF', 'Head', 'iN'],  # LI name is "n"
    'there': ['MergeF', 'ThetaAgr'],
    'the': ['MergeF', 'Head', 'uPhi', 'iD'],
    'a': ['MergeF', 'Head', 'uPhi', 'iD'],
    'D': ['MergeF', 'Head', 'uPhi', 'iD'],
    'Q': ['MergeF', 'Head', 'uPhi', 'iQ', 'uScp'],
    'which': ['MergeF', 'Head', 'uPhi', 'iQ', 'uScp'],
    'root': ['MergeF', 'Root'],
}


class Constituent(list): #collections.UserList):

    def __init__(self, data=None, label = '', part1 = None, part2 = None, features = None):
        super(Constituent, self).__init__(data or [])
        if data and (label or part1 or part2 or features):
            raise ValueError
        if label and part1 and part2:
            self.extend([label, part1, part2])
        elif label and features:
            self.extend([label, features])
        elif label:
            self.append(label)

    @property
    def features(self):
        if len(self) == 2:
            return self[1]

    @features.setter
    def features(self, value):
        self[1] = value

    @property
    def label(self):
        if len(self) > 0:
            return self[0]

    @label.setter
    def label(self, value):
        self[0] = value

    @property
    def part1(self):
        if len(self) == 3:
            return self[1]

    @part1.setter
    def part1(self, value):
        if len(self) == 1:
            self.append(value)
        else:
            self[1] = value

    @property
    def part2(self):
        if len(self) == 3:
            return self[2]

    @part2.setter
    def part2(self, value):
        if len(self) == 1:
            self.extend([None, value])
        elif len(self) == 2:
            self.append(value)
        else:
            self[2] = value

    def unlabeled(self):
        return self[0] == '_'

    def my__repr__(self):
        if self.part1 and self.part2:
            return str([self.label, [self.part1, self.part2]])
        elif self.features:
            return str([self.label, self.features])

class Feature:
    def __init__(self, name, counter=0):
        self.name = name
        self.counter = counter

    def __repr__(self):
        if self.counter:
            return self.name + str(self.counter)
        else:
            return self.name


class Generate:
    def __init__(self, inputlines):

        start = 1  # 1
        finish = 10  # 11
        self.output = []  # List of all (important) steps in the derivation
        self.sub_stream = False
        self.selected_main = None
        self.selected_sub_stream = None
        self.phi_counter = 0
        self.feature_counter = 0
        self.phase = False
        self.main_stack = []
        self.sub_stream_stack = []
        self.remerge = None
        self.crash = False
        self.merge_counter = 0
        self.inheritance_counter = 0
        self.transfer_counter = 0
        self.feature_check_counter = 0
        self.next_so = None
        self.language = ""

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
                sentence = sentence[2:] # remove number and the space after it
                sentence_number = int(sentence_number)
                if sentence_number >= finish:
                    break
                elif sentence_number < start:
                    continue
                target_example = eval(lbracket + target_str)
                self.out(sentence_number, sentence, target_example)
                self.generate_derivation(target_example)
                if self.crash:
                    output = self.label_check(self.selected_main)
                else:
                    self.out("Transfer", self.selected_main)
                self.out("MRGOperations", self.merge_counter)
                self.out("FTInheritanceOp", self.inheritance_counter)
                self.out("FTCheckOp", self.feature_check_counter)

    def out(self, first, second, third=None):
        if third is None:
            self.output.append((str(first), str(second)))
        else:
            self.output.append((str(first), str(second), str(third)))

    @property
    def stack(self):
        if self.sub_stream:
            return self.sub_stream_stack
        else:
            return self.main_stack

    @stack.setter
    def stack(self, value):
        if self.sub_stream:
            self.sub_stream_stack = value
        else:
            self.main_stack = value

    @property
    def selected(self):
        if self.sub_stream:
            return self.selected_sub_stream
        else:
            return self.selected_main

    @selected.setter
    def selected(self, value):
        if self.sub_stream:
            self.selected_sub_stream = value
        else:
            self.selected_main = value

    def find_partial_feature(self, fpart, featurelist):
        for feature in featurelist:
            if fpart in feature:
                return feature

    def generate_derivation(self, target_example):
        target_example.reverse()
        self.selected_main = None
        self.sub_stream = False
        self.selected_sub_stream = None
        self.phi_counter = 0
        self.feature_counter = 0
        self.phase = False
        self.main_stack = []
        self.sub_stream_stack = []
        self.remerge = None
        self.crash = False
        self.merge_counter = 0
        self.inheritance_counter = 0
        self.transfer_counter = 0
        self.feature_check_counter = 0
        self.next_so = None
        so = None
        print(target_example)
        for next_so in target_example:
            self.next_so = next_so
            if so:
                if isinstance(so, list):
                    so.reverse()
                    self.generate_merged_structure_from_list(so)
                else:
                    self.generate_merged_structure(so)
            so = next_so
        self.next_so = None
        if so:
            if isinstance(so, list):
                so.reverse()
                self.generate_merged_structure_from_list(so)
            else:
                self.generate_merged_structure(so)
        if self.selected.unlabeled():
            self.out("Crash(Unlabeled)", self.selected_main)
            self.crash = True

    def generate_merged_structure_from_list(self, synobjlist):
        self.sub_stream = True
        self.out("SubStream", True)
        for so in synobjlist:
            self.generate_merged_structure(so)
        self.sub_stream = False
        # merge substream back to main stream:
        self.out("MainStream", True)
        self.sub_stream_stack = []
        self.out("merge", "merge " + self.selected.label + " + " + self.selected_sub_stream.label)
        self.selected = self.merge(self.selected, self.selected_sub_stream)
        self.selected_sub_stream = None

    def generate_merged_structure(self, synobj):
        if not self.selected:
            self.selected = self.get_form(synobj)
        else:
            x = self.get_form(synobj)
            y = self.selected
            self.out("merge", "merge " + x.label + " + " + y.label)
            self.selected = self.merge(x, y)

    def determine_label(self, x, y):
        x_feats = self.get_head_features(x)
        y_feats = self.get_head_features(y)
        if "Head" in x_feats:
            if "Head" not in y_feats:
                new_x_feats = []
                for f in x_feats:
                    if f != "Head":
                        new_x_feats.append(f)
                label = self.replace_features(x, x_feats, new_x_feats)
                other = y
                return label, other, "Head"

        if y.label in ADJUNCT_LABELS:
            # Assume that label is X
            label = x
            other = y
            return label, other, False

        return False, False, False

    def merge(self, x, y):
        first_merge_x = False
        x_feats = self.get_head_features(x)

        if "MergeF" in x_feats:
            first_merge_x = True
        # push to stack if unlabeled or if it has uFs
        if x not in self.stack:
            self.stack.append(x)
        if y not in self.stack:
            self.stack.append(y)

        x, y, feats_passed = self.check_features(x, y)

        label, other, label_info = self.determine_label(x, y)
        if label:
            merged = Constituent(label=label[0])
            self.merge_counter += 1
            if self.language == "Japanese":
                merged.part1 = other
                merged.part2 = label
            else:
                merged.part1 = label
                merged.part2 = other
            if feats_passed:
                if label_info == "Head":
                    self.out("Label(Head)", merged)
            if self.language == "English":
                output = self.unlabeled_move(merged)
                if output:
                    merged = output
            if self.remerge:
                # check_features of RemergedElement??
                # Find Shared Feats
                shared_feats = []
                merged_feats = self.get_head_features(merged)
                remerge_feats = self.get_head_features(self.remerge)
                for f in merged_feats:
                    if f in remerge_feats:
                        shared_feats.append(f)
                if self.find_partial_feature("iQ", shared_feats):
                    label = "Q"
                elif self.find_partial_feature("iTop", shared_feats):
                    label = "Top"
                else:
                    print("SharedFeats", shared_feats)
                    print("Merged", merged)
                    print("Remerge", self.remerge)
                    print("Can't Determine Label 5555")
                    sys.exit()
                remerge_feats = self.get_head_features(self.remerge)
                new_remerge_feats = remerge_feats + ["Copy"]
                if self.sub_stream:
                    print("Remerging in in substream999999")
                    sys.exit()
                merged = self.replace_everywhere(merged, remerge_feats, new_remerge_feats)
                self.stack = self.replace_everywhere(self.stack, remerge_feats, new_remerge_feats)
                self.out("merge", "merge (for labeling) " + merged.label + " + " +
                         self.remerge.label)
                merged = Constituent(label=label, part1=self.remerge, part2=merged)
                self.merge_counter += 1
                self.out("Label(SharedFeats)", str(merged))
                output = self.label_check(merged)
                if output:
                    merged = output
                self.remerge = None
        else:
            # Check if adjunct
            merged = Constituent(label="_")
            self.merge_counter += 1
            # ordering doesn't matter, but this makes things easier
            complete = False
            if "v" in x.label:
                if self.language == "Japanese":
                    if y.label[0] == "n":
                        merged.part1 = y
                        merged.part2 = x
                        complete = True
                elif y.label[0] == "D":
                    print(y.label)
                    merged.part1 = y
                    merged.part2 = x
                    complete = True
                elif y.label[0] == "Q":
                    merged.part1 = y
                    merged.part2 = x
                    complete = True
            elif "C" in x.label:
                if self.language == "Japanese":
                    merged.part1 = x
                    merged.part2 = y
                else:
                    merged.part1 = y
                    merged.part2 = x
                complete = True
            elif "P_in" in x.label:
                merged.part1 = y
                merged.part2 = x
                complete = True
            if not complete:
                if first_merge_x:
                    if self.language == "Japanese":
                        merged.part1 = y
                        merged.part2 = x
                    else:
                        merged.part1 = x
                        merged.part2 = y
                else:
                    if self.language == "Japanese":
                        merged.part1 = x
                        merged.part2 = y
                    else:
                        merged.part1 = y
                        merged.part2 = x
            self.out("Label(None)", str(merged))
            # If unlabled - then remerge next available element with phi-features
            output = self.unlabeled_move(merged)
            if output:
                merged = output
                # SEe if there are any uFs in XFeats
        if not merged.unlabeled():
            merged_feats = self.get_head_features(merged)
            unvalued_features = []
            pattern = r'[^1-9]+'
            for f in merged_feats:
                if f[0] == "u":
                    if "uCase" not in f:
                        if "uScp" not in f:
                            m = re.findall(pattern, f)
                            goal = "i" + m[0][1:]
                            unvalued_features.append(goal)

            if unvalued_features:
                found = False
                # Search stack for element with a matching goal
                if not self.sub_stream:
                    for current in reversed(self.stack):
                        if not current.unlabeled():
                            current_feats = self.get_head_features(current)
                            for f in current_feats:
                                for goal in unvalued_features:
                                    if goal in f:
                                        found = True
                                        merge_data = "merge (Feature Check) " + merged[0] + " + " +\
                                                     current[0]
                                        self.out("Merge", merge_data)
                                        merged = self.merge(merged, current)
                        if found:
                            break
                    if not found:
                        self.out("Crash(Unchecked Feature)", str(merged))
                        self.crash = True
        if not self.crash:
            if merged[0] in PHASE_HEADS:
                transfer_output = self.transfer_check(merged)
                if transfer_output != merged:
                    merged = transfer_output
        if self.remerge:  # Bug in program?
            self.remerge = None
        return merged

    def transfer_check(self, merged):

        merged_label = merged[0]
        assert(len(merged)==3)
        assert(isinstance(merged[0], str))
        merged_feats = self.get_head_features(merged)
        #print('transfer check, merged= ', merged)
        #print('merged[0]= ', merged[0])

        if merged_label == "v*" and self.language != "Japanese" and not self.sub_stream:
            # Find closest Root
            remerge = None
            for current in reversed(self.stack):
                current_feats = self.get_head_features(current)
                if any(x.startswith("Root") for x in current_feats):
                    remerge = current
                    break
            if remerge:
                # TRansfer the complement of v
                transfer = remerge[2]
                self.stack = self.stack[self.stack.index(remerge):]
                # Dephasing takes the head of the merged structure
                new_label = remerge[0] + "+" + merged_label
                new_merged = Constituent([new_label])
                if merged[1][0] == merged_label:
                    Target = merged[1]
                    MergedFirst = Constituent([new_label] + Target[1:])
                    new_merged.append(MergedFirst)
                    new_merged.append(merged[2])
                else:
                    new_merged += merged[1:]
                merged = new_merged
                self.output.append(("Dephase v", str(merged)))
                self.output.append(("Transfer", str(transfer)))
                self.Transfered = False
                # Check to see if Remerge results in labeling
                if not self.sub_stream:
                    if self.stack:
                        stack_ctr = len(self.stack) - 1
                        cont = True
                        while cont:
                            current = self.stack[stack_ctr]
                            if remerge == current[1]:
                                if current.unlabeled():
                                    print("Relabel", current)
                                    sys.exit()
                            stack_ctr -= 1
                            if stack_ctr < 0:
                                cont = False
        if merged[0] in PHASE_HEADS:  # This is last resort
            Dephase = False
            if "Delete" in merged_feats:
                Spec = merged[1]
                SpecFeats = self.get_head_features(Spec)
                SpecPres = False
                if SpecFeats != merged_feats:
                    if "Delete" not in SpecFeats:
                        SpecPres = True
                        new_merged = Constituent([merged[0], merged[1]])
                        Core = merged[2]
                        CoreDeleteHead = Core[2]
                        # Core Head needs to be deleted
                        new_merged.append(CoreDeleteHead)
                if not SpecPres:
                    new_merged = merged[2]
                self.output.append(("Dephase(DeleteC)", str(new_merged)))
                merged = new_merged
                merged_feats = self.get_head_features(merged)
                Dephase = True
                target_label = merged.label
                # Transfer phasehood to T and transfer complement
                if merged.unlabeled() or "Phi" in target_label:
                    target_label = merged.part2.label
                if not self.sub_stream:
                    stack_ctr = len(self.main_stack) - 1
                    cont = True
                    while cont:
                        current = self.main_stack[stack_ctr]
                        if current.label == target_label:
                            # Find next element that lacks this label
                            next_item = self.main_stack[stack_ctr - 1]
                            if next_item.label != current.label:
                                transfer = next_item
                                cont = False
                        stack_ctr -= 1
                        if stack_ctr < 0:
                            cont = False
                            ##                Transfer = False #C is deleted so there is nothing
                            # to transfer
            remerge = False
            # checkStack
            cont = True
            Ctr = len(self.stack) - 1
            while cont:
                if not self.sub_stream:
                    current = self.stack[Ctr]
                    if current.label != merged.label and "Phi" not in current.label:
                        current_feats = self.get_head_features(current)
                        pattern = r'u[A-Z]+'
                        m = re.findall(pattern, str(current_feats))
                        if m:
                            # if Current is already Merged to element that shares features with
                            # phase head, then Remerge isn't possible
                            # Find complement of Current
                            # See if complement shares features with phase head
                            TempCont = True
                            StackCtrTemp = len(self.main_stack) - 1
                            while TempCont:
                                TempStackCurrent = self.main_stack[StackCtrTemp]
                                if current in TempStackCurrent:
                                    if current != TempStackCurrent:
                                        if current == TempStackCurrent[1]:
                                            Complement = TempStackCurrent[2]
                                        elif current == TempStackCurrent[2]:
                                            Complement = TempStackCurrent[1]
                                        ComplementFeats = self.get_head_features(Complement)
                                        SharedFeats = []
                                        for TempF in ComplementFeats:
                                            if TempF in merged_feats:
                                                SharedFeats.append(TempF)
                                        if SharedFeats:
                                            if not Dephase:
                                                Message = "Remerge of " + current[
                                                    0] + " blocked by Remerge Condition (shared " \
                                                         "features)"
                                                self.output.append(("merge", Message))
                                        else:
                                            remerge = current
                                        TempCont = False
                                StackCtrTemp -= 1
                                if StackCtrTemp < 0:
                                    TempCont = False
                            cont = False
                Ctr -= 1
                if Ctr < 0:
                    cont = False
                    # uF present
                if remerge:
                    new_merged = Constituent(["_", remerge])
                    RemergeFeats = self.get_head_features(remerge)
                    NewRemergeFeats = RemergeFeats + ["Copy"]
                    NewRemerge = self.replace_everywhere(remerge, RemergeFeats, NewRemergeFeats)
                    if not self.sub_stream:
                        merged = self.replace_everywhere(merged, remerge, NewRemerge)
                        self.main_stack = self.replace_everywhere(self.main_stack, remerge, NewRemerge)
                    else:
                        print("Do in substream999999")
                        sys.exit()
                    new_merged.append(merged)
                    merged = new_merged
                    MergeData = "merge (due to uF) " + remerge[0] + " + " + merged[0]
                    self.output.append(("merge", MergeData))
                    self.output.append(("Label(Head)", str(merged)))
            if not Dephase:
                target_label = merged[0]
                if target_label == "_":
                    target_label = merged[2][0]
                if "Phi" in target_label:
                    target_label = merged[2][0]
                cont = True
                stack_ctr = len(self.stack) - 1
                cont = True
                while cont:
                    current = self.stack[stack_ctr]
                    current_label = current[0]
                    if current_label == target_label:
                        # Find next element that lacks this label
                        next = self.stack[stack_ctr - 1]
                        if next[0] != current_label:
                            transfer = next
                            cont = False
                    stack_ctr -= 1
                    if stack_ctr < 0:
                        cont = False
            self.output.append(("Transfer", str(transfer)))
            self.main_stack = []
            if remerge:
                self.main_stack.append(remerge)
        if self.sub_stream:
            self.main_stack.append(merged)
        return merged

    def unlabeled_move(self, merged):

        # I don't like this next move, looking forward to decide on current cycle:
        if self.next_so:
            if merged.part1.label in THETA_ASSIGNERS:  # External merge blocks internal merge
                if isinstance(self.next_so, list):
                    first = self.next_so[0]
                    if first in DET_HEADS or first == "n_Expl":
                        return False
        if not self.sub_stream:
            if merged not in self.stack:
                self.stack.append(merged)
        # Move an element within an unlabeled Merged Structure

        # find element in stack with phi-features and raise if possible
        remerge = False
        if merged.unlabeled():
            merged_one = merged.part1
            merged_one_feats = self.get_head_features(merged_one)
            if self.language == "English":
                if self.find_partial_feature("iD", merged_one_feats):
                    if self.find_partial_feature("iPerson", merged_one_feats):
                        # There's already a DP with phi-features here, so no need to merge
                        # another DP with Phi
                        return False
                elif self.find_partial_feature("iQ", merged_one_feats):
                    if self.find_partial_feature("iPerson", merged_one_feats):
                        # There's already a DP with phi-features here, so no need to merge
                        # another DP with Phi
                        return False
            ###Try looking into complement
            comp = merged.part2
            if comp.unlabeled():
                comp_spec_feats = self.get_head_features(comp.part1)
                if self.find_partial_feature("iD", comp_spec_feats):
                    if self.find_partial_feature("iPerson", comp_spec_feats):
                        remerge = comp.part1
                elif self.find_partial_feature("iQ", comp_spec_feats):
                    if self.find_partial_feature("iPerson", comp_spec_feats):
                        remerge = comp.part1
                elif self.find_partial_feature("iN", comp_spec_feats):
                    if self.find_partial_feature("uPerson", comp_spec_feats):
                        remerge = comp.part1
            else:
                if "Phi" in comp.label:
                    comp_spec_feats = self.get_head_features(comp.part1)
                    if self.find_partial_feature("iD", comp_spec_feats):
                        if self.find_partial_feature("iPerson", comp_spec_feats):
                            remerge = comp.part1
                    elif self.find_partial_feature("iQ", comp_spec_feats):
                        if self.find_partial_feature("iPerson", comp_spec_feats):
                            remerge = comp.part1
                else:
                    comp_feats = self.get_head_features(comp)
                    if self.find_partial_feature("iN", comp_feats):
                        remerge = comp
                    if self.find_partial_feature("iD", comp_feats):
                        if self.find_partial_feature("iPerson", comp_feats):
                            remerge = comp
                    elif self.find_partial_feature("iQ", comp_feats):
                        if self.find_partial_feature("iPerson", comp_feats):
                            remerge = comp
        ReplaceTups = []
        LabeledViaMovement = []
        if not remerge:
            Output = self.label_check(merged)
            if Output:
                NewMerged = Output
                merged = NewMerged
                return merged
        elif remerge:
            RemergeFeats = self.get_head_features(remerge)
            NewRemergeFeats = RemergeFeats + ["Copy"]
            NewRemerge = self.replace_everywhere(remerge, RemergeFeats, NewRemergeFeats)
            if self.sub_stream:
                print("Do in substream999999")
                sys.exit()
            merged = self.replace_everywhere(merged, remerge, NewRemerge)
            self.stack = self.replace_everywhere(self.main_stack, remerge, NewRemerge)
            MergeData = "merge (for labeling) " + remerge[0] + " + " + merged[0]
            self.output.append(("merge", MergeData))
            if merged[1][0] == "vUnerg":
                sys.exit()
            Output = self.label_check(merged)
            if Output:
                NewMerged = Output
                merged = NewMerged
            # Find new MergedLabel
            MergedLabel = merged[0]
            NewMerged = Constituent([MergedLabel, remerge])
            self.main_stack.append(remerge)
            # FindNewLabel
            if merged[1] == remerge:
                Label = merged[2][0]
            else:
                Label = merged[1][0]
            NewMerged.append(merged)
            if not self.sub_stream:
                self.stack.append(NewMerged)
            Output = self.label_check(NewMerged)
            # Fix this
            if Output:
                NewMerged = Output
            if NewMerged.unlabeled():
                self.output.append(("Label(None)", str(NewMerged)))
            else:
                self.output.append(("Label(SharedFeats)", str(NewMerged)))
                print("Label via shared FEatures2", NewMerged)
                print("\n")
            Cont = True
            StackCtr = len(self.main_stack) - 1
            while Cont:
                if not self.sub_stream:
                    Current = self.stack[StackCtr]
                else:
                    print("CheckSubStream55555")
                    sys.exit()
                if str(remerge) in str(Current):
                    if remerge != Current:
                        CurrentFeats = self.get_head_features(Current)
                        if "Root" in str(CurrentFeats):
                            True
                        else:
                            if Current[1] == remerge:
                                LabelElem = Current[2]
                                NewLabel = LabelElem[0]
                            elif Current[2] == remerge:
                                LabelElem = Current[1]
                                NewLabel = LabelElem[0]
                            else:
                                NewLabel = Current[0]
                            NewCurrent = Constituent(label=NewLabel, part1=Current[1],
                                                     part2=Current[2])
                            if "Root" not in str(CurrentFeats):
                                LabeledViaMovement = [NewCurrent]
                            tup = (StackCtr, NewCurrent)
                            ReplaceTups.append(tup)
                            NewMerged = self.replace_everywhere(NewMerged, Current, NewCurrent)
                            if not self.sub_stream:
                                self.stack = self.replace_everywhere(self.main_stack, Current,
                                                                    NewCurrent)
                            Cont = False
                StackCtr -= 1
                if StackCtr < 0:
                    Cont = False
            if not self.sub_stream:
                self.stack.append(NewMerged)
            return NewMerged
        return False

    def label_check(self, Merged):
        Labeled = False
        if not self.stack:
            return False
        ctr = 0
        Cont = True
        while Cont:
            Current = self.stack[ctr]
            if Current[0] == "_":
                Output = self.LabelCheckFunct(Current)
                if Output:
                    if str(Current) not in str(Merged):
                        print("Error not found Label Check")
                        print("Merged", Merged)
                        print("Current", Current)
                        print("Output", Output)
                        print("Merged",)
                        sys.exit()
                    Merged = self.replace_everywhere(Merged, Current, Output)
                    if not self.sub_stream:
                        self.stack = self.replace_everywhere(self.stack, Current, Output)
                    Labeled = True
            ctr += 1
            if ctr > len(self.stack) - 1:
                Cont = False

        if Merged[0] == "_":
            Output = self.LabelCheckFunct(Merged)
        if Labeled:
            return Merged
        else:
            return False

    def LabelCheckFunct(self, Merged):
        SharedFeats = []
        Elem1 = Merged[1]
        Elem2 = Merged[2]
        if Elem1[0] == "_":
            Elem1Feats = self.get_head_features(Elem1[1])
        else:
            Elem1Feats = self.get_head_features(Elem1)
        if Elem2[0] == "_":
            Elem2Feats = self.get_head_features(Elem2[1])
        else:
            Elem2Feats = self.get_head_features(Elem2)
        if not Elem1Feats:
            return False
        if not Elem2Feats:
            return False

        if Elem1[0] == "_":
            if Elem2[0] == "_":
                return False
        Weak = False
        if "Root" in str(Elem1Feats):
            Weak = True
        if Weak:
            if "iPerson" in str(Elem1Feats):
                if "iNumber" in str(Elem1Feats):
                    if "iGender" in str(Elem1Feats):
                        for Elem1F in Elem1Feats:
                            if "iPerson" in Elem1F:
                                Nums = re.findall(NUM_PATTERN, Elem1F)
                        NewMerged = Constituent()
                        if self.language == "Japanese":
                            NewLabel = Merged[-1][0]
                        else:
                            NewLabel = Elem1[0]
                        NewMerged.append(NewLabel)
                        NewMerged.append(Elem1)
                        NewMerged.append(Elem2)
                        self.output.append(("Label(Strengthened)", str(NewMerged)))
                        return NewMerged
                else:
                    print("Only Person")
                    print("Merged", Merged)
                    sys.exit()
            elif "UErg" in str(Elem1Feats):
                NewMerged = Constituent()
                NewLabel = Elem1[0]
                NewMerged.append(NewLabel)
                NewMerged.append(Elem1)
                NewMerged.append(Elem2)
                self.output.append(("Label(Strengthened)", str(NewMerged)))
                return NewMerged
        if "Copy" in Elem1Feats:
            if "Copy" not in Elem2Feats:
                if "Root" in str(Elem2Feats):
                    Weak = True
                if Weak:
                    if "iPerson" in str(Elem2Feats):
                        if "iNumber" in str(Elem2Feats):
                            if "iGender" in str(Elem2Feats):
                                NewMerged = Constituent()
                                NewLabel = Elem2[0]
                                NewMerged.append(NewLabel)
                                NewMerged.append(Elem1)
                                NewMerged.append(Elem2)
                                self.output.append(("Label(Move)", str(NewMerged)))
                                return NewMerged
                else:
                    NewMerged = Constituent()
                    NewLabel = Elem2[0]
                    NewMerged.append(NewLabel)
                    NewMerged.append(Elem1)
                    NewMerged.append(Elem2)
                    self.output.append(("Label(Move)", str(NewMerged)))
                    return NewMerged

        if "Copy" in Elem2Feats:
            if "Copy" not in Elem1Feats:
                if "Root" in str(Elem1Feats):
                    Weak = True
                if Weak:
                    if "iPerson" in str(Elem1Feats):
                        if "iNumber" in str(Elem1Feats):
                            if "iGender" in str(Elem1Feats):
                                NewMerged = Constituent()
                                NewLabel = Elem1[0]
                                NewMerged.append(NewLabel)
                                NewMerged.append(Elem1)
                                NewMerged.append(Elem2)
                                self.output.append(("Label(Move)", str(NewMerged)))
                                return NewMerged
        for F in Elem1Feats:
            if F in Elem2Feats:
                SharedFeats.append(F)
        if not SharedFeats:
            # Check for strengthened element
            return False
        if "iPerson" in str(SharedFeats):
            if "iNumber" in str(SharedFeats):
                if "iGender" in str(SharedFeats):
                    for Elem1F in SharedFeats:
                        if "iPerson" in Elem1F:
                            Nums = re.findall(NUM_PATTERN, Elem1F)
                            if self.language == "Japanese":
                                NewLabel = Merged[-1][0]
                            else:
                                if len(Nums) > 0:
                                    NewLabel = "Phi" + str(Nums[0])
                                else:
                                    NewLabel = "Phi"
                    NewMerged = Constituent([NewLabel, Elem1, Elem2])
                    if self.language == "Japanese":
                        self.output.append(("Label(Strengthened)", str(NewMerged)))
                    else:
                        self.output.append(("Label(SharedFeats)", str(NewMerged)))
                    return NewMerged
            else:
                NewLabel = "Per"
                NewMerged = Constituent([NewLabel, Elem1, Elem2])
                self.output.append(("Label(SharedFeats)", str(NewMerged)))
                return NewMerged
        return False

    def get_head_features_head_final(self, merged):
        """ I'm not putting much effort to fix this, it should be refactored anyways, one method for
         both head final and head first languages
        :param merged:
        :return:
        """
        if "kiPerson" in str(merged):
            print("error")
            print("Merged", merged)
            sys.exit()

        if len(merged) == 2:
            if type(merged[0]) != list:
                if type(merged[1]) == list:
                    head_feats = merged[-1]
                    return head_feats
        if merged[0] == "_":
            head = self.get_head(merged[-1])
        else:
            head = self.get_head(merged)
        ctr = len(merged) - 1
        cont = True
        while cont:
            current = merged[ctr]
            current_head = current[0]
            if current_head == head:
                head_feats = self.get_head_features_head_final(current)
                return head_feats
            if len(current) == 2:
                if type(current[-1]) == list:
                    head_feats = current[-1]
                    return head_feats
            else:
                list_pres = False
                for f in current:
                    if type(f) == list:
                        list_pres = True
                if not list_pres:
                    head_feats = current
                    return current
            ctr -= 1
            if ctr < 0:
                print("Error")
                print("Can't find head feats")
                sys.exit()

    def get_head_features(self, merged):
        def _get_head_features(merged):
            if merged.features:
                return merged.features
            head = merged.label
            if merged.part1.label == head:
                return self.get_head_features(merged.part1)
            if merged.part2.label == head:
                return self.get_head_features(merged.part2)
            if head in SHARED_FEAT_LABELS:
                elem1_feats = self.get_head_features(merged.part1)
                elem2_feats = self.get_head_features(merged.part2)
                shared_feats = []
                for F in elem1_feats:
                    if F in elem2_feats:
                        shared_feats.append(F)
                if shared_feats:
                    return shared_feats
            if "Phi" in head:
                head_features = self.get_head_features(merged.part1)
                return head_features

        if self.language == "Japanese":
            return self.get_head_features_head_final(merged)
        elif merged.features:
            return merged.features
        elif merged.part1:
            if merged.unlabeled():
                return _get_head_features(merged.part1)
            elif merged.part2.unlabeled():
                return _get_head_features(merged.part1) or _get_head_features(merged)
        return _get_head_features(merged)

    @staticmethod
    def get_head(merged):
        # this will find the head of a Merged syntactic object. The head is a string,
        # and shouldn't have
        # any brackets
        for i, li in enumerate(merged):
            if not isinstance(li, list):
                if i != 0:
                    print('not first: ', i, merged)
                return li
        print("Error: No Head found")
        sys.exit()

    def get_form(self, synobj):
        # "MergeF" is a feature that is deleted upon Merged
        # used to keep track of whether or not an element has undergone first MErge
        # can distinguish an X (simple) from an XP (complex)

        # put elements with uFs right onto the stack
        features = list(LEXICON.get(synobj, LEXICON['root']))
        if any((f in COUNTED_FEATURES for f in features)):
            self.feature_counter += 1
            for i, feat in enumerate(list(features)):
                if feat in COUNTED_FEATURES:
                    features[i] = feat + str(self.feature_counter)
        if any((f in COUNTED_PHI_FEATURES for f in features)):
            self.phi_counter += 1
            for i, feat in enumerate(list(features)):
                if feat in COUNTED_PHI_FEATURES:
                    features[i] = feat + str(self.phi_counter)
        if synobj == 'C_null':
            synobj = 'C'
        elif synobj == 'n_Expl':
            synobj = 'n'
        return Constituent([synobj, features])

    def check_features(self, x, y):
        # If X has uPhi, then uPhi are passed down the tree until they are checked
        if x.unlabeled():
            x_feats = self.get_head_features(x.part1)
        else:
            x_feats = self.get_head_features(x)
        if y.unlabeled():
            y_feats = self.get_head_features(y.part1)
        elif y.label in SHARED_LABELS:
            if y.features:
                print('this happens!')
                y_feats = self.get_head_features(y.features)
            else:
                y_feats = self.get_head_features(y.part1)
        else:
            if y.part2:
                if y.part2.unlabeled():
                    print("problem")
                    print("Y", y)
                    sys.exit()

            y_feats = self.get_head_features(y)
        current_label = ''
        if "Head" in x_feats:
            if "Head" in y_feats:
                print("Both are heads")
                print("Figure out label")
                print("%%%%")
                sys.exit()
            else:
                current_label = x.label
        elif "Head" in y_feats:
            current_label = y.label
        if current_label:
            print_merge = Constituent(label=current_label)
            if self.language == "Japanese":
                print_merge.append(y)
                print_merge.append(x)
            else:
                print_merge.append(x)
                print_merge.append(y)
            self.output.append(("Label(Head)", str(print_merge)))
        inherit = None
        u_phi = []
        for f in x_feats:
            if "uPerson" in f:
                u_phi.append(f)
            elif "uNumber" in f:
                u_phi.append(f)
            elif "uGender" in f:
                u_phi.append(f)
            elif "Case" in f:
                if "uCase" not in f:
                    u_phi.append(f)
            elif "UErg" in f:
                u_phi.append(f)
        if len(u_phi) >= 3:
            inherit = x
        elif x.label in PHASE_HEADS:
            inherit = x
        elif "UErg" in x_feats:
            inherit = x
        if not inherit:
            for f in y_feats:
                if "uPerson" in f:
                    u_phi.append(f)
                elif "uNumber" in f:
                    u_phi.append(f)
                elif "uGender" in f:
                    u_phi.append(f)
                elif "Case" in f:
                    if "uCase" not in f:
                        u_phi.append(f)
            if len(u_phi) >= 3:
                inherit = y
        passed_l = []
        feats_passed = False
        prev = False  # block feature passage to nominal
        if inherit:
            passing = False
            # pass feats down the tree
            cont = True
            stack_ctr = len(self.stack) - 1
            while cont:

                current = self.stack[stack_ctr]
                if current == x:
                    stack_ctr -= 1
                    current = self.stack[stack_ctr]
                current_feats = self.get_head_features(current)
                if "Root" in str(current_feats):
                    if "uPerson" not in str(current_feats):
                        if "iPerson" not in str(current_feats):
                            if current not in passed_l:
                                if "iD" not in str(current_feats):
                                    if "iN" not in str(current_feats):
                                        if prev != "n":

                                            passed_l.append(current)
                                            if current.label != "_":
                                                other_label = current.label
                                            else:
                                                if current.part1.label != "_":
                                                    if self.language == "Japanese":
                                                        other_label = current.part2.label
                                                    else:
                                                        other_label = current.part1.label
                                                elif current.part2.label != "_":
                                                    if self.language == "Japanese":
                                                        other_label = current.part1.label
                                                    else:
                                                        other_label = current.part2.label
                                                else:
                                                    print("error - can't find label9999")
                                                    sys.exit()
                                            passing = True
                prev = current.label
                if passing:
                    new_feats = current_feats + u_phi
                    new_current = self.replace_features(current, current_feats, new_feats)
                    phase_head = inherit.label
                    self.output.append(("PassFs", "Pass Features " + phase_head + " to " + other_label))
                    self.output.append(("FeaturesPassed", " ".join(u_phi)))
                    self.inheritance_counter += 1
                    y = self.replace_everywhere(y, current, new_current)
                    feats_passed = True
                    passing = False
                stack_ctr -= 1
                if stack_ctr < 0:
                    cont = False
            x, y, checked_feats = self.check_features_function(x, y)
            label_output = self.label_check(y)
            if label_output:
                y = label_output

        else:
            x, y, checked_feats = self.check_features_function(x, y)
        return x, y, feats_passed

    def replace_features(self, elem, old_feats, new_feats):
        new_elem = self.replace_everywhere(elem, old_feats, new_feats)
        self.stack = self.replace_everywhere(self.stack, old_feats, new_feats)
        return new_elem

    def check_features_function(self, x, y):
        if x.unlabeled():
            x_feats = self.get_head_features(x.part1)
        else:
            x_feats = self.get_head_features(x)
        if y.unlabeled():
            y_feats = self.get_head_features(y.part1)
        elif y.label in SHARED_LABELS:
            if y.features:
                y_feats = self.get_head_features(y.features)
            else:
                y_feats = self.get_head_features(y.part1)
        else:
            y_feats = self.get_head_features(y)
        checked_feats_tup = []  # tuple of previous unchecked features and newly checked features
        checked_feats = []
        # XFeats probe
        if "MergeF" in x_feats:
            new_x_feats = []
            for f in x_feats:
                if f != "MergeF":
                    new_x_feats.append(f)
            x = self.replace_features(x, x_feats, new_x_feats)

            x_feats = new_x_feats
            self.stack = self.replace_everywhere(self.stack, x_feats, new_x_feats)
        Phi = False
        if "uPerson" in str(x_feats):
            if "uNumber" in str(x_feats):
                if "uGender" in str(x_feats):
                    Phi = True
        uFs = []
        for f in x_feats:
            if f[0] == "u":
                uFs.append(f)
            elif "Case" in f:
                if Phi:
                    uFs.append(f)
            elif "iScp" in f:
                uFs.append(f)
        if not self.sub_stream:
            if not self.stack:
                print('quick escape! ', type(x), type(y))
                return x, y
        if not uFs:
            True
        else:
            pattern = r'[^1-9]+'
            uFpattern = r'u[A-Z][a-z]*'
            ####
            FeatCtr = 0
            StackCtr = len(self.stack) - 1  # top element should be identical to probe
            RemovedFeats = dict()
            Cont = True
            FeatCtr = 0
            new_x_feats = []
            CheckedX = False
            while FeatCtr < len(uFs):
                Skip = False
                FeatChecked = False
                f = uFs[FeatCtr]
                if f[0] != "u":
                    Skip = True
                m = re.findall(pattern, f)
                Target = m[0]
                Goal = "i" + Target[1:]
                stack_top = self.stack[StackCtr]
                if stack_top == x:
                    StackCtr -= 1
                    stack_top = self.stack[StackCtr]
                if "Phi" in stack_top[0]:
                    # Don't look at the features of an element with shared phi-features
                    # This is maybe an imperfection
                    top_feats = False
                else:
                    top_feats = self.get_head_features(stack_top)
                if top_feats is None:
                    sys.exit()

                PhiChecked = False
                p = re.findall(uFpattern, str(top_feats))
                if p:
                    uFPresent = False
                    uFPresent = True
                    # Check for possibility of feature unification
                    # Avoid probing from non-root element at this time
                    unified_feats_temp = []
                    for top_f_temp in top_feats:
                        target_temp1 = re.findall(uFpattern, top_f_temp)
                        if target_temp1:
                            top_f_temp = target_temp1[0]
                            if top_f_temp in f:
                                # Find TargetuF
                                target_uf_temp1 = None
                                for uF1 in top_feats:
                                    if top_f_temp in uF1:
                                        target_uf_temp1 = uF1
                                    if target_uf_temp1:
                                        if target_uf_temp1 != f:
                                            if f not in unified_feats_temp:
                                                unified_feats_temp.append(f)
                                                self.stack = self.replace_everywhere(self.stack,
                                                                                     target_uf_temp1,
                                                                                     f)
                                                if target_uf_temp1 in top_feats:
                                                    top_feats[top_feats.index(target_uf_temp1)] = f

                                                stack_top = self.replace_everywhere(stack_top,
                                                                                    target_uf_temp1,
                                                                                    f)
                                                x = self.replace_everywhere(x, target_uf_temp1, f)

                                                y = self.replace_everywhere(y, target_uf_temp1, f)
                                                self.output.append(("Unification", f))
                else:
                    uFPresent = False
                if f == "uQ":
                    uFPresent = True  # it doesn't matter if a potential goal has any uFs
                    # uFs aren't needed to be visible.
                if f == "uTop":
                    uFPresent = True
                if Goal in str(top_feats):
                    if stack_top[0] == "_":
                        Unlabeled = True
                    else:
                        Unlabeled = False
                    if uFPresent:
                        if Unlabeled:
                            True
                        elif "iTop" in Goal:
                            TopuFs = []
                            for TopF in top_feats:
                                if TopF[0] == "u":
                                    TopuFs.append(TopF)
                            TopChkd = []
                            if TopuFs:
                                for TopuF in TopuFs:
                                    m = re.findall(pattern, TopuF)
                                    OriginalTop = TopuF
                                    if m:
                                        TargetTop = m[0]
                                        TargetTopGoal = "i" + TargetTop[1:]

                                    for TempuFGoal in uFs:
                                        if TargetTopGoal in TempuFGoal:
                                            TopChkdTup = (OriginalTop, TempuFGoal)
                                            TopChkd.append(TopChkdTup)
                                if TopChkd:
                                    for tup in TopChkd:
                                        OldTopF = tup[0]
                                        NewTopF = tup[1]
                                        NewTop = self.replace_everywhere(stack_top, OldTopF, NewTopF)
                                        Form = NewTop[1][0]
                                        NewForm = Form + "-wa"
                                        TopTemp = self.replace_everywhere(NewTop, Form, NewForm)
                                        NewTop = TopTemp
                                        stack_top = NewTop
                                        NewX = self.replace_everywhere(x, OldTopF, NewTopF)
                                        x = NewX

                                        NewY = self.replace_everywhere(y, OldTopF, NewTopF)
                                        y = NewY
                                        if OldTopF not in checked_feats:
                                            checked_feats.append(OldTopF)
                                            checked_feats_tup.append(tup)
                                        if self.sub_stream:
                                            print("Check in substream999999")
                                            sys.exit()
                                        self.main_stack = self.replace_everywhere(self.main_stack,
                                                                                  OldTopF,
                                                                                  NewTopF)

                            self.remerge = stack_top
                            # Add Copy to any copy in derivation
                            # REmove Copy from remerged version
                            RemergeFeats = self.get_head_features(self.remerge)
                            if "Copy" in RemergeFeats:
                                # RemoveCopy
                                NewRemergeFeats = []
                                for RemF in RemergeFeats:
                                    if RemF == "Copy":
                                        True
                                    else:
                                        NewRemergeFeats.append(RemF)
                                self.remerge = self.replace_everywhere(self.remerge, RemergeFeats, NewRemergeFeats)
                        elif "iQ" in Goal:
                            TopuFs = []
                            for TopF in top_feats:
                                if TopF[0] == "u":
                                    TopuFs.append(TopF)
                            TopChkd = []
                            if TopuFs:
                                for TopuF in TopuFs:
                                    m = re.findall(pattern, TopuF)
                                    OriginalTop = TopuF
                                    if m:
                                        TargetTop = m[0]
                                        TargetTopGoal = "i" + TargetTop[1:]

                                    for TempuFGoal in uFs:
                                        if TargetTopGoal in TempuFGoal:
                                            TopChkdTup = (OriginalTop, TempuFGoal)
                                            TopChkd.append(TopChkdTup)
                                if TopChkd:
                                    for tup in TopChkd:
                                        OldTopF = tup[0]
                                        NewTopF = tup[1]
                                        NewTop = self.replace_everywhere(stack_top, OldTopF, NewTopF)
                                        stack_top = NewTop
                                        NewX = self.replace_everywhere(x, OldTopF, NewTopF)
                                        x = NewX

                                        NewY = self.replace_everywhere(y, OldTopF, NewTopF)
                                        y = NewY
                                        if OldTopF not in checked_feats:
                                            checked_feats.append(OldTopF)
                                            checked_feats_tup.append(tup)
                                        if self.sub_stream:
                                            print("Check in substream999999")
                                            sys.exit()
                                        self.stack = self.replace_everywhere(self.stack,
                                                                             OldTopF,
                                                                             NewTopF)

                            self.remerge = stack_top
                            # Add Copy to any copy in derivation
                            # REmove Copy from remerged version
                            RemergeFeats = self.get_head_features(self.remerge)
                            if "Copy" in RemergeFeats:
                                # RemoveCopy
                                NewRemergeFeats = []
                                for RemF in RemergeFeats:
                                    if RemF == "Copy":
                                        True
                                    else:
                                        NewRemergeFeats.append(RemF)
                                print('bababoom')
                                self.remerge = self.replace_everywhere(self.remerge, RemergeFeats, NewRemergeFeats)
                                print("self.Remerge111", self.remerge)
                                print("\n")
                                # Find highest instance in derivation and add "Copy"

                        # Remerge due to a need to share Q features
                        if not Unlabeled:
                            for TopF in top_feats:
                                if Goal in TopF:
                                    CheckedX = self.replace_everywhere(x, f, TopF)
                                    x = CheckedX

                                    CheckedY = self.replace_everywhere(y, f, TopF)
                                    y = CheckedY
                                    tup = (f, TopF)
                                    checked_feats_tup.append(tup)
                                    self.stack = self.replace_everywhere(self.stack, f, TopF)
                            FeatChecked = True
                            checked_feats.append(f)
                            # Check uScp as a reflex of uQ checking
                elif "Case:" in f:
                    tup = (f, "NONE")
                    checked_feats_tup.append(tup)
                    checked_feats.append(f)
                    NewX = self.replace_everywhere(x, f, "NONE")
                    x = NewX

                    NewStack = self.replace_everywhere(self.main_stack, f, "NONE")
                    self.main_stack = NewStack
                    NewY = self.replace_everywhere(y, f, "NONE")
                    y = NewY
                    NewYFeats = self.get_head_features(y)
                    if self.language == "Japanese":  # head final issue
                        if "uCase" in str(y):
                            YStr = str(y)
                            Start = YStr.find("uCase")
                            TempYCont = True
                            End = Start + 1
                            while TempYCont:
                                CurrentY = YStr[End]
                                if CurrentY == "'":
                                    TempYCont = False
                                End += 1
                            YFeat = YStr[Start:End - 1]
                            CheckedY = self.replace_everywhere(y, YFeat, f)
                            y = CheckedY
                            tup = (YFeat, f)
                            checked_feats_tup.append(tup)
                            if not self.sub_stream:
                                self.main_stack = self.replace_everywhere(self.stack, YFeat, f)
                    else:  # not Japanese (not head final)
                        for YFeat in y_feats:
                            if "uCase" in YFeat:
                                CheckedY = self.replace_everywhere(y, YFeat, f)
                                y = CheckedY
                                tup = (YFeat, f)
                                checked_feats_tup.append(tup)
                                self.stack = self.replace_everywhere(self.stack, YFeat, f)
                    FeatChecked = True
                elif f == "uPhi":
                    if "iPerson" in str(top_feats):
                        new_x_feats = []
                        for TempXFeat in x_feats:
                            if TempXFeat == "uPhi":
                                True
                            else:
                                new_x_feats.append(TempXFeat)
                        for TopF in top_feats:
                            if "iPerson" in TopF:
                                new_x_feats.append(TopF)
                            elif "iNumber" in TopF:
                                new_x_feats.append(TopF)
                            elif "iGender" in TopF:
                                new_x_feats.append(TopF)
                            elif "uCase" in TopF:
                                new_x_feats.append(TopF)
                    x = self.replace_features(x, x_feats, new_x_feats)
                    x_feats = new_x_feats
                    self.output.append(("PhiPassing", "uPhi"))
                    FeatChecked = True
                    self.inheritance_counter += 1
                if FeatChecked:
                    FeatCtr += 1
                    StackCtr = len(self.stack) - 1  # top element should be identical to probe
                else:
                    StackCtr -= 1
                    if StackCtr < 0:
                        FeatCtr += 1
                        StackCtr = len(self.stack) - 1  # top element should be identical to probe
        if checked_feats:
            CheckedFs = " ".join(checked_feats)
            self.output.append(("CheckedFeatures", CheckedFs))
            self.feature_check_counter += len(checked_feats)
        return x, y, checked_feats_tup

    @staticmethod
    def replace_everywhere_old(element, old_chunk, new_chunk):
        # my version:
        def recursive_replace(element, old, new):
            if element == old:
                return new
            if isinstance(element, Constituent):
                new_element = Constituent()
                if old in element:
                    element = Constituent(element) # don't change the original list
                    element[element.index(old)] = new
                for item in element:
                    new_item = recursive_replace(item, old, new)
                    if new_item:
                        new_element.append(new_item)
                return new_element

            if isinstance(element, list):
                new_element = []
                if old in element:
                    element = list(element) # don't change the original list
                    element[element.index(old)] = new
                for item in element:
                    new_item = recursive_replace(item, old, new)
                    if new_item:
                        new_element.append(new_item)
                return new_element
            elif isinstance(element, str) and isinstance(old, str):
                return element.replace(old, new)
            return element
        if new_chunk == 'NONE':
            new_chunk = ''
        return recursive_replace(element, old_chunk, new_chunk)

    @staticmethod
    def replace_everywhere(element, old_chunk, new_chunk):
        # my version:
        def recursive_replace_constituent(element, old, new):
            if element == old:
                return new
            if not element.part1:
                return element
            element.part1 = recursive_replace_constituent(element.part1, old, new)
            element.part2 = recursive_replace_constituent(element.part2, old, new)
            return element

        def recursive_replace_feature_list(element, old, new):
            if element.part1:
                element.part1 = recursive_replace_feature_list(element.part1, old, new)
            if element.part2:
                element.part2 = recursive_replace_feature_list(element.part2, old, new)
            if old == element.features:
                element.features = new
            return element

        def recursive_replace_feature(element, old, new):
            if element.part1:
                element.part1 = recursive_replace_feature(element.part1, old, new)
            if element.part2:
                element.part2 = recursive_replace_feature(element.part2, old, new)
            if element.features:
                new_features = []
                for f in element.features:
                    new_feat = f.replace(old, new)
                    if new_feat:
                        new_features.append(new_feat)
                if new_features != element.features:
                    element.features = new_features
            return element

        if isinstance(element, list) and not isinstance(element, Constituent):
            new_list = []
            for item in element:
                new_list.append(Generate.replace_everywhere(item, old_chunk, new_chunk))
            return new_list
        if isinstance(old_chunk, Constituent):
            return recursive_replace_constituent(element, old_chunk, new_chunk)
        elif isinstance(old_chunk, list):
            return recursive_replace_feature_list(element, old_chunk, new_chunk)
        elif isinstance(old_chunk, str):
            if new_chunk == 'NONE':
                new_chunk = ''
            return recursive_replace_feature(element, old_chunk, new_chunk)

def start(input_data):
    f = open(input_data, 'r')
    input_data = f.readlines()
    f.close()
    t = time.time()
    a = Generate(input_data)
    ProduceOutput.ProduceFile(a.output, 'new/')
    print(time.time() - t)

# "../Languages/Japanese/DisWarn.txt"

start("./POP.txt")
