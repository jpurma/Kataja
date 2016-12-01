import re

import kataja.globals as g
from kataja.singletons import ctrl
from parser.deprecated.BaseParser import BaseParser


__author__ = 'purma'

# Deprecated -- INodeToKatajaConstituent is the one currently used

class BottomUpParser(BaseParser):
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
        print("Using BottomUpParser")
        self.layers = 0
        string = string.strip()
        if not string.startswith('['):
            string = '[' + string + ']'
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

        def create_constituent(label, dot_label=''):
            # print 'creating a constituent for label "%s"' % label
            """

            :param label:
            :param dot_alias:
            :return:
            """
            label, index = find_index(label)
            constituent = ctrl.syntax.Constituent(label)
            # print label, label in self._definitions, self._definitions
            if label in self._definitions:
                features = self.parse_definition(self._definitions[label])
                if 'gloss' in features:
                    constituent.gloss = features['gloss']
                    del features['gloss']
                constituent.features = features
            if label == 't' and index:
                node = self._new_trace_from_constituent(constituent)
            else:
                node = self._new_node_from_constituent(constituent)
            if index:
                node.index = index
            if dot_label:
                node.display_label = dot_label
            self.add_local_lexicon(constituent)
            return node

        def merge_constituents(left, right, dot_label):
            """

            :param left:
            :param right:
            :param dot_label:
            :return:
            """
            f = self.forest
            constituent = ctrl.syntax.Constituent()
            constituent.left = left.syntactic_object
            constituent.right = right.syntactic_object
            node = self.forest.create_node(synobj=constituent)
            self.forest.add_merge_counter(node)
            if dot_label:
                dot_label, index = find_index(dot_label)
                if index:
                    node.index = index
                if dot_label:
                    node.display_label = dot_label
            if left:
                self.forest.connect_node(parent=node, child=left, direction=g.LEFT)
            if right:
                self.forest.connect_node(parent=node, child=right, direction=g.RIGHT)
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

        def find_dot_label(s):
            """

            :param s:
            :return:
            """
            label_string = ''
            if s[0] == '.':
                # print 'starting dot display_label'
                s, label_string = find_word(s[1:])
                # print 'found label string: ', label_string
            return s, label_string

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
            s, dot_label = find_dot_label(s)
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
                print('too many constituents for binary branching. \nConstituents: %s \nMerging: %s \n%s' % (
                    constituents, merging, string))
                M = merge_constituents(merging[0], merging[1], dot_label)
                return M
            elif len(merging) == 2:
                M = merge_constituents(merging[0], merging[1], dot_label)
                return M
            else:  # len(merging) == 1
                C = merging[0]
                if dot_alias:
                    dot_alias, index = find_index(dot_label)
                    if index:
                        C.index = index
                    if dot_alias:
                        C.display_label = dot_label
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


