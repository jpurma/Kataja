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

from types import FrameType
import gc
import string
import sys
import time
import traceback

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QPointF, QPoint


def print_rect(rect):
    """

    :param rect:
    """
    print('x: %s y: %s width: %s height: %s' % (rect.x(), rect.y(), rect.width(), rect.height()))


def caller(function):
    """

    :param function:
    :return:
    """

    def wrap(*arg):
        """

        :param arg:
        :return:
        """
        if len(traceback.extract_stack()) > 1:
            mod, line, fun, cmd = traceback.extract_stack()[-2]
            print("%s was called by %s l.%s at %s" % (function.__name__, cmd, line, mod))
        return function(*arg)

    return wrap


def time_me(function):
    """

    :param function:
    :return:
    """

    def wrap(*arg, **kwargs):
        """

        :param arg:
        :param kwargs:
        :return:
        """
        start = time.time()
        r = function(*arg, **kwargs)
        end = time.time()
        print("%s (%0.3f ms) at %s" % (function.__name__, (end - start) * 1000, function.__module__))
        return r

    return wrap


def to_tuple(p):
    """ PySide's to_tuple-helper method for PyQt
    :param p:
    """
    return p.x(), p.y()


# not used
def load_features(obj, key, d):
    """

    :param obj:
    :param key:
    :param d:
    :return:
    """
    if (isinstance(obj, str) or isinstance(obj, str)) and obj.startswith('_*'):
        if isinstance(d[obj], str) or isinstance(d[obj], str):
            classname = obj.split('_')[1][1:]  # _*[classname]_id
            obj = eval(classname + '()')
            d[obj] = load_features(obj, obj, d)
        obj = d[obj]
    setattr(obj, key, obj)
    return obj


# not used
def save_features(obj, saved, d):
    """

    :param obj:
    :param saved:
    :param d:
    :return:
    """

    def _save_feature(feat):
        """

        :param feat:
        :return:
        """
        fval = getattr(obj, feat)
        try:
            return fval.save(d)
        except AttributeError:
            if isinstance(fval, QPointF) or isinstance(fval, QPoint):
                return fval.x(), fval.y()
            if isinstance(fval, list):
                nval = []
                for item in fval:
                    try:
                        nval.append(item.save(d))
                    except AttributeError:
                        nval.append(item)
                return nval
            elif isinstance(fval, dict):
                nval = {}
                for ikey, item in fval.items():
                    try:
                        nval[ikey] = item.save(d)
                    except AttributeError:
                        nval[ikey] = item
                return nval
            else:
                return fval

    key = '_*%s_%s' % (obj.__class__.__name__, id(obj))
    if key in d:
        return key
    sob = {}
    d[key] = sob
    for feat in saved:
        sob[feat] = _save_feature(feat)
    d[key] = sob
    return key


# used only in syntax
def load_lexicon(filename, Constituent, Feature):
    """

    :param filename:
    :param Constituent:
    :param Feature:
    :return:
    """
    dict = {}
    try:
        file = open(filename, 'r')
    except IOError:
        print('FileNotFound: %s' % filename)
        return dict
    constituent = None
    constituent_id = ''
    for line in file.readlines():
        line = line.strip()
        if line.startswith('#'):
            continue

        split_char = ''
        for letter in line:
            if letter == '+' or letter == '-' or letter == '=':
                split_char = letter
                break
        if split_char and constituent:
            splitted = line.split(split_char, 1)
            key, value_list = splitted[0].strip(), splitted[1].strip().split(' ')
            base_value = split_char
            feature = Feature(key, base_value)
            constituent.set_feature(key, feature)
            # print "added feature %s:%s to '%s'" % (key, base_value, constituent.id)

        else:
            constituent_id = line.strip()
            if constituent_id:
                constituent = Constituent(constituent_id)
                dict[constituent_id] = constituent
    return dict


# used only in syntax
def save_lexicon(lexicon, filename):
    """

    :param lexicon:
    :param filename:
    :return:
    """
    try:
        file = open(filename, 'w')
    except IOError:
        print('IOError: %s' % filename)
        return
    keys = list(lexicon.keys())
    keys.sort()
    for key in keys:
        constituent = lexicon[key]
        file.write('%s\n' % key)
        for feature in constituent.get_features().values():
            file.write('%s\n' % feature)
        file.write('\n')
    file.close()


# def linearize(node):
# res = []
# for n in node:
# if n not in res:
# res.append(n)
#    return res

def next_free_index(indexes):
    """

    :param indexes:
    :return:
    """
    letters = [c for c in indexes if len(c) == 1 and c in string.ascii_letters]
    # 1 -- default i
    if not letters:
        return 'i'
    # 2 -- see if there is existing pattern and continue it
    letters.sort()
    last_index = string.ascii_letters.index(letters[-1])
    if len(string.ascii_letters) > last_index + 2:
        return string.ascii_letters[last_index + 1]
    else:
        # 3 -- try to find first free letter
        for c in string.ascii_letters:
            if c not in letters:
                return c
    # 4 -- return running number
    return len(indexes)


def print_derivation_steps(objects=gc.garbage, outstream=sys.stdout, show_progress=True):
    """



    :param objects:
    :param outstream:
    :param show_progress:
    objects:       A list of objects to find derivation_steps in.  It is often useful
                   to pass in gc.garbage to find the derivation_steps that are
                   preventing some objects from being garbage collected.
    outstream:     The stream for output.
    show_progress: If True, print the number of objects reached as they are
                   found.
    """

    def print_path(path):
        """

        :param path:
        """
        for i, step in enumerate(path):
            # next "wraps around"
            next = path[(i + 1) % len(path)]

            outstream.write("   %s -- " % str(type(step)))
            if isinstance(step, dict):
                for key, val in step.items():
                    if val is next:
                        outstream.write("[%s]" % repr(key))
                        break
                    if key is next:
                        outstream.write("[key] = %s" % repr(val))
                        break
            elif isinstance(step, list):
                outstream.write("[%d]" % step.index(next))
            elif isinstance(step, tuple):
                outstream.write("[%d]" % list(step).index(next))
            else:
                outstream.write(repr(step))
            outstream.write(" ->\n")
        outstream.write("\n")

    def recurse(obj, start, all, current_path):
        """

        :param obj:
        :param start:
        :param all:
        :param current_path:
        """
        if show_progress:
            outstream.write("%d\r" % len(all))

        all[id(obj)] = None

        referents = gc.get_referents(obj)
        for referent in referents:
            # If we've found our way back to the start, this is
            # a derivation_step, so print it out
            if referent is start:
                print_path(current_path)

            # Don't go back through the original list of objects, or
            # through temporary references to the object, since those
            # are just an artifact of the derivation_step detector itself.
            elif referent is objects or isinstance(referent, FrameType):
                continue

            # We haven't seen this object before, so recurse
            elif id(referent) not in all:
                recurse(referent, start, all, current_path + [obj])

    print('gc:', objects)
    for obj in objects:
        outstream.write("Examining: %r\n" % obj)
        recurse(obj, obj, {}, [])


@time_me
def load_objects(start_obj, full_data):
    """ Load and restore objects starting from given obj (probably Forest or KatajaMain instance)
    :param start_obj:
    :param full_data:
    """

    full_map = {}
    restored = {}

    # First we need a full index of objects that already exist within the existing objects.
    # This is to avoid recreating those objects. We just want to modify them
    def map_existing(obj):
        # containers 
        """

        :param obj:
        :return:
        """
        if isinstance(obj, dict):
            for item in obj.values():
                map_existing(item)
            return
        elif isinstance(obj, (list, tuple, set)):
            for item in obj:
                map_existing(item)
            return
        # objects that support saving
        key = getattr(obj, 'save_key', '') or getattr(obj.__class__, 'singleton_key', '')
        if key and key not in full_map:
            full_map[key] = obj
            field_names = obj.__class__.saved_fields
            if isinstance(field_names, str) and field_names == 'all':
                field_names = list(vars(obj).keys())
                field_names.remove('save_key')
            for fname in field_names:
                map_existing(getattr(obj, fname))

    # Restore either takes existing object or creates a new 'stub' object and then loads it with given data
    def restore(obj_key, class_key='', host=None):
        """

        :param obj_key:
        :param class_key:
        :param host:
        :return:
        """
        if obj_key in restored:
            return restored[obj_key]
        obj = full_map.get(obj_key, None)
        restored[obj_key] = obj
        if not obj:
            # needs to create a stub object
            # how can we reach the constructor?
            pass
        obj_data = full_data[obj_key]
        changes = {}
        for key, value in obj_data.items():
            new_value = inflate(value, obj)
            old_value = getattr(obj, key)
            if new_value != old_value:
                changes[key] = (old_value, new_value)
                setattr(obj, key, new_value)
                #print '  in %s set %s to %s, was %s' % (obj_key, key, new_value, old_value)
                #else:
                #    print 'in %s keep %s value %s' % (obj_key, key, old_value)
        #  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # !!! object needs to be finalized after this !!!
        #  !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        if hasattr(obj, 'after_restore'):
            obj.after_restore(changes)
        else:
            print(' *obj %s (%s) after_restore -method missing *' % (obj, type(obj)))
        return obj


    # Recursively turn QObject descriptions back into actual objects and object references back into real objects
    def inflate(data, host_obj):
        """

        :param data:
        :param host_obj:
        :return:
        """
        if isinstance(data, (int, float, str)):
            return data
        elif isinstance(data, dict):
            result = {}
            for key, value in data.items():
                value = inflate(value, host_obj)
                result[key] = value
            return result
        elif isinstance(data, list):
            result = []
            for item in data:
                result.append(inflate(item, host_obj))
            return result
        elif isinstance(data, tuple):
            if data and isinstance(data[0], str) and data[0].startswith('Q'):
                data_type = data[0]
                if data_type == 'QPointF':
                    return QPointF(data[1], data[2])
                elif data_type == 'QPoint':
                    return QPoint(data[1], data[2])
                elif data_type == 'QRectF':
                    return QtCore.QRectF(data[1], data[2], data[3], data[4])
                elif data_type == 'QRect':
                    return QtCore.QRect(data[1], data[2], data[3], data[4])
                elif data_type == 'QColor':
                    return QtGui.QColor(data[1], data[2], data[3], data[4])
                elif data_type == 'QFont':
                    f = QtGui.QFont()
                    f.fromString(data[1])
                    return f
                else:
                    print('unknown QObject: ', data)
            elif data and isinstance(data[0], str) and data[0] == '*ref*':
                return restore(data[1], data[2], host_obj)
            else:
                result = []
                for item in data:
                    result.append(inflate(item, host_obj))
                result = tuple(result)
                return result
        elif isinstance(data, set):
            result = set()
            for item in data:
                result.add(inflate(item, host_obj))
            return result
        elif data is None:
            return data
        return data

    map_existing(start_obj)
    restore(start_obj.save_key)


def save_object(obj, saved_objs, open_refs, ignore=None):
    """

    :param obj:
    :param saved_objs:
    :param open_refs:
    :param ignore:
    :return: :raise:
    """
    if not ignore:
        ignore = []

    def _simplify(data):
        """ Goes through common iterable datatypes and if common Qt types are found, replaces them
        with basic python tuples. 

        If object is one of Kataja's own data classes, then save its save_key
        """

        if isinstance(data, (int, float, str)):
            return data
        elif isinstance(data, dict):
            result = {}
            for key, value in data.items():
                value = _simplify(value)
                result[key] = value
            return result
        elif isinstance(data, list):
            result = []
            for item in data:
                result.append(_simplify(item))
            return result
        elif isinstance(data, tuple):
            result = []
            for item in data:
                result.append(_simplify(item))
            result = tuple(result)
            return result
        elif isinstance(data, set):
            result = set()
            for item in data:
                result.add(_simplify(item))
            return result
        elif data is None:
            return data
        elif isinstance(data, QPointF):
            return 'QPointF', to_tuple(QPointF)
        elif isinstance(data, QPoint):
            return 'QPoint', to_tuple(QPoint)
        elif isinstance(data, QtGui.QColor):
            return 'QColor', data.red(), data.green(), data.blue(), data.alpha()
        elif isinstance(data, QtGui.QPen):
            pass
        elif isinstance(data, QtCore.QRectF):
            return 'QRectF', data.x(), data.y(), data.width(), data.height()
        elif isinstance(data, QtCore.QRect):
            return 'QRect', data.x(), data.y(), data.width(), data.height()
        elif isinstance(data, QtGui.QFont):
            return 'QFont', data.toString()
        elif hasattr(data, 'save_key'):
            key = getattr(data, 'save_key')
            if key not in saved_objs and key not in open_refs:
                open_refs[key] = data
            return '*ref*', key, data.__class__.__name__
        elif hasattr(data.__class__, 'singleton_key'):
            key = getattr(data.__class__, 'singleton_key')
            if key not in saved_objs and key not in open_refs:
                open_refs[key] = data
            return '*ref*', key, data.__class__.__name__
        else:
            print("simplifying unknown data type:", data, type(data))
            return str(data)


    key = getattr(obj.__class__, 'singleton_key', None) or getattr(obj, 'save_key', None)
    if not key:
        print("trying to save object that doesn't support our save protocol:", obj)
        raise Exception("Trying to save object that doesn't support save protocol")
    if key in saved_objs:
        return
    field_names = obj.__class__.saved_fields
    if isinstance(field_names, str) and field_names == 'all':
        field_names = list(vars(obj).keys())
        if 'save_key' in field_names:
            field_names.remove('save_key')
    obj_data = {}
    #print 'working on object %s of type %s' % (obj, type(obj))
    for fname in field_names:
        if fname in ignore:
            continue
        obj_data[fname] = _simplify(getattr(obj, fname))

    saved_objs[key] = obj_data
    if key in open_refs:
        del open_refs[key]


def quit():
    """


    """
    sys.exit()


def create_shadow_effect(obj, ctrl):
    """

    :param obj:
    :param ctrl:
    :return:
    """
    effect = QtWidgets.QGraphicsDropShadowEffect()
    effect.setBlurRadius(20)
    #self.effect.setColor(ctrl.cm().drawing())
    effect.setColor(ctrl.cm().d['white'])
    effect.setOffset(0, 5)
    effect.setEnabled(False)
    return effect
