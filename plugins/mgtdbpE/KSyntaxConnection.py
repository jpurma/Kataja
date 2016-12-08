from kataja.SavedObject import SavedObject
from kataja.singletons import ctrl
from syntax.SyntaxConnection import SyntaxConnection
from mgtdbpE.Parser import load_grammar, Parser

class KSyntaxConnection(SyntaxConnection):
    role = "SyntaxConnection"
    supports_editable_lexicon = True

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