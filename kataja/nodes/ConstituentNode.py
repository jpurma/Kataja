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
from kataja.singletons import ctrl
from kataja.parser.INodes import ITextNode
import kataja.globals as g

__author__ = 'purma'


class ConstituentNode(BaseConstituentNode):
    """ ConstituentNode is enriched with few fields that have no syntactic meaning but help with
     reading the tree aliases, indices and glosses.
    """
    name = ('Constituent', 'Constituents')
    short_name = "CN"
    display = True
    wraps = 'constituent'

    visible = {'alias': {'order': 0},
               'index': {'order': 1, 'align': 'line-end', 'style': 'subscript'},
               'label': {'order': 2, 'getter': 'triangled_label'},
               'gloss': {'order': 3},
               }
    editable = {'alias': dict(name='Alias', order=3, prefill='alias',
                              tooltip='Non-functional readable label of the constituent'),
                'index': dict(name='Index', order=6, align='line-end', width=20, prefill='i',
                              tooltip='Index to recognize multiple occurences'),
                'label': dict(name='Label', order=9, prefill='label',
                              tooltip='Label of the constituent (functional identifier)',
                              width=200, focus=True, syntactic=True),
                'gloss': dict(name='Gloss', order=12, prefill='gloss',
                              tooltip='translation (optional)', width=200,
                              check_before='is_leaf'),
                'head': dict(name='Head', order=20, tooltip='inherits from',
                             check_before='can_be_projection',
                             option_function='projection_options_for_ui',
                             input_type='multibutton',
                             select_action='constituent_set_head')}
    default_style = {'color': 'content1', 'font': g.MAIN_FONT, 'font-size': 10,
                     'edge': g.CONSTITUENT_EDGE}

    default_edge = {'id': g.CONSTITUENT_EDGE, 'shape_name': 'shaped_cubic', 'color': 'content1',
                    'pull': .24, 'visible': True, 'arrowhead_at_start': False,
                    'arrowhead_at_end': False, 'labeled': False}

    # Touch areas are UI elements that scale with the tree: they can be
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

    touch_areas_when_dragging = {g.LEFT_ADD_ROOT: {'condition': ['is_root',
                                                   'dragging_constituent']},
                   g.RIGHT_ADD_ROOT: {'condition': ['is_root',
                                                    'dragging_constituent']},
                   g.LEFT_ADD_SIBLING: {'place': 'edge_up', 'condition':
                                        'dragging_constituent'},
                   g.RIGHT_ADD_SIBLING: {'place': 'edge_up', 'condition':
                                         'dragging_constituent'},
                   g.TOUCH_CONNECT_COMMENT: {'condition': 'dragging_comment'},
                   g.TOUCH_CONNECT_FEATURE: {'condition': 'dragging_feature'},
                   g.TOUCH_CONNECT_GLOSS: {'condition': 'dragging_gloss'}}

    touch_areas_when_selected = {g.LEFT_ADD_ROOT: {'condition': 'is_root'},
                   g.RIGHT_ADD_ROOT: {'condition': 'is_root'},
                   g.LEFT_ADD_SIBLING: {'place': 'edge_up'},
                   g.RIGHT_ADD_SIBLING: {'place': 'edge_up'}}



    def __init__(self, constituent=None):
        """ Most of the initiation is inherited from Node """
        BaseConstituentNode.__init__(self, constituent=constituent)
        self._index_label = None
        self._index_visible = True
        self.is_trace = False
        self.merge_order = 0
        self.select_order = 0
        self.original_parent = None

        # ### Cycle index stores the order when node was originally merged to structure.
        # going up in tree, cycle index should go up too

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
        a = self.as_inode
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

    def if_changed_gloss(self, value):
        """ Synobj changed, but remind to update inodes here
        :param value:
        :return:
        """
        self._inode_changed = True
        self.update_gloss()

    def if_changed_head(self, value):
        """ If head is changed, the old head cannot be projected upwards from
        here, so check the parents.
        :param value:
        :return:
        """
        pass

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
            elif self.is_root_node():
                name = "Root constituent"
            else:
                name = "Inner constituent"
            self.status_tip = "%s Alias: %s Label: %s is_leaf: %s" % (name, alias, self.label,
                                                                      self.is_leaf_node())
        else:
            self.status_tip = "Empty, but mandatory constituent position"

    def short_str(self):
        if not self.syntactic_object:
            return 'empty'
        alias = self.alias
        label = self.label
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
        return "constituent '%s'" % l

    def as_bracket_string(self):
        """ returns a simple bracket string representation """
        if self.alias:
            if not self.syntactic_object:
                return '0'
            children = self.get_children()
            if children:
                return '[.%s %s ]' % (self.alias, ' '.join([c.as_bracket_string() for c in children]))
            else:
                return self.alias
        else:
            return super().as_bracket_string()



    def update_visibility(self, **kw):
        """ Compute visibility-related attributes for this constituent node and update those that depend on this
        -- meaning features etc.

        :param kw:
        """
        super().update_visibility(**kw)
        if ctrl.forest.settings.label_style == g.ALIASES and self.alias:
            self._label_visible = True
            self._label_complex.setVisible(True)

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
        :return: (text, value, checked) -tuples
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
        else: # don't use arrows for
            prefix = [''] * l
        for n, child in enumerate(children):
            disabled = child.is_placeholder()
            # assume that head is inherited.
            ch = child.head or child
            is_head = ch is self.head
            tt = 'inherit head from ' + str(ch)
            r.append(('%s%s' % (prefix[n], ch.short_str()), ch, is_head,
                      disabled, tt))
        tt = "doesn't inherit head"
        r.append(('None', None, self.head is None, False, tt))
        return r

    def guess_projection(self):
        """ Analyze label, alias and children and try to guess if this is a
        projection from somewhere. Set head accordingly.
        :return:
        """

        suffixes = ['´', "'", "P", "(1/)", "\1"]

        def strip_xbars(al):
            for s in suffixes:
                if len(al) > len(s) and al.endswith(s):
                    return al[:-len(s)]
            else:
                return al

        def find_original(node, head):
            """ Go down in tree until the final matching label/alias is found.
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
        al = str(al)
        self.head = find_original(self, strip_xbars(al)) or self
        return self.head

    def set_projection(self, new_head):
        """ Set this node to be projection from new_head. If the old_head is
        also used by parent node, propagate the change up to parent (and so
        on).
        :param new_head:
        :return:
        """
        suffixes = ['´', "'", "P", "(1/)", "\1"]

        def strip_xbars(al):
            for s in suffixes:
                if len(al) > len(s) and al.endswith(s):
                    return al[:-len(s)]
            else:
                return al

        old_head = self.head
        self.head = new_head
        intermediate_node = False
        if old_head:
            for parent in self.get_parents(only_similar=True,
                                           only_visible=False):
                if parent.head == old_head:
                    parent.set_projection(new_head)
                    intermediate_node = True
            for child in self.get_children():
                if child is old_head or child.head is old_head:
                    al = str(old_head.alias) or ''
                    al = strip_xbars(al)
                    if al:
                        old_head.alias = al + 'P'
                        old_head.update_label()
                    break
        if new_head:
            self.label = new_head.label
            if ctrl.fs.use_xbar_aliases:
                al = str(new_head.alias) or '' # doesn't break if len(None)
                # if previous head was XP or X´, turn it to X
                if strip_xbars(al) != al:
                    new_head.alias = strip_xbars(al)
                    new_head.update_label()
                al = new_head.alias or new_head.label
                print(al)
                if intermediate_node:
                    c = "'"
                else:
                    c = 'P'
                if al:
                    self.alias = al + c
                else:
                    self.alias = ''
            else:
                self.alias = new_head.alias
        elif old_head:
            self.label = ''
            self.alias = ''
        self.update_label()
        print(new_head, self.label, self.alias)


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
        """ Empty nodes can be used as placeholders and deleted or replaced without structural worries """
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
    head = Saved("head", if_changed=if_changed_head)

    is_trace = Saved("is_trace")
    merge_order = Saved("merge_order")
    select_order = Saved("select_order")
    original_parent = Saved("original_parent")
