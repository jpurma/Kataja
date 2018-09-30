from kataja.parser.SuperParser import SuperParser
from kataja.saved.Forest import Forest


class EditableForest(Forest):

    def forest_edited(self):
        super().forest_edited()
        print('doing nodes to synobjs in forest_edited')
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
        result = [self.inode_to_constituentnode(inode) for inode in self.parser.nodes]
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
