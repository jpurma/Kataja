import kataja.globals as g

from kataja.nodes.ConstituentNode import ConstituentNode
from kataja.nodes.AttributeNode import AttributeNode
from kataja.nodes.BaseConstituentNode import BaseConstituentNode
from kataja.nodes.FeatureNode import FeatureNode
from kataja.nodes.GlossNode import GlossNode
from kataja.nodes.PropertyNode import PropertyNode
from kataja.nodes.CommentNode import CommentNode
from kataja.nodes.Node import Node

from kataja.Edge import Edge

from kataja.Forest import Forest
from kataja.ForestSettings import ForestSettings, ForestRules
from kataja.managers.ChainManager import ChainManager
from kataja.DerivationStep import DerivationStep, DerivationStepManager

from syntax.ConfigurableConstituent import ConfigurableConstituent
from syntax.BaseConstituent import BaseConstituent
from syntax.BaseFeature import BaseFeature

# These asserts prevent automated cleanups from removing imports above as unused
# Node types
assert BaseConstituentNode
assert AttributeNode
assert FeatureNode
assert GlossNode
assert PropertyNode
assert CommentNode

# Edge types
assert Edge

# Forest and its sub managers
assert Forest
assert ChainManager
assert DerivationStep, DerivationStepManager
assert ForestSettings
assert ForestRules

# Syntax
assert ConfigurableConstituent
assert BaseConstituent
assert BaseFeature

# We could use globals but it is safer this way: you can only create objects listed here.
factory_models = {ConstituentNode, BaseConstituentNode, AttributeNode, FeatureNode, GlossNode,
                  PropertyNode, CommentNode, Edge, Forest,
                  DerivationStep, DerivationStepManager, ForestSettings, ForestRules,
                  ConfigurableConstituent, BaseConstituent, BaseFeature}
factory_dict = {}
for value in factory_models:
    factory_dict[value.short_name] = value


node_classes = {g.CONSTITUENT_NODE: ConstituentNode, g.ABSTRACT_NODE: Node,
                g.FEATURE_NODE: FeatureNode, g.GLOSS_NODE: GlossNode,
                g.ATTRIBUTE_NODE: AttributeNode, g.PROPERTY_NODE: PropertyNode,
                g.COMMENT_NODE: CommentNode}

edge_class = Edge

synobj_classes = {'constituent': ConfigurableConstituent, 'feature':
    BaseFeature}


def create(object_class_name, *args, **kwargs):
    """ Create empty kataja object stubs, to be loaded with correct values.
    :param object_class_name: __name__ of the original object
    :param args: any args delivered for the object's __init__ -method
    :param kwargs: any kwargs delivered for the object's __init__ -method
    :return: :raise TypeError:
    """
    class_object = factory_dict.get(object_class_name, None)
    if class_object and callable(class_object):
        # print('creating obj %s with args %s and kwargs %s ' % (object_class_name, str(args), str(kwargs)))
        new_object = class_object(*args, **kwargs)
        return new_object
    else:
        # Here we should try importing classes from probable places (plugins, kataja, syntax)
        raise TypeError('class missing: %s ' % object_class_name)

