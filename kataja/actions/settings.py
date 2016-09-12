# coding=utf-8
import kataja.globals as g
from kataja.actions._utils import get_ui_container
from kataja.singletons import ctrl, prefs, log
from kataja.saved.Edge import Edge
from kataja.saved.movables.Node import Node

a = {}


def customize_master_style(checked):
    """
    """
    panel = ctrl.ui.get_panel('StylePanel')
    panel.toggle_customization(checked)

def is_custom_panel_open():
    panel = ctrl.ui.get_panel('StylePanel')
    return panel.style_widgets.isVisible()

a['customize_master_style'] = {'command': 'Customize style',
                               'method': customize_master_style, 'trigger_args': True,
                               'undoable': False,
                               'tooltip': 'Modify the styles of lines and nodes',
                               'getter': is_custom_panel_open}


def change_master_style(sender=None):
    """
    """
    if sender:
        value = sender.currentData(256)
        prefs.style = value
    ctrl.forest.redraw_edges()
    return "Changed master style to '%s'" % value


def can_change_master_style():
    return ctrl.forest is not None and prefs.style


def get_master_style():
    return prefs.style

a['change_master_style'] = {'command': 'Change drawing style',
                            'method': change_master_style, 'sender_arg': True,
                            'undoable': False,
                            'tooltip': 'Changes the style of lines and nodes',
                            'enabler': can_change_master_style,
                            'getter': get_master_style}


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


def can_change_style_scope():
    return ctrl.forest is not None


def get_style_scope():
    return ctrl.ui.active_scope


a['style_scope'] = {'command': 'Select the scope for style changes',
                    'method': change_style_scope, 'sender_arg': True,
                    'undoable': False,
                    'tooltip': 'Select the scope for style changes',
                    'enabler': can_change_style_scope,
                    'getter': get_style_scope}


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


def can_reset_style_in_scope():
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

a['reset_style_in_scope'] = {'command': 'Reset style to original',
                             'method': reset_style_in_scope, 'sender_arg': True,
                             'undoable': True,
                             'tooltip': 'Reset the style to default within the selected scope',
                             'enabler': can_reset_style_in_scope}


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
        ctrl.ui.start_font_dialog(panel, font_key, font_key)


def can_select_font():
    if ctrl.ui.scope_is_selection:
        for item in ctrl.selected:
            if isinstance(item, Node):
                return True
        return False
    else:
        return True


a['start_font_dialog'] = {'command': 'Use a custom font',
                          'method': open_font_selector, 'sender_arg': True,
                          'undoable': False,
                          'tooltip': 'Select your own font for node labels',
                          'enabler': can_select_font}


def select_font():
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


def get_current_font():
    return ctrl.ui.active_node_style.get('font', None)

a['select_font'] = {'command': 'Change label font', 'method': select_font,
                    'tooltip': 'Change font for current selection or for a node type',
                    'enabler': can_select_font,
                    'getter': get_current_font}


def select_font_from_dialog():
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

a['select_font_from_dialog'] = {'command': 'Change label font', 'method': select_font_from_dialog,
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
    line_options = ctrl.ui.get_panel('LineOptionsPanel')

    if line_options:
        line_options.update_panel()
    log.info('(s) Changed relation shape to: %s' % shape)


def can_change_edge_shape():
    if ctrl.ui.scope_is_selection:
        for edge in ctrl.selected:
            if isinstance(edge, Edge):
                return True
        return False
    return True  # all scope options allow defining edge shape


def get_edge_shape():
    return ctrl.ui.active_edge_style.get('shape_name', None)

a['change_edge_shape'] = {'command': 'Change edge shape',
                          'method': change_edge_shape, 'sender_arg': True,
                          'tooltip': 'Change shapes of lines between objects',
                          'enabler': can_change_edge_shape,
                          'getter': get_edge_shape}


def change_node_color():
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


def can_change_node_color():
    if ctrl.ui.scope_is_selection:
        for item in ctrl.selected:
            if isinstance(item, Node):
                return True
        return False
    return True  # all scope options allow defining node color

def get_node_color():
    return ctrl.ui.active_node_style.get('color')

a['change_node_color'] = {'command': 'Change node color',
                          'method': change_node_color,
                          'tooltip': 'Change drawing color of nodes',
                          'enabler': can_change_node_color,
                          'getter': get_node_color}


def change_edge_color():
    """ Change edge shape for selection or in currently active edge type.
    :param sender: field that called this action
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


def get_edge_color():
    return ctrl.ui.active_edge_style.get('color')

a['change_edge_color'] = {'command': 'Change relation color',
                          'method': change_edge_color,
                          'tooltip': 'Change drawing color of relations',
                          'enabler': can_change_edge_shape,
                          'getter': get_edge_color}


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


def can_adjust_control_point0():
    return bool(ctrl.ui.active_edge_style.get('control_points', 0))


def can_adjust_control_point1():
    return bool(ctrl.ui.active_edge_style.get('control_points', 0) > 1)


def get_control_point0x():
    ca = ctrl.ui.active_edge_style.get('curve_adjustment', [])
    if ca:
        return ca[0][0]
    else:
        return 0

a['control_point1_x'] = {'command': 'Adjust curvature, point 1 X',
                         'method': adjust_control_point_x0,
                         'trigger_args': True,
                         'tooltip': 'Adjust curvature, point 1 X',
                         'enabler': can_adjust_control_point0,
                         'getter': get_control_point0x}


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


def get_control_point1x():
    ca = ctrl.ui.active_edge_style.get('curve_adjustment', [])
    if len(ca) > 1:
        return ca[1][0]
    else:
        return 0

a['control_point2_x'] = {'command': 'Adjust curvature, point 2 X',
                         'method': adjust_control_point_x1,
                         'trigger_args': True,
                         'tooltip': 'Adjust curvature, point 2 X',
                         'enabler': can_adjust_control_point1,
                         'getter': get_control_point1x}


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

def get_control_point0y():
    ca = ctrl.ui.active_edge_style.get('curve_adjustment', [])
    if ca:
        return ca[0][1]
    else:
        return 0

a['control_point1_y'] = {'command': 'Adjust curvature, point 1 Y',
                         'method': adjust_control_point_y0,
                         'trigger_args': True,
                         'tooltip': 'Adjust curvature, point 1 Y',
                         'enabler': can_adjust_control_point0,
                         'getter': get_control_point0y}


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

def get_control_point1y():
    ca = ctrl.ui.active_edge_style.get('curve_adjustment', [])
    if len(ca) > 1:
        return ca[1][1]
    else:
        return 0

a['control_point2_y'] = {'command': 'Adjust curvature, point 2 Y',
                         'method': adjust_control_point_y1,
                         'trigger_args': True,
                         'tooltip': 'Adjust curvature, point 2 Y',
                         'enabler': can_adjust_control_point1,
                         'getter': get_control_point1y}


def reset_control_points():
    """ Reset all control points
    :return: None
    """
    for edge in ctrl.selected:
        if isinstance(edge, Edge):
            edge.shape_info.reset_control_points()


def can_reset_control_points():
    for edge in ctrl.selected:
        if isinstance(edge, Edge):
            if edge.curve_adjustment:
                for x, y in edge.curve_adjustment:
                    if x or y:
                        return True
    return False

a['reset_control_points'] = {'command': 'Reset control point 1', 'method': reset_control_points,
                             'tooltip': 'Remove arc adjustments',
                             'enabler': can_reset_control_points}


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


def can_change_leaf_size():
    return ctrl.ui.active_edge_style.get('fill', False)


def get_leaf_width():
    return ctrl.ui.active_edge_style.get('leaf_x')

a['leaf_shape_x'] = {'command': 'Leaf shape width', 'method': change_leaf_width,
                     'trigger_args': True, 'tooltip': 'Leaf shape width',
                     'enabler': can_change_leaf_size,
                     'getter': get_leaf_width}


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


def get_leaf_height():
    return ctrl.ui.active_edge_style.get('leaf_y')


a['leaf_shape_y'] = {'command': 'Leaf shape height', 'method': change_leaf_height,
                     'trigger_args': True,
                     'tooltip': 'Leaf shape height',
                     'enabler': can_change_leaf_size,
                     'getter': get_leaf_height}


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


def can_change_edge_thickness():
    return ctrl.ui.active_edge_style.get('fill', None) is False

def get_edge_thickness():
    return ctrl.ui.active_edge_style.get('thickness', 0)

a['edge_thickness'] = {'command': 'Line thickness',
                       'method': change_edge_thickness, 'trigger_args': True,
                       'tooltip': 'Line thickness',
                       'enabler': can_change_edge_thickness,
                       'getter': get_edge_thickness}


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


def can_change_relative_curvature():
    return ctrl.ui.active_edge_style.get('relative', False) and \
           ctrl.ui.active_edge_style.get('control_points', 0)


def get_relative_curvature_x():
    return ctrl.ui.active_edge_style.get('rel_dx', 0)

a['change_edge_relative_curvature_x'] = {'command': 'Change curvature for edge in X',
                                         'trigger_args': True,
                                         'method': change_edge_relative_curvature_x,
                                         'tooltip': 'Curvature as relative to edge width',
                                         'enabler': can_change_relative_curvature,
                                         'getter': get_relative_curvature_x}


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


def get_relative_curvature_y():
    return ctrl.ui.active_edge_style.get('rel_dy', 0)


a['change_edge_relative_curvature_y'] = {'command': 'Change curvature for edge in Y',
                                         'trigger_args': True,
                                         'method': change_edge_relative_curvature_y,
                                         'tooltip': 'Curvature as relative to edge height',
                                         'enabler': can_change_relative_curvature,
                                         'getter': get_relative_curvature_y}


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


def can_change_fixed_curvature():
    return ctrl.ui.active_edge_style.get('relative', None) and \
           ctrl.ui.active_edge_style.get('control_points', 0)


def get_fixed_curvature_x():
    return ctrl.ui.active_edge_style.get('fixed_dx')

a['change_edge_fixed_curvature_x'] = {'command': 'Change curvature for edge in X',
                                      'trigger_args': True,
                                      'method': change_edge_fixed_curvature_x,
                                      'tooltip': 'Curvature in edge, fixed X value in pixels',
                                      'enabler': can_change_fixed_curvature,
                                      'getter': get_fixed_curvature_x}


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


def get_fixed_curvature_y():
    return ctrl.ui.active_edge_style.get('fixed_dy')

a['change_edge_fixed_curvature_y'] = {'command': 'Change curvature for edge in Y',
                                      'trigger_args': True,
                                      'method': change_edge_fixed_curvature_y,
                                      'tooltip': 'Curvature in edge, fixed Y value in pixels',
                                      'enabler': can_change_fixed_curvature,
                                      'getter': get_fixed_curvature_y}


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
    panel = ctrl.ui.get_panel('LineOptionsPanel')
    if panel:
        panel.update_panel()


def can_toggle_arrowheads():
    return ctrl.ui.active_edge_style


def has_arrowhead_at_start():
    return ctrl.ui.active_edge_style.get('arrowhead_at_start', False)

a['edge_arrowhead_start'] = {
    'command': 'Draw arrowhead at line start',
    'method': toggle_edge_arrowhead_at_start, 'trigger_args': True,
    'tooltip': 'Draw arrowhead at line start',
    'enabler': can_toggle_arrowheads,
    'getter': has_arrowhead_at_start}


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
    panel = ctrl.ui.get_panel('LineOptionsPanel')
    if panel:
        panel.update_panel()


def has_arrowhead_at_end():
    return ctrl.ui.active_edge_style.get('arrowhead_at_end', False)

a['edge_arrowhead_end'] = {
    'command': 'Draw arrowhead at line end',
    'method': toggle_edge_arrowhead_at_end, 'trigger_args': True,
    'tooltip': 'Draw arrowhead at line end',
    'enabler': can_toggle_arrowheads,
    'getter': has_arrowhead_at_end}


def change_edge_shape_to_filled():
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


def can_change_edge_shape_to_filled():
    return ctrl.ui.active_edge_style.get('fill', None) is not None


def is_edge_shape_filled():
    return ctrl.ui.active_edge_style.get('fill', None)

a['edge_shape_fill'] = {
    'command': 'Set edge to be drawn as filled shape',
    'method': change_edge_shape_to_filled,
    'tooltip': 'Set edge to be drawn as filled shape',
    'enabler': can_change_edge_shape_to_filled,
    'getter': is_edge_shape_filled}


def change_edge_shape_to_line():
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


def is_edge_shape_line():
    return not ctrl.ui.active_edge_style.get('fill', None)

a['edge_shape_line'] = {
    'command': 'Set edge to be drawn as line with fixed width',
    'method': change_edge_shape_to_line,
    'tooltip': 'Set edge to be drawn as line with fixed width',
    'enabler': can_change_edge_shape_to_filled,
    'getter': is_edge_shape_line}


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
    panel = ctrl.ui.get_panel('LineOptionsPanel')
    if panel:
        panel.update_panel()


def can_change_edge_shape_to_relative():
    return ctrl.ui.active_edge_style.get('relative', None) is not None and \
        ctrl.ui.active_edge_style.get('control_points', 0)


def is_edge_shape_relative():
    return ctrl.ui.active_edge_style.get('relative', None)

a['edge_curvature_relative'] = {
    'command': 'Change line curvature to be relative to edge dimensions',
    'method': change_edge_curvature_to_relative, 'trigger_args': True,
    'tooltip': 'Change line curvature to be relative to edge dimensions',
    'enabler': can_change_edge_shape_to_relative,
    'getter': is_edge_shape_relative}


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
    panel = ctrl.ui.get_panel('LineOptionsPanel')
    if panel:
        panel.update_panel()


def is_edge_shape_fixed():
    return not ctrl.ui.active_edge_style.get('relative', None)

a['edge_curvature_fixed'] = {
    'command': 'Change line curvature to be a fixed amount',
    'method': change_edge_curvature_to_fixed, 'trigger_args': True,
    'tooltip': 'Change line curvature to be a fixed amount',
    'enabler': can_change_edge_shape_to_relative,
    'getter': is_edge_shape_fixed}


