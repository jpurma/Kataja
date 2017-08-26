from kataja.singletons import ctrl
import copy

from kataja.Shapes import SHAPE_PRESETS, SHAPE_DEFAULTS
from kataja.utils import time_me
from kataja.saved.movables.Node import Node
from kataja.saved.Edge import Edge
from kataja.globals import HIGHEST, FOREST, DOCUMENT, PREFS, OBJECT, SELECTION
from collections import ChainMap


chain_level = {FOREST: 0, DOCUMENT: 1, PREFS: 2}

class Settings:
    """ Settings is a class that gathers user preferences, document settings and forest settings in
    one interface: when a setting is queried, the highest defined possible is used.

     Settings also works as a manager for settings, setting and deleting values is done here.
     Various data objects are not stored here, they are hosted by kataja main, document and forest.

     When setting or deleting a value, it is important to tell which layer is supposed to change.
     get, set and del have layer parameter with possible values:

    HIGHEST = 0
    OBJECT = 1
    SELECTION = 2
    FOREST = 3
    DOCUMENT = 4
    PREFS = 5

    CONFLICT = 666666

    """

    def __init__(self):
        """ Various chains have ChainMaps, mutable settings are plain dicts in their objects (so
        the save system can work with them.) ChainMaps refer to them. Make sure that the
        references keep pointing at the current dict by using set_prefs, set_document and
        set_forest.

        Full chain sequences:
        obj.settings_chain: obj.settings, forest.settings, document.settings, prefs
        forest_chain: forest.settings, document.settings, prefs
        document_chain: document.settings, prefs
        shape_chain: forest.settings['edges'], document.settings['edges'], prefs.edges

        """

        self.ui = None
        self.prefs = None
        self.document = None
        self.forest = None
        self.document_chain = ChainMap({}, {})
        self.forest_chain = self.document_chain.new_child()
        # These are dicts that hold the property chains for subtypes of nodes, edges and shapes
        self.shape_type_chains = {}
        self.node_type_chains = {}
        self.edge_type_chains = {}

    def set_prefs(self, prefs):
        self.prefs = prefs
        self.document_chain.maps[-1] = prefs.__dict__
        self.forest_chain.maps[-1] = prefs.__dict__
        for key, node_settings in prefs.nodes.items():
            if key not in self.node_type_chains:
                self.node_type_chains[key] = ChainMap({}, {}, node_settings)
            else:
                self.node_type_chains[key].maps[-1] = node_settings
        for key, edge_settings in prefs.edges.items():
            if key not in self.edge_type_chains:
                self.edge_type_chains[key] = ChainMap({}, {}, edge_settings)
            else:
                self.edge_type_chains[key].maps[-1] = edge_settings
            shape_name = edge_settings['shape_name']
            if key not in self.shape_type_chains:
                self.shape_type_chains[key] = ChainMap({}, {}, SHAPE_PRESETS[shape_name].defaults)
            else:
                self.shape_type_chains[key].maps[-1] = SHAPE_PRESETS[shape_name].defaults

    def set_ui_manager(self, ui_manager):
        self.ui = ui_manager

    def set_document(self, document):
        self.document = document
        self.forest = None
        self.document_chain.maps[0] = document.settings
        self.forest_chain = self.document_chain.new_child()
        node_types = document.settings.get('nodes', {})
        for key, node in self.node_type_chains.items():
            self.node_type_chains[key].maps[1] = node_types.get(key, {})
        edge_types = document.settings.get('edges', {})
        for key, edge in self.edge_type_chains.items():
            self.edge_type_chains[key].maps[1] = edge_types.get(key, {})

    def set_forest(self, forest):
        self.forest = forest
        self.forest_chain.maps[0] = forest.settings
        node_types = forest.settings.get('nodes', {})
        for key, node in self.node_type_chains.items():
            self.node_type_chains[key].maps[0] = node_types.get(key, {})
        edge_types = forest.settings.get('edges', {})
        for key, edge in self.edge_type_chains.items():
            self.edge_type_chains[key].maps[0] = edge_types.get(key, {})

    #@time_me
    def get(self, key, level=HIGHEST, obj=None, only=False):
        if level == SELECTION:
            level = HIGHEST
        if obj and level <= HIGHEST:
            #if not obj.settings_chain:
            #    obj.settings_chain = self.forest_chain.new_child(obj.settings)
            return obj.settings_chain[key]
        elif level <= FOREST:
            return self.forest_chain[key]
        elif level <= DOCUMENT:
            return self.document_chain[key]
        return getattr(self.prefs, key)

    def set(self, key, value, level=OBJECT, obj=None):
        """ When writing a setting, you have to tell in which level to write on:
        OBJECT, SELECTION, FOREST, DOCUMENT or PREFS. If you are writing to OBJECT,
        you have to provide the object with obj-parameter.
        :param key:
        :param value:
        :param level:
        :param obj:
        :param override: if true, delete value from layers above this. e.g. if you set value in
         DOCUMENT level, remove same value from FOREST and objects.
        :return:
        """
        #print('set settings: key:%s, value:%s, level:%s, obj:%s' %
        #      (key, value, level, obj))

        if level == OBJECT:
            if not obj:
                raise ValueError
            obj.poke('settings')
            obj.settings[key] = value
        elif level == FOREST:
            if self.forest:
                self.forest.poke('settings')
                self.forest.settings[key] = value
        elif level == DOCUMENT:
            self.document.poke('settings')
            self.document.settings[key] = value
        elif level == PREFS:
            setattr(self.prefs, key, value)

    def delete(self, key, level=OBJECT, obj=None):
        """ When deleting a setting, you have to tell in which level to delete:
        OBJECT, FOREST or DOCUMENT. If you are deleting in OBJECT,
        you have to provide the object with obj-parameter. Value cannot be deleted from PREFS.

        Deleting a value in a level causes one to use one from the next level.
        :param key:
        :param value:
        :param level:
        :param obj:
        :return:
        """
        if level == OBJECT:
            if not obj:
                raise ValueError
            if key in obj.settings:
                del obj.settings[key]
        elif level == FOREST:
            if key in self.forest.settings:
                del self.forest.settings[key]
        elif level == DOCUMENT:
            if key in self.document.settings:
                del self.document.settings[key]

    # Those settings that are represented by dict need special methods to get/set/delete, as having
    # some dict set is not enough, one has to check if the dict has necessary key and traverse
    # deeper if that is not the case.

    # Edge settings are stored directly in Edge.settings, but in settings['edges'][edge_type]
    # in layers below.

    # assigning forest and document dicts to ChainMaps requires that the identity of assigned
    # dict remains the same: we shouldn't have missing dicts for certain edge types in
    # intermediate levels.

    #@time_me

    @staticmethod
    def set_in_container(key, value, container, dict_name, subtype, level, chain):
        container.poke('settings')
        if dict_name not in container.settings:
            level_dict = {}
            container.settings[dict_name] = level_dict
        else:
            level_dict = container.settings[dict_name]
        if subtype not in level_dict:
            level_dict[subtype] = {
                key: value
            }
        else:
            level_dict[subtype][key] = value
        chain[subtype].maps[chain_level[level]] = level_dict[subtype]

    @staticmethod
    def del_in_container(key, container, dict_name, subtype, level):
        if dict_name in container.settings and \
                        subtype in container.settings[dict_name] and \
                        key in container.settings[dict_name][subtype]:
            container.poke('settings')
            del container.settings[dict_name][subtype][key]

    @staticmethod
    def reset_in_container(container, dict_name, subtype, level, chain):
        if dictname in container.settings:
            container.poke('settings')
            if dict_name in container and subtype in container[dict_name]:
                del d[subtype]
                chain[subtype].maps[chain_level[level]] = {}
                if not container[dict_name]:
                    del container.settings[dict_name]

    def get_edge_setting(self, key, edge_type=None, edge=None, level=HIGHEST):
        if edge:
            edge_type = edge.edge_type
        if level == HIGHEST or level == OBJECT:
            if edge and edge.settings_chain:
                return edge.settings_chain[key]
            else:
                return self.edge_type_chains[edge_type][key]
        for my_map in self.edge_type_chains[edge_type].maps[chain_level[level]:]:
            if key in my_map:
                return my_map[key]

    def set_edge_setting(self, key, value, edge_type=None, obj=None, level=OBJECT):
        if not (obj or edge_type):
            raise ValueError
        if obj:
            obj.poke('settings')
            obj.settings[key] = value
        elif level == FOREST:
            self.set_in_container(key, value, self.forest, 'edges', edge_type, level,
                                  self.edge_type_chains)
        elif level == DOCUMENT:
            self.set_in_container(key, value, self.document, 'edges', edge_type, level,
                                  self.edge_type_chains)
        elif level == PREFS:
            self.prefs.poke('edges')
            if subtype not in self.prefs.edges:
                self.prefs.edges[edge_type] = {key: value}
            else:
                self.prefs.edges[edge_type][key] = value
            self.edge_type_chains[edge_type].maps[2] = self.prefs.edges[edge_type]


    def del_edge_setting(self, key, edge_type=None, obj=None, level=OBJECT):
        if not (obj or edge_type):
            raise ValueError
        if obj and key in obj.settings:
            obj.poke('settings')
            del obj.settings[key]
        elif level == FOREST:
            self.del_in_container(value, self.forest, 'edges', edge_type, level)
        elif level == DOCUMENT:
            self.del_in_container(value, self.document, 'edges', edge_type, level)
        else:
            if edge_type in self.prefs.edges and \
                    key in self.prefs.edges[edge_type]:
                self.prefs.poke('edges')
                del self.prefs.edges[edge_type][key]

    def reset_edge_setting(self, edge_type=None, obj=None, level=OBJECT):
        if not (obj or edge_type):
            raise ValueError
        if obj and obj.settings: # Note that this removes *all* object-level settings.
            obj.poke('settings')
            obj.settings = {}
        elif level == FOREST:
            self.reset_in_container(self.forest, 'edges', edge_type, level, self.edge_type_chains)
        elif level == DOCUMENT:
            self.reset_in_container(self.document, 'edges', edge_type, level, self.edge_type_chains)


   # Node settings are stored directly in Node.settings, but in settings['nodes'][node_type]
    # in layers below.


    def get_node_setting(self, key, node_type=None, node=None, level=HIGHEST):
        if node:
            node_type = node.node_type
        if level == HIGHEST or level == OBJECT:
            if node and node.settings_chain:
                return node.settings_chain[key]
            else:
                return self.node_type_chains[node_type][key]
        for my_map in self.node_type_chains[node_type].maps[chain_level[level]:]:
            if key in my_map:
                return my_map[key]

    def set_node_setting(self, key, value, node_type=None, obj=None, level=OBJECT):
        if not (obj or node_type):
            raise ValueError
        if obj:
            obj.poke('settings')
            obj.settings[key] = value
        elif level == FOREST:
            self.set_in_container(key, value, self.forest, 'nodes', node_type, level,
                                  self.node_type_chains)
        elif level == DOCUMENT:
            self.set_in_container(key, value, self.document, 'nodes', node_type, level,
                                  self.node_type_chains)
        elif level == PREFS:
            self.prefs.poke('edges')
            if subtype not in self.prefs.nodes:
                self.prefs.nodes[node_type] = {key: value}
            else:
                self.prefs.nodes[node_type][key] = value
            self.node_type_chains[node_type].maps[2] = self.prefs.nodes[node_type]

    def del_node_setting(self, key, node_type=None, obj=None, level=OBJECT):
        if not (obj or node_type):
            raise ValueError
        if obj and key in obj.settings:
            obj.poke('settings')
            del obj.settings[key]
        elif level == FOREST:
            self.del_in_container(value, self.forest, 'nodes', node_type, level)
        elif level == DOCUMENT:
            self.del_in_container(value, self.document, 'nodes', node_type, level)
        else:
            if node_type in self.prefs.nodes and \
                    key in self.prefs.nodes[node_type]:
                self.prefs.poke('nodes')
                del self.prefs.nodes[node_type][key]

    def reset_node_setting(self, node_type=None, obj=None, level=OBJECT):
        if not (obj or node_type):
            raise ValueError
        if obj and obj.settings: # Note that this removes *all* object-level settings.
            obj.poke('settings')
            obj.settings = {}
        elif level == FOREST:
            self.reset_in_container(self.forest, 'nodes', node_type, level, self.node_type_chains)
        elif level == DOCUMENT:
            self.reset_in_container(self.document, 'nodes', node_type, level, self.node_type_chains)

    def get_shape_setting(self, key, edge_type=None, edge=None, level=HIGHEST):
        if edge:
            edge_type = edge.edge_type
        if level == HIGHEST or level == OBJECT:
            if edge:
                return edge.shape_settings_chain[key]
            elif self.shape_type_chains:
                return self.shape_type_chains[edge_type][key]
        for my_map in self.shape_type_chains[edge_type].maps[chain_level[level]:]:
            if key in my_map:
                return my_map[key]

    def remove_all_shape_settings(self, edge, shape_name):
        keys = SHAPE_PRESETS[shape_name].defaults.keys()
        chain = self.shape_type_chains[edge.edge_type]
        for key in keys:
            if key in edge.settings:
                edge.poke('settings')
                del edge.settings[key]
            if key in chain.maps[0]:
                self.forest.poke('settings')
                del chain.maps[0][key]
            if key in chain.maps[1]:
                self.document.poke('settings')
                del chain.maps[1][key]

    def get_flattened_shape_settings(self, edge):
        return dict(edge.shape_settings_chain)

    def active_nodes(self, key, of_type, level):
        """ Return node setting either from selected items or from ui.active_node_type. If there
        are settings made in node level, return first of such occurence.
        :param key:
        :param of_type:
        :param level:
        :return:
        """
        if self.ui.scope_is_selection:
            for node in ctrl.selected:
                if isinstance(node, Node) and node.node_type == of_type:
                    return node.settings[key]
            level = HIGHEST
        return self.get_node_setting(key, node_type=of_type, level=level)

    def active_edge_setting(self, key):
        """ Return edge setting either from selected items or from ui.active_edge_type. If there
        are settings made in node level, return first of such occurence.
        :param key:
        :return:
        """
        if self.ui.scope_is_selection:
            typical_edge = None

            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    if key in edge.settings:
                        return edge.settings[key]
                    if not typical_edge:
                        typical_edge = edge
            if typical_edge:
                return self.get_edge_setting(key, edge=typical_edge)
        return self.get_edge_setting(key, edge_type=self.ui.active_edge_type)


    def active_shape_property(self, key):
        """ Return the class property of currently active edge shape.
        :param key:
        :return:
        """
        if self.ui.scope_is_selection:
            typical_edge = None

            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    if key in edge.settings:
                        return edge.settings[key]
                    if not typical_edge:
                        typical_edge = edge
            if typical_edge:
                return getattr(typical_edge.path.my_shape, key)
        shape_name = self.get_edge_setting('shape_name', edge_type=self.ui.active_edge_type)
        return getattr(SHAPE_PRESETS[shape_name], key)


    def active_shape_setting(self, key):
        """ Return edge setting either from selected items or from ui.active_edge_type. If there
        are settings made in node level, return first of such occurence.
        :param key:
        :return:
        """
        if self.ui.scope_is_selection:
            typical_edge = None

            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    if key in edge.settings:
                        return edge.settings[key]
                    if not typical_edge:
                        typical_edge = edge
            if typical_edge:
                return self.get_shape_setting(key, edge=typical_edge)
        return self.get_shape_setting(key, edge_type=self.ui.active_edge_type)

