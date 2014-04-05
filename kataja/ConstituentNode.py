#############################################################################
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
#############################################################################

from PyQt5 import QtCore, QtGui, QtWidgets

from kataja.Controller import ctrl, prefs, qt_prefs
from kataja.FeatureNode import FeatureNode
from kataja.Node import Node
from kataja.ui.RadialMenu import RadialMenu
from kataja.utils import to_unicode, to_tuple, time_me
from kataja.globals import CONSTITUENT_EDGE, FEATURE_EDGE, ALL_LABELS, ALIASES, ATTRIBUTE_EDGE, CONSTITUENT_NODE


# ctrl = Controller object, gives accessa to other modules

def restore_me(key, forest):
    if key in forest.nodes:
        obj = forest.nodes[key]
    else:
        obj = ConstituentNode(restoring=key)
        obj._revived = True
        if not ctrl.loading:
            forest.add_to_scene(obj)
    # if not ctrl.loading:
    forest.undo_manager.repair_later(obj)
    return obj


class ConstituentNode(Node):
    """ ConstituentNodes are graphical representations of constituents. They are primary objects and need to support saving and loading."""
    width = 20
    height = 20
    default_edge_type = CONSTITUENT_EDGE
    saved_fields = ['has_visible_brackets', 'alias', 'is_trace', 'triangle', 'merge_order', 'select_order']
    saved_fields = list(set(Node.saved_fields + saved_fields))
    node_type = CONSTITUENT_NODE



    # ConstituentNode position points to the _center_ of the node.
    # boundingRect should be (w/-2, h/-2, w, h)

    def __init__(self, constituent=None, forest=None, restoring=''):
        """ Most of the initiation is inherited from Node """
        Node.__init__(self, forest=forest, syntactic_object=constituent, restoring=restoring)
        self.save_key = 'CN%s' % self.syntactic_object.uid
        self.level = 3
        # ------ Bracket drawing -------
        self.has_visible_brackets = False
        self.left_bracket = None
        self.right_bracket = None
        ####
        self.alias = ""
        self.is_trace = False
        self.triangle = False
        self.selectable = True
        self.label_font = qt_prefs.font  # @UndefinedVariable

        #### Projection -- see also preferences that govern if these are used
        self.can_project = True
        self.projecting_to = set()


        #### Cycle index stores the order when node was originally merged to structure.
        # going up in tree, cycle index should go up too
        self.merge_order = 0
        self.select_order = 0

        # ## use update_visibility to change these: visibility of particular elements
        # depends on many factors
        if forest:
            self._visibility_folded = False
            self._visibility_active = True
            self._visibility_label = forest.settings.label_style()
            self._visibility_index = not forest.settings.uses_multidomination()
            self._visibility_edges = forest.settings.shows_constituent_edges()
            self._visibility_features = forest.settings.draw_features()
            self._visibility_brackets = forest.settings.bracket_style()
        else:
            self._visibility_folded = False
            self._visibility_active = True
            self._visibility_label = 0
            self._visibility_index = False
            self._visibility_edges = True
            self._visibility_features = 1
            self._visibility_brackets = 0

        # these are dangerous to call with empty Node. Let __setstate__ restore values
        # before calling these.
        if not restoring:
            self.update_features()
            self.update_gloss()
            self.update_identity()
            self.boundingRect(update=True)
            self.update_visibility()

        self._revived = False
        # ## Crude qt-menus for prototyping
        # self.qt_menu = None

    def boundingRect(self, update=False):
        """ In addition to Node boundingRect, we need to take account the scope boxes """
        if update and self.triangle:
            lbr = self._label_complex.boundingRect()
            lbh = lbr.height()
            lbw = lbr.width()
            self.label_rect = QtCore.QRectF(self._label_complex.x(), self._label_complex.y(), lbw, lbh)
            self.width = max((lbw, self.__class__.width))
            self.height = max((lbh * 1.5, self.__class__.height))
            return Node.boundingRect(self, update, pass_size_calculation=True)
        else:
            return Node.boundingRect(self, update)

    def __str__(self):
        alias = self.alias.encode('utf-8')
        label = self.syntactic_object.label.encode('utf-8')
        if alias and label:
            return ' '.join((alias, label))
        else:
            return alias or label

    def __unicode__(self):
        alias = self.alias
        label = to_unicode(self.syntactic_object.label)
        if alias and label:
            return ' '.join((alias, label))
        else:
            return alias or label

    def as_bracket_string(self):
        """ returns a simple bracket string representation """
        children = self.get_children()
        if children:
            if self.alias:
                return u'[.%s %s %s ]' % (self.alias, children[0].as_bracket_string(), children[1].as_bracket_string())
            elif len(children) == 2:
                return u'[ %s %s ]' % (children[0].as_bracket_string(), children[1].as_bracket_string())
            else:
                return u'[ %s ]' % children[0].as_bracket_string()
        else:
            return to_unicode(self.alias or self.syntactic_object)


    def info_dump(self):
        print '---- %s ----' % self.save_key
        print '| scene: %s' % self.scene()
        print '| isVisible: %s' % self.isVisible()
        print '| print: %s ' % self
        print '| x: %s y: %s z: %s' % self.get_current_position()
        print '| adjustment: x: %s y: %s z: %s ' % self.get_adjustment()
        print '| computed x: %s y: %s z: %s' % self.get_computed_position()
        print '| final: x: %s y: %s z: %s ' % self.get_final_position()
        print '| bind x: %s y: %s z: %s' % (self.bind_x, self.bind_y, self.bind_z)
        print '| locked_to_position: %s ' % self.locked_to_position
        print '| label rect: ', self.label_rect
        print '| index: %s' % self.index
        print '| edges up:', self.edges_up
        print '| edges down:', self.edges_down
        print '| syntactic_object:_________________'
        print self.syntactic_object.__repr__()
        print '----------------------------------'


    def get_attribute_nodes(self, label_key=''):
        atts = [x.end for x in self.edges_down if x.edge_type == ATTRIBUTE_EDGE]
        if label_key:
            for a in atts:
                if a.attribute_label == label_key:
                    return a
        else:
            return atts

    def update_visibility(self, **kw):
        if 'folded' in kw:
            self._visibility_folded = kw['folded']
        if 'active' in kw:
            self._visibility_active = kw['active']
        if 'label' in kw:
            self._visibility_label = kw['label']
            self.update_label()
        if 'show_index' in kw:
            self._visibility_index = kw['show_index']
        if 'show_edges' in kw:
            self._visibility_edges = kw['show_edges']
        if 'features' in kw:
            self._visibility_features = kw['features']
        if 'brackets' in kw:
            self._visibility_brackets = kw['brackets']
        if 'fade' in kw:
            fade = kw['fade']
        else:
            fade = False
        visible = self._visibility_active and not self._visibility_folded
        if fade:
            if visible:
                self.fade_in()
            else:
                self.fade_out()
        else:
            self.setVisible(visible)
        label_visible = self._visibility_label == ALL_LABELS
        label_visible = label_visible or (self._visibility_label == ALIASES and self.alias)
        label_visible = bool(label_visible or self.triangle or (self.has_label() and self.is_leaf_node()))
        self._label_visible = label_visible
        if not self._label_complex:
            self.update_label()
        if label_visible and not self._label_complex.isVisible():
            self.update_label()
        self._label_complex.setVisible(label_visible)
        if self._index_label:
            self._index_label.setVisible(self._visibility_index)
        for edge in self.edges_down:
            if edge.edge_type == self.__class__.default_edge_type:
                edge.set_visible(visible and self._visibility_edges)
            else:
                edge.set_visible(visible)
        for feature in self.get_features():
            feature.setVisible(visible and self._visibility_features)
        if self._visibility_brackets:
            if self._visibility_brackets == 2:
                self.has_visible_brackets = not self.is_leaf_node()
            elif self._visibility_brackets == 1:
                is_left = False
                for edge in self.get_edges_up():
                    if edge.align == 1:  # LEFT
                        is_left = True
                        break
                self.has_visible_brackets = is_left
        else:
            self.has_visible_brackets = False
        if self.left_bracket:
            self.left_bracket.setVisible(self.has_visible_brackets)
        if self.right_bracket:
            self.right_bracket.setVisible(self.has_visible_brackets)

    def reset(self):
        Node.reset(self)
        # self.uses_scope_area = False
        # self.has_visible_brackets = False
        # self.boundingRect(update = True)


    #### Parents & Children ####################################################

    def is_projecting_to(self, other):
        pass

    def rebuild_brackets(self):
        if self.left():
            if not self.left_bracket:
                self.left_bracket = self.forest.create_bracket(host=self, left=True)
        else:
            self.left_bracket = None
        if self.right():
            if not self.right_bracket:
                self.right_bracket = self.forest.create_bracket(host=self, left=False)
        else:
            self.right_bracket = None

    #### Features #########################################

    def set_feature(self, syntactic_feature=None, key=None, value=None, string=''):
        """ Convenience method for assigning a new feature node related to this constituent.
        can take syntactic feature, which is assumed to be already assigned for the syntactic constituent.
            Can take key, value pair to create new syntactic feature object, and then a proper feature object is created from this.
        """
        if syntactic_feature:
            if self.forest.settings.draw_features():
                self.forest.create_feature_node(self, syntactic_feature)
        elif key:
            sf = self.syntactic_object.set_feature(key, value)
            self.set_feature(syntactic_feature=sf)
        elif string:
            features = self.forest.parse_features(string, self)
            if 'gloss' in features:
                self.set_gloss_text(features['gloss'])
                del features['gloss']
            for feature in features.values():
                self.set_feature(syntactic_feature=feature)
            self.update_features()


    def set_gloss_text(self, gloss):
        self.syntactic_object.set_gloss(gloss)
        self.update_gloss()

    def get_gloss(self):
        gl = self.get_children(edge_type='gloss_edge')
        if gl:
            return gl[0]


    def update_gloss(self):
        syn_gloss = self.syntactic_object.get_gloss()
        gloss_node = self.get_gloss()
        if gloss_node and not syn_gloss:
            self.forest.delete_node(gloss_node)
        elif syn_gloss and not gloss_node:
            self.forest.create_gloss_node(self)
        elif syn_gloss and gloss_node:
            gloss_node.update_label()


    def get_features(self):
        """ Returns FeatureNodes """
        return self.get_children(edge_type=FEATURE_EDGE)

    def update_features(self):
        current_features = set([x.syntactic_object.get() for x in self.get_features()])
        correct_features = self.syntactic_object.get_features()
        for key, item in correct_features.items():
            if key not in current_features:
                self.set_feature(syntactic_feature=item, key=key)
            else:
                current_features.remove(key)
        if current_features:
            print 'leftover features:', current_features


    #### Labels #############################################


    # things to do with traces:
    # if renamed and index is removed/changed, update chains
    # if moved, update chains
    # if copied, make sure that copy isn't in chain
    # if deleted, update chains
    # any other operations?

    def is_empty_node(self):
        """ Empty nodes can be used as placeholders and deleted or replaced without structural worries """
        return (not (self.alias or self.get_editable_label() or self.get_index())) and self.is_leaf_node()

    def get_text_for_label(self):
        """ Build html string to be displayed in label_complex """
        alias = self.alias
        label = to_unicode(self.syntactic_object.label)

        index = self.get_index()
        if index:
            i_string = '<sub><i>%s</i></sub>' % index
        else:
            i_string = ''
        if self.forest.settings.label_style() != 0:
            if alias and label:
                padding = len(label) - len(alias)
                if padding > 0:
                    padding = padding / 2
                    s = '%s<b>%s</b>%s<br/>%s' % (padding * "&nbsp;", alias, i_string, label)
                elif padding < 0:
                    padding = padding / -2
                    s = '<b>%s</b>%s<br/>%s%s' % (alias, i_string, padding * "&nbsp;", label)
                else:
                    s = '<b>%s</b>%s<br/>%s' % (alias, i_string, label)
            elif alias:
                s = '<b>%s</b>%s' % (alias, i_string)
            else:
                s = label + i_string
        else:
            s = label + i_string
        if not prefs.hanging_gloss:
            gloss = self.get_gloss_text()
            if gloss:
                s += '<br/><i>%s</i>' % gloss
        if s:
            return s
            # return '<center>%s</center>' % s
        else:
            return ''

    def get_editable_label(self):
        """ """
        return unicode(self.syntactic_object.label)

    def has_label(self):
        return self.syntactic_object.label

    def get_features_as_string(self):
        features = [f.syntactic_object for f in self.get_features()]
        feature_strings = [unicode(f) for f in features]
        return u', '.join(feature_strings)

    def get_alias(self):
        return self.alias

    def set_alias(self, alias):
        self.alias = alias
        self.update_identity()

    def get_gloss_text(self):
        return self.syntactic_object.get_gloss()

    ### Indexes and chains ###################################

    def get_index(self):
        return self.syntactic_object.get_index()

    def set_index(self, i):
        self.syntactic_object.set_index(i)
        self.update_identity()

    def remove_index(self):
        self.syntactic_object.set_index('')
        self.update_identity()

    def is_chain_head(self):
        if self.get_index():
            return not (self.is_leaf_node() and self.syntactic_object.get_label() == 't')
        return False

    #### Folding / Triangles #################################

    def is_folded_away(self):
        if self.folding_towards:
            return True
        else:
            return False

    def fold(self):
        """ Form a triangle """
        self.folding_towards = self
        self.triangle = True
        self._label_complex.fold_label()
        self.update_visibility()

        folded = set()
        questionable = set()
        for node in self.forest.list_nodes(
                self):  # don't fold multidominated nodes unless all of their parents are in fold
            can_be_folded = True
            for parent in node.parents():
                if not parent.folding_towards:
                    can_be_folded = False
                    questionable.add(node)
            if can_be_folded:
                folded.add(node)
                node.prepare_to_be_folded(self)
        # criss-crossing parenthood edges make it difficult to recognize which elements are fully
        # dominated by another node.
        # for questionable elements, iterate through set until iteration round doesn't change it anymore
        prev_size = len(questionable) + 1
        while prev_size > len(questionable):
            prev_size = len(questionable)
            for item in list(questionable):
                keep = True
                for node in item.parents:
                    if node not in folded:
                        keep = False
                if keep:
                    folded.add(item)
                    questionable.remove(item)
                    item.prepare_to_be_folded(self)
        self.finish_folding()

    def unfold_triangle(self):
        """ Restore elements from a triangle """
        self.triangle = False
        self._label_complex.unfold_label()
        for n, node in enumerate(self.forest.list_nodes(self)):
            node.unfold(self, n)

    def prepare_to_be_folded(self, triangle):
        """ Initialize move to triangle's position and make sure that move is not
        interrupted  """
        # print u'node %s preparing to collapse to %s at %s' % (self, triangle, triangle.target_position )
        self.folding_towards = triangle  # folding_towards should override other kinds of movements
        self.after_move_function = self.finish_folding
        tx, ty, tz = triangle.get_computed_position()
        self.set_adjustment(triangle.get_adjustment())
        self.set_computed_position((tx, ty + 30, tz))  # , fast = True)
        for feature in self.features:
            feature.fade_out()

    def finish_folding(self):
        """ Hide, and remember why this is hidden """
        self.folded_away = True
        self.update_visibility(folded=True, show_edges=False)
        self.boundingRect(update=True)

    def unfold(self, from_node, n=0):
        """ Restore folded elements, add some variance (n) to node positions so visualization algorithms won't get stuck """
        self.folded_away = False
        self.folding_towards = None
        x, y, z = from_node.get_computed_position()
        self.set_adjustment(from_node.get_adjustment())
        self.set_computed_position((x + n, y + n, z))
        self.update_visibility()
        for edge in self.edges_down:
            edge.update_visibility()
        self.boundingRect(update=True)
        for feature in self.features:
            feature.fade_in()

    def paint_triangle(self, painter, draw_rect):
        """ Drawing the triangle, called from paint-method """
        br = self.label_rect
        w2 = br.width() / 2
        left = br.x()
        center = left + w2
        right = center + w2
        bottom = br.y()
        top = br.y() - br.height() / 2

        triangle = QtGui.QPainterPath()
        triangle.moveTo(center, top)
        triangle.lineTo(right, bottom)
        triangle.lineTo(left, bottom)
        triangle.lineTo(center, top)
        painter.drawPath(triangle)
        if draw_rect:
            painter.drawRoundedRect(self.label_rect, 5, 5)


    ### Multidomination #############################################


    def is_multidominated(self):
        """ Check if the ConstituentNode has more than one parent. """
        return len(self.get_parents()) > 1

    def get_c_commanded(self):
        """ Returns the closest c-commanded elements of this element. All dominated by those are also c-commanded """
        result = []
        for parent in self.get_parents():
            for child in parent.get_children():
                if child is not self:
                    result.append(child)
        return result

    # ## Magnets

    def top_magnet(self):
        if self.triangle:
            x1, y1, z1 = self.get_current_position()
            y2 = self.label_rect.y() - self.label_rect.height() / 2
            return (x1, y1 + y2, z1)
        else:
            return Node.top_magnet(self)

    def bottom_magnet(self):
        if self.triangle:
            x1, y1, z1 = self.get_current_position()
            y2 = self.label_rect.y() + self.label_rect.height() / 2
            return (x1, y1 + y2, z1)
        else:
            return Node.bottom_magnet(self)


    def left_magnet(self):
        if self.triangle:
            x1, y1, z1 = self.get_current_position()
            x2 = self.label_rect.x()
            return (x1 + x2, y1, z1)
        else:
            return Node.left_magnet(self)

    def right_magnet(self):
        if self.triangle:
            x1, y1, z1 = self.get_current_position()
            x2 = self.label_rect.x() + self.label_rect.width()
            return (x1 + x2, y1, z1)
        else:
            return Node.right_magnet(self)

    ### Scope brackets and scope rectangles #############################################

    # not used
    # def paint_scope_rect(self, painter, draw_rect):
    #     if draw_rect or True:
    #         painter.drawRoundedRect(self.scope_rect, 5, 5)
    #         painter.drawRect(self.label_rect)
    #     if self.has_visible_brackets:
    #         painter.setFont(prefs.font)
    #         painter.drawText(self.scope_rect.left(), self.scope_rect.top() + ((self.scope_rect.height() + (prefs.font_bracket_height / 2)) / 2), '[')
    #         painter.drawText(self.scope_rect.right() - prefs.font_bracket_width, self.scope_rect.top() + ((self.scope_rect.height() + (prefs.font_bracket_height / 2)) / 2), ']')


    ### Qt overrides ######################################################################

    def paint(self, painter, option, widget):
        painter.setPen(self.get_contextual_color())
        if ctrl.pressed == self:
            rect = True
        elif self._hovering:
            rect = True
        elif ctrl.is_selected(self):
            rect = True
        elif self.has_visible_brackets:
            rect = False
        else:
            rect = False
        if self.triangle:
            self.paint_triangle(painter, rect)
        elif rect:
            painter.drawRect(self.inner_rect)
            # elif self.uses_scope_area:
            #    self.paint_scope_rect(painter, rect)

    def itemChange(self, change, value):
        """ Whatever menus or UI objects are associated with object, they move
        when node moves """
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            if self.ui_menu and self.ui_menu.isVisible():
                self.ui_menu.update_position(drag=True)
            if self._hovering or ctrl.focus == self:
                pass
                # print 'ctrl.ui problem here!'
                # assert(False)
                # if self.forest.main.ui.is_target_reticle_over(self):
                # if ctrl.ui.is_target_reticle_over(self):
                #    ctrl.ui.update_target_reticle_position()
        return QtWidgets.QGraphicsItem.itemChange(self, change, value)

    ########### SAVING AND LOADING #######################################################

    #### Qt menus ###################################################

    def open_qt_menu(self):
        if not self.qt_menu:
            self.create_qt_menu()
        else:
            self.qt_menu.focus()

    def create_qt_menu(self, scene):
        def label_edited(self):
            return

        widget = QtWidgets.QDialog(self.forest.main)  # QGroupBox
        layout = QtWidgets.QFormLayout(widget)
        widget.setLayout(layout)
        widget.show()
        label_editor = QtWidgets.QTextEdit('editable label', parent=widget)
        label_editor.setFixedSize(200, 20)
        label_editor.setTabChangesFocus(True)
        label_editor.editingFinished = label_edited
        if not self.label_document:
            self.label_document = QtGui.QTextDocument(self.get_label())
        label_editor.setDocument(self.label_document)
        layout.addRow('&Label:', label_editor)
        index_editor = QtWidgets.QLineEdit(self.get_index(), parent=widget)
        index_editor.editingFinished = label_edited
        index_editor.textChanged = label_edited
        layout.addRow('&Index:', index_editor)
        gloss_editor = QtWidgets.QLineEdit(self.get_gloss_text(), parent=widget)
        layout.addRow('&Gloss:', gloss_editor)
        self.qt_menu = widget

    def close_qt_menu(self):
        self.qt_menu.hide()
        self.qt_menu = None

    #### Selection ########################################################

    def set_selection_status(self, selected):
        if (not selected) and self.ui_menu and self.ui_menu.is_open():
            self.close_menus()
        self.update()

    #### Radial menu #########################################################

    def create_menu(self):
        main = self.forest.main
        menu = main.ui_manager.create_menu(self, actions=[
            {'name': 'Root Merge', 'method': main.do_merge, 'local_shortcut': 'r', 'condition': 'can_root_merge',
             'menu_type': 'Button'},
            {'name': 'Delete', 'method': main.do_delete_node, 'local_shortcut': 'd', 'menu_type': 'Button'},
            {'name': 'Fold', 'method': main.toggle_fold_node, 'checkable': True, 'local_shortcut': 'f',
             'condition': 'canFold', 'menu_type': 'Button'},
            {'name': 'Disconnect', 'method': main.disconnect_node, 'local_shortcut': 'x', 'menu_type': 'Button'},
            {'name': 'Copy', 'method': main.copy_selected, 'local_shortcut': 'c', 'menu_type': 'Button'},
            {'name': 'Label', 'method': self.change_label, 'menu_type': 'TextArea', 'pos': (-10, 0),
             'get_method': self.get_editable_label, 'font': qt_prefs.big_font,  # @UndefinedVariable
             'tab_index': 0},
            {'name': 'Alias', 'method': self.change_alias, 'menu_type': 'TextArea', 'pos': ('top', 'Label'),
             'get_method': self.get_alias, 'tab_index': 1},
            {'name': 'Index', 'method': self.change_index, 'menu_type': 'TextArea', 'pos': ('bottom-right', 'Label'),
             'get_method': self.get_index, 'tab_index': 2},
            {'name': 'Features', 'method': self.change_features_string, 'menu_type': 'TextArea',
             'pos': ('bottom', 'Label'), 'get_method': self.get_features_as_string, 'tab_index': 4},
            {'name': 'Gloss', 'method': self.change_gloss_text, 'menu_type': 'TextArea', 'pos': ('bottom', 'Features'),
             'get_method': self.get_gloss_text, 'tab_index': 3}, ])
        return menu

    def open_menus(self):
        """ Activates menus """
        # only one menu is open at time
        ui = self.forest.main.ui_manager
        ui.close_menus()
        # create menus only when necessary
        if not self.ui_menu:
            self.ui_menu = self.create_menu()
        # it takes a while to open the menu, ignore open-commands if it is still opening
        if not self.ui_menu.moving():
            if self.is_leaf_node():
                focus = 'Label'
            else:
                focus = 'Alias'
            self.ui_menu.open(focus=focus)

    #### Menu commands and related behaviour #############################################

    def change_label(self, caller=None, event=None):
        label = caller.get_value()
        self.syntactic_object.label = label
        self.update_label()
        # # Delete node if just created and saved as empty.
        if self in ctrl.on_cancel_delete:
            if not label:
                for item in ctrl.on_cancel_delete:
                    self.forest.delete_item(item)
        ctrl.on_cancel_delete = []
        self.forest.main.action_finished('edit node text')

    def change_index(self, caller=None, event=None):
        index = caller.get_value()
        self.set_index(index)
        self.forest.main.action_finished('edit node index')

    def change_gloss_text(self, caller=None, event=None):
        gloss = caller.get_value()
        self.set_gloss_text(gloss)
        self.forest.main.action_finished('edit node gloss text')

    def change_alias(self, caller=None, event=None):
        alias = caller.get_value()
        self.set_alias(to_unicode(alias))
        self.forest.main.action_finished('edit node label')

    def change_features_string(self, caller=None, event=None):
        featurestring = caller.get_value()
        self.set_feature(string=featurestring)
        self.forest.main.action_finished('edit node feature text')

    #### Checks for callable actions ####

    def can_root_merge(self):
        root = self.get_root_node()
        return self is not root and self is not root.left(only_visible=False)

    def can_fold(self):
        return not self.triangle

    def can_unfold(self):
        return self.triangle

    #### Dragging #####################################################################

    # ## Some of this needs to be implemented further down in constituentnode-node-movable -inheritance

    def start_dragging(self, mx, my):
        if ctrl.is_selected(self):
            drag_hosts = ctrl.get_all_selected()
        else:
            drag_hosts = [self]
        ctrl.dragged = set()

        # there if node is both above and below the dragged node, it shouldn't move
        for drag_host in drag_hosts:
            root = drag_host.get_root_node()
            nodes = self.forest.list_nodes(root)
            drag_host_index = nodes.index(drag_host)
            dx, dy, dummy_z = drag_host.get_current_position()
            for node in self.forest.list_nodes_once(drag_host):
                if nodes.index(node) >= drag_host_index:
                    ctrl.dragged.add(node)
                    x, y, dummy_z = node.get_current_position()
                    node._position_before_dragging = node.get_current_position()
                    node._adjustment_before_dragging = node.get_adjustment()
                    node._distance_from_dragged = (x - dx, y - dy)
        if len(drag_hosts) == 1:  # don't allow merge if this is multidrag-situation
            self.forest.prepare_touch_areas_for_dragging(excluded=ctrl.dragged)

    def drag(self, event):
        """ Drags also elements that are counted to be involved: features, children etc """
        pos = event.scenePos()
        now_x, now_y = to_tuple(pos)
        if not getattr(ctrl, 'dragged', None):
            self.start_dragging(now_x, now_y)

        # change dragged positions to be based on adjustment instead of distance to main dragged.
        for node in ctrl.dragged:
            dx, dy = node._distance_from_dragged
            px, py, pz = node._position_before_dragging
            if node.can_adjust_position:
                ax, ay, az = node._adjustment_before_dragging
                diff_x = now_x + dx - px - ax
                diff_y = now_y + dy - py - ay
                node.set_adjustment((diff_x, diff_y, az))
            else:
                node.set_computed_position((now_x + dx, now_y + dy, pz))
            # try:
            #    assert (int(px - ax) == int(node._computed_position[0])) # position without adjustment
            # except AssertionError:
            #    print 'Assertion error:'
            #    print px - ax, py - ay, node._computed_position
            node.set_current_position((now_x + dx, now_y + dy, pz))

    def drop_to(self, x, y, received=False):
        self.release()
        self.update()
        if not received:
            for node in ctrl.dragged:
                node.lock()
                ctrl.main.ui_manager.show_anchor(node)  # @UndefinedVariable
        del self._position_before_dragging
        del self._adjustment_before_dragging
        del self._distance_from_dragged
        ctrl.dragged = set()
        ctrl.dragged_positions = set()
        self.forest.main.action_finished('moved node %s' % self)
        # ctrl.scene.fit_to_window()

    def cancel_dragging(self):
        assert (False)
        sx, sy = self._before_drag_position
        z = self.get_current_position()[2]
        self.set_computed_position((sx, sy, z))
        for node, x, y in ctrl.dragged_positions:
            z = node.get_current_position()[2]
            node.set_computed_position((sx + x, sy + y, z))
        del self.before_drag_position
        ctrl.dragged = set()
        ctrl.dragged_positions = set()

    #################################

    def hoverEnterEvent(self, event):
        """ Hovering has some visual effects, usually handled in paint-method """
        if not self._hovering:
            self._hovering = True
            self.prepareGeometryChange()
            if self.left_bracket:
                self.left_bracket._hovering = True
                self.left_bracket.update()
            if self.right_bracket:
                self.right_bracket._hovering = True
                self.right_bracket.update()
            self.update()
        QtWidgets.QGraphicsItem.hoverEnterEvent(self, event)

    def hoverLeaveEvent(self, event):
        """ Object needs to be updated """
        if self._hovering:
            self._hovering = False
            self.prepareGeometryChange()
            if self.left_bracket:
                self.left_bracket._hovering = False
                self.left_bracket.update()
            if self.right_bracket:
                self.right_bracket._hovering = False
                self.right_bracket.update()
            self.update()
        QtWidgets.QGraphicsItem.hoverLeaveEvent(self, event)

    def after_restore(self, changes):
        """ Check what needs to be done """
        self.update_visibility()
        Node.after_restore(self, changes)
        

