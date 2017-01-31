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
from PyQt5 import QtWidgets

import kataja.globals as g
from kataja.SavedField import SavedField
from kataja.parser.INodes import ITextNode, ICommandNode, as_text
from kataja.saved.movables.Node import Node
from kataja.singletons import ctrl, classes, prefs
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

    editable = {'label': dict(name='Displayed label', prefill='label',
                              tooltip='Freeform label or text for ',
                              input_type='expandingtext', order=15,
                              on_edit='update_preview'),
                'synlabel': dict(name='Syntactic label', prefill='label',
                                 tooltip='Label used in syntactic computations, plain string. '
                                         'Visible in <i>syntactic mode</i> or if <i>Displayed '
                                         'label</i> is empty.',
                                 width=160,
                                 focus=True, syntactic=True, order=10, on_edit='update_preview'),
                'triangle': dict(name='Triangle', input_type='checkbox', order=35,
                                 on_edit='update_preview', tooltip='Draw a triangle on top of a '
                                                                   'node to mark an unanalysed '
                                                                   'part of a sentence'),
                'triangle_row': dict(name='label row under triangle', align='line-end', width=20,
                                     prefill=-1, order=36, min=-4, max=4, input_type='spinbox',
                                     tooltip='Use this row of <i>Displayed label</i> '
                                             'as text under the triangle, '
                                             'use negative numbers to count from bottom'),
                'index': dict(name='Index', align='line-end', width=20, prefill='i',
                              tooltip='Optional index for linking multiple instances', order=11,
                              on_edit='update_preview'),
                'preview': dict(name='Preview', tooltip='Preview how label will be displayed. '
                                                        'Display label overrides computational '
                                                        'label.', input_type='preview'),
                'gloss': dict(name='Gloss', prefill='gloss',
                              tooltip='translation (optional)', width=200, condition='is_leaf',
                              order=40),
                'heads': dict(name='Projection from',
                              tooltip='Node receives label and maybe features from this or these '
                                      'children',
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

    def __init__(self, label=''):
        """ Most of the initiation is inherited from Node """
        Node.__init__(self)
        self.heads = []

        # ### Projection -- see also preferences that govern if these are used
        self.can_project = True
        self.projecting_to = set()

        self.index = ''
        self.label = label
        self.gloss = ''
        self.triangle_row = -1

        self.is_trace = False
        self.merge_order = 0
        self.select_order = 0
        self.original_parent = None
        self.in_projections = []

        # ### Cycle index stores the order when node was originally merged to structure.
        # going up in trees, cycle index should go up too

    def after_init(self):
        """ After_init is called in 2nd step in process of creating objects:
        1st wave creates the objects and calls __init__, and then iterates through and sets the
        values. 2nd wave calls after_inits for all created objects. Now they can properly refer
        to each other and know their values.
        :return: None
        """
        self.update_gloss()
        self.update_label_shape()
        self.update_label()
        self.update_visibility()
        self.update_status_tip()
        self.announce_creation()
        if prefs.glow_effect:
            self.toggle_halo(True)
        ctrl.forest.store(self)

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

    def load_values_from_parsernode(self, parsernode):
        """ Update constituentnode with values from parsernode
        :param parsernode:
        :return:
        """

        def remove_dot_label(inode, row_n):
            for i, part in enumerate(list(inode.parts)):
                if isinstance(part, str):
                    if part.startswith('.'):
                        inode.parts[i] = part[1:]
                    return True
                elif isinstance(part, ICommandNode) and part.command == 'qroof':
                    self.triangle_row = row_n
                    self.triangle = True
                    continue
                else:
                    return remove_dot_label(part, row_n)

        if parsernode.index:
            self.index = parsernode.index
        rows = parsernode.label_rows
        # Remove dotlabel

        for i, row in enumerate(list(rows)):
            if isinstance(row, str):
                if row.startswith('.'):
                    rows[i] = row[1:]
                break
            stop = remove_dot_label(row, i)
            if stop:
                break
        # △
        # ########### Flatten rows of label into one string/ITextNode/ICommandNode
        # It gets bit complicated, because str+ITextNode, str+str, ITextNode+ITextNode and
        # ICommandNode + ... all need different ways to join them

        if len(rows) > 1:
            last_row = None
            while rows:
                row = rows.pop()
                if last_row is not None:
                    if isinstance(row, ICommandNode):
                        # commandnode + commandnode, commandnode + str
                        if isinstance(last_row, ICommandNode) or isinstance(last_row, str):
                            last_row = ITextNode(parts=[row, '\n', last_row])
                        # commandnode + textnode
                        else:
                            last_row.parts = [row, '\n'] + last_row.parts
                    elif isinstance(row, ITextNode):
                        # textnode + commandnode, textnode + str
                        if isinstance(last_row, ICommandNode) or isinstance(last_row, str):
                            row.parts.append('\n')
                            row.parts.append(last_row)
                            last_row = row
                        # textnode + textnode
                        else:
                            row.parts.append('\n')
                            row.parts += last_row.parts
                            last_row = row
                    # str + commandnode
                    elif isinstance(last_row, ICommandNode):
                        row = ITextNode(parts=[row, '\n', last_row])
                        last_row = row
                    # str + textnode
                    elif isinstance(last_row, ITextNode):
                        last_row.parts = [row, '\n'] + last_row.parts
                    # str + str
                    else:
                        last_row = row + '\n' + last_row
                else:
                    last_row = row
            self.label = last_row
        elif len(rows) == 1:
            self.label = rows[0]
        else:
            self.label = ''

    # Editing with NodeEditEmbed and given editable-template
    def update_preview(self):
        """ Update preview label in NodeEditEmbed with composite from label, synobj's label and
        index.
        :param edited: the field that triggered the update.
        :return:
        """
        embed = self.sender().parent()
        surefail = 0
        while not hasattr(embed, 'fields') and surefail < 5:
            embed = embed.parent()
            surefail += 1

        index = embed.fields.get('index', None)
        label = embed.fields.get('label', None)
        triangle = embed.fields.get('triangle', None)
        triangle_row = embed.fields.get('triangle_row', -1)
        preview = embed.fields.get('preview', None)
        index_text = as_html(index.text())
        print('preview inode_text: ', label.inode_text())
        print('same as html: ', as_html(label.inode_text()))
        label_text = as_html(label.inode_text())
        parsed = label_text
        if index_text:
            parsed += '<sub>' + index_text + '</sub>'
        preview.setText(parsed)

    def update_label_visibility(self):
        """ Check if the label of the node has any content -- should it be
        displayed. Node itself can be visible even when its label is not.
        :return:
        """
        lo = self.label_object
        if not lo:
            self.update_label()
        self._label_visible = lo.has_content() or lo.is_quick_editing()
        lo.setVisible(self._label_visible)


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
            if (not syntactic_mode) and self.label:
                if isinstance(self.label, ITextNode):
                    return self.label.as_html().split('<br/>')[0]
                elif isinstance(self.label, str):
                    return self.label.splitlines()[0]
            else:
                return self.label_as_html()


    def recursive_lower_html(self, included=None):
        """ Build lower part (part under triangle) of html label.
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
            if (not syntactic_mode) and self.label:
                if isinstance(self.label, ITextNode):
                    return self.label.as_html().split('<br/>')[0]
                elif isinstance(self.label, str):
                    return self.label.splitlines()[0]
            else:
                return self.label_as_html()


    def label_as_html(self) -> str:
        """ Label, reliably a string
        :return:
        """
        return as_html(self.label)

    def update_label_shape(self):
        self.label_object.label_shape = ctrl.settings.get('label_shape')

    def should_show_gloss_in_label(self) -> bool:
        return ctrl.settings.get('show_glosses') == 1

    def update_status_tip(self) -> None:
        """ Hovering status tip """

        if self.label:
            label = f'Label: "{as_text(self.label)}" '
        else:
            label = ''
        syn_label = self.get_syn_label()
        if syn_label:
            syn_label = f' Constituent: "{as_text(syn_label)}" '
        else:
            syn_label = ''
        if self.is_trace:
            name = "Trace"
        if self.is_leaf():
            name = "Leaf "
        # elif self.is_top_node():
        #    name = "Set %s" % self.set_string() # "Root constituent"
        else:
            name = f"Set {self.set_string()}"
        if self.use_adjustment:
            adjustment = f' w. adjustment ({self.adjustment[0]:.1f}, {self.adjustment[1]:.1f})'
        else:
            adjustment = ''
        self.status_tip = f"{name} ({label}{syn_label} pos: ({self.current_scene_position[0]:.1f}, " \
                          f"{self.current_scene_position[1]:.1f}){adjustment} z-index: " \
                          f"{self.zValue()}/{self.z_value})"

    def short_str(self):
        label = as_text(self.label)
        syn_label = as_text(self.get_syn_label())
        if label and syn_label:
            return f'{label} ({syn_label})'
        else:
            return label or syn_label or "no label"

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
        label = as_text(self.label)
        syn_label = as_text(self.get_syn_label())
        if label and syn_label:
            return f'{label} ({syn_label})'
        else:
            return label or syn_label or "no label"

    def get_syn_label(self):
        if self.syntactic_object:
            return self.syntactic_object.label
        return ''

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
        label_text_mode = ctrl.settings.get('label_text_mode')
        l = ''
        if label_text_mode == g.NODE_LABELS:
            if self.label:
                l = as_html(self.label)
            elif self.syntactic_object:
                l = as_html(self.syntactic_object.label)
        elif label_text_mode == g.NODE_LABELS_FOR_LEAVES:
            if self.label:
                l = as_html(self.label)
            elif self.syntactic_object and self.is_leaf(only_similar=True, only_visible=False):
                l = as_html(self.syntactic_object.label)
        elif label_text_mode == g.SYN_LABELS:
            if self.syntactic_object:
                l = as_html(self.syntactic_object.label)
        elif label_text_mode == g.SYN_LABELS_FOR_LEAVES:
            if self.syntactic_object and self.is_leaf(only_similar=True, only_visible=False):
                l = as_html(self.syntactic_object.label)
        elif label_text_mode == g.SECONDARY_LABELS:
            if self.syntactic_object:
                l = as_html(self.syntactic_object.get_secondary_label())

        if l:
            html.append(l)
        if self.index and not syntactic_mode:
            html.append('<sub>%s</sub>' % self.index)

        if self.gloss and self.should_show_gloss_in_label():
            if html:
                html.append('<br/>')
            html.append(as_html(self.gloss))
        if html and html[-1] == '<br/>':
            html.pop()

        if self.triangle and not self.is_leaf(only_similar=True, only_visible=False):
            lower_html.append(self.get_triangle_text())

        return ''.join(html), ''.join(lower_html)

    def compose_html_for_editing(self):
        """ This is used to build the html when quickediting a label. It should reduce the label
        into just one field value that is allowed to be edited, in constituentnode this is
        either label or synobj's label. This can be overridden in syntactic object by having
        'compose_html_for_editing' -method there. The method returns a tuple,
          (field_name, html).
        :return:
        """

        # Allow custom syntactic objects to override this
        if hasattr(self.syntactic_object, 'compose_html_for_editing'):
            return self.syntactic_object.compose_html_for_editing(self)
        label_text_mode = ctrl.settings.get('label_text_mode')
        if label_text_mode == g.NODE_LABELS or label_text_mode == g.NODE_LABELS_FOR_LEAVES:
            if self.label:
                return 'label', as_html(self.label)
            elif self.syntactic_object:
                return 'synlabel', as_html(self.syntactic_object.label)
            else:
                return ''
        elif label_text_mode == g.SYN_LABELS or label_text_mode == g.SYN_LABELS_FOR_LEAVES:
            if self.syntactic_object:
                return 'synlabel', as_html(self.syntactic_object.label)
            else:
                return ''

    def as_bracket_string(self):
        """ returns a simple bracket string representation """
        if self.label:
            children = list(self.get_children(similar=True, visible=False))
            if children:
                return '[.%s %s ]' % \
                       (self.label, ' '.join((c.as_bracket_string() for c in children)))
            else:
                return str(self.label)
        else:
            inside = ' '.join(
                (x.as_bracket_string() for x in self.get_children(similar=True, visible=False)))
            if inside:
                return '[ ' + inside + ' ]'
            elif self.syntactic_object:
                return str(self.syntactic_object)
            else:
                return '-'

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
            heads_of_child = child.heads or [child]
            enabled = True
            d = {'text': '%s%s' % (prefix[n], ', '.join([x.short_str() for x in heads_of_child])),
                 'value': n,
                 'is_checked': heads_of_child == self.heads,
                 'enabled': enabled,
                 'tooltip': 'inherit label from ' + str(heads_of_child)}
            r.append(d)
        return r

    def guess_projection(self):
        """ Analyze labels and children and try to guess if this is a
        projection from somewhere. Set head accordingly.
        :return:
        """

        def find_original(node, head_node):
            """ Go down in trees until the final matching label is found.
            :param node: where to start searching
            :param head:
            :return:
            """
            for child in node.get_children(similar=True, visible=False):
                label = str(child.label or child.get_syn_label())
                if strip_xbars(label) == head_node:
                    found_below = find_original(child, head_node)
                    if found_below:
                        return found_below
                    else:
                        return child
            return None

        label = str(self.label or self.get_syn_label())
        head_node = find_original(self, strip_xbars(str(label)))
        self.set_heads(head_node)

    def set_heads(self, head):
        """ Set projecting head to be Node, list of Nodes or empty. Notice that this doesn't
        affect syntactic objects.
        :param head:
        :return:
        """
        if isinstance(head, list):
            self.heads = list(head)
        elif isinstance(head, Node):
            self.heads = [head]
        elif not head:
            self.heads = []
        else:
            raise ValueError

    def synobj_to_node(self):
        """ Update node's values from its synobj. Subclasses implement this.
        :return:
        """
        self.synheads_to_heads()

    def synheads_to_heads(self):
        """ Make sure that node's heads reflect synobjs heads.
        :return:
        """
        if self.syntactic_object:
            if hasattr(self.syntactic_object, 'heads'):
                heads = []
                for head in self.syntactic_object.heads:
                    node = ctrl.forest.get_node(head)
                    if node:
                        heads.append(node)
                self.heads = heads
                return
            elif hasattr(self.syntactic_object, 'head'):
                node = ctrl.forest.get_node(self.syntactic_object.head)
                if node:
                    self.heads = [node]
                    return
        self.heads = []
        return

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
                ctrl.free_drawing.delete_node(gloss_node)
            elif syn_gloss and not gloss_node:
                ctrl.free_drawing.create_gloss_node(host=self)
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
        return (not (self.syntactic_object or self.label or self.index)) and self.is_leaf()

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

    def get_features(self):
        """ Returns FeatureNodes """
        return self.get_children(visible=True, of_type=g.FEATURE_EDGE)

    def get_features_as_string(self):
        """
        :return:
        """
        features = [f.syntactic_object for f in self.get_features()]
        feature_strings = [str(f) for f in features]
        return ', '.join(feature_strings)

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
        children = ctrl.forest.list_nodes_once(self)

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


    def paint(self, painter, option, widget=None):
        """ Painting is sensitive to mouse/selection issues, but usually with
        :param painter:
        :param option:
        :param widget:
        nodes it is the label of the node that needs complex painting """
        super().paint(painter, option, widget=widget)

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    label = SavedField("label")
    index = SavedField("index")
    gloss = SavedField("gloss", if_changed=update_gloss)
    heads = SavedField("heads")
    triangle_row = SavedField("triangle_row")
    original_parent = SavedField("original_parent")

