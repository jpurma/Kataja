from kataja.saved.movables.Tree import Tree


class TreeManager:

    def __init__(self, forest):
        self.f = forest
        self._update_trees = True

    def get_tree_by_top(self, top_node):
        """ Return tree where this node is the top node
        :param top_node:
        :return:
        """
        for tree in self.f.trees:
            if tree.top is top_node:
                return tree

    def reserve_update_for_trees(self, value=None):
        """ Tree members may have changed, go through them when updating them the next time.
        :param value: not used, it is for BaseModel compatibility
        :return:
        """
        self._update_trees = True

    def update_trees(self):
        """ Rebuild all trees, but try to be little smart about it: Tree where one node is added
        to top should keep its identity, and just reset the top node to be the new node.
        :return:
        """
        invalid_trees = []
        valid_tops = set()
        invalid_tops = set()
        for tree in self.f.trees:
            if not tree.top:
                if not tree.numeration:
                    print('tree without top, removing it')
                    self.remove_tree(tree)
            elif not tree.top.is_top_node():
                invalid_trees.append(tree)
                invalid_tops.add(tree.top)
            elif tree.top in tree.deleted_nodes:
                invalid_trees.append(tree)
                invalid_tops.add(tree.top)
            else:
                valid_tops.add(tree.top)
        invalid_tops -= valid_tops
        top_nodes = set()
        for node in self.f.nodes.values():
            if node.is_top_node():
                top_nodes.add(node)
        unassigned_top_nodes = top_nodes - valid_tops
        # In   (Empty)
        #       /  \
        #     TrA  (Empty)
        #
        # Have TrA to take over the empty nodes
        for node in list(unassigned_top_nodes):
            for child in node.get_children(similar=False, visible=False):
                if child in invalid_tops:
                    tree = self.get_tree_by_top(child)
                    tree.top = child
                    tree.update_items()
                    invalid_tops.remove(child)
                    invalid_trees.remove(tree)
                    unassigned_top_nodes.remove(node)
                    break

        # Create new trees for other unassigned nodes:
        for node in unassigned_top_nodes:
            self.create_tree_for(node)
        # Remove trees that are part of some other tree
        for tree in invalid_trees:
            self.remove_tree(tree)

        if self._update_trees:
            for tree in self.f.trees:
                tree.update_items()

        self._update_trees = False

        # Remove this if we found it to be unnecessary -- it is slow, and these problems
        # shouldn't happen -- this is more for debugging
        # Go through all nodes and check if they are ok.
        if True:
            for node in self.f.nodes.values():
                if node.is_top_node():
                    if not self.get_tree_by_top(node):
                        print('no tree found for potential top node: ', node)
                else:
                    # either parent should have the same trees or parents together should have same
                    # trees
                    union = set()
                    for parent in node.get_parents(similar=False, visible=False):
                        union |= parent.trees
                    problems = node.trees ^ union
                    if problems:
                        print('problem with trees: node %s belongs to trees %s, but its parents '
                              'belong to trees %s' % (node, node.trees, union))

    def create_tree_for(self, node):
        """ Create new trees around given node.
        :param node:
        :return:
        """
        tree = Tree(top=node)
        self.f.add_to_scene(tree)
        self.f.trees.insert(0, tree)
        tree.show()
        tree.update_items()
        return tree

    def remove_tree(self, tree):
        """ Remove trees that has become unnecessary: either because it is subsumed into another
        trees or because it is empty.
        :param tree:
        :return:
        """
        for node in tree.sorted_nodes:
            tree.remove_node(node)
        if tree in self.f.trees:
            self.f.trees.remove(tree)
        self.f.remove_from_scene(tree)