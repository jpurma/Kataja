from kataja.singletons import ctrl
import copy

from kataja.Shapes import SHAPE_PRESETS, SHAPE_DICT
from kataja.utils import time_me
from kataja.saved.movables.Node import Node
from kataja.saved.Edge import Edge
from kataja.globals import HIGHEST, FOREST, DOCUMENT, PREFS, OBJECT, SELECTION


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
        self.document = None
        self.forest = None
        self.s_forest = {}
        self.s_document = {}
        self.prefs = None
        self.ui = None
        self._shape_cache = {}

    def set_prefs(self, prefs):
        self.prefs = prefs

    def set_ui_manager(self, ui_manager):
        self.ui = ui_manager

    def set_document(self, document):
        self.document = document
        self.forest = None
        self.s_document = document.settings
        self.s_forest = {}
        self._shape_cache = {}

    def set_forest(self, forest):
        self.forest = forest
        self.s_forest = forest.settings
        self.update_shape_cache()

    #@time_me
    def get(self, key, level=HIGHEST, obj=None):
        #print('get setting, key:%s, level:%s, obj:%s' % (key, level, obj))
        if obj:
            print('settings.get with object:', obj)
            raise hell
            if level == HIGHEST:
                if key in obj.settings:
                    return obj.settings[key]
        if level == HIGHEST:
            if key in self.s_forest:
                return self.s_forest[key]
            elif key in self.s_document:
                return self.s_document[key]
            return getattr(self.prefs, key)
        elif level == FOREST:
            return self.s_forest.get(key, None)
        elif level == DOCUMENT:
            return self.s_document.get(key, None)
        elif level == PREFS:
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
                self.s_forest[key] = value
        elif level == DOCUMENT:
            self.document.poke('settings')
            self.s_document[key] = value
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
            if key in self.s_forest:
                del self.s_forest[key]
        elif level == DOCUMENT:
            if key in self.s_document:
                del self.s_document[key]

    # Those settings that are represented by dict need special methods to get/set/delete, as having
    # some dict set is not enough, one has to check if the dict has necessary key and traverse
    # deeper if that is not the case.

    # Edge settings are stored directly in Edge.settings, but in settings['edges'][edge_type]
    # in layers below.

    #@time_me
    def get_edge_setting(self, key, edge_type=None, edge=None, level=HIGHEST):
        if edge:
            edge_type = edge.edge_type
        return self._get_dict_setting(key, subtype=edge_type, obj=edge, level=level,
                                      dictname='edges')

    def set_edge_setting(self, key, value, edge_type=None, edge=None, level=OBJECT):
        self._set_dict_setting(key, value, subtype=edge_type, obj=edge, level=level,
                               dictname='edges')
        if level != OBJECT:
            self.update_shape_cache()

    def del_edge_setting(self, key, edge_type=None, edge=None, level=OBJECT):
        self._del_dict_setting(key, subtype=edge_type, obj=edge, level=level, dictname='edges')

    def reset_edge_settings(self, edge_type=None, edge=None, level=OBJECT):
        self._reset_subtype_dict(subtype=edge_type, obj=edge, level=level, dictname='edges')
        self.update_shape_cache()

    # Node settings are stored directly in Node.settings, but in settings['nodes'][node_type]
    # in layers below.

    #@time_me
    def get_node_setting(self, key, node_type=None, node=None, level=HIGHEST):
        if node:
            node_type = node.node_type
        return self._get_dict_setting(key, subtype=node_type, obj=node, level=level,
                                      dictname='nodes')

    def set_node_setting(self, key, value, node_type=None, node=None, level=OBJECT):
        self._set_dict_setting(key, value, subtype=node_type, obj=node, level=level,
                               dictname='nodes')

    def del_node_setting(self, key, node_type=None, node=None, level=OBJECT):
        self._del_dict_setting(key, subtype=node_type, obj=node, level=level, dictname='nodes')

    def reset_node_settings(self, node_type=None, node=None, level=OBJECT):
        self._reset_subtype_dict(subtype=node_type, obj=node, level=level, dictname='nodes')

    #@time_me
    def get_shape_setting(self, key, edge_type=None, edge=None, level=HIGHEST, shape_name=None):
        v = self.get_edge_setting(key, edge_type=edge_type, edge=edge, level=level)
        if v is not None:
            return v
        if not shape_name:
            shape_name = self.get_edge_setting('shape_name', edge_type=edge_type, edge=edge,
                                               level=level)
        return getattr(SHAPE_PRESETS[shape_name], key)

    #@time_me
    def cached_edge(self, key, edge, missing=None):
        if key in edge.settings:
            return edge.settings[key]
        if not self._shape_cache:
            self.update_shape_cache()
        return self._shape_cache[edge.edge_type].get(key, missing)

    def cached_edge_type(self, key, edge_type):
        if not self._shape_cache:
            self.update_shape_cache()
        return self._shape_cache[edge_type][key]

    def cached_active_edge(self, key):
        if not self._shape_cache:
            self.update_shape_cache()
        return self._shape_cache[self.ui.active_edge_type][key]

    def active_nodes(self, key):
        """ Return node setting either from selected items or from ui.active_node_type.
        :param key:
        :return:
        """
        if self.ui.scope_is_selection:
            typical_node = None
            for node in ctrl.selected:
                if isinstance(node, Node):
                    if key in node.settings:
                        return node.settings[key]
                    if not typical_node:
                        typical_node = node
            if typical_node:
                return self.get_node_setting(key, node_type=typical_node.node_type)
        return self.get_node_setting(key, node_type=self.ui.active_node_type)

    def active_edges(self, key):
        """ Return edge setting either from selected items or from ui.active_edge_type
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
                return self.cached_edge(key, typical_edge)
        return self.cached_active_edge(key)


    # ## ### Deep diggers

    def _get_dict_setting(self, key, subtype=None, obj=None, level=HIGHEST, dictname=None):
        if obj:
            if level == HIGHEST:
                if key in obj.settings:
                    return obj.settings[key]
            elif level == OBJECT:
                return obj.settings.get(key, None)
        if level == HIGHEST:
            if dictname in self.s_forest and subtype in self.s_forest[dictname] \
                    and key in self.s_forest[dictname][subtype]:
                return self.s_forest[dictname][subtype][key]
            if dictname in self.s_document and subtype in self.s_document[dictname] \
                    and key in self.s_document[dictname][subtype]:
                return self.s_document[dictname][subtype][key]
            d = getattr(self.prefs, dictname, None)
            if d:
                dd = d.get(subtype, None)
                if dd:
                    return dd.get(key, None)
            return None
        elif level == FOREST:
            if dictname in self.s_forest and subtype in self.s_forest[dictname]:
                return self.s_forest[dictname][subtype].get(key, None)
        elif level == DOCUMENT:
            if dictname in self.s_document and subtype in self.s_document[dictname]:
                return self.s_document[dictname][subtype].get(key, None)
        elif level == PREFS:
            d = getattr(self.prefs, dictname, None)
            if d:
                dd = d.get(subtype, None)
                if dd:
                    return dd.get(key, None)
        return None

    def _set_dict_setting(self, key, value, subtype=None, obj=None, level=OBJECT, dictname=None):
        if not (obj or subtype):
            raise ValueError
        if obj:
            obj.poke('settings')
            obj.settings[key] = value
        elif level == FOREST:
            self.forest.poke('settings')
            if dictname not in self.s_forest:
                self.s_forest[dictname] = {subtype: {key: value}}
            elif subtype not in self.s_forest[dictname]:
                self.s_forest[dictname][subtype] = {key: value}
            else:
                self.s_forest[dictname][subtype][key] = value
        elif level == DOCUMENT:
            self.document.poke('settings')
            if dictname not in self.s_document:
                self.s_document[dictname] = {subtype: {key: value}}
            elif subtype not in self.s_forest[dictname]:
                self.s_document[dictname][subtype] = {key: value}
            else:
                self.s_document[dictname][subtype][key] = value
        elif level == PREFS:
            d = getattr(self.prefs, dictname)
            if subtype not in d:
                d[subtype] = {key: value}
            else:
                d[subtype][key] = value

    def _del_dict_setting(self, key, subtype=None, obj=None, level=None, dictname=None):
        if not (obj or subtype):
            raise ValueError
        if obj and key in obj.settings:
            obj.poke('settings')
            del obj.settings[key]
        elif level == FOREST:
            if dictname in self.s_forest:
                self.forest.poke('settings')
                d = self.s_forest[dictname]
                if subtype in d:
                    if key in d[subtype]:
                        del d[subtype][key]
                        if not d[subtype]:
                            del d[subtype]
                if not d:
                    del self.s_forest[dictname]
        elif level == DOCUMENT:
            if dictname in self.s_document:
                self.document.poke('settings')
                d = self.s_document[dictname]
                if subtype in d:
                    if key in d[subtype]:
                        del d[subtype][key]
                        if not d[subtype]:
                            del d[subtype]
                if not d:
                    del self.s_document[dictname]

    def _reset_subtype_dict(self, subtype=None, obj=None, level=None, dictname=None):
        if not (obj or subtype):
            raise ValueError
        if obj and obj.settings: # Note that this removes *all* object-level settings.
            obj.poke('settings')
            obj.settings = {}
        elif level == FOREST:
            if dictname in self.s_forest:
                self.forest.poke('settings')
                d = self.s_forest[dictname]
                if subtype in d:
                    del d[subtype]
                if not d:
                    del self.s_forest[dictname]
        elif level == DOCUMENT:
            if dictname in self.s_document:
                self.document.poke('settings')
                d = self.s_document[dictname]
                if subtype in d:
                    del d[subtype]
                if not d:
                    del self.s_document[dictname]

    # ## Shape cache #########

    @time_me
    def update_shape_cache(self):
        new = self.prefs.edges.copy()
        if 'edges' in self.s_document:
            for edge_type, edge_data in self.s_document['edges'].items():
                new[edge_type].update(edge_data)
        if 'edges' in self.s_forest:
            for edge_type, edge_data in self.s_forest['edges'].items():
                new[edge_type].update(edge_data)
        for edge_type, edge_data in new.items():
            shape_data = SHAPE_DICT[edge_data['shape_name']].copy()
            shape_data.update(edge_data)
            new[edge_type] = shape_data
        self._shape_cache = new

