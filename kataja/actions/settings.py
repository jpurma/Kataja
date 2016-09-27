# coding=utf-8
from kataja.KatajaAction import KatajaAction
from kataja.singletons import ctrl, prefs, log
from kataja.saved.Edge import Edge
from kataja.saved.movables.Node import Node


class CustomizeMasterStyle(KatajaAction):
    k_action_uid = 'customize_master_style'
    k_command = 'Customize style'
    k_tooltip = 'Modify the styles of lines and nodes'
    k_undoable = False

    def method(self):
        """ """
        panel = ctrl.ui.get_panel('StylePanel')
        panel.toggle_customization(not self.getter())

    def getter(self):
        panel = ctrl.ui.get_panel('StylePanel')
        return panel.style_widgets.isVisible()


class ChangeMasterStyle(KatajaAction):
    k_action_uid = 'change_master_style'
    k_command = 'Change drawing style'
    k_tooltip = 'Changes the style of lines and nodes'
    k_undoable = False

    def method(self):
        """ """
        sender = self.sender()
        value = sender.currentData(256)
        prefs.style = value
        ctrl.forest.redraw_edges()
        return "Changed master style to '%s'" % value

    def enabler(self):
        return ctrl.forest is not None and prefs.style

    def getter(self):
        return prefs.style


class ChangeStyleScope(KatajaAction):
    k_action_uid = 'style_scope'
    k_command = 'Select the scope for style changes'
    k_tooltip = 'Select the scope for style changes'
    k_undoable = False

    def method(self):
        """ Change drawing panel to work on selected nodes, constituent nodes or
        other available
        nodes
        """
        sender = self.sender()
        if sender:
            value = sender.currentData(256)
            ctrl.ui.set_scope(value)

    def enabler(self):
        return ctrl.forest is not None

    def getter(self):
        return ctrl.ui.active_scope


class ResetStyleInScope(KatajaAction):
    k_action_uid = 'reset_style_in_scope'
    k_command = 'Reset style to original definition'
    k_tooltip = 'Reset style to default within the selected scope'

    def method(self):
        """ Restore style to original
        :return: None
        """
        if ctrl.ui.scope_is_selection:
            for item in ctrl.selected:
                if hasattr(item, 'reset_style'):
                    item.reset_style()
        ctrl.fs.reset_node_style(ctrl.ui.active_node_type)
        ctrl.fs.reset_edge_style(ctrl.ui.active_edge_type)
        ctrl.forest.redraw_edges(ctrl.ui.active_edge_type)

    def enabler(self):
        if ctrl.forest is None:
            return False
        if ctrl.ui.scope_is_selection:
            for item in ctrl.selected:
                if hasattr(item, 'has_local_style_settings'):
                    if item.has_local_style_settings():
                        return True
        elif ctrl.ui.active_node_type and ctrl.fs.has_local_node_style(ctrl.ui.active_node_type):
            return True
        elif ctrl.ui.active_edge_type and ctrl.fs.has_local_edge_style(ctrl.ui.active_edge_type):
            return True
        return False


class StartFontDialog(KatajaAction):
    k_action_uid = 'start_font_dialog'
    k_command = 'Use a custom font'
    k_tooltip = 'Select your own font for node labels'
    k_undoable = False

    def method(self):
        """ Change drawing panel to work on selected nodes, constituent nodes or
        other available
        nodes
        """

        panel = self.get_ui_container()
        font_key = panel.cached_font_id
        ctrl.ui.start_font_dialog(panel, font_key, font_key)

    def enabler(self):
        if ctrl.ui.scope_is_selection:
            for item in ctrl.selected:
                if isinstance(item, Node):
                    return True
            return False
        else:
            return True


class SelectFont(KatajaAction):
    k_action_uid = 'select_font'
    k_command = 'Change label font'
    k_tooltip = 'Change font for current selection or for a node type'
    k_undoable = False

    def method(self):
        """ Change font key for current node or node type.
        :return: None
        """
        panel = ctrl.ui.get_panel('StylePanel')
        if panel:
            font_id = panel.font_selector.currentData() or panel.cached_font_id
            panel.update_font_selector(font_id)
            if ctrl.ui.scope_is_selection:
                for node in ctrl.selected:
                    if isinstance(node, Node):
                        node.font_id = font_id
                        node.update_label()
            else:
                ctrl.fs.set_node_style(ctrl.ui.active_node_type, 'font', font_id)
                for node in ctrl.forest.nodes.values():
                    node.update_label()

    def getter(self):
        return ctrl.ui.active_node_style.get('font', None)


class SelectFontFromDialog(KatajaAction):
    k_action_uid = 'select_font_from_dialog'
    k_command = 'Change label font'
    k_tooltip = 'Change font for current selection or for a node type'
    k_undoable = False

    def method(self):
        panel = ctrl.ui.get_panel('StylePanel')
        if panel:
            font_id = panel.cached_font_id
            print('panel.cached_font_id: ', panel.cached_font_id)
            panel.update_font_selector(font_id)
            if ctrl.ui.scope_is_selection:
                for node in ctrl.selected:
                    if isinstance(node, Node):
                        node.font_id = font_id
                        node.update_label()
            else:
                ctrl.fs.set_node_style(ctrl.ui.active_node_type, 'font', font_id)
                for node in ctrl.forest.nodes.values():
                    node.update_label()


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
            ctrl.fs.set_edge_info(ctrl.ui.active_edge_type, 'shape_name', shape)
            for edge in ctrl.forest.edges.values():
                edge.update_shape()
        line_options = ctrl.ui.get_panel('LineOptionsPanel')

        if line_options:
            line_options.update_panel()
        log.info('(s) Changed relation shape to: %s' % shape)

    def enabler(self):
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    return True
            return False
        return True  # all scope options allow defining edge shape

    def getter(self):
        return ctrl.ui.active_edge_style.get('shape_name', None)


class ChangeNodeColor(KatajaAction):
    k_action_uid = 'change_node_color'
    k_command = 'Change node color'
    k_tooltip = 'Change drawing color of nodes'
    k_undoable = False

    def method(self):
        """ Change color for selection or in currently active edge type.
        :return: None
        """
        panel = ctrl.ui.get_panel('StylePanel')
        color_key = panel.node_color_selector.currentData()
        panel.node_color_selector.model().selected_color = color_key
        color = ctrl.cm.get(color_key)
        # launch a color dialog if color_id is unknown or clicking
        # already selected color
        prev_color = panel.cached_node_color
        if not color:
            color = ctrl.cm.get('content1')
            ctrl.cm.d[color_key] = color
            ctrl.ui.start_color_dialog(panel.node_color_selector, panel, 'node', color_key)
        elif prev_color == color_key:
            ctrl.ui.start_color_dialog(panel.node_color_selector, panel, 'node', color_key)
        else:
            ctrl.ui.update_color_dialog('node', color_key)
        panel.update_node_color_selector(color_key)
        # Update color for selected nodes
        if ctrl.ui.scope_is_selection:
            for node in ctrl.selected:
                if isinstance(node, Node):
                    node.color_id = color_key
                    node.update_label()
        # ... or update color for all nodes of this type
        else:
            ctrl.fs.set_node_style(ctrl.ui.active_node_type, 'color', color_key)
            for node in ctrl.forest.nodes.values():
                node.update_label()
        if color_key:
            log.info('(s) Changed node color to: %s' % ctrl.cm.get_color_name(color_key))

    def enabler(self):
        if ctrl.ui.scope_is_selection:
            for item in ctrl.selected:
                if isinstance(item, Node):
                    return True
            return False
        return True  # all scope options allow defining node color

    def getter(self):
        return ctrl.ui.active_node_style.get('color')


class ChangeEdgeColor(KatajaAction):
    k_action_uid = 'change_edge_color'
    k_command = 'Change edge color'
    k_tooltip = 'Change drawing color for edges'
    k_undoable = False

    def method(self):
        """ Change edge shape for selection or in currently active edge type.
        :return: None
        """
        panel = ctrl.ui.get_panel('StylePanel')
        color_key = panel.edge_color_selector.currentData()
        panel.edge_color_selector.model().selected_color = color_key
        color = ctrl.cm.get(color_key)
        # launch a color dialog if color_id is unknown or clicking
        # already selected color
        prev_color = panel.cached_edge_color
        if not color:
            color = ctrl.cm.get('content1')
            ctrl.cm.d[color_key] = color
            ctrl.ui.start_color_dialog(panel.edge_color_selector, panel, 'edge', color_key)
        elif prev_color == color_key:
            ctrl.ui.start_color_dialog(panel.edge_color_selector, panel, 'edge', color_key)
        else:
            ctrl.ui.update_color_dialog('edge', color_key)
        panel.update_edge_color_selector(color_key)
        # Update color for selected edges
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.color_id = color_key
                    edge.update()
        # ... or update color for all edges of this type
        else:
            ctrl.fs.set_edge_info(ctrl.ui.active_edge_type, 'color', color_key)
            for edge in ctrl.forest.edges.values():
                edge.update()
        if color_key:
            log.info('(s) Changed relation color to: %s' % ctrl.cm.get_color_name(color_key))

    def getter(self):
        return ctrl.ui.active_edge_style.get('color')


class ControlPoint1X(KatajaAction):
    k_action_uid = 'control_point1_x'
    k_command = 'Adjust curvature, point 1 X'

    def method(self, value=None):
        """ Adjust specifix control point
        :param value: new value for given dimension, doesn't matter for reset.
        :return: None
        """
        if value is None:
            return
        for edge in ctrl.selected:
            if isinstance(edge, Edge):
                edge.shape_info.adjust_control_point_x0(value)

    def enabler(self):
        return bool(ctrl.ui.active_edge_style.get('control_points', 0))

    def getter(self):
        ca = ctrl.ui.active_edge_style.get('curve_adjustment', [])
        if ca:
            return ca[0][0]
        else:
            return 0


class ControlPoint2X(KatajaAction):
    k_action_uid = 'control_point2_x'
    k_command = 'Adjust curvature, point 2 X'

    def method(self, value=None):
        """ Adjust specifix control point
        :param value: new value for given dimension, doesn't matter for reset.
        :return: None
        """
        if value is None:
            return
        for edge in ctrl.selected:
            if isinstance(edge, Edge):
                edge.shape_info.adjust_control_point_x1(value)

    def enabler(self):
        return bool(ctrl.ui.active_edge_style.get('control_points', 0) > 1)

    def getter(self):
        ca = ctrl.ui.active_edge_style.get('curve_adjustment', [])
        if len(ca) > 1:
            return ca[1][0]
        else:
            return 0


class ControlPoint1Y(KatajaAction):
    k_action_uid = 'control_point1_y'
    k_command = 'Adjust curvature, point 1 Y'

    def method(self, value=None):
        """ Adjust specifix control point
        :param value: new value for given dimension, doesn't matter for reset.
        :return: None
        """
        if value is None:
            return
        for edge in ctrl.selected:
            if isinstance(edge, Edge):
                edge.shape_info.adjust_control_point_y0(value)

    def enabler(self):
        return bool(ctrl.ui.active_edge_style.get('control_points', 0))

    def getter(self):
        ca = ctrl.ui.active_edge_style.get('curve_adjustment', [])
        if ca:
            return ca[0][1]
        else:
            return 0


class ControlPoint2Y(KatajaAction):
    k_action_uid = 'control_point2_y'
    k_command = 'Adjust curvature, point 2 Y'

    def method(self, value=None):
        """ Adjust specifix control point
        :param value: new value for given dimension, doesn't matter for reset.
        :return: None
        """
        if value is None:
            return
        for edge in ctrl.selected:
            if isinstance(edge, Edge):
                edge.shape_info.adjust_control_point_y1(value)

    def enabler(self):
        return bool(ctrl.ui.active_edge_style.get('control_points', 0) > 1)

    def getter(self):
        ca = ctrl.ui.active_edge_style.get('curve_adjustment', [])
        if len(ca) > 1:
            return ca[1][1]
        else:
            return 0


class ResetControlPoints(KatajaAction):
    k_action_uid = 'reset_control_points'
    k_command = 'Reset control point'
    k_tooltip = 'Remove adjustments for these curves'

    def method(self):
        """ Reset all control points
        :return: None
        """
        for edge in ctrl.selected:
            if isinstance(edge, Edge):
                edge.shape_info.reset_control_points()


    def enabler(self):
        for edge in ctrl.selected:
            if isinstance(edge, Edge):
                if edge.curve_adjustment:
                    for x, y in edge.curve_adjustment:
                        if x or y:
                            return True
        return False


class LeafShapeX(KatajaAction):
    k_action_uid = 'leaf_shape_x'
    k_command = 'Edge shape width'
    k_tooltip = 'Adjust horizontal thickness of edges'

    def method(self, value=None):
        """ Change width of leaf-shaped edge.
        :param value: new value (float)
        """
        if value is None:
            return
        elif ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.shape_info.set_leaf_width(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.fs.set_shape_info(etype, 'leaf_x', value)
            ctrl.forest.redraw_edges(edge_type=etype)

    def enabler(self):
        return ctrl.ui.active_edge_style.get('fill', False)

    def getter(self):
        return ctrl.ui.active_edge_style.get('leaf_x')


class LeafShapeY(KatajaAction):
    k_action_uid = 'leaf_shape_y'
    k_command = 'Edge shape height'
    k_tooltip = 'Adjust vertical thickness of edges'

    def method(self, value=None):
        """ Change height of leaf-shaped edge.
        :param value: new value (float)
        """
        if value is None:
            return
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.shape_info.set_leaf_height(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.fs.set_shape_info(etype, 'leaf_y', value)
            ctrl.forest.redraw_edges(edge_type=etype)

    def getter(self):
        return ctrl.ui.active_edge_style.get('leaf_y')


class EdgeThickness(KatajaAction):
    k_action_uid = 'edge_thickness'
    k_command = 'Edge thickness'
    k_tooltip = 'Adjust fixed thickness for edges'

    def method(self, value=None):
        """ If edge is outline (not a leaf shape)
        :param value: new thickness (float)
        """
        if value is None:
            return
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.shape_info.change_thickness(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.fs.set_shape_info(etype, 'thickness', value)
            ctrl.forest.redraw_edges(edge_type=etype)

    def enabler(self):
        return ctrl.ui.active_edge_style.get('fill', None) is False

    def getter(self):
        return ctrl.ui.active_edge_style.get('thickness', 0)


class ChangeEdgeRelativeCurvatureX(KatajaAction):
    k_action_uid = 'change_edge_relative_curvature_x'
    k_command = 'Change horizontal curvature for edge'
    k_tooltip = 'Curvature value is relative to edge width'

    def method(self, value=None):
        """ Change curvature of arching lines. Curvature is relative to width
        :param value: float
        """
        if value is None:
            return
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.shape_info.change_edge_relative_curvature_x(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.fs.set_shape_info(etype, 'rel_dx', value * .01)
            ctrl.forest.redraw_edges(edge_type=etype)

    def enabler(self):
        return ctrl.ui.active_edge_style.get('relative', False) and \
               ctrl.ui.active_edge_style.get('control_points', 0)

    def getter(self):
        return ctrl.ui.active_edge_style.get('rel_dx', 0)


class ChangeEdgeRelativeCurvatureY(KatajaAction):
    k_action_uid = 'change_edge_relative_curvature_y'
    k_command = 'Change vertical curvature for edge'
    k_tooltip = 'Curvature value is relative to edge height'

    def method(self, value=None):
        """ Change curvature of arching lines. Curvature is relative to width
        :param value: float
        """
        if value is None:
            return
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.shape_info.change_edge_relative_curvature_y(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.fs.set_shape_info(etype, 'rel_dy', value * .01)
            ctrl.forest.redraw_edges(edge_type=etype)

    def enabler(self):
        return ctrl.ui.active_edge_style.get('relative', False) and \
               ctrl.ui.active_edge_style.get('control_points', 0)

    def getter(self):
        return ctrl.ui.active_edge_style.get('rel_dy', 0)


class ChangeEdgeFixedCurvatureX(KatajaAction):
    k_action_uid = 'change_edge_fixed_curvature_x'
    k_command = 'Change horizontal curvature for edge'
    k_tooltip = 'Curvature is fixed amount'

    def method(self, value=None):
        """ Change curvature of arching lines. Curvature is absolute pixels (X)
        :param value: float
        """
        if value is None:
            return
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.shape_info.change_edge_fixed_curvature_x(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.fs.set_shape_info(etype, 'fixed_dx', value * .01)
            ctrl.forest.redraw_edges(edge_type=etype)

    def enabler(self):
        return ctrl.ui.active_edge_style.get('relative', None) and \
               ctrl.ui.active_edge_style.get('control_points', 0)

    def getter(self):
        return ctrl.ui.active_edge_style.get('fixed_dx')


class ChangeEdgeFixedCurvatureY(KatajaAction):
    k_action_uid = 'change_edge_fixed_curvature_y'
    k_command = 'Change vertical curvature for edge'
    k_tooltip = 'Curvature is fixed amount'

    def method(self, value=None):
        """ Change curvature of arching lines. Curvature is absolute pixels (X)
        :param value: float
        """
        if value is None:
            return
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.shape_info.change_edge_fixed_curvature_y(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.fs.set_shape_info(etype, 'fixed_dy', value * .01)
            ctrl.forest.redraw_edges(edge_type=etype)

    def enabler(self):
        return ctrl.ui.active_edge_style.get('relative', None) and \
               ctrl.ui.active_edge_style.get('control_points', 0)

    def getter(self):
        return ctrl.ui.active_edge_style.get('fixed_dy')


class EdgeArrowheadStart(KatajaAction):
    k_action_uid = 'edge_arrowhead_start'
    k_command = 'Draw arrowhead at line start'

    def method(self, value):
        """ Draw arrowheads at start for given edges or edge type
        :param value: bool
        """
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.shape_info.set_arrowhead_at_start(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.fs.set_edge_info(etype, 'arrowhead_at_start', value)
            ctrl.forest.redraw_edges(edge_type=etype)
        panel = ctrl.ui.get_panel('LineOptionsPanel')
        if panel:
            panel.update_panel()

    def enabler(self):
        return ctrl.ui.active_edge_style

    def getter(self):
        return ctrl.ui.active_edge_style.get('arrowhead_at_start', False)


class EdgeArrowheadEnd(KatajaAction):
    k_action_uid = 'edge_arrowhead_end'
    k_command = 'Draw arrowhead at line end'

    def method(self, value):
        """ Draw arrowheads at end for given edges or edge type
        :param value: bool
        """
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.shape_info.set_arrowhead_at_end(value)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.fs.set_edge_info(etype, 'arrowhead_at_end', value)
            ctrl.forest.redraw_edges(edge_type=etype)
        panel = ctrl.ui.get_panel('LineOptionsPanel')
        if panel:
            panel.update_panel()

    def enabler(self):
        return ctrl.ui.active_edge_style

    def getter(self):
        return ctrl.ui.active_edge_style.get('arrowhead_at_end', False)


class EdgeShapeFill(KatajaAction):
    k_action_uid = 'edge_shape_fill'
    k_command = 'Set edge to be a filled shape'

    def method(self):
        """ Change edge to draw as filled shape
        :param value: bool
        """
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.shape_info.change_fill(True)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.fs.set_shape_info(etype, 'fill', True)
            ctrl.forest.redraw_edges(edge_type=etype)
        panel = ctrl.ui.get_panel('LineOptionsPanel')
        if panel:
            panel.update_panel()

    def enabler(self):
        return ctrl.ui.active_edge_style.get('fill', None) is not None

    def getter(self):
        return ctrl.ui.active_edge_style.get('fill', None)


class EdgeShapeLine(KatajaAction):
    k_action_uid = 'edge_shape_line'
    k_command = 'Set edge to be a fixed width line'

    def method(self):
        """ Change edge to draw as line instead of filled shape
        :param value: bool
        """
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.shape_info.change_fill(False)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.fs.set_shape_info(etype, 'fill', False)
            ctrl.forest.redraw_edges(edge_type=etype)
        panel = ctrl.ui.get_panel('LineOptionsPanel')
        if panel:
            panel.update_panel()

    def enabler(self):
        return ctrl.ui.active_edge_style.get('fill', None) is not None

    def getter(self):
        return not ctrl.ui.active_edge_style.get('fill', None)


class EdgeCurvatureRelative(KatajaAction):
    k_action_uid = 'edge_curvature_relative'
    k_command = 'Change line curvature to be relative to edge dimensions'

    def method(self, value):
        """ Change curvature computation type. Curvature can be 'relative' or 'fixed'
        :param value: 'relative' or 'fixed'
        """
        if value:
            ref = 'relative'
        else:
            ref = 'fixed'
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.shape_info.change_edge_curvature_reference(ref)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.fs.set_shape_info(etype, 'relative', value)
            ctrl.forest.redraw_edges(edge_type=etype)
        panel = ctrl.ui.get_panel('LineOptionsPanel')
        if panel:
            panel.update_panel()

    def enabler(self):
        return ctrl.ui.active_edge_style.get('relative', None) is not None and \
            ctrl.ui.active_edge_style.get('control_points', 0)

    def getter(self):
        return ctrl.ui.active_edge_style.get('relative', None)


class EdgeCurvatureFixed(KatajaAction):
    k_action_uid = 'edge_curvature_fixed'
    k_command = 'Change line curvature to be a pair of fixed values'

    def method(self, value):
        """ Change curvature computation type. Curvature can be 'relative' or 'fixed'
        :param value: bool
        """
        if value:
            ref = 'fixed'
        else:
            ref = 'relative'
        if ctrl.ui.scope_is_selection:
            for edge in ctrl.selected:
                if isinstance(edge, Edge):
                    edge.shape_info.change_edge_curvature_reference(ref)
        else:
            etype = ctrl.ui.active_edge_type
            ctrl.fs.set_shape_info(etype, 'relative', not value)
            ctrl.forest.redraw_edges(edge_type=etype)
        panel = ctrl.ui.get_panel('LineOptionsPanel')
        if panel:
            panel.update_panel()

    def enabler(self):
        return ctrl.ui.active_edge_style.get('relative', None) is not None and \
            ctrl.ui.active_edge_style.get('control_points', 0)

    def getter(self):
        return not ctrl.ui.active_edge_style.get('relative', None)
