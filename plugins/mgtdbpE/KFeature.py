from syntax.BaseFeature import BaseFeature
from kataja.SavedField import SavedField
from mgtdbpE.Feature import Feature


class KFeature(Feature, BaseFeature):
    role = "Feature"
    syntactic_object = True

    editable = {}
    addable = {}

    def __init__(self, value='', name=''):
        BaseFeature.__init__(self)
        Feature.__init__(self, value, name)
        self.assigned = True
        self.family = ''

    def compose_html_for_viewing(self, node):
        """ Providing this overrides FeatureNode's attempt to represent feature string
        :return:
        """
        return str(self), ''

    def __str__(self):
        return repr(self)

    def __hash__(self):
        return hash(str(self))

