# coding=utf-8
""" helper methods for syntax """
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
#############################################################################

import time
import traceback

from PyQt6.QtCore import QPointF, QPoint


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
            print("%s was called by %s l.%s at %s %s" % (function.__name__, cmd, line, mod, fun))
        return function(*arg)

    return wrap


def time_me(function):
    """

    :param function:
    :return:
    """

    def wrap(*arg):
        """

        :param arg:
        :return:
        """
        start = time.time()
        r = function(*arg)
        end = time.time()
        print("%s (%0.3f ms)" % (function.__name__, (end - start) * 1000))
        return r

    return wrap


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


def save_features(obj, saved, d):
    """

    :param obj:
    :param saved:
    :param d:
    :return:
    """

    def save_feature(feat):
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
        sob[feat] = save_feature(feat)
    d[key] = sob
    return key
