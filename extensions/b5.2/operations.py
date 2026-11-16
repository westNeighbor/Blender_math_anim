# all data operations
import bpy
import tempfile
import random
import bmesh
import os
import time
from . import variables as vb #import vb.font_path_dict, vb.font_save_file
from .utils import load_dict_from_file, build_file_path_dict, extract_text_and_shape, compile_tex
from .properties import MATH_ANIM_Formula_Properties, MATH_ANIM_Morph_Targets
from .geonodes import setup_formula_geonodes, import_anim_nodegroups, create_node, arrange_nodes
from .curve_anim_presets import add_curve_preset, del_curve_preset

class MATH_OT_PATH_FormulaAddPath(bpy.types.Operator):
    """Add a new path"""
    bl_idname = "math_anim.formula_addpath"
    bl_label = "Add Text or Path"
    bl_description = "Add Text or Path"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        formula_props = context.scene.math_anim_formula_props
        formula_paths = [context.scene.math_anim_optexcode, context.scene.math_anim_typstcode,
                         context.scene.math_anim_optexfile, context.scene.math_anim_typstfile,
                         context.scene.math_anim_pdffile]
        source_items = list(MATH_ANIM_Formula_Properties.bl_rna.properties['formula_source'].enum_items)

        for item_idx in range(len(source_items)):
            if formula_props.formula_source == source_items[item_idx].identifier:
                if item_idx < 2:
                    new_item = formula_paths[item_idx].paths.add()
                    formula_paths[item_idx].active_index = len(formula_paths[item_idx].paths) - 1
                    return {'FINISHED'}
                else:
                    new_item = formula_paths[item_idx].paths.add()
                    new_item.path = self.filepath
                    return {'FINISHED'}

    def invoke(self, context, event):
        formula_props = context.scene.math_anim_formula_props

        if formula_props.formula_source == "Optex_Code" or formula_props.formula_source == "Typst_Code":
            return self.execute(context)
        else:
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}


class MATH_OT_PATH_FormulaRemovePath(bpy.types.Operator):
    """Remove selected paths"""
    bl_idname = "math_anim.formula_removepath"
    bl_label = "Remove Selected Items"
    bl_description = "Remove Selected Items"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        formula_props = context.scene.math_anim_formula_props
        formula_paths = [context.scene.math_anim_optexcode, context.scene.math_anim_typstcode,
                         context.scene.math_anim_optexfile, context.scene.math_anim_typstfile,
                         context.scene.math_anim_pdffile]
        source_items = list(MATH_ANIM_Formula_Properties.bl_rna.properties['formula_source'].enum_items)

        for item_idx in range(len(source_items)):
            if formula_props.formula_source == source_items[item_idx].identifier:
                # Get all selected paths
                selected_items = [i for i, item in enumerate(formula_paths[item_idx].paths) if item.selected]
                # Remove from highest index to lowest to avoid shifting issues
                for index in sorted(selected_items, reverse=True):
                    formula_paths[item_idx].paths.remove(index)

                return {'FINISHED'}

def animsetting_status_reset(context, key_name: list):
    # remove the animsetting status
    anim_setting_status = context.scene.math_animSetting_status
    for i, key in enumerate(key_name):
        remove_idx = -1
        for index, item in enumerate(anim_setting_status):
            if item.name == key:
                remove_idx = index
                break
        if remove_idx >= 0:
            anim_setting_status.remove(remove_idx)
            # also remove the animsetting status tracking and reset index
            vb.formula_animsetting_status.pop(key, None)
            if remove_idx < len(anim_setting_status): # only need reindex larger than remove_idx
                for index, item in enumerate(anim_setting_status):
                    if index >= remove_idx:
                        name = item.name
                        vb.formula_animsetting_status[name] = index

class MATH_OT_DelFormulaAnim(bpy.types.Operator):
    bl_idname = "math_anim.del_formula_anim"
    bl_label = "Delete Formula Animations"
    bl_description = "Delete An Animation"
    bl_options = {'REGISTER', 'UNDO'}

    anim_type: bpy.props.StringProperty(default='')
    node_name: bpy.props.StringProperty(default='')

    def execute(self, context):
        curve_anim_setting = context.scene.math_anim_curve_gen_settings
        if self.anim_type.split('.')[1] == 'morph_anim':
            index = int(self.anim_type.split('.')[0])
            key = self.node_name
            morph_list = vb.formula_anim_nodes['morph_anim'][index][key]
            node_group = None
            source_morph = None
            source_node = None
            for morph_node, mute_nodes, morph_setting in morph_list:
                del_curve_preset(curve_anim_setting, morph_node.node_tree.nodes['Float Curve'])
                color_strength = {}
                source_morph = morph_setting[0]
                source_node = mute_nodes[0]
                if source_morph.type == 'layer':
                    node_group = mute_nodes[0].id_data
                else:
                    node_group = mute_nodes[0].node_tree
                join_node = morph_node.inputs['Target'].links[0].from_socket.node
                for link in join_node.inputs['Geometry'].links:
                    if link.from_node.inputs[0].is_linked:
                        node_group.nodes.remove(link.from_socket.node.inputs[0].links[0].from_node)
                    if link.from_node.name.split('.')[-1] == 'Morph':
                        tree_name = link.from_node.name.removesuffix(".Morph")
                        color_strength[tree_name] = link.from_node.inputs['Color Strength'].default_value
                    node_group.nodes.remove(link.from_socket.node)
                node_group.nodes.remove(join_node)
                node_group.nodes.remove(morph_node)
                for i, morph in enumerate(morph_setting):
                    morph.selected = False
                    morph.keep = False
                    morph.morph = False
                    morph.draw_tag = True
                    node = mute_nodes[i]
                    if morph.type == 'layer':
                        if node.inputs['Color Strength'].default_value == 0.0:
                            node.inputs['Color Strength'].default_value = color_strength[f'{node.node_tree.name}']
                    else:
                        node.mute = False
                        ng = node.id_data
                        if node.name.split('.')[0]=='char':
                            groupInput = ng.nodes['Group Input Chars']
                        elif node.name.split('.')[0]=='strokes':
                            groupInput = ng.nodes['Group Input Strokes']
                        elif node.name.split('.')[0]=='fills':
                            groupInput = ng.nodes['Group Input Fills']
                        ng.links.new(groupInput.outputs['Geometry'], node.inputs['Geometry'])
                    if morph.type == 'input':
                        parent_nodegroup = node.id_data
                        parent_nodegroup.nodes.remove(node)
            refer_node = None
            if source_morph.type == 'layer':
                node_group.links.new(source_node.outputs['Geometry'], node_group.nodes['Join Geometry'].inputs['Geometry'])
                refer_node = source_node
            else:
                node_group.links.new(node_group.nodes['Curve Anim'].outputs['Geometry'], node_group.nodes['Join Geometry'].inputs['Geometry'])
                refer_node = node_group.nodes['Curve Anim']
            node_x = refer_node.location.x
            if source_morph.type == 'layer':
                for socket in source_node.outputs:
                    for link in socket.links:
                        if link.to_node.name != 'Join Geometry':
                            link.from_node.location.x = node_x + 190
            else:
                for link in node_group.nodes['Join Geometry'].inputs['Geometry'].links:
                    if link.from_node.name != 'Curve Anim':
                        link.from_node.location.x = node_x + 190
            vb.formula_anim_nodes['morph_anim'].pop(index)
            key_name = [self.node_name]
            animsetting_status_reset(context, key_name)
            return {'FINISHED'}
        elif self.anim_type.split('.')[1] == 'grow_anim':
            anim_type = self.anim_type.split('.')[0]
            formula_props = context.scene.math_anim_formula_props
            if context.object and (context.object.get("math_anim_obj") is not None):
                formula_obj = context.object
                node_tree = bpy.data.node_groups[self.node_name.split('**')[0]]
                node = node_tree.nodes[self.node_name.split('**')[1]]
                node_group = node.node_tree
                vb.formula_anim_nodes[formula_obj["math_anim_obj"]][anim_type]['grow_anim'].remove(node)
                p_socket = node.inputs['Geometry'].links[0].from_socket
                n_socket = node.outputs['Geometry'].links[0].to_socket
                del_curve_preset(curve_anim_setting, node.node_tree.nodes['Float Curve'])
                node_tree.nodes.remove(node)
                node_tree.links.new(p_socket, n_socket)
                # remove the unused nodegroup
                bpy.data.node_groups.remove(node_group)
                key_name = [self.node_name]
                animsetting_status_reset(context, key_name)
                return {'FINISHED'}
            else:
                return {'CANCELLED'}
        elif self.anim_type.split('.')[1] == 'transform_anim':
            anim_type = self.anim_type.split('.')[0]
            formula_props = context.scene.math_anim_formula_props
            if context.object and (context.object.get("math_anim_obj") is not None):
                formula_obj = context.object
                node_tree = bpy.data.node_groups[self.node_name.split('**')[0]]
                node = node_tree.nodes[self.node_name.split('**')[1]]
                node_group = node.node_tree
                vb.formula_anim_nodes[formula_obj["math_anim_obj"]][anim_type]['transform_anim'].remove(node)
                p_socket = node.inputs['Instances'].links[0].from_socket
                n_socket = node.outputs['Instances'].links[0].to_socket
                del_curve_preset(curve_anim_setting, node.node_tree.nodes['Rotate Anim Curve'])
                del_curve_preset(curve_anim_setting, node.node_tree.nodes['Offset Anim Curve'])
                del_curve_preset(curve_anim_setting, node.node_tree.nodes['Scale Anim Curve'])
                node_tree.nodes.remove(node)
                node_tree.links.new(p_socket, n_socket)
                # remove the unused nodegroup
                bpy.data.node_groups.remove(node_group)
                key_name = [self.node_name]
                animsetting_status_reset(context, key_name)
                return {'FINISHED'}
            else:
                return {'CANCELLED'}
        elif self.anim_type.split('.')[1] == 'writing_anim':
            anim_type = self.anim_type.split('.')[0]
            formula_props = context.scene.math_anim_formula_props
            if context.object and (context.object.get("math_anim_obj") is not None):
                formula_obj = context.object
                node_tree = bpy.data.node_groups[self.node_name.split('**')[0]]
                node = node_tree.nodes[self.node_name.split('**')[1]]
                node_group = node.node_tree
                vb.formula_anim_nodes[formula_obj["math_anim_obj"]][anim_type]['writing_anim'].remove(node)
                p_socket = node.inputs['Curve'].links[0].from_socket
                n_socket = node.outputs['Curve'].links[0].to_socket
                del_curve_preset(curve_anim_setting, node.node_tree.nodes['Float Curve'])
                node_tree.nodes.remove(node)
                node_tree.links.new(p_socket, n_socket)
                # remove the unused nodegroup
                bpy.data.node_groups.remove(node_group)
                key_name = [self.node_name]
                animsetting_status_reset(context, key_name)
                return {'FINISHED'}
            else:
                return {'CANCELLED'}
        elif self.anim_type.split('.')[1] == 'color_flow':
            anim_type = self.anim_type.split('.')[0]
            formula_props = context.scene.math_anim_formula_props
            if context.object and (context.object.get("math_anim_obj") is not None):
                formula_obj = context.object
                node_tree = bpy.data.node_groups[self.node_name.split('**')[0]]
                node = node_tree.nodes[self.node_name.split('**')[1]]
                node_group = node.node_tree
                vb.formula_anim_nodes[formula_obj["math_anim_obj"]][anim_type]['color_flow'].remove(node)
                p1_socket = node.inputs['Grease Pencil'].links[0].from_socket
                p2_socket = node.inputs['Mesh'].links[0].from_socket
                n1_socket = node.outputs['Grease Pencil'].links[0].to_socket
                n2_socket = node.outputs['Mesh'].links[0].to_socket
                del_curve_preset(curve_anim_setting, node.node_tree.nodes['Float Curve'])
                del_curve_preset(curve_anim_setting, node.node_tree.nodes['Mesh Float Curve'])
                node_tree.nodes.remove(node)
                node_tree.links.new(p1_socket, n1_socket)
                node_tree.links.new(p2_socket, n2_socket)
                # remove the unused nodegroup
                bpy.data.node_groups.remove(node_group)
                key_name = [self.node_name]
                animsetting_status_reset(context, key_name)
                return {'FINISHED'}
            else:
                return {'CANCELLED'}
        elif self.anim_type.split('.')[1] == 'wave_anim':
            anim_type = self.anim_type.split('.')[0]
            formula_props = context.scene.math_anim_formula_props
            if context.object and (context.object.get("math_anim_obj") is not None):
                formula_obj = context.object
                inode_tree = bpy.data.node_groups[self.node_name.split('**')[0]]
                inode = inode_tree.nodes[self.node_name.split('**')[1]]
                inode_group = inode.node_tree
                cnode_tree = bpy.data.node_groups[self.node_name.split('**')[2]]
                cnode = cnode_tree.nodes[self.node_name.split('**')[3]]
                cnode_group = cnode.node_tree
                vb.formula_anim_nodes[formula_obj["math_anim_obj"]][anim_type]['wave_anim'].remove((inode,cnode))
                p_socket = inode.inputs['Geometry'].links[0].from_socket
                n_socket = inode.outputs['Geometry'].links[0].to_socket
                del_curve_preset(curve_anim_setting, inode.node_tree.nodes['Float Curve'])
                inode_tree.nodes.remove(inode)
                inode_tree.links.new(p_socket, n_socket)
                # remove the unused nodegroup
                bpy.data.node_groups.remove(inode_group)
                p_socket = cnode.inputs['Geometry'].links[0].from_socket
                n_socket = cnode.outputs['Geometry'].links[0].to_socket
                del_curve_preset(curve_anim_setting, cnode.node_tree.nodes['Float Curve'])
                cnode_tree.nodes.remove(cnode)
                cnode_tree.links.new(p_socket, n_socket)
                # remove the unused nodegroup
                bpy.data.node_groups.remove(cnode_group)
                key1 = f"{self.node_name.split('**')[0]}**{self.node_name.split('**')[1]}"
                key2 = f"{self.node_name.split('**')[2]}**{self.node_name.split('**')[3]}"
                key_name = [key1, key2]
                animsetting_status_reset(context, key_name)
                return {'FINISHED'}
            else:
                return {'CANCELLED'}

        elif self.anim_type.split('.')[1] == 'flow_anim':
            anim_type = self.anim_type.split('.')[0]
            formula_props = context.scene.math_anim_formula_props
            if context.object and (context.object.get("math_anim_obj") is not None):
                formula_obj = context.object
                node_tree = bpy.data.node_groups[self.node_name.split('**')[0]]
                node = node_tree.nodes[self.node_name.split('**')[1]]
                node_group = node.node_tree
                vb.formula_anim_nodes[formula_obj["math_anim_obj"]][anim_type]['flow_anim'].remove(node)
                del_curve_preset(curve_anim_setting, node.node_tree.nodes['Float Curve'])
                node_tree.nodes.remove(node)
                # remove the unused nodegroup
                bpy.data.node_groups.remove(node_group)
                key_name = [self.node_name]
                animsetting_status_reset(context, key_name)
                return {'FINISHED'}
            else:
                return {'CANCELLED'}

        elif self.anim_type.split('.')[1] == 'transform':
            anim_type = self.anim_type.split('.')[0]
            node_tree = bpy.data.node_groups[self.node_name.split('**')[0]]
            node = node_tree.nodes[self.node_name.split('**')[1]]
            vb.formula_anim_nodes[context.object["math_anim_obj"]][anim_type]['transform'].remove(node)
            key_name = [self.node_name]
            animsetting_status_reset(context, key_name)
            for socket in node.inputs[2:]:
                data_path = f"{socket.path_from_id()}.default_value"
                # clear keyframes
                if node_tree.animation_data and node_tree.animation_data.action:
                    action = node_tree.animation_data.action
                    slot = node_tree.animation_data.action_slot
                    strip = action.layers[0].strips[0]
                    channelbag = strip.channelbag(slot)
                    fcurves = channelbag.fcurves
                    mark_remove = []
                    for fcurve in fcurves:
                        if fcurve.data_path == data_path:
                            mark_remove.append(fcurve)
                    for fcurve in mark_remove:
                        fcurves.remove(fcurve)
                # reset values
                if socket.name == 'Scale':
                    socket.default_value = (1.0, 1.0, 1.0)
                elif socket.name == 'Local Space':
                    socket.default_value = True
                else:
                    socket.default_value = (0.0, 0.0, 0.0)
            return {'FINISHED'}

        return {'FINISHED'}

class MATH_OT_AddFormulaAnim(bpy.types.Operator):
    bl_idname = "math_anim.add_formula_anim"
    bl_label = "Add Formula Animations"
    bl_description = "Add An Animation"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        formula_props = context.scene.math_anim_formula_props
        if context.object and (context.object.get("math_anim_obj") is not None):
            formula_obj = context.object
            if formula_props.anim_style == 'GROW':
                anim_groups = ['Grow Anim']
                for group_name in anim_groups:
                    if bpy.data.node_groups.get(group_name) is None:
                        import_anim_nodegroups([group_name])
                    bpy.data.node_groups[group_name].use_fake_user = True
                keys = ['text_anim', 'stroke_anim', 'fill_anim']
                for key in keys:
                    if 'grow_anim' not in vb.formula_anim_nodes[formula_obj["math_anim_obj"]][key]:
                        vb.formula_anim_nodes[formula_obj["math_anim_obj"]][key]['grow_anim'] = []
            elif formula_props.anim_style == 'WRITING':
                anim_groups = ['Writing Curve Anim']
                for group_name in anim_groups:
                    if bpy.data.node_groups.get(group_name) is None:
                        import_anim_nodegroups([group_name])
                    bpy.data.node_groups[group_name].use_fake_user = True
                keys = ['text_anim', 'stroke_anim', 'fill_anim']
                for key in keys:
                    if 'writing_anim' not in vb.formula_anim_nodes[formula_obj["math_anim_obj"]][key]:
                        vb.formula_anim_nodes[formula_obj["math_anim_obj"]][key]['writing_anim'] = []
            elif formula_props.anim_style == 'COLOR_FLOW':
                anim_groups = ['Color Flow Anim']
                for group_name in anim_groups:
                    if bpy.data.node_groups.get(group_name) is None:
                        import_anim_nodegroups([group_name])
                    bpy.data.node_groups[group_name].use_fake_user = True
                keys = ['text_anim', 'stroke_anim', 'fill_anim']
                for key in keys:
                    if 'color_flow' not in vb.formula_anim_nodes[formula_obj["math_anim_obj"]][key]:
                        vb.formula_anim_nodes[formula_obj["math_anim_obj"]][key]['color_flow'] = []
            elif formula_props.anim_style == 'WAVE':
                anim_groups = ['Wave Anim']
                for group_name in anim_groups:
                    if bpy.data.node_groups.get(group_name) is None:
                        import_anim_nodegroups([group_name])
                    bpy.data.node_groups[group_name].use_fake_user = True
                keys = ['text_anim', 'stroke_anim', 'fill_anim']
                for key in keys:
                    if 'wave_anim' not in vb.formula_anim_nodes[formula_obj["math_anim_obj"]][key]:
                        vb.formula_anim_nodes[formula_obj["math_anim_obj"]][key]['wave_anim'] = []
            elif formula_props.anim_style == 'FLOW':
                anim_groups = ['Edge Flow Anim']
                for group_name in anim_groups:
                    if bpy.data.node_groups.get(group_name) is None:
                        import_anim_nodegroups([group_name])
                    bpy.data.node_groups[group_name].use_fake_user = True
                keys = ['text_anim', 'stroke_anim', 'fill_anim']
                for key in keys:
                    if 'flow_anim' not in vb.formula_anim_nodes[formula_obj["math_anim_obj"]][key]:
                        vb.formula_anim_nodes[formula_obj["math_anim_obj"]][key]['flow_anim'] = []
            elif formula_props.anim_style == 'TRANSFORM_ANIM':
                anim_groups = ['Transform Anim']
                for group_name in anim_groups:
                    if bpy.data.node_groups.get(group_name) is None:
                        import_anim_nodegroups([group_name])
                    bpy.data.node_groups[group_name].use_fake_user = True
                keys = ['text_anim', 'stroke_anim', 'fill_anim']
                for key in keys:
                    if 'transform_anim' not in vb.formula_anim_nodes[formula_obj["math_anim_obj"]][key]:
                        vb.formula_anim_nodes[formula_obj["math_anim_obj"]][key]['transform_anim'] = []
            elif formula_props.anim_style == 'TRANSFORM':
                keys = ['text_anim', 'stroke_anim', 'fill_anim']
                for key in keys:
                    if 'transform' not in vb.formula_anim_nodes[formula_obj["math_anim_obj"]][key]:
                        vb.formula_anim_nodes[formula_obj["math_anim_obj"]][key]['transform'] = []
            return self.execute(context)
        else:
            self.report({'WARNING'}, 'Select a formula object first!')
            return {"CANCELLED"}

    def execute(self, context):
        formula_props = context.scene.math_anim_formula_props
        anim_setting_status = context.scene.math_animSetting_status
        curve_anim_setting = context.scene.math_anim_curve_gen_settings
        if context.object and (context.object.get("math_anim_obj") is not None):
            formula_obj = context.object
            suffix = formula_obj["math_anim_obj"][formula_obj["math_anim_obj"].find('Global'):]
            if formula_props.anim_style == 'GROW':
                max_len = {'text_len':0, 'stroke_len':0, 'fill_len':0}
                for page_num in range(len(vb.formula_node_trees[formula_obj["math_anim_obj"]])):
                    nodes = vb.formula_node_trees[formula_obj["math_anim_obj"]][page_num]
                    if max_len['text_len'] < len(nodes['text_nodes'])-1:
                        max_len['text_len'] = len(nodes['text_nodes'])-1
                    if max_len['stroke_len'] < len(nodes['stroke_nodes'])-1:
                        max_len['stroke_len'] = len(nodes['stroke_nodes'])-1
                    if max_len['fill_len'] < len(nodes['fill_nodes'])-1:
                        max_len['fill_len'] = len(nodes['fill_nodes'])-1
                setups = [
                        ('text_anim', formula_props.anim_text, bpy.data.node_groups[f"char_instance_anim.{suffix}"], max_len['text_len']),
                        ('stroke_anim', formula_props.anim_stroke, bpy.data.node_groups[f"stroke_instance_anim.{suffix}"], max_len['stroke_len']),
                        ('fill_anim', formula_props.anim_fill, bpy.data.node_groups[f"fill_instance_anim.{suffix}"], max_len['fill_len'])]
                for anim_type, use, instance_animgroup, length in setups:
                    if use and length>0:
                        grow_nodegroup = bpy.data.node_groups['Grow Anim'].copy()
                        grow_node,_,_ = create_node(instance_animgroup, "GeometryNodeGroup", 0, 0)
                        grow_node.name = grow_nodegroup.name
                        n_socket = instance_animgroup.nodes['Group Output'].inputs['Geometry']
                        p_socket = n_socket.links[0].from_socket
                        grow_node.node_tree = grow_nodegroup
                        grow_node.inputs['Range Start'].default_value = context.scene.frame_start
                        grow_node.inputs['Range End'].default_value = context.scene.frame_end
                        arrange_nodes(p_socket.node, grow_node, 'r', 50, 0)
                        arrange_nodes(grow_node, n_socket.node, 'r', 50, 0)
                        instance_animgroup.links.new(p_socket, grow_node.inputs['Geometry'])
                        instance_animgroup.links.new(grow_node.outputs['Geometry'], n_socket)
                        item = anim_setting_status.add()
                        key_name = f"{instance_animgroup.name}**{grow_node.name}"
                        item.name = key_name
                        vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
                        vb.formula_anim_nodes[formula_obj["math_anim_obj"]][anim_type]['grow_anim'].append(grow_node)
                        add_curve_preset(curve_anim_setting, grow_node.node_tree.nodes['Float Curve'])
            elif formula_props.anim_style == 'WRITING':
                max_len = {'text_len':0, 'stroke_len':0, 'fill_len':0}
                for page_num in range(len(vb.formula_node_trees[formula_obj["math_anim_obj"]])):
                    nodes = vb.formula_node_trees[formula_obj["math_anim_obj"]][page_num]
                    if max_len['text_len'] < len(nodes['text_nodes'])-1:
                        max_len['text_len'] = len(nodes['text_nodes'])-1
                    if max_len['stroke_len'] < len(nodes['stroke_nodes'])-1:
                        max_len['stroke_len'] = len(nodes['stroke_nodes'])-1
                    if max_len['fill_len'] < len(nodes['fill_nodes'])-1:
                        max_len['fill_len'] = len(nodes['fill_nodes'])-1
                setups = [
                        ('text_anim', formula_props.anim_text, bpy.data.node_groups[f"char_curve_anim.{suffix}"], max_len['text_len']),
                        ('stroke_anim', formula_props.anim_stroke, bpy.data.node_groups[f"stroke_curve_anim.{suffix}"], max_len['stroke_len']),
                        ('fill_anim', formula_props.anim_fill, bpy.data.node_groups[f"fill_curve_anim.{suffix}"], max_len['fill_len'])]
                for anim_type, use, curve_animgroup, length in setups:
                    if use and length>0:
                        anim_nodegroup = bpy.data.node_groups['Writing Curve Anim'].copy()
                        anim_node,_,_ = create_node(curve_animgroup, "GeometryNodeGroup", 0, 0)
                        anim_node.name = anim_nodegroup.name
                        n_socket = curve_animgroup.nodes['Join Geometry'].inputs['Geometry']
                        p_socket = n_socket.links[0].from_socket
                        curve_animgroup.links.remove(n_socket.links[0])
                        idx_socket = curve_animgroup.nodes['Group Input'].outputs['Index']
                        anim_node.node_tree = anim_nodegroup
                        anim_node.inputs['Total Index'].default_value = length
                        anim_node.inputs['Range Start'].default_value = context.scene.frame_start
                        anim_node.inputs['Range End'].default_value = context.scene.frame_end
                        curve_animgroup.links.new(p_socket, anim_node.inputs['Curve'])
                        curve_animgroup.links.new(anim_node.outputs['Curve'], n_socket)
                        curve_animgroup.links.new(idx_socket, anim_node.inputs['Current Index'])
                        while n_socket.links[0].from_node.name != 'Group Input':
                            arrange_nodes(n_socket.node, n_socket.links[0].from_node, 'l', 50, 0)
                            n_socket = n_socket.links[0].from_node.inputs[0]
                        arrange_nodes(n_socket.node, n_socket.links[0].from_node, 'l', 50, 0)
                        item = anim_setting_status.add()
                        key_name = f"{curve_animgroup.name}**{anim_node.name}"
                        item.name = key_name
                        vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
                        vb.formula_anim_nodes[formula_obj["math_anim_obj"]][anim_type]['writing_anim'].append(anim_node)
                        add_curve_preset(curve_anim_setting, anim_node.node_tree.nodes['Float Curve'])
            elif formula_props.anim_style == 'COLOR_FLOW':
                max_len = {'text_len':0, 'stroke_len':0, 'fill_len':0}
                for page_num in range(len(vb.formula_node_trees[formula_obj["math_anim_obj"]])):
                    nodes = vb.formula_node_trees[formula_obj["math_anim_obj"]][page_num]
                    if max_len['text_len'] < len(nodes['text_nodes'])-1:
                        max_len['text_len'] = len(nodes['text_nodes'])-1
                    if max_len['stroke_len'] < len(nodes['stroke_nodes'])-1:
                        max_len['stroke_len'] = len(nodes['stroke_nodes'])-1
                    if max_len['fill_len'] < len(nodes['fill_nodes'])-1:
                        max_len['fill_len'] = len(nodes['fill_nodes'])-1
                setups = [
                        ('text_anim', formula_props.anim_text, bpy.data.node_groups[f'char_mesh_anim.{suffix}'], max_len['text_len']),
                        ('stroke_anim', formula_props.anim_stroke, bpy.data.node_groups[f'stroke_mesh_anim.{suffix}'], max_len['stroke_len']),
                        ('fill_anim', formula_props.anim_fill, bpy.data.node_groups[f'fill_mesh_anim.{suffix}'], max_len['fill_len'])]
                for anim_type, use, mesh_animgroup, length in setups:
                    if use and length>0:
                        anim_nodegroup = bpy.data.node_groups['Color Flow Anim'].copy()
                        anim_node,_,_ = create_node(mesh_animgroup, "GeometryNodeGroup", 0, 0)
                        anim_node.node_tree = anim_nodegroup
                        anim_node.name = anim_nodegroup.name
                        n1_socket = mesh_animgroup.nodes['Group Output'].inputs['Grease Pencil']
                        n2_socket = mesh_animgroup.nodes['Group Output'].inputs['Mesh']
                        p1_socket = n1_socket.links[0].from_socket
                        p2_socket = n2_socket.links[0].from_socket
                        mesh_animgroup.links.new(p1_socket, anim_node.inputs['Grease Pencil'])
                        mesh_animgroup.links.new(anim_node.outputs['Grease Pencil'], n1_socket)
                        mesh_animgroup.links.new(p2_socket, anim_node.inputs['Mesh'])
                        mesh_animgroup.links.new(anim_node.outputs['Mesh'], n2_socket)
                        mesh_animgroup.links.new(mesh_animgroup.nodes['Group Input'].outputs['Total Index'], anim_node.inputs['Total Index'])
                        mesh_animgroup.links.new(mesh_animgroup.nodes['Group Input'].outputs['Current Index'], anim_node.inputs['Current Index'])
                        while p2_socket.links[0].to_node.name != 'Group Output':
                            arrange_nodes(p2_socket.node, p2_socket.links[0].to_node, 'r', 50, 0)
                            p2_socket = p2_socket.links[0].to_node.outputs[0]
                        item = anim_setting_status.add()
                        key_name = f"{mesh_animgroup.name}**{anim_node.name}"
                        item.name = key_name
                        vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
                        vb.formula_anim_nodes[formula_obj["math_anim_obj"]][anim_type]['color_flow'].append(anim_node)
                        add_curve_preset(curve_anim_setting, anim_node.node_tree.nodes['Float Curve'])
                        add_curve_preset(curve_anim_setting, anim_node.node_tree.nodes['Mesh Float Curve'])
            elif formula_props.anim_style == 'WAVE':
                max_len = {'text_len':0, 'stroke_len':0, 'fill_len':0}
                for page_num in range(len(vb.formula_node_trees[formula_obj["math_anim_obj"]])):
                    nodes = vb.formula_node_trees[formula_obj["math_anim_obj"]][page_num]
                    if max_len['text_len'] < len(nodes['text_nodes'])-1:
                        max_len['text_len'] = len(nodes['text_nodes'])-1
                    if max_len['stroke_len'] < len(nodes['stroke_nodes'])-1:
                        max_len['stroke_len'] = len(nodes['stroke_nodes'])-1
                    if max_len['fill_len'] < len(nodes['fill_nodes'])-1:
                        max_len['fill_len'] = len(nodes['fill_nodes'])-1
                setups = [
                        ('text_anim', formula_props.anim_text, bpy.data.node_groups[f"char_instance_anim.{suffix}"], bpy.data.node_groups[f"char_curve_anim.{suffix}"], max_len['text_len']),
                        ('stroke_anim', formula_props.anim_stroke, bpy.data.node_groups[f"stroke_instance_anim.{suffix}"], bpy.data.node_groups[f"stroke_curve_anim.{suffix}"], max_len['stroke_len']),
                        ('fill_anim', formula_props.anim_fill, bpy.data.node_groups[f"fill_instance_anim.{suffix}"], bpy.data.node_groups[f"fill_curve_anim.{suffix}"], max_len['fill_len'])]
                for anim_type, use, instance_animgroup, curve_animgroup, length in setups:
                    if use and length>0:
                        anim_nodegroup = bpy.data.node_groups['Wave Anim'].copy()
                        # inside Instance Anim group
                        anim_node,_,_ = create_node(instance_animgroup, "GeometryNodeGroup", 0, 0)
                        anim_node.name = anim_nodegroup.name
                        n_socket = instance_animgroup.nodes['Group Output'].inputs['Geometry']
                        p_socket = n_socket.links[0].from_socket
                        anim_node.node_tree = anim_nodegroup
                        anim_node.inputs['Range Start'].default_value = context.scene.frame_start
                        anim_node.inputs['Range End'].default_value = context.scene.frame_end
                        arrange_nodes(p_socket.node, anim_node, 'r', 50, 0)
                        arrange_nodes(anim_node, n_socket.node, 'r', 50, 0)
                        instance_animgroup.links.new(p_socket, anim_node.inputs['Geometry'])
                        instance_animgroup.links.new(anim_node.outputs['Geometry'], n_socket)
                        item = anim_setting_status.add()
                        key_name = f"{instance_animgroup.name}**{anim_node.name}"
                        item.name = key_name
                        vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1

                        anim_nodegroup = bpy.data.node_groups['Wave Anim'].copy()
                        # inside Curve Anim group
                        anim_node2,_,_ = create_node(curve_animgroup, "GeometryNodeGroup", 0, 0)
                        anim_node2.name = anim_nodegroup.name
                        n_socket = curve_animgroup.nodes['Join Geometry'].inputs['Geometry']
                        p_socket = n_socket.links[0].from_socket
                        curve_animgroup.links.remove(n_socket.links[0])
                        anim_node2.node_tree = anim_nodegroup
                        anim_node2.inputs['Range Start'].default_value = context.scene.frame_start
                        anim_node2.inputs['Range End'].default_value = context.scene.frame_end
                        curve_animgroup.links.new(p_socket, anim_node2.inputs['Geometry'])
                        curve_animgroup.links.new(anim_node2.outputs['Geometry'], n_socket)
                        while n_socket.links[0].from_node.name != 'Group Input':
                            arrange_nodes(n_socket.node, n_socket.links[0].from_node, 'l', 50, 0)
                            n_socket = n_socket.links[0].from_node.inputs[0]
                        arrange_nodes(n_socket.node, n_socket.links[0].from_node, 'l', 50, 0)
                        anim_node2.inputs['Passthrough'].default_value = True
                        item = anim_setting_status.add()
                        key_name = f"{curve_animgroup.name}**{anim_node2.name}"
                        item.name = key_name
                        vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
                        vb.formula_anim_nodes[formula_obj["math_anim_obj"]][anim_type]['wave_anim'].append((anim_node, anim_node2))
                        add_curve_preset(curve_anim_setting, anim_node.node_tree.nodes['Float Curve'])
                        add_curve_preset(curve_anim_setting, anim_node2.node_tree.nodes['Float Curve'])
            elif formula_props.anim_style == 'FLOW':
                max_len = {'text_len':0, 'stroke_len':0, 'fill_len':0}
                for page_num in range(len(vb.formula_node_trees[formula_obj["math_anim_obj"]])):
                    nodes = vb.formula_node_trees[formula_obj["math_anim_obj"]][page_num]
                    if max_len['text_len'] < len(nodes['text_nodes'])-1:
                        max_len['text_len'] = len(nodes['text_nodes'])-1
                    if max_len['stroke_len'] < len(nodes['stroke_nodes'])-1:
                        max_len['stroke_len'] = len(nodes['stroke_nodes'])-1
                    if max_len['fill_len'] < len(nodes['fill_nodes'])-1:
                        max_len['fill_len'] = len(nodes['fill_nodes'])-1
                setups = [
                        ('text_anim', formula_props.anim_text, bpy.data.node_groups[f"char_curve_anim.{suffix}"], max_len['text_len']),
                        ('stroke_anim', formula_props.anim_stroke, bpy.data.node_groups[f"stroke_curve_anim.{suffix}"], max_len['stroke_len']),
                        ('fill_anim', formula_props.anim_fill, bpy.data.node_groups[f"fill_curve_anim.{suffix}"], max_len['fill_len'])]
                n_loop = True
                for anim_type, use, curve_animgroup, length in setups:
                    if use and length>0:
                        if not n_loop:
                            break
                        anim_nodegroup = bpy.data.node_groups['Edge Flow Anim'].copy()
                        anim_node,_,_ = create_node(curve_animgroup, "GeometryNodeGroup", 0, 0)
                        anim_node.name = anim_nodegroup.name
                        anim_node.node_tree = anim_nodegroup
                        n_socket = curve_animgroup.nodes['Join Flow'].inputs['Geometry']
                        p_socket = curve_animgroup.nodes['Join Geometry'].outputs['Geometry']
                        anim_node.location.x = p_socket.node.location.x + 190
                        anim_node.location.y = p_socket.node.location.y + (len(n_socket.links)-1)*500
                        curve_animgroup.links.new(p_socket, anim_node.inputs['Geometry'])
                        curve_animgroup.links.new(anim_node.outputs['Geometry'], n_socket)
                        item = anim_setting_status.add()
                        key_name = f"{curve_animgroup.name}**{anim_node.name}"
                        item.name = key_name
                        vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
                        vb.formula_anim_nodes[formula_obj["math_anim_obj"]][anim_type]['flow_anim'].append(anim_node)
                        add_curve_preset(curve_anim_setting, anim_node.node_tree.nodes['Float Curve'])
                        n_loop = False
            elif formula_props.anim_style == 'TRANSFORM_ANIM':
                max_len = {'text_len':0, 'stroke_len':0, 'fill_len':0}
                for page_num in range(len(vb.formula_node_trees[formula_obj["math_anim_obj"]])):
                    nodes = vb.formula_node_trees[formula_obj["math_anim_obj"]][page_num]
                    if max_len['text_len'] < len(nodes['text_nodes'])-1:
                        max_len['text_len'] = len(nodes['text_nodes'])-1
                    if max_len['stroke_len'] < len(nodes['stroke_nodes'])-1:
                        max_len['stroke_len'] = len(nodes['stroke_nodes'])-1
                    if max_len['fill_len'] < len(nodes['fill_nodes'])-1:
                        max_len['fill_len'] = len(nodes['fill_nodes'])-1
                setups = [
                        ('text_anim', formula_props.anim_text, bpy.data.node_groups[f"char_instance_anim.{suffix}"], max_len['text_len']),
                        ('stroke_anim', formula_props.anim_stroke, bpy.data.node_groups[f"stroke_instance_anim.{suffix}"], max_len['stroke_len']),
                        ('fill_anim', formula_props.anim_fill, bpy.data.node_groups[f"fill_instance_anim.{suffix}"], max_len['fill_len'])]
                for anim_type, use, instance_animgroup, length in setups:
                    if use and length>0:
                        trans_anim_nodegroup = bpy.data.node_groups['Transform Anim'].copy()
                        trans_anim_node,_,_ = create_node(instance_animgroup, "GeometryNodeGroup", 0, 0)
                        trans_anim_node.name = trans_anim_nodegroup.name
                        n_socket = instance_animgroup.nodes['Group Output'].inputs['Geometry']
                        p_socket = n_socket.links[0].from_socket
                        trans_anim_node.node_tree = trans_anim_nodegroup
                        trans_anim_node.inputs['Range Start'].default_value = context.scene.frame_start
                        trans_anim_node.inputs['Range End'].default_value = context.scene.frame_end
                        arrange_nodes(p_socket.node, trans_anim_node, 'r', 50, 0)
                        arrange_nodes(trans_anim_node, n_socket.node, 'r', 50, 0)
                        instance_animgroup.links.new(p_socket, trans_anim_node.inputs['Instances'])
                        instance_animgroup.links.new(trans_anim_node.outputs['Instances'], n_socket)
                        instance_animgroup.links.new(instance_animgroup.nodes['Group Input'].outputs['Index'], trans_anim_node.inputs['Index'])
                        item = anim_setting_status.add()
                        key_name = f"{instance_animgroup.name}**{trans_anim_node.name}"
                        item.name = key_name
                        vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
                        vb.formula_anim_nodes[formula_obj["math_anim_obj"]][anim_type]['transform_anim'].append(trans_anim_node)
                        add_curve_preset(curve_anim_setting, trans_anim_node.node_tree.nodes['Rotate Anim Curve'])
                        add_curve_preset(curve_anim_setting, trans_anim_node.node_tree.nodes['Offset Anim Curve'])
                        add_curve_preset(curve_anim_setting, trans_anim_node.node_tree.nodes['Scale Anim Curve'])
            elif formula_props.anim_style == 'TRANSFORM':
                max_len = {'text_len':0, 'stroke_len':0, 'fill_len':0}
                for page_num in range(len(vb.formula_node_trees[formula_obj["math_anim_obj"]])):
                    nodes = vb.formula_node_trees[formula_obj["math_anim_obj"]][page_num]
                    if max_len['text_len'] < len(nodes['text_nodes'])-1:
                        max_len['text_len'] = len(nodes['text_nodes'])-1
                    if max_len['stroke_len'] < len(nodes['stroke_nodes'])-1:
                        max_len['stroke_len'] = len(nodes['stroke_nodes'])-1
                    if max_len['fill_len'] < len(nodes['fill_nodes'])-1:
                        max_len['fill_len'] = len(nodes['fill_nodes'])-1
                setups = [
                        ('text_anim', formula_props.anim_text, bpy.data.node_groups[f"char_instance_anim.{suffix}"], max_len['text_len']),
                        ('stroke_anim', formula_props.anim_stroke, bpy.data.node_groups[f"stroke_instance_anim.{suffix}"], max_len['stroke_len']),
                        ('fill_anim', formula_props.anim_fill, bpy.data.node_groups[f"fill_instance_anim.{suffix}"], max_len['fill_len'])]
                for anim_type, use, node_group, length in setups:
                    if use and length>0:
                        rotate_node = node_group.nodes['Rotate Instances']
                        trans_node = node_group.nodes['Translate Instances']
                        scale_node = node_group.nodes['Scale Instances']
                        nodes = [rotate_node, trans_node, scale_node]
                        vb.formula_anim_nodes[formula_obj["math_anim_obj"]][anim_type]['transform'] = nodes
                        for node in nodes:
                            key_name = f"{node_group.name}**{node.name}"
                            if key_name not in vb.formula_animsetting_status:
                                item = anim_setting_status.add()
                                item.name = key_name
                                vb.formula_animsetting_status[key_name] = len(anim_setting_status)-1
        else:
            self.report({"WARNING"}, "No formula object selected, select one first!")
            return {'CANCELLED'}

        return {'FINISHED'}

class MATH_OT_FormulaMorphAnim(bpy.types.Operator):
    bl_idname = "math_anim.formula_morph_anim"
    bl_label = "Add Formula Morph Animations"
    bl_description = "Config Morph Animation between objects"
    bl_options = {'REGISTER', 'UNDO'}

    popup_window: bpy.props.BoolProperty(default=True)
    win_width: bpy.props.IntProperty(default=1200)
    col_width: bpy.props.IntProperty(default=60)
    width_control: bpy.props.StringProperty(default="col_width")
    morph_order: bpy.props.EnumProperty(
        name="Morph Order",
        items=[("Sequential", "Sequential", "Morph from source to targets in sequential"),
               ("Parallel", "Parallel", "Morph from source to multiple targets at the same") ]
    )

    # Add temporary storage property
    _active_morph_setting = {}
    _obj_holders = {} # obj.name: {obj_holder: [obj_holder, obj_holder, ...], obj_idx: idx}, idx in the morphsettings

    def invoke(self, context, event):
        # import the morph anim
        anim_groups = ['Curve Morph Anim', 'Select Layer']
        for group_name in anim_groups:
            if bpy.data.node_groups.get(group_name) is None:
                import_anim_nodegroups([group_name])
            bpy.data.node_groups[group_name].use_fake_user = True

        morph_targets = context.scene.math_anim_morph_targets
        morph_settings = context.scene.math_anim_morphSettings
        if 'morph_anim' not in vb.formula_anim_nodes:
            vb.formula_anim_nodes['morph_anim'] = []
        #morph_targets.clear()
        if len(morph_targets) == 0:
            target_item = morph_targets.add()
            target_item.collection_idx = 0
            target_item = morph_targets.add()
            target_item.collection_idx = 1
        else:
            # check and delete non exist objects
            for target_coll in morph_targets:
                target = target_coll.math_obj_targets
                if vb._enum_targets and target not in vb._enum_targets:
                    target = next(iter(vb._enum_targets))

        # prepare morph anim preset node_groups for parallel and sequentials
        for i in range(len(morph_targets)-1):
            anim_nodegroup = bpy.data.node_groups['Curve Morph Anim']
            # for parallel
            if i == 0 and bpy.data.node_groups.get("morph_anim_parallel_preset") is None:
                new_group = anim_nodegroup.copy()
                new_group.name = "morph_anim_parallel_preset"
                vb.formula_morph_presets[f'{i}'] = [new_group]
            if bpy.data.node_groups.get(f"morph_anim_sequential_preset{i}") is None:
                new_group = anim_nodegroup.copy()
                new_group.name = f"morph_anim_sequential_preset{i}"
                if i == 0:
                    vb.formula_morph_presets[f'{i}'].append(new_group)
                else:
                    new_group.interface.items_tree['Start Frame'].default_value = 1 + i*24
                    vb.formula_morph_presets[f'{i}'] = new_group

        ncol = 0
        # remove corresponding if the object is deleted
        orphan_idx = [i for i in range(len(morph_settings))]
        for obj in bpy.data.objects:
            if obj.get("math_anim_obj") is not None:
                ncol += 1
                for i in range(len(morph_settings)):
                    if morph_settings[i].name == obj["math_anim_obj"]:
                        orphan_idx.remove(i)
        for i in range(len(orphan_idx)):
            morph_settings.remove(orphan_idx[i])

        bpy.ops.math_anim.update_morph_objects()
        if ncol > 0 and self.popup_window:
            wm = context.window_manager
            #return wm.invoke_props_dialog(self, width=self.win_width if self.width_control == 'win_width' else self.col_width*ncol)
            return wm.invoke_props_dialog(self, width=self.win_width)
        if ncol == 0:
            self.report({"INFO"},"No available text or drawing or plots for morph animation.")
            return {'CANCELLED'}
        return self.execute(context)

    def execute(self, context):
        # Access the stored morph_setting
        if self.__class__._active_morph_setting: # with __class__, the variable will be shared by all instances of the class
            active_morph_settings = self.__class__._active_morph_setting['morph_setting']
            sel_lens = self.__class__._active_morph_setting['sel_len']
            # for the morph nodes
            morph_node_chain = {} # key: [nodes chain], each chain is a list
            # Do your modifications to morph_setting here
            for i in range(len(sel_lens)):
                active_morph_setting = active_morph_settings[i]
                sel_len = sel_lens[i]
                morph_level = {}
                for page_num in range(len(active_morph_setting)):
                    morph_setting = active_morph_setting[page_num]
                    for item_idx in range(len(morph_setting)):
                        morph = morph_setting[item_idx]
                        if morph.selected and not morph.morph:
                            node = ''
                            keep = False
                            if morph.type == 'char':
                                node = vb.formula_node_trees[morph.obj_id][page_num]['text_nodes'][morph.inputs]
                                keep = morph.keep
                            elif morph.type == 'stroke':
                                node = vb.formula_node_trees[morph.obj_id][page_num]['stroke_nodes'][morph.inputs]
                                keep = morph.keep
                            elif morph.type == 'fill':
                                node = vb.formula_node_trees[morph.obj_id][page_num]['fill_nodes'][morph.inputs]
                                keep = morph.keep
                            elif morph.type == 'input' and morph.morph_idx in morph_node_chain:
                                    # use previous node to create a new node
                                    previous_node = ''
                                    if self.morph_order == "Parallel":
                                        previous_node = morph_node_chain[morph.morph_idx][-1][0]
                                    else:
                                        if i==1:
                                            previous_node = morph_node_chain[morph.morph_idx][-1][0]
                                        else:
                                            if morph.morph_idx in morph_level:
                                                previous_node = morph_node_chain[morph.morph_idx][-1][len(morph_level[morph.morph_idx])][0]
                                            else:
                                                previous_node = morph_node_chain[morph.morph_idx][-1][0][0]
                                    parent_nodegroup = previous_node.id_data
                                    node = parent_nodegroup.nodes.new(type="GeometryNodeGroup")
                                    node.node_tree = previous_node.node_tree.copy()
                                    keep = morph.keep
                                    node.node_tree.nodes['String to Curves'].inputs['String'].default_value = morph.inputs
                            elif morph.type == 'layer':
                                node = vb.gpencil_layer_nodes[morph.obj_id][morph.inputs]
                                keep = morph.keep

                            if morph.morph_idx in morph_level:
                                morph_level[morph.morph_idx].append((node, keep, morph))
                            else:
                                morph_level[morph.morph_idx] = [(node, keep, morph)]
                            morph.morph = True
                            morph.draw_tag = False
                        morph.morph_last_idx = morph.morph_last_idx + sel_len # only the source is correct
                for key, item in morph_level.items():
                    if i == 0:
                        morph_node_chain[key] = item
                    else:
                        if key not in morph_node_chain:
                            continue
                        if self.morph_order == "Parallel":
                            morph_node_chain[key].extend(item)
                        else:
                            morph_node_chain[key].append(item)
            # setup morphs
            anim_setting_status = context.scene.math_animSetting_status
            curve_anim_setting = context.scene.math_anim_curve_gen_settings
            if self.morph_order == "Parallel":
                for nodes in morph_node_chain.values():
                    if len(nodes) < 2:
                        source_morph = nodes[0][2]
                        source_morph.selected = False
                        source_morph.keep = False
                        source_morph.morph = False
                        source_morph.draw_tag = True
                        self.report({'INFO'}, f'No morph target for {nodes[0][2].inputs}.')
                        continue
                    morph_nodegroup = vb.formula_morph_presets['0'][0].copy()
                    source_node = nodes[0][0]
                    keep = nodes[0][1]
                    source_morph = nodes[0][2]
                    source_nodegroup = None
                    if source_morph.type == 'layer':
                        source_nodegroup = source_node.id_data
                    else:
                        source_nodegroup = source_node.node_tree
                    n_socket = source_nodegroup.nodes['Join Geometry'].inputs['Geometry']
                    remove_link = None
                    p_socket = None
                    if source_morph.type == 'layer':
                        p_socket = source_node.outputs['Geometry']
                        for link in p_socket.links:
                            if link.to_node.name == 'Join Geometry':
                                remove_link = link
                    else:
                        for link in n_socket.links:
                            if link.from_node.name == 'Curve Anim':
                                remove_link = link
                        p_socket = source_nodegroup.nodes['Curve Anim'].outputs['Geometry']
                    source_nodegroup.links.remove(remove_link)
                    if source_morph.type == 'layer':
                        p_socket = source_node.outputs['Curve']
                    node_x = p_socket.node.location.x + 190
                    node_y = p_socket.node.location.y - 50
                    morph_node, node_x, node_y = create_node(source_nodegroup, "GeometryNodeGroup", node_x, node_y, 50, 0)
                    morph_node.name = morph_nodegroup.name
                    morph_node.node_tree = morph_nodegroup
                    morph_node.inputs['Keep Source'].default_value = keep
                    for link in n_socket.links:
                        link.from_node.location.x += 190
                    n_node = n_socket.node
                    while n_node.name != 'Group Output':
                        n_node.location.x += 190
                        n_node = n_node.outputs[0].links[0].to_node
                    source_nodegroup.nodes['Group Output'].location.x += 190
                    source_nodegroup.links.new(morph_node.outputs['Origin'], n_socket)
                    source_nodegroup.links.new(p_socket, morph_node.inputs['Source'])
                    source_nodegroup.links.new(morph_node.outputs['Morph'], n_socket)
                    node_x = p_socket.node.location.x
                    node_y = p_socket.node.location.y - 256 - 20
                    join_node, node_x, node_y = create_node(source_nodegroup, "GeometryNodeJoinGeometry", node_x, node_y, -50, -50)
                    from_key = None
                    if source_morph.type == 'layer':
                        from_key = f'Layer {source_node.name}'
                    elif source_morph.type == 'char' or source_morph.type == 'input':
                        from_key = source_nodegroup.nodes['String to Curves'].inputs['String'].default_value
                    else:
                        from_key = source_nodegroup.name
                    to_key = []
                    mute_nodes = [source_node]
                    morph_items = [nodes[0][2]]
                    for node in nodes[1:]:
                        if not node[0]:
                            continue
                        if node[2].type == 'layer':
                            color_strength = node[0].inputs['Color Strength'].default_value
                            node[0].inputs['Color Strength'].default_value = 0.0
                        else:
                            node[0].mute = True
                            if node[0].inputs['Geometry'].is_linked:
                                ng = node[0].id_data
                                ng.links.remove(node[0].inputs['Geometry'].links[0])
                        mute_nodes.append(node[0])
                        morph_items.append(node[2])
                        target_node, node_x, node_y = create_node(source_nodegroup, "GeometryNodeGroup", node_x, node_y, 0, -10)
                        target_node.node_tree = node[0].node_tree
                        if node[2].type == 'layer':
                            target_node.label = target_node.inputs['Layer Name'].default_value
                            target_node.name = f'{node[0].node_tree.name}.Morph'
                            if node[2].obj_id == source_morph.obj_id:
                                groupIn_node,_,_ = create_node(source_nodegroup, "NodeGroupInput", target_node.location.x-190, target_node.location.y, 0, 0)
                                source_nodegroup.links.new(groupIn_node.outputs['Geometry'], target_node.inputs['Geometry'])
                            else:
                                target_node.node_tree = bpy.data.node_groups['Select Layer'].copy()
                                groupIn_node,_,_ = create_node(source_nodegroup, "GeometryNodeObjectInfo", target_node.location.x-190, target_node.location.y, 0, 0)
                                refer_obj = None
                                for obj in bpy.data.objects:
                                    if obj.get('math_anim_obj') and obj["math_anim_obj"] == node[2].obj_id:
                                        refer_obj = obj
                                groupIn_node.inputs['Object'].default_value = refer_obj
                                source_nodegroup.links.new(groupIn_node.outputs['Geometry'], target_node.inputs['Geometry'])
                            target_node.inputs['Layer Name'].default_value = node[2].inputs
                            target_node.inputs['Color Strength'].default_value = color_strength
                            source_nodegroup.links.new(target_node.outputs['Curve'], join_node.inputs['Geometry'])
                            to_key.append(f"Layer {target_node.inputs['Layer Name'].default_value}")
                        else:
                            source_nodegroup.links.new(target_node.outputs['Curve'], join_node.inputs['Geometry'])
                            if node[2].type == 'char' or node[2].type == 'input':
                                to_key.append(target_node.node_tree.nodes['String to Curves'].inputs['String'].default_value)
                            else:
                                to_key.append(target_node.node_tree.name)
                    source_nodegroup.links.new(join_node.outputs['Geometry'], morph_node.inputs['Target'])
                    key_name = f"{nodes[0][2].morph_idx}:  {from_key} -> {to_key}"
                    vb.formula_anim_nodes['morph_anim'].append({key_name: [(morph_node, mute_nodes, morph_items)]})
                    item = anim_setting_status.add()
                    item.name = key_name
                    vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
                    add_curve_preset(curve_anim_setting, morph_node.node_tree.nodes['Float Curve'])
            else:
                for nodes in morph_node_chain.values():
                    if len(nodes) < 2:
                        source_morph = nodes[0][2]
                        source_morph.selected = False
                        source_morph.keep = False
                        source_morph.morph = False
                        source_morph.draw_tag = True
                        self.report({'INFO'}, f'No morph target for {nodes[0][2].inputs}.')
                        continue
                    source_node = nodes[0][0]
                    keep = nodes[0][1]
                    source_morph = nodes[0][2]
                    source_nodegroup = None
                    if source_morph.type == 'layer':
                        source_nodegroup = source_node.id_data
                    else:
                        source_nodegroup = source_node.node_tree
                    n_socket = source_nodegroup.nodes['Join Geometry'].inputs['Geometry']
                    p_socket = None
                    remove_link = None
                    if source_morph.type == 'layer':
                        p_socket = source_node.outputs['Geometry']
                        for link in p_socket.links:
                            if link.to_node.name == 'Join Geometry':
                                remove_link = link
                                continue
                            link.to_node.location.x += 190*(len(nodes[1:]))
                    else:
                        p_socket = source_nodegroup.nodes['Curve Anim'].outputs['Geometry']
                        for link in n_socket.links:
                            if link.from_node.name == 'Curve Anim':
                                remove_link = link
                                continue
                            link.from_node.location.x += 190*(len(nodes[1:]))
                    n_node = n_socket.node
                    while n_node.name != 'Group Output':
                        n_node.location.x += 190*(len(nodes[1:]))
                        n_node = n_node.outputs[0].links[0].to_node
                    source_nodegroup.nodes['Group Output'].location.x += 190*(len(nodes[1:]))
                    idx = 0
                    link = None
                    from_key = None
                    if source_morph.type == 'layer':
                        p_socket = source_node.outputs['Curve']
                        from_key = f"Layer {source_node.inputs['Layer Name'].default_value}"
                    elif source_morph.type == 'char' or source_morph.type == 'input':
                        from_key = source_nodegroup.nodes['String to Curves'].inputs['String'].default_value
                    else:
                        from_key = source_nodegroup.name
                    morph_list = []
                    node_x = p_socket.node.location.x + 190
                    node_y = p_socket.node.location.y - 50
                    for targets in nodes[1:]:
                        source_nodegroup.links.remove(remove_link)
                        morph_nodegroup = vb.formula_morph_presets['0'][1].copy() if idx == 0 else vb.formula_morph_presets[f'{idx}'].copy()
                        morph_node,node_x,node_y = create_node(source_nodegroup, "GeometryNodeGroup", node_x, node_y, 50, 0)
                        morph_node.name = morph_nodegroup.name
                        morph_node.node_tree = morph_nodegroup
                        node_yy = 0
                        node_xx = p_socket.node.location.x if len(p_socket.links)==0 else p_socket.links[0].to_node.location.x
                        for link in n_socket.links:
                            if node_yy > link.from_node.location.y - link.from_node.height - 20:
                                node_yy = link.from_node.location.y - link.from_node.height - 20
                        source_nodegroup.links.new(morph_node.outputs['Origin'], n_socket)
                        source_nodegroup.links.new(p_socket, morph_node.inputs['Source'])
                        remove_link = source_nodegroup.links.new(morph_node.outputs['Morph'], n_socket)
                        p_socket = morph_node.outputs['Morph']
                        node_xx = p_socket.node.location.x - 190
                        node_yy = p_socket.node.location.y - 256 - 20
                        join_node, node_xx, node_yy = create_node(source_nodegroup, "GeometryNodeJoinGeometry", node_xx, node_yy, -50, -50)
                        t_idx = 0
                        to_key = []
                        mute_nodes = [source_node]
                        morph_items = [nodes[0][2]]
                        for target in targets:
                            if not target[0]:
                                if t_idx == 0:
                                    morph_node.inputs['Keep Source'].default_value = keep
                                    keep = target[1]
                                continue
                            if target[2].type == 'layer':
                                color_strength = target[0].inputs['Color Strength'].default_value
                                target[0].inputs['Color Strength'].default_value = 0.0
                            else:
                                target[0].mute = True
                                if target[0].inputs['Geometry'].is_linked:
                                    ng = target[0].id_data
                                    ng.links.remove(target[0].inputs['Geometry'].links[0])
                            mute_nodes.append(target[0])
                            morph_items.append(target[2])
                            target_node, node_xx, node_yy = create_node(source_nodegroup, "GeometryNodeGroup", node_xx, node_yy, 0, -10)
                            target_node.node_tree = target[0].node_tree
                            if t_idx == 0:
                                morph_node.inputs['Keep Source'].default_value = keep
                                keep = target[1]
                            t_idx += 1
                            if target[2].type == 'layer':
                                target_node.label = target[2].inputs
                                target_node.name = f'{target[0].node_tree.name}.Morph'
                                if target[2].obj_id == source_morph.obj_id:
                                    groupIn_node,_,_ = create_node(source_nodegroup, "NodeGroupInput", target_node.location.x-190, target_node.location.y, 0, 0)
                                    source_nodegroup.links.new(groupIn_node.outputs['Geometry'], target_node.inputs['Geometry'])
                                else:
                                    target_node.node_tree = bpy.data.node_groups['Select Layer'].copy()
                                    groupIn_node,_,_ = create_node(source_nodegroup, "GeometryNodeObjectInfo", target_node.location.x-190, target_node.location.y, 0, 0)
                                    refer_obj = None
                                    for obj in bpy.data.objects:
                                        if obj.get('math_anim_obj') and obj["math_anim_obj"] == target[2].obj_id:
                                            refer_obj = obj
                                    groupIn_node.inputs['Object'].default_value = refer_obj
                                    source_nodegroup.links.new(groupIn_node.outputs['Geometry'], target_node.inputs['Geometry'])
                                target_node.inputs['Layer Name'].default_value = target[2].inputs
                                target_node.inputs['Color Strength'].default_value = color_strength
                                source_nodegroup.links.new(target_node.outputs['Curve'], join_node.inputs['Geometry'])
                                to_key.append(target_node.label)
                            else:
                                source_nodegroup.links.new(target_node.outputs['Curve'], join_node.inputs['Geometry'])
                                if target[2].type == 'char' or target[2].type == 'input':
                                    to_key.append(target_node.node_tree.nodes['String to Curves'].inputs['String'].default_value)
                                else:
                                    to_key.append(target_node.node_tree.name)
                        from_key = f"{from_key} -> {to_key}"
                        source_nodegroup.links.new(join_node.outputs['Geometry'], morph_node.inputs['Target'])
                        idx += 1
                        morph_list.append((morph_node, mute_nodes, morph_items))
                        add_curve_preset(curve_anim_setting, morph_node.node_tree.nodes['Float Curve'])
                    key_name = f"{nodes[0][2].morph_idx}:  {from_key}"
                    vb.formula_anim_nodes['morph_anim'].append({key_name:  morph_list})
                    item = anim_setting_status.add()
                    item.name = key_name
                    vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1

            # Clear the reference after use
            bpy.data.node_groups['Curve Morph Anim'].interface.items_tree['Start Frame'].default_value = 1
            bpy.data.node_groups['Curve Morph Anim'].interface.items_tree['Anim Length'].default_value = 24
            self.__class__._active_morph_setting = {}
            for i in context.scene.math_anim_morph_selected_idx:
                i.context_selected_idx = 0
                i.context_selected_len = 0
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.
        split = layout.split(factor=0.85)
        row = split.row(align=True)

        morph_targets = context.scene.math_anim_morph_targets
        morph_settings = context.scene.math_anim_morphSettings
        col_target = []
        for i in range(len(morph_targets)):
            col = row.column(align=True)
            col.use_property_split = True
            col.use_property_decorate = False
            col_target.append(col)
            col.prop(morph_targets[i], "math_obj_targets", text="From" if i==0 else 'To')
        row.operator("math_anim.add_morph_target", text="", icon='ADD')
        row.operator("math_anim.del_morph_target", text="", icon='REMOVE')
        col = split.column(align=True)
        col.prop(self, "morph_order", text="")
        col.separator()
        if self.morph_order == "Parallel":
            anim_group = vb.formula_morph_presets['0'][0]
            col.separator()
            col.label(text="Morph Default Setting")
            col.prop(anim_group.interface.items_tree['Start Frame'], 'default_value', text="Start Frame")
            col.prop(anim_group.interface.items_tree['Anim Length'], 'default_value', text="Anim Length")
            col.label(text="Animation Curve")
            col.template_curve_mapping(anim_group.nodes['Float Curve'], "mapping")
        else:
            for i in range(len(vb.formula_morph_presets)):
                anim_group = vb.formula_morph_presets['0'][1] if i==0 else vb.formula_morph_presets[f'{i}']
                col.separator()
                col.label(text=f"Level {i} Setting")
                col.prop(anim_group.interface.items_tree['Start Frame'], 'default_value', text="Start Frame")
                col.prop(anim_group.interface.items_tree['Anim Length'], 'default_value', text="Anim Length")
                col.label(text="Animation Curve")
                col.template_curve_mapping(anim_group.nodes['Float Curve'], "mapping")
                col.separator()

        # initialize _obj_holders
        enum_sources = MATH_ANIM_Morph_Targets.get_math_obj_targets(self, context)
        self._obj_holders.clear()
        for morph_obj, _, _ in enum_sources:
            self._obj_holders[morph_obj] = {} # obj_holder: page_holder, obj_idx, idx
            # source as first
            idx = 0
            for morph_obj_holder in morph_settings:
                if morph_obj == morph_obj_holder.name:
                    page_holder = morph_obj_holder.page_holder
                    self._obj_holders[morph_obj]['obj_holder'] = page_holder
                    self._obj_holders[morph_obj]['obj_idx'] = idx
                idx += 1
        # find the morph setting holder
        self.__class__._active_morph_setting = {'morph_setting': [], 'sel_len': []}
        for i in range(len(morph_targets)):
            morph_target = morph_targets[i].math_obj_targets
            if not morph_target:
                continue
            page_holder = self._obj_holders[morph_target]['obj_holder']
            active_morph_setting = []
            sel_len = 0
            for page_num in range(len(page_holder)):
                if len(page_holder) > 1:
                    col_target[i].label(text=f"Page {page_num}")
                morph_setting = page_holder[page_num].morph_collection[i].morph_setting
                char_idx = []
                stroke_idx = []
                fill_idx = []
                layer_idx = []
                input_idx = []
                for index, morph in enumerate(morph_setting):
                    if morph.type == 'char':
                        char_idx.append(index)
                    elif morph.type == 'stroke':
                        stroke_idx.append(index)
                    elif morph.type == 'fill':
                        fill_idx.append(index)
                    elif morph.type == 'layer':
                        layer_idx.append(index)
                    elif morph.type == 'input':
                        input_idx.append(index)
                idx = char_idx[::-1]
                idx.extend(stroke_idx[::-1])
                idx.extend(fill_idx[::-1])
                idx.extend(layer_idx)
                idx.extend(input_idx)
                for index in idx:
                    morph = morph_setting[index]
                    subrow = col_target[i].row(align=True)
                    subrow.enabled = morph.draw_tag
                    if i==0 and morph.type=='input':
                        subrow.enabled = False
                    if morph.selected:
                        name = morph.inputs
                        if morph.type == 'char':
                            name = morph.inputs[0]
                        subrow.prop(morph,"selected", text=f"{name:<3}{morph.morph_idx:>6}->" if i==0 else f"{morph.morph_idx:>3}->{name:>6}", toggle=1)
                        subrow.prop(morph,"keep", text="keep")
                        if not morph.morph:
                            sel_len += 1
                    else:
                        if not morph.inputs:
                            subrow.prop(morph, "inputs", text=" ")
                            subrow.label(text="")
                        else:
                            name = morph.inputs
                            if morph.type == 'char':
                                name = morph.inputs[0]
                            subrow.prop(morph,"selected", text=f"{name:^9}", toggle=1)
                            subrow.prop(morph,"keep", text="keep")
                subrow = col_target[i].row(align=True)
                subrow.alignment = 'CENTER'
                op_add = subrow.operator("math_anim.add_morph_item", text="", icon='ADD')
                op_del = subrow.operator("math_anim.del_morph_item", text="", icon='REMOVE')
                # Pass the path to the collection
                obj_idx = self._obj_holders[morph_target]['obj_idx']
                op_add.morph_setting_path = f"context.scene.math_anim_morphSettings[{obj_idx}].page_holder[{page_num}]"
                op_add.morph_obj = f"{morph_target}"
                op_del.morph_setting_path = f"context.scene.math_anim_morphSettings[{obj_idx}].page_holder[{page_num}]"
                active_morph_setting.append(morph_setting)
            self.__class__._active_morph_setting['morph_setting'].append(active_morph_setting)
            self.__class__._active_morph_setting['sel_len'].append(sel_len)

class MATH_OT_AddMorphTarget(bpy.types.Operator):
    bl_idname = "math_anim.add_morph_target"
    bl_label = "Add A Morph Target"
    bl_description = "Add A Morph Target"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        # import the morph anim if not existing
        anim_groups = ['Curve Morph Anim']
        for group_name in anim_groups:
            if bpy.data.node_groups.get(group_name) is None:
                import_anim_nodegroups([group_name])
            bpy.data.node_groups[group_name].use_fake_user = True
        return self.execute(context)

    def execute(self, context):
        morph_targets = context.scene.math_anim_morph_targets
        target_item = morph_targets.add()
        target_item.collection_idx = len(morph_targets) - 1
        if len(morph_targets) > len(context.scene.math_anim_morph_selected_idx):
            context.scene.math_anim_morph_selected_idx.add()
        # prepare morph anim preset node_groups for parallel and sequentials
        for i in range(len(morph_targets)-1):
            anim_nodegroup = bpy.data.node_groups['Curve Morph Anim']
            # for parallel
            if i == 0 and bpy.data.node_groups.get("morph_anim_parallel_preset") is None:
                new_group = anim_nodegroup.copy()
                new_group.name = "morph_anim_parallel_preset"
                vb.formula_morph_presets[f'{i}'] = [new_group]
            if bpy.data.node_groups.get(f"morph_anim_sequential_preset{i}") is None:
                new_group = anim_nodegroup.copy()
                new_group.name = f"morph_anim_sequential_preset{i}"
                if i == 0:
                    vb.formula_morph_presets[f'{i}'].append(new_group)
                else:
                    new_group.interface.items_tree['Start Frame'].default_value = 1 + i*24
                    vb.formula_morph_presets[f'{i}'] = new_group

        morph_settings = context.scene.math_anim_morphSettings
        if len(morph_targets) > len(morph_settings):
            for morph_obj in morph_settings:
                for page_holder in morph_obj.page_holder:
                    morph_collection = page_holder.morph_collection
                    new_collection = morph_collection.add()
                    morph_setting = new_collection.morph_setting
                    morph_collection_0 = page_holder.morph_collection[0]
                    for item_0 in morph_collection_0.morph_setting:
                        item = morph_setting.add()
                        item.type = item_0.type
                        item.draw_tag = item_0.draw_tag
                        item.page_idx = item_0.page_idx
                        item.item_idx = item_0.item_idx
                        item.obj_id = item_0.obj_id
                        item.collection_idx = len(morph_collection) - 1
                        item.morph = item_0.morph
                        item.inputs = item_0.inputs

        return {'FINISHED'}

class MATH_OT_DelMorphTarget(bpy.types.Operator):
    bl_idname = "math_anim.del_morph_target"
    bl_label = "Remove The Last Morph Target"
    bl_description = "Delete A Morph Target"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        morph_targets = context.scene.math_anim_morph_targets
        morph_selected_idx = context.scene.math_anim_morph_selected_idx
        morph_settings = context.scene.math_anim_morphSettings
        i = len(morph_targets) - 1
        if len(morph_targets) > 2:
            morph_targets.remove(i)
            for morph_obj in morph_settings:
                for page_holder in morph_obj.page_holder:
                    morph_collection = page_holder.morph_collection
                    if len(morph_collection) > len(morph_targets):
                        last_idx = len(morph_collection) - 1
                        for j in range(last_idx, len(morph_targets)-1, -1):
                            check_use = False
                            for morph in morph_collection[j].morph_setting:
                                if morph.draw_tag:
                                    check_del = True
                                    break
                            if check_use:
                                morph_collection.remove(j)
                                morph_selected_idx.remove(j)
                                #self.report({'INFO'}, 'Delete the last Morph Target')

            preset = vb.formula_morph_presets.pop(f'{i-1}', None)
            if preset is not None:
                bpy.data.node_groups.remove(preset)

        return {'FINISHED'}

class MATH_OT_AddMorphItem(bpy.types.Operator):
    bl_idname = "math_anim.add_morph_item"
    bl_label = "Add A Morph Char"
    bl_description = "Add A Morph Char"
    bl_options = {'REGISTER', 'UNDO'}

    morph_setting_path: bpy.props.StringProperty()
    morph_obj: bpy.props.StringProperty()

    def execute(self, context):
        # Get the collection from the path
        page_holder = eval(self.morph_setting_path)
        morph_collection = page_holder.morph_collection
        for i in range(len(morph_collection)):
            morph_setting = morph_collection[i].morph_setting
            item = morph_setting.add()
            item.type = 'input'
            item.item_idx = len(morph_setting) - 1
            start_idx = self.morph_setting_path.find('page_holder[') + len('page_holder[')
            end_idx = self.morph_setting_path.find(']', start_idx)
            item.page_idx  = int(self.morph_setting_path[start_idx:end_idx])
            item.collection_idx  = i
            item.obj_id  = self.morph_obj
            if len(morph_setting)>1:
                item.morph_last_idx = morph_setting[0].morph_last_idx

        return {'FINISHED'}

class MATH_OT_DelMorphItem(bpy.types.Operator):
    bl_idname = "math_anim.del_morph_item"
    bl_label = "Del A Morph Char"
    bl_description = "Delete A Morph Char"
    bl_options = {'REGISTER', 'UNDO'}

    morph_setting_path: bpy.props.StringProperty()

    def execute(self, context):
        # Get the collection from the path
        page_holder = eval(self.morph_setting_path)
        morph_collection = page_holder.morph_collection
        for i in range(len(morph_collection)):
            morph_setting = morph_collection[i].morph_setting
            if len(morph_setting) > 0 and morph_setting[-1].type == 'input' and not morph_setting[-1].morph:
                if morph_setting[-1].selected:
                    morph_setting[-1].selected = False # first deselect
        for i in range(len(morph_collection)):
            morph_setting = morph_collection[i].morph_setting
            if len(morph_setting) > 0 and morph_setting[-1].type == 'input' and not morph_setting[-1].morph:
                morph_setting.remove(len(morph_setting) - 1)
                self.report({'INFO'}, 'Delete the last input item')
            else:
                self.report({'INFO'}, 'No avaiable input item to delete')

        return {'FINISHED'}

class MATH_OT_CreateFormula(bpy.types.Operator):
    bl_idname = "math_anim.create_formula"
    bl_label = "Create Formula"
    bl_description = "Create a math formula or plain texts"
    bl_options = {'REGISTER', 'UNDO'}

    color_strength : bpy.props.FloatProperty(default=10.0, min=0.0)
    curve_radius : bpy.props.FloatProperty(default=0.005, min=0.0)
    def create_formula_holder(self, context, obj_name="Formula"):
        """ readonly property, doesn't work after reloading the saved file
        def get_math_anim_obj(self):
            return self["math_anim_obj"]

        bpy.types.Object.math_anim_obj = bpy.props.StringProperty(
            name="Math Animation Object",
            description="ID for math animation",
            get=get_math_anim_obj
        )
        """
        # grease pencil object
        bpy.ops.object.grease_pencil_add(type='EMPTY', align='WORLD', use_lights=False, scale=(1, 1, 1))
        formula_obj = context.active_object
        formula_obj.name = obj_name
        names = formula_obj.name.rsplit('.', 1)
        if len(names) == 2 and names[1].isdigit():
            formula_obj["math_anim_obj"] = f"{names[0]}.Global.{names[1]}"
        else:
            formula_obj["math_anim_obj"] = f"{names[0]}.Global"
        formula_obj.data.name = formula_obj.name

        return formula_obj

    def invoke(self, context, event):

        node_groups = ['GP Material', 'Layer Select', 'Finalize Curves']
        for group_name in node_groups:
            if bpy.data.node_groups.get(group_name) is None:
                import_anim_nodegroups([group_name])
                bpy.data.node_groups[group_name].use_fake_user = True

        return self.execute(context)

    def execute(self, context):
        # first check the font libs
        # prepare available fonts, load the font libs from the saved file, otherwise scan the provided path
        prefs = context.preferences.addons[__package__].preferences
        if not vb.font_path_dict:
            if os.path.exists(vb.font_save_file):
                vb.font_path_dict = load_dict_from_file(vb.font_save_file)
            else:
                font_paths = {}
                for font_path in prefs.paths:
                    font_path_dict = build_file_path_dict(font_path.path)
                    font_paths = {**font_paths, **font_path_dict}
                if font_paths:
                    vb.font_path_dict = font_paths
                    if not vb.font_path_dict:
                        self.report({"WARNING"}, "No available fonts, build the font lib or give a directory in the preferences.")
                else:
                    self.report({"WARNING"}, "No available fonts, build the font lib or give a directory in the preferences.")

        # now setup geometry nodes
        props = context.scene.math_anim_formula_props
        math_texts = []
        strokes = []
        fills = []
        colors = {}
        formula_holder = [context.scene.math_anim_optexcode, context.scene.math_anim_typstcode,
                         context.scene.math_anim_optexfile, context.scene.math_anim_typstfile,
                         context.scene.math_anim_pdffile]
        source_items = list(MATH_ANIM_Formula_Properties.bl_rna.properties['formula_source'].enum_items)

        formula_obj = ''
        for item_idx in range(len(source_items)):
            if props.formula_source == source_items[item_idx].identifier:
                contents = []
                mode = []
                font = []
                for item in formula_holder[item_idx].paths:
                    if item.selected:
                        if item.path:
                            contents.append(item.path)
                            mode.append(item.math)
                            if item_idx < 2:
                                font.append(item.font)
                if contents:
                    formula_obj = self.create_formula_holder(context)
                    with tempfile.TemporaryDirectory() as temp_dir:
                        math_texts, strokes, fills, colors = compile_tex(self, context, contents, mode, font, temp_dir, item_idx)
                else:
                    self.report({"ERROR"}, "No inputs to deal with!!!")
                    return {'CANCELLED'}
                if any(math_texts) or any(strokes) or any(fills):
                    mat_name = "math_gp_mat"
                    gp_materials = {'line':{}, 'fill':{}}
                    mesh_material = bpy.data.materials.new(name="math_mesh_mat")
                    mesh_material.use_nodes = True
                    nodes = mesh_material.node_tree.nodes
                    mesh_material.use_fake_user = True
                    nodes.clear()
                    emission = nodes.new('ShaderNodeEmission')
                    attr_color = nodes.new('ShaderNodeAttribute')
                    attr_color.attribute_name = "vertex_color"
                    attr_strength = nodes.new('ShaderNodeAttribute')
                    attr_strength.attribute_name = "opacity"
                    output = nodes.new('ShaderNodeOutputMaterial')
                    mesh_material.node_tree.links.new(attr_color.outputs['Color'], emission.inputs['Color'])
                    mesh_material.node_tree.links.new(attr_strength.outputs['Fac'], emission.inputs['Strength'])
                    mesh_material.node_tree.links.new(emission.outputs['Emission'], output.inputs['Surface'])
                    arrange_nodes(attr_color, attr_strength, 'b', 160)
                    arrange_nodes(attr_strength, emission, 'r', 50)
                    arrange_nodes(emission, output, 'r', 50)

                    if len(colors['line']) > 0:
                        for idx, (color, _) in enumerate(colors['line'].items()):
                            if idx == 0:
                                gp_mat = formula_obj.material_slots[0].material
                                gp_mat.name = f"{mat_name}"
                                gp_mat.grease_pencil.color = color
                                gp_materials['line'][color] = {"index": idx}
                            else:
                                gp_materials['line'][color] = {"index": idx}
                    if len(colors['fill']) > 0:
                        for idx, (color, _) in enumerate(colors['fill'].items()):
                            if len(colors['line']) == 0:
                                gp_mat = formula_obj.material_slots[0].material
                                gp_mat.name = "gp_fill_mat"
                                gp_mat.grease_pencil.color = color
                                gp_mat.grease_pencil.fill_color = color
                                gp_mat.grease_pencil.show_stroke = False
                                gp_mat.grease_pencil.show_fill = True
                                gp_materials['fill'][color] = {"index": idx}
                            else:
                                gp_materials['fill'][color] = {"index": idx}
                    #start = time.perf_counter()
                    nodes = setup_formula_geonodes(self, context, formula_obj, math_texts, strokes, fills, gp_materials, mesh_material, color_strength=self.color_strength, curve_radius=self.curve_radius)
                    #end = time.perf_counter()
                    #print(f"Formula Geonodes setup time: {end - start:.4f} seconds")
                    if nodes is None:
                        return {'CANCELLED'}
                else:
                    self.report({"INFO"}, "No contents found.")

                return {'FINISHED'}

class MATH_OT_DelGroupAnim(bpy.types.Operator):
    bl_idname = "math_anim.del_group_anim"
    bl_label = "Delete a group of individual's anims"
    bl_description = "Delete a group of individual's anims"
    bl_options = {'REGISTER', 'UNDO'}

    node_name: bpy.props.StringProperty(default="")

    def execute(self, context):
        anim_type = self.node_name.split('**')[1]
        node_name = self.node_name.split('**')[0]
        nodes = vb.formula_anim_nodes['group_anim'][anim_type][node_name][-1]
        curve_anim_setting = context.scene.math_anim_curve_gen_settings
        if anim_type == 'wave_anim':
            node1 = vb.formula_anim_nodes['group_anim'][anim_type][node_name][0]
            node2 = vb.formula_anim_nodes['group_anim'][anim_type][node_name][1]
            nodes_name = [node1.name, node2.name]
            for node in nodes:
                for name in nodes_name:
                    node_to_remove = node.node_tree.nodes.get(name)
                    if node_to_remove:
                        p_socket = node_to_remove.inputs[0].links[0].from_socket
                        n_socket = node_to_remove.outputs[0].links[0].to_socket
                        node_group = node_to_remove.node_tree
                        del_curve_preset(curve_anim_setting, node_to_remove.node_tree.nodes['Float Curve'])
                        node.node_tree.nodes.remove(node_to_remove)
                        node.node_tree.links.new(p_socket, n_socket)
                        if node_group:
                            if node_group.users==0:
                                bpy.data.node_groups.remove(node_group)
                            elif node_group.use_fake_user and node_group.users==1:
                                node_group.use_fake_user = False
                                bpy.data.node_groups.remove(node_group)
            vb.formula_anim_nodes['group_anim'][anim_type].pop(node_name, None)
            key_name = [node.name]
            animsetting_status_reset(context, key_name)
        elif anim_type == 'color_flow':
            for node in nodes:
                parent_group = node.outputs[0].links[0].to_node.node_tree
                node_to_remove = parent_group.nodes.get(node_name)
                if node_to_remove:
                    p1_socket = node_to_remove.inputs['Grease Pencil'].links[0].from_socket
                    p2_socket = node_to_remove.inputs['Mesh'].links[0].from_socket
                    n1_socket = node_to_remove.outputs['Grease Pencil'].links[0].to_socket
                    n2_socket = node_to_remove.outputs['Mesh'].links[0].to_socket
                    node_group = node_to_remove.node_tree
                    del_curve_preset(curve_anim_setting, node_to_remove.node_tree.nodes['Mesh Float Curve'])
                    del_curve_preset(curve_anim_setting, node_to_remove.node_tree.nodes['GP Float Curve'])
                    parent_group.nodes.remove(node_to_remove)
                    parent_group.links.new(p1_socket, n1_socket)
                    parent_group.links.new(p2_socket, n2_socket)
                    if node_group:
                        if node_group.users==0:
                            bpy.data.node_groups.remove(node_group)
                        elif node_group.use_fake_user and node_group.users==1:
                            node_group.use_fake_user = False
                            bpy.data.node_groups.remove(node_group)
            vb.formula_anim_nodes['group_anim'][anim_type].pop(node_name, None)
            key_name = [node_name]
            animsetting_status_reset(context, key_name)
        else:
            for node in nodes:
                node_to_remove = node.node_tree.nodes.get(node_name)
                if node_to_remove:
                    if anim_type in ["writing_anim", "grow_anim", "transform_anim", "flow_anim"]:
                        if anim_type == "transform_anim":
                            del_curve_preset(curve_anim_setting, node_to_remove.node_tree.nodes['Rotate Anim Curve'])
                            del_curve_preset(curve_anim_setting, node_to_remove.node_tree.nodes['Offset Anim Curve'])
                            del_curve_preset(curve_anim_setting, node_to_remove.node_tree.nodes['Scale Anim Curve'])
                        else:
                            del_curve_preset(curve_anim_setting, node_to_remove.node_tree.nodes['Float Curve'])
                    p_socket = node_to_remove.inputs[0].links[0].from_socket
                    n_socket = node_to_remove.outputs[0].links[0].to_socket
                    node_group = node_to_remove.node_tree
                    node.node_tree.nodes.remove(node_to_remove)
                    if anim_type != 'flow_anim':
                        node.node_tree.links.new(p_socket, n_socket)
                    if node_group:
                        if node_group.users==0:
                            bpy.data.node_groups.remove(node_group)
                        elif node_group.use_fake_user and node_group.users==1:
                            node_group.use_fake_user = False
                            bpy.data.node_groups.remove(node_group)
            vb.formula_anim_nodes['group_anim'][anim_type].pop(node_name, None)
            key_name = [node_name]
            animsetting_status_reset(context, key_name)
        return {'FINISHED'}

class MATH_OT_GroupSetup(bpy.types.Operator):
    bl_idname = "math_anim.group_setup"
    bl_label = "Setup for a group of individuals"
    bl_description = "Setup animations for a group of individuals"
    bl_options = {'REGISTER', 'UNDO'}

    indiv_anim: bpy.props.BoolProperty(default=False)
    grow_anim: bpy.props.BoolProperty(default=False)
    writing_anim: bpy.props.BoolProperty(default=False)
    color_flow: bpy.props.BoolProperty(default=False)
    flow_anim: bpy.props.BoolProperty(default=False)
    wave_anim: bpy.props.BoolProperty(default=False)
    transform_anim: bpy.props.BoolProperty(default=False)
    transform: bpy.props.BoolProperty(default=False)
    material: bpy.props.BoolProperty(default=False)
    update_font: bpy.props.BoolProperty(default=False)
    win_width: bpy.props.IntProperty(default=690)
    node_path: bpy.props.StringProperty(default="")

    render_type: bpy.props.EnumProperty(
        items=[('GP', 'Grease Pencil', ''),
               ('Mesh', 'Mesh', ''),
               ],
        default = 'GP'
    )

    def invoke(self, context, event):
        # prepare animgroups
        anim_groups = ['Grow Anim.Local', 'Transform.Local', 'Writing Curve Anim.Local', 'Edge Flow Anim.Local', 'Wave Anim.Local', 'Color Flow Anim.Local', 'Transform Anim.Local']
        for group_name in anim_groups:
            if bpy.data.node_groups.get(group_name) is None:
                import_anim_nodegroups([group_name])
                bpy.data.node_groups[group_name].use_fake_user = True
        if not self.indiv_anim:
            # add a new collection to hold the selection
            morph_settings = context.scene.math_anim_morphSettings
            for obj_holder in morph_settings:
                for page_holder in obj_holder.page_holder:
                    new_collection = page_holder.morph_collection.add()
                    new_setting = new_collection.morph_setting
                    for item_0 in page_holder.morph_collection[0].morph_setting:
                        item = new_setting.add()
                        item.type = item_0.type
                        item.page_idx = item_0.page_idx
                        item.item_idx = item_0.item_idx
                        item.obj_id = item_0.obj_id
                        item.collection_idx = len(page_holder.morph_collection) - 1
                        item.inputs = item_0.inputs
            context.scene.math_anim_morph_selected_idx.add()
        # holder for the animgroups
        if not self.indiv_anim:
            if 'group_anim' not in vb.formula_anim_nodes:
                vb.formula_anim_nodes['group_anim'] = {}
                anim_type = ['grow_anim', 'wave_anim', 'writing_anim',  'color_flow', 'flow_anim', 'transform_anim', 'transform']
                for anim in anim_type:
                    if anim not in vb.formula_anim_nodes['group_anim']:
                        vb.formula_anim_nodes['group_anim'][anim] = {} # animgroup.name: (animnode, [node1, node2, ...])
        else:
            if 'indiv_anim' not in vb.formula_anim_nodes:
                vb.formula_anim_nodes['indiv_anim'] = {}
                anim_type = ['grow_anim', 'wave_anim', 'writing_anim', 'color_flow', 'flow_anim', 'transform_anim', 'transform']
                for anim in anim_type:
                    if anim not in vb.formula_anim_nodes['indiv_anim']:
                        vb.formula_anim_nodes['indiv_anim'][anim] = {} # node.name: [animnode, ...]

        if not self.indiv_anim:
            wm = context.window_manager
            return wm.invoke_props_dialog(self, width=self.win_width)
        else:
            return self.execute(context)

    def execute(self, context):
        node_list = []
        if not self.indiv_anim:
            morph_settings = context.scene.math_anim_morphSettings
            for obj_holder in morph_settings:
                for obj in bpy.data.objects:
                    if obj.get('math_anim_obj') is not None and obj["math_anim_obj"] == obj_holder.name:
                        formula_obj = obj
                for page_holder in obj_holder.page_holder:
                    collections = page_holder.morph_collection
                    use_collection = collections[len(collections)-1]
                    for item in use_collection.morph_setting:
                        if item.keep:
                            if item.type == 'char':
                                node = vb.formula_node_trees[item.obj_id][item.page_idx]['text_nodes'][f'{item.inputs}']
                                node_list.append((node, formula_obj))
                            elif item.type == 'stroke':
                                node = vb.formula_node_trees[item.obj_id][item.page_idx]['stroke_nodes'][f'{item.inputs}']
                                node_list.append((node, formula_obj))
                            elif item.type == 'fill':
                                node = vb.formula_node_trees[item.obj_id][item.page_idx]['fill_nodes'][f'{item.inputs}']
                                node_list.append((node, formula_obj))
        else:
            formula_obj = context.object
            if formula_obj.get('math_anim_obj') is None:
                self.report({'WARNING'}, "Select a formula object first.")
                return {'CANCELLED'}
            page_num = int(self.node_path.split('*.*')[0])
            node_type = self.node_path.split('*.*')[1]
            key_name = self.node_path.split('*.*')[2]
            node = vb.formula_node_trees[formula_obj["math_anim_obj"]][page_num][node_type][key_name]
            node_list = [(node, formula_obj)]
        # setup the animation nodes
        if len(node_list) == 0:
            self.report({'INFO'}, 'No items selected.')
            return {'FINISHED'}
        anim_setting_status = context.scene.math_animSetting_status
        curve_anim_setting = context.scene.math_anim_curve_gen_settings
        if self.grow_anim:
            anim_node  = ''
            nodes = []
            anim_group = bpy.data.node_groups['Grow Anim.Local'].copy()
            if not self.indiv_anim:
                anim_group.use_fake_user = True
            for node, formula_obj in node_list:
                nodes.append(node)
                n_socket = node.node_tree.nodes['Realize Instances'].inputs['Geometry']
                p_socket = n_socket.links[0].from_socket
                node_x = p_socket.node.location.x
                node_y = p_socket.node.location.y + 121 + 20
                anim_node,_,_ = create_node(node.node_tree, "GeometryNodeGroup", node_x, node_y)
                anim_node.node_tree = anim_group
                anim_node.name = anim_group.name # make sure the node name same as animgroup name
                node.node_tree.links.new(p_socket, anim_node.inputs['Geometry'])
                node.node_tree.links.new(anim_node.outputs['Geometry'], n_socket)
            item = anim_setting_status.add()
            key_name = f"{anim_node.name}"
            item.name = key_name
            vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
            add_curve_preset(curve_anim_setting, anim_node.node_tree.nodes['Float Curve'])
            if not self.indiv_anim:
                vb.formula_anim_nodes['group_anim']['grow_anim'][anim_group.name] = (anim_node, nodes) # put anim_node here for easy UI drawing
            else:
                if node.name in vb.formula_anim_nodes['indiv_anim']['grow_anim']:
                    vb.formula_anim_nodes['indiv_anim']['grow_anim'][node.name].append(anim_node)  # put anim_node here for easy UI drawing
                else:
                    vb.formula_anim_nodes['indiv_anim']['grow_anim'][node.name] = [anim_node] # put anim_node here for easy UI drawing
        if self.transform_anim:
            anim_node  = ''
            nodes = []
            anim_group = bpy.data.node_groups['Transform Anim.Local'].copy()
            if not self.indiv_anim:
                anim_group.use_fake_user = True
            for node, formula_obj in node_list:
                nodes.append(node)
                n_socket = node.node_tree.nodes['Realize Instances'].inputs['Geometry']
                p_socket = n_socket.links[0].from_socket
                node_x = p_socket.node.location.x
                node_y = p_socket.node.location.y + 121 + 20
                anim_node,_,_ = create_node(node.node_tree, "GeometryNodeGroup", node_x, node_y)
                anim_node.node_tree = anim_group
                anim_node.name = anim_group.name # make sure the node name same as animgroup name
                anim_node.inputs['Index'].default_value = node.node_tree.nodes["Instance Anim"].inputs["Index"].default_value
                node.node_tree.links.new(p_socket, anim_node.inputs['Instances'])
                node.node_tree.links.new(anim_node.outputs['Instances'], n_socket)
            item = anim_setting_status.add()
            key_name = f"{anim_node.name}"
            item.name = key_name
            vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
            add_curve_preset(curve_anim_setting, anim_node.node_tree.nodes['Rotate Anim Curve'])
            add_curve_preset(curve_anim_setting, anim_node.node_tree.nodes['Offset Anim Curve'])
            add_curve_preset(curve_anim_setting, anim_node.node_tree.nodes['Scale Anim Curve'])
            if not self.indiv_anim:
                vb.formula_anim_nodes['group_anim']['transform_anim'][anim_group.name] = (anim_node, nodes) # put anim_node here for easy UI drawing
            else:
                if node.name in vb.formula_anim_nodes['indiv_anim']['transform_anim']:
                    vb.formula_anim_nodes['indiv_anim']['transform_anim'][node.name].append(anim_node)  # put anim_node here for easy UI drawing
                else:
                    vb.formula_anim_nodes['indiv_anim']['transform_anim'][node.name] = [anim_node] # put anim_node here for easy UI drawing
        if self.transform:
            anim_node  = ''
            nodes = []
            anim_group = bpy.data.node_groups['Transform.Local'].copy()
            if not self.indiv_anim:
                anim_group.use_fake_user = True
            for node, formula_obj in node_list:
                nodes.append(node)
                n_socket = node.node_tree.nodes['Realize Instances'].inputs['Geometry']
                p_socket = n_socket.links[0].from_socket
                node_x = p_socket.node.location.x
                node_y = p_socket.node.location.y + 121 + 20
                anim_node,_,_ = create_node(node.node_tree, "GeometryNodeGroup", node_x, node_y)
                anim_node.node_tree = anim_group
                anim_node.name = anim_group.name
                node.node_tree.links.new(p_socket, anim_node.inputs['Geometry'])
                node.node_tree.links.new(anim_node.outputs['Geometry'], n_socket)
            item = anim_setting_status.add()
            key_name = f"{anim_node.name}"
            item.name = key_name
            vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
            if not self.indiv_anim:
                vb.formula_anim_nodes['group_anim']['transform'][anim_group.name] = (anim_node, nodes)
            else:
                if node.name in vb.formula_anim_nodes['indiv_anim']['transform']:
                    vb.formula_anim_nodes['indiv_anim']['transform'][node.name].append(anim_node)
                else:
                    vb.formula_anim_nodes['indiv_anim']['transform'][node.name] = [anim_node]
        if self.writing_anim:
            anim_node  = ''
            nodes = []
            anim_group = bpy.data.node_groups['Writing Curve Anim.Local'].copy()
            if not self.indiv_anim:
                anim_group.use_fake_user = True
            for node, formula_obj in node_list:
                nodes.append(node)
                p_socket = node.node_tree.nodes['Realize Instances'].outputs['Geometry']
                n_socket = p_socket.links[0].to_socket
                node_x = n_socket.node.location.x
                node_y = n_socket.node.location.y + 121 + 20
                anim_node,_,_ = create_node(node.node_tree, "GeometryNodeGroup", node_x, node_y)
                anim_node.node_tree = anim_group
                anim_node.name = anim_group.name
                anim_node.inputs["Total Index"].default_value = len(node_list)
                anim_node.inputs["Current Index"].default_value = len(nodes) - 1
                node.node_tree.links.new(p_socket, anim_node.inputs['Curve'])
                node.node_tree.links.new(anim_node.outputs['Curve'], n_socket)
            item = anim_setting_status.add()
            key_name = f"{anim_node.name}"
            item.name = key_name
            vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
            add_curve_preset(curve_anim_setting, anim_node.node_tree.nodes['Float Curve'])
            if not self.indiv_anim:
                vb.formula_anim_nodes['group_anim']['writing_anim'][anim_group.name] = (anim_node, nodes)
            else:
                if node.name in vb.formula_anim_nodes['indiv_anim']['writing_anim']:
                    vb.formula_anim_nodes['indiv_anim']['writing_anim'][node.name].append(anim_node)
                else:
                    vb.formula_anim_nodes['indiv_anim']['writing_anim'][node.name] = [anim_node]
        if self.color_flow:
            anim_node  = ''
            nodes = []
            anim_group = bpy.data.node_groups['Color Flow Anim.Local'].copy()
            if not self.indiv_anim:
                anim_group.use_fake_user = True
            for node, formula_obj in node_list:
                nodes.append(node)
                parent_group = node.outputs[0].links[0].to_node.node_tree
                n1_socket = parent_group.nodes['Render Type'].inputs['Grease Pencil']
                n2_socket = parent_group.nodes['Render Type'].inputs['Mesh']
                p1_socket = n1_socket.links[0].from_socket
                p2_socket = n2_socket.links[0].from_socket
                node_x = p2_socket.node.location.x + 140
                node_y = p2_socket.node.location.y + 20
                anim_node,_,_ = create_node(parent_group, "GeometryNodeGroup", node_x, node_y)
                anim_node.node_tree = anim_group
                anim_node.name = anim_group.name
                anim_node.inputs["Total Index"].default_value = len(node_list)
                anim_node.inputs["Current Index"].default_value = len(nodes) - 1
                parent_group.links.new(p1_socket, anim_node.inputs['Grease Pencil'])
                parent_group.links.new(anim_node.outputs['Grease Pencil'], n1_socket)
                parent_group.links.new(p2_socket, anim_node.inputs['Mesh'])
                parent_group.links.new(anim_node.outputs['Mesh'], n2_socket)
                while p2_socket.links[0].to_node.name != 'Group Output':
                    arrange_nodes(p2_socket.node, p2_socket.links[0].to_node, 'r', 50, 0)
                    p2_socket = p2_socket.links[0].to_node.outputs[0]
            item = anim_setting_status.add()
            key_name = f"{anim_node.name}"
            item.name = key_name
            vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
            add_curve_preset(curve_anim_setting, anim_node.node_tree.nodes['Mesh Float Curve'])
            add_curve_preset(curve_anim_setting, anim_node.node_tree.nodes['GP Float Curve'])
            if not self.indiv_anim:
                vb.formula_anim_nodes['group_anim']['color_flow'][anim_group.name] = (anim_node, nodes)
            else:
                if node.name in vb.formula_anim_nodes['indiv_anim']['color_flow']:
                    vb.formula_anim_nodes['indiv_anim']['color_flow'][node.name].append(anim_node)
                else:
                    vb.formula_anim_nodes['indiv_anim']['color_flow'][node.name] = [anim_node]
        if self.wave_anim:
            anim_nodes  = ['', '']
            anim_groups  = []
            anim_group = bpy.data.node_groups['Wave Anim.Local'].copy()
            if not self.indiv_anim:
                anim_group.use_fake_user = True
            anim_groups.append(anim_group)
            anim_group = bpy.data.node_groups['Wave Anim.Local'].copy()
            if not self.indiv_anim:
                anim_group.use_fake_user = True
            anim_groups.append(anim_group)
            nodes = []
            for node, formula_obj in node_list:
                nodes.append(node)
                # local wave
                p_socket = node.node_tree.nodes['Realize Instances'].outputs['Geometry']
                n_socket = p_socket.links[0].to_socket
                node_x = n_socket.node.location.x
                node_y = n_socket.node.location.y + 121 + 20
                anim_node,_,_ = create_node(node.node_tree, "GeometryNodeGroup", node_x, node_y)
                anim_node.node_tree = anim_groups[0]
                anim_node.name = anim_groups[0].name
                if not bpy.data.node_groups['Wave Anim.Local'].nodes['Passthrough'].boolean:
                    anim_node.node_tree.nodes['Passthrough'].boolean = True
                node.node_tree.links.new(p_socket, anim_node.inputs['Geometry'])
                node.node_tree.links.new(anim_node.outputs['Geometry'], n_socket)
                anim_nodes[0] = anim_node

                # global wave
                n_socket = node.node_tree.nodes['Realize Instances'].inputs['Geometry']
                p_socket = n_socket.links[0].from_socket
                node_x = p_socket.node.location.x
                node_y = p_socket.node.location.y + 121 + 20
                anim_node,_,_ = create_node(node.node_tree, "GeometryNodeGroup", node_x, node_y)
                anim_node.node_tree = anim_groups[1]
                anim_node.name = anim_groups[1].name
                if bpy.data.node_groups['Wave Anim.Local'].nodes['Passthrough'].boolean:
                    anim_node.node_tree.nodes['Passthrough'].boolean = True
                node.node_tree.links.new(p_socket, anim_node.inputs['Geometry'])
                node.node_tree.links.new(anim_node.outputs['Geometry'], n_socket)
                anim_nodes[1] = anim_node
            item = anim_setting_status.add()
            key_name = f"{anim_groups[0].name}"
            item.name = key_name
            vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
            add_curve_preset(curve_anim_setting, anim_nodes[0].node_tree.nodes['Float Curve'])
            add_curve_preset(curve_anim_setting, anim_nodes[1].node_tree.nodes['Float Curve'])
            if not self.indiv_anim:
                vb.formula_anim_nodes['group_anim']['wave_anim'][anim_groups[0].name] = (anim_nodes[0], anim_nodes[1], nodes) # need to special deal when delete
            else:
                if node.name in vb.formula_anim_nodes['indiv_anim']['wave_anim']:
                    vb.formula_anim_nodes['indiv_anim']['wave_anim'][node.name].append((anim_nodes[0], anim_nodes[1]))
                else:
                    vb.formula_anim_nodes['indiv_anim']['wave_anim'][node.name] = [(anim_nodes[0], anim_nodes[1])]
        if self.flow_anim:
            anim_groups = []
            nodes = []
            group_len = 0
            for node, formula_obj in node_list:
                join_socket = node.node_tree.nodes['Join Geometry'].inputs['Geometry']
                local_len = 0
                for link in join_socket.links:
                    if 'Edge Flow' not in link.from_node.name:
                        local_len += 1
                if group_len < local_len:
                    group_len = local_len
            for i in range(group_len):
                anim_group = bpy.data.node_groups['Edge Flow Anim.Local'].copy()
                if not self.indiv_anim:
                    anim_group.use_fake_user = True
                anim_groups.append(anim_group)
            anim_nodes = [None]*len(anim_groups)
            for node, formula_obj in node_list:
                nodes.append(node)
                join_socket = node.node_tree.nodes['Join Geometry'].inputs['Geometry']
                node_x = join_socket.node.location.x
                node_y = join_socket.node.location.y
                for link in join_socket.links:
                    if node_y < link.from_node.location.y:
                        node_y = link.from_node.location.y
                idx = 0
                for link in join_socket.links:
                    if 'Edge Flow' in link.from_node.name:
                        continue
                    p_socket = link.from_socket
                    node_y += (idx+1)*(500 + 20)
                    anim_node,_,_ = create_node(node.node_tree, "GeometryNodeGroup", node_x, node_y)
                    anim_node.node_tree = anim_groups[idx]
                    anim_node.name = anim_groups[idx].name
                    node.node_tree.links.new(p_socket, anim_node.inputs['Geometry'])
                    node.node_tree.links.new(anim_node.outputs['Geometry'], join_socket)
                    anim_nodes[idx] = anim_node
                    add_curve_preset(curve_anim_setting, anim_nodes[idx].node_tree.nodes['Float Curve'])
                    idx += 1
            if not self.indiv_anim:
                for i in range(len(anim_groups)):
                    item = anim_setting_status.add()
                    key_name = f"{anim_groups[i].name}"
                    item.name = key_name
                    vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
                    vb.formula_anim_nodes['group_anim']['flow_anim'][anim_groups[i].name] = (anim_nodes[i], nodes) # need to special care when delete
            else:
                item = anim_setting_status.add()
                key_name = f"{anim_groups[0].name}"
                item.name = key_name
                vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
                if node.name in vb.formula_anim_nodes['indiv_anim']['flow_anim']:
                    vb.formula_anim_nodes['indiv_anim']['flow_anim'][node.name].append(tuple(anim_nodes))
                else:
                    vb.formula_anim_nodes['indiv_anim']['flow_anim'][node.name] = [tuple(anim_nodes)]
        if self.material:
            for node, formula_obj in node_list:
                set_node = node.node_tree.nodes[f'Char Settings']
                set_node.inputs['Individual Control'].default_value = bpy.data.node_groups['char_settings'].interface.items_tree['Individual Control'].default_value
                set_node.inputs['Color'].default_value = bpy.data.node_groups['char_settings'].interface.items_tree['Color'].default_value
                set_node.inputs['Color Strength'].default_value = bpy.data.node_groups['char_settings'].interface.items_tree['Color Strength'].default_value
                set_node.inputs['Curve Radius'].default_value = bpy.data.node_groups['char_settings'].interface.items_tree['Curve Radius'].default_value
        if self.update_font:
            formula_props = context.scene.math_anim_formula_props
            for node, formula_obj in node_list:
                if node.node_tree.nodes.get("String to Curves") and formula_props.formula_font:
                    node.node_tree.nodes['String to Curves'].inputs['Font'].default_value = formula_props.formula_font

        if not self.indiv_anim:
            # remove the added collection
            morph_settings = context.scene.math_anim_morphSettings
            for obj_holder in morph_settings:
                for page_holder in obj_holder.page_holder:
                    page_holder.morph_collection.remove(len(page_holder.morph_collection)-1)
            context.scene.math_anim_morph_selected_idx.remove(len(context.scene.math_anim_morph_selected_idx)-1)
            # reset material
            bpy.data.node_groups['char_settings'].interface.items_tree['Individual Control'].default_value = False
            bpy.data.node_groups['char_settings'].interface.items_tree['Color'].default_value = (1.0, 0.0, 0.0, 1.0)
            bpy.data.node_groups['char_settings'].interface.items_tree['Color Strength'].default_value = 10.0
            bpy.data.node_groups['char_settings'].interface.items_tree['Curve Radius'].default_value = 0.002

        return{'FINISHED'}

    def draw(self, context):
        layout = self.layout
        #layout.use_property_split = True
        #layout.use_property_decorate = False  # No animation.
        item_settings = context.scene.math_anim_morphSettings
        col = layout.column(align=True)
        for obj_holder in item_settings:
            # get the display name
            obj_name = ''
            for obj in bpy.data.objects:
                if obj.get('math_anim_obj') is not None and obj["math_anim_obj"] == obj_holder.name:
                    obj_name = obj.name
            page_holder = obj_holder.page_holder
            row = col.row(align=True)
            row.label(text=f"{obj_name}")
            for page_num in range(len(page_holder)):
                item_collection = page_holder[page_num].morph_collection[len(page_holder[page_num].morph_collection)-1]
                item_setting = item_collection.morph_setting
                strokes = []
                chars = []
                fills = []
                for i, item in enumerate(item_setting):
                    if item.type == 'char':
                        chars.append(i)
                    elif item.type == 'stroke':
                        strokes.append(i)
                    elif item.type == 'fill':
                        fills.append(i)
                for i, idx in enumerate(chars[::-1]):
                    item = item_setting[idx]
                    if i%25 == 0:
                        row = col.row(align=False)
                    row.prop(item, "keep", text=f"{item.inputs[0]}" if item.type == 'char' else f"{item.inputs}", toggle=1)
                for i, idx in enumerate(strokes):
                    item = item_setting[idx]
                    if i%10 == 0:
                        row = col.row(align=False)
                    row.prop(item, "keep", text=f"{item.inputs[0]}" if item.type == 'char' else f"{item.inputs}", toggle=1)
                for i, idx in enumerate(fills):
                    item = item_setting[idx]
                    if i%15 == 0:
                        row = col.row(align=False)
                    row.prop(item, "keep", text=f"{item.inputs[0]}" if item.type == 'char' else f"{item.inputs}", toggle=1)
        col.separator()
        col.separator()
        col.label(text="Add Animations or set material. Note: if turn off material set, will use global material.")
        anim_type = {'grow_anim': self.grow_anim, 'writing_anim': self.writing_anim, 'wave_anim': self.wave_anim, 'color_flow': self.color_flow, 'flow_anim': self.flow_anim, 'transform_anim': self.transform_anim, 'transform': self.transform, 'material': self.material, 'update_font': self.update_font}
        col_anim = {}
        idx = 0
        for anim, switch in anim_type.items():
            if idx%3 == 0:
                row = col.row(align=True)
            col1 = row.column(align=True)
            col1.ui_units_x = self.win_width/len(anim_type)/2
            col1.prop(self, anim, text=anim.replace('_', ' ').capitalize(), toggle=True)
            col_anim[anim] = col1
            idx += 1
        for anim, switch in anim_type.items():
            if anim=='material' and switch:
                props = bpy.data.node_groups['char_settings']
                col_anim[anim].prop(props.interface.items_tree['Individual Control'], "default_value", text="Turn On/Off Material Set")
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.interface.items_tree['Color'], "default_value", text="Color")
                subrow.prop(props.interface.items_tree['Color Strength'], "default_value", text="Color Strength")
                col_anim[anim].label(text="For Grease Pencil")
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.interface.items_tree['Curve Radius'], "default_value", text="Curve Radius")
                col_anim[anim].separator()
            if anim=='grow_anim' and switch:
                props = bpy.data.node_groups['Grow Anim.Local']
                subrow = col_anim[anim].row(align=True)
                subrow.label(text="Effect Range:")
                subrow.prop(props.nodes['Start'], "integer", text="Start")
                subrow.prop(props.nodes['End'], "integer", text="End")
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.nodes['Start Frame'], "integer", text="Start Frame")
                subrow.prop(props.nodes['Anim Length'], "integer", text="Anim Length")
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.nodes['Reverse Grow'], "boolean", text="Reverse Grow")
                subrow.prop(props.nodes['Local'], "boolean", text="Local Grow")
                col_anim[anim].prop(props.nodes['Center'], "vector", text="Grow Center")
                col_anim[anim].label(text="Grow Anim Curve")
                col_anim[anim].template_curve_mapping(props.nodes['Float Curve'], "mapping")
                col_anim[anim].separator()
            if anim=='transform_anim' and switch:
                props = bpy.data.node_groups['Transform Anim.Local']
                subrow = col_anim[anim].row(align=True)
                subrow.label(text="Effect Range:")
                subrow.prop(props.nodes['Range Start'], "integer", text="Start")
                subrow.prop(props.nodes['Range End'], "integer", text="End")
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.nodes['Start Frame'], "integer", text="Start Frame")
                subrow.prop(props.nodes['Anim Length'], "integer", text="Anim Length")
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.nodes['Reverse'], "boolean", text="Reverse")
                subrow.prop(props.nodes['Randomize'], "boolean", text="Randomize")
                if props.nodes['Randomize'].boolean:
                    subrow.prop(props.nodes['Seed'], "integer", text="Seed")
                col_anim[anim].prop(props.nodes['Keep Before Start'], "boolean", text="Keep Before Start or After End")
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.nodes['Bypass Rotate'], "boolean", text="Mute Rotate")
                subrow.prop(props.nodes['Bypass Offset'], "boolean", text="Mute Offset")
                subrow.prop(props.nodes['Bypass Scale'], "boolean", text="Mute Scale")
                for transform in ['Offset', 'Rotate', 'Scale']:
                    if not props.nodes[f'Bypass {transform}'].boolean:
                        col_anim[anim].label(text=f"{transform} Anim Setting")
                        col_anim[anim].prop(props.nodes[f'{transform} Mix'].inputs['A'], "default_value", text=f"{transform}")
                        col_anim[anim].label(text=f"{transform} Anim Curve")
                        col_anim[anim].template_curve_mapping(props.nodes[f'{transform} Anim Curve'], "mapping")
                        if not props.nodes['Randomize'].boolean:
                            if transform == 'Rotate':
                                col_anim[anim].prop(props.nodes[f"{transform} Instances"].inputs['Pivot Point'], "default_value", text="Pivot Point")
                            elif transform == 'Scale':
                                col_anim[anim].prop(props.nodes[f"{transform} Instances"].inputs['Center'], "default_value", text="Center")
                            col_anim[anim].prop(props.nodes[f"{transform} Instances"].inputs['Local Space'], "default_value", text="Local Space")
                        col_anim[anim].separator()
            if anim=='writing_anim' and switch:
                props = bpy.data.node_groups['Writing Curve Anim.Local']
                subrow = col_anim[anim].row(align=True)
                subrow.label(text="Effect Range:")
                subrow.prop(props.nodes['Range Start'], "integer", text="Start")
                subrow.prop(props.nodes['Range End'], "integer", text="End")
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.nodes['Start Frame'], "integer", text="Start Frame")
                subrow.prop(props.nodes['Anim Length'], "integer", text="Anim Length")
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.nodes['Local'], "boolean", text="Local Writing")
                subrow.prop(props.nodes['Reverse'], "boolean", text="Reverse Writing")
                col_anim[anim].label(text="Writing Anim Curve")
                col_anim[anim].template_curve_mapping(props.nodes['Float Curve'], "mapping")
                ctl_switch = 'Local' if props.nodes['Local'].boolean else 'Global'
                split = col_anim[anim].split(factor=0.5)
                if ctl_switch == 'Global':
                    row = split.row(align=True)
                    row.prop(props.nodes['Writing Style'].inputs['Menu'], "default_value", expand=True)
                if (ctl_switch == 'Global' and props.nodes['Writing Style'].inputs['Menu'].default_value == "Writing") or ctl_switch == 'Local':
                    split.prop(props.nodes[f'Add {ctl_switch} Writing Symbol'], "boolean", text="Add Writing Symbol")
                    if props.nodes[f'Add {ctl_switch} Writing Symbol'].boolean:
                        col_anim[anim].template_ID(data=props.nodes[f'{ctl_switch} Writing Symbol'], property="font", open="font.open", unlink="font.unlink", text="Symbol Font")
                        col_anim[anim].prop(props.nodes[f'{ctl_switch} Writing Symbol'].inputs['String'], "default_value", text="Symbol")
                        col_anim[anim].prop(props.nodes[f'{ctl_switch} Writing Symbol Radius'].outputs['Value'], "default_value", text="Symbol Line Radius")
                        col_anim[anim].prop(props.nodes[f'{ctl_switch} Writing Symbol Color'], "value", text="Symbol Color")
                        col_anim[anim].prop(props.nodes[f'{ctl_switch} Writing Symbol Color Strength'].outputs['Value'], "default_value", text="Symbol Color Strength")
                        col_anim[anim].prop(props.nodes[f'{ctl_switch} Writing Symbol Translation'], "vector", text="Symbol Translation")
                        col_anim[anim].prop(props.nodes[f'{ctl_switch} Writing Symbol Rotation'], "rotation_euler", text="Symbol Rotation")
                        col_anim[anim].prop(props.nodes[f'{ctl_switch} Writing Symbol Scale'], "vector", text="Symbol Scale")
                col_anim[anim].separator()
            if anim=='wave_anim' and switch:
                props = bpy.data.node_groups['Wave Anim.Local']
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.nodes['Passthrough'], 'boolean', text="Global", invert_checkbox=True)
                subrow = col_anim[anim].row(align=True)
                subrow.label(text="Effect Range:")
                subrow.prop(props.nodes['Range Start'], "integer", text="Start")
                subrow.prop(props.nodes['Range End'], "integer", text="End")
                subrow = col_anim[anim].row(align=True)
                if props.nodes["Wave Texture"].wave_type == 'BANDS':
                    subrow.prop(props.nodes["Wave Texture"], "bands_direction", text="Wave Direction")
                else:
                    subrow.prop(props.nodes["Wave Texture"], "rings_direction", text="Wave Direction")
                subrow.prop(props.nodes["Menu Switch"].inputs['Menu'], "default_value", text="Effect On")
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.nodes["Wave Texture"], "wave_type", text="Wave Type")
                subrow.prop(props.nodes["Wave Texture"], "wave_profile", text="Wave Profile")
                col_anim[anim].label(text="Wave Control")
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.nodes['Speed'].outputs['Value'], "default_value", text="Speed")
                subrow.prop(props.nodes['Scale'].outputs['Value'], "default_value", text="Scale")
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.nodes["Wave Texture"].inputs['Distortion'], "default_value", text="Distortion")
                subrow.prop(props.nodes["Wave Texture"].inputs['Detail'], "default_value", text="Detail")
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.nodes["Wave Texture"].inputs['Detail Scale'], "default_value", text="Detail Scale")
                subrow.prop(props.nodes["Wave Texture"].inputs['Detail Roughness'], "default_value", text="Detail Roughness")
                col_anim[anim].label(text="Wave Curve Shape")
                col_anim[anim].template_curve_mapping(props.nodes['Float Curve'], "mapping")
                col_anim[anim].separator()
            if anim=='color_flow' and switch:
                props = bpy.data.node_groups['Color Flow Anim.Local']
                row = col_anim[anim].row(align=True)
                row.label(text="Settings For: ")
                row.prop(self, "render_type", expand=True)
                col_anim[anim].separator()
                render_type = self.render_type
                row = col_anim[anim].row(align=True)
                row.label(text="Effect Range: ")
                row.prop(props.nodes[f'{render_type} Range Start'], "integer", text="Start")
                row.prop(props.nodes[f'{render_type} Range End'], "integer", text="End")
                row = col_anim[anim].row(align=True)
                row.prop(props.nodes[f'{render_type} Start Frame'], "integer", text="Start Frame")
                row.prop(props.nodes[f'{render_type} Anim Length'], "integer", text="Anim Length")
                row = col_anim[anim].row(align=True)
                row.prop(props.nodes[f'{render_type} Flow Length'], "integer", text="Flow Length")
                row.prop(props.nodes[f'{render_type} Flow Speed'].outputs['Value'], "default_value", text="Flow Speed")
                row = col_anim[anim].row(align=True)
                row.prop(props.nodes[f'{render_type} Flow Radius'].outputs['Value'], "default_value", text="Flow Radius")
                row.prop(props.nodes[f'{render_type} Flow Color Strength'].outputs['Value'], "default_value", text="Flow Color Strength")
                row = col_anim[anim].row(align=True)
                row.prop(props.nodes[f'{render_type} Flow Offset'].inputs['Menu'], "default_value", text="Flow Offset")
                row.prop(props.nodes[f'{render_type} Local Flow'], "boolean", text="Local Flow")
                offset_type = props.nodes[f'{render_type} Flow Offset'].inputs['Menu'].default_value
                if offset_type == "Normal":
                    col_anim[anim].prop(props.nodes[f'{render_type} Flow Offset Normal'].outputs['Value'], "default_value", text="Flow Offset")
                else:
                    col_anim[anim].prop(props.nodes[f'{render_type} Flow Offset Vector'], "vector", text="Flow Offset")
                row = col_anim[anim].row(align=True)
                row.prop(props.nodes[f'{render_type} Reverse Flow'], "boolean", text="Reverse Flow")
                row.prop(props.nodes[f'{render_type} Reverse Color'], "boolean", text="Reverse Color")
                col_anim[anim].label(text="Color Flow Anim Curve")
                col_anim[anim].template_curve_mapping(props.nodes[f'{render_type} Float Curve'], "mapping")
                col_anim[anim].prop(props.nodes[f'{render_type} Change Flow Color'], "boolean", text="Change Flow Color")
                if props.nodes[f'{render_type} Change Flow Color'].boolean:
                    col_anim[anim].template_color_ramp(props.nodes[f'{render_type} Color Ramp'], "color_ramp")
                    row = col_anim[anim].row(align=True)
                    row.prop(props.nodes[f'{render_type} Flow Color Direction'].inputs['Menu'], "default_value", text="Color Direction")
                    row.prop(props.nodes[f'{render_type} Flow Style'].inputs['Menu'], "default_value", text="Flow Style")
                row = col_anim[anim].row(align=True)
                row.prop(props.nodes[f'{render_type} Spark Particles'], "boolean", text="Spark Particles")
                if props.nodes[f'{render_type} Spark Particles'].boolean:
                    row.prop(props.nodes[f'{render_type} Particle Source'].inputs['Menu'], "default_value", text="Particle Source")
                    col_anim[anim].prop(props.nodes[f'{render_type} Particle Instancing Probability'].outputs['Value'], "default_value", text="Particle Instancing Probability")
                    row = col_anim[anim].row(align=True)
                    row.prop(props.nodes[f'{render_type} Particle Lifetime'], "integer", text="Particle Lifetime")
                    row.prop(props.nodes[f'{render_type} Particle Color Strength'].outputs['Value'], "default_value", text="Particle Color Strength")
                    row = col_anim[anim].row(align=True)
                    row.prop(props.nodes[f'{render_type} Resample Flow Curve'], "boolean", text="Resample Flow Curve")
                    if props.nodes[f'{render_type} Resample Flow Curve'].boolean:
                        row.prop(props.nodes[f'{render_type} Resample Count'], "integer", text="Resample Count")
                    row = col_anim[anim].row(align=True)
                    row.prop(props.nodes[f'{render_type} Particle Radius Min'].outputs['Value'], "default_value", text="Particle Radius Min")
                    row.prop(props.nodes[f'{render_type} Particle Radius Max'].outputs['Value'], "default_value", text="Particle Radius Max")
                    row = col_anim[anim].row(align=True)
                    col = row.column(align=True)
                    col.prop(props.nodes[f'{render_type} Particle Speed Min'], "vector", text="Particle Speed Min")
                    col = row.column(align=True)
                    col.prop(props.nodes[f'{render_type} Particle Speed Max'], "vector", text="Particle Speed Max")
                    row = col_anim[anim].row(align=True)
                    row.prop(props.nodes[f'{render_type} Randomness'], "boolean", text="Speed Randomness")
                    row.prop(props.nodes[f'{render_type} Seed'], "integer", text="Seed")
                    row = col_anim[anim].row(align=True)
                    row.prop(props.nodes[f'{render_type} Particle to Curve'], "boolean", text="Particle to Curve")
                    col_anim[anim].separator()
            if anim=='flow_anim' and switch:
                props = bpy.data.node_groups['Edge Flow Anim.Local']
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.nodes['Bounding Box'], "boolean", text="Bounding Box")
                subrow.prop(props.nodes['Closed Path'].inputs['Switch'], "default_value", text="Closed Path?")
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.nodes['Reverse Flow'], "boolean", text="Reverse")
                subrow.prop(props.nodes['Subdivide Curve'].inputs['Cuts'], "default_value", text="Subdivide")
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.nodes['Start Frame'], "integer", text="Start Frame")
                subrow.prop(props.nodes['End Frame'], "integer", text="End Length")
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.nodes['Cycle Length'], "integer", text="Cycle Length")
                subrow.prop(props.nodes['Flow Length'].outputs['Value'], "default_value", text="Flow Length")
                subrow = col_anim[anim].row(align=True)
                subrow.prop(props.nodes['Scale'].outputs['Value'], "default_value", text="Scale")
                subrow.prop(props.nodes['Edge Select'], "integer", text="Edge Selection")
                if props.nodes['Bounding Box'].boolean:
                    subrow = col_anim[anim].row(align=True)
                    subrow.prop(props.nodes['BBOX Width Scale'].outputs['Value'], "default_value", text="BBox Width")
                    subrow.prop(props.nodes['BBOX Height Scale'].outputs['Value'], "default_value", text="BBox Height")
                col_anim[anim].template_color_ramp(props.nodes['Color Ramp'], "color_ramp", expand=True)
                col_anim[anim].prop(props.nodes['Color Strength'].inputs['Value'], "default_value", text="Color Strength")
                col_anim[anim].label(text="Edge Flow Curve Shape")
                col_anim[anim].template_curve_mapping(props.nodes['Float Curve'], "mapping")
                col_anim[anim].separator()
            if anim=='transform' and switch:
                props = bpy.data.node_groups['Transform.Local']
                nodes = [props.nodes['Rotate Instances'], props.nodes['Translate Instances'], props.nodes['Scale Instances']]
                for i, node in enumerate(nodes):
                    if i>0:
                        col_anim[anim].separator()
                        col_anim[anim].separator()
                    split = col_anim[anim].split(factor=0.5)
                    for socket in node.inputs[2:]:
                        if socket.name == 'Local Space' or socket.name == 'Translation':
                            col_anim[anim].prop(socket, "default_value", text=socket.name)
                        else:
                            split.prop(socket, "default_value", text=socket.name)
                col_anim[anim].separator()
            if anim=='update_font' and switch:
                formula_props = context.scene.math_anim_formula_props
                col_anim[anim].template_ID(data=formula_props, property='formula_font', open="font.open", unlink="font.unlink", text="")
                col_anim[anim].separator()

class MATH_OT_DelIndivAnim(bpy.types.Operator):
    bl_idname = "math_anim.del_indiv_anim"
    bl_label = "Delete individual's anims"
    bl_description = "Delete individual's anims"
    bl_options = {'REGISTER', 'UNDO'}

    node_tree_name: bpy.props.StringProperty(default="")
    anim_type: bpy.props.StringProperty(default="")

    def execute(self, context):
        anim_type = self.anim_type
        node_tree = bpy.data.node_groups[self.node_tree_name]
        anim_nodes = vb.formula_anim_nodes['indiv_anim'][anim_type][self.node_tree_name]
        curve_anim_setting = context.scene.math_anim_curve_gen_settings
        if anim_type == 'run_number':
            for node in anim_nodes:
                node_to_remove = node_tree.nodes.get(node.name)
                node_name = node.name
                if node_to_remove:
                    node_tree.nodes.remove(node)
                vb.formula_anim_nodes['indiv_anim'][anim_type][self.node_tree_name].remove(node)
                if len(vb.formula_anim_nodes['indiv_anim'][anim_type][self.node_tree_name]) == 0:
                    vb.formula_anim_nodes['indiv_anim'][anim_type].pop(self.node_tree_name, None)
                animsetting_status_reset(context, [f'{self.node_tree_name}.{node_name}'])
        elif anim_type == 'wave_anim' or anim_type == 'flow_anim':
            for item in anim_nodes:
                for node in item:
                    node_to_remove = node_tree.nodes.get(node.name)
                    if node_to_remove:
                        p_socket = node_to_remove.inputs[0].links[0].from_socket
                        n_socket = node_to_remove.outputs[0].links[0].to_socket
                        node_group = node_to_remove.node_tree
                        del_curve_preset(curve_anim_setting, node_to_remove.node_tree.nodes['Float Curve'])
                        node_tree.nodes.remove(node_to_remove)
                        if anim_type != 'flow_anim':
                            node_tree.links.new(p_socket, n_socket)
                        if node_group:
                            if node_group.users==0:
                                bpy.data.node_groups.remove(node_group)
                            elif node_group.use_fake_user and node_group.users==1:
                                node_group.use_fake_user = False
                                bpy.data.node_groups.remove(node_group)
                vb.formula_anim_nodes['indiv_anim'][anim_type][self.node_tree_name].remove(item)
                if len(vb.formula_anim_nodes['indiv_anim'][anim_type][self.node_tree_name]) == 0:
                    vb.formula_anim_nodes['indiv_anim'][anim_type].pop(self.node_tree_name, None)
                animsetting_status_reset(context, [item[0].name])
        elif anim_type == 'color_flow':
            for node in anim_nodes:
                key_name = node.name
                node_to_remove = node
                if node_to_remove:
                    p1_socket = node_to_remove.inputs['Grease Pencil'].links[0].from_socket
                    p2_socket = node_to_remove.inputs['Mesh'].links[0].from_socket
                    n1_socket = node_to_remove.outputs['Grease Pencil'].links[0].to_socket
                    n2_socket = node_to_remove.outputs['Mesh'].links[0].to_socket
                    node_group = node_to_remove.node_tree
                    parent_group = node.id_data
                    del_curve_preset(curve_anim_setting, node_to_remove.node_tree.nodes['GP Float Curve'])
                    del_curve_preset(curve_anim_setting, node_to_remove.node_tree.nodes['Mesh Float Curve'])
                    parent_group.nodes.remove(node_to_remove)
                    parent_group.links.new(p1_socket, n1_socket)
                    parent_group.links.new(p2_socket, n2_socket)
                    if node_group:
                        if node_group.users==0:
                            bpy.data.node_groups.remove(node_group)
                        elif node_group.use_fake_user and node_group.users==1:
                            node_group.use_fake_user = False
                            bpy.data.node_groups.remove(node_group)
                vb.formula_anim_nodes['indiv_anim'][anim_type][self.node_tree_name].remove(node)
                if len(vb.formula_anim_nodes['indiv_anim'][anim_type][self.node_tree_name]) == 0:
                    vb.formula_anim_nodes['indiv_anim'][anim_type].pop(self.node_tree_name, None)
                animsetting_status_reset(context, [key_name])
        else:
            for node in anim_nodes:
                node_to_remove = node_tree.nodes.get(node.name)
                if node_to_remove:
                    if anim_type in ["writing_anim", "grow_anim", "transform_anim"]:
                        if anim_type == "transform_anim":
                            del_curve_preset(curve_anim_setting, node_to_remove.node_tree.nodes['Rotate Anim Curve'])
                            del_curve_preset(curve_anim_setting, node_to_remove.node_tree.nodes['Offset Anim Curve'])
                            del_curve_preset(curve_anim_setting, node_to_remove.node_tree.nodes['Scale Anim Curve'])
                        else:
                            del_curve_preset(curve_anim_setting, node_to_remove.node_tree.nodes['Float Curve'])
                    p_socket = node_to_remove.inputs[0].links[0].from_socket
                    n_socket = node_to_remove.outputs[0].links[0].to_socket
                    node_group = node_to_remove.node_tree
                    node_tree.nodes.remove(node_to_remove)
                    node_tree.links.new(p_socket, n_socket)
                    if node_group:
                        if node_group.users==0:
                            bpy.data.node_groups.remove(node_group)
                        elif node_group.use_fake_user and node_group.users==1:
                            node_group.use_fake_user = False
                            bpy.data.node_groups.remove(node_group)
                vb.formula_anim_nodes['indiv_anim'][anim_type][self.node_tree_name].remove(node)
                if len(vb.formula_anim_nodes['indiv_anim'][anim_type][self.node_tree_name]) == 0:
                    vb.formula_anim_nodes['indiv_anim'][anim_type].pop(self.node_tree_name, None)
                animsetting_status_reset(context, [node.name])

        return {'FINISHED'}

class MATH_OT_IndivSetup(bpy.types.Operator):
    bl_idname = "math_anim.indiv_setup"
    bl_label = "Add an anim"
    bl_description = "Add an anim for selected individual item"
    bl_options = {'REGISTER', 'UNDO'}

    node_path: bpy.props.StringProperty(default="") # path vb.formula_node_trees
    add_anim: bpy.props.EnumProperty(
        name = 'Add Anim',
        items = [
            ('grow_anim', 'Grow Anim', 'Add a preset grow animation for the selection node'),
            ('writing_anim', 'Writing Anim', 'Add a preset writing animation for the selection node'),
            ('color_flow', 'Color Flow Anim', 'Add a preset color flow animation for the selection node'),
            ('wave_anim', 'Wave Anim', 'Add a preset wave animation for the selection node'),
            ('flow_anim', 'Edge Flow Anim', 'Add a preset edge flow animation for the selection node'),
            ('transform_anim', 'Transform Anim', 'Add a transform animation by yourself for the selection node'),
            ('transform', 'Transform', 'Add a transform animation by yourself for the selection node'),
            ('run_number', 'Running Value', 'Change the char to a running number, insert keyframe by yourself'),
        ],
        #default = 'grow_anim',
    )
    def invoke(self, context, event):
        # prepare animgroups
        anim_groups = ['Grow Anim.Local', 'Transform Anim.Local', 'Transform.Local', 'Writing Curve Anim.Local', 'Edge Flow Anim.Local', 'Wave Anim.Local', 'Color Flow Anim.Local']
        for group_name in anim_groups:
            if bpy.data.node_groups.get(group_name) is None:
                import_anim_nodegroups([group_name])
                bpy.data.node_groups[group_name].use_fake_user = True
        if 'indiv_anim' not in vb.formula_anim_nodes:
            vb.formula_anim_nodes['indiv_anim'] = {}
            anim_type = ['grow_anim', 'wave_anim', 'writing_anim',  'color_flow', 'flow_anim', 'transform_anim', 'transform', 'run_number']
            for anim in anim_type:
                if anim not in vb.formula_anim_nodes['indiv_anim']:
                    vb.formula_anim_nodes['indiv_anim'][anim] = {} # node.name: [animnode, ...]

        return self.execute(context)

    def execute(self, context):
        if self.add_anim == 'grow_anim':
            bpy.ops.math_anim.group_setup(indiv_anim=True, grow_anim=True, node_path=self.node_path)
        elif self.add_anim == 'writing_anim':
            bpy.ops.math_anim.group_setup(indiv_anim=True, writing_anim=True, node_path=self.node_path)
        elif self.add_anim == 'color_flow':
            bpy.ops.math_anim.group_setup(indiv_anim=True, color_flow=True, node_path=self.node_path)
        elif self.add_anim == 'wave_anim':
            bpy.ops.math_anim.group_setup(indiv_anim=True, wave_anim=True, node_path=self.node_path)
        elif self.add_anim == 'flow_anim':
            bpy.ops.math_anim.group_setup(indiv_anim=True, flow_anim=True, node_path=self.node_path)
        elif self.add_anim == 'transform_anim':
            bpy.ops.math_anim.group_setup(indiv_anim=True, transform_anim=True, node_path=self.node_path)
        elif self.add_anim == 'transform':
            bpy.ops.math_anim.group_setup(indiv_anim=True, transform=True, node_path=self.node_path)
        elif self.add_anim == 'run_number':
            formula_obj = context.object
            if formula_obj.get('math_anim_obj') is None:
                self.report({'WARNING'}, "Select a formula object first.")
                return {'CANCELLED'}
            page_num = int(self.node_path.split('*.*')[0])
            node_type = self.node_path.split('*.*')[1]
            key_name = self.node_path.split('*.*')[2]
            if node_type != 'text_nodes':
                self.report({'WARNING'}, "Run Number animation only work for text.")
                return {'CANCELLED'}
            node = vb.formula_node_trees[formula_obj["math_anim_obj"]][page_num][node_type][key_name]
            if node.name in vb.formula_anim_nodes['indiv_anim']['run_number']:
                return {'FINISHED'}
            n_socket = node.node_tree.nodes['String to Curves'].inputs['String']
            node_x = n_socket.node.location.x -190
            node_y = n_socket.node.location.y - 190
            anim_node,_,_ = create_node(node.node_tree, "FunctionNodeValueToString", node_x, node_y)
            node.node_tree.links.new(anim_node.outputs['String'], n_socket)
            # setup the animation nodes
            anim_setting_status = context.scene.math_animSetting_status
            item = anim_setting_status.add()
            key_name = f"{node.name}.{anim_node.name}"
            item.name = key_name
            vb.formula_animsetting_status[key_name] = len(anim_setting_status) - 1
            vb.formula_anim_nodes['indiv_anim']['run_number'][node.name] = [anim_node]
        return {'FINISHED'}

class MATH_OT_UpdateMorphObjects(bpy.types.Operator):
    bl_idname = "math_anim.update_morph_objects"
    bl_label = "Update Morph Objects"
    bl_description = "Update objects for morph, also update layer trees, when change layer names, delete layers, add layers, need to update this"
    bl_options = {'REGISTER', 'UNDO'}

    x_labels: bpy.props.StringProperty(default="")
    y_labels: bpy.props.StringProperty(default="")
    z_labels: bpy.props.StringProperty(default="")
    x_size: bpy.props.FloatProperty(default=0.4)
    y_size: bpy.props.FloatProperty(default=0.4)
    z_size: bpy.props.FloatProperty(default=0.4)
    update_layer: bpy.props.StringProperty(default="")
    math_mode: bpy.props.StringProperty(default="")
    def execute(self, context):
        # first update all the layers to the nodetree
        # then update the morph holders
        morph_settings = context.scene.math_anim_morphSettings
        _candidates = {} # object: [layer, ...]
        _object_map = {}
        for obj in bpy.data.objects:
            if obj.get('math_anim_obj'):
                _candidates[obj["math_anim_obj"]] = []
                _object_map[obj["math_anim_obj"]] = obj
                for layer in obj.data.layers:
                    #layer.blend_mode = 'ADD'
                    _candidates[obj["math_anim_obj"]].append(layer.name)

        # update the nodetree
        vb.gpencil_layer_nodes.clear()
        for obj_name, layers in _candidates.items():
            obj = _object_map[obj_name]
            vb.gpencil_layer_nodes[obj_name] = {}
            for md in obj.modifiers:
                if 'drawer' in md.name or 'formula' in md.name or 'plotter' in md.name:
                    node_tree = md.node_group
                    vb.gpencil_layer_nodes[obj_name][obj_name] = node_tree
                    p_socket = node_tree.nodes['GP Material'].outputs['Geometry']
                    for link in p_socket.links:
                        if link.to_node.name != 'Join Geometry':
                            # remove layer nodes if the layers don't exist anymore
                            if link.to_node.name not in layers:
                                node_tree.nodes.remove(link.to_node)
                    if len(p_socket.links)==0:
                        node_tree.links.new(p_socket, node_tree.nodes['Join Geometry'].inputs['Geometry'])

                    node_x = p_socket.node.location.x + 190
                    node_y = 200
                    for link in p_socket.links:
                        if link.to_node.name != 'Join Geometry':
                            if node_y <= link.to_node.location.y:
                                node_y = link.to_node.location.y + 200
                    for layer_name in layers:
                        create_new = True
                        if node_tree.nodes.get(layer_name):
                            layer_node = node_tree.nodes[layer_name]
                            vb.gpencil_layer_nodes[obj_name][layer_name] = layer_node
                            create_new = False
                            if layer_name == self.update_layer:
                                axis_node = node_tree.nodes.get(f'{layer_name}.axis')
                                if axis_node:
                                    label_node = axis_node.node_tree.nodes.get('Axis Labels')
                                    if label_node:
                                        label_node.inputs['X Tick Labels'].default_value = self.x_labels.replace("-","\u2212").replace("pi","\u03c0")
                                        label_node.inputs['Y Tick Labels'].default_value = self.y_labels.replace("-","\u2212").replace("pi","\u03c0")
                                        label_node.inputs['Z Tick Labels'].default_value = self.z_labels.replace("-","\u2212").replace("pi","\u03c0")
                                        label_node.inputs['X Tick Label Scale'].default_value = self.x_size
                                        label_node.inputs['Y Tick Label Scale'].default_value = self.y_size
                                        label_node.inputs['Z Tick Label Scale'].default_value = self.z_size
                                        label_node.inputs['X Tick Label Offset'].default_value = (-1.0, -1.0*self.x_size, 0.0)
                                        label_node.inputs['Y Tick Label Offset'].default_value = (-0.1*self.y_size, -0.45*self.y_size, 0.0)
                                        label_node.inputs['Z Tick Label Offset'].default_value[0] = -0.1*self.z_size
                                        label_node.inputs['Polar Axis'].default_value = False
                                        label_node.inputs['Circle Scale'].default_value = 1.0
                                        if self.math_mode == 'POLARFUNCTION':
                                            label_node.inputs['X Tick Label Offset'].default_value = (-1-0.4*self.x_size, -1*self.x_size, 0.0)
                                            label_node.inputs['Circle Scale'].default_value = 1.1
                                            label_node.inputs['Polar Axis'].default_value = True
                                            label_node.inputs['Y Tick Label Offset'].default_value = (-1.05,-0.05,0.0)
                                #return {'FINISHED'}
                            continue
                        if not create_new:
                            continue
                        layer_node, node_x, node_y = create_node(node_tree, "GeometryNodeGroup",node_x, node_y, 0, 200)
                        layer_node.node_tree = bpy.data.node_groups['Layer Select'].copy()
                        layer_node.node_tree.nodes['GP Material'].node_tree = bpy.data.node_groups['GP Material'].copy()
                        layer_node.name = layer_name
                        layer_node.label = layer_name
                        layer_node.inputs['Layer Name'].default_value = layer_name
                        if 'plotting' in layer_name:
                            layer_node.node_tree.nodes['GP Material'].inputs['Use Custom Color'].default_value = True
                            if layer_name.split('.')[-1] == 'axis':
                                layer_node.inputs['Color Strength'].default_value = 2
                                color_node = layer_node.node_tree.nodes['GP Material'].node_tree.nodes['Color Ramp']
                                for element in color_node.color_ramp.elements:
                                    element.color = (0.9,0.9,0.9,1)
                                if self.x_labels or self.y_labels or self.z_labels:
                                    pp_socket = layer_node.node_tree.nodes['Separate Geometry'].outputs['Selection']
                                    nn_socket = layer_node.node_tree.nodes['GP Material'].inputs['Geometry']
                                    label_node,_,_ = create_node(layer_node.node_tree, "GeometryNodeGroup", pp_socket.node.location.x+150, pp_socket.node.location.y)
                                    label_node.node_tree = bpy.data.node_groups['Axis Labels'].copy()
                                    label_node.name = 'Axis Labels'
                                    label_node.inputs['X Tick Labels'].default_value = self.x_labels.replace("-","\u2212").replace("pi","\u03c0")
                                    label_node.inputs['Y Tick Labels'].default_value = self.y_labels.replace("-","\u2212").replace("pi","\u03c0")
                                    label_node.inputs['Z Tick Labels'].default_value = self.z_labels.replace("-","\u2212").replace("pi","\u03c0")
                                    label_node.inputs['X Tick Label Scale'].default_value = self.x_size
                                    label_node.inputs['Y Tick Label Scale'].default_value = self.y_size
                                    label_node.inputs['Z Tick Label Scale'].default_value = self.z_size
                                    label_node.inputs['X Tick Label Offset'].default_value = (-1.0, -1*self.x_size, 0.0)
                                    label_node.inputs['Y Tick Label Offset'].default_value = (-0.1*self.y_size, -0.45*self.y_size, 0.0)
                                    label_node.inputs['Z Tick Label Offset'].default_value[0] = -0.1*self.z_size
                                    label_node.inputs['Polar Axis'].default_value = False
                                    label_node.inputs['Circle Scale'].default_value = 1.0
                                    if self.math_mode == 'POLARFUNCTION':
                                        label_node.inputs['X Tick Label Offset'].default_value = (-1-0.4*self.x_size, -1*self.x_size, 0.0)
                                        label_node.inputs['Circle Scale'].default_value = 1.1
                                        label_node.inputs['Polar Axis'].default_value = True
                                        label_node.inputs['Y Tick Label Offset'].default_value = (-1.05,-0.05,0.0)
                                    layer_node.node_tree.links.new(pp_socket, label_node.inputs['Geometry'])
                                    layer_node.node_tree.links.new(label_node.outputs['Geometry'], nn_socket)
                                    layer_node.node_tree.nodes.remove(layer_node.node_tree.nodes['Transform Plotting'])
                                    hide0_check = 0
                                    if self.x_labels:
                                        hide0_check += 1
                                    if self.x_labels:
                                        hide0_check += 1
                                    if self.x_labels:
                                        hide0_check += 1
                                    if hide0_check > 1:
                                        label_node.inputs['Hide X 0'].default_value = True
                                        label_node.inputs['Hide Y 0'].default_value = True
                                        label_node.inputs['Hide Z 0'].default_value = True
                        node_tree.links.new(p_socket, layer_node.inputs['Geometry'])
                        node_tree.links.new(layer_node.outputs['Geometry'], node_tree.nodes['Join Geometry'].inputs['Geometry'])
                        if p_socket.links[0].to_node.name == 'Join Geometry':
                            node_tree.links.remove(p_socket.links[0])
                        vb.gpencil_layer_nodes[obj_name][layer_name] = layer_node
                        bpy.ops.outliner.orphans_purge() # clear unused nodegroups

        # delete objects that don't exist anymore
        _candidate_del = {} # object.name: idx
        _candidate_new = list(_candidates.keys())
        collection_len = 2
        for i, morph_obj in enumerate(morph_settings):
            if morph_obj.name not in _candidates:
                _candidate_del[morph_obj.name] = i
            else:
                _candidate_new.remove(morph_obj.name)
            if len(morph_obj.page_holder)>0 and len(morph_obj.page_holder[0].morph_collection)>0:
                collection_len = len(morph_obj.page_holder[0].morph_collection)
        for name, idx in reversed(list(_candidate_del.items())):
            morph_settings.remove(idx)

        # add layers for new objects to the morphs
        for name in _candidate_new:
            if len(_candidates[name]) > 0:
                if len(context.scene.math_anim_morph_selected_idx) == 0:
                    context.scene.math_anim_morph_selected_idx.add()
                    context.scene.math_anim_morph_selected_idx.add()
                item = morph_settings.add()
                item.name = name
                page_holder = item.page_holder
                item = page_holder.add()
                collection = item.morph_collection
                for i in range(collection_len):
                    item = collection.add()
                    morph_setting = item.morph_setting
                    for layer_name in _candidates[name]:
                        item = morph_setting.add()
                        item.inputs = layer_name
                        item.type = 'layer'
                        item.item_idx = len(morph_setting) - 1
                        item.page_idx  = 0
                        item.collection_idx  = i
                        item.obj_id  = name

        # update layers for objects already in the morphs
        # all layers put in the last page
        for obj_name, layers in _candidates.items():
            if obj_name in _candidate_new:
                continue
            if len(layers) > 0:
                for item in morph_settings:
                    if item.name == obj_name:
                        page_holder = item.page_holder
                        # first check existing and delete them
                        last_page = len(page_holder) - 1
                        exist_status = False
                        for morph_collection in page_holder[last_page].morph_collection:
                            del_idx = []
                            for morph in morph_collection.morph_setting:
                                if morph.type == 'layer':
                                    del_idx.append(morph.item_idx)
                                    exist_status = True
                            for i in del_idx[::-1]:
                                morph_collection.morph_setting.remove(i)
                        # adding again
                        if not exist_status:
                            item = page_holder.add()
                            collection = item.morph_collection
                            for i in range(collection_len):
                                item = collection.add()
                        collection = page_holder[len(page_holder)-1].morph_collection
                        for i in range(collection_len):
                            morph_setting = collection[i].morph_setting
                            for layer_name in layers:
                                item = morph_setting.add()
                                item.inputs = layer_name
                                item.type = 'layer'
                                item.item_idx = len(morph_setting) - 1
                                item.page_idx  = len(page_holder) - 1
                                item.collection_idx  = i
                                item.obj_id  = obj_name
        return {'FINISHED'}

class MATH_OT_UpdateFormulaFont(bpy.types.Operator):
    bl_idname = "math_anim.update_formula_font"
    bl_label = "Update Font"
    bl_description = "Update a math formula's font"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        formula_props = context.scene.math_anim_formula_props
        if not formula_props.formula_font:
            self.report({'WARNING'}, "Select a font first.")
            return {'CANCELLED'}
        formula_obj = context.object
        if formula_obj.get('math_anim_obj') is None:
            self.report({'WARNING'}, "Select a formula object first.")
            return {'CANCELLED'}
        if formula_obj["math_anim_obj"] in vb.formula_node_trees:
            for page_num in range(len(vb.formula_node_trees[formula_obj["math_anim_obj"]])):
                nodes = vb.formula_node_trees[formula_obj["math_anim_obj"]][page_num]
                if 'text_nodes' in nodes:
                    for node in nodes['text_nodes'].values():
                        if node.name != 'char_join_node':
                            node.node_tree.nodes['String to Curves'].inputs['Font'].default_value = formula_props.formula_font

        return {'FINISHED'}

classes = (
    MATH_OT_PATH_FormulaAddPath,
    MATH_OT_PATH_FormulaRemovePath,
    MATH_OT_CreateFormula,
    MATH_OT_AddFormulaAnim,
    MATH_OT_DelFormulaAnim,
    MATH_OT_FormulaMorphAnim,
    MATH_OT_AddMorphTarget,
    MATH_OT_DelMorphTarget,
    MATH_OT_AddMorphItem,
    MATH_OT_DelMorphItem,
    MATH_OT_GroupSetup,
    MATH_OT_DelGroupAnim,
    MATH_OT_IndivSetup,
    MATH_OT_DelIndivAnim,
    MATH_OT_UpdateMorphObjects,
    MATH_OT_UpdateFormulaFont,
)
register, unregister = bpy.utils.register_classes_factory(classes)
