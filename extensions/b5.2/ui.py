import bpy
from .properties import MATH_ANIM_Formula_Properties, MATH_ANIM_MorphAnimSettings, MATH_ANIM_IndividualSettings
from . import variables as vb #import vb.formula_node_trees
from .operations import animsetting_status_reset
from .curve_anim_presets import draw_curve_ui

def update_panel_category(self, context):
    bpy.utils.unregister_class(MATH_ANIM_PT_main_panel)
    prefs = bpy.context.preferences.addons[__package__].preferences
    MATH_ANIM_PT_main_panel.bl_category = prefs.panel_category
    bpy.utils.register_class(MATH_ANIM_PT_main_panel)

class MATH_ANIM_PATH_UL_List(bpy.types.UIList):
    """Custom UI List with checkboxes for multi-selection"""
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if item:
            row = layout.row(align=True)
            row.prop(item, "selected", text="")  # Checkbox for selection
            if item.bl_rna.properties["path"].name == "Optex code":
                if item.math:
                    row.prop(item, "path", text="", placeholder="optex input")
                    row.prop(item, "math", text="", icon="FONTPREVIEW")
                else:
                    split = row.split(factor=0.8, align=True)
                    left = split.row(align=True)
                    left.prop(item, "path", text="", placeholder="optex input")
                    left.prop(item, "math", text="", icon="FONTPREVIEW")
                    right = split.row(align=True)
                    right.prop(item, "font", text="", icon="FILE_FONT")
            elif item.bl_rna.properties["path"].name == "Typst code":
                split = row.split(factor=0.8, align=True)
                left = split.row(align=True)
                left.prop(item, "path", text="", placeholder="typst input")
                left.prop(item, "math", text="", icon="FONTPREVIEW")
                right = split.row(align=True)
                right.prop(item, "font", text="", icon="FILE_FONT")
            elif item.bl_rna.properties["path"].name == "File Path":
                if self.list_id == "funcdata_filelist":
                    split = row.split(factor=0.8)
                    split.label(text=item.path, icon="FILE_VOLUME")
                    split.prop(item, "delim", text="sep")
                else:
                    row.label(text=item.path, icon="FILE")
            else:
                row.label(text=item.path, icon="FILE")

class MATH_ANIM_PT_main_panel(bpy.types.Panel):
    bl_label = "Math Anim"
    bl_idname = "MATH_ANIM_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = True  # False for no animation.

        # render settings
        header, panel = layout.panel("math_anim_render_settings", default_closed=True)
        header.label(text="Render Settings")
        if panel:
            row = panel.row(align=True)
            row.operator("math_anim.add_bloom", text="Add Bloom")
            row.prop(context.scene.render, "film_transparent", toggle=True)
            row.prop(context.scene.eevee, "use_raytracing", text="Raytracing", toggle=True)
            row = panel.row(align=True)
            row.prop(context.scene.eevee, "taa_render_samples", text="Samples")
            row.prop(context.scene.eevee, "light_threshold", text="Light Threshold")
            row = panel.row(align=True)
            row.operator("math_anim.add_bg_grid", text="Add Background Grid")
            row.operator("math_anim.del_bg_grid", text="Remove Background Grid")
            for group_name, node_name in  vb.bg_grid_holder.items():
                node_group = bpy.data.node_groups.get(group_name)
                if node_group:
                    node = node_group.nodes.get(node_name)
                    if node:
                        panel.template_node_inputs(node)
        # plotter ui
        plotter_props = context.scene.math_anim_plotter_props
        anim_setting_status = context.scene.math_animSetting_status
        curve_anim_settings = context.scene.math_anim_curve_gen_settings
        header, panel = layout.panel("math_anim_plotter", default_closed=True)
        header.label(text="Function Plotter")
        if panel:
            panel.prop(plotter_props, "math_mode")
            # function
            if plotter_props.math_mode == 'PARAFUNCTION':
                panel.prop(plotter_props, "function_x")
                panel.prop(plotter_props, "function_y")
                panel.prop(plotter_props, "function_z")
            elif plotter_props.math_mode == 'POLARFUNCTION':
                panel.prop(plotter_props, "polar_function")
            elif plotter_props.math_mode == 'EFUNCTION':
                panel.prop(plotter_props, "math_function")
            elif plotter_props.math_mode == 'IFUNCTION':
                panel.prop(plotter_props, "implicit_function")
            elif plotter_props.math_mode == 'ODEFUNCTION':
                panel.prop(plotter_props, "ode_function_x")
                panel.prop(plotter_props, "ode_function_y")
                panel.prop(plotter_props, "ode_function_z")
                if "g_i[N]" in f"{plotter_props.ode_function_x} {plotter_props.ode_function_y} {plotter_props.ode_function_z}":
                    panel.prop(plotter_props, "ds_hybrid_model")
            # variables
            reserved_params = []
            if plotter_props.math_mode == 'FUNCDATA':
                row = panel.row()
                col = row.column()
                funcdata_paths = context.scene.math_anim_func_datafile
                # box for the path list
                col.template_list("MATH_ANIM_PATH_UL_List", "funcdata_filelist", funcdata_paths, "paths", funcdata_paths, "active_index")
                # buttons on the right
                col = row.column(align=True)
                col.operator("math_anim.funcdata_addpath", text="", icon="ADD")
                col.operator("math_anim.funcdata_removepath", text="", icon="REMOVE")
            elif plotter_props.math_mode == 'ODEFUNCTION':
                panel.prop(plotter_props, "ode_solver")
                if plotter_props.ode_solver == 'DIFFSOL':
                    row = panel.row(align=True)
                    row.prop(plotter_props, "ds_solver_type", text="Solver Method")
                    row.prop(plotter_props, "ds_linear_solver_type", text="Linear Solver Type")
                    row = panel.row(align=True)
                    row.prop(plotter_props, "ds_matrix_type", text="Matrix Type")
                    row.prop(plotter_props, "ds_use_dt", text="Use Time Step")
                    row = panel.row(align=True)
                    row.prop(plotter_props, "ds_has_stop", text="Add Stop")
                    if plotter_props.ds_has_stop:
                        row.prop(plotter_props, "ds_stop_function", text="Stop Function")
                        panel.prop(plotter_props, "ds_reset_function", text="Update State at Stopped")
                # for time span
                prop_ids = [f"math_param_t0", f"math_param_t1", f"math_param_dt"]
                reserved_params.extend(prop_ids)
                row = panel.row(align=True)
                for prop_id in prop_ids:
                    if hasattr(context.scene, prop_id):
                        row.prop(context.scene, f"{prop_id}")
                # for initial condition
                row = panel.row(align=True)
                for var in sorted(vb.VARS_USED):
                    if var != 't':
                        prop_id = f"math_param_{var}0"
                        if hasattr(context.scene, prop_id):
                            reserved_params.append(prop_id)
                            row.prop(context.scene, f"{prop_id}")
                row = panel.row(align=True)
                row.prop(plotter_props, "plot_branch", text="Plot Branch")
                col = row.column(align=True)
                col.prop(plotter_props, "branch_axis", text="Branch")
                if not plotter_props.plot_branch:
                    col.enabled = False
                if plotter_props.branch_axis == 'compose':
                    col = panel.row(align=True)
                    col.prop(plotter_props, "branch_compose", text="Branch Compose")
                    if not plotter_props.plot_branch:
                        col.enabled = False
            elif plotter_props.math_mode == 'IFUNCTION':
                # for step and n_steps
                panel.label(text="Solution Tracer")
                prop_ids = [f"math_param_step", f"math_param_n_steps"]
                reserved_params.extend(prop_ids)
                row = panel.row(align=True)
                for prop_id in prop_ids:
                    if hasattr(context.scene, prop_id):
                        row.prop(context.scene, f"{prop_id}")
                # for search domain
                panel.label(text="Search Domain")
                for var in vb.VARS_USED:
                    prop_ids = [f"math_var_{var}_min", f"math_var_{var}_max", f"math_var_{var}_resolution"]
                    row = panel.row(align=True)
                    for prop_id in prop_ids:
                        if hasattr(context.scene, prop_id):
                            row.prop(context.scene, f"{prop_id}")
            else:
                plot_idx = 0
                for var in vb.VARS_USED:
                    if plotter_props.math_mode=="EFUNCTION":
                        if plot_idx == 0:
                            panel.prop(plotter_props, "self_iteration")
                            reserved_params.extend([f"math_param_n_iter", f"math_param_iter_init"])
                            if plotter_props.self_iteration:
                                row = panel.row(align=True)
                                row.prop(context.scene, "math_param_n_iter", text="Iterations")
                                row.prop(context.scene, "math_param_iter_init", text="Initial Value")
                        plot_idx += 1
                    prop_ids = [f"math_var_{var}_min", f"math_var_{var}_max", f"math_var_{var}_resolution"]
                    for prop_id in prop_ids:
                        if hasattr(context.scene, prop_id):
                            panel.prop(context.scene, f"{prop_id}")
                if plotter_props.math_mode == 'PARAFUNCTION':
                    row = panel.row(align=True)
                    row.prop(plotter_props, "plot_branch", text="Plot Branch")
                    col = row.column(align=True)
                    col.prop(plotter_props, "branch_axis", text="Branch")
                    if not plotter_props.plot_branch:
                        col.enabled = False
            panel.separator()
            plot_idx = 0
            for param in vb.DYNAMIC_PARAMS:
                prop_id = vb.DYNAMIC_PARAMS[param]
                if prop_id not in reserved_params and hasattr(context.scene, prop_id):
                    if plot_idx == 0:
                        panel.label(text="Parameters")
                    panel.prop(context.scene, prop_id)
                    plot_idx += 1

            panel.separator()
            gpobjects = context.scene.math_anim_gpobjects
            gplayers  = context.scene.math_anim_gplayers
            split = panel.split(factor=0.7)
            split.prop(gpobjects, "gp_object", text='Plotter Obj', icon='OUTLINER_OB_GREASEPENCIL')
            op = split.operator("math_anim.add_gp_obj", text="Add Plotter", icon='ADD')
            use_data_file = False
            if plotter_props.math_mode == 'FUNCDATA':
                use_data_file = True
            op.obj_name = "Plotter"
            op.geomd_category = 'PLOTTER'
            op = panel.operator("math_anim.create_plot", text="Add Plotting (new layer)", icon='FCURVE')
            op.update_tag = False
            op.use_data_file = use_data_file
            op = panel.operator("math_anim.create_plot", text="Update Plotting (current layer)", icon='FCURVE')
            op.update_tag = True
            op.update_current_layer = True
            op.use_data_file = use_data_file
            panel.separator()
            row = panel.row(align=True)
            row.prop(gplayers, "gp_layer", text='Layer', icon='OUTLINER_DATA_GP_LAYER')
            op = row.operator_menu_enum("math_anim.add_gp_anim", "add_anim")
            op.track_tag = 'plotter_anim'
            gp_obj = bpy.data.objects.get(gpobjects.gp_object)
            if gp_obj and gp_obj["math_anim_obj"]:
                gp_layer = gp_obj.data.layers.get(gplayers.gp_layer)
                if gp_layer:
                    for var_name in vb.plot_variable_tracking['plot']:
                        maths =  vb.plot_variable_tracking['plot'][var_name].get((gp_obj, gp_layer), {})
                        if maths:
                            panel.prop(plotter_props, "plot_ctl")
                            if plotter_props.plot_ctl:
                                row = panel.row(align=True)
                                row.enabled = False
                                row.prop(plotter_props, "plot_func", text=f"{maths['functions'][0]}")
                                reserved_params = []
                                if maths['functions'][0] == 'ODEFUNCTION':
                                    if maths['plot_branch']:
                                        row = panel.row(align=True)
                                        row.enabled = False
                                        row.prop(plotter_props, "branch_plot", text="Branch")
                                        if maths['branch_axis'] == 'compose':
                                            row.prop(plotter_props, "branch_compose", text="Branch Compose")
                                    ode_setting = context.scene.math_anim_ode_settings
                                    row = panel.row(align=True)
                                    col = row.column(align=True)
                                    col.enabled = False
                                    col.prop(ode_setting, "ode_solver")
                                    if ode_setting.ode_solver == 'DIFFSOL':
                                        row.prop(ode_setting, "ds_use_dt", text="Use Time Step")
                                    # for time span
                                    prop_ids = ["ode_t0", "ode_t1", "ode_dt"]
                                    reserved_params.extend(["math_param_t0", "math_param_t1", "math_param_dt"])
                                    row = panel.row(align=True)
                                    for prop_id in prop_ids:
                                        row.prop(ode_setting, f"{prop_id}")
                                    # for initial condition
                                    row = panel.row(align=True)
                                    for var in sorted(maths['vars']):
                                        if var != 't':
                                            prop_id = f"math_param_{var}0"
                                            if hasattr(context.scene, prop_id):
                                                reserved_params.append(prop_id)
                                                row.prop(context.scene, f"{prop_id}")
                                elif maths['functions'][0] == 'IFUNCTION':
                                    # for step and n_steps
                                    panel.label(text="Solution Tracer")
                                    prop_ids = [f"math_param_step", f"math_param_n_steps"]
                                    reserved_params.extend(prop_ids)
                                    row = panel.row(align=True)
                                    for prop_id in prop_ids:
                                        if hasattr(context.scene, prop_id):
                                            row.prop(context.scene, f"{prop_id}")
                                    # for search domain
                                    panel.label(text="Search Domain")
                                    for var in maths['vars']:
                                        prop_ids = [f"math_var_{var}_min", f"math_var_{var}_max", f"math_var_{var}_resolution"]
                                        row = panel.row(align=True)
                                        for prop_id in prop_ids:
                                            if hasattr(context.scene, prop_id):
                                                row.prop(context.scene, f"{prop_id}")
                                else:
                                    if maths['functions'][0] == 'PARAFUNCTION':
                                        if maths['plot_branch']:
                                            row = panel.row(align=True)
                                            row.enabled = False
                                            row.prop(plotter_props, "branch_plot", text="Branch")
                                            if maths['branch_axis'] == 'compose':
                                                row.prop(plotter_props, "branch_compose", text="Branch Compose")
                                    for var in maths['vars']:
                                        prop_ids = [f"math_var_{var}_min", f"math_var_{var}_max", f"math_var_{var}_resolution"]
                                        for prop_id in prop_ids:
                                            if hasattr(context.scene, prop_id):
                                                panel.prop(context.scene, f"{prop_id}")
                                if len(maths['params']) > 0:
                                    panel.separator()
                                    panel.label(text="Parameters")
                                    for param in sorted(maths['params']):
                                        prop_id = f'math_param_{param}'
                                        if prop_id not in reserved_params and hasattr(context.scene, prop_id):
                                            panel.prop(context.scene, prop_id)
                                panel.separator()
                                row = panel.row(align=True)
                                col1 = row.column()
                                col2 = row.column()
                                col3 = row.column()
                                col1.prop(plotter_props, "plot_translation", text="Translation")
                                col2.prop(plotter_props, "plot_rotation", text="Rotation")
                                col3.prop(plotter_props, "plot_scale", text="Scale")
                            break

            panel.separator()
            row = panel.row(align=True)
            row.prop_enum(gpobjects, "settings", "OBJECT")
            row.prop_enum(gpobjects, "settings", "LAYER")
            row.prop_enum(gpobjects, "settings", "LAYER_ANIM")
            if gp_obj and (gpobjects.settings == 'OBJECT' or gpobjects.settings == 'LAYER'):
                props, props2 = None, None
                if gpobjects.settings == 'OBJECT':
                    if gp_obj["math_anim_obj"] in vb.gpencil_layer_nodes and gp_obj["math_anim_obj"] in vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]]:
                        props = vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]][gp_obj["math_anim_obj"]].nodes['GP Material']
                else:
                    gp_layer = gp_obj.data.layers.get(gplayers.gp_layer)
                    if gp_layer and gp_obj["math_anim_obj"] in vb.gpencil_layer_nodes and gp_layer.name in vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]]:
                        props = vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]][gp_layer.name].node_tree.nodes['GP Material']
                        props2 = vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]][gp_layer.name]
                if props:
                    if gpobjects.settings == 'OBJECT':
                        panel.prop(props.inputs['Color Strength'], 'default_value', text="Color Strength")
                    else:
                        if props2.node_tree.users > 1:
                            if 'morph_anim' in vb.formula_anim_nodes and len(vb.formula_anim_nodes['morph_anim'])>0:
                                found = False
                                for index, morph_chain in enumerate(vb.formula_anim_nodes['morph_anim']):
                                    for key, morph_list in morph_chain.items():
                                        for morph_node, mute_nodes, morph_setting in morph_list:
                                            source_node = mute_nodes[0]
                                            morph_node = source_node.node_tree.nodes.get(f'{props2.node_tree.name}.Morph')
                                            if morph_node:
                                                panel.prop(morph_node.inputs['Color Strength'], 'default_value', text="Color Strength")
                                                found = True
                                                break
                                        if found:
                                            break
                                    if found:
                                        break
                        else:
                            panel.prop(gp_layer, 'use_lights', text="Interact with Lights")
                            panel.prop(props2.inputs['Color Strength'], 'default_value', text="Color Strength")
                        panel.prop(props.inputs['Material Index'], 'default_value', text="Material Index")
                    panel.prop(props.inputs['Use Custom Radius'], 'default_value', text="Use Custom Radius")
                    panel.prop(props.inputs['Radius'], 'default_value', text="Curve Radius")
                    if props2:
                        panel.prop(props2.inputs['As Points'], 'default_value', text="As Points")
                    panel.prop(props.inputs['Use Custom Color'], 'default_value', text="Use Custom Color")
                    if props.inputs['Use Custom Color'].default_value:
                        panel.template_color_ramp(props.node_tree.nodes['Color Ramp'], 'color_ramp')
                        panel.prop(props.inputs['Color Direction'], 'default_value', text="Color Direction")
                    panel.prop(props.inputs['Use Custom Fill'], 'default_value', text="Use Custom Fill")
                    if props.inputs['Use Custom Fill'].default_value:
                        panel.template_color_ramp(props.node_tree.nodes['Fill Color Ramp'], 'color_ramp')
                        panel.prop(props.inputs['Fill Direction'], 'default_value', text="Fill Direction")
            elif gp_obj and gpobjects.settings == 'LAYER_ANIM':
                gp_layer = gp_obj.data.layers.get(gplayers.gp_layer)
                if gp_layer:
                    anim_types = ['grow_anim', 'writing_anim', 'light_flow', 'wave_anim', 'flow_anim', 'transform_anim', 'transform', 'add_snapshot', 'curve_normal_tangent']
                    for anim_type in anim_types:
                        if 'plotter_anim' in vb.formula_anim_nodes and gp_obj["math_anim_obj"] in vb.formula_anim_nodes['plotter_anim'] and gp_layer.name in vb.formula_anim_nodes['plotter_anim'][gp_obj["math_anim_obj"]] and anim_type in vb.formula_anim_nodes['plotter_anim'][gp_obj["math_anim_obj"]][gp_layer.name]:
                            anim_nodes = vb.formula_anim_nodes['plotter_anim'][gp_obj["math_anim_obj"]][gp_layer.name][anim_type]
                            if anim_type == 'grow_anim':
                                for anim_node in anim_nodes:
                                    if anim_node.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, anim_node.name)
                                        continue
                                    props = anim_node
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Grow Anim')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{anim_node.id_data.name}**{anim_node.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'plotter_anim'
                                    if status.hide:
                                        continue
                                    row = panel.row(align=True)
                                    row.label(text="Effect Range: ")
                                    row.prop(props.inputs['Range Start'], "default_value", text="Range Start")
                                    row.prop(props.inputs['Range End'], "default_value", text="Range End")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Start Frame'], "default_value", text="Start Frame")
                                    row.prop(props.inputs['Anim Length'], "default_value", text="Anim Length")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Local'], "default_value", text="Local Grow")
                                    row.prop(props.inputs['Reverse'], "default_value", text="Reverse Grow")
                                    panel.prop(props.inputs['Center'].links[0].from_node.inputs[1], "default_value", text="Grow Center")
                                    panel.label(text="Grow Anim Curve")
                                    panel.template_curve_mapping(props.node_tree.nodes['Float Curve'], "mapping")
                                    subheader, subpanel = panel.panel(f"{props.node_tree.name} preset curves", default_closed=True)
                                    subheader.label(text="Preset Curves")
                                    if subpanel:
                                        curve_node = props.node_tree.nodes['Float Curve']
                                        curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                        if curve_setting:
                                            draw_curve_ui(subpanel, curve_setting)
                                    panel.separator()
                                continue
                            elif anim_type == 'writing_anim':
                                for anim_node in anim_nodes:
                                    if anim_node.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, anim_node.name)
                                        continue
                                    props = anim_node
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Writing Anim')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{anim_node.id_data.name}**{anim_node.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'plotter_anim'
                                    if status.hide:
                                        continue
                                    row = panel.row(align=True)
                                    row.label(text="Effect Range: ")
                                    row.prop(props.inputs['Range Start'], "default_value", text="Range Start")
                                    row.prop(props.inputs['Range End'], "default_value", text="Range End")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Start Frame'], "default_value", text="Start Frame")
                                    row.prop(props.inputs['Anim Length'], "default_value", text="Anim Length")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Local'], "default_value", text="Local Writing")
                                    row.prop(props.inputs['Reverse'], "default_value", text="Reverse Writing")
                                    panel.label(text="Writing Anim Curve")
                                    panel.template_curve_mapping(props.node_tree.nodes['Float Curve'], "mapping")
                                    subheader, subpanel = panel.panel(f"{props.node_tree.name} preset curves", default_closed=True)
                                    subheader.label(text="Preset Curves")
                                    if subpanel:
                                        curve_node = props.node_tree.nodes['Float Curve']
                                        curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                        if curve_setting:
                                            draw_curve_ui(subpanel, curve_setting)
                                    ctl_switch = 'Local' if props.inputs['Local'].default_value else 'Global'
                                    panel.prop(props.inputs[f'Add {ctl_switch} Writing Symbol'], "default_value", text="Add Writing Symbol")
                                    if props.inputs[f'Add {ctl_switch} Writing Symbol'].default_value:
                                        panel.template_ID(data=props.node_tree.nodes[f'{ctl_switch} Writing Symbol'].inputs["Font"], property="default_value", open="font.open", unlink="font.unlink", text="Symbol Font")
                                        panel.prop(props.node_tree.nodes[f'{ctl_switch} Writing Symbol'].inputs['String'], "default_value", text="Symbol")
                                        panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Radius'], "default_value", text="Symbol Line Radius")
                                        panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Color'], "default_value", text="Symbol Color")
                                        panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Color Strength'], "default_value", text="Symbol Color Strength")
                                        panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Translation'], "default_value", text="Symbol Translation")
                                        panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Rotation'], "default_value", text="Symbol Rotation")
                                        panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Scale'], "default_value", text="Symbol Scale")
                                    panel.separator()
                                continue
                            elif anim_type == 'light_flow':
                                for anim_node in anim_nodes:
                                    if anim_node.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, anim_node.name)
                                        continue
                                    props = anim_node
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Light Flow Anim')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{anim_node.id_data.name}**{anim_node.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'plotter_anim'
                                    if status.hide:
                                        continue
                                    row = panel.row(align=True)
                                    row.label(text="Effect Range: ")
                                    row.prop(props.inputs['Range Start'], "default_value", text="Start")
                                    row.prop(props.inputs['Range End'], "default_value", text="End")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Start Frame'], "default_value", text="Start Frame")
                                    row.prop(props.inputs['Anim Length'], "default_value", text="Anim Length")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Flow Length'], "default_value", text="Flow Length")
                                    row.prop(props.inputs['Flow Speed'], "default_value", text="Flow Speed")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Flow Radius Multiplier'], "default_value", text="Flow Radius Multiplier")
                                    row.prop(props.inputs['Flow Light Strength'], "default_value", text="Flow Light Strength")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Flow Offset'], "default_value", text="Flow Offset")
                                    row.prop(props.inputs['Reverse Flow'], "default_value", text="Reverse Flow")
                                    if props.inputs['Flow Offset'].default_value == "Normal":
                                        panel.prop(props.inputs['Flow Offset Normal'], "default_value", text="Flow Offset")
                                    else:
                                        panel.prop(props.inputs['Flow Offset Vector'], "default_value", text="Flow Offset")
                                    panel.label(text="Light Flow Anim Curve")
                                    panel.template_curve_mapping(props.node_tree.nodes['Anim Curve'], "mapping")
                                    subheader, subpanel = panel.panel(f"{props.node_tree.name} preset curves", default_closed=True)
                                    subheader.label(text="Preset Curves")
                                    if subpanel:
                                        curve_node = props.node_tree.nodes['Anim Curve']
                                        curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                        if curve_setting:
                                            draw_curve_ui(subpanel, curve_setting)
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Change Color'], "default_value", text="Change Color")
                                    if props.inputs['Change Color'].default_value:
                                        row.prop(props.inputs['Color Direction'], "default_value", text="Color Direction")
                                        panel.template_color_ramp(props.node_tree.nodes['Color Ramp'], "color_ramp", expand=True)
                                    row = panel.row(align=True)
                                    row.prop(props.inputs["Color Direction"], "default_value", text="Color Direction")
                                    row.prop(props.inputs['Flow Style'], "default_value", text="Flow Style")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Spark Particles'], "default_value", text="Spark Particles")
                                    if props.inputs['Spark Particles'].default_value:
                                        row.prop(props.inputs['Particle Source'], "default_value", text="Particle Source")
                                        panel.prop(props.inputs['Particle Instancing Probability'], "default_value", text="Particle Instancing Probability")
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['Particle Lifetime'], "default_value", text="Particle Lifetime")
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['Particle Radius Multiplier'], "default_value", text="Particle Radius Multiplier")
                                        row.prop(props.inputs['Particle Light Strength'], "default_value", text="Particle Light Strength")
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['Resample Curve'], "default_value", text="Resample Curve")
                                        if props.inputs['Resample Curve'].default_value:
                                            row.prop(props.inputs['Resample Count'], "default_value", text="Resample Count")
                                        row = panel.row(align=True)
                                        col = row.column(align=True)
                                        col.prop(props.inputs['Particle Speed Min'], "default_value", text="Particle Speed Min")
                                        col = row.column(align=True)
                                        col.prop(props.inputs['Particle Speed Max'], "default_value", text="Particle Speed Max")
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['Randomness'], "default_value", text="Speed Randomness")
                                        row.prop(props.inputs['Seed'], "default_value", text="Seed")
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['Particle to Curve'], "default_value", text="Particles to Curve")
                                    panel.separator()
                                continue
                            elif anim_type == 'wave_anim':
                                for anim_node in anim_nodes:
                                    gprops, lprops = anim_node
                                    if gprops.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, gprops.name)
                                        continue
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Wave Anim')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{gprops.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{gprops.id_data.name}**{gprops.name}**{lprops.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'plotter_anim'
                                    if status.hide:
                                        continue
                                    split = panel.split(factor=0.5)
                                    split.prop(gprops.inputs['Passthrough'], 'default_value', text="Global", invert_checkbox=True)
                                    split.prop(lprops.inputs['Passthrough'], 'default_value', text="Local", invert_checkbox=True)
                                    for i, props in enumerate([gprops, lprops]):
                                        panel.label(text="Global Wave" if i==0 else "Local Wave")
                                        row = panel.row(align=True)
                                        row.label(text="Effect Range: ")
                                        row.prop(props.inputs['Range Start'], "default_value", text="Range Start")
                                        row.prop(props.inputs['Range End'], "default_value", text="Range End")
                                        row = panel.row(align=True)
                                        if props.node_tree.nodes["Wave Texture"].wave_type == 'BANDS':
                                            row.prop(props.node_tree.nodes["Wave Texture"], "bands_direction", text="Wave Direction")
                                        else:
                                            row.prop(props.node_tree.nodes["Wave Texture"], "rings_direction", text="Wave Direction")
                                        row.prop(props.node_tree.nodes["Menu Switch"].inputs['Menu'], "default_value", text="Effect On")
                                        row = panel.row(align=True)
                                        row.prop(props.node_tree.nodes["Wave Texture"], "wave_type", text="Wave Type")
                                        row.prop(props.node_tree.nodes["Wave Texture"], "wave_profile", text="Wave Profile")
                                        panel.label(text="Wave Control")
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['Speed'], "default_value", text="Speed")
                                        row.prop(props.inputs['Scale'], "default_value", text="Scale")
                                        row = panel.row(align=True)
                                        row.prop(props.node_tree.nodes["Wave Texture"].inputs['Distortion'], "default_value", text="Distortion")
                                        row.prop(props.node_tree.nodes["Wave Texture"].inputs['Detail'], "default_value", text="Detail")
                                        row = panel.row(align=True)
                                        row.prop(props.node_tree.nodes["Wave Texture"].inputs['Detail Scale'], "default_value", text="Detail Scale")
                                        row.prop(props.node_tree.nodes["Wave Texture"].inputs['Detail Roughness'], "default_value", text="Detail Roughness")
                                        panel.label(text="Wave Curve Shape")
                                        panel.template_curve_mapping(props.node_tree.nodes['Float Curve'], "mapping")
                                        subheader, subpanel = panel.panel(f"{props.node_tree.name} preset curves", default_closed=True)
                                        subheader.label(text="Preset Curves")
                                        if subpanel:
                                            curve_node = props.node_tree.nodes['Float Curve']
                                            curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                            if curve_setting:
                                                draw_curve_ui(subpanel, curve_setting)
                                        panel.separator()
                                continue
                            elif anim_type == 'flow_anim':
                                for anim_node in anim_nodes:
                                    if anim_node.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, anim_node.name)
                                        continue
                                    props = anim_node
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Edge Flow Anim')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{anim_node.id_data.name}**{anim_node.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'plotter_anim'
                                    if status.hide:
                                        continue
                                    subrow = panel.row(align=True)
                                    subrow.prop(props.inputs['Bounding Box'], "default_value", text="Bounding Box")
                                    subrow.prop(props.inputs['Closed Path'], "default_value", text="Closed Path?")
                                    subrow = panel.row(align=True)
                                    subrow.prop(props.inputs['Reverse Flow'], "default_value", text="Reverse")
                                    subrow.prop(props.inputs['Subdivide Curve'], "default_value", text="Subdivide")
                                    subrow = panel.row(align=True)
                                    subrow.prop(props.inputs['Start Frame'], "default_value", text="Start Frame")
                                    subrow.prop(props.inputs['End Frame'], "default_value", text="End Frame")
                                    subrow = panel.row(align=True)
                                    subrow.prop(props.inputs['Cycle Length'], "default_value", text="Cycle Length")
                                    subrow.prop(props.inputs['Flow Length'], "default_value", text="Flow Length")
                                    subrow = panel.row(align=True)
                                    subrow.prop(props.inputs['Scale'], "default_value", text="Scale")
                                    subrow.prop(props.inputs['Edge Select'], "default_value", text="Edge Selection")
                                    if props.inputs['Bounding Box'].default_value:
                                        subrow = panel.row(align=True)
                                        subrow.prop(props.inputs['BBOX Width Scale'], "default_value", text="BBox Width")
                                        subrow.prop(props.inputs['BBOX Height Scale'], "default_value", text="BBox Height")
                                    panel.template_color_ramp(props.node_tree.nodes['Color Ramp'], "color_ramp", expand=True)
                                    panel.prop(props.inputs['Color Strength'], "default_value", text="Color Strength")
                                    panel.label(text="Edge Flow Curve Shape")
                                    panel.template_curve_mapping(props.node_tree.nodes['Float Curve'], "mapping")
                                    subheader, subpanel = panel.panel(f"{props.node_tree.name} preset curves", default_closed=True)
                                    subheader.label(text="Preset Curves")
                                    if subpanel:
                                        curve_node = props.node_tree.nodes['Float Curve']
                                        curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                        if curve_setting:
                                            draw_curve_ui(subpanel, curve_setting)
                                    panel.separator()
                                continue
                            elif anim_type == 'transform_anim':
                                for anim_node in anim_nodes:
                                    if anim_node.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, anim_node.name)
                                        continue
                                    props = anim_node
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Transform Anim')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{anim_node.id_data.name}**{anim_node.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'plotter_anim'
                                    if status.hide:
                                        continue
                                    row = panel.row(align=True)
                                    row.label(text="Effect Range: ")
                                    row.prop(props.inputs['Range Start'], "default_value", text="Range Start")
                                    row.prop(props.inputs['Range End'], "default_value", text="Range End")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Start Frame'], "default_value", text="Start Frame")
                                    row.prop(props.inputs['Anim Length'], "default_value", text="Anim Length")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Reverse'], "default_value", text="Reverse")
                                    row.prop(props.inputs['Randomize'], "default_value", text="Randomize")
                                    if props.inputs['Randomize'].default_value:
                                        row.prop(props.inputs['Seed'], "default_value", text="Seed")
                                    panel.prop(props.inputs['Keep Before Start'], "default_value", text="Keep Before Start or After End")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Bypass Rotate'], "default_value", text="Mute Rotate")
                                    row.prop(props.inputs['Bypass Offset'], "default_value", text="Mute Offset")
                                    row.prop(props.inputs['Bypass Scale'], "default_value", text="Mute Scale")
                                    for transform in ['Rotate', 'Offset', 'Scale']:
                                        if not props.inputs[f'Bypass {transform}'].default_value:
                                            panel.label(text=f"{transform} Anim Setting")
                                            panel.prop(props.node_tree.nodes[f'{transform} Mix'].inputs["A"], "default_value", text=f"{transform}")
                                            panel.label(text=f"{transform} Anim Curve")
                                            panel.template_curve_mapping(props.node_tree.nodes[f'{transform} Anim Curve'], "mapping")
                                            subheader, subpanel = panel.panel(f"{props.node_tree.name} {transform} preset curves", default_closed=True)
                                            subheader.label(text="Preset Curves")
                                            if subpanel:
                                                curve_node = props.node_tree.nodes[f'{transform} Anim Curve']
                                                curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                                if curve_setting:
                                                    draw_curve_ui(subpanel, curve_setting)
                                            if not props.inputs["Randomize"].default_value:
                                                if transform == 'Rotate':
                                                    panel.prop(props.node_tree.nodes[f"{transform} Instances"].inputs['Pivot Point'], "default_value", text="Pivot Point")
                                                elif transform == 'Scale':
                                                    panel.prop(props.node_tree.nodes[f"{transform} Instances"].inputs['Center'], "default_value", text="Center")
                                                panel.prop(props.node_tree.nodes[f"{transform} Instances"].inputs['Local Space'], "default_value", text="Local Space")
                                            panel.separator()
                                continue
                            elif anim_type == 'transform':
                                for anim_node in anim_nodes:
                                    if anim_node.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, anim_node.name)
                                        continue
                                    props = anim_node.node_tree
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Transform Anim')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{anim_node.id_data.name}**{anim_node.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'plotter_anim'
                                    if status.hide:
                                        continue
                                    nodes = [props.nodes['Rotate Instances'], props.nodes['Translate Instances'], props.nodes['Scale Instances']]
                                    for i, node in enumerate(nodes):
                                        if i>0:
                                            panel.separator()
                                            panel.separator()
                                        split = panel.split(factor=0.5)
                                        for socket in node.inputs[2:]:
                                            if socket.name == 'Local Space' or socket.name == 'Translation':
                                                panel.prop(socket, "default_value", text=socket.name)
                                            else:
                                                split.prop(socket, "default_value", text=socket.name)
                                    panel.separator()
                                continue
                            elif anim_type == 'add_snapshot':
                                for anim_node in anim_nodes:
                                    if anim_node.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, anim_node.name)
                                        continue
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Add Snapshot')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{anim_node.id_data.name}**{anim_node.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'plotter_anim'
                                    if status.hide:
                                        continue
                                    panel.template_node_inputs(anim_node)
                                    panel.separator()
                                continue
                            elif anim_type == 'curve_normal_tangent':
                                for anim_node in anim_nodes:
                                    if anim_node.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, anim_node.name)
                                        continue
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Curve Normal/Tangent')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{anim_node.id_data.name}**{anim_node.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'plotter_anim'
                                    if status.hide:
                                        continue
                                    panel.template_node_inputs(anim_node)
                                    panel.separator()
            # for the axis control
            if gp_obj:
                gp_layer = gp_obj.data.layers.get(gplayers.gp_layer)
                if gp_layer and gp_layer.name.split('.')[-1]=='axis' and gp_obj["math_anim_obj"] in vb.gpencil_layer_nodes and gp_layer.name in vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]]:
                    panel.prop(gplayers, 'axis_control', text='Axis Settings')
                    if gplayers.axis_control:
                        layer_node = vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]][gp_layer.name]
                        mat_node = layer_node.node_tree.nodes['GP Material']
                        panel.prop(mat_node.inputs['Axis Label Radius'], 'default_value', text='Label Curve Radius')
                        panel.prop(mat_node.inputs['Axis Label Color'], 'default_value', text='Label Color')
                        axis_label_node = layer_node.node_tree.nodes['Axis Labels']
                        panel.template_ID(data=axis_label_node.node_tree.nodes['Label Font'].node_tree.nodes['Label Font'].inputs["Font"],property='default_value',open="font.open",unlink="font.unlink",text="Label Font")
                        panel.template_ID(data=axis_label_node.node_tree.nodes['Tick Label Font'].node_tree.nodes['Tick Label Font'].inputs["Font"],property='default_value',open="font.open",unlink="font.unlink",text="Tick Label Font")
                        panel.template_node_inputs(axis_label_node)


        # formula ui
        formula_props = context.scene.math_anim_formula_props
        header, panel = layout.panel("math_anim_formula", default_closed=True)
        header.label(text="Formula Text")
        if panel:
            panel.prop(formula_props, "formula_source")
            col = panel.column(align=True)
            col.scale_y = 1.2
            if formula_props.optex_preset:
                col.prop(formula_props, "optex_preset")
            if formula_props.typst_preset:
                col.prop(formula_props, "typst_preset")
            if formula_props.formula_source == 'Optex_Code':
                panel.prop(formula_props, "optex_fontfam", text="fontfam")

            row = panel.row()
            col = row.column()
            # box for the path list
            formula_paths = [context.scene.math_anim_optexcode, context.scene.math_anim_typstcode,
                                context.scene.math_anim_optexfile, context.scene.math_anim_typstfile,
                                context.scene.math_anim_pdffile]
            source_items = list(MATH_ANIM_Formula_Properties.bl_rna.properties['formula_source'].enum_items)
            for item_idx in range(len(source_items)):
                if formula_props.formula_source == source_items[item_idx].identifier:
                    col.template_list("MATH_ANIM_PATH_UL_List", "", formula_paths[item_idx], "paths", formula_paths[item_idx], "active_index")
            # buttons on the right
            col = row.column(align=True)
            col.operator("math_anim.formula_addpath", text="", icon="ADD")
            col.operator("math_anim.formula_removepath", text="", icon="REMOVE")

            panel.operator("math_anim.create_formula")
            if context.object and context.object.modifiers and (context.object.get("math_anim_obj") is not None):
                md = context.object.modifiers.get('formulaGeoNodes')
                if md:
                    row = panel.row(align=False)
                    row.prop(md.properties.inputs.Socket_2, 'value', text="Page Size")
                    # check whether having any chars, strokes or fills
                    has_char = False
                    has_stroke = False
                    has_fill = False
                    if vb.formula_node_trees[context.object["math_anim_obj"]]:
                        for page_num in range(len(vb.formula_node_trees[context.object["math_anim_obj"]])):
                            nodes = vb.formula_node_trees[context.object["math_anim_obj"]][page_num]
                            text_nodes = nodes['text_nodes']
                            stroke_nodes = nodes['stroke_nodes']
                            fill_nodes = nodes['fill_nodes']
                            if len(text_nodes)>1:
                                has_char = True
                            if len(stroke_nodes)>1:
                                has_stroke = True
                            if len(fill_nodes)>1:
                                has_fill = True
                    suffix = context.object["math_anim_obj"][context.object["math_anim_obj"].find('Global'):]
                    char_settings = bpy.data.node_groups.get(f"char_settings.{suffix}")
                    render_type = bpy.data.node_groups.get(f"render_type.{suffix}")
                    if render_type:
                        menu_node = render_type.nodes['Menu Switch']
                        row.prop(menu_node.inputs['Menu'], 'default_value', text="Render As")
                    if char_settings:
                        color_node = char_settings.nodes['Color']
                        color_strength_node = char_settings.nodes['Color Strength']
                        row = panel.row(align=False)
                        row.prop(color_node.inputs["Value"], 'default_value', text="")
                        row.prop(color_strength_node.inputs["Value"], 'default_value', text="Color Strength")
                        if menu_node.inputs['Menu'].default_value == 'Grease Pencil':
                            radius_node = char_settings.nodes['Curve Radius']
                            row = panel.row(align=False)
                            row.prop(radius_node.inputs["Value"], 'default_value', text="Curve Radius")
                        row = panel.row(align=False)
                        row.template_ID(data=formula_props, property='formula_font', open="font.open", unlink="font.unlink", text="")
                        row.operator("math_anim.update_formula_font", text="", icon='FILE_REFRESH')

                    panel.separator()
                    panel.prop(formula_props, "anim_style", text="Anim Style")
                    row = panel.row(align=True)
                    col = row.column()
                    if not has_char:
                        col.enabled = False
                    col.prop(formula_props, "anim_text",toggle=1)
                    col = row.column()
                    if not has_stroke:
                        col.enabled = False
                    col.prop(formula_props, "anim_stroke", toggle=1)
                    col = row.column()
                    if not has_fill:
                        col.enabled = False
                    col.prop(formula_props, "anim_fill", toggle=1)
                    col = panel.column()
                    if not has_char and not has_stroke and not has_fill:
                        col.enabled = False
                    col.operator("math_anim.add_formula_anim", text="Add Anim")

                    panel.separator()
                    panel.label(text="Anim Settings")
                    row = panel.row(align=True)
                    row.prop_enum(formula_props, "anim_settings", "TEXT")
                    row.prop_enum(formula_props, "anim_settings", "STROKE")
                    row.prop_enum(formula_props, "anim_settings", "FILL")
                    panel.use_property_decorate = True  # False for no animation.
                    show_settings = ''
                    if formula_props.anim_settings == 'TEXT':
                        show_settings = 'text_anim'
                    elif formula_props.anim_settings == 'STROKE':
                        show_settings = 'stroke_anim'
                    elif formula_props.anim_settings == 'FILL':
                        show_settings = 'fill_anim'
                    if context.object["math_anim_obj"] in vb.formula_anim_nodes and show_settings in vb.formula_anim_nodes[context.object["math_anim_obj"]]:
                        for anim_type in vb.formula_anim_nodes[context.object["math_anim_obj"]][show_settings]:
                            if 'grow_anim' == anim_type and len(vb.formula_anim_nodes[context.object["math_anim_obj"]][show_settings]['grow_anim'])>0:
                                for node in vb.formula_anim_nodes[context.object["math_anim_obj"]][show_settings]['grow_anim']:
                                    if f"{node.id_data.name}**{node.name}" not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, f"{node.id_data.name}**{node.name}")
                                        continue
                                    props = node
                                    split = panel.split(factor=0.7)
                                    split.label(text=f"{props.name.split('.')[0]} settings")
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{node.id_data.name}**{node.name}"]]
                                    subrow.prop(status,"hide")
                                    op = subrow.operator("math_anim.del_formula_anim", text="", icon='PANEL_CLOSE')
                                    op.anim_type = f"{show_settings}.grow_anim"
                                    op.node_name = f"{node.id_data.name}**{node.name}"
                                    if status.hide:
                                        continue
                                    row = panel.row(align=True)
                                    row.label(text="Effect Range: ")
                                    row.prop(props.inputs['Range Start'], "default_value", text="Range Start")
                                    row.prop(props.inputs['Range End'], "default_value", text="Range End")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Start Frame'], "default_value", text="Start Frame")
                                    row.prop(props.inputs['Anim Length'], "default_value", text="Anim Length")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Local'], "default_value", text="Local Grow")
                                    row.prop(props.inputs['Reverse'], "default_value", text="Reverse Grow")
                                    panel.prop(props.inputs['Center'], "default_value", text="Grow Center")
                                    panel.label(text="Grow Anim Curve")
                                    panel.template_curve_mapping(props.node_tree.nodes['Float Curve'], "mapping")
                                    subheader, subpanel = panel.panel(f"{props.node_tree.name} preset curves", default_closed=True)
                                    subheader.label(text="Preset Curves")
                                    if subpanel:
                                        curve_node = props.node_tree.nodes['Float Curve']
                                        curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                        if curve_setting:
                                            draw_curve_ui(subpanel, curve_setting)
                                    panel.separator()

                                panel.separator()
                                continue
                            if 'transform_anim' == anim_type and len(vb.formula_anim_nodes[context.object["math_anim_obj"]][show_settings]['transform_anim'])>0:
                                for node in vb.formula_anim_nodes[context.object["math_anim_obj"]][show_settings]['transform_anim']:
                                    if f"{node.id_data.name}**{node.name}" not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, f"{node.id_data.name}**{node.name}")
                                        continue
                                    props = node
                                    split = panel.split(factor=0.7)
                                    split.label(text=f"{props.name.split('.')[0]} settings")
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{node.id_data.name}**{node.name}"]]
                                    subrow.prop(status,"hide")
                                    op = subrow.operator("math_anim.del_formula_anim", text="", icon='PANEL_CLOSE')
                                    op.anim_type = f"{show_settings}.transform_anim"
                                    op.node_name = f"{node.id_data.name}**{node.name}"
                                    if status.hide:
                                        continue
                                    row = panel.row(align=True)
                                    row.label(text="Effect Range: ")
                                    row.prop(props.inputs['Range Start'], "default_value", text="Range Start")
                                    row.prop(props.inputs['Range End'], "default_value", text="Range End")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Start Frame'], "default_value", text="Start Frame")
                                    row.prop(props.inputs['Anim Length'], "default_value", text="Anim Length")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Reverse'], "default_value", text="Reverse")
                                    row.prop(props.inputs['Randomize'], "default_value", text="Randomize")
                                    if props.inputs['Randomize'].default_value:
                                        row.prop(props.inputs['Seed'], "default_value", text="Seed")
                                    panel.prop(props.inputs['Keep Before Start'], "default_value", text="Keep Before Start or After End")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Bypass Rotate'], "default_value", text="Mute Rotate")
                                    row.prop(props.inputs['Bypass Offset'], "default_value", text="Mute Offset")
                                    row.prop(props.inputs['Bypass Scale'], "default_value", text="Mute Scale")
                                    for transform in ['Rotate', 'Offset', 'Scale']:
                                        if not props.inputs[f'Bypass {transform}'].default_value:
                                            panel.label(text=f"{transform} Anim Setting")
                                            panel.prop(props.node_tree.nodes[f'{transform} Mix'].inputs["A"], "default_value", text=f"{transform}")
                                            panel.label(text=f"{transform} Anim Curve")
                                            panel.template_curve_mapping(props.node_tree.nodes[f'{transform} Anim Curve'], "mapping")
                                            subheader, subpanel = panel.panel(f"{props.node_tree.name} {transform} preset curves", default_closed=True)
                                            subheader.label(text="Preset Curves")
                                            if subpanel:
                                                curve_node = props.node_tree.nodes[f'{transform} Anim Curve']
                                                curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                                if curve_setting:
                                                    draw_curve_ui(subpanel, curve_setting)
                                            if not props.inputs["Randomize"].default_value:
                                                if transform == 'Rotate':
                                                    panel.prop(props.node_tree.nodes[f"{transform} Instances"].inputs['Pivot Point'], "default_value", text="Pivot Point")
                                                elif transform == 'Scale':
                                                    panel.prop(props.node_tree.nodes[f"{transform} Instances"].inputs['Center'], "default_value", text="Center")
                                                panel.prop(props.node_tree.nodes[f"{transform} Instances"].inputs['Local Space'], "default_value", text="Local Space")
                                            panel.separator()
                                panel.separator()
                                continue
                            elif 'writing_anim' == anim_type  and len(vb.formula_anim_nodes[context.object["math_anim_obj"]][show_settings]['writing_anim'])>0:
                                for node in vb.formula_anim_nodes[context.object["math_anim_obj"]][show_settings]['writing_anim']:
                                    if f"{node.id_data.name}**{node.name}" not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, f"{node.id_data.name}**{node.name}")
                                        continue
                                    props = node
                                    split = panel.split(factor=0.7)
                                    split.label(text=f"{props.name.split('.')[0]} settings")
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{node.id_data.name}**{node.name}"]]
                                    subrow.prop(status,"hide")
                                    op = subrow.operator("math_anim.del_formula_anim", text="", icon='PANEL_CLOSE')
                                    op.anim_type = f"{show_settings}.writing_anim"
                                    op.node_name = f"{node.id_data.name}**{node.name}"
                                    if status.hide:
                                        continue
                                    row = panel.row(align=True)
                                    row.label(text="Effect Range: ")
                                    row.prop(props.inputs['Range Start'], "default_value", text="Start")
                                    row.prop(props.inputs['Range End'], "default_value", text="End")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Start Frame'], "default_value", text="Start Frame")
                                    row.prop(props.inputs['Anim Length'], "default_value", text="Anim Length")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Local'], "default_value", text="Local Writing")
                                    row.prop(props.inputs['Reverse'], "default_value", text="Reverse Writing")
                                    panel.label(text="Writing Anim Curve")
                                    panel.template_curve_mapping(props.node_tree.nodes['Float Curve'], "mapping")
                                    subheader, subpanel = panel.panel(f"{props.node_tree.name} preset curves", default_closed=True)
                                    subheader.label(text="Preset Curves")
                                    if subpanel:
                                        curve_node = props.node_tree.nodes['Float Curve']
                                        curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                        if curve_setting:
                                            draw_curve_ui(subpanel, curve_setting)
                                    ctl_switch = 'Local' if props.inputs['Local'].default_value else 'Global'
                                    split = panel.split(factor=0.5)
                                    if ctl_switch == 'Global':
                                        row = split.row(align=True)
                                        row.prop(props.inputs['Writing Style'], "default_value", expand=True)
                                    if (ctl_switch == 'Global' and props.inputs['Writing Style'].default_value == "Writing") or ctl_switch == 'Local':
                                        split.prop(props.inputs[f'Add {ctl_switch} Writing Symbol'], "default_value", text="Add Writing Symbol")
                                        if props.inputs[f'Add {ctl_switch} Writing Symbol'].default_value:
                                            panel.template_ID(data=props.node_tree.nodes[f'{ctl_switch} Writing Symbol'].inputs["Font"], property="default_value", open="font.open", unlink="font.unlink", text="Symbol Font")
                                            panel.prop(props.node_tree.nodes[f'{ctl_switch} Writing Symbol'].inputs['String'], "default_value", text="Symbol")
                                            panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Radius'], "default_value", text="Symbol Line Radius")
                                            panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Color'], "default_value", text="Symbol Color")
                                            panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Color Strength'], "default_value", text="Symbol Color Strength")
                                            panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Translation'], "default_value", text="Symbol Translation")
                                            panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Rotation'], "default_value", text="Symbol Rotation")
                                            panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Scale'], "default_value", text="Symbol Scale")
                                    panel.separator()

                                panel.separator()
                                continue
                            elif 'color_flow' == anim_type  and len(vb.formula_anim_nodes[context.object["math_anim_obj"]][show_settings]['color_flow'])>0:
                                for node in vb.formula_anim_nodes[context.object["math_anim_obj"]][show_settings]['color_flow']:
                                    if f"{node.id_data.name}**{node.name}" not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, f"{node.id_data.name}**{node.name}")
                                        continue
                                    props = node
                                    split = panel.split(factor=0.7)
                                    split.label(text=f"{props.name.split('.')[0]} settings")
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{node.id_data.name}**{node.name}"]]
                                    subrow.prop(status,"hide")
                                    op = subrow.operator("math_anim.del_formula_anim", text="", icon='PANEL_CLOSE')
                                    op.anim_type = f"{show_settings}.color_flow"
                                    op.node_name = f"{node.id_data.name}**{node.name}"
                                    if status.hide:
                                        continue
                                    row = panel.row(align=True)
                                    row.label(text="Effect Range: ")
                                    row.prop(props.inputs['Range Start'], "default_value", text="Start")
                                    row.prop(props.inputs['Range End'], "default_value", text="End")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Start Frame'], "default_value", text="Start Frame")
                                    row.prop(props.inputs['Anim Length'], "default_value", text="Anim Length")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Flow Length'], "default_value", text="Flow Length")
                                    row.prop(props.inputs['Flow Speed'], "default_value", text="Flow Speed")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Flow Radius'], "default_value", text="Flow Radius")
                                    row.prop(props.inputs['Flow Color Strength'], "default_value", text="Flow Color Strength")
                                    row = panel.row(align=True)
                                    offset_type = ''
                                    if render_type and render_type.nodes['Menu Switch'].inputs['Menu'].default_value == 'Grease Pencil':
                                        row.prop(props.inputs['Flow Offset'], "default_value", text="Flow Offset")
                                        offset_type = props.inputs['Flow Offset'].default_value
                                    else:
                                        row.prop(props.inputs['Mesh Flow Offset'], "default_value", text="Flow Offset")
                                        offset_type = props.inputs['Mesh Flow Offset'].default_value
                                    row.prop(props.inputs['Local Flow'], "default_value", text="Local Flow")
                                    if offset_type == "Normal":
                                        panel.prop(props.inputs['Flow Offset Normal'], "default_value", text="Flow Offset")
                                    else:
                                        panel.prop(props.inputs['Flow Offset Vector'], "default_value", text="Flow Offset")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Reverse Flow'], "default_value", text="Reverse Flow")
                                    row.prop(props.inputs['Reverse Color'], "default_value", text="Reverse Color")
                                    panel.label(text="Color Flow Anim Curve")
                                    if render_type and render_type.nodes['Menu Switch'].inputs['Menu'].default_value == 'Grease Pencil':
                                        panel.template_curve_mapping(props.node_tree.nodes['Float Curve'], "mapping")
                                        subheader, subpanel = panel.panel(f"{props.node_tree.name} {render_type} preset curves", default_closed=True)
                                        subheader.label(text="Preset Curves")
                                        if subpanel:
                                            curve_node = props.node_tree.nodes['Float Curve']
                                            curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                            if curve_setting:
                                                draw_curve_ui(subpanel, curve_setting)
                                    elif render_type:
                                        panel.template_curve_mapping(props.node_tree.nodes['Mesh Float Curve'], "mapping")
                                        subheader, subpanel = panel.panel(f"{props.node_tree.name} {render_type} preset curves", default_closed=True)
                                        subheader.label(text="Preset Curves")
                                        if subpanel:
                                            curve_node = props.node_tree.nodes['Mesh Float Curve']
                                            curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                            if curve_setting:
                                                draw_curve_ui(subpanel, curve_setting)
                                    panel.prop(props.inputs['Change Flow Color'], "default_value", text="Change Flow Color")
                                    if props.inputs['Change Flow Color'].default_value:
                                        if render_type and render_type.nodes['Menu Switch'].inputs['Menu'].default_value == 'Grease Pencil':
                                            panel.template_color_ramp(props.node_tree.nodes['Color Ramp'], "color_ramp")
                                        elif render_type:
                                            panel.template_color_ramp(props.node_tree.nodes['Mesh Color Ramp'], "color_ramp")
                                        row = panel.row(align=True)
                                        if render_type and render_type.nodes['Menu Switch'].inputs['Menu'].default_value == 'Grease Pencil':
                                            row.prop(props.inputs['Flow Color Direction'], "default_value", text="Color Direction")
                                            row.prop(props.inputs['Flow Style'], "default_value", text="Flow Style")
                                        elif render_type:
                                            row.prop(props.inputs['Mesh Flow Color Direction'], "default_value", text="Color Direction")
                                            row.prop(props.inputs['Mesh Flow Style'], "default_value", text="Flow Style")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Spark Particles'], "default_value", text="Spark Particles")
                                    if props.inputs['Spark Particles'].default_value:
                                        if render_type and render_type.nodes['Menu Switch'].inputs['Menu'].default_value == 'Grease Pencil':
                                            row.prop(props.inputs['Particle Source'], "default_value", text="Particle Source")
                                        elif render_type:
                                            row.prop(props.inputs['Mesh Particle Source'], "default_value", text="Particle Source")
                                        panel.prop(props.inputs['Particle Instancing Probability'], "default_value", text="Particle Instancing Probability")
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['Particle Lifetime'], "default_value", text="Particle Lifetime")
                                        row.prop(props.inputs['Particle Color Strength'], "default_value", text="Particle Color Strength")
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['Resample Flow Curve'], "default_value", text="Resample Flow Curve")
                                        if props.inputs['Resample Flow Curve'].default_value:
                                            row.prop(props.inputs['Resample Count'], "default_value", text="Resample Count")
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['Particle Radius Min'], "default_value", text="Particle Radius Min")
                                        row.prop(props.inputs['Particle Radius Max'], "default_value", text="Particle Radius Max")
                                        row = panel.row(align=True)
                                        col = row.column(align=True)
                                        col.prop(props.inputs['Particle Speed Min'], "default_value", text="Particle Speed Min")
                                        col = row.column(align=True)
                                        col.prop(props.inputs['Particle Speed Max'], "default_value", text="Particle Speed Max")
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['Randomness'], "default_value", text="Speed Randomness")
                                        row.prop(props.inputs['Seed'], "default_value", text="Seed")
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['Particle to Curve'], "default_value", text="Particle to Curve")
                                    panel.separator()

                                panel.separator()
                                continue
                            elif 'wave_anim' == anim_type and len(vb.formula_anim_nodes[context.object["math_anim_obj"]][show_settings]['wave_anim'])>0:
                                for inode, cnode in vb.formula_anim_nodes[context.object["math_anim_obj"]][show_settings]['wave_anim']:
                                    if f"{inode.id_data.name}**{inode.name}" not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, f"{inode.id_data.name}**{inode.name}")
                                        continue
                                    if f"{cnode.id_data.name}**{cnode.name}" not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, f"{cnode.id_data.name}**{cnode.name}")
                                        continue
                                    split = panel.split(factor=0.5)
                                    split.label(text="Wave Anim settings")
                                    subrow = split.row(align=True)
                                    subrow.alignment = 'RIGHT'
                                    subrow.prop(inode.inputs['Passthrough'], 'default_value', text="Global", invert_checkbox=True)
                                    subrow.prop(cnode.inputs['Passthrough'], 'default_value', text="Local", invert_checkbox=True)
                                    op = subrow.operator("math_anim.del_formula_anim", text="", icon='PANEL_CLOSE')
                                    op.anim_type = f"{show_settings}.wave_anim"
                                    op.node_name = f"{inode.id_data.name}**{inode.name}**{cnode.id_data.name}**{cnode.name}"
                                    for i, node in enumerate([inode, cnode]):
                                        split = panel.split(factor=0.8)
                                        split.label(text="Global Wave" if i==0 else "Local Wave")
                                        status = anim_setting_status[vb.formula_animsetting_status[f"{node.id_data.name}**{node.name}"]]
                                        subrow = split.row(align=True)
                                        subrow.alignment = 'RIGHT'
                                        subrow.prop(status,"hide")
                                        if status.hide:
                                            continue
                                        row = panel.row(align=True)
                                        row.label(text="Effect Range: ")
                                        row.prop(node.inputs['Range Start'], "default_value", text="Start")
                                        row.prop(node.inputs['Range End'], "default_value", text="End")
                                        row = panel.row(align=True)
                                        if node.node_tree.nodes["Wave Texture"].wave_type == 'BANDS':
                                            row.prop(node.node_tree.nodes["Wave Texture"], "bands_direction", text="Wave Direction")
                                        else:
                                            row.prop(node.node_tree.nodes["Wave Texture"], "rings_direction", text="Wave Direction")
                                        row.prop(node.node_tree.nodes["Menu Switch"].inputs[0], "default_value", text="Effect On")
                                        row = panel.row(align=True)
                                        row.prop(node.node_tree.nodes["Wave Texture"], "wave_type", text="Wave Type")
                                        row.prop(node.node_tree.nodes["Wave Texture"], "wave_profile", text="Wave Profile")
                                        panel.label(text="Wave Control")
                                        row = panel.row(align=True)
                                        row.prop(node.inputs['Speed'], "default_value", text="Speed")
                                        row.prop(node.inputs['Scale'], "default_value", text="Scale")
                                        row = panel.row(align=True)
                                        row.prop(node.node_tree.nodes["Wave Texture"].inputs['Distortion'], "default_value", text="Distortion")
                                        row.prop(node.node_tree.nodes["Wave Texture"].inputs['Detail'], "default_value", text="Detail")
                                        row = panel.row(align=True)
                                        row.prop(node.node_tree.nodes["Wave Texture"].inputs['Detail Scale'], "default_value", text="Detail Scale")
                                        row.prop(node.node_tree.nodes["Wave Texture"].inputs['Detail Roughness'], "default_value", text="Detail Roughness")
                                        panel.label(text="Wave Curve Shape")
                                        panel.template_curve_mapping(node.node_tree.nodes['Float Curve'], "mapping")
                                        subheader, subpanel = panel.panel(f"{node.node_tree.name} preset curves", default_closed=True)
                                        subheader.label(text="Preset Curves")
                                        if subpanel:
                                            curve_node = node.node_tree.nodes['Float Curve']
                                            curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                            if curve_setting:
                                                draw_curve_ui(subpanel, curve_setting)
                                        panel.separator()

                                panel.separator()
                                continue
                            elif 'flow_anim' == anim_type and len(vb.formula_anim_nodes[context.object["math_anim_obj"]][show_settings]['flow_anim'])>0:
                                for node in vb.formula_anim_nodes[context.object["math_anim_obj"]][show_settings]['flow_anim']:
                                    if f"{node.id_data.name}**{node.name}" not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, f"{node.id_data.name}**{node.name}")
                                        continue
                                    props = node
                                    split = panel.split(factor=0.7)
                                    split.label(text=f"{props.name.split('.')[0]} settings")
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{node.id_data.name}**{node.name}"]]
                                    subrow.prop(status,"hide")
                                    op = subrow.operator("math_anim.del_formula_anim", text="", icon='PANEL_CLOSE')
                                    op.anim_type = f"{show_settings}.flow_anim"
                                    op.node_name = f"{node.id_data.name}**{node.name}"
                                    if status.hide:
                                        continue
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Closed Path'], "default_value", text="Closed Path?")
                                    row.prop(props.inputs['Bounding Box'], "default_value", text="Bounding Box")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Reverse Flow'], "default_value", text="Reverse")
                                    row.prop(props.inputs['Subdivide Curve'], "default_value", text="Subdivide")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Start Frame'], "default_value", text="Start Frame")
                                    row.prop(props.inputs['End Frame'], "default_value", text="End Frame")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Cycle Length'], "default_value", text="Cycle Length")
                                    row.prop(props.inputs['Flow Length'], "default_value", text="Flow Length")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Scale'], "default_value", text="Scale")
                                    row.prop(props.inputs['Edge Select'], "default_value", text="Edge Selection")
                                    if props.inputs['Bounding Box'].default_value:
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['BBOX Width Scale'], "default_value", text="BBox Width")
                                        row.prop(props.inputs['BBOX Height Scale'], "default_value", text="BBox Height")
                                    panel.template_color_ramp(props.node_tree.nodes['Color Ramp'], "color_ramp", expand=True)
                                    panel.prop(props.inputs['Color Strength'], "default_value", text="Color Strength")
                                    panel.label(text="Edge Flow Curve Shape")
                                    panel.template_curve_mapping(props.node_tree.nodes['Float Curve'], "mapping")
                                    subheader, subpanel = panel.panel(f"{props.node_tree.name} preset curves", default_closed=True)
                                    subheader.label(text="Preset Curves")
                                    if subpanel:
                                        curve_node = props.node_tree.nodes['Float Curve']
                                        curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                        if curve_setting:
                                            draw_curve_ui(subpanel, curve_setting)
                                    panel.separator()

                                panel.separator()
                                continue
                            elif 'transform' == anim_type and len(vb.formula_anim_nodes[context.object["math_anim_obj"]][show_settings]['transform'])>0:
                                panel.label(text="Transform Anim Settings (by yourself)")
                                for node in vb.formula_anim_nodes[context.object["math_anim_obj"]][show_settings]['transform']:
                                    if f"{node.id_data.name}**{node.name}" not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, f"{node.id_data.name}**{node.name}")
                                        continue
                                    panel.separator()
                                    split = panel.split(factor=0.7)
                                    split.label(text=f"{node.name}")
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{node.id_data.name}**{node.name}"]]
                                    subrow.prop(status,"hide")
                                    op = subrow.operator("math_anim.del_formula_anim", text="", icon='PANEL_CLOSE')
                                    op.anim_type = f"{show_settings}.transform"
                                    op.node_name = f"{node.id_data.name}**{node.name}"
                                    if status.hide:
                                        continue
                                    split = panel.split(factor=0.5)
                                    for socket in node.inputs[2:]:
                                        if socket.name == 'Local Space' or socket.name == 'Translation':
                                            panel.prop(socket, "default_value", text=socket.name)
                                        else:
                                            split.prop(socket, "default_value", text=socket.name)

                individual_setting = context.scene.math_anim_individualSettings
                panel.separator()
                panel.separator()
                row = panel.row(align=True)
                row.alignment = 'CENTER'
                row.label(text="Individual Settings")
                row=panel.row(align=True)
                row.prop_enum(individual_setting, "option", 'INDIVIDUAL')
                row.prop_enum(individual_setting, "option", 'GROUP')
                draw_tag = False
                formula_obj = context.object
                for md in formula_obj.modifiers:
                    if 'formula' in md.name:
                        draw_tag = True
                if draw_tag and individual_setting.option == 'INDIVIDUAL':
                    panel.prop(individual_setting,"node_item", text="Item")
                    row = panel.row(align=True)
                    op = row.operator_menu_enum("math_anim.indiv_setup", "add_anim")
                    op.node_path = individual_setting.node_item
                    page_num = int(individual_setting.node_item.split('*.*')[0])
                    node_type = individual_setting.node_item.split('*.*')[1]
                    key_name = individual_setting.node_item.split('*.*')[2]
                    node = vb.formula_node_trees[formula_obj["math_anim_obj"]][page_num][node_type][key_name]
                    row = panel.row(align=True)
                    if node_type == 'text_nodes':
                        row.template_ID(data=node.node_tree.nodes['String to Curves'].inputs["Font"], property="default_value", open="font.open", unlink="font.unlink")
                    setting = node.node_tree.nodes['Char Settings']
                    row = panel.row(align=True)
                    row.prop(setting.inputs['Individual Control'], "default_value", text="Material Setting")
                    if setting.inputs['Individual Control'].default_value:
                        panel.label(text="For Mesh")
                        row = panel.row(align=True)
                        row.prop(setting.inputs['Color'], "default_value", text="Color")
                        row.prop(setting.inputs['Color Strength'], "default_value", text="Color Strength")
                        panel.label(text="For Grease Pencil")
                        row = panel.row(align=True)
                        #row.prop(setting.inputs['Material Index'], "default_value", text="Material Index")
                        row.prop(setting.inputs['Curve Radius'], "default_value", text="Curve Radius")
                    anim_types = ['grow_anim', 'writing_anim', 'wave_anim', 'flow_anim', 'transform_anim', 'transform', 'run_number']
                    if 'indiv_anim' in vb.formula_anim_nodes:
                        for anim_type in vb.formula_anim_nodes['indiv_anim']:
                            if node.name in vb.formula_anim_nodes['indiv_anim'][anim_type]:
                                for anim_node in vb.formula_anim_nodes['indiv_anim'][anim_type][node.name]:
                                    if anim_type == 'grow_anim':
                                        if anim_node.name not in vb.formula_animsetting_status:
                                            animsetting_status_reset(context, anim_node.name)
                                            continue
                                        props = anim_node.node_tree
                                        split = panel.split(factor=0.7)
                                        split.label(text=f'Grow Anim')
                                        subrow = split.row(align=True)
                                        status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                        subrow.prop(status,"hide")
                                        op=subrow.operator("math_anim.del_indiv_anim", text="", icon="PANEL_CLOSE")
                                        op.node_tree_name = f"{node.name}"
                                        op.anim_type = f"{anim_type}"
                                        if status.hide:
                                            continue
                                        row = panel.row(align=True)
                                        row.label(text="Effect Range: ")
                                        row.prop(props.nodes['Start'], "integer", text="Start")
                                        row.prop(props.nodes['End'], "integer", text="End")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes['Start Frame'], "integer", text="Start Frame")
                                        row.prop(props.nodes['Anim Length'], "integer", text="Anim Length")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes['Local'], "boolean", text="Local Grow")
                                        row.prop(props.nodes['Reverse Grow'], "boolean", text="Reverse Grow")
                                        panel.prop(props.nodes['Center'], "vector", text="Grow Center")
                                        panel.label(text="Grow Anim Curve")
                                        panel.template_curve_mapping(props.nodes['Float Curve'], "mapping")
                                        subheader, subpanel = panel.panel(f"{props.name} preset curves", default_closed=True)
                                        subheader.label(text="Preset Curves")
                                        if subpanel:
                                            curve_node = props.nodes['Float Curve']
                                            curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                            if curve_setting:
                                                draw_curve_ui(subpanel, curve_setting)
                                        panel.separator()
                                        continue
                                    if anim_type == 'transform_anim':
                                        if anim_node.name not in vb.formula_animsetting_status:
                                            animsetting_status_reset(context, anim_node.name)
                                            continue
                                        props = anim_node.node_tree
                                        split = panel.split(factor=0.7)
                                        split.label(text=f'Transform Anim')
                                        subrow = split.row(align=True)
                                        status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                        subrow.prop(status,"hide")
                                        op=subrow.operator("math_anim.del_indiv_anim", text="", icon="PANEL_CLOSE")
                                        op.node_tree_name = f"{node.name}"
                                        op.anim_type = f"{anim_type}"
                                        if status.hide:
                                            continue
                                        row = panel.row(align=True)
                                        row.label(text="Effect Range: ")
                                        row.prop(props.nodes['Range Start'], "integer", text="Start")
                                        row.prop(props.nodes['Range End'], "integer", text="End")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes['Start Frame'], "integer", text="Start Frame")
                                        row.prop(props.nodes['Anim Length'], "integer", text="Anim Length")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes['Reverse'], "boolean", text="Reverse")
                                        row.prop(props.nodes['Randomize'], "boolean", text="Randomize")
                                        if props.nodes['Randomize'].boolean:
                                            row.prop(props.nodes['Seed'], "integer", text="Seed")
                                        panel.prop(props.nodes['Keep Before Start'], "boolean", text="Keep Before Start or After End")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes['Bypass Rotate'], "boolean", text="Mute Rotate")
                                        row.prop(props.nodes['Bypass Offset'], "boolean", text="Mute Offset")
                                        row.prop(props.nodes['Bypass Scale'], "boolean", text="Mute Scale")
                                        for transform in ['Rotate', 'Offset', 'Scale']:
                                            if not props.nodes[f'Bypass {transform}'].boolean:
                                                panel.label(text=f"{transform} Anim Setting")
                                                panel.prop(props.nodes[f'{transform} Mix'].inputs['A'], "default_value", text=f"{transform}")
                                                panel.label(text=f"{transform} Anim Curve")
                                                panel.template_curve_mapping(props.nodes[f'{transform} Anim Curve'], "mapping")
                                                subheader, subpanel = panel.panel(f"{props.name} {transform} preset curves", default_closed=True)
                                                subheader.label(text="Preset Curves")
                                                if subpanel:
                                                    curve_node = props.nodes[f'{transform} Anim Curve']
                                                    curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                                    if curve_setting:
                                                        draw_curve_ui(subpanel, curve_setting)
                                                if not props.nodes['Randomize'].boolean:
                                                    if transform == 'Rotate':
                                                        panel.prop(props.nodes[f"{transform} Instances"].inputs['Pivot Point'], "default_value", text="Pivot Point")
                                                    elif transform == 'Scale':
                                                        panel.prop(props.nodes[f"{transform} Instances"].inputs['Center'], "default_value", text="Center")
                                                    panel.prop(props.nodes[f"{transform} Instances"].inputs['Local Space'], "default_value", text="Local Space")
                                                panel.separator()
                                        panel.separator()
                                        continue
                                    elif anim_type == 'writing_anim':
                                        if anim_node.name not in vb.formula_animsetting_status:
                                            animsetting_status_reset(context, anim_node.name)
                                            continue
                                        props = anim_node.node_tree
                                        split = panel.split(factor=0.7)
                                        split.label(text=f'Writing Anim')
                                        subrow = split.row(align=True)
                                        status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                        subrow.prop(status,"hide")
                                        op=subrow.operator("math_anim.del_indiv_anim", text="", icon="PANEL_CLOSE")
                                        op.node_tree_name = f"{node.name}"
                                        op.anim_type = f"{anim_type}"
                                        if status.hide:
                                            continue
                                        row = panel.row(align=True)
                                        row.label(text="Effect Range: ")
                                        row.prop(props.nodes['Range Start'], "integer", text="Start")
                                        row.prop(props.nodes['Range End'], "integer", text="End")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes['Start Frame'], "integer", text="Start Frame")
                                        row.prop(props.nodes['Anim Length'], "integer", text="Anim Length")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes['Local'], "boolean", text="Local Writing")
                                        row.prop(props.nodes['Reverse'], "boolean", text="Reverse Writing")
                                        panel.label(text="Writing Anim Curve")
                                        panel.template_curve_mapping(props.nodes['Float Curve'], "mapping")
                                        subheader, subpanel = panel.panel(f"{props.name} preset curves", default_closed=True)
                                        subheader.label(text="Preset Curves")
                                        if subpanel:
                                            curve_node = props.nodes['Float Curve']
                                            curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                            if curve_setting:
                                                draw_curve_ui(subpanel, curve_setting)
                                        ctl_switch = 'Local' if props.nodes['Local'].boolean else 'Global'
                                        split = panel.split(factor=0.5)
                                        if ctl_switch == 'Global':
                                            row = split.row(align=True)
                                            row.prop(props.nodes['Writing Style'].inputs['Menu'], "default_value", expand=True)
                                        if (ctl_switch == 'Global' and props.nodes['Writing Style'].inputs['Menu'].default_value == "Writing") or ctl_switch == 'Local':
                                            split.prop(props.nodes[f'Add {ctl_switch} Writing Symbol'], "boolean", text="Add Writing Symbol")
                                            if props.nodes[f'Add {ctl_switch} Writing Symbol'].boolean:
                                                panel.template_ID(data=props.nodes[f'{ctl_switch} Writing Symbol'].inputs["Font"], property="default_value", open="font.open", unlink="font.unlink", text="Symbol Font")
                                                panel.prop(props.nodes[f'{ctl_switch} Writing Symbol'].inputs['String'], "default_value", text="Symbol")
                                                panel.prop(props.nodes[f'{ctl_switch} Writing Symbol Radius'].outputs['Value'], "default_value", text="Symbol Line Radius")
                                                panel.prop(props.nodes[f'{ctl_switch} Writing Symbol Color'], "value", text="Symbol Color")
                                                panel.prop(props.nodes[f'{ctl_switch} Writing Symbol Color Strength'].outputs['Value'], "default_value", text="Symbol Color Strength")
                                                panel.prop(props.nodes[f'{ctl_switch} Writing Symbol Translation'], "vector", text="Symbol Translation")
                                                panel.prop(props.nodes[f'{ctl_switch} Writing Symbol Rotation'], "rotation_euler", text="Symbol Rotation")
                                                panel.prop(props.nodes[f'{ctl_switch} Writing Symbol Scale'], "vector", text="Symbol Scale")
                                        panel.separator()
                                        continue
                                    elif anim_type == 'color_flow':
                                        if anim_node.name not in vb.formula_animsetting_status:
                                            animsetting_status_reset(context, anim_node.name)
                                            continue
                                        props = anim_node.node_tree
                                        split = panel.split(factor=0.7)
                                        split.label(text=f'Color Flow Anim')
                                        subrow = split.row(align=True)
                                        status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                        subrow.prop(status,"hide")
                                        op=subrow.operator("math_anim.del_indiv_anim", text="", icon="PANEL_CLOSE")
                                        op.node_tree_name = f"{node.name}"
                                        op.anim_type = f"{anim_type}"
                                        if status.hide:
                                            continue
                                        render_type = "GP" if anim_node.outputs[0].links[0].to_node.node_tree.nodes['Menu Switch'].inputs['Menu'].default_value == "Grease Pencil" else "Mesh"
                                        row = panel.row(align=True)
                                        row.label(text="Effect Range: ")
                                        row.prop(props.nodes[f'{render_type} Range Start'], "integer", text="Start")
                                        row.prop(props.nodes[f'{render_type} Range End'], "integer", text="End")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes[f'{render_type} Start Frame'], "integer", text="Start Frame")
                                        row.prop(props.nodes[f'{render_type} Anim Length'], "integer", text="Anim Length")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes[f'{render_type} Flow Length'], "integer", text="Flow Length")
                                        row.prop(props.nodes[f'{render_type} Flow Speed'].outputs['Value'], "default_value", text="Flow Speed")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes[f'{render_type} Flow Radius'].outputs['Value'], "default_value", text="Flow Radius")
                                        row.prop(props.nodes[f'{render_type} Flow Color Strength'].outputs['Value'], "default_value", text="Flow Color Strength")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes[f'{render_type} Flow Offset'].inputs['Menu'], "default_value", text="Flow Offset")
                                        row.prop(props.nodes[f'{render_type} Local Flow'], "boolean", text="Local Flow")
                                        offset_type = props.nodes[f'{render_type} Flow Offset'].inputs['Menu'].default_value
                                        if offset_type == "Normal":
                                            panel.prop(props.nodes[f'{render_type} Flow Offset Normal'].outputs['Value'], "default_value", text="Flow Offset")
                                        else:
                                            panel.prop(props.nodes[f'{render_type} Flow Offset Vector'], "vector", text="Flow Offset")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes[f'{render_type} Reverse Flow'], "boolean", text="Reverse Flow")
                                        row.prop(props.nodes[f'{render_type} Reverse Color'], "boolean", text="Reverse Color")
                                        panel.label(text="Color Flow Anim Curve")
                                        panel.template_curve_mapping(props.nodes[f'{render_type} Float Curve'], "mapping")
                                        subheader, subpanel = panel.panel(f"{props.name} {render_type} preset curves", default_closed=True)
                                        subheader.label(text="Preset Curves")
                                        if subpanel:
                                            curve_node = props.nodes[f'{render_type} Float Curve']
                                            curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                            if curve_setting:
                                                draw_curve_ui(subpanel, curve_setting)
                                        panel.prop(props.nodes[f'{render_type} Change Flow Color'], "boolean", text="Change Flow Color")
                                        if props.nodes[f'{render_type} Change Flow Color'].boolean:
                                            panel.template_color_ramp(props.nodes[f'{render_type} Color Ramp'], "color_ramp")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes[f'{render_type} Flow Color Direction'].inputs['Menu'], "default_value", text="Color Direction")
                                            row.prop(props.nodes[f'{render_type} Flow Style'].inputs['Menu'], "default_value", text="Flow Style")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes[f'{render_type} Spark Particles'], "boolean", text="Spark Particles")
                                        if props.nodes[f'{render_type} Spark Particles'].boolean:
                                            row.prop(props.nodes[f'{render_type} Particle Source'].inputs['Menu'], "default_value", text="Particle Source")
                                            panel.prop(props.nodes[f'{render_type} Particle Instancing Probability'].outputs['Value'], "default_value", text="Particle Instancing Probability")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes[f'{render_type} Particle Lifetime'], "integer", text="Particle Lifetime")
                                            row.prop(props.nodes[f'{render_type} Particle Color Strength'].outputs['Value'], "default_value", text="Particle Color Strength")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes[f'{render_type} Resample Flow Curve'], "boolean", text="Resample Flow Curve")
                                            if props.nodes[f'{render_type} Resample Flow Curve'].boolean:
                                                row.prop(props.nodes[f'{render_type} Resample Count'], "integer", text="Resample Count")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes[f'{render_type} Particle Radius Min'].outputs['Value'], "default_value", text="Particle Radius Min")
                                            row.prop(props.nodes[f'{render_type} Particle Radius Max'].outputs['Value'], "default_value", text="Particle Radius Max")
                                            row = panel.row(align=True)
                                            col = row.column(align=True)
                                            col.prop(props.nodes[f'{render_type} Particle Speed Min'], "vector", text="Particle Speed Min")
                                            col = row.column(align=True)
                                            col.prop(props.nodes[f'{render_type} Particle Speed Max'], "vector", text="Particle Speed Max")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes[f'{render_type} Randomness'], "boolean", text="Speed Randomness")
                                            row.prop(props.nodes[f'{render_type} Seed'], "integer", text="Seed")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes[f'{render_type} Particle to Curve'], "boolean", text="Particle to Curve")
                                            panel.separator()
                                        continue
                                    elif anim_type == 'wave_anim':
                                        l_anim_node = anim_node[0]
                                        if l_anim_node.name not in vb.formula_animsetting_status:
                                            animsetting_status_reset(context, l_anim_node.name)
                                            continue
                                        g_anim_node = anim_node[1]
                                        lprops = l_anim_node.node_tree
                                        gprops = g_anim_node.node_tree
                                        split = panel.split(factor=0.7)
                                        split.label(text=f'Wave Anim')
                                        subrow = split.row(align=True)
                                        status = anim_setting_status[vb.formula_animsetting_status[f"{l_anim_node.name}"]]
                                        subrow.prop(status,"hide")
                                        op=subrow.operator("math_anim.del_indiv_anim", text="", icon="PANEL_CLOSE")
                                        op.node_tree_name = f"{node.name}"
                                        op.anim_type = f"{anim_type}"
                                        if status.hide:
                                            continue
                                        split = panel.split(factor=0.5)
                                        split.prop(gprops.nodes['Passthrough'], 'boolean', text="Global", invert_checkbox=True)
                                        split.prop(lprops.nodes['Passthrough'], 'boolean', text="Local", invert_checkbox=True)
                                        for i, node in enumerate([g_anim_node, l_anim_node]):
                                            props = node.node_tree
                                            split = panel.split(factor=0.8)
                                            split.label(text="Global Wave" if i==0 else "Local Wave")
                                            row = panel.row(align=True)
                                            row.label(text="Effect Range: ")
                                            row.prop(props.nodes['Range Start'], "integer", text="Start")
                                            row.prop(props.nodes['Range End'], "integer", text="End")
                                            row = panel.row(align=True)
                                            if props.nodes["Wave Texture"].wave_type == 'BANDS':
                                                row.prop(props.nodes["Wave Texture"], "bands_direction", text="Wave Direction")
                                            else:
                                                row.prop(props.nodes["Wave Texture"], "rings_direction", text="Wave Direction")
                                            row.prop(props.nodes["Menu Switch"].inputs['Menu'], "default_value", text="Effect On")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes["Wave Texture"], "wave_type", text="Wave Type")
                                            row.prop(props.nodes["Wave Texture"], "wave_profile", text="Wave Profile")
                                            panel.label(text="Wave Control")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes['Speed'].outputs['Value'], "default_value", text="Speed")
                                            row.prop(props.nodes['Scale'].outputs['Value'], "default_value", text="Scale")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes["Wave Texture"].inputs['Distortion'], "default_value", text="Distortion")
                                            row.prop(props.nodes["Wave Texture"].inputs['Detail'], "default_value", text="Detail")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes["Wave Texture"].inputs['Detail Scale'], "default_value", text="Detail Scale")
                                            row.prop(props.nodes["Wave Texture"].inputs['Detail Roughness'], "default_value", text="Detail Roughness")
                                            panel.label(text="Wave Curve Shape")
                                            panel.template_curve_mapping(props.nodes['Float Curve'], "mapping")
                                            subheader, subpanel = panel.panel(f"{props.name} preset curves", default_closed=True)
                                            subheader.label(text="Preset Curves")
                                            if subpanel:
                                                curve_node = props.nodes['Float Curve']
                                                curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                                if curve_setting:
                                                    draw_curve_ui(subpanel, curve_setting)
                                            panel.separator()
                                        continue
                                    elif anim_type == 'flow_anim':
                                        if anim_node[0].name not in vb.formula_animsetting_status:
                                            animsetting_status_reset(context, anim_node[0].name)
                                            continue
                                        split = panel.split(factor=0.7)
                                        split.label(text=f'Edge Flow Anim')
                                        subrow = split.row(align=True)
                                        status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node[0].name}"]]
                                        subrow.prop(status,"hide")
                                        op=subrow.operator("math_anim.del_indiv_anim", text="", icon="PANEL_CLOSE")
                                        op.node_tree_name = f"{node.name}"
                                        op.anim_type = f"{anim_type}"
                                        if status.hide:
                                            continue
                                        for anim in anim_node:
                                            props = anim.node_tree
                                            label = node.node_tree.nodes['String to Curves'].inputs['String'].default_value
                                            panel.label(text=f"{label} (and it's morphs if any)")
                                            subrow = panel.row(align=True)
                                            subrow.prop(props.nodes['Bounding Box'], "boolean", text="Bounding Box")
                                            subrow.prop(props.nodes['Closed Path'].inputs['Switch'], "default_value", text="Closed Path?")
                                            subrow = panel.row(align=True)
                                            subrow.prop(props.nodes['Reverse Flow'], "boolean", text="Reverse")
                                            subrow.prop(props.nodes['Subdivide Curve'].inputs['Cuts'], "default_value", text="Subdivide")
                                            subrow = panel.row(align=True)
                                            subrow.prop(props.nodes['Start Frame'], "integer", text="Start Frame")
                                            subrow.prop(props.nodes['End Frame'], "integer", text="End Frame")
                                            subrow = panel.row(align=True)
                                            subrow.prop(props.nodes['Cycle Length'], "integer", text="Cycle Length")
                                            subrow.prop(props.nodes['Flow Length'].outputs['Value'], "default_value", text="Flow Length")
                                            subrow = panel.row(align=True)
                                            subrow.prop(props.nodes['Scale'].outputs['Value'], "default_value", text="Scale")
                                            subrow.prop(props.nodes['Edge Select'], "integer", text="Edge Selection")
                                            if props.nodes['Bounding Box'].boolean:
                                                subrow = panel.row(align=True)
                                                subrow.prop(props.nodes['BBOX Width Scale'].outputs['Value'], "default_value", text="BBox Width")
                                                subrow.prop(props.nodes['BBOX Height Scale'].outputs['Value'], "default_value", text="BBox Height")
                                            panel.template_color_ramp(props.nodes['Color Ramp'], "color_ramp", expand=True)
                                            panel.prop(props.nodes['Color Strength'].inputs['Value'], "default_value", text="Color Strength")
                                            panel.label(text="Edge Flow Curve Shape")
                                            panel.template_curve_mapping(props.nodes['Float Curve'], "mapping")
                                            subheader, subpanel = panel.panel(f"{props.name} preset curves", default_closed=True)
                                            subheader.label(text="Preset Curves")
                                            if subpanel:
                                                curve_node = props.nodes['Float Curve']
                                                curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                                if curve_setting:
                                                    draw_curve_ui(subpanel, curve_setting)
                                        continue
                                    elif anim_type == 'transform':
                                        if anim_node.name not in vb.formula_animsetting_status:
                                            animsetting_status_reset(context, anim_node.name)
                                            continue
                                        props = anim_node.node_tree
                                        split = panel.split(factor=0.7)
                                        split.label(text=f'Transform')
                                        subrow = split.row(align=True)
                                        status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                        subrow.prop(status,"hide")
                                        op=subrow.operator("math_anim.del_indiv_anim", text="", icon="PANEL_CLOSE")
                                        op.node_tree_name = f"{node.name}"
                                        op.anim_type = f"{anim_type}"
                                        if status.hide:
                                            continue
                                        nodes = [props.nodes['Rotate Instances'], props.nodes['Translate Instances'], props.nodes['Scale Instances']]
                                        for i, node in enumerate(nodes):
                                            if i>0:
                                                panel.separator()
                                                panel.separator()
                                            split = panel.split(factor=0.5)
                                            for socket in node.inputs[2:]:
                                                if socket.name == 'Local Space' or socket.name == 'Translation':
                                                    panel.prop(socket, "default_value", text=socket.name)
                                                else:
                                                    split.prop(socket, "default_value", text=socket.name)
                                        continue
                                    elif anim_type == 'run_number':
                                        if f"{node.name}.{anim_node.name}" not in vb.formula_animsetting_status:
                                            animsetting_status_reset(context, f"{node.name}.{anim_node.name}")
                                            continue
                                        props = anim_node
                                        split = panel.split(factor=0.7)
                                        split.label(text=f'Running Number')
                                        subrow = split.row(align=True)
                                        status = anim_setting_status[vb.formula_animsetting_status[f"{node.name}.{anim_node.name}"]]
                                        subrow.prop(status,"hide")
                                        op=subrow.operator("math_anim.del_indiv_anim", text="", icon="PANEL_CLOSE")
                                        op.node_tree_name = f"{node.name}"
                                        op.anim_type = f"{anim_type}"
                                        if status.hide:
                                            continue
                                        panel.prop(props, 'data_type', text="Data Type")
                                        panel.prop(props.inputs['Value'], 'default_value', text="Run Number")
                                        if props.data_type == 'FLOAT':
                                            panel.prop(props.inputs['Decimals'], 'default_value', text="Decimals")

                elif draw_tag:
                    row = panel.row(align=True)
                    row.alignment = 'CENTER'
                    row.operator("math_anim.group_setup",text="Group Setup", icon='SETTINGS')
                    if 'group_anim' in vb.formula_anim_nodes:
                        anim_types = ['grow_anim', 'writing_anim', 'color_flow', 'wave_anim', 'flow_anim', 'transform_anim', 'transform']
                        for anim_type in anim_types:
                            if anim_type in vb.formula_anim_nodes['group_anim']:
                                for anim_node_name, item in vb.formula_anim_nodes['group_anim'][anim_type].items():
                                    nodes = item[-1]
                                    label = ''
                                    if len(nodes) < 11:
                                        for i, node in enumerate(nodes):
                                            if node.node_tree.nodes.get('String to Curves'):
                                                tt = node.node_tree.nodes['String to Curves'].inputs['String'].default_value
                                                label = tt if i==0 else f"{label}, {tt}"
                                            else:
                                                label = node.name if i==0 else f"{label}, {node.name}"
                                    else:
                                        for i, node in enumerate(nodes):
                                            f_label = ''
                                            l_label = ''
                                            if i < 5:
                                                if node.node_tree.nodes.get('String to Curves'):
                                                    tt = node.node_tree.nodes['String to Curves'].inputs['String'].default_value
                                                    f_label = tt if i==0 else f"{f_label}, {tt}"
                                                else:
                                                    f_label = node.name if i==0 else f"{f_label}, {node.name}"
                                            elif i > len(nodes) - 6:
                                                if node.node_tree.nodes.get('String to Curves'):
                                                    tt = node.node_tree.nodes['String to Curves'].inputs['String'].default_value
                                                    l_label = tt if i==len(nodes)-5 else f"{l_label}, {tt}"
                                                else:
                                                    l_label = node.name if i==len(nodes)-5 else f"{l_label}, {node.name}"
                                        label = f"{f_label}...{l_label}"

                                    if anim_type == 'grow_anim':
                                        anim_node = item[0]
                                        if anim_node.name not in vb.formula_animsetting_status:
                                            animsetting_status_reset(context, anim_node.name)
                                            continue
                                        props = anim_node.node_tree
                                        split = panel.split(factor=0.7)
                                        split.label(text=f'Grow Anim for {label}')
                                        subrow = split.row(align=True)
                                        status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                        subrow.prop(status,"hide")
                                        op=subrow.operator("math_anim.del_group_anim", text="", icon="PANEL_CLOSE")
                                        op.node_name = f"{anim_node.name}**{anim_type}"
                                        if status.hide:
                                            continue
                                        row = panel.row(align=True)
                                        row.label(text="Effect Range: ")
                                        row.prop(props.nodes['Start'], "integer", text="Start")
                                        row.prop(props.nodes['End'], "integer", text="End")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes['Start Frame'], "integer", text="Start Frame")
                                        row.prop(props.nodes['Anim Length'], "integer", text="Anim Length")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes['Local'], "boolean", text="Local Grow")
                                        row.prop(props.nodes['Reverse Grow'], "boolean", text="Reverse Grow")
                                        panel.prop(props.nodes['Center'], "vector", text="Grow Center")
                                        panel.label(text="Grow Anim Curve")
                                        panel.template_curve_mapping(props.nodes['Float Curve'], "mapping")
                                        subheader, subpanel = panel.panel(f"{props.name} preset curves", default_closed=True)
                                        subheader.label(text="Preset Curves")
                                        if subpanel:
                                            curve_node = props.nodes['Float Curve']
                                            curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                            if curve_setting:
                                                draw_curve_ui(subpanel, curve_setting)
                                        panel.separator()
                                        continue
                                    if anim_type == 'transform_anim':
                                        anim_node = item[0]
                                        if anim_node.name not in vb.formula_animsetting_status:
                                            animsetting_status_reset(context, anim_node.name)
                                            continue
                                        props = anim_node.node_tree
                                        split = panel.split(factor=0.7)
                                        split.label(text=f'Transform Anim')
                                        subrow = split.row(align=True)
                                        status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                        subrow.prop(status,"hide")
                                        op=subrow.operator("math_anim.del_indiv_anim", text="", icon="PANEL_CLOSE")
                                        op.node_tree_name = f"{node.name}"
                                        op.anim_type = f"{anim_type}"
                                        if status.hide:
                                            continue
                                        row = panel.row(align=True)
                                        row.label(text="Effect Range: ")
                                        row.prop(props.nodes['Range Start'], "integer", text="Start")
                                        row.prop(props.nodes['Range End'], "integer", text="End")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes['Start Frame'], "integer", text="Start Frame")
                                        row.prop(props.nodes['Anim Length'], "integer", text="Anim Length")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes['Reverse'], "boolean", text="Reverse")
                                        row.prop(props.nodes['Randomize'], "boolean", text="Randomize")
                                        if props.nodes['Randomize'].boolean:
                                            row.prop(props.nodes['Seed'], "integer", text="Seed")
                                        panel.prop(props.nodes['Keep Before Start'], "boolean", text="Keep Before Start or After End")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes['Bypass Rotate'], "boolean", text="Mute Rotate")
                                        row.prop(props.nodes['Bypass Offset'], "boolean", text="Mute Offset")
                                        row.prop(props.nodes['Bypass Scale'], "boolean", text="Mute Scale")
                                        for transform in ['Rotate', 'Offset', 'Scale']:
                                            if not props.nodes[f'Bypass {transform}'].boolean:
                                                panel.label(text=f"{transform} Anim Setting")
                                                panel.prop(props.nodes[f'{transform} Mix'].inputs['A'], "default_value", text=f"{transform}")
                                                panel.label(text=f"{transform} Anim Curve")
                                                panel.template_curve_mapping(props.nodes[f'{transform} Anim Curve'], "mapping")
                                                subheader, subpanel = panel.panel(f"{props.name} {transform} preset curves", default_closed=True)
                                                subheader.label(text="Preset Curves")
                                                if subpanel:
                                                    curve_node = props.nodes[f'{transform} Anim Curve']
                                                    curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                                    if curve_setting:
                                                        draw_curve_ui(subpanel, curve_setting)
                                                if not props.nodes['Randomize'].boolean:
                                                    if transform == 'Rotate':
                                                        panel.prop(props.nodes[f"{transform} Instances"].inputs['Pivot Point'], "default_value", text="Pivot Point")
                                                    elif transform == 'Scale':
                                                        panel.prop(props.nodes[f"{transform} Instances"].inputs['Center'], "default_value", text="Center")
                                                    panel.prop(props.nodes[f"{transform} Instances"].inputs['Local Space'], "default_value", text="Local Space")
                                                panel.separator()
                                        panel.separator()
                                        continue
                                    elif anim_type == 'writing_anim':
                                        anim_node = item[0]
                                        if anim_node.name not in vb.formula_animsetting_status:
                                            animsetting_status_reset(context, anim_node.name)
                                            continue
                                        props = anim_node.node_tree
                                        split = panel.split(factor=0.7)
                                        split.label(text=f'Writing Anim for {label}')
                                        subrow = split.row(align=True)
                                        status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                        subrow.prop(status,"hide")
                                        op=subrow.operator("math_anim.del_group_anim", text="", icon="PANEL_CLOSE")
                                        op.node_name = f"{anim_node.name}**{anim_type}"
                                        if status.hide:
                                            continue
                                        row = panel.row(align=True)
                                        row.label(text="Effect Range: ")
                                        row.prop(props.nodes['Range Start'], "integer", text="Start")
                                        row.prop(props.nodes['Range End'], "integer", text="End")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes['Start Frame'], "integer", text="Start Frame")
                                        row.prop(props.nodes['Anim Length'], "integer", text="Anim Length")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes['Local'], "boolean", text="Local Writing")
                                        row.prop(props.nodes['Reverse'], "boolean", text="Reverse Writing")
                                        panel.label(text="Writing Anim Curve")
                                        panel.template_curve_mapping(props.nodes['Float Curve'], "mapping")
                                        subheader, subpanel = panel.panel(f"{props.name} preset curves", default_closed=True)
                                        subheader.label(text="Preset Curves")
                                        if subpanel:
                                            curve_node = props.nodes['Float Curve']
                                            curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                            if curve_setting:
                                                draw_curve_ui(subpanel, curve_setting)
                                        ctl_switch = 'Local' if props.nodes['Local'].boolean else 'Global'
                                        split = panel.split(factor=0.5)
                                        if ctl_switch == 'Global':
                                            row = split.row(align=True)
                                            row.prop(props.nodes['Writing Style'].inputs['Menu'], "default_value", expand=True)
                                        if (ctl_switch == 'Global' and props.nodes['Writing Style'].inputs['Menu'].default_value == "Writing") or ctl_switch == 'Local':
                                            split.prop(props.nodes[f'Add {ctl_switch} Writing Symbol'], "boolean", text="Add Writing Symbol")
                                            if props.nodes[f'Add {ctl_switch} Writing Symbol'].boolean:
                                                panel.template_ID(data=props.nodes[f'{ctl_switch} Writing Symbol'].inputs["Font"], property="default_value", open="font.open", unlink="font.unlink", text="Symbol Font")
                                                panel.prop(props.nodes[f'{ctl_switch} Writing Symbol'].inputs['String'], "default_value", text="Symbol")
                                                panel.prop(props.nodes[f'{ctl_switch} Writing Symbol Radius'].outputs['Value'], "default_value", text="Symbol Line Radius")
                                                panel.prop(props.nodes[f'{ctl_switch} Writing Symbol Color'], "value", text="Symbol Color")
                                                panel.prop(props.nodes[f'{ctl_switch} Writing Symbol Color Strength'].outputs['Value'], "default_value", text="Symbol Color Strength")
                                                panel.prop(props.nodes[f'{ctl_switch} Writing Symbol Translation'], "vector", text="Symbol Translation")
                                                panel.prop(props.nodes[f'{ctl_switch} Writing Symbol Rotation'], "rotation_euler", text="Symbol Rotation")
                                                panel.prop(props.nodes[f'{ctl_switch} Writing Symbol Scale'], "vector", text="Symbol Scale")
                                        panel.separator()
                                        continue
                                    elif anim_type == 'color_flow':
                                        anim_node = item[0]
                                        if anim_node.name not in vb.formula_animsetting_status:
                                            animsetting_status_reset(context, anim_node.name)
                                            continue
                                        props = anim_node.node_tree
                                        split = panel.split(factor=0.7)
                                        split.label(text=f'Color Flow Anim')
                                        subrow = split.row(align=True)
                                        status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                        subrow.prop(status,"hide")
                                        op=subrow.operator("math_anim.del_group_anim", text="", icon="PANEL_CLOSE")
                                        op.node_name = f"{anim_node.name}**{anim_type}"
                                        if status.hide:
                                            continue
                                        render_type = "GP" if anim_node.outputs[0].links[0].to_node.node_tree.nodes['Menu Switch'].inputs['Menu'].default_value == "Grease Pencil" else "Mesh"
                                        row = panel.row(align=True)
                                        row.label(text="Effect Range: ")
                                        row.prop(props.nodes[f'{render_type} Range Start'], "integer", text="Start")
                                        row.prop(props.nodes[f'{render_type} Range End'], "integer", text="End")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes[f'{render_type} Start Frame'], "integer", text="Start Frame")
                                        row.prop(props.nodes[f'{render_type} Anim Length'], "integer", text="Anim Length")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes[f'{render_type} Flow Length'], "integer", text="Flow Length")
                                        row.prop(props.nodes[f'{render_type} Flow Speed'].outputs['Value'], "default_value", text="Flow Speed")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes[f'{render_type} Flow Radius'].outputs['Value'], "default_value", text="Flow Radius")
                                        row.prop(props.nodes[f'{render_type} Flow Color Strength'].outputs['Value'], "default_value", text="Flow Color Strength")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes[f'{render_type} Flow Offset'].inputs['Menu'], "default_value", text="Flow Offset")
                                        row.prop(props.nodes[f'{render_type} Local Flow'], "boolean", text="Local Flow")
                                        offset_type = props.nodes[f'{render_type} Flow Offset'].inputs['Menu'].default_value
                                        if offset_type == "Normal":
                                            panel.prop(props.nodes[f'{render_type} Flow Offset Normal'].outputs['Value'], "default_value", text="Flow Offset")
                                        else:
                                            panel.prop(props.nodes[f'{render_type} Flow Offset Vector'], "vector", text="Flow Offset")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes[f'{render_type} Reverse Flow'], "boolean", text="Reverse Flow")
                                        row.prop(props.nodes[f'{render_type} Reverse Color'], "boolean", text="Reverse Color")
                                        panel.label(text="Color Flow Anim Curve")
                                        panel.template_curve_mapping(props.nodes[f'{render_type} Float Curve'], "mapping")
                                        subheader, subpanel = panel.panel(f"{props.name} {render_type} preset curves", default_closed=True)
                                        subheader.label(text="Preset Curves")
                                        if subpanel:
                                            curve_node = props.nodes[f'{render_type} Float Curve']
                                            curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                            if curve_setting:
                                                draw_curve_ui(subpanel, curve_setting)
                                        panel.prop(props.nodes[f'{render_type} Change Flow Color'], "boolean", text="Change Flow Color")
                                        if props.nodes[f'{render_type} Change Flow Color'].boolean:
                                            panel.template_color_ramp(props.nodes[f'{render_type} Color Ramp'], "color_ramp")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes[f'{render_type} Flow Color Direction'].inputs['Menu'], "default_value", text="Color Direction")
                                            row.prop(props.nodes[f'{render_type} Flow Style'].inputs['Menu'], "default_value", text="Flow Style")
                                        row = panel.row(align=True)
                                        row.prop(props.nodes[f'{render_type} Spark Particles'], "boolean", text="Spark Particles")
                                        if props.nodes[f'{render_type} Spark Particles'].boolean:
                                            row.prop(props.nodes[f'{render_type} Particle Source'].inputs['Menu'], "default_value", text="Particle Source")
                                            panel.prop(props.nodes[f'{render_type} Particle Instancing Probability'].outputs['Value'], "default_value", text="Particle Instancing Probability")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes[f'{render_type} Particle Lifetime'], "integer", text="Particle Lifetime")
                                            row.prop(props.nodes[f'{render_type} Particle Color Strength'].outputs['Value'], "default_value", text="Particle Color Strength")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes[f'{render_type} Resample Flow Curve'], "boolean", text="Resample Flow Curve")
                                            if props.nodes[f'{render_type} Resample Flow Curve'].boolean:
                                                row.prop(props.nodes[f'{render_type} Resample Count'], "integer", text="Resample Count")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes[f'{render_type} Particle Radius Min'].outputs['Value'], "default_value", text="Particle Radius Min")
                                            row.prop(props.nodes[f'{render_type} Particle Radius Max'].outputs['Value'], "default_value", text="Particle Radius Max")
                                            row = panel.row(align=True)
                                            col = row.column(align=True)
                                            col.prop(props.nodes[f'{render_type} Particle Speed Min'], "vector", text="Particle Speed Min")
                                            col = row.column(align=True)
                                            col.prop(props.nodes[f'{render_type} Particle Speed Max'], "vector", text="Particle Speed Max")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes[f'{render_type} Randomness'], "boolean", text="Speed Randomness")
                                            row.prop(props.nodes[f'{render_type} Seed'], "integer", text="Seed")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes[f'{render_type} Particle to Curve'], "boolean", text="Particle to Curve")
                                            panel.separator()
                                        continue
                                    elif anim_type == 'wave_anim':
                                        l_anim_node = item[0]
                                        g_anim_node = item[1]
                                        if l_anim_node.name not in vb.formula_animsetting_status:
                                            animsetting_status_reset(context, l_anim_node.name)
                                            continue
                                        lprops = l_anim_node.node_tree
                                        gprops = g_anim_node.node_tree
                                        split = panel.split(factor=0.7)
                                        split.label(text=f'Wave Anim for {label}')
                                        subrow = split.row(align=True)
                                        status = anim_setting_status[vb.formula_animsetting_status[f"{l_anim_node.name}"]]
                                        subrow.prop(status,"hide")
                                        op=subrow.operator("math_anim.del_group_anim", text="", icon="PANEL_CLOSE")
                                        op.node_name = f"{l_anim_node.name}**{anim_type}"
                                        if status.hide:
                                            continue
                                        split = panel.split(factor=0.5)
                                        split.prop(gprops.nodes['Passthrough'], 'boolean', text="Global", invert_checkbox=True)
                                        split.prop(lprops.nodes['Passthrough'], 'boolean', text="Local", invert_checkbox=True)
                                        for i, node in enumerate([g_anim_node, l_anim_node]):
                                            props = node.node_tree
                                            split = panel.split(factor=0.8)
                                            split.label(text="Global Wave" if i==0 else "Local Wave")
                                            row = panel.row(align=True)
                                            row.label(text="Effect Range: ")
                                            row.prop(props.nodes['Range Start'], "integer", text="Start")
                                            row.prop(props.nodes['Range End'], "integer", text="End")
                                            row = panel.row(align=True)
                                            if props.nodes["Wave Texture"].wave_type == 'BANDS':
                                                row.prop(props.nodes["Wave Texture"], "bands_direction", text="Wave Direction")
                                            else:
                                                row.prop(props.nodes["Wave Texture"], "rings_direction", text="Wave Direction")
                                            row.prop(props.nodes["Menu Switch"].inputs['Menu'], "default_value", text="Effect On")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes["Wave Texture"], "wave_type", text="Wave Type")
                                            row.prop(props.nodes["Wave Texture"], "wave_profile", text="Wave Profile")
                                            panel.label(text="Wave Control")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes['Speed'].outputs['Value'], "default_value", text="Speed")
                                            row.prop(props.nodes['Scale'].outputs['Value'], "default_value", text="Scale")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes["Wave Texture"].inputs['Distortion'], "default_value", text="Distortion")
                                            row.prop(props.nodes["Wave Texture"].inputs['Detail'], "default_value", text="Detail")
                                            row = panel.row(align=True)
                                            row.prop(props.nodes["Wave Texture"].inputs['Detail Scale'], "default_value", text="Detail Scale")
                                            row.prop(props.nodes["Wave Texture"].inputs['Detail Roughness'], "default_value", text="Detail Roughness")
                                            panel.label(text="Wave Curve Shape")
                                            panel.template_curve_mapping(props.nodes['Float Curve'], "mapping")
                                            subheader, subpanel = panel.panel(f"{props.name} preset curves", default_closed=True)
                                            subheader.label(text="Preset Curves")
                                            if subpanel:
                                                curve_node = props.nodes['Float Curve']
                                                curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                                if curve_setting:
                                                    draw_curve_ui(subpanel, curve_setting)
                                            panel.separator()
                                        continue
                                    elif anim_type == 'flow_anim':
                                        anim_node = item[0]
                                        if anim_node.name not in vb.formula_animsetting_status:
                                            animsetting_status_reset(context, anim_node.name)
                                            continue
                                        props = anim_node.node_tree
                                        split = panel.split(factor=0.7)
                                        split.label(text=f'Edge Flow Anim for {label}')
                                        subrow = split.row(align=True)
                                        status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                        subrow.prop(status,"hide")
                                        op=subrow.operator("math_anim.del_group_anim", text="", icon="PANEL_CLOSE")
                                        op.node_name = f"{anim_node.name}**{anim_type}"
                                        if status.hide:
                                            continue
                                        subrow = panel.row(align=True)
                                        subrow.prop(props.nodes['Bounding Box'], "boolean", text="Bounding Box")
                                        subrow.prop(props.nodes['Closed Path'].inputs['Switch'], "default_value", text="Closed Path?")
                                        subrow = panel.row(align=True)
                                        subrow.prop(props.nodes['Reverse Flow'], "boolean", text="Reverse")
                                        subrow.prop(props.nodes['Subdivide Curve'].inputs['Cuts'], "default_value", text="Subdivide")
                                        subrow = panel.row(align=True)
                                        subrow.prop(props.nodes['Start Frame'], "integer", text="Start Frame")
                                        subrow.prop(props.nodes['End Frame'], "integer", text="End Frame")
                                        subrow = panel.row(align=True)
                                        subrow.prop(props.nodes['Cycle Length'], "integer", text="Cycle Length")
                                        subrow.prop(props.nodes['Flow Length'].outputs['Value'], "default_value", text="Flow Length")
                                        subrow = panel.row(align=True)
                                        subrow.prop(props.nodes['Scale'].outputs['Value'], "default_value", text="Scale")
                                        subrow.prop(props.nodes['Edge Select'], "integer", text="Edge Selection")
                                        if props.nodes['Bounding Box'].boolean:
                                            subrow = panel.row(align=True)
                                            subrow.prop(props.nodes['BBOX Width Scale'].outputs['Value'], "default_value", text="BBox Width")
                                            subrow.prop(props.nodes['BBOX Height Scale'].outputs['Value'], "default_value", text="BBox Height")
                                        panel.template_color_ramp(props.nodes['Color Ramp'], "color_ramp", expand=True)
                                        panel.prop(props.nodes['Color Strength'].inputs['Value'], "default_value", text="Color Strength")
                                        panel.label(text="Edge Flow Curve Shape")
                                        panel.template_curve_mapping(props.nodes['Float Curve'], "mapping")
                                        subheader, subpanel = panel.panel(f"{props.name} preset curves", default_closed=True)
                                        subheader.label(text="Preset Curves")
                                        if subpanel:
                                            curve_node = props.nodes['Float Curve']
                                            curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                            if curve_setting:
                                                draw_curve_ui(subpanel, curve_setting)
                                        continue
                                    elif anim_type == 'transform':
                                        anim_node = item[0]
                                        if anim_node.name not in vb.formula_animsetting_status:
                                            animsetting_status_reset(context, anim_node.name)
                                            continue
                                        props = anim_node.node_tree
                                        split = panel.split(factor=0.7)
                                        split.label(text=f'Transform for {label}')
                                        subrow = split.row(align=True)
                                        status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                        subrow.prop(status,"hide")
                                        op=subrow.operator("math_anim.del_group_anim", text="", icon="PANEL_CLOSE")
                                        op.node_name = f"{anim_node.name}**{anim_type}"
                                        if status.hide:
                                            continue
                                        nodes = [props.nodes['Rotate Instances'], props.nodes['Translate Instances'], props.nodes['Scale Instances']]
                                        for i, node in enumerate(nodes):
                                            if i>0:
                                                panel.separator()
                                                panel.separator()
                                            split = panel.split(factor=0.5)
                                            for socket in node.inputs[2:]:
                                                if socket.name == 'Local Space' or socket.name == 'Translation':
                                                    panel.prop(socket, "default_value", text=socket.name)
                                                else:
                                                    split.prop(socket, "default_value", text=socket.name)


        # drawing ui
        header, panel = layout.panel("math_anim_drawing", default_closed=True)
        header.label(text="Free Drawer")
        if panel:
            gplayers  = context.scene.math_anim_gplayers
            gpobjects = context.scene.math_anim_gpobjects
            split= panel.split(factor=0.7)
            split.prop(gpobjects, "gp_object", text='Drawer Obj', icon='OUTLINER_OB_GREASEPENCIL')
            op = split.operator("math_anim.add_gp_obj", text="Add Drawer", icon='ADD')
            op.obj_name = "Drawer"
            op.geomd_category = 'DRAWER'
            split= panel.split(factor=0.7)
            split.prop(gplayers, "gp_layer", text='Layer', icon='OUTLINER_DATA_GP_LAYER')
            split.prop(gplayers, "draw_mode", text="Draw Mode", icon='GREASEPENCIL')
            panel.operator("math_anim.update_morph_objects",text="Update Layer Tree", icon='FILE_REFRESH')
            op = panel.operator_menu_enum("math_anim.add_gp_anim", "add_anim")
            op.track_tag = 'drawer_anim'
            row = panel.row(align=True)
            row.prop_enum(gpobjects, "settings", "OBJECT")
            row.prop_enum(gpobjects, "settings", "LAYER")
            row.prop_enum(gpobjects, "settings", "LAYER_ANIM")
            gp_obj = bpy.data.objects.get(gpobjects.gp_object)
            if gp_obj and gpobjects.settings == 'OBJECT' or gpobjects.settings == 'LAYER':
                props, props2 = None, None
                if gpobjects.settings == 'OBJECT':
                    if gp_obj["math_anim_obj"] in vb.gpencil_layer_nodes and gp_obj["math_anim_obj"] in vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]]:
                        props = vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]][gp_obj["math_anim_obj"]].nodes['GP Material']
                else:
                    gp_layer = gp_obj.data.layers.get(gplayers.gp_layer)
                    if gp_layer and gp_obj["math_anim_obj"] in vb.gpencil_layer_nodes and gp_layer.name in vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]]:
                        props = vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]][gp_layer.name].node_tree.nodes['GP Material']
                        props2 = vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]][gp_layer.name]
                if props:
                    if gpobjects.settings == 'OBJECT':
                        panel.prop(props.inputs['Color Strength'], 'default_value', text="Color Strength")
                    else:
                        if props2.node_tree.users > 1:
                            if 'morph_anim' in vb.formula_anim_nodes and len(vb.formula_anim_nodes['morph_anim'])>0:
                                found = False
                                for index, morph_chain in enumerate(vb.formula_anim_nodes['morph_anim']):
                                    for key, morph_list in morph_chain.items():
                                        for morph_node, mute_nodes, morph_setting in morph_list:
                                            source_node = mute_nodes[0]
                                            morph_node = source_node.node_tree.nodes.get(f'{props2.node_tree.name}.Morph')
                                            if morph_node:
                                                panel.prop(morph_node.inputs['Color Strength'], 'default_value', text="Color Strength")
                                                found = True
                                                break
                                        if found:
                                            break
                                    if found:
                                        break
                        else:
                            panel.prop(gp_layer, 'use_lights', text="Interact with Lights")
                            panel.prop(props2.inputs['Color Strength'], 'default_value', text="Color Strength")
                        panel.prop(props.inputs['Material Index'], 'default_value', text="Material Index")
                    panel.prop(props.inputs['Use Custom Radius'], 'default_value', text="Use Custom Radius")
                    panel.prop(props.inputs['Radius'], 'default_value', text="Curve Radius")
                    if props2:
                        panel.prop(props2.inputs['As Points'], 'default_value', text="As Points")
                    panel.prop(props.inputs['Use Custom Color'], 'default_value', text="Use Custom Color")
                    if props.inputs['Use Custom Color'].default_value:
                        panel.template_color_ramp(props.node_tree.nodes['Color Ramp'], 'color_ramp')
                        panel.prop(props.inputs['Color Direction'], 'default_value', text="Color Direction")
                    panel.prop(props.inputs['Use Custom Fill'], 'default_value', text="Use Custom Fill")
                    if props.inputs['Use Custom Fill'].default_value:
                        panel.template_color_ramp(props.node_tree.nodes['Fill Color Ramp'], 'color_ramp')
                        panel.prop(props.inputs['Fill Direction'], 'default_value', text="Fill Direction")
            elif gp_obj and gpobjects.settings == 'LAYER_ANIM':
                gp_layer = gp_obj.data.layers.get(gplayers.gp_layer)
                if gp_layer:
                    anim_types = ['grow_anim', 'writing_anim', 'light_flow', 'wave_anim', 'flow_anim', 'transform_anim', 'transform', 'add_snapshot', 'curve_normal_tangent']
                    for anim_type in anim_types:
                        if 'drawer_anim' in vb.formula_anim_nodes and gp_obj["math_anim_obj"] in vb.formula_anim_nodes['drawer_anim'] and gp_layer.name in vb.formula_anim_nodes['drawer_anim'][gp_obj["math_anim_obj"]] and anim_type in vb.formula_anim_nodes['drawer_anim'][gp_obj["math_anim_obj"]][gp_layer.name]:
                            anim_nodes = vb.formula_anim_nodes['drawer_anim'][gp_obj["math_anim_obj"]][gp_layer.name][anim_type]
                            if anim_type == 'grow_anim':
                                for anim_node in anim_nodes:
                                    if anim_node.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, anim_node.name)
                                        continue
                                    props = anim_node
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Grow Anim')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{anim_node.id_data.name}**{anim_node.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'drawer_anim'
                                    if status.hide:
                                        continue
                                    row = panel.row(align=True)
                                    row.label(text="Effect Range: ")
                                    row.prop(props.inputs['Range Start'], "default_value", text="Range Start")
                                    row.prop(props.inputs['Range End'], "default_value", text="Range End")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Start Frame'], "default_value", text="Start Frame")
                                    row.prop(props.inputs['Anim Length'], "default_value", text="Anim Length")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Local'], "default_value", text="Local Grow")
                                    row.prop(props.inputs['Reverse'], "default_value", text="Reverse Grow")
                                    panel.prop(props.inputs['Center'].links[0].from_node.inputs[1], "default_value", text="Grow Center")
                                    panel.label(text="Grow Anim Curve")
                                    panel.template_curve_mapping(props.node_tree.nodes['Float Curve'], "mapping")
                                    subheader, subpanel = panel.panel(f"{props.node_tree.name} preset curves", default_closed=True)
                                    subheader.label(text="Preset Curves")
                                    if subpanel:
                                        curve_node = props.node_tree.nodes['Float Curve']
                                        curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                        if curve_setting:
                                            draw_curve_ui(subpanel, curve_setting)
                                    panel.separator()
                                continue
                            elif anim_type == 'writing_anim':
                                for anim_node in anim_nodes:
                                    if anim_node.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, anim_node.name)
                                        continue
                                    props = anim_node
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Writing Anim')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{anim_node.id_data.name}**{anim_node.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'drawer_anim'
                                    if status.hide:
                                        continue
                                    row = panel.row(align=True)
                                    row.label(text="Effect Range: ")
                                    row.prop(props.inputs['Range Start'], "default_value", text="Range Start")
                                    row.prop(props.inputs['Range End'], "default_value", text="Range End")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Start Frame'], "default_value", text="Start Frame")
                                    row.prop(props.inputs['Anim Length'], "default_value", text="Anim Length")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Local'], "default_value", text="Local Writing")
                                    row.prop(props.inputs['Reverse'], "default_value", text="Reverse Writing")
                                    panel.label(text="Writing Anim Curve")
                                    panel.template_curve_mapping(props.node_tree.nodes['Float Curve'], "mapping")
                                    subheader, subpanel = panel.panel(f"{props.node_tree.name} preset curves", default_closed=True)
                                    subheader.label(text="Preset Curves")
                                    if subpanel:
                                        curve_node = props.node_tree.nodes['Float Curve']
                                        curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                        if curve_setting:
                                            draw_curve_ui(subpanel, curve_setting)
                                    ctl_switch = "Local" if props.inputs['Local'].default_value else "Global"
                                    panel.prop(props.inputs[f'Add {ctl_switch} Writing Symbol'], "default_value", text="Add Writing Symbol")
                                    if props.inputs[f'Add {ctl_switch} Writing Symbol'].default_value:
                                        panel.template_ID(data=props.node_tree.nodes[f'{ctl_switch} Writing Symbol'].inputs["Font"], property="default_value", open="font.open", unlink="font.unlink", text="Symbol Font")
                                        panel.prop(props.node_tree.nodes[f'{ctl_switch} Writing Symbol'].inputs['String'], "default_value", text="Symbol")
                                        panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Radius'], "default_value", text="Symbol Line Radius")
                                        panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Color'], "default_value", text="Symbol Color")
                                        panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Color Strength'], "default_value", text="Symbol Color Strength")
                                        panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Translation'], "default_value", text="Symbol Translation")
                                        panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Rotation'], "default_value", text="Symbol Rotation")
                                        panel.prop(props.inputs[f'{ctl_switch} Writing Symbol Scale'], "default_value", text="Symbol Scale")
                                    panel.separator()
                                continue
                            elif anim_type == 'light_flow':
                                for anim_node in anim_nodes:
                                    if anim_node.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, anim_node.name)
                                        continue
                                    props = anim_node
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Light Flow Anim')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{anim_node.id_data.name}**{anim_node.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'drawer_anim'
                                    if status.hide:
                                        continue
                                    row = panel.row(align=True)
                                    row.label(text="Effect Range: ")
                                    row.prop(props.inputs['Range Start'], "default_value", text="Start")
                                    row.prop(props.inputs['Range End'], "default_value", text="End")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Start Frame'], "default_value", text="Start Frame")
                                    row.prop(props.inputs['Anim Length'], "default_value", text="Anim Length")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Flow Length'], "default_value", text="Flow Length")
                                    row.prop(props.inputs['Flow Speed'], "default_value", text="Flow Speed")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Flow Radius Multiplier'], "default_value", text="Flow Radius Multiplier")
                                    row.prop(props.inputs['Flow Light Strength'], "default_value", text="Flow Light Strength")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Flow Offset'], "default_value", text="Flow Offset")
                                    row.prop(props.inputs['Reverse Flow'], "default_value", text="Reverse Flow")
                                    if props.inputs['Flow Offset'].default_value == "Normal":
                                        panel.prop(props.inputs['Flow Offset Normal'], "default_value", text="Flow Offset")
                                    else:
                                        panel.prop(props.inputs['Flow Offset Vector'], "default_value", text="Flow Offset")
                                    panel.label(text="Light Flow Anim Curve")
                                    panel.template_curve_mapping(props.node_tree.nodes['Anim Curve'], "mapping")
                                    subheader, subpanel = panel.panel(f"{props.node_tree.name} preset curves", default_closed=True)
                                    subheader.label(text="Preset Curves")
                                    if subpanel:
                                        curve_node = props.node_tree.nodes['Anim Curve']
                                        curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                        if curve_setting:
                                            draw_curve_ui(subpanel, curve_setting)
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Change Color'], "default_value", text="Change Color")
                                    if props.inputs['Change Color'].default_value:
                                        row.prop(props.inputs['Color Direction'], "default_value", text="Color Direction")
                                        panel.template_color_ramp(props.node_tree.nodes['Color Ramp'], "color_ramp", expand=True)
                                    row = panel.row(align=True)
                                    row.prop(props.inputs["Color Direction"], "default_value", text="Color Direction")
                                    row.prop(props.inputs['Flow Style'], "default_value", text="Flow Style")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Spark Particles'], "default_value", text="Spark Particles")
                                    if props.inputs['Spark Particles'].default_value:
                                        row.prop(props.inputs['Particle Source'], "default_value", text="Particle Source")
                                        panel.prop(props.inputs['Particle Instancing Probability'], "default_value", text="Particle Instancing Probability")
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['Particle Lifetime'], "default_value", text="Particle Lifetime")
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['Particle Radius Multiplier'], "default_value", text="Particle Radius Multiplier")
                                        row.prop(props.inputs['Particle Light Strength'], "default_value", text="Particle Light Strength")
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['Resample Curve'], "default_value", text="Resample Curve")
                                        if props.inputs['Resample Curve'].default_value:
                                            row.prop(props.inputs['Resample Count'], "default_value", text="Resample Count")
                                        row = panel.row(align=True)
                                        col = row.column(align=True)
                                        col.prop(props.inputs['Particle Speed Min'], "default_value", text="Particle Speed Min")
                                        col = row.column(align=True)
                                        col.prop(props.inputs['Particle Speed Max'], "default_value", text="Particle Speed Max")
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['Randomness'], "default_value", text="Speed Randomness")
                                        row.prop(props.inputs['Seed'], "default_value", text="Seed")
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['Particle to Curve'], "default_value", text="Particles to Curve")
                                    panel.separator()
                                continue
                            elif anim_type == 'wave_anim':
                                for anim_node in anim_nodes:
                                    gprops, lprops = anim_node
                                    if gprops.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, gprops.name)
                                        continue
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Wave Anim')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{gprops.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{gprops.id_data.name}**{gprops.name}**{lprops.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'drawer_anim'
                                    if status.hide:
                                        continue
                                    split = panel.split(factor=0.5)
                                    split.prop(gprops.inputs['Passthrough'], 'default_value', text="Global", invert_checkbox=True)
                                    split.prop(lprops.inputs['Passthrough'], 'default_value', text="Local", invert_checkbox=True)
                                    for i, props in enumerate([gprops, lprops]):
                                        panel.label(text="Global Wave" if i==0 else "Local Wave")
                                        row = panel.row(align=True)
                                        row.label(text="Effect Range: ")
                                        row.prop(props.inputs['Range Start'], "default_value", text="Range Start")
                                        row.prop(props.inputs['Range End'], "default_value", text="Range End")
                                        row = panel.row(align=True)
                                        if props.node_tree.nodes["Wave Texture"].wave_type == 'BANDS':
                                            row.prop(props.node_tree.nodes["Wave Texture"], "bands_direction", text="Wave Direction")
                                        else:
                                            row.prop(props.node_tree.nodes["Wave Texture"], "rings_direction", text="Wave Direction")
                                        row.prop(props.node_tree.nodes["Menu Switch"].inputs['Menu'], "default_value", text="Effect On")
                                        row = panel.row(align=True)
                                        row.prop(props.node_tree.nodes["Wave Texture"], "wave_type", text="Wave Type")
                                        row.prop(props.node_tree.nodes["Wave Texture"], "wave_profile", text="Wave Profile")
                                        panel.label(text="Wave Control")
                                        row = panel.row(align=True)
                                        row.prop(props.inputs['Speed'], "default_value", text="Speed")
                                        row.prop(props.inputs['Scale'], "default_value", text="Scale")
                                        row = panel.row(align=True)
                                        row.prop(props.node_tree.nodes["Wave Texture"].inputs['Distortion'], "default_value", text="Distortion")
                                        row.prop(props.node_tree.nodes["Wave Texture"].inputs['Detail'], "default_value", text="Detail")
                                        row = panel.row(align=True)
                                        row.prop(props.node_tree.nodes["Wave Texture"].inputs['Detail Scale'], "default_value", text="Detail Scale")
                                        row.prop(props.node_tree.nodes["Wave Texture"].inputs['Detail Roughness'], "default_value", text="Detail Roughness")
                                        panel.label(text="Wave Curve Shape")
                                        panel.template_curve_mapping(props.node_tree.nodes['Float Curve'], "mapping")
                                        subheader, subpanel = panel.panel(f"{props.node_tree.name} preset curves", default_closed=True)
                                        subheader.label(text="Preset Curves")
                                        if subpanel:
                                            curve_node = props.node_tree.nodes['Float Curve']
                                            curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                            if curve_setting:
                                                draw_curve_ui(subpanel, curve_setting)
                                        panel.separator()
                                continue
                            elif anim_type == 'flow_anim':
                                for anim_node in anim_nodes:
                                    if anim_node.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, anim_node.name)
                                        continue
                                    props = anim_node
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Edge Flow Anim')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{anim_node.id_data.name}**{anim_node.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'drawer_anim'
                                    if status.hide:
                                        continue
                                    subrow = panel.row(align=True)
                                    subrow.prop(props.inputs['Bounding Box'], "default_value", text="Bounding Box")
                                    subrow.prop(props.inputs['Closed Path'], "default_value", text="Closed Path?")
                                    subrow = panel.row(align=True)
                                    subrow.prop(props.inputs['Reverse Flow'], "default_value", text="Reverse")
                                    subrow.prop(props.inputs['Subdivide Curve'], "default_value", text="Subdivide")
                                    subrow = panel.row(align=True)
                                    subrow.prop(props.inputs['Start Frame'], "default_value", text="Start Frame")
                                    subrow.prop(props.inputs['End Frame'], "default_value", text="End Frame")
                                    subrow = panel.row(align=True)
                                    subrow.prop(props.inputs['Cycle Length'], "default_value", text="Cycle Length")
                                    subrow.prop(props.inputs['Flow Length'], "default_value", text="Flow Length")
                                    subrow = panel.row(align=True)
                                    subrow.prop(props.inputs['Scale'], "default_value", text="Scale")
                                    subrow.prop(props.inputs['Edge Select'], "default_value", text="Edge Selection")
                                    if props.inputs['Bounding Box'].default_value:
                                        subrow = panel.row(align=True)
                                        subrow.prop(props.inputs['BBOX Width Scale'], "default_value", text="BBox Width")
                                        subrow.prop(props.inputs['BBOX Height Scale'], "default_value", text="BBox Height")
                                    panel.template_color_ramp(props.node_tree.nodes['Color Ramp'], "color_ramp", expand=True)
                                    panel.prop(props.inputs['Color Strength'], "default_value", text="Color Strength")
                                    panel.label(text="Edge Flow Curve Shape")
                                    panel.template_curve_mapping(props.node_tree.nodes['Float Curve'], "mapping")
                                    subheader, subpanel = panel.panel(f"{props.node_tree.name} preset curves", default_closed=True)
                                    subheader.label(text="Preset Curves")
                                    if subpanel:
                                        curve_node = props.node_tree.nodes['Float Curve']
                                        curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                        if curve_setting:
                                            draw_curve_ui(subpanel, curve_setting)
                                    panel.separator()
                                continue
                            elif anim_type == 'transform_anim':
                                for anim_node in anim_nodes:
                                    if anim_node.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, anim_node.name)
                                        continue
                                    props = anim_node
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Transform Anim')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{anim_node.id_data.name}**{anim_node.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'drawer_anim'
                                    if status.hide:
                                        continue
                                    row = panel.row(align=True)
                                    row.label(text="Effect Range: ")
                                    row.prop(props.inputs['Range Start'], "default_value", text="Range Start")
                                    row.prop(props.inputs['Range End'], "default_value", text="Range End")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Start Frame'], "default_value", text="Start Frame")
                                    row.prop(props.inputs['Anim Length'], "default_value", text="Anim Length")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Reverse'], "default_value", text="Reverse")
                                    row.prop(props.inputs['Randomize'], "default_value", text="Randomize")
                                    if props.inputs['Randomize'].default_value:
                                        row.prop(props.inputs['Seed'], "default_value", text="Seed")
                                    panel.prop(props.inputs['Keep Before Start'], "default_value", text="Keep Before Start or After End")
                                    row = panel.row(align=True)
                                    row.prop(props.inputs['Bypass Rotate'], "default_value", text="Mute Rotate")
                                    row.prop(props.inputs['Bypass Offset'], "default_value", text="Mute Offset")
                                    row.prop(props.inputs['Bypass Scale'], "default_value", text="Mute Scale")
                                    for transform in ['Rotate', 'Offset', 'Scale']:
                                        if not props.inputs[f'Bypass {transform}'].default_value:
                                            panel.label(text=f"{transform} Anim Setting")
                                            panel.prop(props.node_tree.nodes[f'{transform} Mix'].inputs["A"], "default_value", text=f"{transform}")
                                            panel.label(text=f"{transform} Anim Curve")
                                            panel.template_curve_mapping(props.node_tree.nodes[f'{transform} Anim Curve'], "mapping")
                                            subheader, subpanel = panel.panel(f"{props.node_tree.name} {transform} preset curves", default_closed=True)
                                            subheader.label(text="Preset Curves")
                                            if subpanel:
                                                curve_node = props.node_tree.nodes[f'{transform} Anim Curve']
                                                curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                                if curve_setting:
                                                    draw_curve_ui(subpanel, curve_setting)
                                            if not props.inputs["Randomize"].default_value:
                                                if transform == 'Rotate':
                                                    panel.prop(props.node_tree.nodes[f"{transform} Instances"].inputs['Pivot Point'], "default_value", text="Pivot Point")
                                                elif transform == 'Scale':
                                                    panel.prop(props.node_tree.nodes[f"{transform} Instances"].inputs['Center'], "default_value", text="Center")
                                                panel.prop(props.node_tree.nodes[f"{transform} Instances"].inputs['Local Space'], "default_value", text="Local Space")
                                            panel.separator()
                                continue
                            elif anim_type == 'transform':
                                for anim_node in anim_nodes:
                                    if anim_node.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, anim_node.name)
                                        continue
                                    props = anim_node.node_tree
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Transform')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{anim_node.id_data.name}**{anim_node.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'drawer_anim'
                                    if status.hide:
                                        continue
                                    nodes = [props.nodes['Rotate Instances'], props.nodes['Translate Instances'], props.nodes['Scale Instances']]
                                    for i, node in enumerate(nodes):
                                        if i>0:
                                            panel.separator()
                                            panel.separator()
                                        split = panel.split(factor=0.5)
                                        for socket in node.inputs[2:]:
                                            if socket.name == 'Local Space' or socket.name == 'Translation':
                                                panel.prop(socket, "default_value", text=socket.name)
                                            else:
                                                split.prop(socket, "default_value", text=socket.name)
                                    panel.separator()
                                continue
                            elif anim_type == 'add_snapshot':
                                for anim_node in anim_nodes:
                                    if anim_node.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, anim_node.name)
                                        continue
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Add Snapshot')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{anim_node.id_data.name}**{anim_node.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'drawer_anim'
                                    if status.hide:
                                        continue
                                    panel.template_node_inputs(anim_node)
                                    panel.separator()
                                continue
                            elif anim_type == 'curve_normal_tangent':
                                for anim_node in anim_nodes:
                                    if anim_node.name not in vb.formula_animsetting_status:
                                        animsetting_status_reset(context, anim_node.name)
                                        continue
                                    split = panel.split(factor=0.7)
                                    split.label(text=f'Curve Normal/Tangent')
                                    subrow = split.row(align=True)
                                    status = anim_setting_status[vb.formula_animsetting_status[f"{anim_node.name}"]]
                                    subrow.prop(status,"hide")
                                    op=subrow.operator("math_anim.del_gp_anim", text="", icon="PANEL_CLOSE")
                                    op.anim_node = f"{anim_node.id_data.name}**{anim_node.name}"
                                    op.anim_type = f"{anim_type}"
                                    op.track_tag = 'drawer_anim'
                                    if status.hide:
                                        continue
                                    panel.template_node_inputs(anim_node)
                                    panel.separator()
        # morphing ui
        header, panel = layout.panel("math_anim_morphing", default_closed=True)
        header.label(text="Morph Anim")
        if panel:
            row = panel.row(align=True)
            row.operator("math_anim.update_morph_objects",text="Update Layer Tree", icon='FILE_REFRESH')
            row.operator("math_anim.formula_morph_anim",text="Morph Setup", icon='SETTINGS')
            if 'morph_anim' in vb.formula_anim_nodes and len(vb.formula_anim_nodes['morph_anim'])>0:
                morphAnimSettings = context.scene.math_anim_morphAnimSettings
                found = True
                if morphAnimSettings.anim_item not in vb.formula_animsetting_status:
                    animsetting_status_reset(context, morphAnimSettings.anim_item)
                    found = False
                if found:
                    panel.prop(morphAnimSettings, "anim_item", text="Morph Items")
                    for index, morph_list in enumerate(vb.formula_anim_nodes['morph_anim']):
                        if morphAnimSettings.anim_item in morph_list:
                            morph_anim = morph_list[morphAnimSettings.anim_item]
                            split = panel.split(factor=0.7)
                            split.label(text=f"{morphAnimSettings.anim_item}")
                            subrow = split.row(align=True)
                            status = anim_setting_status[vb.formula_animsetting_status[morphAnimSettings.anim_item]]
                            subrow.prop(status,"hide")
                            op = subrow.operator("math_anim.del_formula_anim", text="", icon='PANEL_CLOSE')
                            op.anim_type = f'{index}.morph_anim'
                            op.node_name = morphAnimSettings.anim_item
                            if status.hide:
                                continue
                            for anim in morph_anim:
                                morph_node = anim[0]
                                panel.prop(morph_node.inputs['Keep Source'], "default_value", text="Keep Origin")
                                row = panel.row(align=True)
                                row.prop(morph_node.inputs['Start Frame'], "default_value", text="Start Frame")
                                row.prop(morph_node.inputs['Anim Length'], "default_value", text="Anim Length")
                                panel.label(text="Animation Curve")
                                panel.template_curve_mapping(morph_node.node_tree.nodes['Float Curve'], "mapping")
                                subheader, subpanel = panel.panel(f"{morph_node.node_tree.name} preset curves", default_closed=True)
                                subheader.label(text="Preset Curves")
                                if subpanel:
                                    curve_node = morph_node.node_tree.nodes['Float Curve']
                                    curve_setting = curve_anim_settings.get(f"{curve_node.id_data.name}**{curve_node.name}")
                                    if curve_setting:
                                        draw_curve_ui(subpanel, curve_setting)
                                panel.separator()
                                panel.separator()

classes = (
    MATH_ANIM_PATH_UL_List,
    MATH_ANIM_PT_main_panel,
)
register, unregister = bpy.utils.register_classes_factory(classes)
