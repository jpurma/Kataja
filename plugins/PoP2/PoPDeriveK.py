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

start = 1
end = 10

class Generate:
    def __init__(self, out_writer=None):

        self.out_writer = out_writer
        self.so_list = []
        self.phi_counter = 0
        self.feature_counter = 0
        self.in_main = True
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
        #self.dump_to_file(selected)

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
        self.in_main = False
        self.out("SubStream", True)
        substream_spine = None

        while synobjlist:
            x = synobjlist.pop()
            substream_spine = self.merge_so(x, substream_spine)
        self.in_main = True
        print('<<<<<  ended substream')
        # merge substream back to main stream:
        self.out("MainStream", True)
        self.out("merge", "merge " + spine.label + " + " + substream_spine.label)
        self.spine = self.grand_cycle(spine, substream_spine)
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
            if self.in_main:
                self.workspace = parts
            else:
                self.sub_workspace = parts
        if self.lookforward_so:
            num = self.so_list + [self.lookforward_so]
        else:
            num = []
        if self.in_main:
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
            if self.in_main:
                self.spine = x
            return x
        else:
            msg = "merge " + x.label + " + " + spine.label
            self.out("merge", msg)
            spine = self.grand_cycle(x, spine)
            if self.in_main:
                self.spine = spine
            print('finished merge: ', spine)
            print('---- kataja string: ----')
            #print(spine.tex_tree())
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
        passed_features = None
        self.announce_derivation_step([x, y], "selected '%s', '%s' for merge" % (x.label, y.label))

        # Before merge
        # 1. Pass features downwards
        unvalued_phis, passer = self.can_pass_features(x, y)
        if passer:
            passed_features = self.pass_features(passer, unvalued_phis, x, y)
            if passed_features:
                self.announce_derivation_step([x, y], "passed features %s" % unvalued_phis)
        # 2. Check features
        postponed_remerge, checked_feats = self.check_features(x, y)
        if checked_feats:
            self.announce_derivation_step([x, y], "checked features: %s" % checked_feats)

        # 3. Check if labeling situation is changed
        if self.label_if_possible(y):
            self.announce_derivation_step([x, y], "labeled unlabeled element: '%s'" % y.label)

        # Now Merge:
        # 4. Merge
        label_giver, part1, part2 = self.determine_label(x, y)
        merged = self.merge(label_giver, part1, part2)
        self.announce_derivation_step([merged], "merged '%s', '%s'" % (part1.label, part2.label))

        # 5. Try to deal with unlabeled result of merge
        if merged.is_unlabeled():
            self.out("Label(None)", merged)
            remerge = self.unlabeled_move(merged)
            if self.label_if_possible(merged):
                self.announce_derivation_step([merged], "found label for unlabeled element")
            if remerge:
                merged = self.remerge(merged, remerge)
                self.announce_derivation_step([merged], "remerged previously merged element")
                if merged.is_unlabeled():
                    self.out("Label(None)", merged)
                else:
                    self.out("Label(SharedFeats)", merged)
                self.relabel_my_parent(merged, remerge)

        # 6. Echos from feature check
        else:
            if passed_features:
                # if label_info == "Head":
                self.out("Label(Head)", merged)
            if postponed_remerge:
                merged = self.remerge_back(merged, postponed_remerge)
                self.out("Label(SharedFeats)", merged)
                self.announce_derivation_step([merged], "remerged back")
                if self.label_if_possible(merged):
                    self.announce_derivation_step([merged], "found label for unlabeled element")

        # 7. Transfer and dephase
        if merged.label in PHASE_HEADS:
            success = False
            if self.in_main and merged.label == "v*":
                success = self.dephase_and_transfer(merged)
                if success:
                    self.announce_derivation_step(merged, "dephased and transferred")
            if not success:
                merged = self.transfer_check(merged)
        return merged

    def determine_label(self, x, y):
        x_feats = x.get_head_features()
        y_feats = y.get_head_features()
        external_merge = "MergeF" in x_feats
        # Determine label
        # Head-feature gives immediately label, once
        if "Head" in x_feats and "Head" not in y_feats:
            head_f = get_by_part(x_feats, "Head")
            x_feats.remove(head_f)
            label_info = "Head"
            return x, x, y
        elif y.label in ADJUNCT_LABELS:
            return x, x, y
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
                return None, x, y
            else:
                return None, y, x

    def merge(self, label_giver, part1, part2):
        """ Merge two objects with predefined label
        :param label_giver: so or None
        :param part1: so
        :param part2: so
        :return: merged
        """
        print('merge')
        self.merge_counter += 1
        if label_giver:
            label = label_giver.label
        else:
            label = '_'
        merged = Constituent(label=label, part1=part1, part2=part2)
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
        if not self.in_main:
            print("Remerging in in substream999999")
            sys.exit()
        msg = "merge (for labeling(remerge back)) " + merged.label + " + " + remerge.label
        self.out("merge", msg)
        merged = Constituent(label=label, part1=remerge, part2=merged)
        self.merge_counter += 1
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

        merged_feats = merged.get_head_features()
        dephase = False
        transfer = None

        if "Delete" in merged_feats:  # Dephase because C is deleted
            transfer, merged = self.dephase_deleted_c(merged)
            self.announce_derivation_step(merged, "dephased deleted C")
            dephase = True

        # check Stack if unvalued igned features are present
        remerge = None
        if self.in_main:
            merged, remerge = self.remerge_if_can(merged, dephase=dephase)

        if not dephase:
            # Transfer a complement of a phase head
            if merged.is_unlabeled() or "Phi" in merged.label:
                target_label = merged.part2.label
            else:
                target_label = merged.label
            transfer = recursive_find_complement(merged, target_label, False)
        if transfer:
            transfer.transfered = True
        self.out("Transfer", transfer)  # Transfer actually does nothing.
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
        if not current:
            return
        # Transfer the complement of v
        assert current.is_labeled()
        remerge = current
        transfer = remerge.part2
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
        if transfer:
            transfer.transfered = True
        self.out("Transfer", transfer)
        # Check to see if Remerge results in labeling
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
        """ Assume that merged is unlabeled.
        :param merged:
        :return:
        """
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
                    return None
        # Move an element within an unlabeled Merged Structure

        # find element in stack with phi-features and raise if possible
        head = merged.part1
        head_feats = expanded_features(head.get_head_features())
        if has_part(head_feats, "iD", "iPerson"):
            # There's already a DP with phi-features here, so no need to merge
            # another DP with Phi
            return None
        elif has_part(head_feats, "iQ", "iPerson"):
            # There's already a DP with phi-features here, so no need to merge
            # another DP with Phi
            return None
        # Try looking into complement
        comp = merged.part2
        if comp.is_unlabeled():
            locus = comp.part1
            features = expanded_features(locus.get_head_features())
            if has_part(features, "iN", "uPerson") or \
                    has_part(features, "iQ", "iPerson") or \
                    has_part(features, "iD", "iPerson"):
                return locus
        elif "Phi" in comp.label:
            locus = comp.part1
            features = expanded_features(locus.get_head_features())
        else:
            locus = comp
            features = expanded_features(locus.get_head_features())
            if has_part(features, "iN"):
                return locus
        if has_part(features, "iD", "iPerson") or has_part(features, "iQ", "iPerson"):
            return locus
        return None

    def relabel_my_parent(self, current, chosen_one):
        """ Relabel the parent of remerged constituent """
        if chosen_one != current and chosen_one in current:
            current_feats = current.get_head_features()
            if not has_part(current_feats, "Root"):
                if current.part1 == chosen_one:
                    current.label = current.part2.label
                elif current.part2 == chosen_one:
                    current.label = current.part1.label
                return True
        if current.part1 and self.relabel_my_parent(current.part1, chosen_one):
            return True
        return current.part2 and self.relabel_my_parent(current.part2, chosen_one)

    def remerge(self, merged, remerge):
        print('remerge')
        if not self.in_main:
            print("Do in substream999999")
            sys.exit()
        self.out("merge", "merge (for labeling (remerge)) " + remerge.label + " + " + merged.label)
        if merged.part1.label == "vUnerg":
            sys.exit()
        merged = Constituent(label=merged.label, part1=remerge, part2=merged)
        return merged

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
        return success

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

    def can_pass_features(self, x, y):
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
        return unvalued_phis, inherit

    def check_features(self, x, y):
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
            return None, None
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
                    if goal.name == "Top" or goal.name == "Q" and goal.ifeature:  # iTop
                        # "Top" never seems to activate
                        top_chkd = make_checking_pairs(unvalued_features, stack_top_feats)
                        for old_top_f, new_top_f in top_chkd:
                            old_top_f.value_with(new_top_f)
                            if old_top_f not in checked_feats:
                                checked_feats.append(old_top_f)
                            if not self.in_main:
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
        return remerge, checked_feats


    def pass_features(self, inherit, unvalued_phis, x, y):
        """Pass features to those who:

        - Have Root-feature
        - don’t have uPerson or iPerson
        - are not already chosen for feature passing (we don't double-drive)
        - have not iD or iN in features
        - don’t have ”n” as previous item in stack (wtf?)
        - bonus: have not transfered

        p. 27:
        According to (19), a phase head passes its uninterpretable features (uFs) to its
        complement X, if the complement X is unlicensed. Furthermore, X will pass these
        uFs down to its complement Y, if Y is unlicensed, and so on. An unlicensed
        complement is unlabeled.

        (19) Feature inheritance (revised)
        Uninterpretable features are passed to an unlicensed complement.

        hm, hm. Model10 code seems to also allow labeled Roots to inherit features. """

        #input('attempt feature passing for %s' % inherit.label)

        passed_items = []
        feats_passed = False
        prev_label = False  # block feature passage to nominal

        #print('-------------')
        #print('X:', x)
        #print('Y:', y)


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

                        #print('passing features to current: ', node)
                        #print('previous_label:', previous_label)
                        #input()
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
        #print('with inherited features from ', inherit)
        #print('attempting to look into ', spine)
        prev_label = ''
        while spine:  # and False:
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


        return feats_passed

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
