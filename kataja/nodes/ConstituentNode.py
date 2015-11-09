# coding=utf-8
# ############################################################################
#
# *** Kataja - Biolinguistic Visualization tool ***
#
# Copyright 2013 Jukka Purma
#
# This file is part of Kataja.
#
# Kataja is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Kataja is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kataja.  If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################
from kataja.nodes.Node import Node
from kataja.nodes.BaseConstituentNode import BaseConstituentNode
from kataja.BaseModel import Saved
from kataja.singletons import ctrl, qt_prefs
from kataja.parser.INodes import ITextNode
import kataja.globals as g

__author__ = 'purma'

xbar_suffixes = ['´', "'", "P", "(1/)", "\1"]


def strip_xbars(al):
    for s in xbar_suffixes:
        if len(al) > len(s) and al.endswith(s):
            return al[:-len(s)]
    else:
        return al


class ConstituentNode(BaseConstituentNode):
    """ ConstituentNode is enriched with few fields that have no syntactic meaning but help with
     reading the trees aliases, indices and glosses.
    """
    name = ('Constituent', 'Constituents')
    short_name = "CN"
    display = True
    wraps = 'constituent'

    visible = {'alias': {'order': 0},
               'index': {'order': 1, 'align': 'line-end', 'style': 'subscript'},
               'label': {'order': 2, 'getter': 'triangled_label'}, 'gloss': {'order': 3}, }
    editable = {'alias': dict(name='Alias', order=3, prefill='alias',
                              tooltip='Non-functional readable label of the constituent'),
                'index': dict(name='Index', order=6, align='line-end', width=20, prefill='i',
                              tooltip='Index to recognize multiple occurences'),
                'label': dict(name='Label', order=9, prefill='label',
                              tooltip='Label of the constituent (functional identifier)', width=200,
                              focus=True, syntactic=True),
                'gloss': dict(name='Gloss', order=12, prefill='gloss',
                              tooltip='translation (optional)', width=200, check_before='is_leaf'),
                'head': dict(name='Head', order=20, tooltip='inherits from',
                             check_before='can_be_projection',
                             option_function='projection_options_for_ui', input_type='multibutton',
                             select_action='constituent_set_head')}
    default_style = {'color': 'content1', 'font': g.MAIN_FONT, 'font-size': 10,
                     'edge': g.CONSTITUENT_EDGE}

    default_edge = {'id': g.CONSTITUENT_EDGE, 'shape_name': 'shaped_cubic', 'color': 'content1',
                    'pull': .24, 'visible': True, 'arrowhead_at_start': False,
                    'arrowhead_at_end': False, 'labeled': False}

    # Touch areas are UI elements that scale with the trees: they can be
    # temporary shapes suggesting to drag or click here to create the
    # suggested shape.

    # touch_areas_when_dragging and touch_areas_when_selected use the same
    # format.

    # 'condition': there are some general conditions implemented in UIManager,
    # but condition can refer to method defined for node instance. When used
    # for when-dragging checks, the method will be called with two parameters
    # 'dragged_type' and 'dragged_host'.
    # 'place': there are some general places defined in UIManager. The most
    # important is 'edge_up': in this case touch areas are associated with
    # edges going up. When left empty, touch area is associated with the node.

    touch_areas_when_dragging = {
        g.LEFT_ADD_TOP: {'condition': ['is_top_node', 'dragging_constituent']},
        g.RIGHT_ADD_TOP: {'condition': ['is_top_node', 'dragging_constituent']},
        g.LEFT_ADD_SIBLING: {'place': 'edge_up', 'condition': 'dragging_constituent'},
        g.RIGHT_ADD_SIBLING: {'place': 'edge_up', 'condition': 'dragging_constituent'},
        g.TOUCH_CONNECT_COMMENT: {'condition': 'dragging_comment'},
        g.TOUCH_CONNECT_FEATURE: {'condition': 'dragging_feature'},
        g.TOUCH_CONNECT_GLOSS: {'condition': 'dragging_gloss'}}

    touch_areas_when_selected = {g.LEFT_ADD_TOP: {'condition': 'is_top_node',
                                                  'action': 'add_top_left'},
                                 g.RIGHT_ADD_TOP: {'condition': 'is_top_node',
                                                   'action': 'add_top_right'},
                                 g.LEFT_ADD_SIBLING: {'place': 'edge_up',
                                                      'action': 'add_sibling_left'},
                                 g.RIGHT_ADD_SIBLING: {'place': 'edge_up',
                                                       'action': 'add_sibling_right'},
                                 g.LEFT_ADD_CHILD: {'condition': 'is_leaf_node',
                                                    'action': 'add_child_left'},
                                 g.RIGHT_ADD_CHILD: {'condition': 'is_leaf_node',
                                                     'action': 'add_child_right'},
                                 g.ADD_TRIANGLE: {'condition': 'can_have_triangle',
                                                  'action': 'add_triangle'},
                                 g.REMOVE_TRIANGLE: {'condition': 'has_triangle',
                                                     'action': 'remove_triangle'}}

    buttons_when_selected = {g.REMOVE_MERGER: {'condition': 'is_unnecessary_merger'}}
    button_definitions = {g.REMOVE_MERGER:
                          {'icon': 'delete_icon',
                           'host': 'node',
                           'role': g.REMOVE_TRIANGLE,
                           'key': g.REMOVE_MERGER,
                           'text': 'Remove this non-merging node',
                           'action': 'remove_merger'}}

    def __init__(self, constituent=None):
        """ Most of the initiation is inherited from Node """
        BaseConstituentNode.__init__(self, constituent=constituent)
        self._index_label = None
        self._index_visible = True
        self.is_trace = False
        self.merge_order = 0
        self.select_order = 0
        self.original_parent = None
        self._projection_color = None
        self._projection_qcolor = None

        # ### Cycle index stores the order when node was originally merged to structure.
        # going up in trees, cycle index should go up too

        # ## use update_visibility to change these: visibility of particular elements
        # depends on many factors

    def after_init(self):
        """ After_init is called in 2nd step in process of creating objects:
        1st wave creates the objects and calls __init__, and then iterates through and sets the
        values. 2nd wave calls after_inits for all created objects. Now they can properly refer
        to each other and know their values.
        :return: None
        """
        self._inode_changed = True
        a = self.as_inode()
        self.update_features()
        self.update_gloss()
        self.update_label()
        self.update_visibility()
        self.update_status_tip()
        self.announce_creation()
        ctrl.forest.store(self)

    def after_model_update(self, updated_fields, update_type):
        """ This is called after the item's model has been updated, to run the side-effects of
         various setters in an order that makes sense.
        :param updated_fields: list of names of fields that have been updated.
        :return: None
        """
        super().after_model_update(updated_fields, update_type)
        update_label = False
        if 'alias' in updated_fields:
            self._inode_changed = True
            update_label = True
        if 'index' in updated_fields:
            self._inode_changed = True
            update_label = True
        if 'gloss' in updated_fields:
            self._inode_changed = True
            self.update_gloss()
            update_label = True
        if 'head' in updated_fields:
            pass
        if update_label:
            self.update_label()

    # properties implemented by syntactic node
    # set_hooks, to be run when values are set

    def impose_order_to_inode(self):
        """ Prepare inode (ITemplateNode) to match data structure of this type of node.
        ITemplateNode has parsed input from latex trees to rows of text or ITextNodes and
        these can be mapped to match Node fields, e.g. label or index. The mapping is
        implemented here, and subclasses of Node should make their mapping.
        :return:
        """
        Node.impose_order_to_inode(self)
        inode = self._inode
        iv = inode.values
        alias = ''
        label = ''
        gloss = ''
        index = ''
        if inode.indices and inode.indices[0]:
            index = inode.indices[0]

        is_leaf = self.is_leaf_node()
        lines = len(inode.rows)
        if lines >= 3:
            alias = inode.rows[0]
            label = inode.rows[1]
            gloss = inode.rows[2]
        elif lines == 2:
            alias = inode.rows[0]
            label = inode.rows[1]
        elif lines == 1 and is_leaf:
            label = inode.rows[0]
        elif lines == 1:
            alias = inode.rows[0]
        iv['alias']['value'] = alias
        iv['label']['value'] = label
        iv['gloss']['value'] = gloss
        iv['index']['value'] = index

    def as_inode(self):
        """ Inject visibility information of 'alias' and 'label' to inode, so
        that some ConstituentNodes may have visible labels and others not.
        :return: INodes or str or tuple of them
        """
        if self._inode is None:
            self._inode = super().as_inode()
        if self._inode_changed:
            self._inode = super().as_inode()
            s = ctrl.forest.settings
            if self.is_leaf_node(only_visible=True) or self.triangle:
                self._inode.values['alias']['visible'] = s.show_leaf_aliases
                self._inode.values['label']['visible'] = s.show_leaf_labels
            else:
                self._inode.values['alias']['visible'] = s.show_internal_aliases
                self._inode.values['label']['visible'] = s.show_internal_labels
        return self._inode

    def if_changed_gloss(self, value):
        """ Synobj changed, but remind to update inodes here
        :param value:
        :return:
        """
        self._inode_changed = True
        self.update_gloss()

    # Saved properties

    # Other properties

    @property
    def gloss_node(self):
        """
        :return:
        """
        gl = self.get_children_of_type(edge_type=g.GLOSS_EDGE)
        return next(gl, None)

    @property
    def raw_alias(self):
        """ Get the unparsed raw version of label (str)
        :return:
        """
        return self.alias

    @property
    def triangled_label(self):
        """ Label with triangled elements concatenated into it
        :return:
        """
        if self.triangle:
            leaves = ITextNode()
            # todo: Use a better linearization here
            for node in ctrl.forest.list_nodes_once(self):
                if node.is_leaf_node(only_visible=False) and node.label:
                    leaves += node.label
                    leaves += ' '
            return leaves.tidy()
        else:
            return self.label

    def update_status_tip(self):
        """ Hovering status tip """
        if self.syntactic_object:
            if self.alias:
                alias = '"%s" ' % self.alias
            else:
                alias = ''
            if self.is_trace:
                name = "Trace"
            if self.is_leaf_node():
                name = "Leaf constituent"
            elif self.is_top_node():
                name = "Root constituent"
            else:
                name = "Inner constituent"
            self.status_tip = "%s Alias: %s Label: %s is_leaf: %s" % (
            name, alias, self.label, self.is_leaf_node())
        else:
            self.status_tip = "Empty, but mandatory constituent position"

    def short_str(self):
        if not self.syntactic_object:
            return 'empty'
        alias = self.alias
        label = self.label
        if isinstance(alias, ITextNode):
            alias = alias.plain_string()
        if isinstance(label, ITextNode):
            label = label.plain_string()
        if alias and label:
            l = ' '.join((str(alias), str(label)))
        elif alias:
            l = str(alias)
        elif label:
            l = str(label)
        else:
            return "no label"
        return l

    def __str__(self):
        if not self.syntactic_object:
            return 'a placeholder for constituent'
        alias = self.alias
        label = self.label
        if alias and label:
            l = ' '.join((str(alias), str(label)))
        elif alias:
            l = str(alias)
        elif label:
            l = str(label)
        else:
            return "anonymous constituent"

        return "constituent '%s' from trees %s" % (l, [t.save_key for t in self.trees])

    def as_bracket_string(self):
        """ returns a simple bracket string representation """
        if self.alias:
            if not self.syntactic_object:
                return '0'
            children = list(self.get_children())
            if children:
                return '[.%s %s ]' % \
                       (self.alias, ' '.join((c.as_bracket_string() for c in children)))
            else:
                return self.alias
        else:
            return super().as_bracket_string()

    def is_unnecessary_merger(self):
        """ This merge can be removed, if one or both children are placeholders
        :return:
        """
        children = list(self.get_all_children())
        lc = len(children)
        if lc == 0:
            return False
        elif lc == 1:
            return True
        good_children = 0
        for child in children:
            if not child.is_placeholder():
                good_children += 1
        return good_children < 2


    def can_be_projection(self):
        """ Node can be projection from other nodes if it has other nodes
        below it.
        It may be necessary to move this check to syntactic level at some
        point.
        :return:
        """
        if ctrl.fs.use_projection:
            return not self.is_leaf_node(only_similar=True, only_visible=False)
        else:
            return False

    def projection_options_for_ui(self):
        """ Build tuples for showing projection options
        :return: (text, value, checked, disabled, tooltip) -tuples
        """
        r = []
        children = list(self.get_children())
        l = len(children)
        # chr(2193) = down arrow
        # chr(2198) = right down arrow
        # chr(2199) = left down arrow
        if l == 1:
            prefix = [chr(0x2193)]
        elif l == 2:
            prefix = [chr(0x2199), chr(0x2198)]
        elif l == 3:
            prefix = [chr(0x2199), chr(0x2193), chr(0x2198)]
        else:  # don't use arrows for
            prefix = [''] * l
        for n, child in enumerate(children):
            ch = child.head or child
            potent = child.head or (
            child.is_leaf_node(only_visible=False) and not child.is_placeholder())
            d = {'text': '%s%s' % (prefix[n], ch.short_str()), 'value': ch,
                 'is_checked': ch is self.head, 'enabled': bool(potent),
                 'tooltip': 'inherit head from ' + str(ch)}
            r.append(d)
        d = {'text': 'None', 'value': None, 'is_checked': not self.head, 'enabled': True,
             'tooltip': "doesn't inherit head"}
        r.append(d)
        return r

    def guess_projection(self):
        """ Analyze label, alias and children and try to guess if this is a
        projection from somewhere. Set head accordingly.
        :return:
        """

        def find_original(node, head):
            """ Go down in trees until the final matching label/alias is found.
            :param node: where to start searching
            :param head:
            :return:
            """
            for child in node.get_children():
                al = child.alias or child.label
                al = str(al)
                if strip_xbars(al) == head:
                    found_below = find_original(child, head)
                    if found_below:
                        return found_below
                    else:
                        return child
            return None

        al = self.alias or self.label
        self.head = find_original(self, strip_xbars(str(al))) or self
        ctrl.forest.update_projection_map(self, None, self.head)
        # ctrl.forest.update_projection_visual(self, self.head)
        return self.head

    def fix_projection_labels(self):
        """ If node has head, then start from this node, and
        move upwards labeling the nodes that also use the same head.

        If head is None, then remove label and alias.
        :return:
        """
        xbar = ctrl.fs.use_xbar_aliases

        def fix_label(node, level, head):
            last = True
            for parent in node.get_parents(only_similar=True, only_visible=False):
                if parent.head is head:
                    fix_label(parent, level + 1, head)
                    last = False
            node.label = head.label
            if xbar:
                if head_base:
                    if last:
                        node.alias = head_base + 'P'
                    elif level > 0:
                        node.alias = head_base + '´'
                    else:
                        node.alias = head_base
                else:
                    node.alias = ''
            node.update_label()

        h = self.head
        if h:
            head_base = None
            if h.alias:
                head_base = str(h.alias)
                head_base = strip_xbars(head_base)
            fix_label(h, 0, h)
        else:
            self.label = ''
            if xbar:
                self.alias = ''
            self.update_label()

    def set_projection(self, new_head, replace_up=False):
        """ Set this node to be projection from new_head. If the old_head is
        also used by parent node, propagate the change up to parent (and so
        on).
        :param new_head:
        :param replace_up: If True, iterate upwards and change nodes that used this head to use
        the new head instead. If False, the projection ends here.
        :return:
        """
        old_head = self.head
        if old_head:
            # nodes up from here cannot use old_head as head anymore,
            # as projection chain is broken.
            # set those parent heads to None, and they will recursively
            # fix their parents
            for parent in self.get_parents(only_similar=True, only_visible=False):
                if parent.head is old_head:
                    if replace_up:
                        parent.set_projection(new_head, True)
                    else:
                        parent.set_projection(None, False)
        self.head = new_head
        # following may look odd, but projecting head node's head should be the node itself.
        if new_head and new_head.head is not new_head:
            new_head.head = new_head
        ctrl.forest.update_projection_map(self, old_head, new_head)
        # ctrl.forest.update_projection_visual(self, new_head)
        if new_head:
            new_head.fix_projection_labels()
        else:
            self.fix_projection_labels()
        if old_head:
            old_head.fix_projection_labels()

    def set_projection_display(self, color_id):
        self._projection_color = color_id
        if color_id:
            self._projection_qcolor = ctrl.cm.get(color_id)
        else:
            self._projection_color = None

    @property
    def contextual_color(self):
        """ Drawing color that is sensitive to node's state
        :return: QColor
        """

        if ctrl.is_selected(self):
            base = ctrl.cm.selection()
        elif self._projection_color:
            base = self._projection_qcolor
        else:
            base = self.color
        if self.drag_data:
            return ctrl.cm.lighter(base)
        elif ctrl.pressed is self:
            return ctrl.cm.active(base)
        elif self._hovering:
            return ctrl.cm.hovering(base)
        else:
            return base

    # ### Features #########################################

    def update_gloss(self):
        """


        """
        if not self.syntactic_object:
            return
        syn_gloss = self.gloss
        gloss_node = self.gloss_node
        if gloss_node and not syn_gloss:
            ctrl.forest.delete_node(gloss_node)
        elif syn_gloss and not gloss_node:
            ctrl.forest.create_gloss_node(self)
        elif syn_gloss and gloss_node:
            gloss_node.update_label()

    # ### Labels #############################################
    # things to do with traces:
    # if renamed and index is removed/changed, update chains
    # if moved, update chains
    # if copied, make sure that copy isn't in chain
    # if deleted, update chains
    # any other operations?

    def is_empty_node(self):
        """ Empty nodes can be used as placeholders and deleted or replaced without structural
        worries """
        return (not (self.alias or self.label or self.index)) and self.is_leaf_node()

    # ## Indexes and chains ###################################

    def is_chain_head(self):
        """


        :return:
        """
        if self.index:
            return not (self.is_leaf_node() and self.label == 't')
        return False

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    index = Saved("index", if_changed=BaseConstituentNode.alert_inode)
    alias = Saved("alias", if_changed=BaseConstituentNode.alert_inode)
    gloss = Saved("gloss", if_changed=if_changed_gloss)
    head = Saved("head")

    is_trace = Saved("is_trace")
    merge_order = Saved("merge_order")
    select_order = Saved("select_order")
    original_parent = Saved("original_parent")
