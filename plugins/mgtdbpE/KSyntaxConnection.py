from kataja.SavedObject import SavedObject
from kataja.singletons import ctrl
from syntax.SyntaxConnection import SyntaxConnection
from mgtdbpE.Parser import load_grammar, Parser
from mgtdbpE.OutputTrees import StateTree, XBarTree, BareTree, TracelessXBarTree

class KSyntaxConnection(SyntaxConnection):
    role = "SyntaxConnection"
    supports_editable_lexicon = True
    supports_secondary_labels = True
    display_modes = ['Derivation tree', 'State tree', 'Bare tree', 'XBar tree']

    def __init__(self, classes):
        SavedObject.__init__(self)
        self.Constituent = classes.get('Constituent')
        self.Feature = classes.get('Feature')
        self.trees = []
        self.constituents = {}
        self.features = {}
        self.lexicon = {}
        self.rules = {}
        self.sentence = ''
        self.parser = None
        self.syntax_display_mode = 3
        for key, value in self.options.items():
            self.rules[key] = value.get('default')

    def get_editable_lexicon(self):
        """ If it is possible to provide editable lexicon, where to get it
        :return:
        """
        return '\n'.join([str(const) for const in self.lexicon])

    def derive_from_editable_lexicon(self, lexdata):
        """ Take edited version of get_editable_lexicon output and try derivation with it.
        """
        grammar = load_grammar(g=lexdata)
        self.lexicon = grammar
        ctrl.disable_undo()
        f = ctrl.forest
        f.clear()
        self.parser = Parser(grammar, -0.0001, forest=f)
        # parser doesn't return anything, it pushes derivation steps to forest
        self.parser.parse(sentence=self.sentence, start='C')
        ds = f.derivation_steps
        ds.derivation_step_index = len(ds.derivation_steps) - 1
        ds.jump_to_derivation_step(ds.derivation_step_index)
        f.prepare_for_drawing()
        ctrl.resume_undo()

    def create_derivation(self, forest):
        """ This is always called to initially turn syntax available here and some input into a
        structure. Resulting structures are used to populate a forest.
        :return:
        """
        print('create_derivation: ', self.lexicon)
        self.parser = Parser(self.lexicon, -0.0001, forest=forest)
        # parser doesn't return anything, it pushes derivation steps to forest
        self.parser.parse(sentence=self.sentence, start='C')
        ds = forest.derivation_steps
        ds.derivation_step_index = len(ds.derivation_steps) - 1
        ds.jump_to_derivation_step(ds.derivation_step_index)

    def set_display_mode(self, i):
        self.syntax_display_mode = i

    def next_display_mode(self):
        self.syntax_display_mode += 1
        if self.syntax_display_mode == len(self.display_modes):
            self.syntax_display_mode = 0

    def transform_trees_for_display(self, synobjs):
        if self.syntax_display_mode == 0:
            # Just derivation trees
            return synobjs
        elif self.syntax_display_mode == 1:
            # StateTree(dt)
            res = []
            for synobj in synobjs:
                const = StateTree(synobj).to_constituent()
                res.append(const)
            return res
        elif self.syntax_display_mode == 2:
            # BareTree(dt)
            res = []
            for synobj in synobjs:
                const = BareTree(synobj).to_constituent()
                res.append(const)
            return res
        elif self.syntax_display_mode == 3:
            # XBarTree(dt)
            res = []
            for synobj in synobjs:
                const = TracelessXBarTree(synobj).to_constituent()
                res.append(const)
            return res

        return synobjs