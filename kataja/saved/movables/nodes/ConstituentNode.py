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
import kataja.globals as g
from kataja.Saved import SavedField, SavedSynField
from kataja.saved.movables.Node import Node
from kataja.parser.INodes import ITextNode
from kataja.singletons import ctrl
from kataja.saved.movables.nodes.BaseConstituentNode import BaseConstituentNode

__author__ = 'purma'

xbar_suffixes = ['´', "'", "P", "(1/)", "\1"]


def strip_xbars(al):
    for s in xbar_suffixes:
        if len(al) > len(s) and al.endswith(s):
            return al[:-len(s)]
    else:
        return al


class ConstituentNode(BaseConstituentNode):
    """ ConstituentNode is enriched with few elements that have no syntactic meaning but help with
     reading the trees aliases, indices and glosses.
    """
    name = ('Constituent', 'Constituents')
    short_name = "CN"
    display = True
    wraps = 'constituent'
    visible_in_label = ['alias', 'index', 'triangle', 'label', 'gloss']
    editable_in_label = ['alias', 'index', 'label', 'gloss', 'head']

    display_styles = {'index': {'align': 'line-end', 'start_tag': '<sub>', 'end_tag': '</sub>'},
                      'triangle': {'special': 'triangle', 'readonly': True},
                      'label': {'getter': 'triangled_label', 'condition': 'should_show_label'},
                      'alias': {'condition': 'should_show_alias'}}
    editable = {'alias': dict(name='Alias', prefill='alias',
                              tooltip='Non-functional readable label of the constituent'),
                'index': dict(name='Index', align='line-end', width=20, prefill='i',
                              tooltip='Index to recognize multiple occurences'),
                'label': dict(name='Label', prefill='label',
                              tooltip='Label of the constituent (functional identifier)', width=200,
                              focus=True, syntactic=True),
                'gloss': dict(name='Gloss', prefill='gloss',
                              tooltip='translation (optional)', width=200, check_before='is_leaf'),
                'head': dict(name='Projection from',
                             tooltip='Inherit label from another node and rewrite alias to '
                                     'reflect this',
                             check_before='can_be_projection_of_another_node',
                             option_function='build_projection_options_for_ui',
                             input_type='radiobutton',
                             select_action='constituent_set_head')}
    default_style = {'color': 'content1', 'font': g.MAIN_FONT, 'font-size': 10}

    default_edge = {'id': g.CONSTITUENT_EDGE, 'shape_name': 'shaped_cubic', 'color': 'content1',
                    'pull': .24, 'visible': True, 'arrowhead_at_start': False,
                    'arrowhead_at_end': False, 'labeled': False, 'name_pl': 'Constituent edges'}

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
        g.LEFT_ADD_TOP: {'condition': ['is_top_node', 'dragging_constituent', 'free_drawing_mode']},
        g.RIGHT_ADD_TOP: {'condition': ['is_top_node', 'dragging_constituent', 'free_drawing_mode']},
        g.LEFT_ADD_SIBLING: {'place': 'edge_up', 'condition': ['dragging_constituent', 'free_drawing_mode']},
        g.RIGHT_ADD_SIBLING: {'place': 'edge_up', 'condition': ['dragging_constituent',
                                                                'free_drawing_mode']},
        g.TOUCH_CONNECT_COMMENT: {'condition': 'dragging_comment'},
        g.TOUCH_CONNECT_FEATURE: {'condition': ['dragging_feature', 'free_drawing_mode']},
        g.TOUCH_CONNECT_GLOSS: {'condition': 'dragging_gloss'}}

    touch_areas_when_selected = {
        g.LEFT_ADD_TOP: {'condition': ['is_top_node', 'free_drawing_mode'],
                         'action': 'add_top_left'},
        g.RIGHT_ADD_TOP: {'condition': ['is_top_node', 'free_drawing_mode'],
                          'action': 'add_top_right'},
        g.INNER_ADD_SIBLING_LEFT: {'condition': ['inner_add_sibling', 'free_drawing_mode'],
                                   'place': 'edge_up',
                                   'action': 'inner_add_sibling_left'},
        g.INNER_ADD_SIBLING_RIGHT: {'condition': ['inner_add_sibling', 'free_drawing_mode'],
                                    'place': 'edge_up',
                                    'action': 'inner_add_sibling_right'},
        g.UNARY_ADD_CHILD_LEFT: {'condition': ['has_one_child', 'free_drawing_mode'],
                                 'action': 'unary_add_child_left'},
        g.UNARY_ADD_CHILD_RIGHT: {'condition': ['has_one_child', 'free_drawing_mode'],
                                  'action': 'unary_add_child_right'},
        g.LEAF_ADD_SIBLING_LEFT: {'condition': ['is_leaf', 'free_drawing_mode'],
                                  'action': 'leaf_add_sibling_left'},
        g.LEAF_ADD_SIBLING_RIGHT: {'condition': ['is_leaf', 'free_drawing_mode'],
                                   'action': 'leaf_add_sibling_right'},
        g.ADD_TRIANGLE: {'condition': 'can_have_triangle',
                         'action': 'add_triangle'},
        g.REMOVE_TRIANGLE: {'condition': 'has_triangle',
                            'action': 'remove_triangle'}
    }

    buttons_when_selected = {
        g.REMOVE_MERGER: {'condition': ['is_unnecessary_merger', 'free_drawing_mode'], 'action': 'remove_merger'},
        g.NODE_EDITOR_BUTTON: {'action': 'toggle_node_edit_embed'},
        g.REMOVE_NODE: {'condition': ['not:is_unnecessary_merger', 'free_drawing_mode'], 'action': 'remove_node'}
    }

    def __init__(self, constituent=None):
        """ Most of the initiation is inherited from Node """
        BaseConstituentNode.__init__(self, constituent=constituent)
        self.index = ''
        self.alias = ''
        self.gloss = ''

        self.is_trace = False
        self.merge_order = 0
        self.select_order = 0
        self.original_parent = None
        self._projection_color = None

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
        :param updated_fields: list of names of elements that have been updated.
        :return: None
        """
        # update_label will be called by Node.after_model_update
        super().after_model_update(updated_fields, update_type)

    def load_values_from_parsernode(self, parsernode):
        """ Update constituentnode with values from parsernode
        :param parsernode:
        :return:
        """
        if parsernode.indices and parsernode.indices[0]:
            self.index = parsernode.indices[0]

        is_leaf = self.is_leaf()
        rows = parsernode.rows
        rowcount = len(rows)
        features = []
        if rowcount > 3:
            self.alias, self.label, self.gloss, *features = rows
        if rowcount == 3:
            self.alias, self.label, self.gloss = rows
        elif rowcount == 2:
            self.alias, self.label = rows
        elif rowcount == 1 and is_leaf:
            self.label = rows[0]
        elif rowcount == 1:
            self.alias = rows[0]

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
                if node.is_leaf(only_visible=False) and node.label:
                    leaves += node.label
                    leaves += ' '
            return leaves.tidy()
        else:
            return self.label

    def should_show_label(self):
        if self.is_leaf(only_visible=True) or self.triangle:
            return ctrl.forest.settings.show_leaf_labels
        else:
            return ctrl.forest.settings.show_internal_labels

    def should_show_alias(self):
        if self.is_leaf(only_visible=True) or self.triangle:
            return ctrl.forest.settings.show_leaf_aliases
        else:
            return ctrl.forest.settings.show_internal_aliases

    def update_status_tip(self):
        """ Hovering status tip """
        if self.syntactic_object:
            if self.alias:
                alias = '"%s" ' % self.alias
            else:
                alias = ''
            if self.label:
                label = '"%s" ' % self.label
            else:
                label = ''
            if self.is_trace:
                name = "Trace"
            if self.is_leaf():
                name = "Leaf constituent"
            elif self.is_top_node():
                name = "Root constituent"
            else:
                name = "Inner constituent"
            if self.use_adjustment:
                self.status_tip = "%s (Alias: %s Label: %s pos: (%.1f, %.1f) w. adjustment (%.1f, " \
                                  "%.1f))" % (
                                  name, alias, label, self.current_scene_position[0],
                                  self.current_scene_position[1],
                                  self.adjustment[0], self.adjustment[1])
            else:
                self.status_tip = "%s (Alias: %s Label: %s pos: (%.1f, %.1f))" % (
                                  name, alias, label, self.current_scene_position[0],
                                  self.current_scene_position[1])

        else:
            self.status_tip = "Empty, but mandatory constituent position"

    def short_str(self):
        if not self.syntactic_object:
            return 'empty'
        alias = str(self.alias)
        label = str(self.label)
        if alias and label:
            return alias + ' ' + label
        else:
            return alias or label or "no label"

    def __str__(self):
        if not self.syntactic_object:
            return 'const with missing synobj'
        alias = str(self.alias)
        label = str(self.label)
        if alias and label:
            l = alias + ' ' + label
        elif alias:
            l = alias
        elif label:
            l = label
        else:
            return "anonymous constituent"
        return "constituent '%s'" % l

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
                return str(self.alias)
        else:
            return super().as_bracket_string()

    def is_unnecessary_merger(self):
        """ This merge can be removed, if it has only one child
        :return:
        """
        return len(list(self.get_children())) == 1

    def fix_edge_aligns(self):
        aligns = []
        edges = []
        for edge in self.edges_down:
            if edge.edge_type == g.CONSTITUENT_EDGE:
                aligns.append(edge.alignment)
                edges.append(edge)
        if len(aligns) == 1:
            edges[0].alignment = g.NO_ALIGN
        else:
            # do syntactically justified align
            children = self.get_ordered_children()
            edges = [self.get_edge_to(child) for child in children]
            for item in edges:
                if item is None:
                    raise ValueError
            if not edges:
                return
            elif len(edges) == 1:
                edges[0].alignment = g.LEFT
                edges[1].alignment = g.RIGHT
            elif len(edges) == 2:
                edges[0].alignment = g.LEFT
                edges[1].alignment = g.RIGHT
            else:
                edges[0].alignment = g.LEFT
                edges[-1].alignment = g.RIGHT
                for edge in edges[1:-1]:
                    edge.alignment = g.NO_ALIGN



    # Conditions ##########################
    # These are called from templates with getattr, and may appear unused for IDE's analysis.
    # Check their real usage with string search before removing these.

    def inner_add_sibling(self):
        """ Node has child and it is not unary child. There are no other reasons preventing
        adding siblings
        :return: bool
        """
        return list(self.get_children()) and not self.is_unary()

    def has_one_child(self):
        return len(list(self.get_children())) == 1

    def can_be_projection_of_another_node(self):
        """ Node can be projection from other nodes if it has other nodes
        below it.
        It may be necessary to move this check to syntactic level at some
        point.
        :return:
        """
        if ctrl.fs.use_projection:
            if self.is_leaf(only_similar=True, only_visible=False):
                return False
            else:
                return True
        else:
            return False

    def build_projection_options_for_ui(self):
        """ Build tuples for showing projection options
        :return: (text, value, checked, disabled, tooltip) -tuples
        """
        r = []
        children = list(self.get_children())
        l = len(children)
        if l == 1:
            # down arrow
            prefix = [chr(0x2193)]
        elif l == 2:
            # left down arrow, right down arrow
            prefix = [chr(0x2199), chr(0x2198)]
        elif l == 3:
            # left down arrow, down arrow, right down arrow
            prefix = [chr(0x2199), chr(0x2193), chr(0x2198)]
        else:
            # don't use arrows if more than 3
            prefix = [''] * l
        for n, child in enumerate(children):
            head_node_of_child = child.head_node or child
            enabled = True #bool(child.head_node or child.is_leaf(only_visible=False))
            d = {'text': '%s%s' % (prefix[n], head_node_of_child.short_str()),
                 'value': head_node_of_child,
                 'is_checked': head_node_of_child == self.head_node,
                 'enabled': enabled,
                 'tooltip': 'inherit label from ' + str(head_node_of_child)}
            r.append(d)
        print('self.head_node:', self.head_node, self.head_node == self)
        d = {'text': 'Undefined',
             'value': None,
             'is_checked': not self.head_node,
             'enabled': True,
             'tooltip': "doesn't inherit head"}
        r.append(d)
        print(r)
        return r

    def guess_projection(self):
        """ Analyze label, alias and children and try to guess if this is a
        projection from somewhere. Set head accordingly.
        :return:
        """

        def find_original(node, head_node):
            """ Go down in trees until the final matching label/alias is found.
            :param node: where to start searching
            :param head:
            :return:
            """
            for child in node.get_children():
                al = child.alias or child.label
                al = str(al)
                if strip_xbars(al) == head_node:
                    found_below = find_original(child, head_node)
                    if found_below:
                        return found_below
                    else:
                        return child
            return None

        al = self.alias or self.label
        head_node = find_original(self, strip_xbars(str(al)))
        self.set_projection(head_node)

    def set_projection(self, new_head):
        """ Set this node to be projection from new_head.
        :param new_head:
        :return:
        """
        if new_head == self or new_head == self.syntactic_object:
            raise hell
        if isinstance(new_head, Node):
            self.head = new_head.syntactic_object
        else:
            self.head = new_head

    def set_projection_display(self, color_id):
        self._projection_color = color_id

    @property
    def head_node(self):
        """ Heads are syntactic objects, not nodes. This is helper to get the node instead.
        :return:
        """
        if self.head is self.syntactic_object:
            return self
        elif self.head:
            return ctrl.forest.get_node(self.head)
        else:
            return None

    @property
    def contextual_color(self):
        """ Drawing color that is sensitive to node's state
        :return: QColor
        """

        if ctrl.is_selected(self):
            base = ctrl.cm.selection()
        elif self._projection_color:
            base = ctrl.cm.get(self._projection_color)
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

    def update_gloss(self, value=None):
        """


        """
        if not self.syntactic_object:
            return
        syn_gloss = self.gloss
        gloss_node = self.gloss_node
        if not ctrl.undo_disabled:
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
        return (not (self.alias or self.label or self.index)) and self.is_leaf()

    # ## Indexes and chains ###################################

    def is_chain_head(self):
        """


        :return:
        """
        if self.index:
            return not (self.is_leaf() and self.label == 't')
        return False

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    index = SavedField("index")
    alias = SavedField("alias")
    gloss = SavedField("gloss", if_changed=update_gloss)
    head = SavedSynField("head")

    is_trace = SavedField("is_trace")
    merge_order = SavedField("merge_order")
    select_order = SavedField("select_order")
    original_parent = SavedField("original_parent")
