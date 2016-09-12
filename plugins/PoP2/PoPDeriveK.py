#######################################################
###Derivation Generator - Problems of Projection Version
## Rewriting Jason Ginsburg's computer model for PoP,
# http://www.osaka-kyoiku.ac.jp/~jginsbur/MinimalistModeling.html
# Jukka Purma
#########################################################

import sys
import time
import logging

try:
    from PoP2.Lexicon import DET_HEADS, PHASE_HEADS, THETA_ASSIGNERS, SHARED_LABELS, \
        ADJUNCT_LABELS, COUNTED_FEATURES, COUNTED_PHI_FEATURES, LEXICON
    from PoP2.ConstituentB import Constituent, find_shared_features, expanded_features
    from PoP2.FeatureB import Feature
    in_kataja = True
except ImportError:
    from Lexicon import DET_HEADS, PHASE_HEADS, THETA_ASSIGNERS, SHARED_LABELS, \
        ADJUNCT_LABELS, COUNTED_FEATURES, COUNTED_PHI_FEATURES, LEXICON
    from ConstituentB import Constituent, find_shared_features, expanded_features
    from FeatureB import Feature
    in_kataja = False

start = 3
end = 4


def find(features, name=None, value=None, u=None, i=None, phi=None):
    return [x for x in features if x.match(name=name, value=value, u=u, i=i, phi=phi)]


class Generate:
    def __init__(self, out_writer=None):

        self.out_writer = out_writer
        self.so_list = []
        self.phi_counter = 0
        self.feature_counter = 0
        self.in_main = True
        self.lookforward_so = None
        self.over_counter = 0
        self.dumpfile = None
        self.forest = None
        self.workspace = []
        self.sub_workspace = []
        self.msg_stack = []
        self.spine = None
        self.gloss = None
        self.transferred = []

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
            self.gloss = sentence
            target_example = eval(lbracket + target_str)
            self.out(sentence_number, sentence, target_example)
            so = self.generate_derivation(target_example)

    def out(self, first, second, third=None):
        msg = '%s: %s' % (first, second)
        if self.forest:
            self.msg_stack.append(msg)
        #print('%s: %s' % (first, second))
        logging.info(msg)
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
        self.lookforward_so = None
        self.so_list = build_synobj_lists(target_example, [])
        self.forest = forest
        self.spine = None
        self.workspace = []
        self.transferred = []
        so = None
        selected = None
        self.announce_derivation_step([], msg=str(target_example))

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
        self.announce_derivation_step([selected], msg='finished')

        return selected

    def merge_substream(self, synobjlist, spine):
        """ Switch into substream (phrase within sentence) and build that before
        merging the whole thing into main spine.
        :param synobjlist: list of syntactic objects
        :param spine: main structure of merged objects
        :return: spine
        """
        self.in_main = False
        self.out("SubStream", True)
        substream_spine = None

        while synobjlist:
            x = synobjlist.pop()
            substream_spine = self.merge_so(x, substream_spine)
        self.in_main = True
        # merge substream back to main stream:
        self.out("MainStream", True)
        self.out("merge", "merge " + spine.label + " + " + substream_spine.label)
        self.spine = self.grand_cycle(spine, substream_spine)
        return self.spine

    def announce_derivation_step(self, parts=None, msg='', transfer=None):
        """ Send current structure for Kataja so it can store it as a derivation step.
        :param parts: list of current root nodes
        :param msg: message to show with the derivation step
        :return:
        """
        if not self.forest:
            return
        self.msg_stack.append(msg)
        msg = '\n'.join(self.msg_stack)
        self.msg_stack = []
        if transfer:
            self.transferred.append(transfer)
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
                                                                     msg=msg,
                                                                     gloss=self.gloss,
                                                                     transferred=self.transferred)

    def merge_so(self, x, spine):
        """ Select new item and merge it into structure
        :param x: syntactic object
        :param spine: main structure of merged objects
        :return: spine
        """
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
            #print('finished merge: ', spine)
            #print('---- kataja string: ----')
            #print(spine.tex_tree())
            #print('----------------- ', self.over_counter)
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
        external_merge = find(x.features, "MergeF") 

        # Before merge
        # 1. Pass unvalued phi-features downwards
        unvalued_phis, inherit, complement = self.can_pass_features(x, y)
        if inherit:
            passed_features = self.pass_features(inherit, complement, unvalued_phis)
            if passed_features:
                self.announce_derivation_step([x, y], "passed features %s" % unvalued_phis)
        # 2. Check features
        postponed_remerge, checked_feats = self.check_features(x, y)
        if checked_feats:
            self.announce_derivation_step([x, y], "checked features: %s" % checked_feats)

        # 3. Check if labeling situation has changed
        new_labels = self.label_if_possible(y)
        if new_labels:
            self.announce_derivation_step([x, y], "labeled unlabeled element: %s" % new_labels)

        # Now Merge:
        # 4. Merge
        label_giver, part1, part2 = self.determine_label(x, y, external_merge)
        merged = self.merge(label_giver, part1, part2)
        self.announce_derivation_step([merged], "merged '%s', '%s'" % (part1.label, part2.label))

        # 5. Try to deal with possible unlabeled result of merge
        if merged.is_unlabeled():
            self.out("Label(None)", merged)
            remerge = self.find_mover_in_unlabeled(merged)
            new_labels = self.label_if_possible(merged)
            if new_labels:
                self.announce_derivation_step([merged], "labeled unlabeled element: %s" %
                                              new_labels)
            if remerge:
                self.out("merge",
                         "merge (for labeling (remerge)) %s +  %s" % (remerge.label,
                                                                      merged.label))
                merged = self.remerge(merged, remerge)
                new_labels = self.label_if_possible(merged)
                if new_labels:
                    self.announce_derivation_step([merged], "labeled unlabeled element: %s"
                                                  % new_labels)
                self.announce_derivation_step([merged], "remerged previous element '%s'"
                                              % remerge.label)
                if merged.is_unlabeled():
                    self.out("Label(None)", merged)
                else:
                    self.out("Label(SharedFeats)", merged)
                # remerge may change the labeling situation in previous place of remerged
                self.relabel_my_parent(merged, remerge)

        # 6. Echos from feature check
        else:
            if passed_features:
                # if label_info == "Head":
                self.out("Label(Head)", merged)
            if postponed_remerge:
                self.out("merge", "merge (remerge back) %s + %s" % (merged.label,
                                                                    postponed_remerge.label))
                merged = self.remerge_postponed(merged, postponed_remerge)
                self.out("Label(SharedFeats)", merged)
                self.announce_derivation_step([merged], "remerged back '%s'" %
                                              postponed_remerge.label)
                new_labels = self.label_if_possible(merged)
                if new_labels:
                    self.announce_derivation_step([merged], "labeled unlabeled element: %s"
                                                  % new_labels)

        # 7. Transfer and dephase
        if merged.label in PHASE_HEADS:
            success = False
            if self.in_main and merged.label == "v*":
                success = self.dephase_and_transfer(merged)
                if success:
                    merged, transfer = success
                    self.announce_derivation_step(merged, "dephased '%s' and transferred '%s'" %
                                                  (merged.label, transfer.label), transfer=transfer)
            if not success:
                merged = self.transfer_check(merged)
        return merged

    def determine_label(self, x, y, external_merge):
        x_feats = x.get_head_features()
        y_feats = y.get_head_features()
        # Determine label
        # Head-feature gives immediately label, once
        head_xf = find(x_feats, "Head")
        head_yf = find(y_feats, "Head")
        if y.label in ADJUNCT_LABELS:
            return x, x, y
        elif head_xf and not head_yf:
            x.get_head().features.remove(head_xf[0])
            # label_info = "Head"
            return x, x, y
        else:
            # Check if adjunct
            # ordering doesn't matter, but this makes things easier
            if "v" in x.label:
                if y.label.startswith("D") or y.label.startswith("Q"):
                    return None, y, x
            elif "C" in x.label:
                return None, y, x
            elif "P_in" in x.label:
                return None, y, x
            if external_merge: 
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
        if label_giver:
            label = label_giver.label
        else:
            label = '_'
        merged = Constituent(label=label, part1=part1, part2=part2)
        return merged

    def remerge(self, merged, remerge):
        merged = Constituent(label=merged.label, part1=remerge, part2=merged)
        return merged

    def remerge_postponed(self, merged, remerge):
        shared_feats = merged.shared_features(remerge)
        if find(shared_feats, "Q", i=True):
            label = "Q"
        elif find(shared_feats, "Top", i=True):
            label = "Top"
        else:
            assert False
        merged = Constituent(label=label, part1=remerge, part2=merged)
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

        # ##### Dephase because T inherits phasehood ##### #

        merged_feats = merged.get_head_features()
        dephase = False
        transfer = None

        if "Delete" in merged_feats:  # Dephase because C is deleted
            transfer, merged = self.dephase_deleted_c(merged)
            self.announce_derivation_step(merged, "dephased deleted C to '%s' and transfered '%s'"
                                          % (merged.label, transfer.label), transfer=transfer)
            dephase = True

        # check Stack if unvalued igned features are present
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
            merged.label = new_label
        self.out("Dephase v", merged)
        if transfer:
            transfer.transfered = True
        self.out("Transfer", transfer)
        # Check to see if Remerge results in labeling
        return merged, transfer

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

        left = merged.part1
        right = merged.part2
        label = merged.label
        merged_feats = merged.get_head_features(expanded=True)
        spec = merged.part1
        spec_feats = spec.get_head_features(expanded=True)
        if spec_feats != merged_feats and not find(spec_feats, "Delete"):
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
                # any item with unlabeled features:
                for x in find(current.get_head_features(expanded=True), u=True):
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

    def find_mover_in_unlabeled(self, merged):
        """ Assuming that merged is unlabeled, find Q or D with valued phi features to raise.
        :param merged:
        :return:
        """
        # I don't like this next move, looking forward to decide on current cycle:
        if self.lookforward_so:
            # External merge blocks internal merge
            if merged.part1.label in THETA_ASSIGNERS:
                if isinstance(self.lookforward_so, list):
                    lf_so = self.lookforward_so[0]  # look into substream
                else:
                    lf_so = self.lookforward_so
                if lf_so.label in DET_HEADS or \
                    (lf_so.label == "n" and find(lf_so.features, "Person", u=True)):  # = n_Expl
                    return None

        # find element in stack with phi-features and raise if possible
        head = merged.part1
        head_feats = head.get_head_features(expanded=True)
        if find(head_feats, ["Q", "D"], i=True) and find(head_feats, "Person", i=True):
            # There's already a DP with phi-features here, so no need to merge
            # another DP with Phi
            return None
        # Try looking into complement
        comp = merged.part2
        if comp.is_unlabeled():
            locus = comp.part1
            features = locus.get_head_features(expanded=True)
            if find(features, "N", i=True) and find(features, "Person", u=True):
                return comp.part1
        elif "Phi" in comp.label:
            locus = comp.part1
            features = locus.get_head_features(expanded=True)
        else:
            locus = comp
            features = locus.get_head_features(expanded=True)
            if find(features, "N", i=True):
                return locus
        if find(features, ["Q", "D"], i=True) and find(features, "Person", i=True):
            return locus
        return None

    def relabel_my_parent(self, current, chosen_one):
        """ Relabel the parent of remerged constituent """
        if chosen_one != current and chosen_one in current:
            current_feats = current.get_head_features()
            if not find(current_feats, "Root"):
                if current.part1 == chosen_one:
                    current.label = current.part2.label
                elif current.part2 == chosen_one:
                    current.label = current.part1.label
                return True
        if current.part1 and self.relabel_my_parent(current.part1, chosen_one):
            return True
        return current.part2 and self.relabel_my_parent(current.part2, chosen_one)

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
            if item in found_items:
                return
            found_items.add(item)
            if item.is_unlabeled():
                p1_is_copy = item.part1 in found_items
                p2_is_copy = item.part2 in found_items
                waiting_for_labeling.append((item, p1_is_copy, p2_is_copy))
            if item.part1:
                build_pairs_to_analyse(item.part1)
            if item.part2:
                build_pairs_to_analyse(item.part2)

        build_pairs_to_analyse(merged)
        successes = []

        for item, p1_is_copy, p2_is_copy in reversed(waiting_for_labeling):
            new_label = self.labeling_function(item.part1, item.part2, p1_is_copy, p2_is_copy)
            if new_label is not False:
                item.label = new_label
                successes.append(new_label)
        return successes

    def labeling_function(self, x, y, x_has_moved, y_has_moved):
        """ Compute label for SO that merges x, y
        :param x: Constituent
        :param y: Constituent
        :param x_has_moved: bool, analyse structure instead of using Copy-feature.
        :param y_has_moved: bool
        :return: label string or False
        """
        if x.is_unlabeled() and y.is_unlabeled():
            return False
        elem1_feats = x.get_head_features(expanded=True)
        elem2_feats = y.get_head_features(expanded=True)
        if not (elem1_feats and elem2_feats):
            return False
        if find(elem1_feats, "Root"):  # weak
            phis = find(elem1_feats, i=True, phi=True)
            if len(phis) > 1:
                self.out("Label(Strengthened)", x.label)
                return x.label
        if x_has_moved and not y_has_moved:
            if find(elem2_feats, "Root") or find(elem1_feats, "Root"):  # weak
                phis = find(elem2_feats, i=True, phi=True)
                if len(phis) > 1:
                    self.out("Label(Move)", y.label)
                    return y.label
            else:
                self.out("Label(Move)", y.label)
                return y.label
        elif y_has_moved and find(elem1_feats, "Root"):
            if len(find(elem1_feats, i=True, phi=True)) > 1:
                # weak if Root
                self.out("Label(Move)", x.label)
                return x.label
        shared_feats = find_shared_features(elem1_feats, elem2_feats)
        if not shared_feats:
            # Check for strengthened element
            return False
        phis = find(shared_feats, i=True, phi=True)
        if len(phis) == 3:
            for person_f in find(phis, "Person"):
                new_label = "Phi%s" % person_f.counter or ''
                self.out("Label(SharedFeats)", new_label)
                return new_label
        elif len(phis) == 1:
            self.out("Label(SharedFeats)", "Per")
            return "Per"
        return False

    def get_lexem(self, synobj):
        """

        :param synobj:
        :return:
        """
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
        # Leave the actual feature parsing to feature constructor, called by Constituent
        # as it gets strings as features.
        return Constituent(label=synobj, features=features)

    def can_pass_features(self, x, y):
        # If X has uPhi, then uPhi are passed down the tree until they are checked
        x_feats = x.get_head_features(expanded=True)  # sharing is possible
        y_feats = y.get_head_features(no_sharing=True, expanded=True)
        # Which is head?
        current_label = ''
        x_head = find(x_feats, "Head")  # find returns lists, so this returns [x_head] or []
        y_head = find(y_feats, "Head")
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
        complement = None
        inherit = None

        # First thing is to collect unvalued phis from either x or y. First try x,
        # if it has impressive amount of unvalued features, then it is the feature giver.
        # Then y. If neither has enough, scoot off.
        unvalued_phis = find(x_feats, u=True, phi=True)
        unvalued_phis += find(x_feats, "Case", u=False)
        if len(unvalued_phis) >= 3 or x.label in PHASE_HEADS:
            inherit = x
            complement = y

        if not inherit:
            unvalued_phis = find(y_feats, u=True, phi=True)
            unvalued_phis += find(y_feats, "Case", u=False)
            if len(unvalued_phis) >= 3:
                inherit = y
                complement = x
        return unvalued_phis, inherit, complement

    def check_features(self, x, y):
        """

        :param x:
        :param y:
        :return:
        """

        def list_builder(node, l):
            if node not in l:
                l.append(node)
                # Again it seems that anything deeper than spine is off-limits
                if node.part1:
                    l = list_builder(node.part1, l)
                if node.part2:
                    l = list_builder(node.part2, l)
            return l

        x_feats = x.get_head_features(no_sharing=True, expanded=True)
        y_feats = y.get_head_features(no_sharing=True, expanded=True)
        checked_feats = []
        # XFeats probe
        for mf in find(x_feats, "MergeF"):
            x.get_head().features.remove(mf)
        unvalued_features = find(x_feats, u=True)
        if find(unvalued_features, phi=True):
            unvalued_features += find(x_feats, "Case")
        unvalued_features += find(x_feats, "Scp", i=True)
        if not unvalued_features:
            return None, None
        remerge = None
        tree_as_list = list_builder(x, [])
        tree_as_list = list_builder(y, tree_as_list)

        for uf in unvalued_features:
            for probe in tree_as_list:
                feat_checked = False
                if probe == x:
                    continue
                if "Phi" in probe.label:
                    # Don't look at the features of an element with shared phi-features
                    # This is maybe an imperfection
                    probe_feats = []
                    probe_base = probe
                else:
                    probe_feats = probe.get_head_features(expanded=True)
                    probe_base = probe.get_head()
                if probe_feats is None:
                    sys.exit()
                unvalued_probe_feats = find(probe_feats, u=True)
                # Unification
                # This can match only two unvalued, but uf:s can also be iScp:s or Cases
                if uf.unvalued:
                    for unvalued_probe in unvalued_probe_feats:
                        if unvalued_probe != uf and unvalued_probe.match(uf.name):
                            probe_base.features.remove(unvalued_probe)
                            probe_base.features.append(uf)
                            self.out("Unification", uf)

                if find(probe_feats, uf.name, i=True, value=uf.value):  # goal in probe
                    if probe.is_unlabeled() or not (unvalued_probe_feats or uf.match(["Q", "Top"])):
                        continue
                    if uf.match(["Top", "Q"]):
                        # "Top" never seems to activate, for "Q" this gets used
                        for upb in unvalued_probe_feats:
                            for found in find(unvalued_features, upb.name, i=True):
                                upb.value_with(found)
                                if upb not in checked_feats:
                                    checked_feats.append(upb)
                                break
                        remerge = probe

                    # Remerge due to a need to share Q features
                    for probe_match in find(probe_feats, uf.name, i=True, value=uf.value):
                        if uf != probe_match:
                            uf.value_with(probe_match)
                            break

                    feat_checked = True
                    checked_feats.append(uf)
                    # Check uScp as a reflex of uQ checking
                elif uf.name == "Case" and uf.value:
                    checked_feats.append(uf)
                    # hmm... Case disappears from original place and is active only in new place.
                    # x.replace_within(uf, None)
                    # y.replace_within(uf, None)

                    # I can't accept it?
                    uf.inactive = True
                    for y_feat in find(y_feats, "Case", u=True):
                        y_feat.value_with(uf)
                    feat_checked = True
                elif uf.name == "Phi":
                    if find(probe_feats, "Person", i=True):
                        for i_phi in find(probe_feats, i=True, phi=True):
                            uf.value_with(i_phi)
                        for u_case in find(probe_feats, "Case", u=True):
                            uf.value_with(u_case)
                            break

                    self.out("PhiPassing", "uPhi")
                    feat_checked = True
                if feat_checked:
                    break
        if checked_feats:
            self.out("CheckedFeatures", checked_feats)
        return remerge, checked_feats

    def pass_features(self, inherit, comp, unvalued_phis):
        """Pass features to those who:

        Model10:s logic for passing features
        - Have Root-feature
        - don’t have uPerson or iPerson
        - are not already chosen for feature passing (we don't double-drive)
        - have not iD or iN in features
        - don’t have ”n” as previous item in stack (wtf?)

        reliance on stack causes some weird situations in Model10, where some roots in n receive
         features because the stack has items added in unusual order. It is difficult to replicate
         stackless, and it is wrong anyways.

        Feature passing described in Ginsburg 2016 is different, p. 27:
        According to (19), a phase head passes its uninterpretable features (uFs) to its
        complement X, if the complement X is unlicensed. Furthermore, X will pass these
        uFs down to its complement Y, if Y is unlicensed, and so on. An unlicensed
        complement is unlabeled.

        (19) Feature inheritance (revised)
        Uninterpretable features are passed to an unlicensed complement.

        Email clarifies how Model10 should work, and that is implemented here:
        "The rule should be that features can’t be passed onto any element that has valued phi-features, so n and d should’t inherit features. The exception here is the n that Merges with ‘there’. This n lacks any features of its own (if I remember correctly), so it can inherit phi-features. The rule really should be that if a syntactic object has iPhi, it can’t inherit features, since an element with iPhi has no need to inherit features. In general, only roots and “weak” elements (such as T) should be able to inherit features. I think that the n that Merges with ‘there’, which I indicate as ’n_Expl’, is essentially a weak element without any phi-feaures. "

         """

        feats_passed = False

        def find_empty_root_leaf(node):
            found = False
            feats = node.get_head_features(expanded=True)
            if find(feats, ["Person", "Phi"]):
                return False
            elif node.is_leaf():
                if find(node.features, "Root"):
                    feats = expanded_features(node.features)
                    if not find(feats, ["D", "N"], i=True):
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
                        for item in unvalued_phis:
                            node.features.append(item)
                        self.out("PassFs", "Pass Features " + inherit.label + " to " + other_label)
                        self.out("FeaturesPassed", unvalued_phis)
                        found = True
            else:
                got_it = find_empty_root_leaf(node.part2)
                if got_it:
                    found = True
                got_it = find_empty_root_leaf(node.part1)
                if got_it:
                    found = True
            return found

        while comp:  # and False:
            current = comp
            if comp.is_unlabeled():
                found_it = find_empty_root_leaf(comp.part1)
                if found_it:
                    feats_passed = True
            if comp.part2:
                if comp.part2.is_labeled() and\
                        find(comp.part2.get_head_features(), ["Phi", "Person"]):
                    comp = None
                else:
                    comp = comp.part2
            else:
                comp = None
                found_it = find_empty_root_leaf(current)
                if found_it:
                    feats_passed = True
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
    a = Generate(out_writer=out)  # out)
    a.load_data(input_data, start, end)
    out.close()
    print(time.time() - t)
