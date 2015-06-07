

from kataja.AttributeNode import AttributeNode
from kataja.ConstituentNode import ConstituentNode
from kataja.FeatureNode import FeatureNode
from kataja.GlossNode import GlossNode
from kataja.PropertyNode import PropertyNode
from kataja.CommentNode import CommentNode

from kataja.Edge import Edge

from kataja.Forest import Forest
from kataja.ForestSettings import ForestSettings, ForestRules
from kataja.ChainManager import ChainManager
from kataja.DerivationStep import DerivationStep, DerivationStepManager

from syntax.ConfigurableConstituent import ConfigurableConstituent
from syntax.BaseConstituent import BaseConstituent
from syntax.ConfigurableFeature import Feature

# These asserts prevent automated cleanups from removing imports above as unused
# Node types
assert ConstituentNode
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
assert Feature

# We could use globals but it is safer this way: you can only create objects listed here.
factory_models = {ConstituentNode, AttributeNode, FeatureNode, GlossNode, PropertyNode, CommentNode, Edge, Forest,
                  DerivationStep, DerivationStepManager, ForestSettings, ForestRules,
                  ConfigurableConstituent, BaseConstituent, Feature}
factory_dict = {}
for value in factory_models:
    factory_dict[value.short_name] = value


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
