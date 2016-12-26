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
from kataja.SavedField import SavedField, SavedSynField
from kataja.parser.INodes import ITextNode, ICommandNode
from kataja.saved.movables.Node import Node
from kataja.singletons import ctrl, classes
from kataja.uniqueness_generator import next_available_type_id
from kataja.parser.INodes import as_html
from kataja.utils import time_me

__author__ = 'purma'

xbar_suffixes = ['´', "'", "P", "(1/)", "\1"]


def strip_xbars(al):
    for s in xbar_suffixes:
        if len(al) > len(s) and al.endswith(s):
            return al[:-len(s)]
    else:
        return al


class ConstituentNode(Node):
    """ ConstituentNode is enriched with few elements that have no syntactic meaning but help with
     reading the trees aliases, indices and glosses.
    """
    __qt_type_id__ = next_available_type_id()
    display_name = ('Constituent', 'Constituents')
    display = True
    width = 20
    height = 20
    is_constituent = True
    node_type = g.CONSTITUENT_NODE
    wraps = 'constituent'

    editable = {'display_label': dict(name='Displayed label', prefill='display_label',
                                      tooltip='Rich text representing the constituent',
                                      input_type='expandingtext', order=15,
                                      on_edit='update_preview'),
                'label': dict(name='Computational label', prefill='label',
                              tooltip='Label used for computations, plain string', width=160,
                              focus=True, syntactic=True, order=10, on_edit='update_preview'),
                'index': dict(name='Index', align='line-end', width=20, prefill='i',
                              tooltip='Optional index for linking multiple instances', order=11,
                              on_edit='update_preview'),
                'preview': dict(name='Preview', tooltip='Preview how label will be displayed. '
                                                        'Display label overrides computational '
                                                        'label.', input_type='preview'),
                'gloss': dict(name='Gloss', prefill='gloss',
                              tooltip='translation (optional)', width=200, condition='is_leaf',
                              order=40),
                'head': dict(name='Projection from',
                             tooltip='Inherit label from another node and rewrite display_label to '
                                     'reflect this',
                             condition='can_be_projection_of_another_node',
                             option_function='build_projection_options_for_ui',
                             input_type='radiobutton',
                             select_action='constituent_set_head', order=30)}
    default_style = {'plain': {'color_id': 'content1', 'font_id': g.MAIN_FONT, 'font-size': 10},
                     'fancy': {'color_id': 'content1', 'font_id': g.MAIN_FONT, 'font-size': 10}}

    default_edge = g.CONSTITUENT_EDGE

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
        g.MERGE_TO_TOP: {'condition': ['not:is_top_node', 'free_drawing_mode'],
                          'action': 'merge_to_top'},
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
        g.REMOVE_MERGER: {'condition': ['is_unnecessary_merger', 'free_drawing_mode'],
                          'action': 'remove_merger'},
        g.NODE_EDITOR_BUTTON: {'action': 'toggle_node_edit_embed'},
        g.REMOVE_NODE: {'condition': ['not:is_unnecessary_merger', 'free_drawing_mode'],
                        'action': 'remove_node'},
        #g.QUICK_EDIT_LABEL: {}, # 'condition': 'is_quick_editing'
    }

    def __init__(self, syntactic_object=None, forest=None):
        """ Most of the initiation is inherited from Node """
        Node.__init__(self, syntactic_object=syntactic_object, forest=forest)

        # ### Projection -- see also preferences that govern if these are used
        self.can_project = True
        self.projecting_to = set()

        self.index = ''
        self.display_label = ''
        self.gloss = ''

        self.is_trace = False
        self.merge_order = 0
        self.select_order = 0
        self.original_parent = None
        self.in_projections = []
        self.halo = False

        # ### Cycle index stores the order when node was originally merged to structure.
        # going up in trees, cycle index should go up too

    def after_init(self):
        """ After_init is called in 2nd step in process of creating objects:
        1st wave creates the objects and calls __init__, and then iterates through and sets the
        values. 2nd wave calls after_inits for all created objects. Now they can properly refer
        to each other and know their values.
        :return: None
        """
        self.update_features()
        self.update_gloss()
        self.update_label_shape()
        self.update_label()
        self.update_visibility()
        self.update_status_tip()
        self.announce_creation()
        self.forest.store(self)

    @staticmethod
    def create_synobj(label, forest):
        """ ConstituentNodes are wrappers for Constituents. Exact
        implementation/class of constituent is defined in ctrl.
        :return:
        """
        if not label:
            label = forest.get_first_free_constituent_name()
        c = ctrl.syntax.Constituent(label)
        c.after_init()
        return c

    def after_model_update(self, updated_fields, update_type):
        """ This is called after the item's model has been updated, to run the side-effects of
         various setters in an order that makes sense.
        :param updated_fields: list of names of elements that have been updated.
        :return: None
        """
        # update_label will be called by Node.after_model_update
        super().after_model_update(updated_fields, update_type)
        if 'features' in updated_fields:
            self.update_features()

    def load_values_from_parsernode(self, parsernode):
        """ Update constituentnode with values from parsernode
        :param parsernode:
        :return:
        """
        if parsernode.index:
            self.index = parsernode.index
        rows = parsernode.label_rows
        leaf = not parsernode.parts
        # Remove dotlabel
        if len(rows):
            first = rows[0]
            sfirst = str(first)
            if len(sfirst) > 1 and sfirst.startswith('.'):
                if isinstance(first, ICommandNode):
                    if first.parts:
                        rows[0] = first.parts[0]
                    else:
                        rows[0] = ''
                if isinstance(first, ITextNode):
                    first.remove_prefix('.')
                else:
                    rows[0] = first[1:]
        # With inner nodes everything goes to display_label, with leaf nodes the second line is the
        # best bet for actual label. (first is category, second the word, third and more features)
        if leaf:
            if len(rows) == 1:
                self.label = rows[0]
            elif len(rows) > 1:
                self.label = rows[1:1]
        self.display_label = rows

    def if_changed_features(self, value):
        """ Synobj changed, but remind to update label here
        :param value:
        :return:
        """
        self.update_features()

    # Editing with NodeEditEmbed and given editable-template
    def update_preview(self):
        """ Update preview label in NodeEditEmbed with composite from display_label, label and index
        :param edited: the field that triggered the update.
        :return:
        """
        embed = self.sender().parent()
        surefail = 0
        while not hasattr(embed, 'fields') and surefail < 5:
            embed = embed.parent()
            surefail += 1
        index = embed.fields.get('index', None)
        display_label = embed.fields.get('display_label', None)
        label = embed.fields.get('label', None)
        preview = embed.fields.get('preview', None)
        index_text = as_html(index.text())
        display_label_text = as_html(display_label.inode_text())
        label_text = as_html(label.text())
        if display_label_text:
            parsed = display_label_text
        else:
            parsed = label_text
            if index_text:
                parsed += '<sub>' + index_text + '</sub>'
        preview.setText(parsed)

    def update_label_visibility(self):
        """ Check if the label of the node has any content -- should it be
        displayed. Node itself can be visible even when its label is not.
        :return:
        """
        if not self.label_object:
            self.update_label()
        if not ctrl.settings.get('inner_labels'):
            if self.is_leaf(only_similar=True, only_visible=True):
                self._label_visible = self.label_object.has_content() or \
                                      self.label_object.is_quick_editing()
            else:
                self._label_visible = self.label_object.is_quick_editing()
        else:
            self._label_visible = self.label_object.has_content() or \
                                  self.label_object.is_quick_editing()
        self.label_object.setVisible(self._label_visible)


    # Other properties


    @property
    def gloss_node(self):
        """
        :return:
        """
        gs = self.get_children(visible=True, of_type=g.GLOSS_EDGE)
        if gs:
            return gs[0]

    def get_triangle_text(self, included=None):
        """ Label with triangled elements concatenated into it
        :return:
        """
        if not included:
            included = set()
        children = self.get_children(visible=False, similar=True)
        if children:
            parts = []
            for node in children:
                if node not in included:
                    included.add(node)
                    nodestr = node.get_triangle_text(included)
                    if nodestr:
                        parts.append(nodestr)
            return ' '.join(parts)
        else:
            syntactic_mode = ctrl.settings.get('syntactic_mode')
            if (not syntactic_mode) and self.display_label:
                if isinstance(self.display_label, ITextNode):
                    return self.display_label.as_html().split('<br/>')[0]
                elif isinstance(self.display_label, str):
                    return self.display_label.splitlines()[0]
                elif isinstance(self.display_label, list):
                    return str(self.display_label[0])
            else:
                return self.label_html

    @property
    def label_html(self):
        """ Label as string
        :return:
        """
        if self.syntactic_object and hasattr(self.syntactic_object, 'features'):
            for item in self.syntactic_object.features:
                name = getattr(item, 'name', '')
                if name and isinstance(name, str) and name.lower() == 'root':
                    return '<u>' + as_html(self.label) + '</u>'
        return as_html(self.label)

    def update_label_shape(self):
        self.label_object.label_shape = ctrl.settings.get('label_shape')

    def update_locked_features(self):
        """

        :return:
        """
        pass

    def should_show_gloss_in_label(self) -> bool:
        return ctrl.settings.get('show_glosses') == 1


    def update_status_tip(self) -> None:
        """ Hovering status tip """
        if self.syntactic_object:
            if self.display_label:
                alias = 'Alias: "%s" ' % self.display_label
            else:
                alias = ''
            if self.label:
                label = ' Label: "%s" ' % self.label
            else:
                label = ''
            if self.is_trace:
                name = "Trace"
            if self.is_leaf():
                name = "Leaf constituent"
            # elif self.is_top_node():
            #    name = "Set %s" % self.set_string() # "Root constituent"
            else:
                name = "Set %s" % self.set_string()
            if self.use_adjustment:
                adjustment = ' w. adjustment (%.1f, "%.1f)' % (self.adjustment[0],
                                                              self.adjustment[1])
            else:
                adjustment = ''
            self.status_tip = "%s (%s%s pos: (%.1f, %.1f)%s z-index: %s/%s)" % (
                              name, alias, label, self.current_scene_position[0],
                              self.current_scene_position[1], adjustment, self.zValue(), self.z_value)

        else:
            self.status_tip = "Empty, but mandatory constituent position"

    def short_str(self):
        if not self.syntactic_object:
            return 'empty'
        alias = as_html(self.display_label)
        label = as_html(self.label)
        if alias and label:
            return alias + ' ' + label
        else:
            return alias or label or "no label"

    def set_string(self):
        if self.syntactic_object and hasattr(self.syntactic_object, 'set_string'):
            return self.syntactic_object.set_string()
        else:
            return self._set_string()

    def _set_string(self):
        parts = []
        for child in self.get_children(similar=True, visible=False):
            parts.append(str(child._set_string()))
        if parts:
            return '{%s}' % ', '.join(parts)
        else:
            return self.label

    def __str__(self):
        if not self.syntactic_object:
            return 'const with missing synobj'
        alias = str(self.display_label)
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

    def compose_html_for_viewing(self, peek_into_synobj=True):
        """ This method builds the html to display in label. For convenience, syntactic objects
        can override this (going against the containment logic) by having their own
        'compose_html_for_viewing' -method. This is so that it is easier to create custom
        implementations for constituents without requiring custom constituentnodes.

        Note that synobj's compose_html_for_viewing receives the node object as parameter,
        so you can replicate the behavior below and add your own to it.

        :param peek_into_synobj: allow syntactic object to override this method. If synobj in turn
        needs the result from this implementation (e.g. to append something to it), you have to
        turn this off to avoid infinite loop. See example plugins.
        :return:
        """

        # Allow custom syntactic objects to override this
        if peek_into_synobj and hasattr(self.syntactic_object, 'compose_html_for_viewing'):
            return self.syntactic_object.compose_html_for_viewing(self)

        html = []
        lower_html = []
        syntactic_mode = ctrl.settings.get('syntactic_mode')
        display_labels = ctrl.settings.get('show_display_labels')
        inner_labels = ctrl.settings.get('inner_labels')

        leaf = self.is_leaf(only_similar=True, only_visible=False)
        if self.triangle and not leaf:
            lower_html.append(self.get_triangle_text())
        if inner_labels == 2:  # use secondary labels
            html.append(as_html(self.syntactic_object.get_secondary_label()))
        elif display_labels and self.display_label:
            html.append(as_html(self.display_label))
        else:
            if self.label_html:
                html.append(self.label_html)
            if self.index and not syntactic_mode:
                html.append('<sub>%s</sub>' % self.index)

        if self.gloss and self.should_show_gloss_in_label():
            if html:
                html.append('<br/>')
            html.append(as_html(self.gloss))
        if html and html[-1] == '<br/>':
            html.pop()
        return ''.join(html), ''.join(lower_html)

    def compose_html_for_editing(self):
        """ This is used to build the html when quickediting a label. It should reduce the label
        into just one field value that is allowed to be edited, in constituentnode this is
        either label or display_label. This can be overridden in syntactic object by having
        'compose_html_for_editing' -method there. The method returns a tuple,
          (field_name, html).
        :return:
        """

        # Allow custom syntactic objects to override this
        if hasattr(self.syntactic_object, 'compose_html_for_editing'):
            return self.syntactic_object.compose_html_for_editing(self)

        display_labels = ctrl.settings.get('show_display_labels')
        if display_labels and self.display_label:
            return 'display_label', as_html(self.display_label)
        else:
            return 'label', as_html(self.label)

    def as_bracket_string(self):
        """ returns a simple bracket string representation """
        if not self.syntactic_object:
            return '0'
        if self.display_label:
            children = list(self.get_children(similar=True, visible=False))
            if children:
                return '[.%s %s ]' % \
                       (self.display_label, ' '.join((c.as_bracket_string() for c in children)))
            else:
                return str(self.display_label)
        else:
            inside = ' '.join(
                (x.as_bracket_string() for x in self.get_children(similar=True, visible=False)))
            if inside:
                return '[ ' + inside + ' ]'
            else:
                return str(self.syntactic_object)

    def get_attribute_nodes(self, label_key=''):
        """

        :param label_k ey:
        :return:
        """
        atts = [x.end for x in self.edges_down if x.edge_type == g.ATTRIBUTE_EDGE]
        if label_key:
            for a in atts:
                if a.attribute_label == label_key:
                    return a
        else:
            return atts

    def is_unnecessary_merger(self):
        """ This merge can be removed, if it has only one child
        :return:
        """
        return len(list(self.get_children(similar=True, visible=False))) == 1


    # Conditions ##########################
    # These are called from templates with getattr, and may appear unused for IDE's analysis.
    # Check their real usage with string search before removing these.

    def inner_add_sibling(self):
        """ Node has child and it is not unary child. There are no other reasons preventing
        adding siblings
        :return: bool
        """
        return self.get_children(similar=True, visible=False) and not self.is_unary()

    def has_one_child(self):
        return len(self.get_children(similar=True, visible=False)) == 1

    def can_be_projection_of_another_node(self):
        """ Node can be projection from other nodes if it has other nodes
        below it.
        It may be necessary to move this check to syntactic level at some
        point.
        :return:
        """
        if ctrl.settings.get('use_projection'):
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
        children = self.get_children(similar=True, visible=False)
        my_heads = self.get_head_nodes()
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
            head_nodes_of_child = child.get_head_nodes() or [child]
            enabled = True
            d = {'text': '%s%s' % (prefix[n], ', '.join([x.short_str() for x in
                                                         head_nodes_of_child])),
                 'value': n,
                 'is_checked': head_nodes_of_child == my_heads,
                 'enabled': enabled,
                 'tooltip': 'inherit label from ' + str(head_nodes_of_child)}
            r.append(d)
        return r

    def guess_projection(self):
        """ Analyze label, display_label and children and try to guess if this is a
        projection from somewhere. Set head accordingly.
        :return:
        """

        def find_original(node, head_node):
            """ Go down in trees until the final matching label/display_label is found.
            :param node: where to start searching
            :param head:
            :return:
            """
            for child in node.get_children(similar=True, visible=False):
                al = child.display_label or child.label
                al = str(al)
                if strip_xbars(al) == head_node:
                    found_below = find_original(child, head_node)
                    if found_below:
                        return found_below
                    else:
                        return child
            return None

        al = self.display_label or self.label
        head_node = find_original(self, strip_xbars(str(al)))
        self.set_projection(head_node)

    def set_projection(self, head):
        """ Set this node to be projection from new_head.
        :param new_head:
        :return:
        """
        print('set_projection called with ', head)

        if head:
            if isinstance(head, list):
                if isinstance(head[0], Node):
                    self.syntactic_object.set_head([x.syntactic_object for x in head])
                else:
                    self.syntactic_object.set_head(head)
            elif isinstance(head, Node):
                self.syntactic_object.set_head([head.syntactic_object])
            else:
                self.syntactic_object.set_head([head])
        else:
            self.syntactic_object.set_head([])

    def get_syn_heads(self):
        """ Heads are syntactic objects, not nodes. This helper reminds of that and fails nicely.
        :return:
        """
        if not self.syntactic_object:
            return []
        return getattr(self.syntactic_object, 'heads', [])

    def get_head_nodes(self):
        """ Heads are syntactic objects, not nodes. This is helper to get the node instead.
        :return:
        """
        heads = []
        for synobj in self.syntactic_object.heads:
            if synobj:
                h = self.forest.get_node(synobj)
                if h:
                    heads.append(h)
            else:
                print(self.syntactic_object, ' has bad heads: ', self.syntactic_object.heads)
        return heads

    @property
    def contextual_color(self):
        """ Drawing color that is sensitive to node's state
        :return: QColor
        """

        if ctrl.is_selected(self):
            base = ctrl.cm.selection()
        elif self.in_projections:
            base = ctrl.cm.get(self.in_projections[0].color_id)
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
                self.forest.delete_node(gloss_node)
            elif syn_gloss and not gloss_node:
                self.forest.create_gloss_node(self)
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
        return (not (self.display_label or self.label or self.index)) and self.is_leaf()

    # ## Indexes and chains ###################################

    def is_chain_head(self):
        """


        :return:
        """
        if self.index:
            return not (self.is_leaf() and self.label == 't')
        return False

    ### UI support

    def dragging_constituent(self):
        """ Check if the currently dragged item is constituent and can connect with me
        :return:
        """
        return self.is_dragging_this_type(g.CONSTITUENT_NODE)

    def dragging_feature(self):
        """ Check if the currently dragged item is feature and can connect with me
        :return:
        """
        return self.is_dragging_this_type(g.FEATURE_NODE)

    def dragging_gloss(self):
        """ Check if the currently dragged item is gloss and can connect with me
        :return:
        """
        return self.is_dragging_this_type(g.GLOSS_NODE)

    def dragging_comment(self):
        """ Check if the currently dragged item is comment and can connect with me
        :return:
        """
        return self.is_dragging_this_type(g.COMMENT_NODE)

    # ### Features #########################################
    # !!!! Shouldn't be done this way. In forest, create a feature, then connect it to
    # ConstituentNode and let Forest's
    # methods to take care that syntactic parts are reflected properly. ConstituentNode shouldn't
    #  be modifying its
    # syntactic component.
    # def set_feature(self, syntactic_feature=None, key=None, value=None, string=''):
    #     """ Convenience method for assigning a new feature node related to this constituent.
    #     can take syntactic feature, which is assumed to be already assigned for the syntactic
    # constituent.
    #         Can take key, value pair to create new syntactic feature object, and then a proper
    # feature object is created from this.
    #     :param syntactic_feature:
    #     :param key:
    #     :param value:
    #     :param string:
    #     """
    #     assert self.syntactic_object
    #     if syntactic_feature:
    #         if ctrl.forest.settings.draw_features:
    #             ctrl.forest.create_feature_node(self, syntactic_feature)
    #     elif key:
    #         sf = self.syntactic_object.set_feature(key, value)
    #         self.set_feature(syntactic_feature=sf)
    #     elif string:
    #         features = ctrl.forest.parse_features(string, self)
    #         if 'gloss' in features:
    #             self.gloss = features['gloss']
    #             del features['gloss']
    #         for feature in features.values():
    #             self.set_feature(syntactic_feature=feature)
    #         self.update_features()

    def get_features(self):
        """ Returns FeatureNodes """
        return self.get_children(visible=True, of_type=g.FEATURE_EDGE)

    def update_features(self):
        """ """
        pass
        # if not self.syntactic_object:
        # return
        # current_features = set([x.syntactic_object.get() for x in self.get_features()])
        # correct_features = self.syntactic_object.features
        # print(current_features, correct_features)
        # for key, item in correct_features.items():
        # if key not in current_features:
        # self.set_feature(syntactic_feature=item, key=key)
        # else:
        # current_features.remove(key)
        # if current_features:
        # print('leftover features:', current_features)

    def get_features_as_string(self):
        """
        :return:
        """
        features = [f.syntactic_object for f in self.get_features()]
        feature_strings = [str(f) for f in features]
        return ', '.join(feature_strings)

    # Reflecting structural changes in syntax
    # Nodes are connected and disconnected to each other by user, through UI,
    # and these connections may have different syntactical meaning.
    # Each node type can define how connect or disconnect affects syntactic
    # elements.
    #
    # These are called in all forest's connect and disconnect -activities,
    # so they get called also when the connection was initiated from syntax.
    # In these cases methods should be smart enough to notice that the
    # connection is already there and not duplicate it.
    # ########################################

    def connect_in_syntax(self, edge):
        """ Implement this if connecting this node (using this edge) needs to be
         reflected in syntax. Remember to verify it already isn't there.
        :param edge:
        :return:
        """
        if edge.edge_type is not g.CONSTITUENT_EDGE:
            # We care only for constituent relations
            return
        assert edge.end is self
        s = edge.start
        if s and s.node_type == g.CONSTITUENT_NODE and s.syntactic_object:
            # Calling syntax!
            parent = s.syntactic_object
            child = self.syntactic_object
            if child not in parent.parts:
                ctrl.syntax.connect(parent, child)

    def disconnect_in_syntax(self, edge):
        """ Implement this if disconnecting this node (using this edge) needs
        to be reflected in syntax. Remember to verify it already isn't there.
        :param edge:
        :return:
        """
        if edge.edge_type is not g.CONSTITUENT_EDGE:
            # We care only for constituent relations
            return
        assert edge.end is self
        s = edge.start
        if s and s.node_type == g.CONSTITUENT_NODE and s.syntactic_object:
            # Calling syntax!
            parent = s.syntactic_object
            child = self.syntactic_object
            if child in parent.parts:
                ctrl.syntax.disconnect(parent, child)

    # ### Selection ########################################################

    def update_selection_status(self, selected):
        """

        :param selected:
        """

        super().update_selection_status(selected)
        if ctrl.cm.use_glow():
            self.effect.setEnabled(selected)
            self.update()

    # ### Checks for callable actions ####

    def can_top_merge(self):
        """
        :return:
        """
        top = self.get_top_node()
        return self is not top and self not in top.get_children()

    # ### Dragging #####################################################################

    # ## Most of this is implemented in Node

    def prepare_children_for_dragging(self, scene_pos):
        """ Implement this if structure is supposed to drag with the node
        :return:
        """
        children = self.forest.list_nodes_once(self)

        for tree in self.trees:
            dragged_index = tree.sorted_constituents.index(self)
            for i, node in enumerate(tree.sorted_constituents):
                if node is not self and i > dragged_index and node in children:
                    node.start_dragging_tracking(host=False, scene_pos=scene_pos)

    #################################

    # ### Parents & Children ####################################################

    def is_projecting_to(self, other):
        """

        :param other:
        """
        pass

    # ###### Halo for showing some association with selected node (e.g. c-command) ######

    def toggle_halo(self, value):
        self.halo = value
        self.update()

    def paint(self, painter, option, widget=None):
        """ Painting is sensitive to mouse/selection issues, but usually with
        :param painter:
        :param option:
        :param widget:
        nodes it is the label of the node that needs complex painting """
        super().paint(painter, option, widget=widget)
        if self.halo:
            painter.drawEllipse(self.inner_rect)

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    label = SavedSynField("label")
    index = SavedField("index")
    display_label = SavedField("display_label")
    features = SavedSynField("features", if_changed=if_changed_features)
    gloss = SavedField("gloss", if_changed=update_gloss)
    head = SavedSynField("head")
    merge_order = SavedField("merge_order")
    select_order = SavedField("select_order")
    original_parent = SavedField("original_parent")

