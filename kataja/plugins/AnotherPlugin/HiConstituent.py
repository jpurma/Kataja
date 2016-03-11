# coding=utf-8
from kataja.BaseModel import Saved
from syntax.BaseConstituent import BaseConstituent


class HiConstituent(BaseConstituent):
    """ HiConstituent is a slight modification from BaseConstituent.
    Everything that is not explicitly defined here is inherited from parent class."""

    # info for kataja engine on how to display the constituent and what is editable

    # short_name should match with the class we inherited, so that the plugin
    # knows that all "BC":s should be replaced with this version.
    short_name = "BC"

    # 'viewable' names the fields that should be visible in graphical representation of this kind of
    #  element. Syntax for defining viewable and editable fields can be found in ...
    viewable = BaseConstituent.viewable.copy()
    viewable['hi'] = {'order': 15}
    # 'editable' names the fields that should be editable.
    editable = BaseConstituent.editable.copy()
    editable['hi'] = {'order': 15}

    def __init__(self, **kw):
        """
         """
        super().__init__(**kw)
        self.hi = 'hi'

    def __repr__(self):
        if self.is_leaf():
            return 'HiConstituent(id=%s)' % self.label
        else:
            return "[ %s ]" % (' '.join((x.__repr__() for x in self.parts)))

    def copy(self):
        """ Make a deep copy of constituent. Useful for picking constituents from Lexicon.
        :return: BaseConstituent
        """
        nc = super().copy()
        nc.hi = self.hi
        return nc

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    hi = Saved("hi")
