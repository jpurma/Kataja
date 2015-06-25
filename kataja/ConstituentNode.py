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

from kataja.BaseConstituentNode import BaseConstituentNode
from kataja.BaseModel import Saved
from kataja.singletons import ctrl
from kataja.parser.INodes import ITextNode, IConstituentNode
import kataja.globals as g

__author__ = 'purma'


class ConstituentNode(BaseConstituentNode):
    """ ConstituentNode is enriched with few fields that have no syntactic meaning but help with reading the tree,
    like aliases, indices and glosses.
    """

    receives_signals = []
    short_name = "CN"

    # ConstituentNode position points to the _center_ of the node.
    # boundingRect should be (w/-2, h/-2, w, h)

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
        1st wave creates the objects and calls __init__, and then iterates through and sets the values.
        2nd wave calls after_inits for all created objects. Now they can properly refer to each other and know their
        values.
        :return: None
        """
        self.update_features()
        self.update_gloss()
        self.update_label()
        self.update_visibility()
        self.announce_creation()
        ctrl.forest.store(self)

    def after_model_update(self, updated_fields, update_type):
        """ This is called after the item's model has been updated, to run the side-effects of various
        setters in an order that makes sense.
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
        if gl:
            return gl[0]

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

            self._inode = IConstituentNode(alias=self.alias,
                                           label=label,
                                           index=self.index,
                                           gloss=self.gloss,
                                           features=self.features)
            self._inode_changed = False
        print(self._inode)
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
            self.status_tip = "%s %s%s" % (name, alias, self.label)
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
            self._label_complex.setVisible(self._label_visible)

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
