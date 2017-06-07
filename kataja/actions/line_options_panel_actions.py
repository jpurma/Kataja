# coding=utf-8

import math
from PyQt5 import QtCore
from kataja.KatajaAction import KatajaAction
from kataja.saved.Edge import Edge
import kataja.globals as g

from kataja.singletons import ctrl, log


# ==== Class variables for KatajaActions:
#
# k_action_uid : unique id for calling this action. required, other are optional
# k_command : text used for menu command and log feedback, unless the method returns a fdback string
# k_tooltip : tooltip text for ui element. If not given, uses k_command as tooltip.
# k_undoable : is the action undoable, default is True
# k_shortcut : keyboard shortcut given as string, e.g. 'Ctrl+x'
# k_shortcut_context : can be nothing or 'parent_and_children' if shortcut is active only when the
#                      parent widget is visible and active
# k_checkable : should the action be checkable, default False
#
# ==== Methods:
#
# method : gets called when action is triggered. If it returns a string, this is used as a command
#          feedback string, otherwise k_command is printed to log.
# getter : if there is an UI element that can show state or display value, this method returns the
#          value. These are called quite often, but with values that have to change e.g. when item
#          is dragged, you'll have to update manually.
# enabler : if enabler is defined, the action is active (also reflected into its UI elements) only
#           when enabler returns True
#


# Edge settings

class ChangeEdgeShape(KatajaAction):
    k_action_uid = 'change_edge_shape'
    k_command = 'Change edge shape'
    k_tooltip = 'Change shapes of lines between objects'
    k_undoable = False

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        shape_name = sender.currentData()

        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
            edge_type = None
        else:
            level = ctrl.ui.active_scope
            edge_type = ctrl.ui.active_edge_type
        return [shape_name], {'edge_type': edge_type, 'level': level}

    def method(self, shape_name, edge_type=None, level=None):
        """ Change edge shape for selection or in currently active edge type.
        :param shape_name: str, shape_name from available shapes.
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        if not edge_type:
            edge_type = ctrl.active_edge_type
        if not level:
            level = ctrl.ui_active_scope
        if level == g.SELECTION:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.shape_name = shape_name
                    edge.update_shape()
        else:
            ctrl.settings.set_edge_setting('shape_name', shape_name,
                                           edge_type=edge_type, level=level)
            for edge in ctrl.forest.edges.values():
                edge.update_shape()
        line_options = ctrl.ui.get_panel('LineOptionsPanel')
        if line_options:
            line_options.update_panel()

    def enabler(self):
        return ctrl.ui.has_edges_in_scope()

    def getter(self):
        return ctrl.settings.cached_active_edge('shape_name')


class ChangeEdgeColor(KatajaAction):
    k_action_uid = 'change_edge_color'
    k_command = 'Change edge color'
    k_tooltip = 'Change drawing color for edges'
    k_undoable = False

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        color_key = sender.receive_color_selection()
        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
            edge_type = None
        else:
            level = ctrl.ui.active_scope
            edge_type = ctrl.ui.active_edge_type
        return [color_key], {'edge_type': edge_type, 'level': level}

    def method(self, color_key, edge_type=None, level=None):
        """ Change edge color for selection or in currently active edge type.
        :param color_key: str, color_key from available colors.
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        if not edge_type:
            edge_type = ctrl.active_edge_type
        if not level:
            level = ctrl.ui_active_scope
        # Update color for selected edges
        if level == g.SELECTION:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.color_id = color_key
                    edge.update()
        # ... or update color for all edges of this type
        else:
            ctrl.settings.set_edge_setting('color_id', color_key,
                                           edge_type=edge_type, level=level)
            for edge in ctrl.forest.edges.values():
                edge.update()
        ctrl.call_watchers(self, 'active_edge_color_changed')  # shape_selector needs this

    def enabler(self):
        return ctrl.ui.has_edges_in_scope()

    def getter(self):
        return ctrl.settings.active_edges('color_id')


class EdgeArrowheadStart(KatajaAction):
    k_action_uid = 'edge_arrowhead_start'
    k_command = 'Draw arrowhead at line start'
    k_checkable = True

    def prepare_parameters(self, args, kwargs):
        ah_at_start = args[0]
        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
            edge_type = None
        else:
            level = ctrl.ui.active_scope
            edge_type = ctrl.ui.active_edge_type
        return [ah_at_start], {'edge_type': edge_type, 'level': level}

    def method(self, value: bool, edge_type=None, level=None):
        """ Draw arrowheads at the start of the edge.
        :param value: bool, draw arrowhead or not
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        if not edge_type:
            edge_type = ctrl.active_edge_type
        if not level:
            level = ctrl.ui_active_scope
        if level == g.SELECTION:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_arrowhead_at_start(value)
        else:
            ctrl.settings.set_edge_setting('arrowhead_at_start', value, edge_type=edge_type,
                                           level=level)
            ctrl.forest.redraw_edges(edge_type=edge_type)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope()

    def getter(self):
        return ctrl.settings.active_edges('arrowhead_at_start')


class EdgeArrowheadEnd(KatajaAction):
    k_action_uid = 'edge_arrowhead_end'
    k_command = 'Draw arrowhead at line end'
    k_checkable = True

    def prepare_parameters(self, args, kwargs):
        ah_at_end = args[0]

        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
            edge_type = None
        else:
            level = ctrl.ui.active_scope
            edge_type = ctrl.ui.active_edge_type
        return [ah_at_end], {'edge_type': edge_type, 'level': level}

    def method(self, value: bool, edge_type=None, level=None):
        """ Draw arrowheads at the end of the edge.
        :param value: bool, draw arrowhead or not
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        if not edge_type:
            edge_type = ctrl.active_edge_type
        if not level:
            level = ctrl.ui_active_scope
        if level == g.SELECTION:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_arrowhead_at_end(value)
        else:
            ctrl.settings.set_edge_setting('arrowhead_at_end', value, edge_type=edge_type,
                                           level=level)
            ctrl.forest.redraw_edges(edge_type=edge_type)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope()

    def getter(self):
        return ctrl.settings.active_edges('arrowhead_at_end')


class ResetControlPoints(KatajaAction):
    k_action_uid = 'reset_control_points'
    k_command = 'Reset control point'
    k_tooltip = 'Remove adjustments for these curves'

    def prepare_parameters(self, args, kwargs):
        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
            edge_type = None
        else:
            level = ctrl.ui.active_scope
            edge_type = ctrl.ui.active_edge_type
        return [], {'edge_type': edge_type, 'level': level}

    def method(self, edge_type=None, level=None):
        """ Reset all adjustments for curves in selected edges or this type of edges.
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        if not edge_type:
            edge_type = ctrl.active_edge_type
        if not level:
            level = ctrl.ui_active_scope
        if level == g.SELECTION:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.reset_control_points()
        else:
            for edge in ctrl.forest.edges.values():
                if edge.edge_type == edge_type:
                    edge.reset_control_points()

    def enabler(self):
        return ctrl.ui.has_edges_in_scope()


class ResetEdgeSettings(KatajaAction):
    k_action_uid = 'reset_edge_settings'
    k_command = 'Reset edge settings'
    k_tooltip = 'Reset settings for this type of edges back to defaults'

    def prepare_parameters(self, args, kwargs):
        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
            edge_type = None
        else:
            level = ctrl.ui.active_scope
            edge_type = ctrl.ui.active_edge_type
        return [], {'edge_type': edge_type, 'level': level}

    def method(self, edge_type=None, level=None):
        """ Reset all additional settings in selected edges or for this type of edges.
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        if not edge_type:
            edge_type = ctrl.active_edge_type
        if not level:
            level = ctrl.ui_active_scope
        if level == g.SELECTION:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.reset_shape()
                    ctrl.settings.del_edge_setting('arrowhead_at_start', edge=edge)
                    ctrl.settings.del_edge_setting('arrowhead_at_end', edge=edge)
            ctrl.forest.redraw_edges()
        else:
            ctrl.settings.reset_shape_settings(level=level, edge_type=edge_type)
            ctrl.settings.del_edge_setting('arrowhead_at_start', edge_type=edge_type)
            ctrl.settings.del_edge_setting('arrowhead_at_end', edge_type=edge_type)

            for edge in ctrl.forest.edges.values():
                if edge.edge_type == edge_type:
                    edge.reset_shape()
            ctrl.forest.redraw_edges(edge_type=edge_type)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope()


class LeafShapeX(KatajaAction):
    k_action_uid = 'leaf_shape_x'
    k_command = 'Edge shape width'
    k_tooltip = 'Adjust horizontal thickness of edges'

    def prepare_parameters(self, args, kwargs):
        value = args[0]

        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
            edge_type = None
        else:
            level = ctrl.ui.active_scope
            edge_type = ctrl.ui.active_edge_type
        return [value], {'edge_type': edge_type, 'level': level}

    def method(self, value: int, edge_type=None, level=None):
        """ Adjust horizontal thickness for leaf-shaped edges.
        :param value: int, horizontal thickness of leaf-shaped edge
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        if not edge_type:
            edge_type = ctrl.active_edge_type
        if not level:
            level = ctrl.ui_active_scope
        if level == g.SELECTION:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_leaf_width(value)
        else:
            ctrl.settings.set_edge_setting('leaf_x', value, edge_type=edge_type, level=level)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope() and \
               ctrl.settings.cached_active_edge('fillable')

    def getter(self):
        return ctrl.settings.active_edges('leaf_x')


class LeafShapeY(KatajaAction):
    k_action_uid = 'leaf_shape_y'
    k_command = 'Edge shape height'
    k_tooltip = 'Adjust vertical thickness of edges'

    def prepare_parameters(self, args, kwargs):
        value = args[0]

        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
            edge_type = None
        else:
            level = ctrl.ui.active_scope
            edge_type = ctrl.ui.active_edge_type
        return [value], {'edge_type': edge_type, 'level': level}

    def method(self, value: int, edge_type=None, level=None):
        """ Adjust vertical thickness for leaf-shaped edges.
        :param value: int, vertical thickness of leaf-shaped edge
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        if not edge_type:
            edge_type = ctrl.active_edge_type
        if not level:
            level = ctrl.ui_active_scope
        if level == g.SELECTION:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_leaf_height(value)
        else:
            ctrl.settings.set_edge_setting('leaf_y', value, edge_type=edge_type, level=level)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope() and \
               ctrl.settings.active_edges('fillable')

    def getter(self):
        return ctrl.settings.active_edges('leaf_y')


class EdgeThickness(KatajaAction):
    k_action_uid = 'edge_thickness'
    k_command = 'Edge thickness'
    k_tooltip = 'Adjust fixed thickness for edges'

    def prepare_parameters(self, args, kwargs):
        value = args[0]

        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
            edge_type = None
        else:
            level = ctrl.ui.active_scope
            edge_type = ctrl.ui.active_edge_type
        return [value], {'edge_type': edge_type, 'level': level}

    def method(self, value: float, edge_type=None, level=None):
        """ Edge outline thickness.
        :param value: float, thickness in pixels
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        if not edge_type:
            edge_type = ctrl.active_edge_type
        if not level:
            level = ctrl.ui_active_scope
        if level == g.SELECTION:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_thickness(value)
        else:
            ctrl.settings.set_edge_setting('thickness', value, edge_type=edge_type, level=level)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope() and \
               ctrl.settings.active_edges('outline')

    def getter(self):
        return ctrl.settings.active_edges('thickness')


class EdgeCurvatureRelative(KatajaAction):
    k_action_uid = 'edge_curvature_relative'
    k_command = 'Change line curvature to be relative to edge dimensions'
    k_checkable = True

    def prepare_parameters(self, args, kwargs):
        value = args[0]

        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
            edge_type = None
        else:
            level = ctrl.ui.active_scope
            edge_type = ctrl.ui.active_edge_type
        return [value], {'edge_type': edge_type, 'level': level}

    def method(self, value: bool, edge_type=None, level=None):
        """ Is edge curvature a fixed amount (False) or relative to edge length (True)
        :param value: bool, True = relative, False = fixed
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        if not edge_type:
            edge_type = ctrl.active_edge_type
        if not level:
            level = ctrl.ui_active_scope
        if level == g.SELECTION:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_edge_curvature_relative(value)
        else:
            ctrl.settings.set_edge_setting('relative', value, edge_type=edge_type, level=level)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope() and \
               ctrl.settings.active_edges('relative') is not None and \
               ctrl.settings.active_edges('control_points')

    def getter(self):
        return ctrl.settings.active_edges('relative')


class EdgeCurvatureFixed(KatajaAction):
    k_action_uid = 'edge_curvature_fixed'
    k_command = 'Change line curvature to be a pair of fixed values'
    k_checkable = True

    def prepare_parameters(self, args, kwargs):
        value = args[0]

        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
            edge_type = None
        else:
            level = ctrl.ui.active_scope
            edge_type = ctrl.ui.active_edge_type
        return [value], {'edge_type': edge_type, 'level': level}

    def method(self, value: bool, edge_type=None, level=None):
        """ Is edge curvature a fixed amount (True) or relative to edge length (False)
        :param value: bool, True = fixed, False = relative
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        if not edge_type:
            edge_type = ctrl.active_edge_type
        if not level:
            level = ctrl.ui_active_scope
        if level == g.SELECTION:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_edge_curvature_relative(not value)
        else:
            ctrl.settings.set_edge_setting('relative', not value, edge_type=edge_type, level=level)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope() and \
               ctrl.settings.active_edges('relative') is not None and \
               ctrl.settings.active_edges('control_points')

    def getter(self):
        return not ctrl.settings.active_edges('relative')


class ChangeEdgeRelativeCurvatureX(KatajaAction):
    k_action_uid = 'change_edge_relative_curvature_x'
    k_command = 'Change horizontal curvature for edge'
    k_tooltip = 'Curvature value is relative to edge width'

    def prepare_parameters(self, args, kwargs):
        value = args[0]

        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
            edge_type = None
        else:
            level = ctrl.ui.active_scope
            edge_type = ctrl.ui.active_edge_type
        return [value], {'edge_type': edge_type, 'level': level}

    def method(self, value: int, edge_type=None, level=None):
        """ Set curvature to be relative to edge width.
        :param value: int, percentage of edge width
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        if not edge_type:
            edge_type = ctrl.active_edge_type
        if not level:
            level = ctrl.ui_active_scope
        if level == g.SELECTION:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.change_edge_relative_curvature_x(value)
        else:
            ctrl.settings.set_edge_setting('rel_dx', value * .01, edge_type=edge_type, level=level)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope() and \
               ctrl.settings.active_edges('relative') and \
               ctrl.settings.active_edges('control_points')

    def getter(self):
        return round((ctrl.settings.active_edges('rel_dx') or 0) * 100)


class ChangeEdgeRelativeCurvatureY(KatajaAction):
    k_action_uid = 'change_edge_relative_curvature_y'
    k_command = 'Change vertical curvature for edge'
    k_tooltip = 'Curvature value is relative to edge height'

    def prepare_parameters(self, args, kwargs):
        value = args[0]

        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
            edge_type = None
        else:
            level = ctrl.ui.active_scope
            edge_type = ctrl.ui.active_edge_type
        return [value], {'edge_type': edge_type, 'level': level}

    def method(self, value: int, edge_type=None, level=None):
        """ Set curvature to be relative to edge height.
        :param value: int, percentage of edge height
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        if not edge_type:
            edge_type = ctrl.active_edge_type
        if not level:
            level = ctrl.ui_active_scope
        if level == g.SELECTION:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.change_edge_relative_curvature_y(value)
                else:
                    ctrl.settings.set_edge_setting('rel_dy', value * .01, edge_type=edge_type,
                                                   level=level)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope() and \
               ctrl.settings.active_edges('relative') and \
               ctrl.settings.active_edges('control_points')

    def getter(self):
        return round((ctrl.settings.active_edges('rel_dy') or 0) * 100)


class ChangeEdgeFixedCurvatureX(KatajaAction):
    k_action_uid = 'change_edge_fixed_curvature_x'
    k_command = 'Change horizontal curvature for edge'
    k_tooltip = 'Curvature is fixed amount'

    def prepare_parameters(self, args, kwargs):
        value = args[0]

        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
            edge_type = None
        else:
            level = ctrl.ui.active_scope
            edge_type = ctrl.ui.active_edge_type
        return [value], {'edge_type': edge_type, 'level': level}

    def method(self, value: int, edge_type=None, level=None):
        """ Set curvature to fixed amount, x-dimension.
        :param value: int, amount in pixels
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        if not edge_type:
            edge_type = ctrl.active_edge_type
        if not level:
            level = ctrl.ui_active_scope
        if level == g.SELECTION:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.change_edge_fixed_curvature_x(value)
        else:
            ctrl.settings.set_edge_setting('fixed_dx', value, edge_type=edge_type, level=level)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope() and \
               ctrl.settings.active_edges('relative') is False and \
               ctrl.settings.active_edges('control_points')

    def getter(self):
        return ctrl.settings.active_edges('fixed_dx')


class ChangeEdgeFixedCurvatureY(KatajaAction):
    k_action_uid = 'change_edge_fixed_curvature_y'
    k_command = 'Change vertical curvature for edge'
    k_tooltip = 'Curvature is fixed amount'

    def prepare_parameters(self, args, kwargs):
        value = args[0]

        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
            edge_type = None
        else:
            level = ctrl.ui.active_scope
            edge_type = ctrl.ui.active_edge_type
        return [value], {'edge_type': edge_type, 'level': level}

    def method(self, value: int, edge_type=None, level=None):
        """ Set curvature to fixed amount, y-dimension.
        :param value: int, amount in pixels
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        if not edge_type:
            edge_type = ctrl.active_edge_type
        if not level:
            level = ctrl.ui_active_scope
        if level == g.SELECTION:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.change_edge_fixed_curvature_y(value)
        else:
            ctrl.settings.set_edge_setting('fixed_dy', value, edge_type=edge_type, level=level)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope() and \
               ctrl.settings.active_edges('relative') is False and \
               ctrl.settings.active_edges('control_points')

    def getter(self):
        return ctrl.settings.active_edges('fixed_dy')


class EdgeShapeFill(KatajaAction):
    k_action_uid = 'edge_shape_fill'
    k_command = 'Set edges to be drawn as filled'
    k_checkable = True

    def prepare_parameters(self, args, kwargs):
        value = args[0]

        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
            edge_type = None
        else:
            level = ctrl.ui.active_scope
            edge_type = ctrl.ui.active_edge_type
        return [value], {'edge_type': edge_type, 'level': level}

    def method(self, value: bool, edge_type=None, level=None):
        """ Set edges to be drawn as filled.
        :param value: bool, draw as filled or not
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        if not edge_type:
            edge_type = ctrl.active_edge_type
        if not level:
            level = ctrl.ui_active_scope
        if level == g.SELECTION:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_fill(value)
        else:
            ctrl.settings.set_edge_setting('fill', value, edge_type=edge_type, level=level)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope() and \
               ctrl.settings.active_edges('fillable')

    def getter(self):
        return ctrl.settings.active_edges('fill') and \
               ctrl.settings.active_edges('fillable')


class EdgeShapeLine(KatajaAction):
    k_action_uid = 'edge_shape_line'
    k_command = 'Set edges to be drawn with outlines'
    k_checkable = True

    def prepare_parameters(self, args, kwargs):
        value = args[0]

        if ctrl.ui.scope_is_selection:
            level = g.SELECTION
            edge_type = None
        else:
            level = ctrl.ui.active_scope
            edge_type = ctrl.ui.active_edge_type
        return [value], {'edge_type': edge_type, 'level': level}

    def method(self, value: bool, edge_type=None, level=None):
        """ Set edges to be drawn with outlines.
        :param value: bool, draw outlines or not
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        if not edge_type:
            edge_type = ctrl.active_edge_type
        if not level:
            level = ctrl.ui_active_scope
        if level == g.SELECTION:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_outline(value)
        else:
            ctrl.settings.set_edge_setting('outline', value, edge_type=edge_type, level=level)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope() and \
               ctrl.settings.active_edges('fillable')

    def getter(self):
        return ctrl.settings.active_edges('outline')


