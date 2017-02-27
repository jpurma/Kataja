from collections import Counter, defaultdict

from kataja.saved.movables.Tree import Tree
from kataja.utils import time_me


class TreeManager:

    def __init__(self, forest):
        self.f = forest

    @time_me
    def update_trees(self):
        def count_top_nodes_for_each_node(top, n, btrees):
            tops_for_node[n].append(top)
            for tree in n.trees:
                if tree not in btrees:
                    btrees.append(tree)
            for child in n.get_children(similar=False, visible=False):
                count_top_nodes_for_each_node(top, child, btrees)

        tree_candidates = []
        used_trees = set()
        tops_for_node = defaultdict(list)

        for node in self.f.nodes.values():
            if not node.get_parents(similar=True, visible=True):
                if len(node.trees) > 1:
                    for tree in list(node.trees):
                        if tree.top is not node:
                            node.trees.remove(tree)
                best_trees = list(node.trees)
                count_top_nodes_for_each_node(node, node, best_trees)
                tree_candidates.append((node, best_trees))

        for top, best_trees in tree_candidates:
            available_trees = [t for t in best_trees if t not in used_trees]
            if available_trees:
                tree = available_trees[0]
                used_trees.add(tree)
                tree.top = top
                tree.update_items()
            else:
                tree = self.create_tree_for(top)
                used_trees.add(tree)
        for node, tops in tops_for_node.items():
            for tree in list(node.trees):
                if tree.top not in tops:
                    tree.remove_node(node)
        for tree in self.f.trees:
            if tree not in used_trees:
                self.remove_tree(tree)

    @time_me
    def create_tree_for(self, node):
        """ Create new trees around given node.
        :param node:
        :return:
        """
        tree = Tree(top=node)
        self.f.add_to_scene(tree)
        self.f.trees.insert(0, tree)
        #tree.show()
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