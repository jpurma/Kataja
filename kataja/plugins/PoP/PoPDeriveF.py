#######################################################
###Derivation Generator - Problems of Projection Version
## Rewriting Jason Ginsburg's computer model for PoP,
# http://www.osaka-kyoiku.ac.jp/~jginsbur/MinimalistModeling.html
# Jukka Purma
#########################################################

import sys
import time

try:
    from PoP.Lexicon import DET_HEADS, PHASE_HEADS, THETA_ASSIGNERS, SHARED_LABELS, \
        ADJUNCT_LABELS, COUNTED_FEATURES, COUNTED_PHI_FEATURES, LEXICON
    from PoP.Constituent import Constituent
    from PoP.Feature import Feature, has_part, get_by_part
    from kataja.syntax.SyntaxState import SyntaxState
    in_kataja = True
except ImportError:
    from Lexicon import DET_HEADS, PHASE_HEADS, THETA_ASSIGNERS, SHARED_LABELS, \
        ADJUNCT_LABELS, COUNTED_FEATURES, COUNTED_PHI_FEATURES, LEXICON
    from Constituent import Constituent
    from Feature import Feature, has_part, get_by_part
    in_kataja = False

start = 1
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
        self.transfer_counter = 0
        self.feature_check_counter = 0
        self.lookforward_so = None
        self.over_counter = 0
        self.dumpfile = None
        self.forest = None
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
        if not self.out_writer:
            return
        self.out_writer.push(first, second, third)

    def dump_to_file(self, synobj):
        if not self.dumpfile:
            self.dumpfile = open('deriveF.log', 'w')
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
        self.transfer_counter = 0
        self.feature_check_counter = 0
        self.lookforward_so = None
        self.so_list = build_synobj_lists(target_example, [])
        self.forest = forest
        self.spine = None
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
            self.label_if_possible(selected)
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
            if not substream_spine:
                self.announce_derivation_step(x, msg="Substream select " + x.label)
            substream_spine = self.merge_so(x, substream_spine)
        self.stack.end_sub_stream()
        print('<<<<<  ended substream')
        # merge substream back to main stream:
        self.out("MainStream", True)
        msg = "merge " + spine.label + " + " + substream_spine.label
        self.out("merge", msg)
        self.spine = self.merge(spine, substream_spine)
        self.announce_derivation_step(msg=msg)
        return self.spine

    def announce_derivation_step(self, spine=None, msg=''):
        if self.forest:
            if spine and self.stack.is_sub():
                so_list = [spine, self.spine]
            elif spine:
                so_list = [spine]
            elif self.spine:
                so_list = [self.spine]
            else:
                so_list = []
            if self.lookforward_so:
                num = self.so_list + [self.lookforward_so]
            else:
                num = []
            syn_state = SyntaxState(tree_roots=so_list, numeration=num,
                                    msg=msg)
            self.forest.add_step(syn_state)

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
            self.announce_derivation_step(spine, "select " + x.label)
            return x
        else:
            msg = "merge " + x.label + " + " + spine.label
            self.out("merge", msg)
            spine = self.merge(x, spine)
            if self.stack.is_main():
                self.spine = spine
            self.announce_derivation_step(spine, msg)
            print('finished merge: ', spine)
            #self.dump_to_file(spine, self.over_counter)
            print('---- kataja string: ----')
            print(spine.tex_tree(self.stack.main_stack))
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
        print('++ stack append in merge1 ')
        self.stack.append(x, duplicates=False)
        print('++ stack append in merge2 ')
        self.stack.append(y, duplicates=False)
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
            # ordering doesn't matter, but this makes things easier
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
            merged = Constituent(label="_", part1=part1, part2=part2)

            self.out("Label(None)", merged)
            # If unlabled - then remerge next available element with phi-features
            merged = self.unlabeled_move(merged)
        if merged.label in PHASE_HEADS:
            merged = self.transfer_check(merged)
        return merged

    def remerge_back(self, merged, remerge):
        print('remerge_postponed')
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
        ## Adding a Copy 1 (not in Remerge) ##
        remerge = remerge.demote_to_copy()

        #remerge_feats = remerge.get_head_features()
        #new_remerge_feats = list(remerge_feats)
        #new_remerge_feats.append(Feature(name="Copy"))

        if self.stack.is_sub():
            print("Remerging in in substream999999")
            sys.exit()
        #merged.replace_within(remerge_feats, new_remerge_feats)
        #self.stack.replace(remerge_feats, new_remerge_feats)
        msg = "merge (for labeling) " + merged.label + " + " + remerge.label
        self.out("merge", msg)
        merged = Constituent(label=label, part1=remerge, part2=merged)
        self.merge_counter += 1
        self.announce_derivation_step(merged, msg)
        self.out("Label(SharedFeats)", merged)
        merged = self.label_if_possible(merged)
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
        if self.stack.is_main() and merged.label == "v*":
            success = self.dephase_and_transfer(merged)
            if success:
                return success

        if merged.label in PHASE_HEADS:  # This is last resort
            merged_feats = merged.get_head_features()
            transfer = None

            if "Delete" in merged_feats:  # Dephase because C is deleted
                transfer, merged = self.dephase_deleted_c(merged)
                remerge = None
                if self.stack.is_main():
                    merged, remerge = self.remerge_if_can(merged, dephase=True)
                self.out("Transfer", transfer)  # Transfer actually does nothing.
                #print('******** Transfer ********')
                self.stack.clear_main_stack()
                if remerge:
                    #print('++ stack append remerge, in transfer_check')
                    self.stack.append(remerge, force_main=True)
                if self.stack.is_sub():
                    #print('++ substack append merged, in transfer_check')
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
            self.stack.clear_main_stack()
            if remerge:
                print('++ stack append remerge 2, in transfer_check')
                self.stack.append(remerge, force_main=True)
        if self.stack.is_sub():
            print('++ stack append merged 2, in transfer_check')
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
            if const.stacked and any(x.name == "Root" for x in const.get_head_features()):
                return const
            # (jukka) We are looking for v:s but if we go into branches we hit into n:s.
            # let's try to not go into branches. another option would be to directly demand 'v' in
            # label
            #if const.part1:
            #    found = find_closest_root(const.part1)
            #    if found:
            #        return found
            if const.part2:
                return find_closest_root(const.part2)
            return None

        # struct-based
        current = find_closest_root(merged)
        # stack-based:
        # current = None
        # for const in reversed(self.stack):
        #    if any(x.name == "Root" for x in const.get_head_features()):
        #        current = const
        #        break
        if current:
            # Transfer the complement of v
            assert current.is_labeled()
            remerge = current
            transfer = remerge.part2
            print('-- stack cut in dephase and transfer')
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
            self.announce_derivation_step(merged, "Dephase v")
            self.out("Dephase v", merged)
            self.out("Transfer", transfer)
            # Check to see if Remerge results in labeling
            if self.stack.is_sub():
                print('++ stack append merged, in dephase and transfer')
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
        merged_feats = merged.get_head_features()
        spec = merged.part1
        spec_feats = spec.get_head_features()
        if spec_feats != merged_feats and "Delete" not in spec_feats:
            merged = Constituent(label=merged.label, part1=spec, part2=merged.part2.part2)
            # Core Head needs to be deleted
        else:
            merged = merged.part2
        self.announce_derivation_step(merged, "Dephase(DeleteC)")
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
                                remerge = current.demote_to_copy()
                                merged = Constituent(label="_", part1=remerge, part2=merged)
                                #remerge_feats = remerge.get_head_features()
                                #new_remerge_feats = remerge_feats.copy()
                                #new_remerge_feats.append(Feature(name="Copy"))
                                #remerge.replace_within(remerge_feats, new_remerge_feats)
                                msg = "merge (due to uF) %s + %s" % (remerge.label,
                                                                     merged.label)
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
                    print('external merge blocks internal merge')
                    return merged
        if self.stack.is_main():
            print('++ stack append in unlabeled_move')
            self.stack.append(merged)
        # Move an element within an unlabeled Merged Structure

        # find element in stack with phi-features and raise if possible
        remerge = None
        if merged.is_unlabeled():
            head = merged.part1
            head_feats = head.get_head_features()
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
                locus_features = locus.get_head_features()
                if has_part(locus_features, "iN", "uPerson") or \
                        has_part(locus_features, "iQ", "iPerson") or \
                        has_part(locus_features, "iD", "iPerson"):
                    remerge = locus
            elif "Phi" in comp.label:
                locus = comp.part1
                locus_features = locus.get_head_features()
            else:
                locus = comp
                locus_features = locus.get_head_features()
                if has_part(locus_features, "iN"):
                    remerge = locus
            if not remerge:
                if has_part(locus_features, "iD", "iPerson") or \
                        has_part(locus_features, "iQ", "iPerson"):
                    remerge = locus
        if remerge:
            merged = self.remerge(merged, remerge)
        else:
            merged = self.label_if_possible(merged)
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
        remerge = remerge.demote_to_copy()
        #new_remerge_feats = new_remerge.get_head_features()
        #new_remerge_feats.append(Feature(name="Copy"))
        #assert(remerge == merged.part2.part1 or remerge == merged.part2) # can be false,
        # just for curiosity
        #merged.replace_within(remerge, new_remerge)  # brr, brrrr, brrrr
        self.out("merge", "merge (for labeling) " + remerge.label + " + " + merged.label)
        if merged.part1.label == "vUnerg":
            sys.exit()

        merged = self.label_if_possible(merged)
        # Find new MergedLabel
        new_merged = Constituent(label=merged.label, part1=remerge, part2=merged)
        self.announce_derivation_step(merged, "merge (for labeling)")

        #print('++ stack append remerge, in remerge')
        self.stack.append(remerge)
        #print('++ stack append new_merged, in remerge:', new_merged.label)
        self.stack.append(new_merged)
        new_merged = self.label_if_possible(new_merged)
        if new_merged.is_unlabeled():
            self.out("Label(None)", new_merged)
        else:
            self.out("Label(SharedFeats)", new_merged)
            print("Label via shared FEatures2", new_merged)
            print("\n")
        relabel_my_parent(new_merged, remerge)

        #print('++ stack append new_merged 2, in remerge, replaces previous', new_merged.label)
        self.stack.append(new_merged)
        return new_merged

    def label_if_possible(self, merged):
        """

        :param merged:
        :return:
        """
        def check_labeling(const, merged):
            if const.part2:
                check_labeling(const.part2, merged)
            if const.part1:
                check_labeling(const.part1, merged)
            if const.is_unlabeled() and const.part1 and const.part2:
                #print('attempt labeling for ', const)
                new_label = self.labeling_function(const.part1, const.part2)
                if new_label is not False:
                    const.label = new_label
        check_labeling(merged, merged)
        return merged

    def labeling_function(self, x, y):
        """ Compute label for SO that merges x, y
        :param x: Constituent
        :param y: Constituent
        :return: label string or False
        """
        print('labeling_function for ', x.label, y.label)
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
        #print(elem1_feats)
        #print(elem2_feats)
        #input()

        if not (elem1_feats and elem2_feats):
            print('1: no elem1 and elem2 features')
            return False
        if x.is_unlabeled() and y.is_unlabeled():
            print('2: both are unlabeled')
            return False
        if has_part(elem1_feats, "Root"):  # weak
            if has_part(elem1_feats, "iPerson", "iNumber", "iGender"):
                self.out("Label(Strengthened)", x.label)
                print('3: iPerson, iNumber or iGender')
                return x.label
            elif has_part(elem1_feats, "iPerson"):
                print("elem1 has only iPerson of phi")
                #print("Merged", x, y)
                sys.exit()
        if "Copy" in elem1_feats:
            if "Copy" not in elem2_feats:
                if has_part(elem2_feats, "Root") or has_part(elem1_feats, "Root"):  # weak
                    if has_part(elem2_feats, "iPerson", "iNumber", "iGender"):
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
            if has_part(elem1_feats, "Root", "iPerson", "iNumber", "iGender"):
                self.out("Label(Move)", x.label)
                print('7: elem2 is Copy, elem1 is Root and phi')
                return x.label
        shared_feats = [ef for ef in elem1_feats if ef in elem2_feats]
        if not shared_feats:
            # Check for strengthened element
            print('8: no shared feats (return False)')
            return False
        person_f = get_by_part(shared_feats, "iPerson")
        if person_f:
            if has_part(shared_feats, "iNumber", "iGender"):
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

    @staticmethod
    def get_head_features(x, y):
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
                y_feats = y.features
            else:
                y_feats = y.part1.get_head_features()
        elif y.part2 and y.part2.is_unlabeled():
            print("problem")
            print("Y", y)
            sys.exit()
        else:
            y_feats = y.get_head_features()
        return x_feats, y_feats

    @staticmethod
    def get_feature_givers(x, y):
        """

        :param x:
        :param y:
        :return:
        """
        x_base = x
        y_base = y
        if x.is_unlabeled():
            x_base = x.part1
        if y.is_unlabeled():
            y_base = y.part1
        elif y.label in SHARED_LABELS:
            if y.is_leaf():
                y_base = y
            else:
                y_base = y.part1
        elif y.part2 and y.part2.is_unlabeled():
            print("problem")
            print("Y", y)
            sys.exit()
        return x_base.get_feature_giver(), y_base.get_feature_giver()

    def check_features(self, x, y):
        print('check_features: ', x.label, y.label)
        # If X has uPhi, then uPhi are passed down the tree until they are checked
        x_feat_host, y_feat_host = self.get_feature_givers(x, y)
        assert x_feat_host and y_feat_host

        x_feats, y_feats = self.get_head_features(x, y)
        print('x_feats (expanded):', x_feats)
        print('y_feats (expanded):', y_feats)
        #input()

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
        unvalued_phis = []
        for f in x_feats:
            if f.name in ["Person", "Number", "Gender"] and f.unvalued:
                unvalued_phis.append(f)
            elif f.name == "Case" and not f.unvalued:
                unvalued_phis.append(f)
        if len(unvalued_phis) >= 3 or x.label in PHASE_HEADS:
            inherit = x
        if not inherit:
            for f in y_feats:
                if f.name in ["Person", "Number", "Gender"] and f.unvalued:
                    unvalued_phis.append(f)
                elif f.name == "Case" and not f.unvalued:
                    unvalued_phis.append(f)
            if len(unvalued_phis) >= 3:
                inherit = y
        if not inherit:
            x, y, remerge = self.feature_checking_function(x, y)
            return x, y, False, remerge

        # pass feats down the tree
        passed_items = []
        feats_passed = False
        prev_label = False  # block feature passage to nominal

        def pass_features(current, ignored, feats_passed, prev_label, recursive=True, parent=None):
            cannot = False
            if current == ignored: #or not (current.part1 and current.part2):
                print('ignore x: ', current.label)
                cannot = True
            elif not current.stacked:
                #print('not stacked: ', current.label)
                cannot = True
            elif prev_label == "n": # (not parent) and
                prev_label = current.label
                cannot = True
                print('skip: ', current.label, current.get_head_features())
            elif current in passed_items:
                cannot = True
                prev_label = current.label
                print('passed already: ', current.label, current.get_head_features())
            elif parent and ((parent.part1 is current and parent.part2.label == 'n') or (parent.part2 is current and parent.part1.label == 'n')):
                cannot = True
                print("sibling of 'n': ", current.label, current.get_head_features())
            else:
                prev_label = current.label
                #if current.label == 'n':

                    #print('current:', current)
                current_feats = current.get_head_features()
                print('stack_label: ', current.label, current_feats)
                if has_part(current_feats, "Root"):
                    go_on = True
                    for item in ["uPerson", "iPerson", "iD", "iN"]:
                        if has_part(current_feats, item):
                            go_on = False
                            break
                    if go_on:
                        print('go_on')
                        passed_items.append(current)
                        #assert(current not in x)
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
                        fhost = current.get_feature_giver()
                        for item in unvalued_phis:
                            fhost.features.append(item)
                        self.out("PassFs", "Pass Features " + inherit.label + " to " + other_label)
                        self.out("FeaturesPassed", unvalued_phis)
                        self.inheritance_counter += 1
                        feats_passed = True
            if recursive:

                if current.part1 and current.part2:
                    if current.part1.label == current.label:
                        ignored, feats_passed, prev_label = pass_features(current.part2, ignored, feats_passed, prev_label, parent=current)
                        ignored, feats_passed, prev_label = pass_features(current.part1, ignored, feats_passed, prev_label, parent=current)
                    else:
                        ignored, feats_passed, prev_label = pass_features(current.part1, ignored, feats_passed, prev_label, parent=current)
                        ignored, feats_passed, prev_label = pass_features(current.part2, ignored, feats_passed, prev_label, parent=current)
            return ignored, feats_passed, prev_label

        print('******************=======------- Feature check ------======*****')
        #print('x:', x)
        #print('y:', y)
        if self.stack.is_main():
            temp_stack = list(self.stack.main_stack)
        else:
            temp_stack = list(self.stack.sub_stack)
        def find_item(item, temp_stack):
            #if item in temp_stack:
            #    print('stack head')
            #else:
            #    print('item in tree, but not stack head', item)
            if item.stacked:
                print(item.label, item.get_head_features())
                if item not in temp_stack:
                    print('marked stacked, but not there.')
                    assert False

            if item in temp_stack:
                for otter in temp_stack:
                    if otter == item and otter is not item:
                        print('%s is not the same in stack and tree' % item)
                        #input()
            if item.part1 and item.part2:
                if item.part1.label == item.label:
                    find_item(item.part2, temp_stack)
                    find_item(item.part1, temp_stack)
                else:
                    find_item(item.part1, temp_stack)
                    find_item(item.part2, temp_stack)
        print('-------- SO ---------')
        find_item(x, temp_stack)
        find_item(y, temp_stack)

        #print('-------- stack ---------')
        #for item in reversed(temp_stack):
        #    print(item.label, item.get_head_features())

        so = False
        if so:
            print('--------SO-based algo-------')
            if inherit == x:
                ignored, feats_passed, prev_label = pass_features(y, x, feats_passed, prev_label)
            else:
                ignored, feats_passed, prev_label = pass_features(x, x, feats_passed,
                                                              prev_label)

        if not so:
            print('---------Stack-based algo--------')
            print('unvalued phis looking for who should inherit them:', unvalued_phis)
            if self.stack.is_main():
                temp_stack = list(self.stack.main_stack)
            else:
                temp_stack = list(self.stack.sub_stack)
            c = 0
            while temp_stack:
                current = temp_stack.pop()
                print(c)
                ignored, feats_passed, prev_label = pass_features(current, x, feats_passed, prev_label, recursive=False)
                c += 1
        x, y, remerge = self.feature_checking_function(x, y)
        y = self.label_if_possible(y)
        return x, y, feats_passed, remerge

    def feature_checking_function(self, x, y):
        """

        :param x:
        :param y:
        :return:
        """

        def make_checking_pairs(unvalued_features, probe_feats):
            unvalued = [p for p in probe_feats if p.unvalued]
            chkd = []
            for unvalued_feature in unvalued:
                for u_goal in unvalued_features.copy():
                    if u_goal.name == unvalued_feature.name and u_goal.ifeature:
                        chkd.append((unvalued_feature, u_goal))
            return chkd

        print('feature_checking_function: ', x.label, y.label)
        if self.stack.is_main() and not self.stack:
            print('quick escape! ', type(x), type(y))
            return x, y, None
        x_feat_giver, y_feat_giver = self.get_feature_givers(x, y)
        x_feats = x_feat_giver.features
        y_feats = y_feat_giver.features
        checked_feats = []
        # XFeats probe
        if "MergeF" in x_feats:
            mf = get_by_part(x_feats, "MergeF")
            x_feats.remove(mf)
        unvalued_phi = bool(has_part(x_feats, "uPerson", "uNumber", "uGender"))
        unvalued_features = [mf for mf in x_feats if mf.unvalued or
                                                     (mf.name == "Case" and unvalued_phi) or
                                                     (mf.name == "Scp" and mf.ifeature)]
        print('x_feats:' , x_feats)
        print('y_feats:' , y_feats)
        print('unvalued_features: ', unvalued_features)
        if not unvalued_features:
            print('-- no unvalued features, escaping feature_checking_function --')
            return x, y, None
        ###########################
        temp_stack = list(self.stack)
        remerge = None
        new_x_feats = []
        unvalued_feature_stack = sorted(list(unvalued_features))
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
                    top_feats = []
                else:
                    top_feats = stack_top.get_head_features()
                if top_feats is None:
                    sys.exit()
                uf_present = False
                # This can match only two unvalued, but uf:s can also be iScp:s or Cases
                if uf.unvalued:
                    utop_feats = [feat for feat in top_feats if feat.unvalued]
                    for top_feat in utop_feats:
                        uf_present = True
                        if top_feat != uf and top_feat.name == uf.name: # both are unvalued
                            print('unification possible: %s -> %s' % (top_feat, uf))
                            top_feats.remove(top_feat)
                            top_feats.append(uf)
                            self.stack.replace(top_feat, uf)
                            stack_top.replace_within(top_feat, uf)
                            x.replace_within(top_feat, uf)
                            y.replace_within(top_feat, uf)
                            self.out("Unification", uf)
                if uf.name == "Q" or uf.name == "Top":
                    uf_present = True  # it doesn't matter if a potential goal has any uFs
                    # uFs aren't needed to be visible.
                if has_part(top_feats, goal):
                    labeled = stack_top.is_labeled()
                    if uf_present:
                        if not labeled:
                            pass
                        elif goal.name == "Top" and goal.ifeature:
                            # This one never seems to activate
                            assert False
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
                                    checked_feats.append(old_top_f)
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
                                copy_f = get_by_part(remerge_feats, "Copy")
                                remerge_feats.remove(copy_f)
                                # print(self.remerge)
                        elif "iQ" in goal:
                            top_chkd = make_checking_pairs(unvalued_features, top_feats)
                            for old_top_f, new_top_f in top_chkd:
                                print('iQ replace')
                                stack_top.replace_within(old_top_f, new_top_f)
                                x.replace_within(old_top_f, new_top_f)
                                y.replace_within(old_top_f, new_top_f)
                                if old_top_f not in checked_feats:
                                    checked_feats.append(old_top_f)
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
                                copy_f = get_by_part(remerge_feats, "Copy")
                                remerge_feats.remove(copy_f)
                                print("self.Remerge111", remerge)
                                print("\n")
                                # Find highest instance in derivation and add "Copy"

                        # Remerge due to a need to share Q features
                        if labeled:
                            #print('goal in top feats, raise feature from top_f to uf')
                            for top_f in top_feats:
                                if goal in top_f:
                                    print('replace ', uf, ' with ', top_f)
                                    x.replace_within(uf, top_f)
                                    y.replace_within(uf, top_f)
                                    self.stack.replace(uf, top_f)
                            feat_checked = True
                            checked_feats.append(uf)
                            # Check uScp as a reflex of uQ checking
                elif uf.name == "Case" and uf.value:
                    checked_feats.append(uf)
                    print('remove Case ', uf)
                    x.replace_within(uf, None)
                    y.replace_within(uf, None)
                    self.stack.replace(uf, None, main_only=True)
                    #for i, item in enumerate(self.stack):
                    #    print(i, item)
                    #    print('')
                    #raise hell
                    for y_feat in y_feats:
                        if y_feat.name == "Case" and y_feat.unvalued:
                            print('... but put it in y to replace this: ', y_feat)
                            y.replace_within(y_feat, uf)
                            self.stack.replace(y_feat, uf)
                    feat_checked = True
                elif uf.name == "Phi":
                    if has_part(top_feats, "iPerson"):
                        u_phi = get_by_part(x_feats, "Phi")
                        if u_phi.unvalued:
                            x_feats.remove(u_phi)
                        for top_f in top_feats:
                            if any([tf in top_f for tf in ["iPerson", "iNumber", "iGender",
                                                           "uCase"]]):
                                print('add feature to x_feats ', top_f)
                                x_feats.append(top_f)
                    self.out("PhiPassing", "uPhi")
                    feat_checked = True
                    self.inheritance_counter += 1
                if feat_checked:
                    print('checked ok')
                    break

        if checked_feats:
            self.out("CheckedFeatures", checked_feats)
            self.feature_check_counter += len(checked_feats)
        print('---check features func ends ---')
        return x, y, remerge

# "../Languages/Japanese/DisWarn.txt"

if __name__ == "__main__":
    import ProduceOutput
    if len(sys.argv) > 1:
        filename = int(sys.argv[1])
    else:
        filename = "./POP.txt"
    f = open(filename, 'r')
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

    out = ProduceOutput.ProduceFile('ignore/new/')
    a = Generate(out_writer=out)
    a.load_data(input_data, start, end)
    out.close()
    print(time.time() - t)
