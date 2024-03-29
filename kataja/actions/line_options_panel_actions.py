# coding=utf-8

import kataja.globals as g
from kataja.singletons import ctrl
from kataja.ui_widgets.Panel import PanelAction


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


class SetEdgeType(PanelAction):
    k_action_uid = 'set_edge_type_for_editing'
    k_command = 'Set edge type to be modified'
    k_tooltip = 'Set which kind of edges are changed by this panel'
    k_undoable = True

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        return [sender.currentData()], {}

    def method(self, node_type):
        if self.panel:
            self.panel.active_node_type = node_type
            self.panel.update_panel()

    def getter(self):
        return self.panel.active_node_type

    def enabler(self):
        return self.panel and not ctrl.ui.scope_is_selection


class ChangeEdgeColor(PanelAction):
    k_action_uid = 'change_edge_color'
    k_command = 'Change edge color'
    k_tooltip = 'Change drawing color for edges'
    k_undoable = False

    def prepare_parameters(self, args, kwargs):
        sender = self.sender()
        color_key = sender.receive_color_selection()
        if ctrl.ui.scope_is_selection:
            kwargs = {'level': ctrl.ui.active_scope}
        else:
            kwargs = {'level': ctrl.ui.active_scope, 'edge_type': self.panel.active_edge_type}
        return [color_key], kwargs

    def method(self, color_key, edge_type=None, level=None):
        """ Change edge color for selection or in currently active edge type.
        :param color_key: str, color_key from available colors.
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        ctrl.ui.set_active_edge_setting('color_key', color_key, edge_type=edge_type)
        for edge in ctrl.forest.edges.values():
            edge.update()
        ctrl.main.active_edge_color_changed.emit()  # shape_selector needs this

    def enabler(self):
        return self.panel and ctrl.ui.has_edges_in_scope()

    def getter(self):
        return ctrl.ui.get_active_edge_setting('color_key', self.panel.active_edge_type) or \
               self.panel.get_active_node_setting('color_key')


class EdgeArrowheadStart(PanelAction):
    k_action_uid = 'edge_arrowhead_start'
    k_command = 'Draw arrowhead at line start'
    k_checkable = True

    def prepare_parameters(self, args, kwargs):
        ah_at_start = bool(args[0])
        if ctrl.ui.scope_is_selection:
            kwargs = {'level': ctrl.ui.active_scope}
        else:
            kwargs = {'level': ctrl.ui.active_scope, 'edge_type': self.panel.active_edge_type}
        return [ah_at_start], kwargs

    def method(self, value: bool, edge_type=None, level=None):
        """ Draw arrowheads at the start of the edge.
        :param value: bool, draw arrowhead or not
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        old_value = ctrl.ui.get_active_edge_setting('arrowheads', self.panel.active_edge_type)
        if old_value == g.AT_END and value:
            new_value = g.AT_BOTH
        elif old_value == g.AT_BOTH and not value:
            new_value = g.AT_END
        elif old_value == g.AT_START and not value:
            new_value = 0
        elif (not old_value) and value:
            new_value = g.AT_START
        else:
            return
        ctrl.ui.set_active_edge_setting('arrowheads', new_value, edge_type)
        ctrl.forest.redraw_edges(edge_type=edge_type)

    def enabler(self):
        return self.panel and ctrl.ui.has_edges_in_scope()

    def getter(self):
        if self.panel:
            arrowheads = ctrl.ui.get_active_edge_setting('arrowheads', self.panel.active_edge_type)
            return arrowheads == g.AT_START or arrowheads == g.AT_BOTH


class EdgeArrowheadEnd(PanelAction):
    k_action_uid = 'edge_arrowhead_end'
    k_command = 'Draw arrowhead at line end'
    k_checkable = True

    def prepare_parameters(self, args, kwargs):
        ah_at_end = bool(args[0])
        if ctrl.ui.scope_is_selection:
            kwargs = {'level': ctrl.ui.active_scope}
        else:
            kwargs = {'level': ctrl.ui.active_scope, 'edge_type': self.panel.active_edge_type}
        return [ah_at_end], kwargs

    def method(self, value: bool, edge_type=None, level=None):
        """ Draw arrowheads at the end of the edge.
        :param value: bool, draw arrowhead or not
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        old_value = ctrl.ui.get_active_edge_setting('arrowheads', self.panel.active_edge_type)
        if old_value == g.AT_START and value:
            new_value = g.AT_BOTH
        elif old_value == g.AT_BOTH and not value:
            new_value = g.AT_START
        elif old_value == g.AT_END and not value:
            new_value = 0
        elif (not old_value) and value:
            new_value = g.AT_END
        else:
            return
        ctrl.ui.set_active_edge_setting('arrowheads', new_value, edge_type)
        ctrl.forest.redraw_edges(edge_type=edge_type)

    def enabler(self):
        return ctrl.ui.has_edges_in_scope()

    def getter(self):
        if self.panel:
            arrowheads = ctrl.ui.get_active_edge_setting('arrowheads', self.panel.active_edge_type)
            return arrowheads == g.AT_END or arrowheads == g.AT_BOTH


class ResetControlPoints(PanelAction):
    k_action_uid = 'reset_control_points'
    k_command = 'Reset control point'
    k_tooltip = 'Remove adjustments for these curves'

    def prepare_parameters(self, args, kwargs):
        if ctrl.ui.scope_is_selection:
            kwargs = {'level': ctrl.ui.active_scope}
        else:
            kwargs = {'level': ctrl.ui.active_scope, 'edge_type': self.panel.active_edge_type}
        return [], kwargs

    def method(self, edge_type=None, level=None):
        """ Reset all adjustments for curves in selected edges or this type of edges.
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        ctrl.ui.reset_control_points()

    def enabler(self):
        return self.panel and ctrl.ui.has_edges_in_scope()


class ResetEdgeSettings(PanelAction):
    k_action_uid = 'reset_edge_settings'
    k_command = 'Reset edge settings'
    k_tooltip = 'Reset settings for this type of edges back to defaults'

    def prepare_parameters(self, args, kwargs):
        if ctrl.ui.scope_is_selection:
            kwargs = {'level': ctrl.ui.active_scope}
        else:
            kwargs = {'level': ctrl.ui.active_scope, 'edge_type': self.panel.active_edge_type}
        return [], kwargs

    def method(self, edge_type=None, level=None):
        """ Reset all additional settings in selected edges or for this type of edges.
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        ctrl.ui.reset_active_edge_setting(edge_type)

    def enabler(self):
        return self.panel and ctrl.ui.has_edges_in_scope()


class LeafShapeX(PanelAction):
    k_action_uid = 'leaf_shape_x'
    k_command = 'Edge shape width'
    k_tooltip = 'Adjust horizontal thickness of edges'

    def prepare_parameters(self, args, kwargs):
        value = args[0]

        if ctrl.ui.scope_is_selection:
            kwargs = {'level': ctrl.ui.active_scope}
        else:
            kwargs = {'level': ctrl.ui.active_scope, 'edge_type': self.panel.active_edge_type}
        return [value], kwargs

    def method(self, value: int, edge_type=None, level=None):
        """ Adjust horizontal thickness for leaf-shaped edges.
        :param value: int, horizontal thickness of leaf-shaped edge
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        ctrl.ui.set_active_edge_shape_setting('leaf_x', value, edge_type=edge_type, level=level)
        ctrl.forest.redraw_edges(edge_type=edge_type)

    def enabler(self):
        return self.panel and ctrl.ui.has_edges_in_scope() and self.panel.is_active_fillable() and self.panel.active_edge_has_setting(
            'leaf_x')

    def getter(self):
        return self.panel.get_active_shape_setting('leaf_x')


class LeafShapeY(PanelAction):
    k_action_uid = 'leaf_shape_y'
    k_command = 'Edge shape height'
    k_tooltip = 'Adjust vertical thickness of edges'

    def prepare_parameters(self, args, kwargs):
        value = args[0]

        if ctrl.ui.scope_is_selection:
            kwargs = {'level': ctrl.ui.active_scope}
        else:
            kwargs = {'level': ctrl.ui.active_scope, 'edge_type': self.panel.active_edge_type}
        return [value], kwargs

    def method(self, value: int, edge_type=None, level=None):
        """ Adjust vertical thickness for leaf-shaped edges.
        :param value: int, vertical thickness of leaf-shaped edge
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        ctrl.ui.set_active_edge_shape_setting('leaf_y', value, edge_type=edge_type, level=level)
        ctrl.forest.redraw_edges(edge_type=edge_type)

    def enabler(self):
        return self.panel and ctrl.ui.has_edges_in_scope() and self.panel.is_active_fillable() and self.panel.active_edge_has_setting(
            'leaf_y')

    def getter(self):
        return self.panel.get_active_shape_setting('leaf_y')


class EdgeThickness(PanelAction):
    k_action_uid = 'edge_thickness'
    k_command = 'Edge thickness'
    k_tooltip = 'Adjust fixed thickness for edges'

    def prepare_parameters(self, args, kwargs):
        value = args[0]
        if ctrl.ui.scope_is_selection:
            kwargs = {'level': ctrl.ui.active_scope}
        else:
            kwargs = {'level': ctrl.ui.active_scope, 'edge_type': self.panel.active_edge_type}
        return [value], kwargs

    def method(self, value: float, edge_type=None, level=None):
        """ Edge outline thickness.
        :param value: float, thickness in pixels
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        ctrl.ui.set_active_edge_shape_setting('thickness', value, edge_type=edge_type)
        ctrl.forest.redraw_edges(edge_type=edge_type)

    def enabler(self):
        return self.panel and ctrl.ui.has_edges_in_scope() and self.panel.has_active_outline()

    def getter(self):
        return self.panel.get_active_shape_setting('thickness')


class ChangeEdgeRelativeCurvatureX(PanelAction):
    k_action_uid = 'change_edge_relative_curvature_x'
    k_command = 'Change horizontal curvature for edge'
    k_tooltip = 'Curvature value is relative to edge width'

    def prepare_parameters(self, args, kwargs):
        value = args[0] if args else 0
        if ctrl.ui.scope_is_selection:
            kwargs = {'level': ctrl.ui.active_scope}
        else:
            kwargs = {'level': ctrl.ui.active_scope, 'edge_type': self.panel.active_edge_type}
        return [value], kwargs

    def method(self, value: int, edge_type=None, level=None):
        """ Set curvature to be relative to edge width.
        :param value: int, percentage of edge width
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        ctrl.ui.set_active_edge_shape_setting('rel_dx', value * .01, edge_type=edge_type)
        ctrl.forest.redraw_edges(edge_type=edge_type)

    def enabler(self):
        return self.panel and ctrl.ui.has_edges_in_scope() and \
               self.panel.get_active_shape_property('control_points_n')

    def getter(self):
        return round((self.panel.get_active_shape_setting('rel_dx') or 0) * 100)


class ChangeEdgeRelativeCurvatureY(PanelAction):
    k_action_uid = 'change_edge_relative_curvature_y'
    k_command = 'Change vertical curvature for edge'
    k_tooltip = 'Curvature value is relative to edge height'

    def prepare_parameters(self, args, kwargs):
        value = args[0]
        if ctrl.ui.scope_is_selection:
            kwargs = {'level': ctrl.ui.active_scope}
        else:
            kwargs = {'level': ctrl.ui.active_scope, 'edge_type': self.panel.active_edge_type}
        return [value], kwargs

    def method(self, value: int, edge_type=None, level=None):
        """ Set curvature to be relative to edge height.
        :param value: int, percentage of edge height
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        ctrl.ui.set_active_edge_shape_setting('rel_dy', value * .01, edge_type=edge_type)
        ctrl.forest.redraw_edges(edge_type=edge_type)

    def enabler(self):
        return self.panel and ctrl.ui.has_edges_in_scope() and \
               self.panel.get_active_shape_property('control_points_n')

    def getter(self):
        return round((self.panel.get_active_shape_setting('rel_dy') or 0) * 100)


class ChangeEdgeFixedCurvatureX(PanelAction):
    k_action_uid = 'change_edge_fixed_curvature_x'
    k_command = 'Change horizontal curvature for edge'
    k_tooltip = 'Curvature is fixed amount'

    def prepare_parameters(self, args, kwargs):
        value = args[0]
        if ctrl.ui.scope_is_selection:
            kwargs = {'level': ctrl.ui.active_scope}
        else:
            kwargs = {'level': ctrl.ui.active_scope, 'edge_type': self.panel.active_edge_type}
        return [value], kwargs

    def method(self, value: int, edge_type=None, level=None):
        """ Set curvature to fixed amount, x-dimension.
        :param value: int, amount in pixels
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        ctrl.ui.set_active_edge_shape_setting('fixed_dx', value, edge_type=edge_type)
        ctrl.forest.redraw_edges(edge_type=edge_type)

    def enabler(self):
        return self.panel and ctrl.ui.has_edges_in_scope() and \
               self.panel.get_active_shape_property('control_points_n')

    def getter(self):
        return self.panel.get_active_shape_setting('fixed_dx')


class ChangeEdgeFixedCurvatureY(PanelAction):
    k_action_uid = 'change_edge_fixed_curvature_y'
    k_command = 'Change vertical curvature for edge'
    k_tooltip = 'Curvature is fixed amount'

    def prepare_parameters(self, args, kwargs):
        value = args[0]
        if ctrl.ui.scope_is_selection:
            kwargs = {'level': ctrl.ui.active_scope}
        else:
            kwargs = {'level': ctrl.ui.active_scope, 'edge_type': self.panel.active_edge_type}
        return [value], kwargs

    def method(self, value: int, edge_type=None, level=None):
        """ Set curvature to fixed amount, y-dimension.
        :param value: int, amount in pixels
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        ctrl.ui.set_active_edge_shape_setting('fixed_dy', value, edge_type=edge_type)
        ctrl.forest.redraw_edges(edge_type=edge_type)

    def enabler(self):
        return self.panel and ctrl.ui.has_edges_in_scope() and \
               self.panel.get_active_shape_property('control_points_n')

    def getter(self):
        return self.panel.get_active_shape_setting('fixed_dy')


class EdgeShapeFill(PanelAction):
    k_action_uid = 'edge_shape_fill'
    k_command = 'Set edges to be drawn as filled'
    k_checkable = True

    def prepare_parameters(self, args, kwargs):
        value = args[0]
        if ctrl.ui.scope_is_selection:
            kwargs = {'level': ctrl.ui.active_scope}
        else:
            kwargs = {'level': ctrl.ui.active_scope, 'edge_type': self.panel.active_edge_type}
        return [value], kwargs

    def method(self, value: bool, edge_type=None, level=None):
        """ Set edges to be drawn as filled.
        :param value: bool, draw as filled or not
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        ctrl.ui.set_active_edge_shape_setting('fill', value, edge_type=edge_type)
        ctrl.forest.redraw_edges(edge_type=edge_type)

    def enabler(self):
        return self.panel and ctrl.ui.has_edges_in_scope() and self.panel.is_active_fillable()

    def getter(self):
        return self.panel.has_active_fill()


class EdgeShapeLine(PanelAction):
    k_action_uid = 'edge_shape_line'
    k_command = 'Set edges to be drawn with outlines'
    k_checkable = True

    def prepare_parameters(self, args, kwargs):
        value = args[0]
        if ctrl.ui.scope_is_selection:
            kwargs = {'level': ctrl.ui.active_scope}
        else:
            kwargs = {'level': ctrl.ui.active_scope, 'edge_type': self.panel.active_edge_type}
        return [value], kwargs

    def method(self, value: bool, edge_type=None, level=None):
        """ Set edges to be drawn with outlines.
        :param value: bool, draw outlines or not
        :param edge_type: str, what kind of edges are affected. Ignored if level is g.SELECTION.
        :param level: int or None, optional level where change takes effect: g.SELECTION (66),
          g.FOREST (2), g.DOCUMENT (3), g.PREFS (4).
        :return: None
        """
        ctrl.ui.set_active_edge_shape_setting('outline', value, edge_type=edge_type)
        ctrl.forest.redraw_edges(edge_type=edge_type)

    def enabler(self):
        return self.panel and ctrl.ui.has_edges_in_scope()

    def getter(self):
        return self.panel.has_active_outline()
