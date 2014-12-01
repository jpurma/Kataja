

from kataja.AttributeNode import AttributeNode
from kataja.ChainManager import ChainManager
from kataja.ConstituentNode import ConstituentNode
from kataja.DerivationStep import DerivationStep, DerivationStepManager
from kataja.Edge import Edge
from kataja.FeatureNode import FeatureNode
from kataja.Forest import Forest
from kataja.ForestSettings import ForestSettings, ForestRules
from kataja.GlossNode import GlossNode
from kataja.PropertyNode import PropertyNode
from syntax.BareConstituent import BareConstituent
from syntax.BaseConstituent import BaseConstituent
from syntax.ConfigurableFeature import Feature


class ObjectFactory:

    def __init__(self):
        pass


    def create(self, object_class_name, *args, **kwargs):
        class_object = globals().get(object_class_name, None)
        if class_object:
            #print('creating obj %s with args %s and kwargs %s ' % (object_class_name, str(args), str(kwargs)))
            new_object = class_object(*args, **kwargs)
            #new_object = object.__new__(class_object, *args, **kwargs)
            #print(new_object)
            return new_object
        else:
            #print('class missing: ', object_class_name)
            raise TypeError('class missing: %s ' % object_class_name)
            #print(globals().keys())
