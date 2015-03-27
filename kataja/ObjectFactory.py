

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

from syntax.BareConstituent import BareConstituent
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
assert BareConstituent
assert BaseConstituent
assert Feature


class ObjectFactory:
    """

    """

    def __init__(self):
        pass


    def create(self, object_class_name, *args, **kwargs):
        class_object = globals().get(object_class_name, None)
        if class_object:
            # print('creating obj %s with args %s and kwargs %s ' % (object_class_name, str(args), str(kwargs)))
            new_object = class_object(*args, **kwargs)
            # new_object = object.__new__(class_object, *args, **kwargs)
            # print(new_object)
            return new_object
        else:
            # print('class missing: ', object_class_name)
            raise TypeError('class missing: %s ' % object_class_name)
            # print(globals().keys())
