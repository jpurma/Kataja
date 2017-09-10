import kataja.globals as g

# We could use globals but it is safer this way: you can only create objects listed here.

def get_role(classobj):
    return getattr(classobj, 'role', classobj.__name__)


class KatajaFactory:
    def __init__(self):
        """ Factory creates object instances of desired class. Factory is used instead of direct
        instance creation to allow flexibility in defining what exactly is the class
        implementation we are going to use.

        Example:
        A plugin can replace Constituent with its own implementation, and by using
        katajafactory.get('Constituent')() as constructor you would get this
        replaced implementation -- if you are working with plugin activated, you'd want all
        Constituents to be these. If your code would 'import syntax.Constituent' and create
        'Constituent()', it would cause problems when a plugin that replaces Constituent is active.

        Of course, when you are working within plugin, you can directly import and construct
        objects, assuming we are not going to have multiple plugins active. (That feature would
        lead to lots of problems.)
        """

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
        self.base_node_class = None

        self.node_type_to_edge_type = {}
        self.edge_type_to_node_type = {}

    def late_init(self):
        """ Import and set available all of the default classes """

        from kataja.saved.movables.nodes.CommentNode import CommentNode
        from kataja.saved.movables.nodes.ConstituentNode import ConstituentNode
        from kataja.saved.movables.nodes.FeatureNode import FeatureNode
        from kataja.saved.movables.nodes.GlossNode import GlossNode
        from kataja.saved.movables.Node import Node
        from kataja.saved.Group import Group
        from kataja.saved.DerivationStep import DerivationStep, DerivationStepManager
        from kataja.saved.Edge import Edge
        from kataja.saved.Forest import Forest
        from kataja.saved.KatajaDocument import KatajaDocument
        from syntax.SyntaxConnection import SyntaxConnection
        from syntax.BaseFeature import BaseFeature
        from syntax.ConfigurableConstituent import BaseConstituent

        self.default_models = {ConstituentNode, FeatureNode,
                               GlossNode, CommentNode, Edge, Forest, DerivationStep,
                               DerivationStepManager, BaseConstituent, BaseFeature,
                               Group, KatajaDocument, SyntaxConnection}

        self.default_node_classes = {g.CONSTITUENT_NODE: ConstituentNode,
                                     g.FEATURE_NODE: FeatureNode, g.GLOSS_NODE: GlossNode,
                                     g.COMMENT_NODE: CommentNode}
        # g.ABSTRACT_NODE: Node,

        self.default_edge_class = Edge
        self.base_node_class = Node
        self.node_type_to_edge_type = {}
        self.edge_type_to_node_type = {}

        self.classes = {}
        for class_object in self.default_models:
            role = get_role(class_object)
            self.classes[role] = class_object
        self.nodes = self.default_node_classes.copy()
        self.edge_class = self.default_edge_class
        self.base_name_to_plugin_class = {}
        self.plugin_name_to_base_class = {}
        self.update_node_info()

    def add_mapping(self, base_class, plugin_class):
        plugin_role = get_role(plugin_class)
        if base_class:
            base_role = get_role(base_class)
            self.base_name_to_plugin_class[base_role] = plugin_class
            self.plugin_name_to_base_class[plugin_role] = base_class
            for key, value in list(self.nodes.items()):
                if value == base_class:
                    self.nodes[key] = plugin_class
        else:
            self.base_name_to_plugin_class[plugin_role] = plugin_class
            self.plugin_name_to_base_class[plugin_role] = plugin_class
        self.classes[plugin_role] = plugin_class

    def restore_default_classes(self):
        """ Restore all classes to their default implementation """
        self.classes = {}
        for class_object in self.default_models:
            role = get_role(class_object)
            self.classes[role] = class_object
        self.base_name_to_plugin_class = {}
        self.plugin_name_to_base_class = {}
        self.nodes = self.default_node_classes.copy()
        self.edge_class = self.default_edge_class
        self.update_node_info()

    def update_node_info(self):
        self.node_info = {}
        self.node_types_order = []
        self.node_type_to_edge_type = {}
        self.edge_type_to_node_type = {}
        for node_type, nodeclass in self.nodes.items():
            self.node_info[node_type] = {'name': nodeclass.display_name[0],
                                         'name_pl': nodeclass.display_name[1],
                                         'display': nodeclass.display,
                                         'ui_sheet': nodeclass.ui_sheet}
            if nodeclass.display:
                self.node_types_order.append(node_type)
            self.node_type_to_edge_type[node_type] = nodeclass.default_edge
            self.edge_type_to_node_type[nodeclass.default_edge] = node_type
        self.node_types_order.sort()

    def get(self, class_name):
        if class_name in self.base_name_to_plugin_class:
            return self.base_name_to_plugin_class[class_name]
        else:
            return self.classes[class_name]

    @property
    def KatajaDocument(self):
        return self.get('KatajaDocument')

    def get_original(self, class_name):
        if class_name in self.classes:
            return self.classes[class_name]
        elif class_name in self.plugin_name_to_base_class:
            return self.plugin_name_to_base_class[class_name]

    def find_base_model(self, class_item):
        if class_item in self.default_models:
            return class_item
        elif hasattr(class_item, 'role'):
            class_name = class_item.role
            for klass in self.default_models:
                role = get_role(klass)
                if role == class_name:
                    return klass
            raise NameError
        else:
            for base in class_item.__bases__:
                found = self.find_base_model(base)
                if found:
                    return found

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

