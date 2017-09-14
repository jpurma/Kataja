

class SyntaxState:
    """ This is a simple class to provide a common format for syntactic objects when they are
    a) restored from stored/pickled data or
    b) built by syntax
    SyntaxStates are turned into nodes by separate syntactic_state_to_nodes -function. These are
    kept separate because SyntaxState is only about syntactic objects and shouldn't depend on
    or refer to Nodes and other Kataja visualisation objects.

    Objects in Kataja's side of syntax/Kataja -division should be able to rely that SyntaxState
    has at least the fields defined here, otherwise basic functionality may break down, badly.
    """

    def __init__(self, tree_roots=None, numeration=None, msg=None, gloss=None,
                 transferred=None, marked=None, semantic_hierarchies=None):
        self.tree_roots = tree_roots or []
        self.numeration = numeration or []
        self.msg = msg or ''
        self.gloss = gloss or ''
        self.transferred = transferred or []
        self.marked = marked or []
        self.semantic_hierarchies = semantic_hierarchies or []




