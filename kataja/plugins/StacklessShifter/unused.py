# def _find_first_left(node):
#     if node.parts:
#         return _find_first_left(node.parts[0])
#     else:
#         return node

# elif item == '^':
#     mover = _find_first_left(tree)
#     mover.has_raised = True
#     tree = Constituent(parts=[mover, tree])

def tree_to_monorail(tree):
    recipe = []

    def _tree_to_monorail(node, spine):
        if len(node.parts) == 2:
            # Left node is built as usual, will return [node.left, spine]
            left = _tree_to_monorail(node.left, spine)
            # Right node is the tricky one, it will return [node.right, [node.left, spine]]
            right = _tree_to_monorail(node.right, left)
            # Merging left and right will create [[node.left, spine], [node.right, [node.left, spine]]]
            # If node = [X, Y], spine = Z
            # this returns [[X, Z], [Y, [X, Z]]]
            #
            #               /\        /\
            #              /\ Z  =>  /\ \
            #             X  Y      X  Z \
            #                            /\
            #                           Y /\
            #                            X  Z
            #
            # if there is no spine, it returns [X, [Y, X]] which is the basic case of merging X and Y in a manner
            # that gives them asymmetrical ordering.
            #
            #                         /\
            #              /\   =>   X /\
            #             X  Y        Y  X
            #
            merged = Constituent(parts=[left, right])
            recipe.append('|')
        elif spine:  # external merge
            # Bottom left node of the branch. If Z is bottom right node (spine) and N is bottom left (node),
            # return [X Y]
            #
            #              /\        /\
            #             N  Z  =>  N  Z
            left = Constituent(label=node.label)
            recipe.append(node.label)
            merged = Constituent(parts=[left, spine])
        else:  # first node
            # Bottom right node of the branch. Just make a simple constituent and return it.
            #
            #             X    =>    X
            merged = Constituent(label=node.label)
            recipe.append(node.label)
        return merged

    return _tree_to_monorail(tree, None), recipe


def find_checked_features_b(mover, spine):
    if mover and mover.head is not spine.head:
        for neg_feature in mover.head.features:
            if neg_feature.sign == '-' or neg_feature.sign == '=' and not neg_feature.checked_by:
                for plus_feature in spine.head.features:
                    if plus_feature.checks or plus_feature.sign:
                        continue
                    elif neg_feature.sign == '-' and neg_feature.name == plus_feature.name:
                        plus_feature.check(neg_feature)
                        return plus_feature, neg_feature, mover.head
                    elif neg_feature.sign == '=' and neg_feature.name == plus_feature.name:
                        plus_feature.check(neg_feature)
                        return plus_feature, neg_feature, spine.head
                return

    def parse_o(self, sentence):
        """ Parse that is greedy to external merge. Do external merge if there would be compatible features w. trunk"""
        # print(f'*** Parsing {sentence}')
        if '[' in sentence:
            return self.analyze_and_make_features(sentence)
        if isinstance(sentence, str):
            words = sentence.split()
        else:
            words = sentence
        tree = None
        for word in words:
            const = self.pick_constituent(word)
            # print('at constituent ', const)
            checking_feats = find_checked_features(const, tree, do_check=False)

            # External merge new constituent
            # print(f'external merge "{const}" into "{tree and tree.head}"')
            tree = Constituent(const.label, parts=[const, tree]) if tree else const
            tree.head = const
            if checking_feats:
                # print('keep going on because ', checking_feats)

                continue
            # print('continue to internal merge: ', checking_feats)
            # Do Internal merge as many times as possible
            mover = find_mover(tree, skip_first=True)
            assert mover is not tree
            checking_feats = find_checked_features(mover, tree)
            self.export_to_kataja(tree, f'External merge {const.label}', mover)
            while checking_feats:
                mover_feat, tree_feat, head = checking_feats
                # print(f'internal merge "{mover.head}" into "{tree.head}", checking feats: {mover_feat}+{tree_feat}')
                tree = Constituent(label=head.label, parts=[mover, tree])
                mover.has_raised = True
                tree.head = head
                mover = find_mover(tree, skip_first=True)
                checking_feats = find_checked_features(mover, tree)
                self.export_to_kataja(tree, f'Internal merge {head.label}', mover)
        return tree


def build_from_recipe(recipe):
    def _find_movable(node, skip_first=False, is_leftmost=False):
        # finds the uppermost result of external merge element (this is recognized by it having flag 'has_raised')
        if not skip_first and not getattr(node, 'has_raised', None) and (node.parts or not is_leftmost):
            return node
        leftmost = True
        for part in node.parts:
            n = _find_movable(part, is_leftmost=leftmost)
            if n:
                return n
            leftmost = False

    tree = None
    for item in recipe:
        if not tree:
            tree = Constituent(item)
        elif item == '|':
            mover = _find_movable(tree, skip_first=True)
            if not mover:
                mover = tree.right
            mover.has_raised = True
            tree = Constituent(parts=[mover, tree])
        else:
            node = Constituent(item)
            tree = Constituent(parts=[node, tree])
        self.export_to_kataja(tree, item)
    return tree


def parse_a(self, sentence):
    """ Parse that is greedy on internal merge: do all internal merges possible before moving to next EM """
    if '[' in sentence:
        return self.analyze_and_make_features(sentence)
    if isinstance(sentence, str):
        words = sentence.split()
    else:
        words = sentence
    tree = None
    for word in words:
        const = self.pick_constituent(word)
        # External merge new constituent
        tree = Constituent(const.label, parts=[const, tree]) if tree else const
        tree.head = const
        # Do Internal merge as many times as possible
        mover = find_mover(tree, skip_first=True)
        assert mover is not tree
        checking_feats = find_checked_features(mover, tree)
        self.export_to_kataja(tree, f'External merge {const.label}', mover)
        while checking_feats:
            mover_feat, tree_feat, head = checking_feats
            tree = Constituent(label=head.label, parts=[mover, tree])
            mover.has_raised = True
            tree.head = head
            mover = find_mover(tree, skip_first=True)
            checking_feats = find_checked_features(mover, tree)
            self.export_to_kataja(tree, f'Internal merge {head.label}', mover)
    return tree
