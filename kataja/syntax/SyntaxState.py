

class SyntaxState:
    """ This is a simple class to provide a common format for syntactic objects when they are
    a) restored from stored/pickled data or
    b) built by syntax
    SyntaxStates are turned into nodes by separate syntactic_state_to_nodes -function. These are
    kept separate because SyntaxState is only about syntactic objects and shouldn't depend on
    or refer to Nodes and other Kataja visualisation objects.

    There is a corresponding DerivationStep -object in kataja/saved.

    Objects in Kataja's side of syntax/Kataja -division should be able to rely that SyntaxState
    has at least the fields defined here (though they can remain empty), otherwise basic functionality may break down,
    badly.
    """

    def __init__(self, tree_roots=None, numeration=None, msg=None, gloss=None,
                 groups=None, state_id=0, parent_id=None, semantic_hierarchies=None, log=None):
        self.tree_roots = tree_roots or []
        self.numeration = numeration or []
        self.msg = msg or ''
        self.gloss = gloss or ''
        self.groups = groups or []
        self.state_id = state_id
        self.parent_id = parent_id
        self.semantic_hierarchies = semantic_hierarchies or []
        self.log = log or []




