from kataja.parser.SuperParser import SuperParser
from plugins.FreeDrawing.FreeDrawing import FreeDrawing
from kataja.saved.Forest import Forest


class EditableForest(Forest):

    def __init__(self, heading_text='', comments=None, syntax=None):
        Forest.__init__(self, heading_text=heading_text, comments=comments, syntax=syntax)
        self.should_add_to_scene = False

    def init_factories(self):
        super().init_factories()
        self.drawing = FreeDrawing(self)

    def clear(self):
        super().clear()
        self.drawing = FreeDrawing(self)

    def forest_edited(self):
        super().forest_edited()
        self.syntax.nodes_to_synobjs(self, self.trees)

    def simple_parse(self, string):
        """ Parse the text as merged nodes in the current forest.
        :param string:
        """
        if not string:
            return None
        old_should_add = self.should_add_to_scene
        self.should_add_to_scene = True
        # the heavy work is done in SuperParser ###
        self.parser = SuperParser(string)
        result = [self.parser.inode_to_constituentnode(inode) for inode in self.parser.nodes]
        if len(result) > 1:
            right = result.pop()
            while result:
                left = result.pop()
                right = self.drawing.create_merger_node(left, right, new=left, heads=left)
            result = right
        elif result:
            result = result[0]
        self.should_add_to_scene = old_should_add
        return result
