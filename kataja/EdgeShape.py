# coding=utf-8
from kataja.shapes import SHAPE_PRESETS
from kataja.singletons import ctrl
from kataja.utils import time_me


class EdgeShape:
    """ Helper class to gather all shape-related setters and getters. The data itself is saved as
    a dict in host object (Edge) so that the save file won't multiply its number of objects.
    """

    def __init__(self, edge):
        self.host = edge

    def copy(self):
        return self.shape_info().copy()

    def get_edge_info(self, key):
        value = self.host.local_shape_info.get(key, None)
        if value is None:
            return ctrl.fs.edge_info(self.host.edge_type, key)
        else:
            return value

    def has_arrowhead_at_start(self):
        return self.get_edge_info('arrowhead_at_start')

    def set_arrowhead_at_start(self, value):
        self.host.poke('local_shape_info')
        self.host.local_shape_info['arrowhead_at_start'] = value

    def has_arrowhead_at_end(self):
        return self.get_edge_info('arrowhead_at_start')

    def set_arrowhead_at_end(self, value):
        self.host.poke('local_shape_info')
        self.host.local_shape_info['arrowhead_at_end'] = value

    def set_leaf_width(self, value):
        self.set_shape_info('leaf_x', value)
        self.host.update_shape()

    def set_leaf_height(self, value):
        self.set_shape_info('leaf_y', value)
        self.host.update_shape()

    def reset_leaf_shape(self):
        self.reset_shape_info('leaf_x', 'leaf_y')
        self.host.update_shape()

    def change_edge_relative_curvature_x(self, value):
        self.set_shape_info('rel_dx', value * .01)
        self.host.update_shape()

    def change_edge_relative_curvature_y(self, value):
        self.set_shape_info('rel_dy', value * .01)
        self.host.update_shape()

    def change_edge_fixed_curvature_x(self, value):
        self.set_shape_info('fixed_dx', value)
        self.host.update_shape()

    def change_edge_fixed_curvature_y(self, value):
        self.set_shape_info('fixed_dy', value)
        self.host.update_shape()

    def change_edge_curvature_reference(self, value):
        self.set_shape_info('relative', value == 'relative')
        self.host.update_shape()

    def reset_edge_curvature(self):
        self.reset_shape_info('rel_dx', 'rel_dy', 'fixed_dx', 'fixed_dy', 'relative')
        self.host.update_shape()

    def reset_thickness(self):
        self.reset_shape_info('thickness')
        self.host.update_shape()

    def change_thickness(self, value):
        self.set_shape_info('thickness', value)
        self.host.update_shape()

    def reset_shape_info(self, *args):
        """ Remove local settings for shape args
        :param args:
        :return:
        """
        for key in args:
            if key in self.host.local_shape_info:
                self.host.poke('local_shape_info')
                del self.host.local_shape_info[key]

    def shape_info(self, key=None):
        """ Without key, return a dict of shape drawing arguments that should
        be used with shape drawing method.
        With key, give a certain shape_arg.
        :param key:
        :return:
        """
        e = self.host
        if key is None:
            shape_info = ctrl.fs.shape_info(e.edge_type)
            if e.local_shape_info:
                sa = shape_info.copy()
                sa.update(e.local_shape_info)
                return sa
            else:
                return shape_info
        else:
            local = e.local_shape_info.get(key, None)
            if local is not None:
                return local
            else:
                # if this edge type uses different shape in settings,
                # this should get the shape preset value and not shape settings
                # value.
                if ctrl.fs.shape_for_edge(e.edge_type) != e.shape_name:
                    return SHAPE_PRESETS[e.shape_name][key]
                else:
                    return ctrl.fs.shape_info(e.edge_type, key)

    def set_shape_info(self, key=None, value=None):
        """ Set local settings for shape. These override shape settings from
        forest or from preferences.
        :param key:
        :param value:
        :return:
        """
        self.host.poke('local_shape_info')
        self.host.local_shape_info[key] = value

    def prepare_adjust_array(self, index):
        """

        :param index:
        """
        if self.host.curve_adjustment is None:
            self.host.curve_adjustment = [(0, 0)] * (index + 1)
        elif index >= len(self.host.curve_adjustment):
            self.host.curve_adjustment += [(0, 0)] * (index - len(self.host.curve_adjustment) + 1)

    def adjust_control_point(self, index, points):
        """ Called from UI, when dragging
        :param index:
        :param points:
        :param cp:
        """
        x, y = points
        self.host.poke('curve_adjustment')
        self.prepare_adjust_array(index)
        self.host.curve_adjustment[index] = x, y
        self.host.call_watchers('edge_adjustment', 'curve_adjustment', self.host.curve_adjustment)
        self.host.make_path()
        self.host.update()

    def adjust_control_point_x0(self, value):
        """ Called when modifying control point settings directly
        :param value:
        :return:
        """
        self.host.poke('curve_adjustment')
        self.prepare_adjust_array(0)
        x, y = self.host.curve_adjustment[0]
        self.host.curve_adjustment[0] = value, y
        self.host.call_watchers('edge_adjustment', 'curve_adjustment', self.host.curve_adjustment)
        self.host.make_path()
        self.host.update()

    def adjust_control_point_y0(self, value):
        """ Called when modifying control point settings directly
        :param value:
        :return:
        """
        self.host.poke('curve_adjustment')
        self.prepare_adjust_array(0)
        x, y = self.host.curve_adjustment[0]
        self.host.curve_adjustment[0] = x, value
        self.host.call_watchers('edge_adjustment', 'curve_adjustment', self.host.curve_adjustment)
        self.host.make_path()
        self.host.update()

    def adjust_control_point_x1(self, value):
        """ Called when modifying control point settings directly
        :param value:
        :return:
        """
        self.host.poke('curve_adjustment')
        self.prepare_adjust_array(1)
        x, y = self.host.curve_adjustment[1]
        self.host.curve_adjustment[1] = value, y
        self.host.call_watchers('edge_adjustment', 'curve_adjustment', self.host.curve_adjustment)
        self.host.make_path()
        self.host.update()

    def adjust_control_point_y1(self, value):
        """ Called when modifying control point settings directly
        :param value:
        :return:
        """
        self.host.poke('curve_adjustment')
        self.prepare_adjust_array(1)
        x, y = self.host.curve_adjustment[1]
        self.host.curve_adjustment[1] = x, value
        self.host.call_watchers('edge_adjustment', 'curve_adjustment', self.host.curve_adjustment)
        self.host.make_path()
        self.host.update()

    def reset_control_points(self):
        """
        Set adjustments back to zero
        :return:
        """

        n = self.shape_info('control_points')
        self.host.poke('curve_adjustment')
        self.host.curve_adjustment = [(0, 0)] * n
        self.host.make_path()
        self.host.update()
