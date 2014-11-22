# -*- coding: UTF-8 -*-

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


import re
from kataja.debug import parser
from kataja.singletons import ctrl
from kataja.Presentation import TextArea, Image
from kataja.utils import next_free_index


latex_symbols_to_unicode = {'bar': '\u00AF', 'abar': '\u0100',  # small greek alphabet
                            'alpha': '\u03b1', 'beta': '\u03b2', 'gamma': '\u03b3', 'delta': '\u03b4',
                            'epsilon': '\u03b5', 'zeta': '\u03b6', 'eta': '\u03b7', 'theta': '\u03b8', 'iota': '\u03b9',
                            'kappa': '\u03ba', 'lambda': '\u03bb', 'mu': '\u03bc', 'nu': '\u03bd', 'xi': '\u03be',
                            'omicron': '\u03bf', 'pi': '\u03c0', 'rho': '\u03c1', 'varsigma': '\u03c2',
                            'sigma': '\u03c3', 'tau': '\u03c4', 'upsilon': '\u03c5', 'phi': '\u03c6', 'chi': '\u03c7',
                            'psi': '\u03c8', 'omega': '\u03c9', 'leftarrow': '\u2190', 'rightarrow': '\u2192',
                            'righthookarrow': '\u21aa'}

latex_scopes_to_tags = {'sup': 'sup', 'emph': 'i', 'textbf': 'b'}
# 'index':'sub'}

feature_markers = ('+', '-', '=', '>')
feature_names = ('index', 'dotlabel')
cosmetic_features = ('emph', 'textsc', 'overrightarrow', 'sup')
cases = ['NOM', 'ACC', 'PRT', 'GEN', 'DAT', 'ILL']

# # this doesn't work now because of preferences rearrangement
# def get_color_for_feature(feature_name):
# if feature_name in cases:
# return colors[cases.index(feature_name)]
# else:
# return colors[-1]


class Parser:
    """ Methods to translate strings to trees or other objects. Base class Parser has general methods, subclasses have specific parsers. Parsers are created on fly and they generally shouldn't hold anything that needs long term storing or saving. (If they do, e.g. lexicons those should be moved to a more suitable place.) """
    saved_fields = ['save_key', 'local_lexicon', '_definitions', '_gloss', 'forest']


    def __init__(self, forest):
        """ Parsers have own lexicons to allow referencing to parsed objects """
        self.save_key = forest.save_key + '_parser'
        self.local_lexicon = {}
        # ## Layered parsing uses these:
        self._definitions = {}
        self._gloss = ''
        self.forest = forest


    def detect_suitable_parser(self, text):
        """ There are several parser methods that can be used to create different kinds of objects
        :param text:
        """
        if text.startswith("'"):
            return self.text_area_parser
        elif text.startswith('%'):
            return self.image_parser
        elif text.startswith('['):
            return self.parse
        elif text.startswith('<<'):
            return self.advanced_reverse_tree_parser
        elif text.startswith('<'):
            return self.reverse_tree_parser
        elif text.startswith('>>'):
            return self.bottom_up_parser
        else:
            return self.parse

    # ## General methods

    def add_definition(self, word, definition):
        """

        :param word:
        :param definition:
        """
        self._definitions[word] = definition  # self.parse_definition(definition)
        # we don't want to create the features yet, separate words would get the same instance of feature then.

    def add_gloss(self, gloss):
        """

        :param gloss:
        """
        self._gloss = gloss

    def parse_definition(self, definition, host=None):
        """

        :param definition:
        :param host:
        :return:
        """
        definitions = [d.strip() for d in definition.split(',')]
        gloss = ''
        new_values = {}
        if host:
            features = host.features
        else:
            features = {}
        for dstring in definitions:
            if dstring.startswith("'") or dstring.startswith('"'):
                gloss = dstring
                continue
            parts = dstring.split(':', 1)
            if len(parts) > 1:
                key = parts[0]
                value = parts[1]
                new_values[key] = value
            elif len(parts) == 1:
                key = parts[0]
                new_values[key] = ''
        for key, value in new_values.items():
            if key in features:
                features[key].set(value)
            else:
                feature = ctrl.Feature(key, value)
                features[key] = feature
        if gloss:
            features['gloss'] = gloss
        return features

    def add_local_lexicon(self, C):
        """

        :param C:
        """
        self.local_lexicon[C.label] = C

    def get_word(self, word):
        """

        :param word:
        :return:
        """
        return self.local_lexicon.get(word, None)

    def text_area_parser(self, text):
        """ string to TextArea
        :param text:
        """
        if text.startswith("'"):
            text = text[1:]
        ta = TextArea(text)
        self.forest.others[ta.save_key] = ta
        return ta

    def image_parser(self, text):
        """ string to Image
        :param text:
        """
        if text.startswith("%"):
            image_path = text[1:]
        else:
            image_path = text
        im = Image(image_path)
        self.forest.others[im.save_key] = im
        return im

    def _create_constituent(self, features):
        """ Uses parsed dict of features """
        label = features['label']
        if isinstance(label, ctrl.Feature):
            label = features['label'].get_value()
        else:
            raise Exception("Label is not a proper Feature")
        lexicon_entry = ctrl.UG.lexicon.get(label, None)
        local_entry = self.local_lexicon.get(label, None)
        if local_entry:
            constituent = local_entry
        elif lexicon_entry:
            constituent = lexicon_entry.copy()
        else:
            constituent = ctrl.Constituent(label)
        constituent.set_features(features)
        self.add_local_lexicon(constituent)
        return constituent


    def _new_trace_from_constituent(self, constituent):
        node = self.forest.create_node_from_constituent(constituent, silent=True)
        node.is_trace = True
        return node

    def _new_node_from_constituent(self, constituent):
        node = self.forest.create_node_from_constituent(constituent, result_of_select=True)
        return node

    def _new_merger_node_from_constituent(self, constituent):
        node = self.forest.create_node_from_constituent(constituent, result_of_merge=True)
        return node

    # not used
    #def _merge_trees(self, node, left, right):
    #    if self.forest:
    #        self.forest.update_roots()

    # ## Bottom-up Parser, does not handle trees, but strings of words

    def bottom_up_parser(self, buildstring):
        """ stringToBottomUp
        :param buildstring:
        """
        topmost_C = None
        self.indexes = []
        if buildstring.startswith('>>'):
            buildstring = buildstring[2:]
        self.tree_object = None

        def _find_in_tree(const_id):
            def _find(const_id, X):
                if not X:
                    return None
                if X.label == const_id:
                    return X
                else:
                    found = None
                    if X.left:
                        found = _find(const_id, X.left)
                        if found:
                            return found
                    if X.right:
                        found = _find(const_id, X.right)
                    return found

            return _find(const_id, topmost_C)

        def _merge_up(word_string, topmost_C):
            features = self.parse_definition(definition=word_string)
            if 'label' not in features:
                features['label'] = word_string
                const_id = word_string
            else:
                const_id = features['label'].get_value()
            dotlabel = features.get('dotlabel', None)
            if dotlabel:
                dotlabel = dotlabel.get_value()
                if not dotlabel:
                    assert False
            C = _find_in_tree(const_id)
            if not C:
                C = self._create_constituent(features=features)
                # index=utils.next_free_index(self.indexes)
                # self.indexes.append(index)
                # C.set_index(index)
                node = self._new_node_from_constituent(C)
                external_merge = True
            else:
                external_merge = False
                node = self.forest.get_node(C)
                index = node.get_index()
                if not index:
                    index = next_free_index(self.indexes)
                    self.indexes.append(index)
                    node.set_index(index)
                node = self.forest.create_trace_for(node)
            if topmost_C:
                if external_merge and topmost_C.label:
                    tid = topmost_C.label
                else:
                    tid = C.label
                topmost_C = ctrl.UG.Merge(C, topmost_C)
                topmost_C.label = C.label
                topmost_node = self._new_merger_node_from_constituent(topmost_C)
                if dotlabel:
                    topmost_node.alias = dotlabel
                elif external_merge:
                    topmost_node.alias = tid
                left = self.forest.get_node(topmost_C.left)
                right = self.forest.get_node(topmost_C.right)
                # These are not implemented anymore:
                self.forest.mirror_syntactic_edges(topmost_node, left)
                self.forest.mirror_syntactic_edges(topmost_node, right)
                # self._merge_trees(node, left, right)
            else:
                topmost_C = C
            return topmost_C

        count = 0
        word = []
        words = buildstring.strip().split()
        for word in words:
            topmost_C = _merge_up(word, topmost_C)
            count += 1
        root = self.forest.get_node(topmost_C)
        return root

    def after_restore(self, values=None):
        """

        :param values:
        :return:
        """
        if not values:
            values = {}
        return


class LayeredParser(Parser):
    # ### Layered parser ########################################################

    """

    """

    def __init__(self, forest):
        Parser.__init__(self, forest)
        self._layers = [('', [])]
        self._current_layer = []
        self._state = ''

    def _new_merge(self, args):
        f = self.forest
        left = None
        right = None
        constituent = ctrl.Constituent()
        children = []
        alias = None
        for arg in args:
            if isinstance(arg, list):
                for item in arg:
                    if isinstance(item, tuple):
                        if item[0] == 'index':
                            constituent.set_index(item[1])
                        elif item[0] == 'alias':
                            alias = item[1]

            if isinstance(arg, ctrl.Constituent):
                children.append(arg)
            if isinstance(arg, tuple):
                if arg[0] == 'index':
                    constituent.set_index(arg[1])
                elif arg[0] == 'alias':
                    alias = arg[1]
        if len(children) == 2:
            left = children[0]
            right = children[1]
            constituent.left = left
            constituent.right = right
            node = self._new_merger_node_from_constituent(constituent)
        elif len(children) == 1:
            constituent = children[0]
            node = self.forest.get_node(constituent)
        if alias:
            node.set_alias(alias)
        if left:
            self.forest._connect_node(parent=node, child=f.get_node(left), direction='left')
        if right:
            self.forest._connect_node(parent=node, child=f.get_node(right), direction='right')
        node.update_label()
        f.derivation_steps.save_and_create_derivation_step()
        return constituent

    def _new_constituent(self, args):
        label = args[0]
        features = args[1:]
        if isinstance(label, list):
            features += label[1:]
            label = label[0]
        constituent = ctrl.Constituent(label)
        for arg in features:
            if isinstance(arg, ctrl.Feature):
                constituent.set_feature(arg.save_key, arg)
            elif isinstance(arg, tuple) and arg[0] == 'index':
                constituent.set_index(arg[1])
        if label in self._definitions:
            features = self.parse_definition(self._definitions[label])
            if 'gloss' in features:
                constituent.set_gloss(features['gloss'])
                del features['gloss']
            constituent.set_features(features)
        self.add_local_lexicon(constituent)
        node = self._new_node_from_constituent(constituent)
        return constituent

    def _new_command(self, command, args=None):
        if not args:
            args = []
        commands = []
        if command in commands:
            pass
        else:
            feature = ctrl.Feature(command, ''.join(args))
            return feature

    def _new_string(self, args):
        string = ''
        as_list = []
        for arg in args:
            if isinstance(arg, str):
                string += arg
            else:
                as_list.append(arg)
        if as_list:
            return [string] + as_list
        else:
            return string

    def _new_alias(self, args):
        alias = ""
        others = []
        if len(args) == 1 and isinstance(args[0], list):
            args = args[0]
        for arg in args:
            if isinstance(arg, tuple):
                others.append(arg)
            else:
                alias += arg
        if alias and others:
            return [('alias', alias)] + others
        elif alias:
            return 'alias', alias
        elif others:
            if len(others) == 1:
                return others[0]
            else:
                return others
        else:
            return ""

    def _new_index(self, args):
        return 'index', ''.join(args)

    def _new_superscript(self, args):
        return '<sup>%s</sup>' % ''.join(args)

    def parse(self, string):
        """ parse parse state machine.
        This can read latex-type Tree structures and turn them to Kataja objects

        The idea is that the inputstring is split into meaningful tokens,
        and tokens can switch the state of the parser. For each state, there
        is a token or tokens that can end this state. When the state is finished,
        tokens handled within that state are grouped together (to layer) and used as arguments
        for building a certain type of Object, depending on state. When this Object
        has been built, the (state, layer)-tuple is replaced with the Object. So when objects
        are built, their arguments can only be plain strings or other Objects.
        (commands are special, they get their arguments as [command_name, [list_of_args]])

        :param string:
        layers are stored as a stack: you only operate on topmost object, but when it turns to Object, you remove it from stack and add the Object as an argument for next layer in stack.

        """
        self._layers = [('', [])]
        self._current_layer = []
        self._state = ''

        def _indent():
            """ This is for debugging printout """
            return ' ' * len(self._layers)

        def _new_state(state_marker):
            # print 'starting: %s' % state_marker
            self._current_layer = []
            # print "%s+opening state= '%s'" % (_indent() , state_marker)
            self._layers.append((state_marker, self._current_layer))
            self._state = state_marker

        def _close_this_and_get_previous_state():
            # print 'finishing:' + str(((self._state, self._current_layer)))
            self._layers.pop()
            previous_state, previous_layer = self._layers[-1]
            # make this layer an argument for previous layer.
            # print u"%s-closing state= '%s', layer=%s" % (_indent(), self._state, self._current_layer)
            layer = finalized_layer(self._state, self._current_layer, previous_state)
            # print _indent(), '= ', repr(layer), layer
            previous_layer.append(layer)
            self._current_layer = previous_layer
            self._state = previous_state


        def finalized_layer(type, layer, prev_type):
            """ This layer is ready to be turned into command with arguments. Layer
            :param type:
            :param layer:
            :param prev_type:
            turns into some kind of object: Constituent, Feature, Merge etc. """
            if type == 'word':
                if prev_type in ['\\', '_', '^', '.']:
                    return ''.join(layer)
                else:
                    return self._new_constituent(layer)
            elif type == '[':
                return self._new_merge(layer)
            elif type == '{':
                return self._new_string(layer)
            elif type == '\\':
                command = layer.pop(0)
                if layer:
                    return self._new_command(command, layer[0])
                else:
                    return self._new_command(command)
            elif type == '.':
                al = self._new_alias(layer)
                return al
            elif type == '_':
                return self._new_index(layer)
            elif type == '^':
                return self._new_superscript(layer)
            elif type == 'arg':
                return layer
            else:
                # print '=== finalizing whole structure === '
                return layer

        splitter = '([\\\[\]\{\} +_\^\$])'  #

        items = re.split(splitter, string)

        for item in items:
            # splitting algorithm leaves empty strings to list, ignore them
            if not item:
                continue

            # print "item: '%s', state: '%s', depth: %s" % (item,self._state, len(self._layers))
            # print 'this layer:', self._current_layer
            # print u"%sreading token '%r' in state '%s'" % (_indent(), item, self._state)
            # print u"%sreading token '%s' in state '%s'" % (_indent(), item, self._state)

            if not self._state:
                # at the beginning there is no state
                if item == '[':
                    _new_state('[')
                elif item == '{':
                    _new_state('word')
                    _new_state('{')
                elif item == '\\':
                    _new_state('\\')
                elif item == '_':
                    _new_state('_')
                elif item == '^':
                    _new_state('^')
                elif item == ' ':
                    pass
                elif item:
                    _new_state('word')
                    self._current_layer.append(item)

            elif self._state == '[':
                # everything inside brackets should eventually be turned into words

                if item == '[':
                    _new_state('[')
                elif item == ']':
                    # do what needs to be done to build constituents.
                    _close_this_and_get_previous_state()
                elif item == '{':
                    _new_state('word')
                    _new_state('{')
                elif item == '\\':
                    _new_state('\\')
                elif item == '_':
                    _new_state('_')
                elif item == '^':
                    _new_state('^')
                elif item == '.':
                    _new_state('.')
                elif item == ' ':
                    pass
                elif item:
                    _new_state('word')
                    self._current_layer.append(item)

            elif self._state == 'word':
                # the actual word has already been read, now we want to find end of the word
                if item == '[':
                    # ends the word but starts a new constituent: [Jukka[halaa puita]]
                    _close_this_and_get_previous_state()
                    _new_state('[')
                elif item == ']':
                    _close_this_and_get_previous_state()
                    # ends the word but also ends the constituent
                    _close_this_and_get_previous_state()
                elif item == '{':
                    # starting a { inside a word will end the word.
                    # {jukka}{salla} are separate words.
                    _close_this_and_get_previous_state()
                    _new_state('word')
                    _new_state('{')
                elif item == '\\':
                    _new_state('\\')
                elif item == '_':
                    _new_state('_')
                elif item == '^':
                    _new_state('^')
                elif item == ' ':
                    # ends the word
                    _close_this_and_get_previous_state()
                elif item:
                    # strange character: let's just add it to word
                    self._current_layer.append(item)

            elif self._state == '{':
                if item == '{':
                    _new_state('{')
                elif item == '}':
                    _close_this_and_get_previous_state()
                    if self._state in ['\\', '_', '^']:
                        # these commands end after they have been given an argument
                        _close_this_and_get_previous_state()
                elif item == '\\':
                    _new_state('\\')
                elif item == '_':
                    _new_state('_')
                elif item == '^':
                    _new_state('^')
                elif item == ' ':
                    self._current_layer.append(item)
                else:
                    self._current_layer.append(item)
            elif self._state in ['_', '^', '.']:
                if item == '{':
                    _new_state('{')
                elif item == '\\':
                    _new_state('\\')
                elif item == ' ':
                    _close_this_and_get_previous_state()
                else:
                    self._current_layer.append(item)
                    _close_this_and_get_previous_state()

            elif self._state == '\\':  # \command{}
                self._current_layer.append(item)
                _new_state('arg')
            elif self._state == 'arg':  # argument either takes { or closes the thing
                if item == '{':
                    _new_state('{')
                elif item == '[':
                    _close_this_and_get_previous_state()
                    _close_this_and_get_previous_state()
                    _new_state('[')
                elif item == ']':
                    _close_this_and_get_previous_state()
                    _close_this_and_get_previous_state()
                elif item == '\\':
                    _close_this_and_get_previous_state()
                    _new_state('\\')
                elif item == '_':
                    _close_this_and_get_previous_state()
                    _new_state('_')
                elif item == '^':
                    _close_this_and_get_previous_state()
                    _new_state('^')
                elif item == ' ':
                    _close_this_and_get_previous_state()
                    _close_this_and_get_previous_state()
                else:
                    _close_this_and_get_previous_state()

        self._layers = finalized_layer(self._state, self._current_layer, '')
        # self.forest.
        # print self._layers

    # tree= r'''[ {Hei} [ sana\komento{parametri} {pitempi kokonaisuus_{toinen kokonaisuus}}]]'''
    # tree= r''' [ Jukka [ {Salla vai}{muuta ei} ] ]'''

    # p=Parser()
    # out= p.parse(tree)

    def after_restore(self, values=None):
        """

        :param values:
        :return:
        """
        if not values:
            values = {}
        return


class BottomUpParser(Parser):
    # ### Layered parser 2 -- start from right ########################################################

    def parse(self, string):
        """ parse parse state machine.
        This can read latex-type Tree structures and turn them to Kataja objects

        The idea is that the inputstring is split into meaningful tokens,
        and tokens can switch the state of the parser. For each state, there
        is a token or tokens that can end this state. When the state is finished,
        tokens handled within that state are grouped together (to layer) and used as arguments
        for building a certain type of Object, depending on state. When this Object
        has been built, the (state, layer)-tuple is replaced with the Object. So when objects
        are built, their arguments can only be plain strings or other Objects.
        (commands are special, they get their arguments as [command_name, [list_of_args]])

        :param string:
        layers are stored as a stack: you only operate on topmost object, but when it turns to Object, you remove it from stack and add the Object as an argument for next layer in stack.

        """
        self.layers = 0

        splitter = re.compile(r'(\\|\[|\]|{|}| +)')

        stream = [x for x in re.split(splitter, string) if x]


        def find_index(label):
            """

            :param label:
            :return:
            """
            label_tuple = tuple(label.split('_', 1))
            if len(label_tuple) == 2:
                hlabel, index = label_tuple
            else:
                hlabel = label_tuple[0]
                index = ''
            return hlabel, index

        def create_constituent(label, dot_alias=''):
            # print 'creating a constituent for label "%s"' % label
            """

            :param label:
            :param dot_alias:
            :return:
            """
            label, index = find_index(label)
            constituent = ctrl.Constituent(label)
            # print label, label in self._definitions, self._definitions
            if label in self._definitions:
                features = self.parse_definition(self._definitions[label])
                if 'gloss' in features:
                    constituent.set_gloss(features['gloss'])
                    del features['gloss']
                constituent.set_features(features)
            if label == 't' and index:
                node = self._new_trace_from_constituent(constituent)
            else:
                node = self._new_node_from_constituent(constituent)
            if index:
                node.set_index(index)
            if dot_alias:
                node.set_alias(dot_alias)
            self.add_local_lexicon(constituent)
            return node

        def merge_constituents(left, right, dot_alias):
            """

            :param left:
            :param right:
            :param dot_alias:
            :return:
            """
            f = self.forest
            constituent = ctrl.Constituent()
            constituent.left = left.syntactic_object
            constituent.right = right.syntactic_object
            node = self._new_merger_node_from_constituent(constituent)
            if dot_alias:
                dot_alias, index = find_index(dot_alias)
                if index:
                    node.set_index(index)
                if dot_alias:
                    node.set_alias(dot_alias)
            if left:
                self.forest._connect_node(parent=node, child=left, direction='left')
            if right:
                self.forest._connect_node(parent=node, child=right, direction='right')
            node.update_label()
            f.derivation_steps.save_and_create_derivation_step()
            return node

        def merge_curlies(s):
            """

            :param s:
            :return:
            """
            pieces = []
            i = 0
            while i < len(s):
                if s[i] == '{':
                    # print 'more curlies'
                    s, merged = merge_curlies(s[i + 1:])
                elif s[i] == '}':
                    # print 'merged to %s, continuing with: %s' % (''.join(pieces), s[i+1:])
                    return s[i + 1:], ''.join(pieces)
                else:
                    pieces.append(s[i])
                i += 1
            return [], ''.join(pieces)

        def find_word(s):
            """

            :param s:
            :return:
            """
            i = 0
            word = ''
            command = False
            while i < len(s):
                c = s[i]
                if c == '{':
                    # print 'found curlies, merging:', s[i+1:]
                    s, word = merge_curlies(s[i + 1:])
                    # print 'we have curlies as a word ', word
                    return s, word.strip()
                elif c == ' ':
                    pass
                elif c == '\\':
                    # found something that starts a command word
                    # keep listening for next word
                    word = '\\'
                    command = True
                else:
                    # found regular word
                    word += c
                    # print 'found word %s, returning %s' % (word, s[i+1:])
                    return s[i + 1:], word.strip()
                i += 1
            # print 'didnt find a word'
            return [], word.strip()

        def find_dot_alias(s):
            """

            :param s:
            :return:
            """
            alias_string = ''
            if s[0] == '.':
                # print 'starting dot alias'
                s, alias_string = find_word(s[1:])
                # print 'found label string: ', label_string
            return s, alias_string

        def find_constituent(s):
            """

            :param s:
            :return:
            """
            s, word = find_word(s)
            # if word:
            # print 'find constituent found %s, still remaining %s' % (word, s)
            return s, word

        def analyze_words_inside_brackets(s, constituents):
            # print 'starting analyze, len(s): %s, s: %s' % (len(s), s)
            """

            :param s:
            :param constituents:
            :return: :raise:
            """
            merging = []
            s, dot_alias = find_dot_alias(s)
            s, new_label = find_constituent(s)
            if new_label:
                # print 'found one constituent (%s), len(s): %s, s: %s' % (new_label, len(s), s)
                D = None
                if s:  # for correct order the right side constituent needs to be created first
                    s, other_label = find_constituent(s)
                    if other_label:
                        D = create_constituent(other_label)
                        # print 'found second constituent (%s), len(s): %s, s: %s' % (other_label, len(s), s)
                C = create_constituent(new_label)
                merging.append(C)
                if D:
                    merging.append(D)

            # print 'done analyzing, len(s): %s, s: %s' % (len(s), s)
            merging += constituents
            if not merging:
                merging.append(create_constituent(''))
            if len(merging) > 2:
                parser('too many constituents for binary branching. \nConstituents: %s \nMerging: %s \n%s' % (
                    constituents, merging, string))
                M = merge_constituents(merging[0], merging[1], dot_alias)
                return M
            elif len(merging) == 2:
                M = merge_constituents(merging[0], merging[1], dot_alias)
                return M
            else:  # len(merging) == 1
                C = merging[0]
                if dot_alias:
                    dot_alias, index = find_index(dot_alias)
                    if index:
                        C.set_index(index)
                    if dot_alias:
                        C.set_alias(dot_alias)
                return C

        def bottom_up_bracket_parser(s):
            """

            :param s:
            :return:
            """
            self.layers += 1
            # print 'starting layer ', self.layers
            inside = []
            constituent = None
            constituents = []
            while s:
                c = s.pop()
                if s:
                    escape = s[-1] == '\\'
                else:
                    escape = False
                if c == ']' and not escape:
                    s, constituent = bottom_up_bracket_parser(s)
                    if constituent:
                        constituents.append(constituent)
                        # print 'received a layer: ', constituent
                elif c == '[' and not escape:
                    inside.reverse()
                    constituents.reverse()
                    constituent = analyze_words_inside_brackets(inside, constituents)
                    # print 'finalizing layer %s to %s' % (self.layers, constituent)
                    return s, constituent
                elif c:
                    # print 'adding "%s" inside' % c
                    inside.append(c)
            return s, constituent

        remainder, constituent = bottom_up_bracket_parser(list(stream))
        return remainder, constituent

    def after_restore(self, values=None):
        """

        :param values:
        :return:
        """
        if not values:
            values = {}
        return



