try:
    from kataja.syntax.SyntaxState import SyntaxState
    from kataja.syntax.BaseConstituent import BaseConstituent as Constituent
    from LinearPhaseParser.Feature import Feature
    from LinearPhaseParser.PhraseStructure import PhraseStructure
    in_kataja = True
except ImportError:
    from PhraseStructure import PhraseStructure
    Constituent = object
    SyntaxState = object
    Feature = None
    in_kataja = False

from collections import defaultdict

from support import set_logging, log, set_log_buffering, get_log_buffer, clear_log_buffer
from linear_phase_parser import LinearPhaseParser as LinearPhaseParserBase

# State types
DONE_SUCCESS = 7
DONE_FAIL = 2
CONSUME = 0
MERGE = 3
START = 5


class LinearPhaseParser(LinearPhaseParserBase):
    """ This class inherits and requires LinearPhaseParser from https://github.com/pajubrat/parser-grammar
    Credits for parser performance should go to original authors there.
    """

    def __init__(self, context, forest=None):
        super().__init__(context)
        set_log_buffering(True)
        self.forest = forest
        self.kataja_items = {}
        self.dead_ends = 0
        self.state_id_counter = 0
        # Lexicon has to be reloaded so that it uses our version of PhraseStructure instead.
        self.lexicon.PhraseStructure = PhraseStructure
        self.lexicon.d.clear()
        self.lexicon.load_lexicon(self.context.lexicon_file, context.language)
        self.lexicon.load_lexicon(self.context.ug_morphemes_file, context.language, combine=True)

    def next_state_id(self):
        self.state_id_counter += 1
        return self.state_id_counter

    def parse(self, lst):
        self.state_id_counter = 0
        super().parse(lst)

    # This is modified to track state_id:s to find when the derivation steps are branching from a common ancestor step.
    # Also op_type (operation type) tracks what kind of operation the previous operation was. It is easier to report
    # steps for kataja just once at the beginning of the method, but this means that the op_type must come from the
    # previous step.
    # Recursive parsing algorithm
    def _first_pass_parse(self, ps, lst, parent_id=None, op_type=START):

        if self.exit:
            return

        set_logging(True)
        self.number_of_Merges += 1

        # Print the current state to the log file
        log(f'\t\t\t={ps}')
        log(f'\n{self.number_of_Merges}.')

        # Test if we have reached at the end of the input list
        if not lst:
            res_size = len(self.result_list)
            self.evaluate_solution(ps)
            success = len(self.result_list) > res_size
            msg = 'Success' if success else 'Crash'
            state_type = DONE_SUCCESS if success else DONE_FAIL
            self.export_to_kataja([ps], msg, state_id=self.next_state_id(), parent_id=parent_id, state_type=state_type)
            return

        state_id = self.next_state_id()
        self.export_to_kataja([ps] if ps else [], ' '.join(lst), state_id=state_id, parent_id=parent_id,
                              state_type=op_type)
        parent_id = state_id

        # Process next word
        # Initialize morphology
        m = self.morphology

        # Lexical ambiguity
        # If the item was not recognized, an ad hoc constituent is returned that has unknown label CAT:X
        word = lst.pop(0)
        disambiguated_word_list = self.lexicon.access_lexicon(word)
        if len(disambiguated_word_list) > 1:
            log(f'\t\tAmbiguous lexical item "{word}" detected.')

        # We explore all possible lexical items
        for lexical_constituent in disambiguated_word_list:
            lst_branched = lst.copy()

            # Morphological decomposition: increases the input list if there are several morphemes
            # If the word was not recognized (CAT:X), generative morphology will be tried
            lexical_item, lst_branched = m.morphological_parse(lexical_constituent,
                                                               lst_branched,
                                                               word)

            # Read inflectional features (if any) and store them into memory buffer, then consume next word
            inflection = m.get_inflection(lexical_item)
            if inflection:

                # Add inflectional features and prosodic features into memory
                self.memory_buffer_inflectional_affixes |= inflection
                log(f'\n\t\tConsume "{lst_branched[0]}"\n')
                new_ps = None
                if ps:
                    new_ps = ps.copy()
                self._first_pass_parse(new_ps, lst_branched, parent_id=parent_id, op_type=CONSUME)
                continue

            # If the item was not inflection, it is a morpheme that must be merged

            # Unload inflectional suffixes from the memory into the morpheme as features
            lexical_item = m.set_inflection(lexical_item, self.memory_buffer_inflectional_affixes)
            lexical_item.get_new_key()
            self.memory_buffer_inflectional_affixes = set()

            # If there is no prior phrase structure, we create it by using the first word
            if not ps:
                ps = lexical_item.copy()
                self._first_pass_parse(ps, lst_branched, parent_id=parent_id, op_type=MERGE)
                continue

            # ------------------------------------------------------------------------------------
            # MAIN PARSER LOOP
            # ------------------------------------------------------------------------------------

            # Merge the new word (disambiguated lexical item) to the existing phrase structure
            log(f'\n\t\tConsume "{lexical_item.get_pf()}"\n')
            log(f'\t\t{ps.illustrate()} + {lexical_item.get_pf()}')

            # Get the merge sites
            # Impossible merge sites are first filtered out
            # Possible merge sites are then ranked
            adjunction_sites = self.ranking(self.filter(ps, lexical_item), lexical_item)

            # Test the adjunction sites in the order of ranking
            for i, site in enumerate(adjunction_sites, start=1):
                ps_ = ps.get_top().copy()

                # If the next morpheme was inside the same word as previous, it will be
                # eaten inside the constituent (will be reconstructed later)
                if site.get_bottom_affix().internal:
                    log(f'\t\tExploring solution number ({i}) =' + f'[{site}*{lexical_item.get_pf()}]')
                    site_ = ps_[ps.index(site)]
                    new_ps = site_ * lexical_item

                # If the next morpheme was not inside the same word as previous, it will be merged
                else:
                    log(f'\t\tExploring solution number ({i}) =' + f'[{site} {lexical_item.get_pf()}]')
                    site_ = self.transfer_to_lf(ps_[ps.index(site)])
                    new_ps = site_ + lexical_item
                self._first_pass_parse(new_ps, lst_branched, parent_id=parent_id, op_type=MERGE)
                if self.exit:
                    break

            # ------------------------------------------------------------------------------------
            #
            # ------------------------------------------------------------------------------------

        # If all solutions in the list have been explored, we backtrack
        if not self.exit:
            # All branches for the incoming surface word have been explored
            log(f'\t\tI have now explored all solutions for "{word}".')
            log('\t\tGoing one step backwards and taking another solution from previous ranking list........'
                '\n\t\t.\n\t\t.\n\t\t.')
        return

    # ############ functions related to Kataja export ##########################

    @staticmethod
    def feature_check(match):
        if in_kataja:
            comp_feature, cat_feature = match
            log(f'\tChecking feature {comp_feature} with {cat_feature}.')
            cat_feature.check(comp_feature)

    def turn_into_kataja_feature(self, fstr, host_id, host):
        feat_id = f'{fstr}_{host_id}'
        if feat_id in self.kataja_items:
            feat = self.kataja_items[feat_id]
        else:
            feat = Feature.from_string(fstr)
            self.kataja_items[feat_id] = feat
        feat.host = host
        return feat

    @staticmethod
    def pick_gloss(features):
        for feat in features:
            if feat.startswith('LF:'):
                return feat[3:]
        return ''

    @staticmethod
    def merge_features(features):
        feats = defaultdict(list)
        for feat in features:
            first, *rest = feat.split(':', 1)
            if rest:
                feats[first] += rest
        result = []
        cat = None
        for fname, fvalue in feats.items():
            if fname in ['LANG', 'PF', 'LF']:
                continue
            elif fname == 'CAT':
                cat = ", ".join(fvalue)
            else:
                result.append(f'{fname}:{",".join(fvalue)}')
        result.sort()
        if cat:
            result = [cat] + result
        return result

    def turn_into_kataja_constituent(self, ps):
        ps_id = ps.key
        if not ps.is_primitive():
            if ps.adjunct:
                label = f'<{ps.get_head().get_pf()}>'
            else:
                label = ps.get_head().get_pf()
        elif ps.adjunct:
            label = f'<{ps.get_pf()}>'
        else:
            label = ps.get_pf()
        if ps_id in self.kataja_items:
            const = self.kataja_items[ps_id]
            const.label = label
            if ps.adjunct and not const.adjunct:
                print(f'turning {const} into adjunct (it was stored, but not as an adjunct')
                const.adjunct = True
        else:
            const = Constituent(label=label)
            self.kataja_items[ps_id] = const
            const.adjunct = ps.adjunct
        const.gloss = self.pick_gloss(ps.features)
        feats = self.merge_features(ps.features)
        feats = [self.turn_into_kataja_feature(feat, ps_id, const) for feat in feats]
        const.features = feats
        if ps.left_const and ps.right_const:
            const.parts = [self.turn_into_kataja_constituent(ps.left_const),
                           self.turn_into_kataja_constituent(ps.right_const)]
        return const

    def export_to_kataja(self, trees, message, marked=None, state_id=0, parent_id=None, state_type=DONE_FAIL):
        if self.forest:
            trees = [self.turn_into_kataja_constituent(tree) for tree in trees if tree]
            syn_state = SyntaxState(tree_roots=trees, msg=message, groups=[('', marked)],
                                    log=get_log_buffer(), state_id=state_id, parent_id=parent_id, state_type=state_type)
            clear_log_buffer()
            self.forest.add_step(syn_state)

    # def why_merge(self, site, w):
    #     """ This is just an inspection method for me to check if there are feature-based justifications that can be
    #     found for this merge -- this parser doesn't require there to be such when the merge is made, but I want to
    #     see how common such merges are.
    #     """
    #     def match(first_set, second_set):
    #        return any((x in second_set for x in first_set))
    #
    #     word_specs = self.for_parsing(w.get_specs())
    #     word_cats = set(w.get_cats())
    #     word_tail_set = w.get_tail_sets()
    #     word_labels = w.get_labels()
    #     site_comps = self.for_parsing(site.get_comps())
    #     site_head_comps = self.for_parsing(site.get_head().get_comps())
    #     if match(word_specs, site.get_head().get_cats()):
    #         print('merge because spec.')
    #     elif '*' in word_specs:
    #         print('merge because * spec.')
    #     elif match(word_cats, site_comps):
    #         print('merge because comp.')
    #     elif '*' in site_comps:
    #         print('merge because * comp.')
    #     elif match(word_cats, site_head_comps):
    #         print('merge because head comp.')
    #     elif '*' in site_head_comps:
    #         print('merge because * head comp.')
    #     elif self.is_word_internal(site) or site.internal:
    #         print('merge because word internal')
    #     elif 'ADV' in word_labels and word_tail_set:
    #         print('merge because of tail thingy')
    #     else:
    #         self.merges_to_fix.append((w.copy(), site.get_head().copy()))
    #         print('no local reason for merge:', w,
    #               [f for f in w.features if f.startswith('CAT:')])
    #         print('site:', site,
    #               [f for f in site.features if f.startswith('COMP') or f.startswith('SPEC')])
    #         print('site head:', site.get_head(),
    #               [f for f in site.get_head().features if f.startswith('COMP') or f.startswith('SPEC')])
