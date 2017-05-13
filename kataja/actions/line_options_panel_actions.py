# coding=utf-8

import math
from PyQt5 import QtCore
from kataja.KatajaAction import KatajaAction
from kataja.saved.Edge import Edge
from kataja.globals import FOREST

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

    def method(self):
        """ Change edge shape for selection or in currently active edge type.
        :return: None
        """
        sender = self.sender()
        shape = sender.currentData()

        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.shape_name = shape
                    edge.update_shape()
        else:
            ctrl.settings.set_edge_setting('shape_name', shape,
                                           edge_type=ctrl.ui.active_edge_type, level=FOREST)
            for edge in ctrl.forest.edges.values():
                edge.update_shape()
        line_options = ctrl.ui.get_panel('LineOptionsPanel')

        if line_options:
            line_options.update_panel()
        log.info('(s) Changed relation shape to: %s' % shape)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope()

    def getter(self):
        return ctrl.settings.cached_active_edge('shape_name')


class ChangeEdgeColor(KatajaAction):
    k_action_uid = 'change_edge_color'
    k_command = 'Change edge color'
    k_tooltip = 'Change drawing color for edges'
    k_undoable = False

    def method(self):
        """ Change edge shape for selection or in currently active edge type.
        :return: None
        """
        selector = self.sender()
        color_key = selector.receive_color_selection()
        if not color_key:
            return

        # Update color for selected edges
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.color_id = color_key
                    edge.update()
        # ... or update color for all edges of this type
        else:
            ctrl.settings.set_edge_setting('color_id', color_key,
                                           edge_type=ctrl.ui.active_edge_type, level=FOREST)
            for edge in ctrl.forest.edges.values():
                edge.update()
        ctrl.call_watchers(self, 'active_edge_color_changed')  # shape_selector needs this
        if color_key:
            log.info('(s) Changed relation color to: %s' % ctrl.cm.get_color_name(color_key))

    def enabler(self):
        return ctrl.ui.has_edges_in_scope()

    def getter(self):
        return ctrl.settings.active_edges('color_id')


class EdgeArrowheadStart(KatajaAction):
    k_action_uid = 'edge_arrowhead_start'
    k_command = 'Draw arrowhead at line start'
    k_checkable = True

    def method(self):
        """ Draw arrowheads at start for given edges or edge type
        """
        value = self.state_arg
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_arrowhead_at_start(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.settings.set_edge_setting('arrowhead_at_start', value, edge_type=etype,
                                           level=FOREST)
            ctrl.forest.redraw_edges(edge_type=etype)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope()

    def getter(self):
        return ctrl.settings.active_edges('arrowhead_at_start')


class EdgeArrowheadEnd(KatajaAction):
    k_action_uid = 'edge_arrowhead_end'
    k_command = 'Draw arrowhead at line end'
    k_checkable = True

    def method(self):
        """ Draw arrowheads at end for given edges or edge type
        :param value: bool
        """
        value = self.state_arg
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_arrowhead_at_end(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.settings.set_edge_setting('arrowhead_at_end', value, edge_type=etype, level=FOREST)
            ctrl.forest.redraw_edges(edge_type=etype)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope()

    def getter(self):
        return ctrl.settings.active_edges('arrowhead_at_end')


class ResetControlPoints(KatajaAction):
    k_action_uid = 'reset_control_points'
    k_command = 'Reset control point'
    k_tooltip = 'Remove adjustments for these curves'

    def method(self):
        """ Reset all control points
        :return: None
        """
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.reset_control_points()
        else:
            etype = ctrl.ui.active_edge_type
            if etype:
                for edge in ctrl.forest.edges.values():
                    if edge.edge_type == etype:
                        edge.reset_control_points()

    def enabler(self):
        return ctrl.ui.has_edges_in_scope()


class ResetEdgeSettings(KatajaAction):
    k_action_uid = 'reset_edge_settings'
    k_command = 'Reset edge settings'
    k_tooltip = 'Reset settings for this type of edges back to defaults'

    def method(self):
        """ Reset all control points
        :return: None
        """
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.reset_shape()
                    ctrl.settings.del_edge_setting('arrowhead_at_start', edge=edge)
                    ctrl.settings.del_edge_setting('arrowhead_at_end', edge=edge)

            ctrl.forest.redraw_edges()

        else:
            etype = ctrl.ui.active_edge_type
            if etype:
                ctrl.settings.reset_shape_settings(level=FOREST, edge_type=etype)
                ctrl.settings.del_edge_setting('arrowhead_at_start', edge_type=etype)
                ctrl.settings.del_edge_setting('arrowhead_at_end', edge_type=etype)

                for edge in ctrl.forest.edges.values():
                    if edge.edge_type == etype:
                        edge.reset_shape()
                ctrl.forest.redraw_edges(edge_type=etype)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope()


class LeafShapeX(KatajaAction):
    k_action_uid = 'leaf_shape_x'
    k_command = 'Edge shape width'
    k_tooltip = 'Adjust horizontal thickness of edges'

    def method(self):
        """ Change width of leaf-shaped edge.
        """
        value = self.state_arg
        if value is None:
            return
        elif ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_leaf_width(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.settings.set_edge_setting('leaf_x', value, edge_type=etype, level=FOREST)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope() and \
               ctrl.settings.cached_active_edge('fillable')

    def getter(self):
        return ctrl.settings.active_edges('leaf_x')


class LeafShapeY(KatajaAction):
    k_action_uid = 'leaf_shape_y'
    k_command = 'Edge shape height'
    k_tooltip = 'Adjust vertical thickness of edges'

    def method(self):
        """ Change height of leaf-shaped edge.
        """
        value = self.state_arg
        if value is None:
            return
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_leaf_height(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.settings.set_edge_setting('leaf_y', value, edge_type=etype, level=FOREST)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope() and \
               ctrl.settings.active_edges('fillable')

    def getter(self):
        return ctrl.settings.active_edges('leaf_y')


class EdgeThickness(KatajaAction):
    k_action_uid = 'edge_thickness'
    k_command = 'Edge thickness'
    k_tooltip = 'Adjust fixed thickness for edges'

    def method(self):
        """ If edge is outline (not a leaf shape)
        """
        value = self.state_arg
        if value is None:
            return
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_thickness(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.settings.set_edge_setting('thickness', value, edge_type=etype, level=FOREST)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope() and \
               ctrl.settings.active_edges('outline')

    def getter(self):
        return ctrl.settings.active_edges('thickness')


class EdgeCurvatureRelative(KatajaAction):
    k_action_uid = 'edge_curvature_relative'
    k_command = 'Change line curvature to be relative to edge dimensions'
    k_checkable = True

    def method(self):
        """ Change curvature computation type. Curvature can be 'relative' or 'fixed'
        """
        value = self.state_arg
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_edge_curvature_relative(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.settings.set_edge_setting('relative', value, edge_type=etype, level=FOREST)

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

    def method(self):
        """ Change curvature computation type. Curvature can be 'relative' or 'fixed'
        """
        value = self.state_arg
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_edge_curvature_relative(not value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.settings.set_edge_setting('relative', not value, edge_type=etype, level=FOREST)

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

    def method(self):
        """ Change curvature of arching lines. Curvature is relative to width
        """
        value = self.state_arg
        if value is None:
            return
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.change_edge_relative_curvature_x(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.settings.set_edge_setting('rel_dx', value * .01, edge_type=etype, level=FOREST)

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

    def method(self):
        """ Change curvature of arching lines. Curvature is relative to width
        """
        value = self.state_arg
        if value is None:
            return
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.change_edge_relative_curvature_y(value)
                else:
                    etype = ctrl.ui.active_edge_type
                    ctrl.settings.set_edge_setting('rel_dy', value * .01, edge_type=etype,
                                                    level=FOREST)

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

    def method(self):
        """ Change curvature of arching lines. Curvature is absolute pixels (X)
        """
        value = self.state_arg
        if value is None:
            return
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.change_edge_fixed_curvature_x(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.settings.set_edge_setting('fixed_dx', value, edge_type=etype, level=FOREST)

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

    def method(self):
        """ Change curvature of arching lines. Curvature is absolute pixels (X)
        :param value: float
        """
        value = self.state_arg
        if value is None:
            return
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.change_edge_fixed_curvature_y(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.settings.set_edge_setting('fixed_dy', value, edge_type=etype, level=FOREST)

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

    def method(self):
        """ Change edge to draw as filled shape
        """
        value = self.state_arg
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_fill(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.settings.set_edge_setting('fill', value, edge_type=etype, level=FOREST)

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

    def method(self):
        """ Change edge to draw as line instead of filled shape
        """

        value = self.state_arg
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.set_outline(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.settings.set_edge_setting('outline', value, edge_type=etype, level=FOREST)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope() and \
               ctrl.settings.active_edges('fillable')

    def getter(self):
        return ctrl.settings.active_edges('outline')


