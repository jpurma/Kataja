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
from PyQt5 import QtWidgets, QtCore, QtGui

import kataja.globals as g
from kataja.SavedField import SavedField
from kataja.parser.INodes import ITextNode, ICommandNode, as_text, extract_triangle, join_lines, \
    as_html
from kataja.saved.movables.Node import Node
import kataja.ui_graphicsitems.TouchArea as ta
import kataja.ui_widgets.buttons.OverlayButton as ob
from kataja.singletons import ctrl, classes, prefs
from kataja.uniqueness_generator import next_available_type_id
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
    editable = {}  # Uses custom ConstituentNodeEmbed instead of template-based NodeEditEmbed

    default_style = {
        'plain': {
            'color_key': 'content1',
            'font_id': g.MAIN_FONT,
            'font-size': 10,
            'visible': True
        },
        'fancy': {
            'color_key': 'content1',
            'font_id': g.MAIN_FONT,
            'font-size': 10,
            'visible': True

        }
    }

    default_edge = g.CONSTITUENT_EDGE
    allowed_child_types = [g.CONSTITUENT_NODE, g.FEATURE_NODE, g.GLOSS_NODE, g.COMMENT_NODE]

    # Touch areas are UI elements that scale with the trees: they can be
    # temporary shapes suggesting to drag or click here to create the
    # suggested shape.

    # touch_areas_when_dragging and touch_areas_when_selected are lists of strings, where strings
    # are names of classes found in TouchArea. There are ways for plugins to inject new
    # TouchAreas.
    #
    # TouchAreas have classmethods 'select_condition' and 'drop_condition' which are used to
    # check if this is an appropriate toucharea to draw for given node or edge.
    # format.

    touch_areas_when_dragging = [ta.LeftAddTop, ta.LeftAddSibling, ta.RightAddSibling,
                                 ta.AddBelowTouchArea]
    touch_areas_when_selected = [ta.LeftAddTop, ta.RightAddTop, ta.MergeToTop,
                                 ta.LeftAddInnerSibling, ta.RightAddInnerSibling,
                                 ta.LeftAddUnaryChild, ta.RightAddUnaryChild, ta.LeftAddLeafSibling,
                                 ta.RightAddLeafSibling, ta.AddTriangleTouchArea,
                                 ta.RemoveTriangleTouchArea]

    buttons_when_selected = [ob.RemoveMergerButton, ob.NodeEditorButton, ob.RemoveNodeButton,
                             ob.NodeUnlockButton]

    def __init__(self, label=''):
        """ Most of the initiation is inherited from Node """
        Node.__init__(self)
        self.heads = []

        # ### Projection -- see also preferences that govern if these are used
        self.can_project = True
        self.projecting_to = set()

        self.index = ''
        self.label = label
        self.autolabel = ''
        self.gloss = ''

        self.is_trace = False
        self.merge_order = 0
        self.select_order = 0
        self.in_projections = []
        self.cached_sorted_feature_edges = []
        self._can_cascade_edges = None

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
        self.update_node_shape()
        self.update_label()
        self.update_visibility()
        self.update_tooltip()
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

    def is_card(self):
        return self.label_object and self.label_object.is_card()

    def preferred_z_value(self):
        if self.is_card():
            return 2
        else:
            return 20

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
                    self.triangle_stack = [self]
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

        self.label = join_lines(rows)
        # now as rows are in one INode / string, we can extract the triangle part and put it to
        # end. It is different to qtree's way of handling triangles, but much simpler for us in
        # long run.
        triangle_part = extract_triangle(self.label, remove_from_original=True)
        if triangle_part:
            assert isinstance(self.label, ITextNode)

            self.label.parts.append('\n')
            self.label.parts.append(triangle_part)
        if self.index:
            base = as_html(self.label)
            if base.strip().startswith('t<sub>'):
                self.is_trace = True

    def get_syntactic_label(self):
        if self.syntactic_object:
            return self.syntactic_object.label

    # Other properties

    @property
    def gloss_node(self):
        """
        :return:
        """
        gs = self.get_children(visible=True, of_type=g.GLOSS_EDGE)
        if gs:
            return gs[0]

    def is_edge(self):
        return self.syntactic_object and getattr(self.syntactic_object, 'word_edge', False)

    def has_ordered_children(self):
        mode = ctrl.settings.get('linearization_mode')
        if mode == g.NO_LINEARIZATION or mode == g.RANDOM_NO_LINEARIZATION:
            return False
        elif mode == g.USE_LINEARIZATION:
            return getattr(self.syntactic_object, 'is_ordered', False)
        else:
            return True

    def get_sorted_constituents(self):
        sorted_constituents = []
        used = set()

        def add_children(node):
            if node not in used:
                used.add(node)
                sorted_constituents.append(node)
                for child in node.get_children(similar=True, visible=False):
                    add_children(child)

        add_children(self)
        return sorted_constituents

    def get_sorted_leaf_constituents(self):
        sorted_constituents = []
        used = set()

        def add_children(node):
            if node not in used:
                used.add(node)
                children = node.get_children(similar=True, visible=False)
                if not children:
                    sorted_constituents.append(node)
                else:
                    for child in children:
                        add_children(child)

        add_children(self)
        return sorted_constituents

    def reindex_edges(self):
        self._can_cascade_edges = None
        self.can_cascade_edges()
        super().reindex_edges()


    def update_node_shape(self):
        self.label_object.node_shape = ctrl.settings.get('node_shape')

    def should_show_gloss_in_label(self) -> bool:
        return ctrl.settings.get('lock_glosses_to_label') == 1

    def update_tooltip(self) -> None:
        """ Hovering status tip """
        tt_style = f'<tt style="background:{ctrl.cm.paper2().name()};">%s</tt>'
        ui_style = f'<strong style="color:{ctrl.cm.ui().name()};">%s</tt>'

        lines = []
        if self.is_trace:
            lines.append("<strong>Trace</strong>")
        elif self.is_leaf():
            lines.append("<strong>Leaf constituent</strong>")
            lines.append(f"Syntactic label: {repr(self.get_syn_label())}")
        else:
            lines.append("<strong>Set constituent</strong>")
            lines.append(f"Syntactic label: {repr(self.get_syn_label())}")
        if self.index:
            lines.append(f' Index: {repr(self.index)}')

        heads = ["itself" if h is self else f'{h.get_syn_label()}, {tt_style % h.uid}' for h in
                 self.heads]
        heads = '; '.join(heads)
        if len(self.heads) == 1:
            lines.append(f'head: {heads}')
        elif len(self.heads) > 1:
            lines.append(f'heads: {heads}')

        # x, y = self.current_scene_position
        # lines.append(f'pos: ({x:.1f},{y:.1f})')

        if self.use_adjustment:
            lines.append(f' adjusted position ({self.adjustment[0]:.1f}, {self.adjustment[1]:.1f})')
        lines.append(f'uid: {tt_style % self.uid}')

        if self.syntactic_object:
            lines.append(f'Inherited features: '
                         f'{self.syntactic_object.inherited_features}')
        if self.syntactic_object and self.syntactic_object.word_edge:
            lines.append('--Word edge--')
        lines.append('')
        if self.selected:
            lines.append(ui_style % 'Click to edit text, drag to move')
        else:
            lines.append(ui_style % 'Click to select, drag to move')


        self.k_tooltip = '<br/>'.join(lines)

    def short_str(self):
        label = as_text(self.label)
        if label:
            lines = label.splitlines()
            if len(lines) > 3:
                label = f'{lines[0]} ...\n{lines[-1]}'
        syn_label = as_text(self.get_syn_label())
        if label and syn_label:
            return f'{label} ({syn_label})'
        else:
            return label or syn_label or "no label"

    def set_string(self):
        """ This can be surprisingly expensive to calculate
        :return: 
        """
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
        label = as_text(self.label, single_line=True)
        syn_label = as_text(self.get_syn_label(), single_line=True)
        if label and syn_label:
            return f'CN {label} ({syn_label})'
        else:
            return f'CN {label or syn_label or "no label"}'

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

        label_text_mode = self.allowed_label_text_mode()
        include_index = False
        l = ''
        if label_text_mode == g.NODE_LABELS:
            if self.label:
                l = self.label
            elif self.syntactic_object:
                l = self.syntactic_object.label
        elif label_text_mode == g.NODE_LABELS_FOR_LEAVES:
            if self.label:
                l = self.label
            elif self.syntactic_object and self.is_leaf(only_similar=True, only_visible=False):
                l = self.syntactic_object.label
        elif label_text_mode == g.SYN_LABELS:
            if self.syntactic_object:
                l = self.syntactic_object.label
        elif label_text_mode == g.SYN_LABELS_FOR_LEAVES:
            if self.syntactic_object and self.is_leaf(only_similar=True, only_visible=False):
                l = self.syntactic_object.label
        elif label_text_mode == g.SECONDARY_LABELS:
            if self.syntactic_object:
                l = self.syntactic_object.get_secondary_label()
        elif label_text_mode == g.XBAR_LABELS:
            l = self.get_autolabel()
        separate_triangle = bool(self.is_cosmetic_triangle() and self.triangle_stack[-1] is self)
        l_html = as_html(l, omit_triangle=separate_triangle,
                         include_index=include_index and self.index)
        if l_html:
            html.append(l_html)

        if self.gloss and self.should_show_gloss_in_label():
            if html:
                html.append('<br/>')
            html.append(as_html(self.gloss))
        if html and html[-1] == '<br/>':
            html.pop()

        # Lower part
        lower_html = ''
        if separate_triangle:
            qroof_content = extract_triangle(l)
            if qroof_content:
                lower_html = as_html(qroof_content)
        return ''.join(html), lower_html

    def compose_html_for_editing(self):
        """ This is used to build the html when quickediting a label. It should reduce the label
        into just one field value that is allowed to be edited, in constituentnode this is
        either label or synobj's label. This can be overridden in syntactic object by having
        'compose_html_for_editing' -method there. The method returns a tuple,
          (field_name, setter, html).
        :return:
        """

        # Allow custom syntactic objects to override this
        if self.syntactic_object and hasattr(self.syntactic_object, 'compose_html_for_editing'):
            return self.syntactic_object.compose_html_for_editing(self)
        label_text_mode = self.allowed_label_text_mode()
        if label_text_mode == g.NODE_LABELS or label_text_mode == g.NODE_LABELS_FOR_LEAVES:
            if self.label:
                if self.triangle_stack:
                    lower_part = extract_triangle(self.label)
                    return 'node label', as_html(self.label,
                                                 omit_triangle=True) + '<br/>' + as_html(
                        lower_part or '')
                else:
                    return 'node label', as_html(self.label)
            elif self.syntactic_object:
                return 'syntactic label', as_html(self.syntactic_object.label)
            else:
                return '', '', ''
        elif label_text_mode == g.SYN_LABELS or label_text_mode == g.SYN_LABELS_FOR_LEAVES:
            if self.syntactic_object:
                return 'syntactic label', as_html(self.syntactic_object.label)
            else:
                return '', ''
        else:
            return '', ''

    def parse_edited_label(self, label_name, value):
        success = False
        if self.syntactic_object and hasattr(self.syntactic_object, 'parse_edited_label'):
            success = self.syntactic_object.parse_edited_label(label_name, value)
        if not success:
            if label_name == 'node label':
                self.poke('label')
                self.label = value
                return True
            elif label_name == 'syntactic label':
                self.syntactic_object.label = value
                return True
            elif label_name == 'index':
                self.index = value
        return False

    def as_bracket_string(self):
        """ returns a simple bracket string representation """
        if self.label:
            children = list(self.get_children(similar=True, visible=False))
            if children:
                return '[.%s %s ]' % (
                    self.label, ' '.join((c.as_bracket_string() for c in children)))
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

    def get_autolabel(self):
        return self.autolabel

    def is_unnecessary_merger(self):
        """ This merge can be removed, if it has only one child
        :return:
        """
        return len(list(self.get_children(similar=True, visible=False))) == 1

    def can_cascade_edges(self):
        """ Cascading edges is a visual effect for nodes that try to display many similar edges
        that go through this node. When cascaded, each edge has increasing/decreasing starting y
        compared to others. It gets ugly if some edges are strongly cascaded while others are
        flat, so node should make a decision if this should be applied at all.
        :return:
        :rtype:
        """
        if self._can_cascade_edges is not None:
            return self._can_cascade_edges
        else:
            self._can_cascade_edges = True
            for edge in self.edges_down:
                if edge.edge_type == g.FEATURE_EDGE and not edge.start_links_to:
                    self._can_cascade_edges = False
                    break
            return self._can_cascade_edges

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

    def contextual_color(self):
        """ Drawing color that is sensitive to node's state
        :return: QColor
        """

        if self.selected:
            base = ctrl.cm.selection()
        elif self.in_projections and self.in_projections[0].style == g.COLORIZE_PROJECTIONS:
            base = ctrl.cm.get(self.in_projections[0].color_key)
        else:
            base = self.color
        if self.drag_data:
            return ctrl.cm.lighter(base)
        elif ctrl.pressed is self:
            return ctrl.cm.active(base)
        elif self.hovering:
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

    def gather_children(self):
        """ If there are other Nodes that are childItems for this node, arrange them to their 
        proper positions. 
        
        For ConstituentNodes this means collecting the locked-in FeatureNodes and positioning 
        them in three possible ways. 
        :return: 
        """

        fpos = ctrl.settings.get('feature_positioning')
        shape = ctrl.settings.get('node_shape')
        children = self.get_children(visible=True, similar=False)
        if not children:
            return
        if shape == g.CARD:
            fpos = g.TWO_COLUMNS  # only two column arrangement looks good on cards

        if fpos == g.VERTICAL_COLUMN:
            center_x = self.boundingRect().center().x()
            bottom_y = self.boundingRect().bottom()
            y = bottom_y
            for fnode in children:
                if fnode.locked_to_node is self:
                    fbr = fnode.future_children_bounding_rect()
                    fnode.move_to(center_x, y - fbr.y())
                    y += fbr.height() + 2
        elif fpos == g.HORIZONTAL_ROW:  # horizontal
            bottom_y = self.boundingRect().bottom()
            nods = []
            total_width = 0
            max_height = 0
            for fnode in children:
                if fnode.locked_to_node is self:
                    fbr = fnode.future_children_bounding_rect()
                    nods.append((fnode, total_width - fbr.x()))
                    total_width += fbr.width() + 4
                    if fnode.height > max_height:
                        max_height = fbr.height()
            if nods:
                left_margin = (total_width / -2)
                y = bottom_y + (max_height / 2)
                for fnode, x in nods:
                    fnode.move_to(left_margin + x, y)
        elif fpos == g.TWO_COLUMNS:  # card layout, two columns
            in_card = ctrl.settings.get('node_shape') == g.CARD
            cw, ch = self.label_object.card_size
            center_x = self.boundingRect().center().x()
            top_y = 22
            left_margin = center_x - (cw / 2)
            right_margin = center_x + (cw / 2)
            left_nods = []
            right_nods = []
            for fnode in children:
                if fnode.locked_to_node is self:
                    if fnode.is_needy() or fnode.is_satisfied():
                        right_nods.append(fnode)
                    else:
                        left_nods.append(fnode)
            y = top_y
            if in_card:
                nup_width = 4
                hspace = ch - top_y
                if left_nods:
                    node_hspace = hspace / len(left_nods)
                    half_h = node_hspace / 2
                    for fnode in left_nods:
                        fbr = fnode.future_children_bounding_rect()
                        fnode.move_to(left_margin - fbr.x() - nup_width, y + half_h)
                        y += node_hspace
                if right_nods:
                    y = top_y
                    node_hspace = hspace / len(right_nods)
                    half_h = node_hspace / 2
                    for fnode in right_nods:
                        fbr = fnode.future_children_bounding_rect()
                        fnode.move_to(right_margin - fbr.width() - fbr.x(), y + half_h)
                        y += node_hspace
            else:
                for fnode in left_nods:
                    fbr = fnode.future_children_bounding_rect()
                    fnode.move_to(left_margin + fbr.width() / 2, y)
                    y += fbr.height() + 2
                y = top_y
                for fnode in right_nods:
                    fbr = fnode.future_children_bounding_rect()
                    fnode.move_to(right_margin - fbr.width() / 2, y)
                    y += fbr.height() + 2

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

    # ### Features #########################################

    def get_features(self):
        """ Returns FeatureNodes """
        if self.syntactic_object:
            g = ctrl.forest.get_node
            return [g(f) for f in self.syntactic_object.get_features()]
        else:
            return [f for f in self.get_children(visible=True, of_type=g.FEATURE_EDGE) if
                    f.node_type != g.FEATURE_NODE]

    def get_features_as_string(self):
        """
        :return:
        """
        if self.syntactic_object:
            feature_strings = [str(f) for f in self.syntactic_object.features]
            return ', '.join(feature_strings)
        return ''

    def is_merging_features(self):
        if self.syntactic_object:
            syn_feats = getattr(self.syntactic_object, 'checked_features', None)
            nodes = []
            if syn_feats:
                for f in syn_feats:
                    n = ctrl.forest.get_node(f)
                    if n:
                        nodes.append(n)
            return nodes

    # ### Checks for callable actions ####

    def can_top_merge(self):
        """
        :return:
        """
        return bool(self.get_parents())

    # ### Dragging #####################################################################

    # ## Most of this is implemented in Node

    def prepare_children_for_dragging(self, scene_pos):
        """ Drag those nodes that are children of the current node, but don't include them into
        drag them if they are (also) raised above it.
        :return:
        """
        nodes_above = set()
        for top_node in self.get_highest():
            for node in top_node.get_sorted_nodes():
                if node is self:
                    break
                nodes_above.add(node)

        for child in self.get_sorted_nodes():
            if child not in nodes_above:
                child.prepare_dragging_participiant(host=False, scene_pos=scene_pos)

    #################################

    # ### Parents & Children ####################################################

    def is_projecting_to(self, other):
        """

        :param other:
        """
        pass

    # ### Paint overrides

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget=widget)
        feats = self.is_merging_features()
        if feats and False:
            old_pen = painter.pen()
            feat_color = feats[0].get_color_key()
            r = QtCore.QRectF(self.inner_rect)
            w = r.width()
            h = r.height()
            if w > h:
                s = h
            else:
                s = w
            c = r.center()
            r = QtCore.QRectF(0, 0, s, s)
            r.moveCenter(c)
            if ctrl.printing:
                if not feat_color.endswith('tr'):
                    feat_color = feat_color + 'tr'
                color = ctrl.cm.get(feat_color)
                painter.setBrush(color)
            else:
                gradient = QtGui.QRadialGradient(0, 0, r.height() / 2, 0, r.top() + 4)
                if ctrl.cm.light_on_dark():
                    color = ctrl.cm.get(feat_color)
                    gradient.setColorAt(1, QtCore.Qt.transparent)
                    gradient.setColorAt(0, color)
                else:
                    if not feat_color.endswith('tr'):
                        feat_color = feat_color + 'tr'
                    color = ctrl.cm.get(feat_color)
                    gradient.setColorAt(0, QtCore.Qt.transparent)
                    gradient.setColorAt(1, color)
                painter.setBrush(gradient)
            painter.setPen(QtCore.Qt.NoPen)
            painter.drawEllipse(r)
            painter.setPen(old_pen)
        elif self.has_visible_label():
            old_pen = painter.pen()
            painter.setPen(QtCore.Qt.NoPen)
            paper = ctrl.cm.paper()
            r = self.inner_rect
            w = r.width()
            h = r.height()
            if w > h:
                radius = h / 2
            else:
                radius = w / 2

            if ctrl.printing:
                paper = QtGui.QColor(255, 255, 255, 128)
                painter.setBrush(paper)
            else:
                gradient = QtGui.QRadialGradient(0, 0, radius)
                gradient.setColorAt(0, paper)
                gradient.setColorAt(1, QtCore.Qt.transparent)
                painter.setBrush(gradient)
            painter.drawEllipse(r)
            painter.setPen(old_pen)
        if self.is_edge():
            r = self.inner_rect
            p = QtGui.QPen(ctrl.cm.drawing())
            p.setWidth(3)
            painter.setPen(p)
            painter.drawLine(r.topLeft().toPoint(), r.topRight().toPoint())

    @staticmethod
    def allowed_label_text_mode():
        mode = ctrl.settings.get('label_text_mode')
        if mode == g.SECONDARY_LABELS and not ctrl.forest.syntax.supports_secondary_labels:
            return g.SYN_LABELS
        if not ctrl.settings.get('syntactic_mode'):
            return mode
        if mode == g.NODE_LABELS:
            return g.SYN_LABELS
        elif mode == g.NODE_LABELS_FOR_LEAVES:
            return g.SYN_LABELS_FOR_LEAVES
        elif mode == g.XBAR_LABELS:
            return g.SYN_LABELS

    @staticmethod
    def allowed_label_text_modes():
        """
        SYN_LABELS = 0
        SYN_LABELS_FOR_LEAVES = 1
        NODE_LABELS = 2
        NODE_LABELS_FOR_LEAVES = 3
        XBAR_LABELS = 4
        SECONDARY_LABELS = 5
        NO_LABELS = 6
        :return:
        """
        if ctrl.settings.get('syntactic_mode'):
            allowed = [0, 1, 5, 6]
        else:
            allowed = [0, 1, 2, 3, 4, 5, 6]
        if (not ctrl.forest) or (not ctrl.forest.syntax.supports_secondary_labels):
            allowed.remove(5)
        return allowed

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    label = SavedField("label")
    index = SavedField("index")
    gloss = SavedField("gloss", if_changed=update_gloss)
    heads = SavedField("heads")
