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

from PyQt5 import QtWidgets, QtCore, QtGui

from PyQt5.QtCore import QPointF, QPoint

import kataja.globals as g


def colored_image(color, base_image):
    image = QtGui.QImage(base_image)
    painter = QtGui.QPainter(image)
    painter.setRenderHint(QtGui.QPainter.Antialiasing)
    painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
    painter.fillRect(image.rect(), color)
    painter.end()
    return image


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

    def wrap(*arg, **kwargs):
        """

        :param arg:
        :return:
        """
        if len(traceback.extract_stack()) > 1:
            mod, line, fun, cmd = traceback.extract_stack()[-2]
            print("%s was called by %s l.%s at %s" % (function.__name__, cmd, line, mod))
        return function(*arg, **kwargs)

    return wrap


def time_me(function):
    """ Print out the duration in ms it takes to run this function.
    You know, for debugging!
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


def report(function):
    """ Print out the name of function and representation (__repr__) of its returned value.
    You know, for debugging!
    :param function:
    :return:
    """

    def wrap(*arg, **kwargs):
        """

        :param arg:
        :param kwargs:
        :return:
        """
        r = function(*arg, **kwargs)
        print("%s: %r" % (function.__name__, r))
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
            classname = obj.split('_')[1][1:]  # _*[classname]ui_key
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


def find_free_filename(fixed_part, extension, counter=0):
    """ Generate file names until free one is found """
    if not counter:
        fpath = fixed_part + extension
    else:
        fpath = fixed_part + str(counter) + extension
    if os.path.exists(fpath):
        fpath = find_free_filename(fixed_part, extension, counter + 1)
    return fpath


# def linearize(node):
# res = []
# for n in node:
# if n not in res:
# res.append(n)
# return res

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


def quit():
    """


    """
    sys.exit()


def create_blur_effect():
    """ Prepare a blur effect, good for moving things.
    :return: QGraphicsBlurEffect
    """
    effect = QtWidgets.QGraphicsBlurEffect()
    effect.setBlurHints(QtWidgets.QGraphicsBlurEffect.QualityHint)
    effect.setBlurRadius(3)
    effect.setEnabled(False)
    return effect

def create_shadow_effect(color):
    """ Prepare shadow effect for highlighting
    :param color: color of effect
    :return: QGraphicsDropShadowEffect
    """
    effect = QtWidgets.QGraphicsDropShadowEffect()
    effect.setBlurRadius(10)
    effect.setColor(color)
    effect.setOffset(0, 5)
    effect.setEnabled(False)
    return effect


def print_transform(transform):
    """

    :param transform:
    """
    t = transform

    print('m11:%s m12:%s m13:%s | m21:%s m22:%s m23:%s | m31:%s m32:%s m33:%s | dx:%s dy:%s' % (
        t.m11(), t.m12(), t.m13(), t.m21(), t.m22(), t.m23(), t.m31(), t.m32(), t.m33(), t.dx(), t.dy()))
    print('isRotating:%s isScaling:%s isTranslating:%s' % (t.isRotating(), t.isScaling(), t.isTranslating()))




def add_xy(a, b):
    """
    :rtype : tuple
    """
    return a[0] + b[0], a[1] + b[1]


def div_xy(a, div):
    """
    :rtype : tuple
    """
    return a[0] / div, a[1] / div


def multiply_xy(a, mul):
    """
    :rtype : tuple
    """
    return a[0] * mul, a[1] * mul


def open_symbol_data(mimedata):
    # strange fuckery required
    ba = mimedata.data("application/x-qabstractitemmodeldatalist")
    ds = QtCore.QDataStream(ba)
    data = {}
    while not ds.atEnd():
        row = ds.readInt32()
        column = ds.readInt32()
        map_items = ds.readInt32()
        for i in range(map_items):
            key = ds.readInt32()
            value = QtCore.QVariant()
            ds >> value
            data[key] = value.value()
    if 55 in data:
        return data[55]


def guess_node_type(text):

    text = text.strip()
    if text.startswith('['):
        return g.TREE
    if text.startswith('#'):
        return g.COMMENT_NODE
    if '=' in text:
        return g.FEATURE_NODE
    elif ':' in text:
        return g.FEATURE_NODE
    spaced = text.split()
    if len(spaced) > 1:
        return g.TREE
    else:
        return g.CONSTITUENT_NODE


def combine_dicts(primary, secondary):
    """ Take two dicts and return one that key:value pairs from both, but if they share a key,
    and values are dicts, combine these too.
    :param primary: dict that overwrites
    :param secondary: dict that is overwritten
    :return: combined dict
    """
    if not primary:
        return secondary.copy()
    elif not secondary:
        return primary.copy()

    combo = secondary.copy()
    for key, value in primary.items():
        if isinstance(value, dict):
            combo[key] = combine_dicts(value, secondary.get(key, {}))
        else:
            combo[key] = value
    return combo


def combine_lists(primary, secondary):
    """ Take two lists and append the second to first, but don't let it repeat items.
    :param primary:
    :param secondary:
    :return:
    """
    combo = list(primary)
    for item in secondary:
        if item not in primary:
            combo.append(item)
    return combo

