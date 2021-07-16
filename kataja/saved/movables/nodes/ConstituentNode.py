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

from PyQt6 import QtCore, QtGui

import kataja.globals as g
import kataja.ui_graphicsitems.TouchArea as TA
import kataja.ui_widgets.buttons.OverlayButton as OB
from kataja.ComplexLabel import ComplexLabel
from kataja.SavedField import SavedField
from kataja.parser.INodes import as_text, as_html
from kataja.saved.movables.Node import Node
from kataja.singletons import ctrl, prefs, qt_prefs
from kataja.ui_widgets.embeds.ConstituentNodeEditEmbed import ConstituentNodeEditEmbed
from kataja.uniqueness_generator import next_available_type_id
from kataja.utils import coords_as_str, escape

__author__ = 'purma'


def flatten(thick_list):
    res = []

    def flat(listlike):
        for item in listlike:
            if isinstance(item, list) or isinstance(item, tuple):
                flat(item)
            else:
                res.append(item)

    flat(thick_list)
    return res

class ConstituentNode(Node):
    """ ConstituentNode is enriched with few elements that have no syntactic meaning but help with
     reading the trees aliases, indices and glosses.
    """
    __qt_type_id__ = next_available_type_id()
    display_name = ('Constituent', 'Constituents')
    short_name = "CN"
    display = True
    width = 20
    height = 20
    is_constituent = True
    quick_editable = False
    node_type = g.CONSTITUENT_NODE
    wraps = 'constituent'

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
    allowed_child_types = [g.GLOSS_NODE, g.COMMENT_NODE]

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

    touch_areas_when_dragging = []
    touch_areas_when_selected = [TA.AddTriangleTouchArea,
                                 TA.RemoveTriangleTouchArea]

    buttons_when_selected = [OB.NodeEditorButton, OB.NodeUnlockButton]

    embed_edit = ConstituentNodeEditEmbed

    def __init__(self, label='', forest=None):
        """ Most of the initiation is inherited from Node """
        super().__init__(forest=forest)
        self.label_object = ComplexLabel(parent=self)

        self.index = ''
        self.gloss = ''

        self.use_lexical_color = False
        self.is_trace = False
        self.cached_sorted_feature_edges = []
        self._can_cascade_edges = None
        self._lexical_color = None

        # ### Cycle index stores the order when node was originally merged to structure.
        # going up in trees, cycle index should go up too

    # Creating constituent nodes will happen in coarsely three different circumstances. There are different
    # presuppositions in each about the forest context in that creation.
    #
    # 1. Creating nodes because of user's drawing action or because the treeloader parsed a node into existence.
    #    Here the node is addition to existing and can immediately join into the necessary relations.
    # 2. Restoring nodes into forest from derivation step or from undo.
    #    Here there are bundle of nodes that are removed or added at once, so when they are sequently created, they may
    #    have relations to nodes that are not yet created -- handling of such relations has to be delayed until all
    #    nodes, edges etc. are there.
    # 3. Loading nodes into forests that are not currently visible. Same limitations as with 2, but also restoring of
    #    relations shouldn't refer to currently active forest -- it should point to the real originating forest.

    def after_init(self):
        """ After_init is called in 2nd step in process of creating objects:
        1st wave creates the objects and calls __init__, and then iterates through and sets the
        values. 2nd wave calls after_inits for all created objects. Now they can properly refer
        to each other and know their values.
        :return: None
        """
        self.update_gloss()
        self.update_cn_shape()
        self.update_label()
        self.update_visibility()
        self.update_tooltip()
        self.announce_creation()
        if prefs.glow_effect:
            self.toggle_halo(True)
        self.forest.store(self)

    def update_label(self):
        self.get_lexical_color(refresh=True)
        super().update_label()

    @property
    def label(self):
        return self.syntactic_object.label if self.syntactic_object else ''

    @label.setter
    def label(self, value):
        if self.syntactic_object:
            self.syntactic_object.label = value

    def get_gloss(self):
        if self.syntactic_object:
            return self.syntactic_object.gloss
        return self.gloss

    def set_gloss(self, text):
        if self.syntactic_object:
            self.syntactic_object.gloss = text
        else:
            self.gloss = text
        self.update_gloss()

    def is_card(self) -> bool:
        return self.label_object and self.label_object.is_card()

    def get_font_id(self) -> str:
        """
        :return:
        """
        if self.get_cn_shape() == g.FEATURE_SHAPE and self.has_merged_features():
            return self.forest.settings.get_for_node_type('font_id', node_type=g.FEATURE_NODE)
        return self.settings.get('font_id')

    def preferred_z_value(self) -> int:
        if self.is_card():
            return 2
        else:
            return 20

    # Other properties

    @property
    def label_text_mode(self):
        return self.forest.settings.get('label_text_mode')

    @property
    def gloss_node(self):
        """
        :return:
        """
        gs = self.get_children(visible=True, of_type=g.GLOSS_NODE)
        if gs:
            return gs[0]

    def is_edge(self):
        return self.syntactic_object and getattr(self.syntactic_object, 'word_edge', False)

    def has_ordered_children(self):
        mode = self.forest.settings.get('linearization_mode')
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
                for child in node.get_children():
                    add_children(child)

        add_children(self)
        return sorted_constituents

    def get_sorted_leaf_constituents(self):
        sorted_constituents = []
        used = set()

        def add_children(node):
            if node not in used:
                used.add(node)
                children = node.get_children()
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

    def update_cn_shape(self):
        self.label_object.cn_shape = self.forest.settings.get('cn_shape')

    def update_tooltip(self) -> None:
        """ Hovering status tip """
        tt_style = f'<tt style="background:{ctrl.cm.paper2().name()};">%s</tt>'
        ui_style = f'<strong style="color:{ctrl.cm.ui().name()};">%s</tt>'

        lines = [f"<strong>ConstituentNode{' (Trace)' if self.is_trace else ''}</strong>",
                 f'uid: {tt_style % self.uid}',
                 f'label: {escape(str(self.label))}',
                 f'target position: {coords_as_str(self.target_position)}']

        if self.index:
            lines.append(f' Index: {repr(self.index)}')
        if not self.syntactic_object:
            heads = self.get_heads()
            heads_str = ["itself" if h is self
                         else f'{escape(str(h.label))}, {tt_style % h.uid}'
                         for h in heads]
            heads_str = '; '.join(heads_str)
            if len(heads) == 1:
                lines.append(f'head: {heads_str}')
            elif len(heads) > 1:
                lines.append(f'heads: {heads_str}')

        # x, y = self.current_scene_position
        # lines.append(f'pos: ({x:.1f},{y:.1f})')

        if self.use_adjustment:
            lines.append(f' adjustment to position {coords_as_str(self.adjustment)}')

        synobj = self.syntactic_object
        if synobj:
            lines.append('')
            lines.append(f"<strong>Syntactic object: {synobj.__class__.__name__}</strong>")
            lines.append(f'uid: {tt_style % synobj.uid}')
            lines.append(f"label: '{escape(synobj.label)}'")
            lines.append(f"adjunct: {synobj.adjunct}")
            heads = flatten(synobj.get_heads())
            heads_str = [f"itself, {tt_style % h.uid}" if h is synobj
                         else f'{escape(h.label)}, {tt_style % h.uid}'
                         for h in heads]
            heads_str = '; '.join(heads_str)
            if len(heads) == 1:
                lines.append(f'head: {heads_str}')
            elif len(heads) > 1:
                lines.append(f'heads: {heads_str}')

            if hasattr(synobj, 'mover'):
                lines.append(f'mover: {synobj.mover}')
            if hasattr(synobj, 'result_of_em'):
                lines.append(f'result of external merge: {synobj.result_of_em}')
            if synobj.inherited_features:
                lines.append(f'inherited features: {synobj.inherited_features}')
            if synobj.checked_features:
                lines.append(f'checked features: {synobj.checked_features}')
            if synobj.features:
                lines.append(f'features: {synobj.features}')
            if hasattr(synobj, 'sticky'):
                lines.append(f'sticky: {synobj.sticky}')
            lines.append('')
            if getattr(synobj, 'word_edge', None):
                lines.append('--Word edge--')
                lines.append('')
            if self.syntactic_object.parts:  # fixme: for debugging ordering problems
                lines.append(f'Children: {[c.label for c in self.syntactic_object.parts]}')
                #lines.append(f'Child nodes: {[f"{cn.uid}-{cn.label}" for cn in self.get_all_children()]}')
                #lines.append(f'Edge ends: {[f"{e.end.uid}-{e.end.label}" for e in self.edges_down]}')

        if self.selected:
            lines.append(ui_style % 'Click to edit text, drag to move')
        else:
            lines.append(ui_style % 'Click to select, drag to move')
        self.k_tooltip = '<br/>'.join(lines)

    def __str__(self):
        label = as_text(self.label, single_line=True)
        return f'CN {label}'

    def edge_type(self):
        if self.syntactic_object and self.syntactic_object.adjunct:
            return g.ADJUNCT_EDGE
        else:
            return g.CONSTITUENT_EDGE

    def label_as_html(self):
        """ This method builds the html to display in label. For convenience, syntactic objects
        can override this (going against the containment logic) by having their own
        'label_as_html' -method. This is so that it is easier to create custom
        implementations for constituents without requiring custom constituentnodes.

        Note that synobj's label_as_html receives the node object as parameter,
        so you can replicate the behavior below and add your own to it.
        """

        # Allow custom syntactic objects to override this
        if hasattr(self.syntactic_object, 'label_as_html'):
            return self.syntactic_object.label_as_html(self)

        html = []

        label_text_mode = self.label_text_mode
        include_index = True
        l = ''
        if label_text_mode == g.NODE_LABELS:
            l = self.label
        elif label_text_mode == g.NODE_LABELS_FOR_LEAVES:
            if self.is_leaf():
                l = self.label
        elif label_text_mode == g.CHECKED_FEATURES:
            if self.syntactic_object.parts and self.syntactic_object.checked_features:
                fl = []
                for f in self.syntactic_object.checked_features:
                    if isinstance(f, tuple):
                        fl.append(' '.join([str(x) for x in f]))
                    else:
                        fl.append(str(f))
                l = ' '.join(fl)
            else:
                l = self.label
        # fixme: remove this hack after use
        #i = self.get_highest()[0].get_sorted_nodes().index(self)
        #html.append(f'{i} ')
        l_html = as_html(l, omit_triangle=True, include_index=include_index and self.index)
        if l_html:
            html.append(l_html)

        if self.gloss and self.forest.settings.get('lock_glosses_to_label') == 1:
            if html:
                html.append('<br/>')
            html.append(as_html(self.gloss))
        if html and html[-1] == '<br/>':
            html.pop()

        return ''.join(html)

    def label_as_editable_html(self):
        """ This is used to build the html when quickediting a label. It should reduce the label
        into just one field value that is allowed to be edited, in constituentnode this is
        either label or synobj's label. This can be overridden in syntactic object by having
        'label_as_editable_html' -method there. The method returns a tuple,
          (field_name, setter, html).
        :return:
        """
        return None, ''

    def as_bracket_string(self):
        """ returns a simple bracket string representation """
        children = self.get_children()
        if children:
            return '[.%s %s ]' % (
                self.label, ' '.join((c.as_bracket_string() for c in children)))
        else:
            return str(self.label)

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

    def get_cn_shape(self):
        """ Node shapes are based on settings-stack, but also get_shape_setting in label.
        Return this get_shape_setting value.
        :return:
        """
        return self.label_object.cn_shape

    def get_heads(self):
        res = []
        if self.syntactic_object:
            for head in flatten(self.syntactic_object.get_heads()):
                node = self.forest.get_node(head)
                if node:
                    res.append(node)
        return res

    def get_lexical_color(self, refresh=True):
        if self.is_fading_out:
            return ctrl.cm.get('content1')
        if refresh or not self._lexical_color:
            if self.syntactic_object:
                heads = self.get_heads()
                if heads and heads[0] is not self:
                    if heads[0]:
                        self._lexical_color = heads[0].get_lexical_color()
                        return self._lexical_color
                l = ' '.join([str(f) for f in self.syntactic_object.features])
            else:
                l = str(self.label)
            if l:
                hue = hash(l) % 360
            else:
                hue = 1
            self._lexical_color = ctrl.cm.accent_from_hue(hue)
        return self._lexical_color

    def contextual_color(self):
        """ Drawing color that is sensitive to node's state
        :return: QColor
        """
        if self.selected:
            base = ctrl.cm.selection()
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

    @property
    def color(self) -> QtGui.QColor:
        """ Helper property to directly get the inherited/local QColor
        :return:
        """
        if self.use_lexical_color:
            return self.get_lexical_color()
        return ctrl.cm.get(self.get_color_key())

    # ### Features #########################################

    def update_gloss(self):
        gloss_text = self.get_gloss()
        gloss_node = self.gloss_node
        if gloss_node and not gloss_text:
            ctrl.drawing.delete_node(gloss_node)
        elif gloss_text and not gloss_node:
            ctrl.drawing.create_gloss_node(host=self)
        elif gloss_text and gloss_node:
            gloss_node.update_label()

    def gather_children(self, position, shape):
        """ If there are other Nodes that are childItems for this node, arrange them to their 
        proper positions. 
        
        For ConstituentNodes this means collecting the locked-in FeatureNodes and positioning 
        them in three possible ways. 
        :return: 
        """
        children = self.get_children(visible=True, of_type=g.FEATURE_NODE)
        if not (children or self.gloss_node):
            return
        bottom_y = self.boundingRect().bottom()
        y = bottom_y
        if shape == g.CARD:
            position = g.TWO_COLUMNS  # only two column arrangement looks good on cards

        if position == g.VERTICAL_COLUMN:
            center_x = self.boundingRect().center().x()
            for fnode in children:
                if fnode.locked_to_node is self:
                    fbr = fnode.future_children_bounding_rect()
                    fnode.move_to(center_x, y - fbr.y())
                    y += fbr.height() + 2
        elif position == g.HORIZONTAL_ROW:  # horizontal
            nods = []
            total_width = 0
            max_height = 0
            for fnode in children:
                if fnode.locked_to_node is self:
                    fbr = fnode.future_children_bounding_rect()
                    nods.append((fnode, total_width - fbr.x()))
                    total_width += fbr.width()  # + 4
                    if fnode.height > max_height:
                        max_height = fbr.height()
            if nods:
                left_margin = (total_width / -2)
                y = bottom_y + (max_height / 2)
                for fnode, x in nods:
                    fnode.move_to(left_margin + x, y)
            y = bottom_y + max_height + 2
        elif position == g.TWO_COLUMNS:  # card layout, two columns
            self._can_cascade_edges = False
            in_card = self.forest.settings.get('cn_shape') == g.CARD
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
                yr = top_y
                for fnode in right_nods:
                    fbr = fnode.future_children_bounding_rect()
                    fnode.move_to(right_margin - fbr.width() / 2, yr)
                    yr += fbr.height() + 2
                y = max(y, yr)
        if self.gloss_node:
            self.gloss_node.lock_to_node(self, (0, y + self.gloss_node.height / 2 + 2))
            # self.gloss_node.move_to(0, y)

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
            getnode = self.forest.get_node
            return [getnode(f) for f in self.syntactic_object.get_features()]
        else:
            return self.get_children(visible=True, of_type=g.FEATURE_NODE)

    def get_features_as_string(self):
        """
        :return:
        """
        if self.syntactic_object:
            feature_strings = [str(f) for f in self.syntactic_object.features]
            return ', '.join(feature_strings)
        return ''

    def get_merged_features(self):
        if self.syntactic_object:
            checked_feats = getattr(self.syntactic_object, 'checked_features', [])
            nodes = []
            if checked_feats:
                for f in checked_feats:
                    if isinstance(f, tuple):
                        for ff in f:
                            n = self.forest.get_node(ff)
                            if n:
                                nodes.append(n)
                    else:
                        n = self.forest.get_node(f)
                        if n:
                            nodes.append(n)
            return nodes

    def has_merged_features(self):
        return self.syntactic_object and getattr(self.syntactic_object, 'checked_features', [])

    def first_feature(self):
        if self.syntactic_object and self.syntactic_object.features:
            return self.forest.get_node(self.syntactic_object.features[0])

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
            if child not in nodes_above and not child.parentItem():
                child.prepare_dragging_participant(host=False, scene_pos=scene_pos)

    #################################

    # ### Paint overrides

    def _calculate_inner_rect(self, min_w=0, min_h=0):
        if self.label_object.cn_shape == g.BRACKETED or self.label_object.cn_shape == g.SCOPEBOX:
            min_w = self.forest.width_map.get(self.uid, 0)
        return super()._calculate_inner_rect(min_w=min_w)

    def paint(self, painter, option, widget=None):
        """ Painting is sensitive to mouse/selection issues, but usually with nodes it is
        the label of the node that needs complex painting.
        :param painter:
        :param option:
        :param widget:
         """
        shape = self.label_object.cn_shape
        if shape == g.CARD:
            xr = 4
            yr = 8
        else:
            xr = 5
            yr = 5
        pen = QtGui.QPen(self.contextual_color())
        pen.setWidth(1)
        rect = False
        brush = QtCore.Qt.BrushStyle.NoBrush

        if shape == g.SCOPEBOX or (shape == g.BOX and not self.is_empty()):
            pen.setWidthF(0.5)
            brush = ctrl.cm.paper2()
            rect = True
        elif self.label_object.is_card():
            brush = ctrl.cm.paper2()
            rect = True
        if self.drag_data:
            rect = True
            brush = self.drag_data.background
        elif self.hovering:
            if rect:
                brush = ctrl.cm.paper()
            rect = True
        elif ctrl.pressed is self or self.selected:
            if rect:
                brush = ctrl.cm.paper()
            if not hasattr(self, 'halo'):
                rect = True

        # elif self.has_empty_label() and self.node_alone():
        #    pen.setStyle(QtCore.Qt.DotLine)
        #    rect = True
        painter.setPen(pen)
        if rect:
            painter.setBrush(brush)
            painter.drawRoundedRect(self.inner_rect, xr, yr)
        if shape == g.BRACKETED and not self.is_leaf(visible=True):
            painter.setFont(self.get_font())
            painter.drawText(self.inner_rect.right() - qt_prefs.font_bracket_width - 2, 2, ']')

        self.use_lexical_color = False
        if shape == g.FEATURE_SHAPE:
            feats = self.get_merged_features()
            self.use_lexical_color = True
            if not feats:
                self.invert_colors = False
            else:
                self.invert_colors = True
                x = self.inner_rect.left()
                y = self.inner_rect.top()
                h = self.inner_rect.height()
                for feat in feats:
                    left = feat.fshape if feat.is_valuing() else 0
                    right = feat.fshape if feat.is_needy() or feat.is_satisfied() else 0
                    color = feat.get_host_color()
                    w = feat.compute_piece_width(self.label_object.string_width, left, right)
                    if left:
                        x -= 4
                    feat.draw_feature_shape(painter, QtCore.QRectF(x, y, w, h), left, right, color)
                    painter.setPen(ctrl.cm.get('background1'))
                    x += w - 4
        elif self.has_visible_label():
            old_pen = painter.pen()
            painter.setPen(QtCore.Qt.PenStyle.NoPen)
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
                gradient.setColorAt(1, QtCore.Qt.GlobalColor.transparent)
                painter.setBrush(gradient)
            painter.drawEllipse(r)
            painter.setPen(old_pen)
        if self.is_edge():
            r = self.inner_rect
            p = QtGui.QPen(ctrl.cm.drawing())
            p.setWidth(3)
            painter.setPen(p)
            painter.drawLine(r.topLeft().toPoint(), r.topRight().toPoint())

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    index = SavedField("index")
    gloss = SavedField("gloss")
