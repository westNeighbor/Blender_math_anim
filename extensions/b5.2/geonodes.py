import bpy
import mathutils
import os
import time
from . import variables as vb
from .utils import get_font_name, get_unicode_name

def import_anim_nodegroups(node_group_name: list):
    filepath = os.path.join(os.path.dirname(__file__), "anim_setups/geoAnimGroups.blend")
    node_group_name = node_group_name
    if not node_group_name:
        node_group_name = ["Curve Morph Anim", "Grow Anim", "Writing Curve Anim", "Edge Flow Anim", "Color Glow Anim"]  # Name of the node group to import
    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        for node_group in node_group_name:
            if node_group not in bpy.data.node_groups.keys():
                if node_group in data_from.node_groups:
                    data_to.node_groups.append(node_group)
                    #print(f"Node group '{node_group}' successfully imported")
                else:
                    print(f"Node group '{node_group}' not exist in '{filepath}'")
                    ...

def import_char_nodegroups(node_group_name: list):
    filepath = os.path.join(os.path.dirname(__file__), "anim_setups/geoAnimGroups.blend")
    node_group_name = node_group_name
    if not node_group_name:
        node_group_name = ['char_settings', 'apply_settings', 'char_instance_anim', 'char_curve_anim', 'stroke_instance_anim', 'stroke_curve_anim', 'fill_instance_anim', 'fill_curve_anim', 'char_nodegroup', 'quad_nodegroup', 'curve_nodegroup']  # Name of the node group to import
    with bpy.data.libraries.load(filepath, link=False) as (data_from, data_to):
        for node_group in node_group_name:
            if node_group not in bpy.data.node_groups.keys():
                if node_group in data_from.node_groups:
                    data_to.node_groups.append(node_group)
                    #print(f"Node group '{node_group}' successfully imported")
                else:
                    print(f"Node group '{node_group}' not exist in '{filepath}'")
                    ...

def font_scale(char, font_path, bbox_h):
    if char and bbox_h > 0.0:
        # evalue the char bbox height with default size 1m, so can propagate the real size with bbox_h
        # use geometry nodes to achieve this
        mesh_name = "math_anim_emptyMesh"
        obj_name = "math_anim_emptyMeshObject"
        geoMd_name = "emptyGeoNodes"
        if not char:
            return 0.0, 0.0, 0.0, 0.0
        if obj_name in bpy.data.objects and bpy.data.objects[obj_name].data.name == mesh_name:
            obj = bpy.data.objects[obj_name]
            bpy.context.collection.objects.link(obj)
            nodegroup = obj.modifiers[geoMd_name].node_group
            char_node = nodegroup.nodes["String to Curves"]
            char_node.inputs['String'].default_value = char
            char_node.inputs['Size'].default_value = 1.0
            if font_path:
                char_node.inputs["Font"].default_value = bpy.data.fonts.load(font_path, check_existing=True)

            depsgraph = bpy.context.evaluated_depsgraph_get()
            obj_eval = obj.evaluated_get(depsgraph)
            eval_h = obj_eval.bound_box[2][1] - obj_eval.bound_box[1][1]
            actual_fontsize = bbox_h/eval_h
            char_node.inputs['Size'].default_value = actual_fontsize
            depsgraph = bpy.context.evaluated_depsgraph_get()
            obj_eval = obj.evaluated_get(depsgraph)
            actual_bbox_w = obj_eval.bound_box[4][0] - obj_eval.bound_box[3][0]
            middle_y = (obj_eval.bound_box[2][1] + obj_eval.bound_box[1][1])/2.0
            middle_x = (obj_eval.bound_box[4][0] + obj_eval.bound_box[3][0])/2.0
            bpy.context.collection.objects.unlink(obj)
            return actual_fontsize, actual_bbox_w, middle_x, middle_y
        else:
            mesh = bpy.data.meshes.new(name=mesh_name)
            obj = bpy.data.objects.new(name=obj_name, object_data=mesh)
            bpy.context.collection.objects.link(obj)
            geometryMd = obj.modifiers.new(name=geoMd_name, type='NODES')
            nodegroup = bpy.data.node_groups.new(type = 'GeometryNodeTree', name = "emptyNodeGroup")
            geometryMd.node_group = nodegroup

            nodegroup.interface.new_socket(name="Geometry", in_out='OUTPUT',socket_type='NodeSocketGeometry')
            node_x = 0
            char_node, node_x, _ = create_node(nodegroup, "GeometryNodeStringToCurves", node_x, 0, 50, 0) # next node right
            realizeInstance_node, node_x, _ = create_node(nodegroup, "GeometryNodeRealizeInstances", node_x, 0, 50, 0) # next node right
            bbox_node, node_x, _ = create_node(nodegroup, "GeometryNodeBoundBox", node_x, 0, 50, 0) # next node right
            bbox_node.inputs["Use Radius"].default_value = False
            out_node, _, _ = create_node(nodegroup, "NodeGroupOutput", node_x, 0, 0, 0)

            nodegroup.links.new(char_node.outputs["Curve Instances"], realizeInstance_node.inputs["Geometry"])
            nodegroup.links.new(realizeInstance_node.outputs["Geometry"], bbox_node.inputs["Geometry"])
            nodegroup.links.new(bbox_node.outputs["Bounding Box"], out_node.inputs["Geometry"])

            char_node.inputs['String'].default_value = char
            char_node.inputs['Size'].default_value = 1.0
            if font_path:
                char_node.inputs["Font"].default_value = bpy.data.fonts.load(font_path)

            depsgraph = bpy.context.evaluated_depsgraph_get()
            obj_eval = obj.evaluated_get(depsgraph)
            eval_h = obj_eval.bound_box[2][1] - obj_eval.bound_box[1][1]
            actual_fontsize = bbox_h/eval_h
            char_node.inputs['Size'].default_value = actual_fontsize
            depsgraph = bpy.context.evaluated_depsgraph_get()
            obj_eval = obj.evaluated_get(depsgraph)
            actual_bbox_w = obj_eval.bound_box[4][0] - obj_eval.bound_box[3][0]
            middle_y = (obj_eval.bound_box[2][1] + obj_eval.bound_box[1][1])/2.0
            middle_x = (obj_eval.bound_box[4][0] + obj_eval.bound_box[3][0])/2.0
            bpy.context.collection.objects.unlink(obj)
            return actual_fontsize, actual_bbox_w, middle_x, middle_y

    return 0.0, 0.0, 0.0, 0.0

def create_node(node_tree, type_name, node_x_location, node_y_location, x_gap=20, y_gap=20):
    """Creates a node of a given type, and sets/updates the location of the node.
    Returning the node object and the next location for the next node.
    """
    node_obj = node_tree.nodes.new(type=type_name)
    node_obj.location.x = node_x_location
    node_obj.location.y = node_y_location
    if x_gap > 0:
        node_x_location += node_obj.width + x_gap
    elif x_gap < 0:
        node_x_location -= node_obj.width - x_gap

    if y_gap > 0:
        node_y_location += node_obj.height + y_gap
    elif y_gap < 0:
        node_y_location -= node_obj.height - y_gap

    return node_obj, node_x_location, node_y_location

def arrange_nodes(refer_node, target_node, direction="r", x_gap=20, y_gap=20):
    """ Arrange targart relative to reference node, direction can be 'r', 'l', 't', 'b'
    stand for right, left, top, or bottom
    returning the target node final location,
    correct way should be use node.dimentsions.x to get the width, but in python code environment,
    it always get 0, tried node_tree.update_tag() and context.view_layer.update(), no effect
    the following way has no effect too
    bpy.ops.wm.redraw_timer(type='DRAW_WIN', iterations=1)
    bpy.context.area.tag_redraw()
    """
    refer_x = refer_node.location.x
    refer_y = refer_node.location.y
    refer_w = refer_node.width
    refer_h = refer_node.height
    target_w = target_node.width
    target_h = target_node.height

    if direction == 'r':
        target_node.location.x = refer_x + refer_w + x_gap
        target_node.location.y = refer_y
    elif direction == 'l':
        target_node.location.x = refer_x - x_gap - target_w
        target_node.location.y = refer_y
    elif direction == 't':
        target_node.location.y = refer_y + target_h + y_gap
        target_node.location.x = refer_x
    elif direction == 'b':
        target_node.location.y = refer_y - y_gap - refer_h
        target_node.location.x = refer_x
    else:
        print("Give a right option to arrange the node, can be 'r' for right, 'l' for left, 't' for top or 'b' for bottom")

    return target_node.location.x, target_node.location.y

def create_char_nodegroup(name="char_nodegroup"):
    char_nodegroup = bpy.data.node_groups.new(type = 'GeometryNodeTree', name = name)
    char_nodegroup.interface.new_socket(name="Curve", in_out='OUTPUT',socket_type='NodeSocketGeometry')
    char_node, char_node_x, _ = create_node(char_nodegroup, "GeometryNodeStringToCurves", 0, 0, 30, 0) # next node right
    pos_node, char_node_x, _ = create_node(char_nodegroup, "GeometryNodeSetPosition", char_node_x, 0, 30, 0) # next node down
    scale_node, char_node_x, _ = create_node(char_nodegroup, "GeometryNodeScaleInstances", char_node_x, 0, 30, 0) # next node on right
    storeColor_node, char_node_x, _ = create_node(char_nodegroup, "GeometryNodeStoreNamedAttribute", char_node_x, 0, 30, 0) # next node on right
    storeColor_node.name = "Color Attribute"
    storeColor_node.data_type = "FLOAT_VECTOR"
    storeColor_node.domain = "INSTANCE"
    storeColor_node.inputs["Name"].default_value = "color"
    storeAlpha_node, char_node_x, _ = create_node(char_nodegroup, "GeometryNodeStoreNamedAttribute", char_node_x, 0, 30, 0) # next node on right
    storeAlpha_node.name = "Alpha Attribute"
    storeAlpha_node.data_type = "FLOAT"
    storeAlpha_node.domain = "INSTANCE"
    storeAlpha_node.inputs["Name"].default_value = "alpha"
    realizeInstance_node, char_node_x, _ = create_node(char_nodegroup, "GeometryNodeRealizeInstances", char_node_x, 0, 30, 0) # next node on right
    '''
    setRaduis_node, char_node_x, _ = create_node(char_nodegroup, "GeometryNodeSetCurveRadius", char_node_x, 0, 30, 0) # next node on right
    curveToGP_node, char_node_x, _ = create_node(char_nodegroup, "GeometryNodeCurvesToGreasePencil", char_node_x, 0, 30, 0) # next node on right
    curveToGP_node.inputs['Instances As Layers'].default_value = False
    setMaterial_node, char_node_x, _ = create_node(char_nodegroup, "GeometryNodeSetMaterial", char_node_x, 0, 30, 0) # next node on right
    '''
    char_out_node, _, _ = create_node(char_nodegroup, "NodeGroupOutput", char_node_x, 0)
    char_nodegroup.links.new(char_node.outputs['Curve Instances'], pos_node.inputs['Geometry'])
    char_nodegroup.links.new(pos_node.outputs['Geometry'], scale_node.inputs['Instances'])
    char_nodegroup.links.new(char_node.outputs['Pivot Point'], scale_node.inputs['Center'])
    char_nodegroup.links.new(scale_node.outputs['Instances'], storeColor_node.inputs['Geometry'])
    char_nodegroup.links.new(storeColor_node.outputs['Geometry'], storeAlpha_node.inputs['Geometry'])
    char_nodegroup.links.new(storeAlpha_node.outputs['Geometry'], realizeInstance_node.inputs['Geometry'])
    char_nodegroup.links.new(realizeInstance_node.outputs['Geometry'], char_out_node.inputs['Curve'])

    return char_nodegroup

def create_quad_nodegroup(name="quad_nodegroup"):
    quad_nodegroup = bpy.data.node_groups.new(type = 'GeometryNodeTree', name = name)
    quad_nodegroup.interface.new_socket(name="Curve", in_out='OUTPUT',socket_type='NodeSocketGeometry')
    node_x = 0
    node_y = 0
    x_gap = 50
    y_gap = 10
    quad_node, node_x, node_y = create_node(quad_nodegroup, "GeometryNodeCurvePrimitiveQuadrilateral", node_x, node_y, x_gap, 0) # next on right
    quad_node.mode = 'POINTS'
    quad_node.inputs['Width'].hide = True
    geo_to_ins_node, node_x, node_y  = create_node(quad_nodegroup, "GeometryNodeGeometryToInstance", node_x, node_y, x_gap, 0) # next on right
    pos_node, node_x, node_y  = create_node(quad_nodegroup, "GeometryNodeSetPosition", node_x, node_y, x_gap, 0) # next on right
    realizeInstance_node, node_x, node_y  = create_node(quad_nodegroup, "GeometryNodeRealizeInstances", node_x, node_y, x_gap, 0) # next on right
    out_node, node_x, node_y  = create_node(quad_nodegroup, "NodeGroupOutput", node_x, node_y, x_gap, 0) # next on right

    quad_nodegroup.links.new(quad_node.outputs['Curve'], geo_to_ins_node.inputs['Geometry'])
    quad_nodegroup.links.new(geo_to_ins_node.outputs['Instances'], pos_node.inputs['Geometry'])
    quad_nodegroup.links.new(pos_node.outputs['Geometry'], realizeInstance_node.inputs['Geometry'])
    quad_nodegroup.links.new(realizeInstance_node.outputs['Geometry'], out_node.inputs['Curve'])

    return quad_nodegroup

def create_curve_nodegroup(name="curve_nodegroup", control_points=[], left_handles=[], right_handles=[], line_width=0.0):
    curve_nodegroup = bpy.data.node_groups.new(type = 'GeometryNodeTree', name = name)
    curve_nodegroup.interface.new_socket(name="Curve", in_out='OUTPUT',socket_type='NodeSocketGeometry')
    node_x = 0
    node_y = 0
    x_gap = 50
    y_gap = 10
    join_node, node_x, node_y  = create_node(curve_nodegroup, "GeometryNodeJoinGeometry", node_x + x_gap, node_y, x_gap*(-1.0), 0) # for the control points join
    join_node.name = "Control_points Join Geometry"
    node_yy = node_y
    for i in range(len(control_points)-1,-1,-1):
        point_node, node_x, node_yy = create_node(curve_nodegroup, "GeometryNodePoints", node_x, node_yy, 0, y_gap) # next on top
        point_node.inputs['Position'].default_value = control_points[i]
        point_node.inputs['Position'].hide = True
        point_node.inputs['Count'].hide = True
        point_node.inputs['Radius'].hide = True
        point_node.name = "Control Points"
        curve_nodegroup.links.new(point_node.outputs['Points'], join_node.inputs['Geometry'])

    point_to_curve_node, node_x, node_y = create_node(curve_nodegroup, "GeometryNodePointsToCurves", node_x + x_gap*2, node_y, x_gap, 0) # next on right
    node_x, _ = arrange_nodes(join_node, point_to_curve_node, 'r', 50, 0)
    curve_nodegroup.links.new(join_node.outputs['Geometry'], point_to_curve_node.inputs['Points'])
    set_type_node, node_x, node_y = create_node(curve_nodegroup, "GeometryNodeCurveSplineType", node_x + point_to_curve_node.width + x_gap, node_y, x_gap, 0) # next on right
    set_type_node.spline_type = 'BEZIER'
    curve_nodegroup.links.new(point_to_curve_node.outputs['Curves'], set_type_node.inputs['Curve'])
    set_lhandle_node, node_x, node_y = create_node(curve_nodegroup, "GeometryNodeSetCurveHandlePositions", node_x, node_y, x_gap, 0) # next on right
    set_lhandle_node.mode = 'LEFT'
    curve_nodegroup.links.new(set_type_node.outputs['Curve'], set_lhandle_node.inputs['Curve'])

    # set left handle positions
    sample_index_node, node_xx, node_yy = create_node(curve_nodegroup, "GeometryNodeSampleIndex", set_type_node.location.x, set_type_node.location.y-set_type_node.height-30 , -50, -50) # next on left
    sample_index_node.data_type = 'FLOAT_VECTOR'
    pos_node, node_xx, node_yy = create_node(curve_nodegroup, "GeometryNodeInputPosition", node_xx, node_yy, 0, -10) # next on lower
    index_node, node_xx, node_yy = create_node(curve_nodegroup, "GeometryNodeInputIndex", node_xx, node_yy+50, -50, 100) # next on left
    join_node, node_xx, node_yy = create_node(curve_nodegroup, "GeometryNodeJoinGeometry", node_xx, node_yy, -50, 0) # for left handle points, next on lower
    join_node.name = "Left_handle Join Geometry"
    for i in range(len(left_handles)-1,-1,-1):
        point_node, node_xx, node_yy = create_node(curve_nodegroup, "GeometryNodePoints", node_xx, node_yy, 0, -10) # next on lower
        point_node.inputs['Position'].default_value = left_handles[i]
        point_node.inputs['Position'].hide = True
        point_node.inputs['Count'].hide = True
        point_node.inputs['Radius'].hide = True
        point_node.name = "Left_handle Points"
        curve_nodegroup.links.new(point_node.outputs['Points'], join_node.inputs['Geometry'])
    curve_nodegroup.links.new(join_node.outputs['Geometry'], sample_index_node.inputs['Geometry'])
    curve_nodegroup.links.new(pos_node.outputs['Position'], sample_index_node.inputs['Value'])
    curve_nodegroup.links.new(index_node.outputs['Index'], sample_index_node.inputs['Index'])
    curve_nodegroup.links.new(sample_index_node.outputs['Value'], set_lhandle_node.inputs['Position'])

    set_rhandle_node, node_x, node_y = create_node(curve_nodegroup, "GeometryNodeSetCurveHandlePositions", node_x, node_y, x_gap, 0) # next on right
    set_rhandle_node.mode = 'RIGHT'
    curve_nodegroup.links.new(set_lhandle_node.outputs['Curve'], set_rhandle_node.inputs['Curve'])

    # set right handle positions
    sample_index_node, node_xx, node_yy = create_node(curve_nodegroup, "GeometryNodeSampleIndex", set_lhandle_node.location.x, set_lhandle_node.location.y-set_lhandle_node.height-150, -50, -50) # next on left
    sample_index_node.data_type = 'FLOAT_VECTOR'
    pos_node, node_xx, node_yy = create_node(curve_nodegroup, "GeometryNodeInputPosition", node_xx, node_yy, 0, -10) # next on lower
    index_node, node_xx, node_yy = create_node(curve_nodegroup, "GeometryNodeInputIndex", node_xx, node_yy+50, -50, 100) # next on left
    join_node, node_xx, node_yy = create_node(curve_nodegroup, "GeometryNodeJoinGeometry", node_xx, pos_node.location.y, -50,0) # for right handle points, next on lower
    join_node.name = "Right_handle Join Geometry"
    for i in range(len(right_handles)-1,-1,-1):
        point_node, node_xx, node_yy = create_node(curve_nodegroup, "GeometryNodePoints", node_xx, node_yy, 0, -10) # next on lower
        point_node.inputs['Position'].default_value = right_handles[i]
        point_node.inputs['Position'].hide = True
        point_node.inputs['Count'].hide = True
        point_node.inputs['Radius'].hide = True
        point_node.name = "Right_handle Points"
        curve_nodegroup.links.new(point_node.outputs['Points'], join_node.inputs['Geometry'])
    curve_nodegroup.links.new(join_node.outputs['Geometry'], sample_index_node.inputs['Geometry'])
    curve_nodegroup.links.new(pos_node.outputs['Position'], sample_index_node.inputs['Value'])
    curve_nodegroup.links.new(index_node.outputs['Index'], sample_index_node.inputs['Index'])
    curve_nodegroup.links.new(sample_index_node.outputs['Value'], set_rhandle_node.inputs['Position'])

    subdivide_curve_node, node_x, node_y = create_node(curve_nodegroup, "GeometryNodeSubdivideCurve", node_x, node_y, x_gap, 0) # next on right
    curve_nodegroup.links.new(set_rhandle_node.outputs['Curve'], subdivide_curve_node.inputs['Curve'])

    # for stroke with linewith > 0.0
    set_pos_node1, node_x, node_y = create_node(curve_nodegroup, "GeometryNodeSetPosition", node_x, node_y, 0, -80) # next on lower
    set_pos_node1.name = 'Set Position Upper'
    curve_nodegroup.links.new(subdivide_curve_node.outputs['Curve'], set_pos_node1.inputs['Geometry'])
    scale_node, node_xx, node_yy = create_node(curve_nodegroup, "ShaderNodeVectorMath", subdivide_curve_node.location.x, subdivide_curve_node.location.y-subdivide_curve_node.height-10, -50, -30) # next on lower
    scale_node.operation = 'SCALE'
    scale_node.inputs['Scale'].default_value = line_width/(-2.0)
    scale_node.name = 'Scale1'
    normal_node, node_xx, node_yy = create_node(curve_nodegroup, "GeometryNodeInputNormal", node_xx, node_yy, -50, 0) # next on lower
    curve_nodegroup.links.new(normal_node.outputs['Normal'], scale_node.inputs['Vector'])
    curve_nodegroup.links.new(scale_node.outputs['Vector'], set_pos_node1.inputs['Offset'])

    set_pos_node2, node_x, node_y = create_node(curve_nodegroup, "GeometryNodeSetPosition", node_x, node_y, x_gap, 80) # next on right
    set_pos_node2.name = 'Set Position Lower'
    curve_nodegroup.links.new(subdivide_curve_node.outputs['Curve'], set_pos_node2.inputs['Geometry'])
    scale_node, node_xx, node_yy = create_node(curve_nodegroup, "ShaderNodeVectorMath", scale_node.location.x, scale_node.location.y-scale_node.height-30, -50, -10) # next on lower
    scale_node.operation = 'SCALE'
    scale_node.inputs['Scale'].default_value = line_width/2.0
    scale_node.name = 'Scale2'
    normal_node, node_xx, node_yy = create_node(curve_nodegroup, "GeometryNodeInputNormal", node_xx, node_yy, -50, 0) # next on lower
    curve_nodegroup.links.new(normal_node.outputs['Normal'], scale_node.inputs['Vector'])
    curve_nodegroup.links.new(scale_node.outputs['Vector'], set_pos_node2.inputs['Offset'])

    join_node, node_x, node_y = create_node(curve_nodegroup, "GeometryNodeJoinGeometry", node_x, node_y-40, x_gap, 0) # next on right
    switch_node, node_x, node_y = create_node(curve_nodegroup, "GeometryNodeSwitch", node_x, node_y+40, x_gap, 0) # next on right
    switch_node.label = "Stroke or fill switch"

    curve_nodegroup.links.new(set_pos_node1.outputs['Geometry'], join_node.inputs['Geometry'])
    curve_nodegroup.links.new(set_pos_node2.outputs['Geometry'], join_node.inputs['Geometry'])
    curve_nodegroup.links.new(join_node.outputs['Geometry'], switch_node.inputs['True'])
    curve_nodegroup.links.new(subdivide_curve_node.outputs['Curve'], switch_node.inputs['False'])
    if line_width > 0.0:
        switch_node.inputs['Switch'].default_value = True

    geo_to_ins_node, node_x, node_y  = create_node(curve_nodegroup, "GeometryNodeGeometryToInstance", node_x, node_y, x_gap, 0) # next on right
    pos_node, node_x, node_y  = create_node(curve_nodegroup, "GeometryNodeSetPosition", node_x, node_y, x_gap, 0) # next on right
    realizeInstance_node, node_x, node_y  = create_node(curve_nodegroup, "GeometryNodeRealizeInstances", node_x, node_y, x_gap, 0) # next on right
    out_node, _, _ = create_node(curve_nodegroup, "NodeGroupOutput", node_x, node_y)
    curve_nodegroup.links.new(switch_node.outputs['Output'], geo_to_ins_node.inputs['Geometry'])
    curve_nodegroup.links.new(geo_to_ins_node.outputs['Instances'], pos_node.inputs['Geometry'])
    curve_nodegroup.links.new(pos_node.outputs['Geometry'], realizeInstance_node.inputs['Geometry'])
    curve_nodegroup.links.new(realizeInstance_node.outputs['Geometry'], out_node.inputs['Curve'])

    return curve_nodegroup

def setup_gpencil_geonodes(gp_obj, cate_name="Drawer"):
    geometryMd = gp_obj.modifiers.new(name=f'{cate_name.lower()}GeoNodes', type='NODES')
    drawer_nodegroup = bpy.data.node_groups.new(type = 'GeometryNodeTree', name = f"{cate_name}NodeGroup")
    geometryMd.node_group = drawer_nodegroup

    drawer_nodegroup.interface.new_socket(name="Geometry", in_out='OUTPUT',socket_type='NodeSocketGeometry')
    drawer_nodegroup.interface.new_socket(name="Geometry", in_out='INPUT',socket_type='NodeSocketGeometry')

    drawer_in_node, node_x, node_y = create_node(drawer_nodegroup, "NodeGroupInput", -500, 0, 50, 0)
    drawer_mat_node, node_x, node_y = create_node(drawer_nodegroup, "GeometryNodeGroup", node_x, node_y, 50, 0)
    drawer_mat_node.node_tree = bpy.data.node_groups['GP Material'].copy()
    drawer_mat_node.name = 'GP Material'
    drawer_mat_node.label = 'GP Material'
    drawer_layer_node, node_x, node_y = create_node(drawer_nodegroup, "GeometryNodeGroup", node_x, node_y, 50, 0)
    drawer_layer_node.node_tree = bpy.data.node_groups['Layer Select'].copy()
    drawer_layer_node.node_tree.nodes['GP Material'].node_tree = bpy.data.node_groups['GP Material'].copy()
    drawer_layer_node.name = 'Layer'
    drawer_layer_node.label = 'Layer'
    drawer_layer_node.inputs['Layer Name'].default_value = 'Layer'
    drawer_join_node, node_x, node_y = create_node(drawer_nodegroup, "GeometryNodeJoinGeometry", 300, 0, 50, 0)
    drawer_curve_node, node_x, node_y = create_node(drawer_nodegroup, "GeometryNodeGroup", node_x, node_y, 50, 0)
    drawer_curve_node.node_tree = bpy.data.node_groups['Finalize Curves'].copy()
    drawer_out_node, _, _ = create_node(drawer_nodegroup, "NodeGroupOutput", node_x, node_y, 50, 0)
    drawer_nodegroup.links.new(drawer_in_node.outputs['Geometry'], drawer_mat_node.inputs['Geometry'])
    drawer_nodegroup.links.new(drawer_mat_node.outputs['Geometry'], drawer_layer_node.inputs['Geometry'])
    drawer_nodegroup.links.new(drawer_layer_node.outputs['Geometry'], drawer_join_node.inputs['Geometry'])
    drawer_nodegroup.links.new(drawer_join_node.outputs['Geometry'], drawer_curve_node.inputs['Geometry'])
    drawer_nodegroup.links.new(drawer_curve_node.outputs['Geometry'], drawer_out_node.inputs['Geometry'])
    return drawer_nodegroup

def setup_formula_geonodes(self, context, formula_obj, texts, strokes, fills, gp_materials, mesh_material, color_strength=10.0, curve_radius=0.005):

    t = time.perf_counter()
    formula_nodegroup = setup_gpencil_geonodes(formula_obj, cate_name="Formula")
    layout_factor_socket = formula_nodegroup.interface.new_socket(name="Scale Factor", in_out='INPUT',socket_type='NodeSocketFloat')
    layout_factor_socket.default_value = 1.0
    layout_factor_socket.description = "Layout scale adjustment"
    formula_in_node = formula_nodegroup.nodes['Group Input']
    formula_join_node = formula_nodegroup.nodes['Join Geometry']
    geometryMd = formula_obj.modifiers['formulaGeoNodes']

    use_node_groups = ['char_settings', 'apply_settings', 'char_instance_anim', 'char_curve_anim', 'stroke_instance_anim', 'stroke_curve_anim', 'fill_instance_anim', 'fill_curve_anim', 'char_mesh_anim', 'stroke_mesh_anim', 'fill_mesh_anim', 'char_nodegroup', 'quad_nodegroup', 'curve_nodegroup', 'render_type']  # Name of the node group to import
    for group_name in use_node_groups:
        groups = bpy.data.node_groups.get(group_name)
        if groups is None:
            import_char_nodegroups([group_name])
    char_settings = bpy.data.node_groups.get("char_settings")
    apply_settings = bpy.data.node_groups.get("apply_settings")
    char_instance_anim = bpy.data.node_groups.get("char_instance_anim")
    char_curve_anim = bpy.data.node_groups.get("char_curve_anim")
    char_mesh_anim = bpy.data.node_groups.get("char_mesh_anim")
    stroke_instance_anim = bpy.data.node_groups.get("stroke_instance_anim")
    stroke_curve_anim = bpy.data.node_groups.get("stroke_curve_anim")
    stroke_mesh_anim = bpy.data.node_groups.get("stroke_mesh_anim")
    fill_instance_anim = bpy.data.node_groups.get("fill_instance_anim")
    fill_curve_anim = bpy.data.node_groups.get("fill_curve_anim")
    fill_mesh_anim = bpy.data.node_groups.get("fill_mesh_anim")
    char_nodegroup = bpy.data.node_groups.get("char_nodegroup")
    quad_nodegroup = bpy.data.node_groups.get("quad_nodegroup")
    curve_nodegroup = bpy.data.node_groups.get("curve_nodegroup")
    render_type = bpy.data.node_groups.get("render_type")
    check_groups = {"char_settings": char_settings, "apply_settings": apply_settings, "char_instance_anim": char_instance_anim, "char_curve_anim": char_curve_anim, "char_mesh_anim": char_mesh_anim, "stroke_instance_anim": stroke_instance_anim, "stroke_curve_anim": stroke_curve_anim, "stroke_mesh_anim": stroke_mesh_anim, "fill_instance_anim": fill_instance_anim, "fill_curve_anim": fill_curve_anim, "fill_mesh_anim": fill_mesh_anim, "char_nodegroup": char_nodegroup, "quad_nodegroup": quad_nodegroup, "curve_nodegroup": curve_nodegroup, "render_type": render_type}
    for group_name, group in check_groups.items():
         if group is None:
            self.report({"ERROR"},f"Node group {group_name} not found!")
            return None
         else:
            group.use_fake_user = True

    global_suffix = formula_obj["math_anim_obj"][formula_obj["math_anim_obj"].find('Global'):]
    use_render_type = bpy.data.node_groups.get(f"render_type.{global_suffix}")
    if use_render_type is None:
        use_render_type = render_type.copy()
        use_render_type.use_fake_user = True
        use_render_type.name = f"render_type.{global_suffix}"
        use_render_type.nodes['Set Material'].inputs['Material'].default_value = mesh_material
    use_char_setting = bpy.data.node_groups.get(f"char_settings.{global_suffix}")
    if use_char_setting is None:
        use_char_setting = char_settings.copy()
        use_char_setting.use_fake_user = True
        use_char_setting.name = f"char_settings.{global_suffix}"
    base_color = (0.0, 0.0, 0.0, 1.0)
    if len(gp_materials['line']) > 0:
        base_color = list(gp_materials['line'].keys())[0]
    elif len(gp_materials['fill']) > 0:
        base_color = list(gp_materials['fill'].keys())[0]
    use_char_setting.nodes['Color'].inputs['Value'].default_value = base_color
    use_char_setting.nodes['Color Strength'].inputs['Value'].default_value = color_strength
    use_char_setting.nodes['Curve Radius'].inputs['Value'].default_value = curve_radius

    use_char_instance_anim = bpy.data.node_groups.get(f"char_instance_anim.{global_suffix}")
    if use_char_instance_anim is None:
        use_char_instance_anim = char_instance_anim.copy()
        use_char_instance_anim.use_fake_user = True
        use_char_instance_anim.name = f"char_instance_anim.{global_suffix}"
    use_char_curve_anim = bpy.data.node_groups.get(f"char_curve_anim.{global_suffix}")
    if use_char_curve_anim is None:
        use_char_curve_anim = char_curve_anim.copy()
        use_char_curve_anim.use_fake_user = True
        use_char_curve_anim.name = f"char_curve_anim.{global_suffix}"
    use_char_mesh_anim = bpy.data.node_groups.get(f"char_mesh_anim.{global_suffix}")
    if use_char_mesh_anim is None:
        use_char_mesh_anim = char_mesh_anim.copy()
        use_char_mesh_anim.use_fake_user = True
        use_char_mesh_anim.name = f"char_mesh_anim.{global_suffix}"

    use_stroke_instance_anim = bpy.data.node_groups.get(f"stroke_instance_anim.{global_suffix}")
    if use_stroke_instance_anim is None:
        use_stroke_instance_anim = stroke_instance_anim.copy()
        use_stroke_instance_anim.use_fake_user = True
        use_stroke_instance_anim.name = f"stroke_instance_anim.{global_suffix}"
    use_stroke_curve_anim = bpy.data.node_groups.get(f"stroke_curve_anim.{global_suffix}")
    if use_stroke_curve_anim is None:
        use_stroke_curve_anim= stroke_curve_anim.copy()
        use_stroke_curve_anim.use_fake_user = True
        use_stroke_curve_anim.name = f"stroke_curve_anim.{global_suffix}"
    use_stroke_mesh_anim = bpy.data.node_groups.get(f"stroke_mesh_anim.{global_suffix}")
    if use_stroke_mesh_anim is None:
        use_stroke_mesh_anim = stroke_mesh_anim.copy()
        use_stroke_mesh_anim.use_fake_user = True
        use_stroke_mesh_anim.name = f"stroke_mesh_anim.{global_suffix}"

    use_fill_instance_anim = bpy.data.node_groups.get(f"fill_instance_anim.{global_suffix}")
    if use_fill_instance_anim is None:
        use_fill_instance_anim = fill_instance_anim.copy()
        use_fill_instance_anim.use_fake_user = True
        use_fill_instance_anim.name = f"fill_instance_anim.{global_suffix}"
    use_fill_curve_anim = bpy.data.node_groups.get(f"fill_curve_anim.{global_suffix}")
    if use_fill_curve_anim is None:
        use_fill_curve_anim= fill_curve_anim.copy()
        use_fill_curve_anim.use_fake_user = True
        use_fill_curve_anim.name = f"fill_curve_anim.{global_suffix}"
    use_fill_mesh_anim = bpy.data.node_groups.get(f"fill_mesh_anim.{global_suffix}")
    if use_fill_mesh_anim is None:
        use_fill_mesh_anim = fill_mesh_anim.copy()
        use_fill_mesh_anim.use_fake_user = True
        use_fill_mesh_anim.name = f"fill_mesh_anim.{global_suffix}"

    #if not char_nodegroup:
    #    char_nodegroup = create_char_nodegroup("char_nodegroup")

    # each page as one nodegroup
    page_node_x = 0
    page_node_y = -260
    vb.formula_node_trees[formula_obj["math_anim_obj"]] = []
    vb.formula_anim_nodes[formula_obj["math_anim_obj"]] = {}
    vb.formula_anim_nodes[formula_obj["math_anim_obj"]]['text_anim'] = {}
    vb.formula_anim_nodes[formula_obj["math_anim_obj"]]['stroke_anim'] = {}
    vb.formula_anim_nodes[formula_obj["math_anim_obj"]]['fill_anim'] = {}
    morph_obj_holder = context.scene.math_anim_morphSettings
    morph_selected_idx = context.scene.math_anim_morph_selected_idx
    if len(morph_selected_idx) == 0:
        morph_selected_idx.add()
        morph_selected_idx.add()
    # delete old if having same name
    idx = []
    for i in range(len(morph_obj_holder)):
        if morph_obj_holder[i].name == formula_obj["math_anim_obj"]:
            idx.append(i)
    for i in idx:
        morph_obj_holder.remove(i)
    # add current object's
    item = morph_obj_holder.add()
    item.name = formula_obj["math_anim_obj"]
    morph_page_holder = item.page_holder

    for page_num in range(len(texts)):
        item = morph_page_holder.add()
        item = item.morph_collection
        collection_len = 2
        morph_setting = []
        if len(morph_obj_holder) > 1:
            collection_len = len(morph_obj_holder[0].page_holder[0].morph_collection)
        for cc in range(collection_len):
            settings = item.add()
            morph_setting.append(settings.morph_setting)

        text_nodes = {}
        stroke_nodes = {}
        fill_nodes = {}

        page_node, page_node_x, page_node_y = create_node(formula_nodegroup, "GeometryNodeGroup", page_node_x, page_node_y, 0, -10) # next node on bottom
        page_nodegroup = bpy.data.node_groups.new(type = 'GeometryNodeTree', name = f"Page{page_num}NodeGroup")
        page_nodegroup.interface.new_socket(name="Geometry", in_out='INPUT',socket_type='NodeSocketGeometry')
        # normal chars
        page_text = texts[page_num]

        page_nodegroup.interface.new_socket(name="Geometry", in_out='OUTPUT',socket_type='NodeSocketGeometry')
        layout_factor_socket = page_nodegroup.interface.new_socket(name="Scale Factor", in_out='INPUT',socket_type='NodeSocketFloat')
        layout_factor_socket.default_value = 1.0
        layout_factor_socket.description = "Layout scale adjustment"

        char_join_node, node_x, _ = create_node(page_nodegroup, "GeometryNodeJoinGeometry", 1000, 0, 50, 0) # next on right
        char_join_node.name = 'char_join_node'
        char_join_node.label = 'Char Join Node'
        text_nodes['text_join'] = char_join_node
        stroke_join_node, node_x, _ = create_node(page_nodegroup, "GeometryNodeJoinGeometry", 2500, 100, 50, 0) # next on right
        stroke_join_node.name = 'stroke_join_node'
        stroke_join_node.label = 'Stroke Join Node'
        stroke_nodes['stroke_join'] = stroke_join_node
        fill_join_node, node_x, _ = create_node(page_nodegroup, "GeometryNodeJoinGeometry", 4000, -100, 50, 0) # next on right
        fill_join_node.name = 'fill_join_node'
        fill_join_node.label = 'Fill Join Node'
        fill_nodes['fill_join'] = fill_join_node
        join_node, node_x, _ = create_node(page_nodegroup, "GeometryNodeJoinGeometry", node_x, 0, 50, 0) # next on right
        in_node, node_x, _ = create_node(page_nodegroup, "NodeGroupInput", node_x, -200, 50, 0) # next on right
        trans_node, node_x, _ = create_node(page_nodegroup, "GeometryNodeTransform", node_x, 0, 50, 0) # next on right
        out_node, _, _ = create_node(page_nodegroup, "NodeGroupOutput", node_x, 0)

        node_x = -500
        node_y = -len(page_text)*100/2
        x_gap = 50
        y_gap = 10

        found_bracket_len = 0
        char_len = len(page_text)
        groupIn_node, _, _ = create_node(page_nodegroup, "NodeGroupInput", -900, 0, 0, 0) # next node right
        groupIn_node.name = "Group Input Chars"

        # 3. page setup settings
        print("3 page setup:", time.perf_counter()-t); t=time.perf_counter()

        for c_idx in range(char_len-1,-1,-1):
            char = page_text[c_idx]
            if char['char'] == '{' and c_idx<char_len-1:
                n_char = page_text[c_idx+1]
                if n_char['char'] == '⎩' or n_char['char'] == '⎨':
                    continue
            elif char['char'] == '}' and c_idx<char_len-1:
                n_char = page_text[c_idx+1]
                if n_char['char'] == '⎭' or n_char['char'] == '⎬':
                    continue
            elif (char['char'] is None) or (len(char['char']) != 1):
                continue
            # check components "[", "]", "{", "}", "(", ")" and replace them with big one
            bracket_parts = ["[", "]", "{", "}", "(", ")"]
            found_bracket_part = False
            found_bracket_end = False
            for part in bracket_parts:
                if char['char'] == part and char_len>1:
                    found_bracket_part = True
                    if c_idx > 0 and c_idx < char_len - 1:
                        p_char = page_text[c_idx+1]
                        n_char = page_text[c_idx-1]
                        if p_char['char'] == part and char["location"][0] == p_char["location"][0]:
                            char['bbox_h'] = char['bbox_h'] + p_char['bbox_h']
                        if n_char['char'] == part and char["location"][0] == n_char["location"][0]:
                            continue
                        else:
                            found_bracket_end = True
                    elif c_idx == char_len-1:
                        n_char = page_text[c_idx-1]
                        if n_char['char'] == part and char["location"][0] == n_char["location"][0]:
                            continue
                        found_bracket_end = True
                    else:
                        p_char = page_text[c_idx+1]
                        if p_char['char'] == part and char["location"][0] == p_char["location"][0]:
                            char['bbox_h'] = char['bbox_h'] + p_char['bbox_h']
                        found_bracket_end = True
                    break
            found_bracket_len += found_bracket_part
            if found_bracket_part and not found_bracket_end:
                continue

            # char node with other nodes as group
            text_node, node_xx, node_y = create_node(page_nodegroup, "GeometryNodeGroup", node_x, node_y, x_gap, y_gap) # next node top
            apply_node, _, _ = create_node(page_nodegroup, "GeometryNodeGroup", node_x+190, node_y-110, 0, 0) # next node top
            apply_node.node_tree = apply_settings.copy()
            apply_node.node_tree.nodes['Render Type'].node_tree = use_render_type
            apply_node.node_tree.nodes['Mesh Anim'].node_tree = use_char_mesh_anim
            apply_node.node_tree.nodes['Mesh Anim'].inputs["Current Index"].default_value = c_idx
            apply_node.node_tree.nodes['Mesh Anim'].inputs["Total Index"].default_value = char_len
            char_nodegroup_temp = char_nodegroup.copy()
            char_nodegroup_temp.nodes['Char Settings'].node_tree = use_char_setting
            char_nodegroup_temp.nodes['Instance Anim'].node_tree = use_char_instance_anim
            char_nodegroup_temp.nodes['Curve Anim'].node_tree = use_char_curve_anim
            char_nodegroup_temp.nodes['Curve Anim'].inputs['Index'].default_value = c_idx
            char_nodegroup_temp.nodes['Instance Anim'].inputs['Index'].default_value = c_idx
            unicode_name = get_unicode_name(char['char'])
            if unicode_name:
                unicode_name = unicode_name.lower().replace(' ', '_')
            char_nodegroup_temp.name = f"char.{char['char']}.U{char['unicode']}"
            char_node  = char_nodegroup_temp.nodes["String to Curves"]
            char_setting_node   = char_nodegroup_temp.nodes["Char Settings"]
            char_setting_node.inputs['Curve Radius'].default_value = curve_radius
            char_setting_node.inputs['Color Strength'].default_value = color_strength
            font_name = f"{char['font']}.otf"
            font_path = ''
            if font_name not in vb.font_path_dict:
                font_name = f"{char['font']}.ttf"
                if font_name not in vb.font_path_dict:
                    self.report({"WARNING"}, f"Font {os.path.splitext(font_name)[0]} not found, will use system default font, make sure the font available to correctly display the contents.")
                else:
                    font_path = vb.font_path_dict[f"{font_name}"]['path']
                    font_path = font_path.replace('\\','/')
                    char_node.inputs["Font"].default_value = bpy.data.fonts.load(font_path, check_existing=True)
            else:
                font_path = vb.font_path_dict[f"{font_name}"]['path']
                font_path = font_path.replace('\\','/')
                char_node.inputs["Font"].default_value = bpy.data.fonts.load(font_path, check_existing=True)
            char_node.inputs['String'].default_value = char['char']
            actual_fontsize, actual_bbox_w, middle_x, middle_y = font_scale(char['char'], font_path, char['bbox_h'])
            if actual_fontsize == 0.0:
                continue
            char_node.inputs['Size'].default_value = actual_fontsize
            x, y = char['location']
            if found_bracket_len > 1 and found_bracket_end:
                y = y + char['bbox_h']*0.8
            char_setting_node.inputs['Offset'].default_value = (x, y, 0.0)
            if (char['bbox_h'] > char['fontsize']):
                if (char['char'] not in vb.openBracketChars):
                    shift_x = middle_x*(char['fontsize']/char['bbox_h'])*(1.0-char['bbox_h']/char['fontsize'])
                    shift_y = middle_y*(char['fontsize']/char['bbox_h'])*(1.0-char['bbox_h']/char['fontsize'])
                    char_setting_node.inputs['Offset'].default_value = (x+shift_x/4.0, y+shift_y/1.0, 0.0)
                if char['char'] in vb.specialChars:
                    shift_y = char['fontsize']*0.70 + (char['bbox_h'] - char['fontsize'])/2.0
                    char_setting_node.inputs['Offset'].default_value = (x, y + shift_y , 0.0)


            if actual_bbox_w > char['bbox_w']*0.9 or (found_bracket_len>1 and found_bracket_end):
                char_setting_node.inputs['Scale'].default_value[0] = char['bbox_w']*0.90/actual_bbox_w
                if (found_bracket_len>1 and found_bracket_end):
                    char_setting_node.inputs['Scale'].default_value[0] = char['bbox_w']*0.55/actual_bbox_w
                    char_setting_node.inputs['Offset'].default_value[1] -= char['bbox_h']/2.65
                    if char['char'] == '{' or char['char'] == '(':
                        char_setting_node.inputs['Offset'].default_value[0] += 0.004

            text_node.node_tree = char_nodegroup_temp
            if gp_materials['line'][char['color']]['index'] != 0:
                char_setting_node.inputs['Individual Control'].default_value = True
                char_setting_node.inputs['Color'].default_value = char['color']
            text_node.name = f"char.{char['char']}.U{char['unicode']}"
            if unicode_name:
                text_node.label = f"char.{unicode_name}.U{char['unicode']}"
            else:
                text_node.label = f"char.unknown.U{char['unicode']}"
            page_nodegroup.links.new(groupIn_node.outputs['Geometry'], text_node.inputs['Geometry'])
            page_nodegroup.links.new(text_node.outputs['Curve'], apply_node.inputs['Geometry'])
            page_nodegroup.links.new(apply_node.outputs['Geometry'], char_join_node.inputs['Geometry'])
            if found_bracket_end:
                found_bracket_len = 0
            suffix = text_node.name.split('.')[-1]
            key_name = ''
            if len(suffix) > 3:
                key_name = char['char']
            else:
                key_name = f"{char['char']}.{suffix}"
            text_nodes[key_name] = text_node
            for idx in range(len(morph_setting)):
                item = morph_setting[idx].add()
                item.inputs = key_name
                item.type = 'char'
                item.item_idx = len(morph_setting[idx]) - 1
                item.page_idx  = page_num
                item.collection_idx  = idx
                item.obj_id  = formula_obj["math_anim_obj"]

        # char node settings
        print("char loop time:", time.perf_counter()-t); t=time.perf_counter()

        # special chars and vector shapes
        page_strokes = strokes[page_num]
        node_x = 1800
        node_y = -len(page_strokes)*100/2
        x_gap = 50
        y_gap = 10
        if len(page_strokes) > 0:
            groupIn_node, _, _ = create_node(page_nodegroup, "NodeGroupInput", 1400, 100, 0, 0) # next node right
            groupIn_node.name = "Group Input Strokes"
        for s_idx, stroke in enumerate(page_strokes[::-1]):
            if stroke['type'] == 'line': # simple vertical or horizontal lines
                quad_node, node_xx, node_y = create_node(page_nodegroup, "GeometryNodeGroup", node_x, node_y, x_gap, y_gap) # next on top
                apply_node, _, _ = create_node(page_nodegroup, "GeometryNodeGroup", node_x+190, node_y-110, 0, 0) # next node top
                apply_node.node_tree = apply_settings.copy()
                apply_node.node_tree.nodes['Render Type'].node_tree = use_render_type
                apply_node.node_tree.nodes['Mesh Anim'].node_tree = use_stroke_mesh_anim
                apply_node.node_tree.nodes['Mesh Anim'].inputs["Current Index"].default_value = len(page_strokes)-1-s_idx
                apply_node.node_tree.nodes['Mesh Anim'].inputs["Total Index"].default_value = len(page_strokes)
                quad_node.name = f"strokes.line"
                quad_node.label = f"strokes.line"
                quad_nodegroup_temp = quad_nodegroup.copy()
                quad_nodegroup_temp.nodes['Char Settings'].node_tree = use_char_setting
                quad_nodegroup_temp.nodes['Instance Anim'].node_tree = use_stroke_instance_anim
                quad_nodegroup_temp.nodes['Curve Anim'].node_tree = use_stroke_curve_anim
                quad_nodegroup_temp.nodes['Curve Anim'].inputs['Index'].default_value = len(page_strokes)-1-s_idx
                quad_nodegroup_temp.nodes['Instance Anim'].inputs['Index'].default_value = len(page_strokes)-1-s_idx
                quad_nodegroup_temp.name = quad_node.name
                set_quad_node = quad_nodegroup_temp.nodes['Quadrilateral']
                char_setting_node = quad_nodegroup_temp.nodes['Char Settings']
                char_setting_node.inputs['Curve Radius'].default_value = curve_radius
                char_setting_node.inputs['Color Strength'].default_value = color_strength
                # get average and shift to center zero
                sum_x = sum(point[0] for point in stroke['control_points'])
                sum_y = sum(point[1] for point in stroke['control_points'])
                num_points = len(stroke['control_points'])
                avg_x = sum_x/num_points
                avg_y = sum_y/num_points
                points = [(x-avg_x, y-avg_y, z) for x, y, z in stroke['control_points']]
                char_setting_node.inputs['Offset'].default_value = (avg_x, avg_y, 0.0)
                for j in range(7,11):
                    set_quad_node.inputs[j].default_value = points[j-7]
                quad_node.use_custom_color = True
                quad_node.color = (0.35, 0.35, 0.6)
                quad_node.node_tree = quad_nodegroup_temp
                if gp_materials['line'][stroke['color']]['index'] != 0:
                    char_setting_node.inputs['Individual Control'].default_value = True
                    char_setting_node.inputs['Color'].default_value = stroke['color']
                page_nodegroup.links.new(groupIn_node.outputs['Geometry'], quad_node.inputs["Geometry"])
                page_nodegroup.links.new(quad_node.outputs['Curve'], apply_node.inputs["Geometry"])
                page_nodegroup.links.new(apply_node.outputs['Geometry'], stroke_join_node.inputs["Geometry"])
                stroke_nodes[f"{quad_node.name}"] = quad_node
                for idx in range(len(morph_setting)):
                    item = morph_setting[idx].add()
                    item.inputs = quad_node.name
                    item.type = 'stroke'
                    item.item_idx = len(morph_setting[idx]) - 1
                    item.page_idx  = page_num
                    item.collection_idx  = idx
                    item.obj_id  = formula_obj["math_anim_obj"]

            elif stroke['type'] == 're':
                quad_node, node_xx, node_y = create_node(page_nodegroup, "GeometryNodeGroup", node_x, node_y, x_gap, y_gap) # next on top
                apply_node, _, _ = create_node(page_nodegroup, "GeometryNodeGroup", node_x+190, node_y-110, 0, 0) # next node top
                apply_node.node_tree = apply_settings.copy()
                apply_node.node_tree.nodes['Render Type'].node_tree = use_render_type
                apply_node.node_tree.nodes['Mesh Anim'].node_tree = use_stroke_mesh_anim
                apply_node.node_tree.nodes['Mesh Anim'].inputs["Current Index"].default_value = len(page_strokes)-1-s_idx
                apply_node.node_tree.nodes['Mesh Anim'].inputs["Total Index"].default_value = len(page_strokes)
                quad_node.name = f"strokes.rectange"
                quad_node.label = f"strokes.rectange"
                quad_nodegroup_temp = quad_nodegroup.copy()
                quad_nodegroup_temp.nodes['Char Settings'].node_tree = use_char_setting
                quad_nodegroup_temp.nodes['Instance Anim'].node_tree = use_stroke_instance_anim
                quad_nodegroup_temp.nodes['Curve Anim'].node_tree = use_stroke_curve_anim
                quad_nodegroup_temp.nodes['Curve Anim'].inputs['Index'].default_value = len(page_strokes)-1-s_idx
                quad_nodegroup_temp.nodes['Instance Anim'].inputs['Index'].default_value = len(page_strokes)-1-s_idx
                quad_nodegroup_temp.name = quad_node.name
                set_quad_node = quad_nodegroup_temp.nodes['Quadrilateral']
                char_setting_node = quad_nodegroup_temp.nodes['Char Settings']
                char_setting_node.inputs['Curve Radius'].default_value = curve_radius
                char_setting_node.inputs['Color Strength'].default_value = color_strength
                # get average and shift to center zero
                sum_x = sum(point[0] for point in stroke['control_points'])
                sum_y = sum(point[1] for point in stroke['control_points'])
                num_points = len(stroke['control_points'])
                avg_x = sum_x/num_points
                avg_y = sum_y/num_points
                points = [(x-avg_x, y-avg_y, z) for x, y, z in stroke['control_points']]
                char_setting_node.inputs['Offset'].default_value = (avg_x, avg_y, 0.0)
                for j in range(7,11):
                    set_quad_node.inputs[j].default_value[0:2] = points[j-7]
                quad_node.use_custom_color = True
                quad_node.color = (0.35, 0.35, 0.6)
                quad_node.node_tree = quad_nodegroup_temp
                if gp_materials['line'][stroke['color']]['index'] != 0:
                    char_setting_node.inputs['Individual Control'].default_value = True
                    char_setting_node.inputs['Color'].default_value = stroke['color']
                page_nodegroup.links.new(groupIn_node.outputs['Geometry'], quad_node.inputs["Geometry"])
                page_nodegroup.links.new(quad_node.outputs['Curve'], apply_node.inputs["Geometry"])
                page_nodegroup.links.new(apply_node.outputs['Geometry'], stroke_join_node.inputs["Geometry"])
                stroke_nodes[f"{quad_node.name}"] = quad_node
                for idx in range(len(morph_setting)):
                    item = morph_setting[idx].add()
                    item.inputs = quad_node.name
                    item.type = 'stroke'
                    item.item_idx = len(morph_setting[idx]) - 1
                    item.page_idx  = page_num
                    item.collection_idx  = idx
                    item.obj_id  = formula_obj["math_anim_obj"]

            elif stroke['type'] == 'qu':
                quad_node, node_xx, node_y = create_node(page_nodegroup, "GeometryNodeGroup", node_x, node_y, x_gap, y_gap) # next on top
                apply_node, _, _ = create_node(page_nodegroup, "GeometryNodeGroup", node_x+190, node_y-110, 0, 0) # next node top
                apply_node.node_tree = apply_settings.copy()
                apply_node.node_tree.nodes['Render Type'].node_tree = use_render_type
                apply_node.node_tree.nodes['Mesh Anim'].node_tree = use_stroke_mesh_anim
                apply_node.node_tree.nodes['Mesh Anim'].inputs["Current Index"].default_value = len(page_strokes)-1-s_idx
                apply_node.node_tree.nodes['Mesh Anim'].inputs["Total Index"].default_value = len(page_strokes)
                quad_node.name = f"strokes.quad"
                quad_node.label = f"strokes.quad"
                quad_nodegroup_temp = quad_nodegroup.copy()
                quad_nodegroup_temp.nodes['Char Settings'].node_tree = use_char_setting
                quad_nodegroup_temp.nodes['Instance Anim'].node_tree = use_stroke_instance_anim
                quad_nodegroup_temp.nodes['Curve Anim'].node_tree = use_stroke_curve_anim
                quad_nodegroup_temp.nodes['Curve Anim'].inputs['Index'].default_value = len(page_strokes)-1-s_idx
                quad_nodegroup_temp.nodes['Instance Anim'].inputs['Index'].default_value = len(page_strokes)-1-s_idx
                quad_nodegroup_temp.name = quad_node.name
                set_quad_node = quad_nodegroup_temp.nodes['Quadrilateral']
                char_setting_node = quad_nodegroup_temp.nodes['Char Settings']
                char_setting_node.inputs['Curve Radius'].default_value = curve_radius
                char_setting_node.inputs['Color Strength'].default_value = color_strength
                # get average and shift to center zero
                sum_x = sum(point[0] for point in stroke['control_points'])
                sum_y = sum(point[1] for point in stroke['control_points'])
                num_points = len(stroke['control_points'])
                avg_x = sum_x/num_points
                avg_y = sum_y/num_points
                points = [(x-avg_x, y-avg_y, z) for x, y, z in stroke['control_points']]
                char_setting_node.inputs['Offset'].default_value = (avg_x, avg_y, 0.0)
                for j in range(7,11):
                    set_quad_node.inputs[j].default_value[0:2] = points[j-7]
                quad_node.use_custom_color = True
                quad_node.color = (0.35, 0.35, 0.6)
                quad_node.node_tree = quad_nodegroup_temp
                if gp_materials['line'][stroke['color']]['index'] != 0:
                    char_setting_node.inputs['Individual Control'].default_value = True
                    char_setting_node.inputs['Color'].default_value = stroke['color']
                page_nodegroup.links.new(groupIn_node.outputs['Geometry'], quad_node.inputs["Geometry"])
                page_nodegroup.links.new(quad_node.outputs['Curve'], apply_node.inputs["Geometry"])
                page_nodegroup.links.new(apply_node.outputs['Geometry'], stroke_join_node.inputs["Geometry"])
                stroke_nodes[f"{quad_node.name}"] = quad_node
                for idx in range(len(morph_setting)):
                    item = morph_setting[idx].add()
                    item.inputs = quad_node.name
                    item.type = 'stroke'
                    item.item_idx = len(morph_setting[idx]) - 1
                    item.page_idx  = page_num
                    item.collection_idx  = idx
                    item.obj_id  = formula_obj["math_anim_obj"]

            elif stroke['type'] == 'curve':
                curve_nodegroup_temp = curve_nodegroup.copy()
                curve_nodegroup_temp.nodes['Char Settings'].node_tree = use_char_setting
                curve_nodegroup_temp.nodes['Instance Anim'].node_tree = use_stroke_instance_anim
                curve_nodegroup_temp.nodes['Curve Anim'].node_tree = use_stroke_curve_anim
                curve_nodegroup_temp.nodes['Curve Anim'].inputs['Index'].default_value = len(page_strokes)-1-s_idx
                curve_nodegroup_temp.nodes['Instance Anim'].inputs['Index'].default_value = len(page_strokes)-1-s_idx
                scale_node = curve_nodegroup_temp.nodes["Scale1"]
                scale_node.inputs['Scale'].default_value = stroke['line_width']/(-2.0)
                scale_node = curve_nodegroup_temp.nodes["Scale2"]
                scale_node.inputs['Scale'].default_value = stroke['line_width']/2.0
                switch_node = curve_nodegroup_temp.nodes['Switch']
                switch_node.inputs['Switch'].default_value = True
                char_setting_node = curve_nodegroup_temp.nodes['Char Settings']
                char_setting_node.inputs['Curve Radius'].default_value = curve_radius
                char_setting_node.inputs['Color Strength'].default_value = color_strength

                # control points
                control_points = stroke['control_points']
                # get average and shift to zero
                sum_x = sum(point[0] for point in control_points)
                sum_y = sum(point[1] for point in control_points)
                num_points = len(control_points)
                avg_x = sum_x/num_points
                avg_y = sum_y/num_points
                control_points = [(x-avg_x, y-avg_y, z) for x, y, z in control_points]
                char_setting_node.inputs['Offset'].default_value = (avg_x, avg_y, 0.0)
                control_points_join_node = curve_nodegroup_temp.nodes['Control_points Join Geometry']
                for j in range(len(control_points)-1,-1,-1):
                    if j == len(control_points) - 1:
                        point_node = curve_nodegroup_temp.nodes['Control Points']
                        node_lx = point_node.location.x
                        node_ly = point_node.location.y + point_node.height + 10
                    else:
                        point_node, node_lx, node_ly = create_node(curve_nodegroup_temp, "GeometryNodePoints", node_lx, node_ly, 0, 10) # next on top
                        point_node.name = "Control Points"
                    point_node.inputs['Position'].default_value = control_points[j]
                    point_node.inputs['Position'].hide = True
                    point_node.inputs['Count'].hide = True
                    point_node.inputs['Radius'].hide = True
                    curve_nodegroup_temp.links.new(point_node.outputs['Points'], control_points_join_node.inputs['Geometry'])
                # left handle points
                left_handles = stroke['left_handles']
                left_handles = [(x-avg_x, y-avg_y, z) for x, y, z in left_handles]
                left_handle_join_node = curve_nodegroup_temp.nodes['Left_handle Join Geometry']
                for j in range(len(left_handles)-1,-1,-1):
                    if j == len(left_handles) - 1:
                        point_node = curve_nodegroup_temp.nodes['Left_handle Points']
                        node_lx = point_node.location.x
                        node_ly = point_node.location.y - point_node.height - 10
                    else:
                        point_node, node_lx, node_ly = create_node(curve_nodegroup_temp, "GeometryNodePoints", node_lx, node_ly, 0, -10) # next on lower
                        point_node.name = "Left_handle Points"
                    point_node.inputs['Position'].default_value = left_handles[j]
                    point_node.inputs['Position'].hide = True
                    point_node.inputs['Count'].hide = True
                    point_node.inputs['Radius'].hide = True
                    curve_nodegroup_temp.links.new(point_node.outputs['Points'], left_handle_join_node.inputs['Geometry'])
                # right handle points
                right_handles = stroke['right_handles']
                right_handles = [(x-avg_x, y-avg_y, z) for x, y, z in right_handles]
                right_handle_join_node = curve_nodegroup_temp.nodes['Right_handle Join Geometry']
                for j in range(len(right_handles)-1,-1,-1):
                    if j == len(right_handles) - 1:
                        point_node = curve_nodegroup_temp.nodes['Right_handle Points']
                        node_lx = point_node.location.x
                        node_ly = point_node.location.y - point_node.height - 10
                    else:
                        point_node, node_lx, node_ly = create_node(curve_nodegroup_temp, "GeometryNodePoints", node_lx, node_ly, 0, -10) # next on lower
                        point_node.name = "Right_handle Points"
                    point_node.inputs['Position'].default_value = right_handles[j]
                    point_node.inputs['Position'].hide = True
                    point_node.inputs['Count'].hide = True
                    point_node.inputs['Radius'].hide = True
                    curve_nodegroup_temp.links.new(point_node.outputs['Points'], right_handle_join_node.inputs['Geometry'])

                curve_node, node_xx, node_y = create_node(page_nodegroup, "GeometryNodeGroup", node_x, node_y, x_gap, y_gap)
                apply_node, _, _ = create_node(page_nodegroup, "GeometryNodeGroup", node_x+190, node_y-110, 0, 0) # next node top
                apply_node.node_tree = apply_settings.copy()
                apply_node.node_tree.nodes['Render Type'].node_tree = use_render_type
                apply_node.node_tree.nodes['Mesh Anim'].node_tree = use_stroke_mesh_anim
                apply_node.node_tree.nodes['Mesh Anim'].inputs["Current Index"].default_value = len(page_strokes)-1-s_idx
                apply_node.node_tree.nodes['Mesh Anim'].inputs["Total Index"].default_value = len(page_strokes)
                curve_node.name = f"strokes.curve"
                curve_node.label = f"strokes.curve"
                curve_nodegroup_temp.name = curve_node.name
                curve_node.node_tree = curve_nodegroup_temp
                if gp_materials['line'][stroke['color']]['index'] != 0:
                    char_setting_node.inputs['Individual Control'].default_value = True
                    char_setting_node.inputs['Color'].default_value = stroke['color']
                curve_node.use_custom_color = True
                curve_node.color = (0.35, 0.35, 0.6)
                page_nodegroup.links.new(groupIn_node.outputs['Geometry'], curve_node.inputs["Geometry"])
                page_nodegroup.links.new(curve_node.outputs['Curve'], apply_node.inputs["Geometry"])
                page_nodegroup.links.new(apply_node.outputs['Geometry'], stroke_join_node.inputs["Geometry"])
                stroke_nodes[f"{curve_node.name}"] = curve_node
                for idx in range(len(morph_setting)):
                    item = morph_setting[idx].add()
                    item.inputs = curve_node.name
                    item.type = 'stroke'
                    item.item_idx = len(morph_setting[idx]) - 1
                    item.page_idx  = page_num
                    item.collection_idx  = idx
                    item.obj_id  = formula_obj["math_anim_obj"]

            else:
                self.report({"WARNING"},f"The shape type of stroke {stroke['type']} hasn't supported yet!")

        # stroke node settings
        print("stroke loop time:", time.perf_counter()-t); t=time.perf_counter()

        page_fills = fills[page_num]
        node_x = 3300
        node_y = -len(page_fills)*100/2
        x_gap = 50
        y_gap = 10
        if len(page_fills)>0:
            groupIn_node, _, _ = create_node(page_nodegroup, "NodeGroupInput", 2900, -100, 0, 0) # next node right
            groupIn_node.name = "Group Input Fills"
        for f_idx, fill in enumerate(page_fills[::-1]):
            if fill['type'] == 'rect':
                quad_node, node_xx, node_y = create_node(page_nodegroup, "GeometryNodeGroup", node_x, node_y, x_gap, y_gap) # next on top
                apply_node, _, _ = create_node(page_nodegroup, "GeometryNodeGroup", node_x+190, node_y-110, 0, 0) # next node top
                apply_node.node_tree = apply_settings.copy()
                apply_node.node_tree.nodes['Render Type'].node_tree = use_render_type
                apply_node.node_tree.nodes['Mesh Anim'].node_tree = use_fill_mesh_anim
                apply_node.node_tree.nodes['Mesh Anim'].inputs["Current Index"].default_value = len(page_fills)-1-f_idx
                apply_node.node_tree.nodes['Mesh Anim'].inputs["Total Index"].default_value = len(page_fills)
                quad_node.name = f"fills.rectange"
                quad_node.label = f"fills.rectange"
                quad_nodegroup_temp = quad_nodegroup.copy()
                quad_nodegroup_temp.nodes['Char Settings'].node_tree = use_char_setting
                quad_nodegroup_temp.nodes['Instance Anim'].node_tree = use_fill_instance_anim
                quad_nodegroup_temp.nodes['Curve Anim'].node_tree = use_fill_curve_anim
                quad_nodegroup_temp.nodes['Curve Anim'].inputs['Index'].default_value = len(page_fills)-1-f_idx
                quad_nodegroup_temp.nodes['Instance Anim'].inputs['Index'].default_value = len(page_fills)-1-f_idx
                quad_nodegroup_temp.name = quad_node.name
                set_quad_node = quad_nodegroup_temp.nodes['Quadrilateral']
                char_setting_node = quad_nodegroup_temp.nodes['Char Settings']
                char_setting_node.inputs['Curve Radius'].default_value = curve_radius
                char_setting_node.inputs['Color Strength'].default_value = color_strength
                # get average and shift to center zero
                sum_x = sum(point[0] for point in stroke['control_points'])
                sum_y = sum(point[1] for point in stroke['control_points'])
                num_points = len(stroke['control_points'])
                avg_x = sum_x/num_points
                avg_y = sum_y/num_points
                points = [(x-avg_x, y-avg_y, z) for x, y, z in stroke['control_points']]
                char_setting_node.inputs['Offset'].default_value = (avg_x, avg_y, -0.0001)
                for i in range(7,11):
                    set_quad_node.inputs[j].default_value[0:2] = points[j-7]
                quad_node.use_custom_color = True
                quad_node.color = (0.60, 0.60, 0.40)
                quad_node.node_tree = quad_nodegroup_temp
                if gp_materials['fill'][fill['color']]['index'] != 0:
                    char_setting_node.inputs['Individual Control'].default_value = True
                    char_setting_node.inputs['Color'].default_value = fill['color']
                page_nodegroup.links.new(groupIn_node.outputs['Geometry'], quad_node.inputs["Geometry"])
                page_nodegroup.links.new(quad_node.outputs['Curve'], apply_node.inputs["Geometry"])
                page_nodegroup.links.new(apply_node.outputs['Geometry'], fill_join_node.inputs["Geometry"])
                fill_nodes[f"{quad_node.name}"] = quad_node
                for idx in range(len(morph_setting)):
                    item = morph_setting[idx].add()
                    item.inputs = quad_node.name
                    item.type = 'fill'
                    item.item_idx = len(morph_setting[idx]) - 1
                    item.page_idx  = page_num
                    item.collection_idx  = idx
                    item.obj_id  = formula_obj["math_anim_obj"]

            elif fill['type'] == 'quad':
                quad_node, node_xx, node_y = create_node(page_nodegroup, "GeometryNodeCurvePrimitiveQuadrilateral", node_x, node_y, x_gap, y_gap) # next on top
                apply_node, _, _ = create_node(page_nodegroup, "GeometryNodeGroup", node_x+190, node_y-110, 0, 0) # next on top
                apply_node.node_tree = apply_settings.copy()
                apply_node.node_tree.nodes['Render Type'].node_tree = use_render_type
                apply_node.node_tree.nodes['Mesh Anim'].node_tree = use_fill_mesh_anim
                apply_node.node_tree.nodes['Mesh Anim'].inputs["Current Index"].default_value = len(page_fills)-1-f_idx
                apply_node.node_tree.nodes['Mesh Anim'].inputs["Total Index"].default_value = len(page_fills)
                quad_node.name = f"fills.quad"
                quad_node.label = f"fills.quad"
                quad_nodegroup_temp = quad_nodegroup.copy()
                quad_nodegroup_temp.nodes['Char Settings'].node_tree = use_char_setting
                quad_nodegroup_temp.nodes['Instance Anim'].node_tree = use_fill_instance_anim
                quad_nodegroup_temp.nodes['Curve Anim'].node_tree = use_fill_curve_anim
                quad_nodegroup_temp.nodes['Curve Anim'].inputs['Index'].default_value = len(page_fills)-1-f_idx
                quad_nodegroup_temp.nodes['Instance Anim'].inputs['Index'].default_value = len(page_fills)-1-f_idx
                quad_nodegroup_temp.name = quad_node.name
                set_quad_node = quad_nodegroup_temp.nodes['Quadrilateral']
                char_setting_node = quad_nodegroup_temp.nodes['Char Settings']
                char_setting_node.inputs['Curve Radius'].default_value = curve_radius
                char_setting_node.inputs['Color Strength'].default_value = color_strength
                # get average and shift to center zero
                sum_x = sum(point[0] for point in stroke['control_points'])
                sum_y = sum(point[1] for point in stroke['control_points'])
                num_points = len(stroke['control_points'])
                avg_x = sum_x/num_points
                avg_y = sum_y/num_points
                points = [(x-avg_x, y-avg_y, z) for x, y, z in stroke['control_points']]
                char_setting_node.inputs['Offset'].default_value = (avg_x, avg_y, -0.0001)
                for j in range(7,11):
                    set_quad_node.inputs[j].default_value[0:2] = points[j-7]
                quad_node.use_custom_color = True
                quad_node.color = (0.60, 0.60, 0.40)
                quad_node.node_tree = quad_nodegroup_temp
                if gp_materials['fill'][fill['color']]['index'] != 0:
                    char_setting_node.inputs['Individual Control'].default_value = True
                    char_setting_node.inputs['Color'].default_value = fill['color']
                page_nodegroup.links.new(groupIn_node.outputs['Geometry'], quad_node.inputs["Geometry"])
                page_nodegroup.links.new(quad_node.outputs['Curve'], apply_node.inputs["Geometry"])
                page_nodegroup.links.new(apply_node.outputs['Geometry'], fill_join_node.inputs["Geometry"])
                fill_nodes[f"{quad_node.name}"] = quad_node
                for idx in range(len(morph_setting)):
                    item = morph_setting[idx].add()
                    item.inputs = quad_node.name
                    item.type = 'fill'
                    item.item_idx = len(morph_setting[idx]) - 1
                    item.page_idx  = page_num
                    item.collection_idx  = idx
                    item.obj_id  = formula_obj["math_anim_obj"]

            elif fill['type'] == 'curve':
                #curve_nodegroup = create_curve_nodegroup("curve_nodegroup", fill['control_points'], fill['left_handles'], fill['right_handles'], 0.0)
                curve_nodegroup_temp = curve_nodegroup.copy()
                curve_nodegroup_temp.nodes['Char Settings'].node_tree = use_char_setting
                curve_nodegroup_temp.nodes['Instance Anim'].node_tree = use_fill_instance_anim
                curve_nodegroup_temp.nodes['Curve Anim'].node_tree = use_fill_curve_anim
                curve_nodegroup_temp.nodes['Curve Anim'].inputs['Index'].default_value = len(page_fills)-1-f_idx
                curve_nodegroup_temp.nodes['Instance Anim'].inputs['Index'].default_value = len(page_fills)-1-f_idx
                switch_node = curve_nodegroup_temp.nodes['Switch']
                switch_node.inputs['Switch'].default_value = False
                char_setting_node = curve_nodegroup_temp.nodes['Char Settings']
                char_setting_node.inputs['Curve Radius'].default_value = curve_radius
                char_setting_node.inputs['Color Strength'].default_value = color_strength

                # control points
                control_points = fill['control_points']
                # get average and shift to zero
                sum_x = sum(point[0] for point in control_points)
                sum_y = sum(point[1] for point in control_points)
                num_points = len(control_points)
                avg_x = sum_x/num_points
                avg_y = sum_y/num_points
                control_points = [(x-avg_x, y-avg_y, z) for x, y, z in control_points]
                char_setting_node.inputs['Offset'].default_value = (avg_x, avg_y, -0.0001)
                control_points_join_node = curve_nodegroup_temp.nodes['Control_points Join Geometry']
                for j in range(len(control_points)-1,-1,-1):
                    if j == len(control_points) - 1:
                        point_node = curve_nodegroup_temp.nodes['Control Points']
                        node_lx = point_node.location.x
                        node_ly = point_node.location.y + point_node.height + 10
                    else:
                        point_node, node_lx, node_ly = create_node(curve_nodegroup_temp, "GeometryNodePoints", node_lx, node_ly, 0, 10) # next on top
                        point_node.name = "Control Points"
                    point_node.inputs['Position'].default_value = control_points[j]
                    point_node.inputs['Position'].hide = True
                    point_node.inputs['Count'].hide = True
                    point_node.inputs['Radius'].hide = True
                    curve_nodegroup_temp.links.new(point_node.outputs['Points'], control_points_join_node.inputs['Geometry'])
                # left handle points
                left_handles = fill['left_handles']
                left_handles = [(x-avg_x, y-avg_y, z) for x, y, z in left_handles]
                left_handle_join_node = curve_nodegroup_temp.nodes['Left_handle Join Geometry']
                for j in range(len(left_handles)-1,-1,-1):
                    if j == len(left_handles) - 1:
                        point_node = curve_nodegroup_temp.nodes['Left_handle Points']
                        node_lx = point_node.location.x
                        node_ly = point_node.location.y - point_node.height - 10
                    else:
                        point_node, node_lx, node_ly = create_node(curve_nodegroup_temp, "GeometryNodePoints", node_lx, node_ly, 0, -10) # next on lower
                        point_node.name = "Left_handle Points"
                    point_node.inputs['Position'].default_value = left_handles[j]
                    point_node.inputs['Position'].hide = True
                    point_node.inputs['Count'].hide = True
                    point_node.inputs['Radius'].hide = True
                    curve_nodegroup_temp.links.new(point_node.outputs['Points'], left_handle_join_node.inputs['Geometry'])
                # right handle points
                right_handles = fill['right_handles']
                right_handles = [(x-avg_x, y-avg_y, z) for x, y, z in right_handles]
                right_handle_join_node = curve_nodegroup_temp.nodes['Right_handle Join Geometry']
                for j in range(len(right_handles)-1,-1,-1):
                    if j == len(right_handles) - 1:
                        point_node = curve_nodegroup_temp.nodes['Right_handle Points']
                        node_lx = point_node.location.x
                        node_ly = point_node.location.y - point_node.height - 10
                    else:
                        point_node, node_lx, node_ly = create_node(curve_nodegroup_temp, "GeometryNodePoints", node_lx, node_ly, 0, -10) # next on lower
                        point_node.name = "Right_handle Points"
                    point_node.inputs['Position'].default_value = right_handles[j]
                    point_node.inputs['Position'].hide = True
                    point_node.inputs['Count'].hide = True
                    point_node.inputs['Radius'].hide = True
                    curve_nodegroup_temp.links.new(point_node.outputs['Points'], right_handle_join_node.inputs['Geometry'])
                curve_node, node_xx, node_y = create_node(page_nodegroup, "GeometryNodeGroup", node_x, node_y, x_gap, y_gap)
                apply_node, _, _ = create_node(page_nodegroup, "GeometryNodeGroup", node_x+190, node_y-110, 0, 0) # next on top
                apply_node.node_tree = apply_settings.copy()
                apply_node.node_tree.nodes['Render Type'].node_tree = use_render_type
                apply_node.node_tree.nodes['Mesh Anim'].node_tree = use_fill_mesh_anim
                apply_node.node_tree.nodes['Mesh Anim'].inputs["Current Index"].default_value = len(page_fills)-1-f_idx
                apply_node.node_tree.nodes['Mesh Anim'].inputs["Total Index"].default_value = len(page_fills)
                curve_node.name = f"fills.curve"
                curve_node.label = f"fills.curve"
                curve_node.node_tree = curve_nodegroup_temp
                if gp_materials['fill'][fill['color']]['index'] != 0:
                    char_setting_node.inputs['Individual Control'].default_value = True
                    char_setting_node.inputs['Color'].default_value = fill['color']
                curve_nodegroup_temp.name = curve_node.name
                curve_node.use_custom_color = True
                curve_node.color = (0.60, 0.60, 0.40)
                page_nodegroup.links.new(groupIn_node.outputs['Geometry'], curve_node.inputs["Geometry"])
                page_nodegroup.links.new(curve_node.outputs['Curve'], apply_node.inputs["Geometry"])
                page_nodegroup.links.new(apply_node.outputs['Geometry'], fill_join_node.inputs["Geometry"])
                fill_nodes[f"{curve_node.name}"] = curve_node
                for idx in range(len(morph_setting)):
                    item = morph_setting[idx].add()
                    item.inputs = curve_node.name
                    item.type = 'fill'
                    item.item_idx = len(morph_setting[idx]) - 1
                    item.page_idx  = page_num
                    item.collection_idx  = idx
                    item.obj_id  = formula_obj["math_anim_obj"]

            else:
                self.report({"WARNING"},f"The shape type of fill {fill['type']} hasn't supported yet!")

        # fill node settings
        print("fill loop time:", time.perf_counter()-t); t=time.perf_counter()

        page_node.name = f"page{page_num}group"
        page_node.node_tree = page_nodegroup

        page_nodegroup.links.new(char_join_node.outputs['Geometry'], join_node.inputs['Geometry'])
        page_nodegroup.links.new(stroke_join_node.outputs['Geometry'], join_node.inputs['Geometry'])
        page_nodegroup.links.new(fill_join_node.outputs['Geometry'], join_node.inputs['Geometry'])
        page_nodegroup.links.new(join_node.outputs['Geometry'], trans_node.inputs['Geometry'])
        page_nodegroup.links.new(in_node.outputs['Scale Factor'], trans_node.inputs['Scale'])
        page_nodegroup.links.new(trans_node.outputs['Geometry'], out_node.inputs['Geometry'])

        formula_nodegroup.links.new(formula_in_node.outputs['Scale Factor'], page_node.inputs["Scale Factor"])
        formula_nodegroup.links.new(formula_in_node.outputs['Geometry'], page_node.inputs["Geometry"])
        formula_nodegroup.links.new(page_node.outputs['Geometry'], formula_join_node.inputs["Geometry"])

        node_trees = {'text_nodes': text_nodes, 'stroke_nodes': stroke_nodes, 'fill_nodes': fill_nodes}
        vb.formula_node_trees[formula_obj["math_anim_obj"]].append(node_trees)

    geometryMd.properties.inputs['Socket_2']['value'] = 1.0

    return formula_nodegroup
