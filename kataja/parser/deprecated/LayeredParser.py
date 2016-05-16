import re

__author__ = 'purma'

from kataja.singletons import classes
import kataja.globals as g
from parser.deprecated.BaseParser import BaseParser

# Deprecated -- INodeToKatajaConstituent is the one currently used

class LayeredParser(BaseParser):
    # ### Layered parser ########################################################

    """

    """

    def __init__(self, forest):
        BaseParser.__init__(self, forest)
        self._layers = [('', [])]
        self._current_layer = []
        self._state = ''

    def _new_merge(self, args):
        f = self.forest
        left = None
        right = None
        constituent = classes.Constituent()
        children = []
        alias = None
        for arg in args:
            if isinstance(arg, list):
                for item in arg:
                    if isinstance(item, tuple):
                        if item[0] == 'index':
                            constituent.index = item[1]
                        elif item[0] == 'alias':
                            alias = item[1]

            if isinstance(arg, classes.Constituent):
                children.append(arg)
            if isinstance(arg, tuple):
                if arg[0] == 'index':
                    constituent.index = arg[1]
                elif arg[0] == 'alias':
                    alias = arg[1]
        if len(children) == 2:
            left = children[0]
            right = children[1]
            constituent.left = left
            constituent.right = right
            node = self.forest.create_node(synobj=constituent)
            self.forest.add_merge_counter(node)
        elif len(children) == 1:
            constituent = children[0]
            node = self.forest.get_node(constituent)
        if alias:
            node.alias = alias
        if left:
            self.forest.connect_node(parent=node, child=f.get_node(left), direction=g.LEFT)
        if right:
            self.forest.connect_node(parent=node, child=f.get_node(right), direction=g.RIGHT)
        node.update_label()
        f.derivation_steps.save_and_create_derivation_step()
        return constituent

    def _new_constituent(self, args):
        label = args[0]
        features = args[1:]
        if isinstance(label, list):
            features += label[1:]
            label = label[0]
        constituent = classes.Constituent(label)
        for arg in features:
            if isinstance(arg, classes.Feature):
                constituent.set_feature(arg.uid, arg)
            elif isinstance(arg, tuple) and arg[0] == 'index':
                constituent.index = arg[1]
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
            feature = classes.Feature(fname=command, value=''.join(args))
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
        print("Using layered parser")

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

        # trees= r'''[ {Hei} [ sana\komento{parametri} {pitempi kokonaisuus_{toinen kokonaisuus}}]]'''
        # trees= r''' [ Jukka [ {Salla vai}{muuta ei} ] ]'''

        # p=Parser()
        # out= p.parse(trees)

