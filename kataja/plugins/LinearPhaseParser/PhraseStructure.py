
from phrase_structure import PhraseStructure as BasePhraseStructure


# See inherited original:
# https://github.com/pajubrat/parser-grammar/blob/master/phrase_structure.py

class PhraseStructure(BasePhraseStructure):
    id_counter = 0

    def __init__(self, left_constituent=None, right_constituent=None):
        BasePhraseStructure.__init__(self, left_constituent=left_constituent, right_constituent=right_constituent)
        self.key = 0
        self.get_new_key()

    def get_new_key(self):
        PhraseStructure.id_counter += 1
        self.key = PhraseStructure.id_counter
        return self.key

    # Copies a phrase structure
    def copy(self):
        ps_ = PhraseStructure()
        if self.left_const:
            ps_.left_const = self.left_const.copy()
            ps_.left_const.mother = ps_
        if self.right_const:
            ps_.right_const = self.right_const.copy()
            ps_.right_const.mother = ps_
        if self.features:
            ps_.features = self.features.copy()
        ps_.morphology = self.morphology
        ps_.internal = self.internal
        ps_.adjunct = self.adjunct
        ps_.find_me_elsewhere = self.find_me_elsewhere
        ps_.identity = self.identity
        # This key is an added property, it is needed to help constituents recognize when they have the same origin
        # across derivation steps, even if they are actually copies of each other. This way Kataja doesn't
        # try to remove them from display when moving to next derivation step and replace them with new constituents.
        ps_.key = self.key
        return ps_

    # extract_pro and merge are exact copies of code from phrase_structure.PhraseStructure, the difference is that when
    # they are here, they create our PhraseStructures instead of phrase_structure.PhraseStructures. This should be kept
    # up-to-date with the changes in pajubrat/parser-grammar
    #
    # COPIED CODE STARTS

    # This extracts a pro-element from a primitive head
    def extract_pro(self):
        phi_set = set()

        # Only phi-active head can contain a pro-element
        if 'ARG' in self.features:
            # Collect phi-features
            for f in self.features:
                if f[:4] == 'PHI:':
                    phi_set.add(f)
            # Construct a pronominal phi-set
            if phi_set:
                # Assumption 1. Pro-element is a constituent
                pro = PhraseStructure()

                # Assumption 2. Pro-element has the phi-features from the host
                pro.features = pro.features | phi_set

                # Assumption 3. Pro-element has label D
                pro.features.add('CAT:D')

                # Assumption 4. Pro-element is printed out as 'pro'
                pro.features.add('PF:pro')

                # Assumption 5. Pro-element is phonologically covert
                pro.silence_phonologically()

                # Assumption 6. Pro-element is a copy
                pro.find_me_elsewhere = True

                # Assumption 7. Pro-element can be created only from a consistent phi-set
                if not pro.phi_conflict():
                    return pro
            return None

    # Merges 'ps' to 'self' at 'direction, i.e. H.merge(G, 'right'') = [H G]
    def merge(self, ps, direction='right'):

        new_ps = None               # The resulting new complex constituent
        left = False
        right = False

        if self.mother:             # Determines whether 'self' is left or right
            if self.is_left():
                left = True
            else:
                right = True

        old_mother = self.mother    # Store link between mother and self

        # Create new constituent
        if direction == 'left':
            new_ps = PhraseStructure(ps, self)          # An elementary Merge operation
        if direction == 'right':
            new_ps = PhraseStructure(self, ps)          # An elementary Merge operation

            if self.adjunct and self.is_primitive():    # Percolation adjuncthood from head to phrase
                new_ps.adjunct = True
                self.adjunct = False

        # Put the new constituent countercyclically into the tree into the position of original 'self'
        if right:
            old_mother.right_const = new_ps
        if left:
            old_mother.left_const = new_ps
        new_ps.mother = old_mother

        return new_ps.get_top()

    # COPIED CODE ENDS
