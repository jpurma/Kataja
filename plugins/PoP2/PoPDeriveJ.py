#######################################################
###Derivation Generator - Problems of Projection Version
## Rewriting Jason Ginsburg's computer model for PoP,
# http://www.osaka-kyoiku.ac.jp/~jginsbur/MinimalistModeling.html
# Jukka Purma
#########################################################

import sys
import time

try:
    from PoP2.Lexicon import DET_HEADS, PHASE_HEADS, THETA_ASSIGNERS, SHARED_LABELS, \
        ADJUNCT_LABELS, COUNTED_FEATURES, COUNTED_PHI_FEATURES, LEXICON
    from PoP2.ConstituentB import Constituent, find_shared_features, expanded_features
    from PoP2.FeatureB import Feature, has_part, get_by_part
    in_kataja = True
except ImportError:
    from Lexicon import DET_HEADS, PHASE_HEADS, THETA_ASSIGNERS, SHARED_LABELS, \
        ADJUNCT_LABELS, COUNTED_FEATURES, COUNTED_PHI_FEATURES, LEXICON
    from ConstituentB import Constituent, find_shared_features, expanded_features
    from FeatureB import Feature, has_part, get_by_part
    in_kataja = False

start = 9
end = 10


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
        for item in self.sub_stack:
            item.stacked = False
        self.sub_stack = []

    def clear_main_stack(self):
        for item in self.main_stack:
            item.stacked = False
        self.main_stack = []

    def append(self, item, force_main=False, duplicates=True):
        item.stacked = True
        if force_main or not self.sub_stream:
            if duplicates or item not in self.main_stack:
                self.main_stack.append(item)
        else:
            if duplicates or item not in self.sub_stack:
                self.sub_stack.append(item)

    def cut_to(self, item):
        if self.sub_stream:
            for it in self.sub_stack[:self.sub_stack.index(item)]:
                it.stacked = False
            self.sub_stack = self.sub_stack[self.sub_stack.index(item):]
        else:
            for it in self.main_stack[:self.main_stack.index(item)]:
                it.stacked = False
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
                    item.stacked = True
                else:
                    item.recursive_replace_constituent(old_chunk, new_chunk)
            elif isinstance(old_chunk, set):
                found = item.recursive_replace_feature_set(old_chunk, new_chunk)
                #print('in stack, replacing feature sets, found: ', found)
            elif isinstance(old_chunk, (str, Feature)):
                found = item.recursive_replace_feature(old_chunk, new_chunk)
                #print('in stack, replacing features, found: ', found)
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


class Generate:
    def __init__(self, out_writer=None):

        self.out_writer = out_writer
        self.so_list = []
        self.phi_counter = 0
        self.feature_counter = 0
        self.stack = None
        self.merge_counter = 0
        self.inheritance_counter = 0
        self.feature_check_counter = 0
        self.lookforward_so = None
        self.over_counter = 0
        self.dumpfile = None
        self.forest = None
        self.workspace = []
        self.sub_workspace = []
        self.msg_stack = []
        self.spine = None

    def load_data(self, inputlines, start=0, end=0):
        for line in inputlines:
            sentence, lbracket, target_str = line.partition('[')
            if not (sentence and lbracket and target_str):
                continue
            sentence = sentence.strip()
            sentence_number = sentence[0]

            if not sentence_number.isdigit():
                continue
            sentence_number = int(sentence_number)
            if end and sentence_number >= end:
                break
            elif sentence_number < start:
                continue
            sentence = sentence[2:]  # remove number and the space after it
            target_example = eval(lbracket + target_str)
            self.out(sentence_number, sentence, target_example)
            so = self.generate_derivation(target_example)
            self.out("MRGOperations", self.merge_counter)
            self.out("FTInheritanceOp", self.inheritance_counter)
            self.out("FTCheckOp", self.feature_check_counter)

    def out(self, first, second, third=None):
        if self.forest:
            self.msg_stack.append('%s: %s' % (first, second))
        #print('%s: %s' % (first, second))
        if not self.out_writer:
            return
        self.out_writer.push(first, second, third)

    def dump_to_file(self, synobj):
        if not self.dumpfile:
            self.dumpfile = open('deriveG.log', 'w')
        self.dumpfile.write(str(synobj.model10_string()))
        self.dumpfile.write('\n')

    def generate_derivation(self, target_example, forest=None):
        """
        :param target_example:
        :param forest: (optional) Kataja forest where the derivation will be pushed
        :return:
        """
        def build_synobj_lists(example_list, result_list):
            for li in reversed(example_list):
                if isinstance(li, list):
                    result_list.append(build_synobj_lists(li, []))
                else:
                    result_list.append(self.get_lexem(li))
            result_list.reverse()
            return result_list

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
        self.feature_check_counter = 0
        self.lookforward_so = None
        self.so_list = build_synobj_lists(target_example, [])
        self.forest = forest
        self.spine = None
        self.workspace = []
        so = None
        selected = None
        while self.so_list:
            self.lookforward_so = self.so_list.pop()
            if so:
                selected = merge_so(so, selected)
            so = self.lookforward_so
            # Use self.so_list + [self.looforward_so] as remaining numeration, lookforward_so is
            # not actually processed yet.

        self.lookforward_so = None
        selected = merge_so(so, selected)
        self.dump_to_file(selected)

        if selected.is_unlabeled():
            selected, success = self.label_if_possible(selected)
            self.out("Crash(Unlabeled)", selected)
            sys.exit()

        self.out("Transfer", selected)
        return selected

    def merge_substream(self, synobjlist, spine):
        """ Switch into substream (phrase within sentence) and build that before
        merging the whole thing into main spine.
        :param synobjlist: list of syntactic objects
        :param spine: main structure of merged objects
        :return: spine
        """
        print('merge_substream')
        print('>>>>>  starting substream')
        self.stack.start_sub_stream()
        self.out("SubStream", True)
        substream_spine = None

        while synobjlist:
            x = synobjlist.pop()
            substream_spine = self.merge_so(x, substream_spine)
        self.stack.end_sub_stream()
        print('<<<<<  ended substream')
        # merge substream back to main stream:
        self.out("MainStream", True)
        msg = "merge " + spine.label + " + " + substream_spine.label
        self.out("merge", msg)
        self.spine = self.merge(spine, substream_spine)
        return self.spine

    def announce_derivation_step(self, parts=None, msg=''):
        if not self.forest:
            return
        self.msg_stack.append(msg)
        msg = '\n'.join(self.msg_stack)
        self.msg_stack = []
        if parts:
            if not isinstance(parts, list):
                parts = [parts]
            if self.stack.is_main():
                self.workspace = parts
            else:
                self.sub_workspace = parts
        if self.lookforward_so:
            num = self.so_list + [self.lookforward_so]
        else:
            num = []
        if self.stack.is_main():
            self.sub_workspace = []
        self.forest.derivation_steps.save_and_create_derivation_step(self.sub_workspace +
                                                                     self.workspace,
                                                                     numeration=num,
                                                                     msg=msg)

    def merge_so(self, x, spine):
        """ Select new item and merge it into structure
        :param x: syntactic object
        :param spine: main structure of merged objects
        :return: spine
        """
        print('merge_so')
        if not spine:
            if self.stack.is_main():
                self.spine = x
            return x
        else:
            msg = "merge " + x.label + " + " + spine.label
            self.out("merge", msg)
            spine = self.merge(x, spine)
            if self.stack.is_main():
                self.spine = spine
            print('finished merge: ', spine)
            print('---- kataja string: ----')
            print(spine.tex_tree(self.stack.main_stack))
            print('----------------- ', self.over_counter)
            self.over_counter += 1
            return spine

    def grand_cycle(self, x, spine):
        """ Do all operations of one derivation cycle

        :param x:
        :param spine:
        :return:
        """
        y = spine
        x, y, passed_features, postponed_remerge = self.check_features(x, y)

        label_giver, part1, part2 = self.determine_label(x, y)
        merged = self.merge(label_giver, part1, part2)
        if merged.is_unlabeled():
            merged, remerge = self.unlabeled_move(merged)
        else:
            remerge = None
        merged, success = self.label_if_possible(merged)
        if remerge:
            merged = self.remerge(merged, remerge)
            merged, success = self.label_if_possible(merged)
            self.relabel_my_parent(merged, remerge)

        if label_giver:
            if postponed_remerge:
                merged = self.remerge_back(merged, postponed_remerge)
                merged, success = self.label_if_possible(merged)
                if success:
                    self.announce_derivation_step([merged], "found label for unlabeled element")


        if merged.label in PHASE_HEADS:
            merged = self.transfer_check(merged)



    def merge(self, x, y):
        """ Merge two objects and trigger all the complications...
        :param x: so
        :param y: so
        :return: merged
        """
        print('merge')
        self.announce_derivation_step([x, y], "selected x, y for merge")
        external_merge = "MergeF" in x.get_head_features()
        # push to stack if unlabeled or if it has uFs
        self.stack.append(x, duplicates=False)
        self.stack.append(y, duplicates=False)
        x, y, passed_features, postponed_remerge = self.check_features(x, y)
        label_giver = None
        other = None
        label_info = None
        x_feats = x.get_head_features()
        y_feats = y.get_head_features()
        # Determine label
        # Head-feature gives immediately label, once
        if "Head" in x_feats and "Head" not in y_feats:
            head_f = get_by_part(x_feats, "Head")
            x_feats.remove(head_f)
            label_giver = x
            other = y
            label_info = "Head"
        elif y.label in ADJUNCT_LABELS:
            label_giver = x
            other = y

        self.merge_counter += 1
        if label_giver:
            # Head merge
            part1 = label_giver
            part2 = other
            label = label_giver.label
        else:
            # Check if adjunct
            # ordering doesn't matter, but this makes things easier
            label = "_"
            x_is_head = None
            if "v" in x.label:
                if y.label.startswith("D"):
                    x_is_head = False
                elif y.label.startswith("Q"):
                    x_is_head = False
            elif "C" in x.label:
                x_is_head = False
            elif "P_in" in x.label:
                x_is_head = False
            if x_is_head is None:
                if external_merge:
                    x_is_head = True
                else:
                    x_is_head = False
            if x_is_head:
                part1 = x
                part2 = y
            else:
                part1 = y
                part2 = x

        merged = Constituent(label=label, part1=part1, part2=part2)
        self.announce_derivation_step([merged], "merged x, y")

        if not label_giver:
            self.out("Label(None)", str(merged))
        merged = self.unlabeled_move(merged)
        if label_giver:
            if passed_features:
                if label_info == "Head":
                    self.out("Label(Head)", merged)
            if postponed_remerge:
                # check_features of RemergedElement??
                # Find Shared Feats
                merged = self.remerge_back(merged, postponed_remerge)
        if merged.label in PHASE_HEADS:
            merged = self.transfer_check(merged)
        return merged

    def remerge_back(self, merged, remerge):
        print('remerge_back')
        shared_feats = merged.shared_features(remerge)
        if has_part(shared_feats, "iQ"):
            label = "Q"
        elif has_part(shared_feats, "iTop"):
            label = "Top"
        else:
            print("SharedFeats", shared_feats)
            print("Merged", merged)
            print("Remerge", remerge)
            print("Can't Determine Label 5555")
            sys.exit()
        if self.stack.is_sub():
            print("Remerging in in substream999999")
            sys.exit()
        msg = "merge (for labeling(remerge back)) " + merged.label + " + " + remerge.label
        self.out("merge", msg)
        merged = Constituent(label=label, part1=remerge, part2=merged)
        self.merge_counter += 1
        self.out("Label(SharedFeats)", merged)
        self.announce_derivation_step([merged], "remerged back")
        merged, success = self.label_if_possible(merged)
        if success:
            self.announce_derivation_step([merged], "found label for unlabeled element")
        return merged

    def transfer_check(self, merged):
        """
        Transfer
        a) The complement of a phase head is transferred.
        b) A derivation is transferred when all operations are completed
        :param merged:
        :return: merged
        """
        def recursive_find_complement(item, target_label, parent_matched):
            label_match = item.label == target_label
            if parent_matched and not label_match:
                return item
            if item.part1:
                found = recursive_find_complement(item.part1, target_label, label_match)
                if found:
                    return found
            if item.part2:
                found = recursive_find_complement(item.part2, target_label, label_match)
                if found:
                    return found
            return None

        print('transfer_check')
        # ##### Dephase because T inherits phasehood ##### #
        if self.stack.is_main() and merged.label == "v*":
            success = self.dephase_and_transfer(merged)
            if success:
                self.announce_derivation_step(merged, "dephased and transferred")
                return success

        if merged.label in PHASE_HEADS:  # This is last resort
            merged_feats = merged.get_head_features()

            if "Delete" in merged_feats:  # Dephase because C is deleted
                transfer, merged = self.dephase_deleted_c(merged)
                transfer.transfered = True
                self.announce_derivation_step(merged, "dephased deleted C")
                remerge = None
                if self.stack.is_main():
                    merged, remerge = self.remerge_if_can(merged, dephase=True)
                self.out("Transfer", transfer)  # Transfer actually does nothing.
                # print('******** Transfer ********')
                self.stack.clear_main_stack()
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

            transfer = recursive_find_complement(merged, target_label, False)
            transfer.transfered = True
            self.out("Transfer", transfer)  # Transfer actually does nothing.
            self.stack.clear_main_stack()
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

        def find_closest_root(const):
            if any(x.name == "Root" for x in const.get_head_features()):
                return const
            # (jukka) We are looking for v:s but if we go into branches we hit into n:s.
            # let's try to not go into branches. another option would be to directly
            # demand 'v' in label
            #if const.part1:
            #    found = find_closest_root(const.part1)
            #    if found:
            #        return found
            if const.part2:
                return find_closest_root(const.part2)
            return None

        current = find_closest_root(merged)
        if current:
            # Transfer the complement of v
            assert current.is_labeled()
            remerge = current
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
            transfer.transfered = True
            self.out("Transfer", transfer)
            # Check to see if Remerge results in labeling
            if self.stack.is_sub():
                print('++ stack append 7 merged, in dephase and transfer')
                self.stack.append(merged, force_main=True)
            return merged

    def dephase_deleted_c(self, merged):
        """ Dephase
            b) Deletion of C transfers phasehood to T.
        """
        def find_next_head(con, target_l, parent_l):
            if con.label != target_l and parent_l == target_l:
                return con
            if con.part1:
                found_left = find_next_head(con.part1, target_l, con.label)
                if found_left:
                    return found_left
            if con.part2:
                return find_next_head(con.part2, target_l, con.label)

        print('dephase_deleted_c')
        left = merged.part1
        right = merged.part2
        label = merged.label
        merged_feats = expanded_features(merged.get_head_features())
        spec = merged.part1
        spec_feats = expanded_features(spec.get_head_features())
        if spec_feats != merged_feats and "Delete" not in spec_feats:
            input('Delete-delete')
            merged = Constituent(label=merged.label, part1=spec, part2=merged.part2.part2)
            # Core Head needs to be deleted
        else:
            merged = merged.part2
        self.out("Dephase(DeleteC)", merged)
        target_label = merged.label
        # Transfer phasehood to T and transfer complement
        if merged.is_unlabeled() or "Phi" in target_label:
            target_label = merged.part2.label

        transfer = find_next_head(left, target_label, label)
        if not transfer:
            transfer = find_next_head(right, target_label, label)
        return transfer, merged

    def remerge_if_can(self, merged, dephase=False):
        print('remerge_if_can')

        def list_builder(node, l):
            if node not in l:
                l.append(node)
                # Again it seems that anything deeper than spine is off-limits
                #if node.part1:
                #    l = list_builder(node.part1, l)
                if node.part2:
                    l = list_builder(node.part2, l)
            return l

        rstack = list_builder(merged, [])
        for current in list(rstack):
            if current.label != merged.label and "Phi" not in current.label:
                current_feats = expanded_features(current.get_head_features())
                if any([x.unvalued_and_alone() for x in current_feats]):
                    # if Current is already Merged to element that shares features with
                    # phase head, then Remerge isn't possible
                    # Find complement of Current
                    # See if complement shares features with phase head
                    for inner_current in rstack:
                        if current == inner_current.part1:  # shared_feats with complement
                            shared_feats = merged.shared_features(inner_current.part2)
                        elif current == inner_current.part2:  # shared_feats with complement
                            shared_feats = merged.shared_features(inner_current.part1)
                        else:
                            continue
                        if shared_feats:
                            remerge = None
                            # input('skipping :' + str(shared_feats))
                            if not dephase:
                                self.out("merge", """
                            Remerge of "%s" blocked by Remerge Condition (shared features)
                            """ % current.label)
                        else:
                            remerge = current
                            merged = Constituent(label="_", part1=remerge, part2=merged)
                            msg = "merge (due to uF) %s + %s" % (remerge.label, merged.label)
                            self.announce_derivation_step(merged, msg)
                            self.out("merge", msg)
                            self.out("Label(Head)", merged)
                        return merged, remerge
                    return merged, None
        return merged, None

    def unlabeled_move(self, merged):
        print('unlabeled_move')
        # I don't like this next move, looking forward to decide on current cycle:
        if self.lookforward_so:
            # External merge blocks internal merge
            if merged.part1.label in THETA_ASSIGNERS:
                if isinstance(self.lookforward_so, list):
                    lf_so = self.lookforward_so[0]  # look into substream
                else:
                    lf_so = self.lookforward_so
                if lf_so.label in DET_HEADS or \
                    (lf_so.label == "n" and has_part(lf_so.features, "uPerson")):  # = n_Expl
                    return merged
        if self.stack.is_main():
            self.stack.append(merged, duplicates=False)
        # Move an element within an unlabeled Merged Structure

        # find element in stack with phi-features and raise if possible
        remerge = None
        if merged.is_unlabeled():
            head = merged.part1
            head_feats = expanded_features(head.get_head_features())
            if has_part(head_feats, "iD", "iPerson"):
                # There's already a DP with phi-features here, so no need to merge
                # another DP with Phi
                return merged
            elif has_part(head_feats, "iQ", "iPerson"):
                # There's already a DP with phi-features here, so no need to merge
                # another DP with Phi
                return merged
            # Try looking into complement
            comp = merged.part2
            if comp.is_unlabeled():
                locus = comp.part1
                locus_features = expanded_features(locus.get_head_features())
                if has_part(locus_features, "iN", "uPerson") or \
                        has_part(locus_features, "iQ", "iPerson") or \
                        has_part(locus_features, "iD", "iPerson"):
                    remerge = locus
            elif "Phi" in comp.label:
                locus = comp.part1
                locus_features = expanded_features(locus.get_head_features())
            else:
                locus = comp
                locus_features = expanded_features(locus.get_head_features())
                if has_part(locus_features, "iN"):
                    remerge = locus
            if not remerge:
                if has_part(locus_features, "iD", "iPerson") or \
                        has_part(locus_features, "iQ", "iPerson"):
                    remerge = locus
        if remerge:
            merged = self.remerge(merged, remerge)
            self.announce_derivation_step([merged], "remerged previously merged element")
        else:
            merged, success = self.label_if_possible(merged)
            if success:
                self.announce_derivation_step([merged], "found label for unlabeled element")
        return merged

    def remerge(self, merged, remerge):
        def relabel_my_parent(current, chosen_one):
            """ Relabel the parent of remerged constituent """
            if chosen_one != current and chosen_one in current:
                current_feats = current.get_head_features()
                if not has_part(current_feats, "Root"):
                    if current.part1 == chosen_one:
                        current.label = current.part2.label
                    elif current.part2 == chosen_one:
                        current.label = current.part1.label
                    return True
            if current.part1 and relabel_my_parent(current.part1, chosen_one):
                return True
            return current.part2 and relabel_my_parent(current.part2, chosen_one)

        print('remerge (attempting to remerge)')
        if self.stack.is_sub():
            print("Do in substream999999")
            sys.exit()
        # just for curiosity
        self.out("merge", "merge (for labeling (remerge)) " + remerge.label + " + " + merged.label)
        if merged.part1.label == "vUnerg":
            sys.exit()

        merged, success = self.label_if_possible(merged)
        if success:
            self.announce_derivation_step([merged], "found label for unlabeled element")
        # Find new MergedLabel
        new_merged = Constituent(label=merged.label, part1=remerge, part2=merged)

        self.stack.append(remerge)
        self.stack.append(new_merged)
        new_merged, success = self.label_if_possible(new_merged)
        if success:
            self.announce_derivation_step([new_merged], "found label for unlabeled element")

        if new_merged.is_unlabeled():
            self.out("Label(None)", new_merged)
        else:
            self.out("Label(SharedFeats)", new_merged)
        relabel_my_parent(new_merged, remerge)
        self.stack.append(new_merged)
        return new_merged

    def label_if_possible(self, merged):
        """

        :param merged:
        :return:
        """
        # hmm.. here we have whole structure, but labeling function needs to know if given
        #  items are copies. It would be straightforward to flag those if we would be
        # analysing tree from top down, but labeling happens from bottom up. So we have to
        #  do it in two stages, first go top down to build a list of tuples, (item1, item2,
        #  is_copy1, is_copy2) and second to go through it in reverse.

        found_items = set()
        waiting_for_labeling = []
        def build_pairs_to_analyse(item):
            found_items.add(item)
            if item.is_unlabeled() and item.part1 and item.part2:
                p1_is_copy = item.part1 in found_items
                p2_is_copy = item.part2 in found_items
                waiting_for_labeling.append((item, p1_is_copy, p2_is_copy))
            if item.part1:
                build_pairs_to_analyse(item.part1)
            if item.part2:
                build_pairs_to_analyse(item.part2)

        build_pairs_to_analyse(merged)
        success = False

        for item, p1_is_copy, p2_is_copy in reversed(waiting_for_labeling):
            new_label = self.labeling_function(item.part1, item.part2, p1_is_copy, p2_is_copy)
            if new_label is not False:
                item.label = new_label
                success = True
        return merged, success

    def labeling_function(self, x, y, x_has_moved, y_has_moved):
        """ Compute label for SO that merges x, y
        :param x: Constituent
        :param y: Constituent
        :param x_has_moved: bool, analyse structure instead of using Copy-feature.
        :param y_has_moved: bool
        :return: label string or False
        """
        print('labeling_function')
        if x.is_unlabeled():
            elem1_feats = x.part1.get_head_features()
        else:
            elem1_feats = x.get_head_features()
        if y.is_unlabeled():
            elem2_feats = y.part1.get_head_features()
        else:
            elem2_feats = y.get_head_features()
        if not (elem1_feats and elem2_feats):
            return False
        if x.is_unlabeled() and y.is_unlabeled():
            return False
        elem1_feats = expanded_features(elem1_feats)
        elem2_feats = expanded_features(elem2_feats)
        if has_part(elem1_feats, "Root"):  # weak
            if has_part(elem1_feats, "iPerson", "iNumber", "iGender"):
                self.out("Label(Strengthened)", x.label)
                return x.label
            elif has_part(elem1_feats, "iPerson"):
                sys.exit()
        if x_has_moved and not y_has_moved:
            if has_part(elem2_feats, "Root") or has_part(elem1_feats, "Root"):  # weak
                if has_part(elem2_feats, "iPerson", "iNumber", "iGender"):
                    self.out("Label(Move)", y.label)
                    return y.label
            else:
                self.out("Label(Move)", y.label)
                return y.label
        elif y_has_moved and has_part(elem1_feats, "Root", "iPerson", "iNumber", "iGender"):
                # weak if Root
                self.out("Label(Move)", x.label)
                return x.label
        shared_feats = find_shared_features(elem1_feats, elem2_feats)
        if not shared_feats:
            # Check for strengthened element
            return False
        person_f = get_by_part(shared_feats, "iPerson")
        if person_f:
            if has_part(shared_feats, "iNumber", "iGender"):
                new_label = "Phi%s" % person_f.counter or ''
                self.out("Label(SharedFeats)", new_label)
                return new_label
            else:
                self.out("Label(SharedFeats)", "Per")
                return "Per"
        return False

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
        features = []
        for feat in features0:
            if feat in COUNTED_FEATURES:
                features.append(feat + str(self.feature_counter))
            elif feat in COUNTED_PHI_FEATURES:
                features.append(feat + str(self.phi_counter))
            else:
                features.append(feat)
        if synobj == 'C_Null':
            synobj = 'C'
        elif synobj == 'n_Expl':
            synobj = 'n'
        return Constituent(label=synobj, features=features)

    def check_features(self, x, y):
        print('check_features: ', x.label, y.label)
        # If X has uPhi, then uPhi are passed down the tree until they are checked
        x_feat_host = x.get_head()
        y_feat_host = y.get_head()
        assert x_feat_host and y_feat_host

        x_feats = expanded_features(x.get_head_features())
        y_feats = expanded_features(y.get_head_features(no_sharing=True))
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
            # we used to have "merged" here as parameter, now we have to cook one up for debug
            self.out("Label(Head)", Constituent(label=current_label, part1=x, part2=y))
        inherit = False

        # First thing is to collect unvalued phis from either x or y. First try x,
        # if it has impressive amount of unvalued features, then it is the feature giver.
        # Then y. If neither has enough, scoot off.
        unvalued_phis = []
        for f in x_feats:
            if f.name in ["Person", "Number", "Gender"] and f.unvalued_and_alone():
                unvalued_phis.append(f)
            elif f.name == "Case" and not f.unvalued_and_alone():
                unvalued_phis.append(f)
        if len(unvalued_phis) >= 3 or x.label in PHASE_HEADS:
            inherit = x
        if not inherit:
            for f in y_feats:
                if f.name in ["Person", "Number", "Gender"] and f.unvalued_and_alone():
                    unvalued_phis.append(f)
                elif f.name == "Case" and not f.unvalued_and_alone():
                    unvalued_phis.append(f)
            if len(unvalued_phis) >= 3:
                inherit = y
        if not inherit:
            x, y, remerge = self.feature_checking_function(x, y)
            assert(not remerge)
            return x, y, False, remerge

        # Pass features to those who:
        #
        # - Have Root-feature
        # - don’t have uPerson or iPerson
        # - are not already chosen for feature passing (we don't double-drive)
        # - have not iD or iN in features
        # - don’t have ”n” as previous item in stack (wtf?)
        # - bonus: have not transfered
        #
        # p. 27:
        # According to (19), a phase head passes its uninterpretable features (uFs) to its
        # complement X, if the complement X is unlicensed. Furthermore, X will pass these
        # uFs down to its complement Y, if Y is unlicensed, and so on. An unlicensed
        # complement is unlabeled.

        # (19) Feature inheritance (revised)
        # Uninterpretable features are passed to an unlicensed complement.

        # hm, hm. Model10 code seems to also allow labeled Roots to inherit features.

        #input('attempt feature passing for %s' % inherit.label)

        passed_items = []
        feats_passed = False
        prev_label = False  # block feature passage to nominal

        print('-------------')
        print('X:', x)
        print('Y:', y)
        print('stack: ', [x.label for x in reversed(self.stack)])
        for item in reversed(self.stack):
            print('   ---- ', item)

        def find_empty_root(node, previous_label):
            feats = expanded_features(node.get_head_features())
            found = False
            if has_part(feats, "Root"):
                go_on = True
                for item in ["uPerson", "iPerson", "iD", "iN"]:
                    if has_part(feats, item):
                        go_on = False
                        break
                if prev_label == "n":
                    go_on = False
                if go_on:
                    if node.is_labeled():
                        other_label = node.label
                    else:
                        if node.part1.is_labeled():
                            other_label = node.part1.label
                        elif node.part2.is_labeled():
                            other_label = node.part2.label
                        else:
                            print("error - can't find label9999")
                            sys.exit()

                    print('passing features to current: ', node)
                    input()
                    fhost = node.get_feature_giver()
                    print('fhost: ', fhost)
                    #input('passing success')
                    for item in unvalued_phis:
                        fhost.features.append(item)
                    self.out("PassFs", "Pass Features " + inherit.label + " to " + other_label)
                    self.out("FeaturesPassed", unvalued_phis)
                    self.inheritance_counter += 1
                    found = True
            if previous_label != "n":
                if node.part2 and find_empty_root(node.part2, node.label):
                    found = True
                if node.part1 and find_empty_root(node.part1, node.label):
                    found = True
            return found

        def find_empty_root_leaf(node, previous_label):
            found = False
            if node.is_leaf():
                if has_part(node.features, "Root"):
                    feats = expanded_features(node.features)
                    go_on = True
                    for item in ["uPerson", "iPerson", "iD", "iN"]:
                        if has_part(feats, item):
                            go_on = False
                            break
                    if previous_label == "n":
                        go_on = False
                    if go_on:
                        if node.is_labeled():
                            other_label = node.label
                        else:
                            if node.part1.is_labeled():
                                other_label = node.part1.label
                            elif node.part2.is_labeled():
                                other_label = node.part2.label
                            else:
                                print("error - can't find label9999")
                                sys.exit()

                        print('passing features to current: ', node)
                        print('previous_label:', previous_label)
                        input()
                        # input('passing success')
                        for item in unvalued_phis:
                            node.features.append(item)
                        self.out("PassFs", "Pass Features " + inherit.label + " to " + other_label)
                        self.out("FeaturesPassed", unvalued_phis)
                        self.inheritance_counter += 1
                        found = True

                previous_label = node.label
            else:
                previous_label, got_it = find_empty_root_leaf(node.part2, previous_label)
                if got_it:
                    found = True
                previous_label, got_it = find_empty_root_leaf(node.part1, previous_label)
                if got_it:
                    found = True
            return previous_label, found

        if inherit == x:
            spine = y
        else:
            spine = x
        print('with inherited features from ', inherit)
        print('attempting to look into ', spine)
        prev_label = ''
        while spine and False:
            current = spine
            if spine.part1:
                prev_label, found_it = find_empty_root_leaf(spine.part1, prev_label)
                if found_it:
                    feats_passed = True
            if spine.part2:
                spine = spine.part2
            else:
                spine = None
                prev_label, found_it = find_empty_root_leaf(current, prev_label)
                if found_it:
                    feats_passed = True
            prev_label = current.label

        while False and spine:
            print('*putter-putter*')
            if not (spine.part1 and spine.part2):
                comp = spine
                spine = None
            elif spine.part1.is_unlabeled() and spine.part2.is_unlabeled():
                print('both children unlabeled. too strange.')
                sys.exit()
            elif spine.part1.is_unlabeled():
                comp = spine.part2
                spine = spine.part1
            elif spine.part2.is_unlabeled():
                comp = spine.part1
                spine = spine.part2
            elif False and not spine.part2.transfered:
                comp = spine.part1
                spine = spine.part2
            else:
                comp = spine.part1
                spine = None
            if comp:
                print('looking into "%s"' % comp)
                did_it = find_empty_root(comp, '')
                if did_it:
                    feats_passed = True
                    #input('found some ^')
                else:
                    #input('no win this time')
                    pass

        def pass_features(current, ignored, passed, prev_label):
            if current == ignored: #or not (current.part1 and current.part2):
                pass
            elif not current.stacked:
                pass
            elif prev_label == "n" and False: # (not parent) and
                prev_label = current.label
            elif current in passed_items:
                prev_label = current.label
            else:
                prev_label = current.label
                current_feats = expanded_features(current.get_head_features())
                if has_part(current_feats, "Root"):
                    go_on = True
                    for item in ["uPerson", "iPerson", "iD", "iN"]:
                        if has_part(current_feats, item):
                            go_on = False
                            break
                    if go_on:
                        passed_items.append(current)
                        if current.is_labeled():
                            other_label = current.label
                        else:
                            if current.part1.is_labeled():
                                other_label = current.part1.label
                            elif current.part2.is_labeled():
                                other_label = current.part2.label
                            else:
                                print("error - can't find label9999")
                                sys.exit()
                        print('-------------')
                        print('X:', x)
                        print('Y:', y)

                        print('passing features to current: ', current)
                        fhost = current.get_feature_giver()
                        print('fhost:', fhost)
                        #input('passing success')
                        for item in unvalued_phis:
                            fhost.features.append(item)
                        self.out("PassFs", "Pass Features " + inherit.label + " to " + other_label)
                        self.out("FeaturesPassed", unvalued_phis)
                        self.inheritance_counter += 1
                        passed = True
            return ignored, passed, prev_label

        if True:
            print('---------Stack-based algo--------')
            print('unvalued phis looking for who should inherit them:', unvalued_phis)
            if self.stack.is_main():
                temp_stack = list(self.stack.main_stack)
            else:
                temp_stack = list(self.stack.sub_stack)
            while temp_stack:
                current = temp_stack.pop()
                ignored, feats_passed, prev_label = pass_features(current, x, feats_passed, prev_label)
        if feats_passed:
            self.announce_derivation_step([x, y], "passed features %s" % unvalued_phis)
        x, y, remerge = self.feature_checking_function(x, y)
        y, success = self.label_if_possible(y)
        if success:
            self.announce_derivation_step([x, y], "found label for unlabeled element")
        return x, y, feats_passed, remerge

    def feature_checking_function(self, x, y):
        """

        :param x:
        :param y:
        :return:
        """

        def make_checking_pairs(unvalued_features, probe_feats):
            unvalued = [p for p in probe_feats if p.unvalued_and_alone()]
            chkd = []
            for unvalued_feature in unvalued:
                for u_goal in unvalued_features:
                    if u_goal.name == unvalued_feature.name and u_goal.ifeature:
                        chkd.append((unvalued_feature, u_goal))
            return chkd

        def list_builder(node, l):
            if node not in l:
                l.append(node)
                # Again it seems that anything deeper than spine is off-limits
                if node.part1:
                    l = list_builder(node.part1, l)
                if node.part2:
                    l = list_builder(node.part2, l)
            return l

        print('feature_checking_function: ', x.label, y.label)
        if self.stack.is_main() and not self.stack:
            return x, y, None
        x_feat_giver = x.get_head()
        y_feat_giver = y.get_head()
        x_feats = x_feat_giver.features
        y_feats = y_feat_giver.features
        checked_feats = []
        # XFeats probe
        if "MergeF" in x_feats:
            mf = get_by_part(x_feats, "MergeF")
            x_feats.remove(mf)
        exp_x_feats = expanded_features(x_feats)
        exp_y_feats = expanded_features(y_feats)
        unvalued_phi = bool(has_part(exp_x_feats, "uPerson", "uNumber", "uGender"))
        unvalued_features = [mf for mf in exp_x_feats if mf.unvalued_and_alone() or
                             (mf.name == "Case" and unvalued_phi) or
                             (mf.name == "Scp" and mf.ifeature)]
        if not unvalued_features:
            return x, y, None
        remerge = None
        unvalued_feature_stack = list(sorted(unvalued_features)) # oh the ordering matters
        tree_as_list = list_builder(x, [])
        tree_as_list = list_builder(y, tree_as_list)

        while unvalued_feature_stack:
            uf = unvalued_feature_stack.pop()
            goal = Feature(name=uf.name, ifeature=True, value=uf.value)
            for stack_top in tree_as_list:
                feat_checked = False
                if stack_top == x:
                    continue
                if "Phi" in stack_top.label:
                    # Don't look at the features of an element with shared phi-features
                    # This is maybe an imperfection
                    stack_top_feats = []
                    stack_top_feat_base = stack_top
                else:
                    stack_top_feats = expanded_features(stack_top.get_head_features())
                    stack_top_feat_base = stack_top.get_feature_giver()
                if stack_top_feats is None:
                    sys.exit()
                uf_present = False
                # This can match only two unvalued, but uf:s can also be iScp:s or Cases
                if uf.unvalued_and_alone():
                    unvalued_top_feats = [feat for feat in stack_top_feats if
                                          feat.unvalued_and_alone()]
                    for top_feat in unvalued_top_feats:
                        uf_present = True
                        if top_feat != uf and top_feat.name == uf.name: # both are unvalued
                            stack_top_feat_base.features.remove(top_feat)
                            stack_top_feat_base.features.append(uf)
                            self.out("Unification", uf)
                if uf.name == "Q" or uf.name == "Top":
                    uf_present = True  # it doesn't matter if a potential goal has any uFs
                    # uFs aren't needed to be visible.
                if has_part(stack_top_feats, goal):
                    if not (uf_present and stack_top.is_labeled()):
                        continue
                    if goal.name == "Top" and goal.ifeature:  # iTop
                        # This one never seems to activate
                        top_chkd = make_checking_pairs(unvalued_features, stack_top_feats)
                        for old_top_f, new_top_f in top_chkd:
                            old_top_f.value_with(new_top_f)
                            if old_top_f not in checked_feats:
                                checked_feats.append(old_top_f)
                            if self.stack.is_sub():
                                print("Check in substream999999")
                                sys.exit()
                        remerge = stack_top
                    elif goal.name == "Q" and goal.ifeature:  # iQ
                        top_chkd = make_checking_pairs(unvalued_features, stack_top_feats)
                        for old_top_f, new_top_f in top_chkd:
                            old_top_f.value_with(new_top_f)
                            if old_top_f not in checked_feats:
                                checked_feats.append(old_top_f)
                            if self.stack.is_sub():
                                print("Check in substream999999")
                                sys.exit()
                        remerge = stack_top

                    # Remerge due to a need to share Q features
                    for top_f in stack_top_feats:
                        if goal in top_f:
                            uf.value_with(top_f)

                    feat_checked = True
                    checked_feats.append(uf)
                    # Check uScp as a reflex of uQ checking
                elif uf.name == "Case" and uf.value:
                    checked_feats.append(uf)
                    # hmm... Case disappears from original place and is active only in new place.
                    x.replace_within(uf, None)
                    y.replace_within(uf, None)

                    # I can't accept it?
                    uf.inactive = True
                    for y_feat in exp_y_feats:
                        if y_feat.name == "Case" and y_feat.unvalued_and_alone():
                            print('replace in Y: ', y_feat, uf)
                            y_feat.value_with(uf)
                    feat_checked = True
                elif uf.name == "Phi":
                    if has_part(stack_top_feats, "iPerson"):
                        u_phi = get_by_part(x_feats, "Phi")
                        if u_phi.unvalued_and_alone():
                            for top_f in stack_top_feats:
                                for match_f in ["Person", "Number", "Gender"]:
                                    if top_f.name == match_f and top_f.ifeature:
                                        u_phi.value_with(top_f)
                                        break
                                if top_f.name == 'Case' and top_f.unvalued_and_alone():
                                    u_phi.value_with(top_f)

                    self.out("PhiPassing", "uPhi")
                    feat_checked = True
                    self.inheritance_counter += 1
                if feat_checked:
                    break

        if checked_feats:
            self.out("CheckedFeatures", checked_feats)
            self.feature_check_counter += len(checked_feats)
            self.announce_derivation_step([x, y], "checked features")
        return x, y, remerge

# "../Languages/Japanese/DisWarn.txt"

if __name__ == "__main__":
    import ProduceOutput
    if len(sys.argv) > 1:
        filename = int(sys.argv[1])
    else:
        filename = "./POP.txt"
    file = open(filename, 'r')
    input_data = file.readlines()
    file.close()
    t = time.time()
    print('*****')
    print('*****')
    print('*****')
    print('*MOD*')
    print('*****')
    print('*****')
    print('*****')
    print('*****')

    out = ProduceOutput.ProduceFile('ignore/new/')
    a = Generate(out_writer=out)
    a.load_data(input_data, start, end)
    out.close()
    print(time.time() - t)
