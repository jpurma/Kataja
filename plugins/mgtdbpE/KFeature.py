from syntax.BaseFeature import BaseFeature
from kataja.SavedField import SavedField
from mgtdbpE.Feature import Feature


class KFeature(Feature, BaseFeature):
    replaces = "BaseFeature"
    syntactic_object = True

    editable = {}
    addable = {}

    def __init__(self, name=None, value=None):
        BaseFeature.__init__(self)
        Feature.__init__(self, name, value)
        self.assigned = True
        self.family = ''

    def __str__(self):
        return repr(self)

    def __hash__(self):
        return hash(str(self))

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    ftype = SavedField("ftype")
    value = SavedField("value")
