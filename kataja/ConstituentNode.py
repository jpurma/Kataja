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
from kataja.Node import Node
from kataja.BaseConstituentNode import BaseConstituentNode
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
    visible = {'alias': {'order': 0},
               'index': {'order': 1, 'align': 'line-end', 'style': 'subscript'},
               'label': {'order': 2},
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
                              tooltip='translation (optional)', width=200)}
    default_style = {'color': 'content1', 'font': g.MAIN_FONT, 'font-size': 10,
                     'edge': g.CONSTITUENT_EDGE}

    default_edge = {'id': g.CONSTITUENT_EDGE, 'shape_name': 'shaped_cubic', 'color': 'content1',
                    'pull': .24, 'visible': True, 'arrowhead_at_start': False,
                    'arrowhead_at_end': False, 'labeled': False}

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
        self.update_status_tip()

    def after_init(self):
        """ After_init is called in 2nd step in process of creating objects:
        1st wave creates the objects and calls __init__, and then iterates through and sets the
        values. 2nd wave calls after_inits for all created objects. Now they can properly refer
        to each other and know their values.
        :return: None
        """
        self.update_features()
        self.update_gloss()
        self.update_label()
        self.update_visibility()
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
    def as_inode(self):
        """
        :return: INodes or str or tuple of them
        """
        if self._inode_changed:
            if not self._inode.values:
                return ''
            if self.triangle:
                leaves = ITextNode()
                # todo: Use a better linearization here
                for node in ctrl.forest.list_nodes_once(self):
                    if node.is_leaf_node(only_visible=False):
                        leaves += node.label
                        leaves += ' '
                label = leaves.tidy()
            else:
                label = self.label

            iv = self._inode.values
            iv['label']['value'] = label
            iv['alias']['value'] = self.alias
            iv['index']['value'] = self.index
            iv['gloss']['value'] = self.gloss
            #iv['features']['value'] = self.features
            self._inode_changed = False
        return self._inode

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

    def __str__(self):
        if not self.syntactic_object:
            return 'Placeholder node'
        alias = str(self.alias)
        label = str(self.label)
        if alias and label:
            return ' '.join((alias, label))  # + ' adj: %s fixed: %s' % (self.adjustment, self.fixed_position)
        else:
            return alias or label  # + ' adj: %s fixed: %s' % (self.adjustment, self.fixed_position)

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

    is_trace = Saved("is_trace")
    merge_order = Saved("merge_order")
    select_order = Saved("select_order")
    original_parent = Saved("original_parent")
