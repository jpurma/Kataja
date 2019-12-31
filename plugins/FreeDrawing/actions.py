import kataja.globals as g
from kataja.KatajaAction import KatajaAction
from kataja.actions.nodes_panel_actions import AbstractAddNode
from kataja.saved.Edge import Edge
from kataja.singletons import ctrl, log
from kataja.ui_widgets.UIEmbed import EmbedAction
from kataja.utils import guess_node_type


class CreateNewNodeFromText(EmbedAction):
    k_action_uid = 'create_new_node_from_text'
    k_command = 'New node from text'

    k_shortcut = 'Return'
    k_shortcut_context = 'parent_and_children'

    def prepare_parameters(self, args, kwargs):
        ci = self.embed.node_type_selector.currentIndex()
        node_type = self.embed.node_type_selector.itemData(ci)
        guess_mode = self.embed.guess_mode
        focus_point = self.embed.get_marker_point()
        text = self.embed.input_line_edit.text()
        return [focus_point, text], {
            'node_type': node_type,
            'guess_mode': guess_mode
        }

    def method(self, focus_point, text, node_type=None, guess_mode=True):

        """ Create new element according to elements in this embed. Can create
        constituentnodes,
        features, arrows, etc.
        :return: None
        """
        ctrl.focus_point = focus_point
        if (not node_type) or node_type == g.GUESS_FROM_INPUT:
            if guess_mode:
                node_type = guess_node_type(text)
            else:
                node_type = g.CONSTITUENT_NODE
        if node_type == g.TREE:
            node = ctrl.forest.simple_parse(text)
        else:
            node = ctrl.drawing.create_node(pos=focus_point, node_type=node_type, label=text)
        if node:
            node.lock()
        ctrl.ui.close_active_embed()
        ctrl.forest.forest_edited()


class RemoveMerger(KatajaAction):
    k_action_uid = 'remove_merger'
    k_command = 'Remove merger'
    k_tooltip = "Remove intermediate node (If binary branching is assumed, these shouldn't exist.)"

    def prepare_parameters(self, args, kwargs):
        node = self.get_host()
        return [node.uid], kwargs

    def method(self, node_uid):
        """ In cases where there another part of binary merge is removed,
        and a stub edge is left dangling, there is an option to remove the unnecessary
        merge -- this is the triggering host.
        :param node_uid: int or string, node's unique identifier
        :return: None
        """
        ctrl.release_editor_focus()
        node = ctrl.forest.nodes[node_uid]
        children = node.get_children()
        if len(children) != 1:
            log.warn('Trying to remove an intermediate monobranch node, but node "%s" '
                     'is not such node.' % node)
        ctrl.remove_from_selection(node)
        ctrl.drawing.delete_unnecessary_merger(node)
        ctrl.forest.forest_edited()


class RemoveNode(KatajaAction):
    k_action_uid = 'remove_node'
    k_command = 'Delete node'

    def prepare_parameters(self, args, kwargs):
        node = self.get_host()
        return [node.uid], kwargs

    def method(self, node_uid):
        """ Remove given node
        :param node_uid: int or string, node's unique identifier
        :return:
        """
        ctrl.release_editor_focus()
        node = ctrl.forest.nodes[node_uid]
        ctrl.remove_from_selection(node)
        ctrl.drawing.delete_node(node, touch_edges=True)
        ctrl.forest.forest_edited()


# Actions for TouchAreas #######################################


class ConnectNode(KatajaAction):
    k_action_uid = 'connect_node'
    k_command = 'Connect node to'

    def prepare_parameters(self, args, kwargs):
        if not args:
            kwargs = self.sender().click_kwargs
            target = self.get_host()
        else:
            target = args[0]
        if isinstance(target, Edge):
            target = target.end
        return [target.uid], kwargs

    def method(self, target_uid: int, node_uid=0, position='child', new_label='', new_type=0):
        """ Connect a new or an existing node into an an existing node. By default the new node is
        set as a child of the target node, but other positions are possible too.
        """
        target = None
        if target_uid in ctrl.forest.nodes:
            target = ctrl.forest.nodes[target_uid]
        elif target_uid in ctrl.forest.edges:
            edge = ctrl.forest.edges[target_uid]
            target = edge.end
        if node_uid:
            new_node = ctrl.forest.nodes[node_uid]
        else:
            label = new_label or ctrl.drawing.next_free_label()
            new_node = ctrl.drawing.create_node(label=label, relative=target,
                                                node_type=new_type)
        if position == 'child':
            ctrl.drawing.connect_node(parent=target, child=new_node)
        elif position == 'top_left':
            # fixme: check that this is top node
            ctrl.drawing.merge_to_top(target, new_node, merge_to_left=True)
        elif position == 'top_right':
            ctrl.drawing.merge_to_top(target, new_node, merge_to_left=False)
        elif position == 'sibling_left':
            ctrl.drawing.add_sibling_for_constituentnode(new_node, target, add_left=True)
        elif position == 'sibling_right':
            ctrl.drawing.add_sibling_for_constituentnode(new_node, target, add_left=False)
        elif position == 'child_left':
            ctrl.drawing.unary_add_child_for_constituentnode(new_node, target, add_left=True)
        elif position == 'child_right':
            ctrl.drawing.unary_add_child_for_constituentnode(new_node, target, add_left=False)
        ctrl.forest.forest_edited()

    def drop2(self, dropped_node):
        """
        Connect dropped node to host of this TouchArea.
        Connection depends on which merge area this is:
        top left, top right, left, right
        :param dropped_node:
        """
        if isinstance(dropped_node, str):
            dropped_node = self.make_node_from_string(dropped_node)
        if not dropped_node:
            return
        # host is an edge
        ctrl.drawing.insert_node_between(dropped_node, self.host.start, self.host.end,
                                         self._align_left, self.start_point)
        for node in ctrl.dragged_set:
            node.adjustment = self.host.end.adjustment
        message = 'moved node %s to sibling of %s' % (dropped_node, self.host)
        ctrl.forest.forest_edited()
        return message


class MergeToTop(KatajaAction):
    k_action_uid = 'merge_to_top'
    k_command = 'Merge this node to left of topmost node'

    # fixme! also support drag to right

    def prepare_parameters(self, args, kwargs):
        # fixme!
        # if isinstance(dropped_node, str):
        #    dropped_node = self.make_node_from_string(dropped_node)
        node = self.get_host()
        return [node.uid], kwargs

    def method(self, node_uid, left=True):
        """ Merge this node to left of topmost node of node's tree. It's internal merge!
        """
        ctrl.release_editor_focus()
        node = ctrl.forest.nodes[node_uid]
        tops = node.get_highest()
        if len(tops) == 1:
            ctrl.drawing.merge_to_top(tops[0], node, merge_to_left=left)
            ctrl.forest.forest_edited()


class InsertNodeBetween(KatajaAction):
    k_action_uid = 'insert_node_between'
    k_command = 'Insert node between'

    def prepare_parameters(self, args, kwargs):
        node = self.get_host()
        return [node.uid], {}

    def method(self, node_uid):
        """
        Connect dropped node to host of this TouchArea.
        Connection depends on which merge area this is: top left, top right, left, right
        """
        dropped_node = ctrl.forest.nodes.get(node_uid, self.make_node_from_string(node_uid))
        assert (self.host.start and self.host.end)
        adjustment = self.host.end.adjustment
        # host is an edge
        ctrl.drawing.insert_node_between(dropped_node, self.host.start, self.host.end,
                                         self._align_left, self.start_point)

        for node in ctrl.dragged_set:
            node.adjustment = adjustment
        ctrl.forest.forest_edited()
        return 'moved node %s to sibling of %s' % (dropped_node, self.host)


class AddConstituentNode(AbstractAddNode):
    k_action_uid = 'add_constituent_node'
    k_command = 'Add constituent node'
    k_tooltip = 'Create new constituent node'
    node_type = g.CONSTITUENT_NODE

    def enabler(self):
        return True


class AddFeatureNode(AbstractAddNode):
    k_action_uid = 'add_feature_node'
    k_command = 'Add feature node'
    k_tooltip = 'Create new feature node'
    node_type = g.FEATURE_NODE

    def enabler(self):
        return True


class SetProjectingNode(KatajaAction):
    k_action_uid = 'set_projecting_node'
    k_command = 'Set projecting node'
    k_tooltip = 'Set which child constituent projects to this constituent'

    def prepare_parameters(self, args, kwargs):
        button_group = self.sender()
        heads = []
        for button in button_group.buttons():
            if button.isChecked():
                child = ctrl.forest.nodes.get(button.my_value, None)
                if child:
                    heads += child.heads
        host = self.get_host()
        return [host.uid, [x.uid for x in heads]], kwargs

    def method(self, node_uid, projecting_uids):
        """ Set which child constituent projects to this constituent
        :param node_uid: int or string, node's unique identifier
        :param projecting_uids: list of uids, projecting nodes' unique identifiers
        """
        if isinstance(projecting_uids, (str, int)):
            projecting_uids = [projecting_uids]
        node = ctrl.forest.nodes[node_uid]
        heads = [ctrl.forest.nodes[uid] for uid in projecting_uids]
        node.set_heads(heads)
        ctrl.forest.forest_edited()
        embed = ctrl.ui.active_embed
        if embed:
            embed.update_fields()


class SetLabel(KatajaAction):
    k_action_uid = 'set_label'
    k_command = 'Set label'

    def method(self, node_uid, label):
        node = ctrl.forest.nodes[node_uid]
        if node and node.syntactic_object:
            node.syntactic_object.label = label


class SetIndex(KatajaAction):
    k_action_uid = 'set_index'
    k_command = 'Set index'

    def method(self, node_uid, index):
        node = ctrl.forest.nodes[node_uid]
        if node:
            node.index = index


class RotateChildren(KatajaAction):
    k_action_uid = 'rotate_children'
    k_command = 'Switch left and right children'
    k_tooltip = "Switch the order of children for this node"

    def prepare_parameters(self, args, kwargs):
        node = self.get_host()
        return [node.uid], kwargs

    def method(self, node_uid):
        """ In cases where there another part of binary merge is removed,
        and a stub edge is left dangling, there is an option to remove the unnecessary
        merge -- this is the triggering host.
        :param node_uid: int or string, node's unique identifier
        :return: None
        """
        ctrl.release_editor_focus()
        node = ctrl.forest.nodes[node_uid]
        node.rotate_children()
        ctrl.forest.forest_edited()
