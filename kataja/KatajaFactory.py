import kataja.globals as g

# We could use globals but it is safer this way: you can only create objects listed here.


class KatajaFactory:
    def __init__(self):
        """ Load factory with default classes for objects. Plugins can overload these with their
        own classes. """

        self.default_models = {}
        self.default_edge_class = None
        self.default_node_classes = {}

        self.classes = {}
        self.nodes = {}
        self.edge_class = None

    def late_init(self):
        """ Import and set available all of the default classes """

        from kataja.AttributeNode import AttributeNode
        from kataja.BaseConstituentNode import BaseConstituentNode
        from kataja.CommentNode import CommentNode
        from kataja.ConstituentNode import ConstituentNode
        from kataja.FeatureNode import FeatureNode
        from kataja.GlossNode import GlossNode
        from kataja.Node import Node
        from kataja.PropertyNode import PropertyNode
        from kataja.Amoeba import Amoeba
        from kataja.DerivationStep import DerivationStep, DerivationStepManager
        from kataja.Edge import Edge
        from kataja.Forest import Forest
        from kataja.ForestSettings import ForestSettings, ForestRules
        from kataja.Tree import Tree
        from kataja.managers.ChainManager import ChainManager
        from syntax.BaseConstituent import BaseConstituent
        from syntax.BaseFeature import BaseFeature
        from syntax.ConfigurableConstituent import ConfigurableConstituent
        from syntax.BaseFL import FL

        self.default_models = {ConstituentNode, BaseConstituentNode, AttributeNode, FeatureNode,
                               GlossNode, PropertyNode, CommentNode, Edge, Forest, DerivationStep,
                               DerivationStepManager, ForestSettings, ForestRules,
                               ConfigurableConstituent, BaseFeature, Tree,
                               Amoeba, FL}

        self.default_node_classes = {g.CONSTITUENT_NODE: ConstituentNode, g.ABSTRACT_NODE: Node,
                                     g.FEATURE_NODE: FeatureNode, g.GLOSS_NODE: GlossNode,
                                     g.ATTRIBUTE_NODE: AttributeNode, g.PROPERTY_NODE: PropertyNode,
                                     g.COMMENT_NODE: CommentNode}

        self.default_edge_class = Edge

        self.classes = {}
        for class_object in self.default_models:
            self.classes[class_object.short_name] = class_object
        self.nodes = self.default_node_classes.copy()
        self.edge_class = self.default_edge_class

    @property
    def Constituent(self):
        return self.classes['C']

    @property
    def Feature(self):
        return self.classes['F']

    @property
    def FL(self):
        return self.classes['FL']

    def add_class(self, key, class_object):
        """ Add or replace class with given key """
        self.classes[key] = class_object

    def restore_default_classes(self):
        """ Restore all classes to their default implementation """
        self.classes = self.default_models.copy()
        self.nodes = self.default_node_classes.copy()
        self.edge_class = self.default_edge_class

    def get(self, key):
        return self.classes[key]

    def remove_class(self, key):
        """ Restore single class to its default implementation """
        found = False
        for class_object in self.default_models:
            if class_object.short_name == key:
                found = True
                self.classes[key] = class_object
                break
        if key in self.classes and not found:
            del self.classes[key]

    def create(self, object_class_name, *args, **kwargs):
        """ Create empty kataja object stubs, to be loaded with correct values.
        :param object_class_name: __name__ of the original object
        :param args: any args delivered for the object's __init__ -method
        :param kwargs: any kwargs delivered for the object's __init__ -method
        :return: :raise TypeError:
        """
        class_object = self.classes.get(object_class_name, None)
        if class_object and callable(class_object):
            # print('creating obj %s with args %s and kwargs %s ' % (object_class_name, str(args), str(kwargs)))
            new_object = class_object(*args, **kwargs)
            return new_object
        else:
            # Here we should try importing classes from probable places (plugins, kataja, syntax)
            raise TypeError('class missing: %s ' % object_class_name)

