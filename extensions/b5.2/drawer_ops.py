import bpy
from . import variables as vb #import vb.font_path_dict, vb.font_save_file
from .operations import MATH_OT_CreateFormula, animsetting_status_reset
from .geonodes import create_node, arrange_nodes, import_anim_nodegroups, setup_gpencil_geonodes
from .curve_anim_presets import add_curve_preset, del_curve_preset

class MATH_OT_CreateGPencil(bpy.types.Operator):
    bl_idname = "math_anim.add_gp_obj"
    bl_label = "Add GPencil"
    bl_description = 'Add a Grease Pencil'
    bl_options = {'REGISTER', 'UNDO'}

    obj_name: bpy.props.StringProperty(default="GPencil")
    geomd_category: bpy.props.StringProperty(
            default="Plotter",
            description="Geometry Nodes Modifier category, Plotter or Drawer or Formula",
            )

    def invoke(self, context, event):
        node_groups = ['GP Material', 'Layer Select', 'Axis Labels', 'Finalize Curves']
        for group_name in node_groups:
            if bpy.data.node_groups.get(group_name) is None:
                import_anim_nodegroups([group_name])
                bpy.data.node_groups[group_name].use_fake_user = True
        return self.execute(context)

    def execute(self, context):
        gp_obj = MATH_OT_CreateFormula.create_formula_holder(self, context, obj_name=self.obj_name)
        context.scene.math_anim_gpobjects.gp_object = gp_obj.name
        node_group = setup_gpencil_geonodes(gp_obj, cate_name=self.geomd_category)
        bpy.ops.math_anim.update_morph_objects()
        bpy.data.grease_pencils[gp_obj.data.name].stroke_depth_order = '3D'
        return {'FINISHED'}

class MATH_OT_AddGPAnim(bpy.types.Operator):
    bl_idname = "math_anim.add_gp_anim"
    bl_label = "Add Anims for GP layers "
    bl_description = 'Add Anims for a Grease Pencil layer'
    bl_options = {'REGISTER', 'UNDO'}

    add_anim: bpy.props.EnumProperty(
        name = 'Add Anim',
        items = [
            ('grow_anim', 'Grow Anim', 'Add a preset grow animation for the selection node'),
            ('writing_anim', 'Writing Anim', 'Add a preset writing animation for the selection node'),
            ('light_flow', 'Light Flow Anim', 'Add a preset writing animation for the selection node'),
            ('wave_anim', 'Wave Anim', 'Add a preset wave animation for the selection node'),
            ('flow_anim', 'Edge Flow Anim', 'Add a preset edge flow animation for the selection node'),
            ('transform_anim', 'Transform Anim', 'Add a preset transform animation for the selection node'),
            ('transform', 'Transform', 'Add a transform animation by yourself for the selection node'),
            ('add_snapshot', 'Add Snapshot', 'Add snapshots to remember states, should be used with changing parameters or transform over time'),
            ('curve_normal_tangent', 'Normal/Tanget Line', 'Add normal or tangent lines for a curve'),
        ],
        #default = 'grow_anim',
    )
    track_tag: bpy.props.StringProperty( default = '', name = 'Track Tag')
    def invoke(self, context, event):
        gp_obj = bpy.data.objects.get(context.scene.math_anim_gpobjects.gp_object)
        if gp_obj is None:
            self.report({'WARNING'}, "No GP object found")
            return {'CANCELLED'}
        gp_layer = gp_obj.data.layers.get(context.scene.math_anim_gplayers.gp_layer)
        if gp_layer is None:
            self.report({'WARNING'}, "No GP layer found")
            return {'CANCELLED'}
        # prepare animgroups
        anim_options = {'grow_anim': 'Grow Anim', 'transform': 'Transform.Local', 'writing_anim': 'Writing Curve Anim', 'transform_anim': "Transform Anim", 'flow_anim': 'Edge Flow Anim', 'light_flow':'Light Flow Anim', 'wave_anim': 'Wave Anim', 'curve_normal_tangent': 'Curve Normal Tangent', 'add_snapshot': 'Add Snapshot'}
        anim_groups = ['Curve Arrow', anim_options[self.add_anim], 'GP Material', 'Layer Select']
        for group_name in anim_groups:
            if bpy.data.node_groups.get(group_name) is None:
                import_anim_nodegroups([group_name])
                bpy.data.node_groups[group_name].use_fake_user = True
        # initialize the anim nodes tracker
        if self.track_tag not in vb.formula_anim_nodes:
            vb.formula_anim_nodes[self.track_tag] = {}
        if gp_obj["math_anim_obj"] not in vb.formula_anim_nodes[self.track_tag]:
            vb.formula_anim_nodes[self.track_tag][gp_obj["math_anim_obj"]] = {}
        if gp_layer.name not in vb.formula_anim_nodes[self.track_tag][gp_obj["math_anim_obj"]]:
            vb.formula_anim_nodes[self.track_tag][gp_obj["math_anim_obj"]][gp_layer.name] = {}
        if self.add_anim not in vb.formula_anim_nodes[self.track_tag][gp_obj["math_anim_obj"]][gp_layer.name]:
            vb.formula_anim_nodes[self.track_tag][gp_obj["math_anim_obj"]][gp_layer.name][self.add_anim] = []

        return self.execute(context)

    def execute(self, context):
        gp_obj = bpy.data.objects.get(context.scene.math_anim_gpobjects.gp_object)
        if gp_obj is None:
            self.report({'WARNING'}, "No GP object found")
            return {'CANCELLED'}
        gp_layer = gp_obj.data.layers.get(context.scene.math_anim_gplayers.gp_layer)
        if gp_layer is None:
            self.report({'WARNING'}, "No GP layer found")
            return {'CANCELLED'}
        node_group = None
        for md in gp_obj.modifiers:
            if 'drawerGeoNodes' == md.name or 'formulaGeoNodes' == md.name or 'plotterGeoNodes' == md.name:
                node_group = md.node_group
        if node_group is None:
            self.report({'WARNING'}, "No node group found")
            return {'CANCELLED'}

        layer_node = node_group.nodes.get(gp_layer.name)
        layer_nodegroup = layer_node.node_tree
        anim_setting_status = context.scene.math_animSetting_status
        curve_anim_setting = context.scene.math_anim_curve_gen_settings
        if self.add_anim == 'grow_anim':
            node = layer_nodegroup.nodes.new('GeometryNodeGroup')
            node.node_tree = bpy.data.node_groups['Grow Anim'].copy()
            node.name = node.node_tree.name
            p_socket = layer_nodegroup.nodes['Geometry to Instance'].outputs['Instances']
            n_socket = p_socket.links[0].to_socket
            layer_nodegroup.links.new(p_socket, node.inputs['Geometry'])
            layer_nodegroup.links.new(node.outputs['Geometry'], n_socket)
            layer_nodegroup.links.new(layer_nodegroup.nodes['Center'].outputs['Vector'], node.inputs['Center'])
            node_x = p_socket.node.location.x + 190
            node_y = p_socket.node.location.y
            n_node = p_socket.links[0].to_node
            while n_node.name != 'Reroute':
                n_node.location.x = node_x
                n_node.location.y = node_y
                node_x = n_node.location.x + 190
                node_y = n_node.location.y
                n_node = n_node.outputs[0].links[0].to_node
            vb.formula_anim_nodes[self.track_tag][gp_obj["math_anim_obj"]][gp_layer.name][self.add_anim].append(node)
            item = anim_setting_status.add()
            key_name = f"{node.name}"
            item.name = key_name
            vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
            add_curve_preset(curve_anim_setting, node.node_tree.nodes['Float Curve'])
        elif self.add_anim == 'writing_anim':
            node = layer_nodegroup.nodes.new('GeometryNodeGroup')
            node.node_tree = bpy.data.node_groups['Writing Curve Anim'].copy()
            node.name = node.node_tree.name
            node.inputs['Local'].default_value = False
            node.inputs['Is GP Layer?'].default_value = True
            p_socket = layer_nodegroup.nodes['Realize Instances'].outputs['Geometry']
            n_socket = p_socket.links[0].to_socket
            layer_nodegroup.links.new(p_socket, node.inputs['Curve'])
            layer_nodegroup.links.new(node.outputs['Curve'], n_socket)
            node_x = p_socket.node.location.x + 190
            node_y = p_socket.node.location.y
            n_node = p_socket.links[0].to_node
            while n_node.name != 'Reroute':
                n_node.location.x = node_x
                n_node.location.y = node_y
                node_x = n_node.location.x + 190
                node_y = n_node.location.y
                n_node = n_node.outputs[0].links[0].to_node
            vb.formula_anim_nodes[self.track_tag][gp_obj["math_anim_obj"]][gp_layer.name][self.add_anim].append(node)
            item = anim_setting_status.add()
            key_name = f"{node.name}"
            item.name = key_name
            vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
            add_curve_preset(curve_anim_setting, node.node_tree.nodes['Float Curve'])
        elif self.add_anim == 'light_flow':
            node = layer_nodegroup.nodes.new('GeometryNodeGroup')
            node.node_tree = bpy.data.node_groups['Light Flow Anim'].copy()
            node.name = node.node_tree.name
            p_socket = layer_nodegroup.nodes['Realize Instances'].outputs['Geometry']
            n_socket = p_socket.links[0].to_socket
            layer_nodegroup.links.new(p_socket, node.inputs['Geometry'])
            layer_nodegroup.links.new(node.outputs['Geometry'], n_socket)
            node_x = p_socket.node.location.x + 190
            node_y = p_socket.node.location.y
            n_node = p_socket.links[0].to_node
            while n_node.name != 'Reroute':
                n_node.location.x = node_x
                n_node.location.y = node_y
                node_x = n_node.location.x + 190
                node_y = n_node.location.y
                n_node = n_node.outputs[0].links[0].to_node
            vb.formula_anim_nodes[self.track_tag][gp_obj["math_anim_obj"]][gp_layer.name][self.add_anim].append(node)
            item = anim_setting_status.add()
            key_name = f"{node.name}"
            item.name = key_name
            vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
            add_curve_preset(curve_anim_setting, node.node_tree.nodes['Anim Curve'])
        elif self.add_anim == 'wave_anim':
            # global wave
            node1 = layer_nodegroup.nodes.new('GeometryNodeGroup')
            node1.node_tree = bpy.data.node_groups['Wave Anim'].copy()
            node1.name = node1.node_tree.name
            node1.inputs['Passthrough'].default_value = False
            p_socket = layer_nodegroup.nodes['Geometry to Instance'].outputs['Instances']
            n_socket = p_socket.links[0].to_socket
            layer_nodegroup.links.new(p_socket, node1.inputs['Geometry'])
            layer_nodegroup.links.new(node1.outputs['Geometry'], n_socket)
            node_x = p_socket.node.location.x + 190
            node_y = p_socket.node.location.y
            n_node = p_socket.links[0].to_node
            while n_node.name != 'Reroute':
                n_node.location.x = node_x
                n_node.location.y = node_y
                node_x = n_node.location.x + 190
                node_y = n_node.location.y
                n_node = n_node.outputs[0].links[0].to_node
            # local wave
            node2 = layer_nodegroup.nodes.new('GeometryNodeGroup')
            node2.node_tree = bpy.data.node_groups['Wave Anim'].copy()
            node2.name = node2.node_tree.name
            node2.inputs['Passthrough'].default_value = True
            p_socket = layer_nodegroup.nodes['Realize Instances'].outputs['Geometry']
            n_socket = p_socket.links[0].to_socket
            layer_nodegroup.links.new(p_socket, node2.inputs['Geometry'])
            layer_nodegroup.links.new(node2.outputs['Geometry'], n_socket)
            node_x = p_socket.node.location.x + 190
            node_y = p_socket.node.location.y
            n_node = p_socket.links[0].to_node
            while n_node.name != 'Reroute':
                n_node.location.x = node_x
                n_node.location.y = node_y
                node_x = n_node.location.x + 190
                node_y = n_node.location.y
                n_node = n_node.outputs[0].links[0].to_node
            vb.formula_anim_nodes[self.track_tag][gp_obj["math_anim_obj"]][gp_layer.name][self.add_anim].append((node1, node2))
            item = anim_setting_status.add()
            key_name = f"{node1.name}"
            item.name = key_name
            vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
            for node in [node1, node2]:
                add_curve_preset(curve_anim_setting, node.node_tree.nodes['Float Curve'])
        elif self.add_anim == 'flow_anim':
            join_socket = layer_nodegroup.nodes['Join Curve'].inputs['Geometry']
            node_y = join_socket.node.location.y
            for link in join_socket.links:
                if link.from_node.location.y > node_y:
                    node_y = link.from_node.location.y
            flow_node, _, _ = create_node(layer_nodegroup, "GeometryNodeGroup", join_socket.node.location.x - 190, node_y+520,0,0)
            flow_node.node_tree = bpy.data.node_groups['Edge Flow Anim'].copy()
            flow_node.name = flow_node.node_tree.name
            flow_node.inputs['Closed Path'].default_value = False
            p_socket = layer_nodegroup.nodes['GP to Curve'].outputs['Curves']
            n_socket = layer_nodegroup.nodes['Join Geometry'].inputs['Geometry']
            layer_nodegroup.links.new(p_socket, flow_node.inputs['Geometry'])
            layer_nodegroup.links.new(flow_node.outputs['Geometry'], n_socket)
            layer_nodegroup.links.new(flow_node.outputs['Geometry'], join_socket)
            vb.formula_anim_nodes[self.track_tag][gp_obj["math_anim_obj"]][gp_layer.name][self.add_anim].append(flow_node)
            item = anim_setting_status.add()
            key_name = f"{flow_node.name}"
            item.name = key_name
            vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
            add_curve_preset(curve_anim_setting, node.node_tree.nodes['Float Curve'])
        elif self.add_anim == 'transform':
            node = layer_nodegroup.nodes.new('GeometryNodeGroup')
            node.node_tree = bpy.data.node_groups['Transform.Local'].copy()
            node.name = node.node_tree.name
            p_socket = layer_nodegroup.nodes['Geometry to Instance'].outputs['Instances']
            n_socket = p_socket.links[0].to_socket
            layer_nodegroup.links.new(p_socket, node.inputs['Geometry'])
            layer_nodegroup.links.new(node.outputs['Geometry'], n_socket)
            node_x = p_socket.node.location.x + 190
            node_y = p_socket.node.location.y
            n_node = p_socket.links[0].to_node
            while n_node.name != 'Reroute':
                n_node.location.x = node_x
                n_node.location.y = node_y
                node_x = n_node.location.x + 190
                node_y = n_node.location.y
                n_node = n_node.outputs[0].links[0].to_node
            vb.formula_anim_nodes[self.track_tag][gp_obj["math_anim_obj"]][gp_layer.name][self.add_anim].append(node)
            item = anim_setting_status.add()
            key_name = f"{node.name}"
            item.name = key_name
            vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
        elif self.add_anim == 'transform_anim':
            node = layer_nodegroup.nodes.new('GeometryNodeGroup')
            node.node_tree = bpy.data.node_groups['Transform Anim'].copy()
            node.name = node.node_tree.name
            p_socket = layer_nodegroup.nodes['Geometry to Instance'].outputs['Instances']
            n_socket = p_socket.links[0].to_socket
            layer_nodegroup.links.new(p_socket, node.inputs['Instances'])
            layer_nodegroup.links.new(node.outputs['Instances'], n_socket)
            node_x = p_socket.node.location.x + 190
            node_y = p_socket.node.location.y
            n_node = p_socket.links[0].to_node
            while n_node.name != 'Reroute':
                n_node.location.x = node_x
                n_node.location.y = node_y
                node_x = n_node.location.x + 190
                node_y = n_node.location.y
                n_node = n_node.outputs[0].links[0].to_node
            vb.formula_anim_nodes[self.track_tag][gp_obj["math_anim_obj"]][gp_layer.name][self.add_anim].append(node)
            item = anim_setting_status.add()
            key_name = f"{node.name}"
            item.name = key_name
            vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
            for transform in ['Rotate', 'Offset', 'Scale']:
                add_curve_preset(curve_anim_setting, node.node_tree.nodes[f'{transform} Anim Curve'])
        elif self.add_anim == 'add_snapshot':
            node = layer_nodegroup.nodes.new('GeometryNodeGroup')
            node.node_tree = bpy.data.node_groups['Add Snapshot'].copy()
            node.name = node.node_tree.name
            n_socket = layer_nodegroup.nodes['Realize Instances'].inputs['Geometry']
            p_socket = n_socket.links[0].from_socket
            layer_nodegroup.links.new(p_socket, node.inputs['Geometry'])
            layer_nodegroup.links.new(node.outputs['Geometry'], n_socket)
            node_x = p_socket.node.location.x + 190
            node_y = p_socket.node.location.y
            n_node = p_socket.links[0].to_node
            while n_node.name != 'Reroute':
                n_node.location.x = node_x
                n_node.location.y = node_y
                node_x = n_node.location.x + 190
                node_y = n_node.location.y
                n_node = n_node.outputs[0].links[0].to_node
            vb.formula_anim_nodes[self.track_tag][gp_obj["math_anim_obj"]][gp_layer.name][self.add_anim].append(node)
            item = anim_setting_status.add()
            key_name = f"{node.name}"
            item.name = key_name
            vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
        elif self.add_anim == 'curve_normal_tangent':
            join_socket = layer_nodegroup.nodes['Join Curve'].inputs['Geometry']
            node_y = join_socket.node.location.y
            for link in join_socket.links:
                if link.from_node.location.y < node_y:
                    node_y = link.from_node.location.y
            normal_node, _, _ = create_node(layer_nodegroup, "GeometryNodeGroup", join_socket.node.location.x - 190, node_y-520,0,0)
            normal_node.node_tree = bpy.data.node_groups['Curve Normal Tangent'].copy()
            normal_node.name = normal_node.node_tree.name
            p_socket = layer_nodegroup.nodes['Reroute'].outputs['Output']
            n_socket = layer_nodegroup.nodes['Join Geometry'].inputs['Geometry']
            layer_nodegroup.links.new(p_socket, normal_node.inputs['Grease Pencil'])
            layer_nodegroup.links.new(normal_node.outputs['Grease Pencil'], n_socket)
            layer_nodegroup.links.new(normal_node.outputs['Curve'], join_socket)
            vb.formula_anim_nodes[self.track_tag][gp_obj["math_anim_obj"]][gp_layer.name][self.add_anim].append(normal_node)
            item = anim_setting_status.add()
            key_name = f"{normal_node.name}"
            item.name = key_name
            vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
        return {'FINISHED'}

class MATH_OT_DelGPAnim(bpy.types.Operator):
    bl_idname = "math_anim.del_gp_anim"
    bl_label = "Del Anims for GP layers "
    bl_description = 'Delete Anims for a Grease Pencil layer'
    bl_options = {'REGISTER', 'UNDO'}

    anim_type: bpy.props.StringProperty( default = '', name = 'Anim Type')
    anim_node: bpy.props.StringProperty( default = '', name = 'Anim Node')
    track_tag: bpy.props.StringProperty( default = '', name = 'Track Tag')

    def execute(self, context):
        gp_obj = bpy.data.objects.get(context.scene.math_anim_gpobjects.gp_object)
        gp_layer = gp_obj.data.layers.get(context.scene.math_anim_gplayers.gp_layer)
        node_group = bpy.data.node_groups[self.anim_node.split('**')[0]]
        node = node_group.nodes[self.anim_node.split('**')[1]]
        anim_nodes = vb.formula_anim_nodes[self.track_tag][gp_obj["math_anim_obj"]][gp_layer.name][self.anim_type]
        curve_anim_setting = context.scene.math_anim_curve_gen_settings
        if self.anim_type == 'wave_anim':
            node2 = node_group.nodes[self.anim_node.split('**')[2]]
            nodes = [node2, node]
            vb.formula_anim_nodes[self.track_tag][gp_obj["math_anim_obj"]][gp_layer.name][self.anim_type].remove((node, node2))
            animsetting_status_reset(context, [node.name])
            for rnode in nodes:
                del_curve_preset(curve_anim_setting, rnode.node_tree.nodes['Float Curve'])
                p_socket = rnode.inputs[0].links[0].from_socket
                n_socket = rnode.outputs[0].links[0].to_socket
                node_group.nodes.remove(rnode)
                node_group.links.new(p_socket, n_socket)
        else:
            vb.formula_anim_nodes[self.track_tag][gp_obj["math_anim_obj"]][gp_layer.name][self.anim_type].remove(node)
            animsetting_status_reset(context, [node.name])
            p_socket = node.inputs[0].links[0].from_socket
            n_socket = node.outputs[0].links[0].to_socket
            if self.anim_type != 'flow_anim':
                node_group.links.new(p_socket, n_socket)
            if self.anim_type in ["writing_anim", "flow_anim", "grow_anim", "transform_anim", "light_flow"]:
                if self.anim_type == "transform_anim":
                    for transform in ["Scale", "Offset", "Rotate"]:
                        del_curve_preset(curve_anim_setting, node.node_tree.nodes[f'{transform} Anim Curve'])
                elif self.anim_type == "light_flow":
                    del_curve_preset(curve_anim_setting, node.node_tree.nodes['Anim Curve'])
                else:
                    del_curve_preset(curve_anim_setting, node.node_tree.nodes['Float Curve'])
            node_group.nodes.remove(node)

        return {'FINISHED'}

classes = (
    MATH_OT_CreateGPencil,
    MATH_OT_AddGPAnim,
    MATH_OT_DelGPAnim,
)
register, unregister = bpy.utils.register_classes_factory(classes)
