from kataja.singletons import ctrl
import copy

from kataja.Shapes import SHAPE_PRESETS
from kataja.utils import time_me
from kataja.saved.movables.Node import Node
from kataja.saved.Edge import Edge
from kataja.globals import HIGHEST, FOREST, DOCUMENT, PREFS, OBJECT, SELECTION
from collections import ChainMap

chain_level = {
    FOREST: 0,
    DOCUMENT: 1,
    PREFS: 2
}



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
        self.flat_shape_settings = {}
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
            self.flat_shape_settings[key] = dict(SHAPE_PRESETS[shape_name].defaults)

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
        for key in self.edge_type_chains.keys():
            document_edge_settings = edge_types.get(key, {})
            self.edge_type_chains[key].maps[1] = document_edge_settings
            shape_name = self.get_edge_setting('shape_name', edge_type=key, level=DOCUMENT)
            shape = SHAPE_PRESETS[shape_name]
            chain_parts = self.edge_type_chains[key].maps
            flat = dict(shape.defaults)
            flat.update(chain_parts[1])
            self.flat_shape_settings[key] = flat

    def set_forest(self, forest):
        self.forest = forest
        self.forest_chain.maps[0] = forest.settings
        node_types = forest.settings.get('nodes', {})
        for key, node in self.node_type_chains.items():
            self.node_type_chains[key].maps[0] = node_types.get(key, {})
        edge_types = forest.settings.get('edges', {})
        for key in self.edge_type_chains.keys():
            forest_edge_settings = edge_types.get(key, {})
            self.edge_type_chains[key].maps[0] = forest_edge_settings
            shape_name = self.get_edge_setting('shape_name', edge_type=key, level=FOREST)
            shape = SHAPE_PRESETS[shape_name]
            chain_parts = self.edge_type_chains[key].maps
            flat = dict(shape.defaults)
            flat.update(chain_parts[1])
            flat.update(chain_parts[0])
            self.flat_shape_settings[key] = flat
        for edge in forest.edges.values():
            edge.flatten_settings()

    # @time_me
    def get(self, key, level=HIGHEST, obj=None):
        if level == SELECTION:
            level = HIGHEST
        if obj and level <= HIGHEST:
            if obj.settings_chain is None:
                obj.settings_chain = self.forest_chain.new_child(obj.settings)
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
        :return:
        """
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

    @staticmethod
    def set_in_container(key, value, container, dict_name, subtype, level, chain):
        container.poke('settings')
        if dict_name not in container.settings:
            level_dict = {}
            container.settings[dict_name] = level_dict
        else:
            level_dict = container.settings[dict_name]
        if subtype not in level_dict:
            level_dict[subtype] = chain[subtype].maps[chain_level[level]]
        level_dict[subtype][key] = value
        chain[subtype].maps[chain_level[level]] = level_dict[subtype]

    @staticmethod
    def del_in_container(key, container, dict_name, subtype):
        if dict_name in container.settings and subtype in container.settings[dict_name] and key in \
                container.settings[dict_name][subtype]:
            container.poke('settings')
            del container.settings[dict_name][subtype][key]

    @staticmethod
    def reset_in_container(container, dict_name, subtype, level, chain):
        settings = container.settings
        if dict_name in settings:
            container.poke('settings')
            if dict_name in settings and subtype in settings[dict_name]:
                del settings[dict_name][subtype]
                chain[subtype].maps[chain_level[level]] = {}
                if not settings[dict_name]:
                    del settings[dict_name]

    def get_edge_setting(self, key, edge_type=None, edge=None, level=HIGHEST):
        if edge:
            edge_type = edge.edge_type
        if level == HIGHEST or level == OBJECT:
            if edge and edge.flattened_settings:
                return edge.flattened_settings[key]
            else:
                return self.edge_type_chains[edge_type][key]
        for my_map in self.edge_type_chains[edge_type].maps[chain_level[level]:]:
            if key in my_map:
                return my_map[key]

    def set_edge_setting(self, key, value, edge_type=None, edge=None, level=OBJECT):
        # print('set_edge_setting ', key, value, edge_type, obj, level)
        if not (edge or edge_type):
            raise ValueError
        if edge:
            edge.poke('settings')
            edge.settings[key] = value
            edge.flatten_settings()
            return
        elif level == FOREST:
            self.set_in_container(key, value, self.forest, 'edges', edge_type, level,
                                  self.edge_type_chains)
        elif level == DOCUMENT:
            self.set_in_container(key, value, self.document, 'edges', edge_type, level,
                                  self.edge_type_chains)
        elif level == PREFS:
            if edge_type not in self.prefs.edges:
                self.prefs.edges[edge_type] = {
                    key: value
                }
            else:
                self.prefs.edges[edge_type][key] = value
            self.edge_type_chains[edge_type].maps[2] = self.prefs.edges[edge_type]
        for edge in ctrl.forest.edges.values():
            if edge.edge_type == edge_type:
                edge.flatten_settings()

    def del_edge_setting(self, key, edge_type=None, obj=None, level=OBJECT):
        if not (obj or edge_type):
            raise ValueError
        if obj and key in obj.settings:
            obj.poke('settings')
            del obj.settings[key]
        elif level == FOREST:
            self.del_in_container(value, self.forest, 'edges', edge_type)
        elif level == DOCUMENT:
            self.del_in_container(value, self.document, 'edges', edge_type)
        else:
            if edge_type in self.prefs.edges and key in self.prefs.edges[edge_type]:
                del self.prefs.edges[edge_type][key]

    def reset_edge_settings(self, edge_type, level=HIGHEST):
        print('reset edge settings called')
        if level == HIGHEST:
            level = FOREST
        if level == FOREST:
            self.reset_in_container(self.forest, 'edges', edge_type, level, self.edge_type_chains)
        elif level == DOCUMENT:
            self.reset_in_container(self.document, 'edges', edge_type, level, self.edge_type_chains)
            # Node settings are stored in Node.settings, at settings['nodes'][node_type]
        self.flatten_shape_settings(edge_type)
        for edge in ctrl.forest.edges.values():
            if edge.edge_type == edge_type:
                edge.reset_settings()

    def get_node_setting(self, key, node_type=None, node=None, level=HIGHEST):
        if node:
            node_type = node.node_type
        if level == SELECTION:
            level = HIGHEST
        if level == HIGHEST or level == OBJECT:
            if node and node.node_type_settings_chain:
                return node.node_type_settings_chain[key]
            else:
                return self.node_type_chains[node_type][key]
        for my_map in self.node_type_chains[node_type].maps[chain_level[level]:]:
            if key in my_map:
                return my_map[key]

    def set_node_setting(self, key, value, node_type=None, node=None, level=OBJECT):
        if not (node or node_type):
            raise ValueError
        if node:
            node.poke('settings')
            node.settings[key] = value
        elif level == FOREST:
            self.set_in_container(key, value, self.forest, 'nodes', node_type, level,
                                  self.node_type_chains)
        elif level == DOCUMENT:
            self.set_in_container(key, value, self.document, 'nodes', node_type, level,
                                  self.node_type_chains)
        elif level == PREFS:
            if node_type not in self.prefs.nodes:
                self.prefs.nodes[node_type] = {
                    key: value
                }
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
            self.del_in_container(value, self.forest, 'nodes', node_type)
        elif level == DOCUMENT:
            self.del_in_container(value, self.document, 'nodes', node_type)
        else:
            if node_type in self.prefs.nodes and key in self.prefs.nodes[node_type]:
                del self.prefs.nodes[node_type][key]

    def reset_node_setting(self, node_type=None, obj=None, level=OBJECT):
        if not (obj or node_type):
            raise ValueError
        if obj and obj.settings:  # Note that this removes *all* object-level settings.
            obj.poke('settings')
            obj.settings = {}
        elif level == FOREST:
            self.reset_in_container(self.forest, 'nodes', node_type, level, self.node_type_chains)
        elif level == DOCUMENT:
            self.reset_in_container(self.document, 'nodes', node_type, level, self.node_type_chains)

    def get_shape_setting(self, key, edge_type=None, level=HIGHEST):
        # print('get_shape_setting ', key, edge_type, edge, level)
        if level == HIGHEST or level == FOREST:
            return self.flat_shape_settings[edge_type][key]
        elif level == DOCUMENT:
            if key in self.edge_type_chains[edge_type].maps[chain_level[DOCUMENT]]:
                return self.edge_type_chains[edge_type].maps[chain_level[DOCUMENT]][key]
        shape_name = self.get_edge_setting('shape_name', edge_type=edge_type, level=level)
        return SHAPE_PRESETS[shape_name].defaults[key]

    @time_me
    def set_shape_setting(self, key, value, edge_type=None, edge=None, level=HIGHEST):
        if level != PREFS:
            self.set_edge_setting(key, value, edge_type=edge_type, edge=edge, level=level)
        else:
            pass
        self.flatten_shape_settings(edge_type)
        for edge in ctrl.forest.edges.values():
            if edge.edge_type == edge_type:
                edge.flatten_settings()

    def flatten_shape_settings(self, edge_type):
        shape_name = self.get_edge_setting('shape_name', edge_type=edge_type, level=HIGHEST)
        shape = SHAPE_PRESETS[shape_name]
        chain_parts = self.edge_type_chains[edge_type].maps
        flattened = dict(shape.defaults)
        flattened.update(chain_parts[1])
        flattened.update(chain_parts[0])
        self.flat_shape_settings[edge_type] = flattened
        return flattened

# def remove_all_shape_settings(self, edge=None, edge_type=None):
    #     if edge:
    #         edge_type = edge.edge_type
    #         shape_name = edge.shape_name
    #         edges = [edge]
    #     elif edge_type:
    #         shape_name = self.get_edge_setting('shape_name')
    #         edges = [e for e in ctrl.forest.edges.values() if e.edge_type == edge_type]
    #     keys = SHAPE_PRESETS[shape_name].defaults.keys()
    #     chain = self.shape_type_chains[edge_type]
    #     for key in keys:
    #         for ed in edges:
    #             if key in ed.settings:
    #                 ed.poke('settings')
    #                 del ed.settings[key]
    #         if key in chain.maps[0]:
    #             self.forest.poke('settings')
    #             del chain.maps[0][key]
    #         if key in chain.maps[1]:
    #             self.document.poke('settings')
    #             del chain.maps[1][key]

    def get_active_setting(self, key):
        """ Shortcut for get(key, obj=None, level=ctrl.ui.active_scope)
        :param key:
        :return:
        """
        return self.get(key, obj=None, level=ctrl.ui.active_scope)

    def get_active_node_setting(self, key, of_type):
        """ Return node setting either from selected items or from ui.active_scope. If there
        are settings made in node level, return first of such occurence.
        :param key:
        :param of_type:
        :return:
        """
        if self.ui.scope_is_selection:
            typical_node = None
            for node in ctrl.get_selected_nodes(of_type=of_type):
                if key in node.settings:
                    return node.settings[key]
                if not typical_node:
                    typical_node = node
            if typical_node:
                return self.get_node_setting(key, node=typical_node)
            level = HIGHEST
        else:
            level = ctrl.ui.active_scope
        return self.get_node_setting(key, node_type=of_type, level=level)
