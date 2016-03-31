# coding=utf-8
import kataja.globals as g
from kataja.actions._utils import get_ui_container
from kataja.singletons import ctrl
from saved.Edge import Edge
from saved.movables.Node import Node

a = {}


def customize_master_style(checked):
    """
    """
    panel = ctrl.ui.get_panel(g.STYLE)
    panel.toggle_customization(checked)

a['customize_master_style'] = {'command': 'Customize style',
                               'method': customize_master_style, 'trigger_args': True,
                               'undoable': False,
                               'tooltip': 'Modify the styles of lines and nodes'}


def change_master_style(style_id):
    """
    """
    print(style_id)

a['change_master_style'] = {'command': 'Change drawing style',
                            'method': change_master_style, 'trigger_args': True,
                            'undoable': False,
                            'tooltip': 'Changes the style of lines and nodes'}


def change_style_scope(sender=None):
    """ Change drawing panel to work on selected nodes, constituent nodes or
    other available
    nodes
    :param sender: field that called this action
    :return: None
    """
    if sender:
        value = sender.currentData(256)
        ctrl.ui.set_scope(value)


a['style_scope'] = {'command': 'Select the scope for style changes',
                    'method': change_style_scope, 'sender_arg': True,
                    'undoable': False,
                    'tooltip': 'Select the scope for style changes'}


def reset_style_in_scope(sender=None):
    """ Restore style to original
    :param sender: field that called this action
    :return: None
    """
    if ctrl.ui.scope_is_selection:
        for item in ctrl.selected:
            if hasattr(item, 'reset_style'):
                item.reset_style()
    ctrl.fs.reset_node_style(ctrl.ui.active_node_type)
    ctrl.fs.reset_edge_style(ctrl.ui.active_edge_type)
    ctrl.forest.redraw_edges(ctrl.ui.active_edge_type)


a['reset_style_in_scope'] = {'command': 'Reset style to original',
                             'method': reset_style_in_scope, 'sender_arg': True,
                             'undoable': True,
                             'tooltip': 'Reset the style to default within the selected scope'}


def open_font_selector(sender=None):
    """ Change drawing panel to work on selected nodes, constituent nodes or
    other available
    nodes
    :param sender: field that called this action
    :return: None
    """
    if sender:
        panel = get_ui_container(sender)
        font_key = panel.cached_font_id
        ctrl.ui.start_font_dialog(panel, 'node_font', font_key)


a['start_font_dialog'] = {'command': 'Use a custom font',
                          'method': open_font_selector, 'sender_arg': True,
                          'undoable': False, 'tooltip': 'Select custom font '
                                                        'for node label'}


def select_font():
    """ Change drawing panel to work on selected nodes, constituent nodes or
    other available nodes
    :return: None
    """
    panel = ctrl.ui.get_panel(g.STYLE)
    if panel:
        font_id = panel.font_selector.currentData() or panel.cached_font_id
        panel.update_font_selector(font_id)
    if ctrl.ui.scope_is_selection:
        for node in ctrl.selected:
            if isinstance(node, Node):
                node.font_id = font_id
                node.update_label()
    else:
        ctrl.fs.set_node_info(ctrl.ui.active_node_type, 'font', font_id)
        for node in ctrl.forest.nodes.values():
            node.update_label()

a['select_font'] = {'command': 'Change label font', 'method': select_font,
                    'tooltip': 'Change font for current selection or for a node type'}


def change_edge_shape(sender=None):
    """ Change edge shape for selection or in currently active edge type.
    :param sender: field that called this action
    :return: None
    """
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
    line_options = ctrl.ui.get_panel(g.LINE_OPTIONS)

    if line_options:
        line_options.update_panel()
    ctrl.main.add_message('(s) Changed relation shape to: %s' % shape)


a['change_edge_shape'] = {'command': 'Change relation shape',
                          'method': change_edge_shape, 'sender_arg': True,
                          'tooltip': 'Change shape of relations (lines, '
                                     'edges) between objects'}


def change_node_color():
    """ Change color for selection or in currently active edge type.
    :return: None
    """
    panel = ctrl.ui.get_panel(g.STYLE)
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
        ctrl.fs.set_node_info(ctrl.ui.active_node_type, 'color', color_key)
        for node in ctrl.forest.nodes.values():
            node.update_label()
    if color_key:
        ctrl.main.add_message('(s) Changed node color to: %s' % ctrl.cm.get_color_name(color_key))


a['change_node_color'] = {'command': 'Change node color',
                          'method': change_node_color,
                          'tooltip': 'Change drawing color of nodes'}


def change_edge_color():
    """ Change edge shape for selection or in currently active edge type.
    :param sender: field that called this action
    :return: None
    """
    panel = ctrl.ui.get_panel(g.STYLE)
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
        ctrl.main.add_message(
            '(s) Changed relation color to: %s' % ctrl.cm.get_color_name(color_key))


a['change_edge_color'] = {'command': 'Change relation color',
                          'method': change_edge_color,
                          'tooltip': 'Change drawing color of relations'}


def adjust_control_point_x0(value=None):
    """ Adjust specifix control point
    :param value: new value for given dimension, doesn't matter for reset.
    :return: None
    """
    if value is None:
        return
    for edge in ctrl.selected:
        if isinstance(edge, Edge):
            edge.shape_info.adjust_control_point_x0(value)


a['control_point1_x'] = {'command': 'Adjust curvature, point 1 X',
                         'method': adjust_control_point_x0,
                         'trigger_args': True,
                         'tooltip': 'Adjust curvature, point 1 X'}


def adjust_control_point_x1(value=None):
    """ Adjust specifix control point
    :param value: new value for given dimension, doesn't matter for reset.
    :return: None
    """
    if value is None:
        return
    for edge in ctrl.selected:
        if isinstance(edge, Edge):
            edge.shape_info.adjust_control_point_x1(value)


a['control_point2_x'] = {'command': 'Adjust curvature, point 2 X',
                         'method': adjust_control_point_x1,
                         'trigger_args': True,
                         'tooltip': 'Adjust curvature, point 2 X'}


def adjust_control_point_y0(value=None):
    """ Adjust specifix control point
    :param value: new value for given dimension, doesn't matter for reset.
    :return: None
    """
    if value is None:
        return
    for edge in ctrl.selected:
        if isinstance(edge, Edge):
            edge.shape_info.adjust_control_point_y0(value)


a['control_point1_y'] = {'command': 'Adjust curvature, point 1 Y',
                         'method': adjust_control_point_y0,
                         'trigger_args': True,
                         'tooltip': 'Adjust curvature, point 1 Y'}


def adjust_control_point_y1(value=None):
    """ Adjust specifix control point
    :param value: new value for given dimension, doesn't matter for reset.
    :return: None
    """
    if value is None:
        return
    for edge in ctrl.selected:
        if isinstance(edge, Edge):
            edge.shape_info.adjust_control_point_y1(value)


a['control_point2_y'] = {'command': 'Adjust curvature, point 2 Y',
                         'method': adjust_control_point_y1,
                         'trigger_args': True,
                         'tooltip': 'Adjust curvature, point 2 Y'}


def reset_control_points():
    """ Reset all control points
    :return: None
    """
    for edge in ctrl.selected:
        if isinstance(edge, Edge):
            edge.shape_info.reset_control_points()


a['reset_control_points'] = {'command': 'Reset control point 1', 'method': reset_control_points,
                             'tooltip': 'Remove arc adjustments'}


def change_leaf_width(value=None):
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

a['leaf_shape_x'] = {'command': 'Leaf shape width', 'method': change_leaf_width,
                     'trigger_args': True, 'tooltip': 'Leaf shape width'}


def change_leaf_height(value=None):
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

a['leaf_shape_y'] = {'command': 'Leaf shape height', 'method': change_leaf_height,
                     'trigger_args': True,
                     'tooltip': 'Leaf shape height'}


def change_edge_thickness(value=None):
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

a['edge_thickness'] = {'command': 'Line thickness',
                       'method': change_edge_thickness, 'trigger_args': True,
                       'tooltip': 'Line thickness'}


def change_edge_relative_curvature_x(value=None):
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

a['change_edge_relative_curvature_x'] = {'command': 'Change curvature for edge in X',
                                         'trigger_args': True,
                                         'method': change_edge_relative_curvature_x,
                                         'tooltip': 'Curvature as relative to edge width'}


def change_edge_relative_curvature_y(value=None):
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

a['change_edge_relative_curvature_y'] = {'command': 'Change curvature for edge in Y',
                                         'trigger_args': True,
                                         'method': change_edge_relative_curvature_y,
                                         'tooltip': 'Curvature as relative to edge height'}


def change_edge_fixed_curvature_x(value=None):
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

a['change_edge_fixed_curvature_x'] = {'command': 'Change curvature for edge in X',
                                      'trigger_args': True,
                                      'method': change_edge_fixed_curvature_x,
                                      'tooltip': 'Curvature in edge, fixed X value in pixels'}


def change_edge_fixed_curvature_y(value=None):
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

a['change_edge_fixed_curvature_y'] = {'command': 'Change curvature for edge in Y',
                                      'trigger_args': True,
                                      'method': change_edge_fixed_curvature_y,
                                      'tooltip': 'Curvature in edge, fixed Y value in pixels'}

def toggle_edge_arrowhead_at_start(value):
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
    panel = ctrl.ui.get_panel(g.LINE_OPTIONS)
    if panel:
        panel.update_panel()

a['edge_arrowhead_start'] = {
    'command': 'Draw arrowhead at line start',
    'method': toggle_edge_arrowhead_at_start, 'trigger_args': True,
    'tooltip': 'Draw arrowhead at line start'}


def toggle_edge_arrowhead_at_end(value):
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
    panel = ctrl.ui.get_panel(g.LINE_OPTIONS)
    if panel:
        panel.update_panel()

a['edge_arrowhead_end'] = {
    'command': 'Draw arrowhead at line end',
    'method': toggle_edge_arrowhead_at_end, 'trigger_args': True,
    'tooltip': 'Draw arrowhead at line end'}


def change_edge_shape_to_filled(value):
    """ Change edge to draw as filled shape
    :param value: bool
    """
    fill = value
    if ctrl.ui.scope_is_selection:
        for edge in ctrl.selected:
            if isinstance(edge, Edge):
                edge.shape_info.change_fill(fill)
    else:
        etype = ctrl.ui.active_edge_type
        ctrl.fs.set_shape_info(etype, 'fill', fill)
        ctrl.forest.redraw_edges(edge_type=etype)
    panel = ctrl.ui.get_panel(g.LINE_OPTIONS)
    if panel:
        panel.update_panel()

a['edge_shape_fill'] = {
    'command': 'Set edge to be drawn as filled shape',
    'method': change_edge_shape_to_filled, 'trigger_args': True,
    'tooltip': 'Set edge to be drawn as filled shape'}


def change_edge_shape_to_line(value):
    """ Change edge to draw as line instead of filled shape
    :param value: bool
    """
    fill = not value
    if ctrl.ui.scope_is_selection:
        for edge in ctrl.selected:
            if isinstance(edge, Edge):
                edge.shape_info.change_fill(fill)
    else:
        etype = ctrl.ui.active_edge_type
        ctrl.fs.set_shape_info(etype, 'fill', fill)
        ctrl.forest.redraw_edges(edge_type=etype)
    panel = ctrl.ui.get_panel(g.LINE_OPTIONS)
    if panel:
        panel.update_panel()

a['edge_shape_line'] = {
    'command': 'Set edge to be drawn as line with fixed width',
    'method': change_edge_shape_to_line, 'trigger_args': True,
    'tooltip': 'Set edge to be drawn as line with fixed width'}


def change_edge_curvature_to_relative(value):
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
    panel = ctrl.ui.get_panel(g.LINE_OPTIONS)
    if panel:
        panel.update_panel()

a['edge_curvature_relative'] = {
    'command': 'Change line curvature to be relative to edge dimensions',
    'method': change_edge_curvature_to_relative, 'trigger_args': True,
    'tooltip': 'Change line curvature to be relative to edge dimensions'}


def change_edge_curvature_to_fixed(value):
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
    panel = ctrl.ui.get_panel(g.LINE_OPTIONS)
    if panel:
        panel.update_panel()


a['edge_curvature_fixed'] = {
    'command': 'Change line curvature to be a fixed amount',
    'method': change_edge_curvature_to_fixed, 'trigger_args': True,
    'tooltip': 'Change line curvature to be a fixed amount'}

