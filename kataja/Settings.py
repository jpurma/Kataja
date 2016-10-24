from kataja.singletons import ctrl
import copy

from kataja.Shapes import SHAPE_PRESETS

HIGHEST = 0
OBJECT = 1
SELECTION = 2
FOREST = 3
DOCUMENT = 4
PREFS = 5

CONFLICT = 666666


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
        self.s_unified = {}
        self.s_forest = {}
        self.s_document = {}
        self.prefs = None

    def set_prefs(self, prefs):
        self.prefs = prefs

    def set_document(self, document):
        self.s_document = document.settings
        self.s_forest = {}
        self.s_unified = {}

    def set_forest(self, forest):
        self.s_forest = forest.settings
        self.s_unified = {}

    def get(self, key, level=HIGHEST, obj=None, ignore_selection=False):
        if obj:
            if level == HIGHEST:
                if key in obj.settings:
                    return obj.settings[key]
            elif level == OBJECT:
                return obj.settings.get(key, None)
        elif not ignore_selection:
            if level == HIGHEST:
                if key in self.s_unified:
                    return self.s_unified[key]
            elif level == SELECTION:
                return self.s_unified.get(key, None)
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
        if level == OBJECT:
            if not obj:
                raise ValueError
            if obj.can_have_setting(key):
                obj.settings[key] = value
        elif level == FOREST:
            self.s_forest[key] = value
        elif level == DOCUMENT:
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

    def update_selection(self):
        """ Make a new s_unified -dict that combines the settings of all selected objects. If there
        are conflicting settings in selection, these will have value CONFLICT. If no selection, this
        dict is empty.
        Settings of selection should only be used for updating UI dials.
        :return:
        """
        new_d = {}
        for item in ctrl.selected:
            for key, value in item.settings.items():
                if isinstance(value, dict):
                    n_d = {}
                    for k, v in value.items():
                        if key in new_d \
                                and isinstance(new_d[key], dict)\
                                and new_d[key].get(k, None) != v:
                            n_d[k] = CONFLICT
                        else:
                            n_d[k] = v
                    new_d[key] = n_d
                else:
                    if key in new_d and new_d[key] != value:
                        new_d[key] = CONFLICT
                    else:
                        new_d[key] = value
        if new_d:
            print(new_d)
        self.s_unified = new_d

    # Those settings that are represented by dict need special methods to get/set/delete, as having
    # some dict set is not enough, one has to check if the dict has necessary key and traverse
    # deeper if that is not the case.

    # Edge settings are stored directly in Edge.settings, but in settings['edges'][edge_type]
    # in layers below.

    def get_edge_setting(self, key, edge_type=None, edge=None, level=HIGHEST):
        if edge:
            edge_type = edge.edge_type
        return self._get_dict_setting(key, subtype=edge_type, obj=edge, level=level,
                                      dictname='edges')

    def set_edge_setting(self, key, value, edge_type=None, edge=None, level=OBJECT):
        self._set_dict_setting(key, value, subtype=edge_type, obj=edge, level=level,
                               dictname='edges')

    def del_edge_setting(self, key, edge_type=None, edge=None, level=OBJECT):
        self._del_dict_setting(key, subtype=edge_type, obj=edge, level=level, dictname='edges')

    # Node settings are stored directly in Node.settings, but in settings['nodes'][node_type]
    # in layers below.

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

    def get_shape_setting(self, key, edge_type=None, edge=None, level=HIGHEST):
        v = self.get_edge_setting(key, edge_type=edge_type, edge=edge, level=level)
        if v is not None:
            return v
        sn = self.get_edge_setting('shape_name', edge_type=edge_type, edge=edge, level=level)
        return getattr(SHAPE_PRESETS[sn], key)

    def _get_dict_setting(self, key, subtype=None, obj=None, level=HIGHEST, dictname=None):
        if not (subtype or obj):
            raise ValueError
        if obj:
            if level == HIGHEST:
                if key in obj.settings:
                    return obj.settings[key]
            elif level == OBJECT:
                return obj.settings.get(key, None)
        else:
            if level == HIGHEST:
                if key in self.s_unified:
                    return self.s_unified[key]
            elif level == SELECTION:
                return self.s_unified.get(key, None)
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
            obj.settings[key] = value
        elif level == FOREST:
            if dictname not in self.s_forest:
                self.s_forest[dictname] = {subtype: {key: value}}
            elif subtype not in self.s_forest[dictname]:
                self.s_forest[dictname][subtype] = {key: value}
            else:
                self.s_forest[dictname][subtype][key] = value
        elif level == DOCUMENT:
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
            del obj.settings[key]
        elif level == FOREST:
            if dictname in self.s_forest:
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
                d = self.s_document[dictname]
                if subtype in d:
                    if key in d[subtype]:
                        del d[subtype][key]
                        if not d[subtype]:
                            del d[subtype]
                if not d:
                    del self.s_document[dictname]

