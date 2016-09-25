import kataja.globals as g

# We could use globals but it is safer this way: you can only create objects listed here.


class KatajaFactory:
    def __init__(self):
        """ Load factory with default classes for objects. Plugins can overload these with their
        own classes. """

        self.default_models = {}
        self.default_edge_class = None
        self.default_node_classes = {}
        self.base_name_to_plugin_class = {}
        self.plugin_name_to_base_class = {}

        self.classes = {}
        self.nodes = {}
        self.node_info = {}
        self.node_types_order = []
        self.edge_class = None

    def late_init(self):
        """ Import and set available all of the default classes """

        from kataja.saved.movables.nodes.AttributeNode import AttributeNode
        from kataja.saved.movables.nodes.BaseConstituentNode import BaseConstituentNode
        from kataja.saved.movables.nodes.CommentNode import CommentNode
        from kataja.saved.movables.nodes.ConstituentNode import ConstituentNode
        from kataja.saved.movables.nodes.FeatureNode import FeatureNode
        from kataja.saved.movables.nodes.GlossNode import GlossNode
        from kataja.saved.movables.Node import Node
        from kataja.saved.movables.nodes.PropertyNode import PropertyNode
        from kataja.saved.Group import Group
        from kataja.saved.DerivationStep import DerivationStep, DerivationStepManager
        from kataja.saved.Edge import Edge
        from kataja.saved.Forest import Forest
        from kataja.saved.ForestSettings import ForestSettings, ForestRules
        from kataja.saved.ForestKeeper import ForestKeeper
        from kataja.saved.movables.Tree import Tree
        from syntax.BaseFeature import BaseFeature
        from syntax.ConfigurableConstituent import ConfigurableConstituent
        from syntax.BaseConstituent import BaseConstituent
        from syntax.BaseFL import FL

        self.default_models = {ConstituentNode, BaseConstituentNode, AttributeNode, FeatureNode,
                               GlossNode, PropertyNode, CommentNode, Edge, Forest, DerivationStep,
                               DerivationStepManager, ForestSettings, ForestRules,
                               ConfigurableConstituent, BaseFeature, Tree,
                               Group, FL, ForestKeeper, BaseConstituent}

        self.default_node_classes = {g.CONSTITUENT_NODE: ConstituentNode, g.ABSTRACT_NODE: Node,
                                     g.FEATURE_NODE: FeatureNode, g.GLOSS_NODE: GlossNode,
                                     g.ATTRIBUTE_NODE: AttributeNode, g.PROPERTY_NODE: PropertyNode,
                                     g.COMMENT_NODE: CommentNode}

        self.default_edge_class = Edge

        self.classes = {}
        for class_object in self.default_models:
            self.classes[class_object.__name__] = class_object
        self.nodes = self.default_node_classes.copy()
        self.edge_class = self.default_edge_class
        self.base_name_to_plugin_class = {}
        self.plugin_name_to_base_class = {}
        self.update_node_info()

    @property
    def Constituent(self):
        return self.get('ConfigurableConstituent')

    @property
    def Feature(self):
        return self.get('BaseFeature')

    @property
    def FL(self):
        return self.get('FL')

    def add_mapping(self, base_class, plugin_class):
        if base_class:
            self.base_name_to_plugin_class[base_class.__name__] = plugin_class
            self.plugin_name_to_base_class[plugin_class.__name__] = base_class
        else:
            self.base_name_to_plugin_class[plugin_class.__name__] = plugin_class
            self.plugin_name_to_base_class[plugin_class.__name__] = plugin_class
        self.classes[plugin_class.__name__] = plugin_class

    def restore_default_classes(self):
        """ Restore all classes to their default implementation """
        self.classes = {}
        for class_object in self.default_models:
            self.classes[class_object.__name__] = class_object
        self.base_name_to_plugin_class = {}
        self.plugin_name_to_base_class = {}
        self.nodes = self.default_node_classes.copy()
        self.edge_class = self.default_edge_class
        self.update_node_info()

    def update_node_info(self):
        self.node_info = {}
        self.node_types_order = []
        for key, nodeclass in self.nodes.items():
            self.node_info[key] = {'name': nodeclass.display_name[0],
                                   'name_pl': nodeclass.display_name[1],
                                   'display': nodeclass.display}
            if nodeclass.display:
                self.node_types_order.append(key)
        self.node_types_order.sort()

    def get(self, class_name):
        if class_name in self.base_name_to_plugin_class:
            return self.base_name_to_plugin_class[class_name]
        else:
            return self.classes[class_name]

    @property
    def ForestKeeper(self):
        return self.get('ForestKeeper')

    def get_original(self, class_name):
        if class_name in self.classes:
            return self.classes[class_name]
        elif class_name in self.plugin_name_to_base_class:
            return self.plugin_name_to_base_class[class_name]

    def find_base_model(self, class_item):
        if class_item in self.default_models:
            return class_item
        elif hasattr(class_item, 'replaces'):
            class_name = class_item.replaces
            for klass in self.default_models:
                if klass.__name__ == class_name:
                    return klass
            raise NameError
        else:
            for base in class_item.__bases__:
                found = self.find_base_model(base)
                if found:
                    return found

    def remove_class(self, class_name):
        """ Remove mappings that replace original class with plugin's class """
        for replaced, class_item_candidate in list(self.base_name_to_plugin_class.items()):
            if class_item_candidate.__name__ == class_name:
                del self.base_name_to_plugin_class[replaced]
                break
        if class_name in self.plugin_name_to_base_class:
            del self.plugin_name_to_base_class[class_name]

    def create(self, object_class_name, *args, **kwargs):
        """ Create empty kataja object stubs, to be loaded with correct values.
        :param object_class_name: __name__ of the original object
        :param args: any args delivered for the object's __init__ -method
        :param kwargs: any kwargs delivered for the object's __init__ -method
        :return: :raise TypeError:
        """
        class_object = self.get(object_class_name)
        if class_object and callable(class_object):
            #print('creating obj %s with args %s and kwargs %s ' % (object_class_name, str(args), str(kwargs)))
            new_object = class_object(*args, **kwargs)
            return new_object
        else:
            # Here we should try importing classes from probable places (plugins, kataja, syntax)
            raise TypeError('class missing: %s ' % object_class_name)
