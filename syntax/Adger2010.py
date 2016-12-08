# coding=utf-8


class AdgerConstituent(BaseConstituent):


    def __init__(self, cat_feature=None, sel_feature=None, **kw):
        """ This is a constituent that
         """
        super().__init__(**kw)
        self.cat_feature = cat_feature
        self.sel_feature = sel_feature
