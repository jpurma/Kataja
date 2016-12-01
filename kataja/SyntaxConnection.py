
from kataja.KatajaFactory import KatajaFactory


class SyntaxConnection:
    """ This class is an interface for attempting syntactic operations on syntaxes that may not
    support them. So this defines operations generally useful or needed and hides the troubles of
    looking for their implementation. Syntax implementations should look here for what is
    expected from them. Notice the call stack on some commands: not everything need to be
    implemented, if something is not found, the next more generic command is attempted.

    One SyntaxConnection is created per forest.

    Of course, a plugin can subclass and replace this to create an interface to plugin's more
    exotic features.
    """

    def __init__(self, classes: KatajaFactory):
        self.Constituent = classes.get('Constituent')
        self.Feature = classes.get('Feature')
        self.FL = classes.get('FL')()

    def get_trees(self):
        """ List the constituent structures of the workspace, represented by their topmost element
        """
        if hasattr(self.FL, 'get_trees'):
            return self.FL.get_trees()
        else:
            raise NotImplementedError

    def get_constituent_from_lexicon(self, identifier):
        """ Fetch constituent from lexicon
        :param identifier:
        :return:
        """
        if hasattr(self.FL, 'get_constituent_from_lexicon'):
            return self.FL.get_constituent_from_lexicon(identifier)
        else:
            raise NotImplementedError

    def get_feature_from_lexicon(self, identifier):
        """ Fetch the feature matching the key from workspace
        :param identifier:
        :return:
        """
        if hasattr(self.FL, 'get_feature_from_lexicon'):
            return self.FL.get_feature_from_lexicon(identifier)
        else:
            raise NotImplementedError

    def merge(self, A, B, merge_type=None):
        """ Do Merge of given type, return result
        :param A:
        :param B:
        :param merge_type:
        :return:
        """
        if hasattr(self.FL, 'merge'):
            return self.FL.merge(A, B, merge_type=merge_type)
        else:
            raise NotImplementedError


    def linearize(self, a, linearization_type=None):
        """ Do linearisation for a structure, there may be various algorithms
        :param a:
        :param linearization_type: 'implicit', 'kayne' etc. if empty, use rules set for this FL
        :return: list of leaf constituents ?
        """
        if hasattr(self.FL, 'linearize'):
            return self.FL.linearize(a, linearization_type=linearization_type)
        else:
            raise NotImplementedError

    def precedes(self, a, b, linearization_type=None):
        """
        :param a:
        :param b:
        :param linearization_type: 'implicit', 'kayne' etc. if empty, use rules set for this FL.
        :return: 1 if a precedes b, -1 if b precedes b, 0 if cannot say
        """
        if hasattr(self.FL, 'precedes'):
            return self.FL.precedes(a, b, linearization_type=linearization_type)
        else:
            raise NotImplementedError

    def feature_check(self, suitor, bride):
        """ Check if the features(?) match(?)
        :param suitor:
        :param bride:
        :return: bool
        """
        if hasattr(self.FL, 'feature_check'):
            return self.FL.feature_check(suitor, bride)
        else:
            raise NotImplementedError

    def c_commands(self, A, B):
        """ Evaluate if A C-commands B
        :param A:
        :param B:
        :return: bool
        """
        if hasattr(self.FL, 'c_commands'):
            return self.FL.c_commands(A, B)
        else:
            raise NotImplementedError

    def parse(self, sentence, silent=False, **kwargs):
        """ Returns structure (constituent or list of constituents) if given sentence can be parsed. Not
        necessary to implement.
        :param sentence:
        :param silent:
        :return: :raise "Word '%s' missing from the lexicon" % word:
        """
        if hasattr(self.FL, 'parse'):
            return self.FL.parse(sentence, silent=silent, **kwargs)
        else:
            raise NotImplementedError

    # Direct editing of FL constructs ##########################
    # these methods don't belong to assumed capabilities of FL, they are to allow Kataja editing
    # capabilities to directly create and modify FL structures.

    def create_constituent(self, **kw):
        """ Create constituent with provided values and return it
        :param kw:
        :return: IConstituent
        """

        if hasattr(self.FL, 'create_constituent'):
            return self.FL.create_constituent(**kw)
        else:
            return self.Constituent(**kw)

    def get_constituent(self, key):
        """ Fetch the constituent matching the key from workspace
        :param key:
        :return:
        """
        if hasattr(self.FL, 'get_constituent'):
            return self.FL.get_constituent(key)
        else:
            raise NotImplementedError

    def get_feature(self, key):
        """ Fetch the feature matching the key from workspace
        :param key:
        :return:
        """
        if hasattr(self.FL, 'get_features'):
            return self.FL.get_feature(key)
        else:
            raise NotImplementedError

    def construct(self, parent, children, purge_existing=True):
        """ Sets up connections between constituents without caring if there are syntactic
        operations to allow that
        :param parent:
        :param children:
        :param purge_existing:
        :return:
        """
        if hasattr(self.FL, 'construct'):
            return self.FL.construct(parent, children, purge_existing=purge_existing)
        else:
            raise NotImplementedError

    def connect(self, parent, child, align=None):
        """ Tries to set a parent-child connection. It may be necessary to
        force parts to be in specific order, alignment can be used to give
        hints about the order
        :param parent:
        :param child:
        :param align: edge alignment
        :return:

        """
        if hasattr(self.FL, 'connect'):
            return self.FL.connect(parent, child, align=align)
        else:
            raise NotImplementedError

    def disconnect(self, parent, child):
        """ Tries to remove parent-child connection. Primitive: may leave binary trees to have empty
        branch.
        :param parent:
        :param child:
        :return:

        """
        if hasattr(self.FL, 'disconnect'):
            return self.FL.disconnect(parent, child)
        else:
            raise NotImplementedError

    def replace(self, old_c, new_c, under_parent=None):
        """ Replace constituent with another, either in all occurences or only under specific parent
        :param old_c:
        :param new_c:
        :param under_parent:
        :return:
        """
        if hasattr(self.FL, 'replace'):
            return self.FL.replace(old_c, new_c, under_parent=under_parent)
        else:
            raise NotImplementedError

    def linearization_types(self) -> list:
        """ Return available options for linearization
        :return:
        """
        if hasattr(self.FL, 'linearization_types'):
            if callable(self.FL.linearization_types):
                return self.FL.linearization_types()
            else:
                return self.FL.linearization_types
        else:
            raise []

    def merge_types(self) -> list:
        """ Provide available merge types
        :return:
        """
        if hasattr(self.FL, 'merge_types'):
            if callable(self.FL.merge_types):
                return self.FL.merge_types()
            else:
                return self.FL.merge_types
        else:
            return []

    def create_feature(self, **kw):
        """ Create feature with provided values and return it
        :param kw:
        :return: IConstituent
        """
        if hasattr(self.FL, 'create_feature'):
            return self.FL.create_feature(**kw)
        else:
            return self.FL.Feature(**kw)

    # these are properties so they will get docstrings. Instead of reimplementing methods they should
    # use the base implementation and other implementations should modify the referred dicts instead.

    @property
    def available_rules(self):
        """ Return dict of info about features offered by this FL implementation.
        These may be used to create UI choices for these rules or limit available actions.

        Dict values should be dicts with at least
         {"options":[list of option_keys (str)], "default":option_key}
        :return: dict of rules
        """
        if hasattr(self.FL, 'available_rules'):
            if callable(self.FL.available_rules):
                return self.FL.available_rules()
            else:
                return self.FL.available_rules
        else:
            return {}

    def rules(self):
        """ Return dict of currently active rules
        :return: dict of rule:value -pairs.
        """
        if hasattr(self.FL, 'rules'):
            if callable(self.FL.rules):
                return self.FL.rules()
            else:
                return self.FL.rules
        else:
            return {}

    @property
    def ui_strings(self):
        """ Provide a dict that provides user-readable names for option_keys and help text for them if
        required.
        :return: dict where keys are option_keys and values are (readable_name, help_text) -tuples
        """
        if hasattr(self.FL, 'ui_strings'):
            if callable(self.FL.ui_strings):
                return self.FL.ui_strings()
            else:
                return self.FL.ui_strings
        else:
            return {}
