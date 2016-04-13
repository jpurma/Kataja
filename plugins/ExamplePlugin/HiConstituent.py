# coding=utf-8
from kataja.Saved import SavedField
from syntax.BaseConstituent import BaseConstituent


class HiConstituent(BaseConstituent):
    """ HiConstituent is a slight modification from BaseConstituent.
    Everything that is not explicitly defined here is inherited from parent class."""

    # Info for kataja engine on how to display the constituent and what is editable.
    # Note that when you use inherited list or dict from parent class, don't modify it in place,
    # as the changes will then affect the parent class too. Construct a new list or dict instead,
    # or use methods that result in a new list and then you can modify it at will.
    visible_in_label = BaseConstituent.visible_in_label + ['hi']
    editable_in_label = BaseConstituent.editable_in_label + ['hi']

    def __init__(self, *args, **kwargs):
        """ Constructor for new HiConstituents """
        super().__init__(*args, **kwargs)
        if 'hi' in kwargs:
            self.hi = kwargs['hi']
        else:
            self.hi = 'hello'

    def __repr__(self):
        """ Readable representation for debugging. (E.g. how item will look as a list member,
        when the list is printed out.) You can also define __str__ for even more
        readable output, otherwise __str__ will use __repr__.
        :return:
        """
        if self.is_leaf():
            return 'HiConstituent(id=%s)' % self.label
        else:
            return "[ %s ]" % (' '.join((x.__repr__() for x in self.parts)))

    def copy(self):
        """ Make a deep copy of constituent. Useful for picking constituents from Lexicon.
        :return: HiConstituent
        """
        nc = super().copy()
        nc.hi = self.hi
        return nc

    #  Announce save support for given fields (+ those that are inherited from parent class):
    hi = SavedField("hi")
