

from kataja.saved.Forest import Forest


class EditableForest(Forest):

    def forest_edited(self):
        super().forest_edited()
        print('doing nodes to synobjs in forest_edited')
        self.syntax.nodes_to_synobjs(self, self.trees)
