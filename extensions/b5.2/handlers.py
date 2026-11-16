import bpy
from . import variables as vb
from .plotter_ops import update_scene_plot, register_dynamic_scene_props
import json
import re
import numpy as np
import ast
from bpy.props import FloatProperty, IntProperty

def all_handlers():
    """return a list of handler stored in .blend"""

    return_list = []
    for oh in bpy.app.handlers:
        try:
            for h in oh:
                return_list.append(h)
        except:
            pass
    return return_list


def register_handlers(status):
    """register dispatch for handlers"""

    if (status == "register"):

        all_handler_names = [h.__name__ for h in all_handlers()]

        # frame_change
        if "plot_frame_post" not in all_handler_names:
            bpy.app.handlers.frame_change_post.append(plot_frame_post)

        # save tracking when saving the file
        if "save_trackings" not in all_handler_names:
            bpy.app.handlers.save_pre.append(save_trackings)

        # restore tracking when open the file
        if "restore_trackings" not in all_handler_names:
            bpy.app.handlers.load_post.append(restore_trackings)

        return None

    elif (status == "unregister"):

        for h in all_handlers():

            # frame_change
            if (h.__name__ == "plot_frame_post"):
                bpy.app.handlers.frame_change_post.remove(h)

            # save_trackings
            if (h.__name__ == "save_trackings"):
                bpy.app.handlers.save_pre.remove(h)

            # restore_trackings
            if (h.__name__ == "restore_trackings"):
                bpy.app.handlers.load_post.remove(h)

    return None

@bpy.app.handlers.persistent
def plot_frame_post(scene):  # used for scene driven properties live udpating!
    changed = False
    for param, (value, update_tag) in vb.plot_variable_tracking['value'].items():
        prop_id = None
        if param in vb.plot_variable_tracking['params']:
            prop_id = f"math_param_{param}"
            try:
                getattr(scene, prop_id)
            except:
                pass
            if value != getattr(scene, prop_id):
                vb.plot_variable_tracking['value'][param] = (getattr(scene, prop_id), True)
                changed = True
        else:
            prop_id = param
            try:
                getattr(scene, prop_id)
            except:
                pass
            if value != getattr(scene, prop_id):
                vb.plot_variable_tracking['value'][param] = (getattr(scene, prop_id), True)
                changed = True
    if changed:
        # queue operator to run later, outside depsgraph/frame_post evaluation, otherwise crashes when rendering
        def safe_update():
            bpy.ops.math_anim.create_plot(update_tag=True)
        bpy.app.timers.register(safe_update, first_interval=0.0)

# save trackings when saving the file
@bpy.app.handlers.persistent
def save_trackings(dummy):
    tracking_lists = ["formula_node_trees","formula_anim_nodes", "formula_animsetting_status", "gpencil_layer_nodes", "VARS_USED","DYNAMIC_PARAMS","plot_variable_tracking", "bg_grid_holder"]
    for trackings in tracking_lists:
        trackings_data = {}
        if trackings not in bpy.data.texts:
            text_block = bpy.data.texts.new(trackings)
        else:
            text_block = bpy.data.texts[trackings]
        text_block.clear()
        if trackings == "formula_node_trees":
            for obj_name, pages in vb.formula_node_trees.items():
                trackings_data[obj_name] = []
                for page in pages:
                    nodes_in_page = {}
                    for node_type, nodes in page.items():
                        nodes_in_type = {}
                        for key_name, node in nodes.items():
                            nodes_in_type[key_name] = f"{node.id_data.name}+-+{node.name}"
                        nodes_in_page[node_type] = nodes_in_type
                    trackings_data[obj_name].append(nodes_in_page)
        elif trackings == "formula_anim_nodes":
            for obj_name, anim_categories in vb.formula_anim_nodes.items():
                if 'morph_anim' == obj_name:
                    trackings_data['morph_anim'] = []
                    for item in vb.formula_anim_nodes['morph_anim']:
                        for key_name, anim_morphs in item.items():
                            anim_in_morph = []
                            for anim_morph in anim_morphs: # list of (morph_node, [mute_nodes], [morph_items])
                                morph_node, mute_nodes, morph_items = anim_morph
                                mute_node_names = []
                                morph_item_ids = []
                                for mute_node in mute_nodes:
                                    mute_node_names.append(f"{mute_node.id_data.name}+-+{mute_node.name}")
                                for morph_item in morph_items:
                                    id_data_name = morph_item.id_data.name
                                    obj_id = morph_item.obj_id
                                    page_idx = morph_item.page_idx
                                    collection_idx = morph_item.collection_idx
                                    morph_idx = morph_item.morph_idx
                                    morph_item_ids.append(f"{id_data_name}+-+{obj_id}+-+{page_idx}+-+{collection_idx}+-+{morph_idx}")
                                anim_in_morph.append((f"{morph_node.id_data.name}+-+{morph_node.name}", mute_node_names, morph_item_ids))
                            trackings_data['morph_anim'].append({key_name: anim_in_morph})
                elif 'group_anim' == obj_name:
                    trackings_data['group_anim'] = {}
                    for anim_type, anim_groups in vb.formula_anim_nodes['group_anim'].items():
                        trackings_data['group_anim'][anim_type] = {}
                        for groupname, anim_nodes in vb.formula_anim_nodes['group_anim'][anim_type].items():
                            if anim_type == 'wave_anim':
                                animnode1, animnode2, nodes = anim_nodes
                                node_list = []
                                for node in nodes:
                                    node_list.append(f"{node.id_data.name}+-+{node.name}")
                                trackings_data['group_anim'][anim_type][groupname] = (f"{animnode1.id_data.name}+-+{animnode1.name}", f"{animnode2.id_data.name}+-+{animnode2.name}", node_list)
                            else:
                                animnode, nodes = anim_nodes
                                node_list = []
                                for node in nodes:
                                    node_list.append(f"{node.id_data.name}+-+{node.name}")
                                trackings_data['group_anim'][anim_type][groupname] = (f"{animnode.id_data.name}+-+{animnode.name}", node_list)
                elif 'indiv_anim' == obj_name:
                    trackings_data['indiv_anim'] = {}
                    for anim_type, anim_groups in vb.formula_anim_nodes['indiv_anim'].items():
                        trackings_data['indiv_anim'][anim_type] = {}
                        for nodename, anim_nodes in vb.formula_anim_nodes['indiv_anim'][anim_type].items():
                            node_list = []
                            for node in anim_nodes:
                                if anim_type == 'wave_anim':
                                    node1, node2 = node
                                    node_list.append((f"{node1.id_data.name}+-+{node1.name}", f"{node2.id_data.name}+-+{node2.name}"))
                                elif anim_type == 'flow_anim':
                                    nest_nodes = []
                                    for n in node:
                                        nest_nodes.append(f"{n.id_data.name}+-+{n.name}")
                                    node_list.append(tuple(nest_nodes))
                                else:
                                    node_list.append(f"{node.id_data.name}+-+{node.name}")
                            trackings_data['indiv_anim'][anim_type][nodename] = node_list
                elif 'plotter_anim' == obj_name:
                    trackings_data['plotter_anim'] = {}
                    for gp_obj, gp_layers in vb.formula_anim_nodes['plotter_anim'].items():
                        trackings_data['plotter_anim'][gp_obj] = {}
                        for gp_layer, anim_types in vb.formula_anim_nodes['plotter_anim'][gp_obj].items():
                            trackings_data['plotter_anim'][gp_obj][gp_layer] = {}
                            for anim_type, anim_nodes in vb.formula_anim_nodes['plotter_anim'][gp_obj][gp_layer].items():
                                trackings_data['plotter_anim'][gp_obj][gp_layer][anim_type] = []
                                for anim_node in anim_nodes:
                                    if anim_type == 'wave_anim':
                                        node1, node2 = anim_node
                                        trackings_data['plotter_anim'][gp_obj][gp_layer][anim_type].append((f"{node1.id_data.name}+-+{node1.name}", f"{node2.id_data.name}+-+{node2.name}"))
                                    else:
                                        trackings_data['plotter_anim'][gp_obj][gp_layer][anim_type].append(f"{anim_node.id_data.name}+-+{anim_node.name}")
                elif 'drawer_anim' == obj_name:
                    trackings_data['drawer_anim'] = {}
                    for gp_obj, gp_layers in vb.formula_anim_nodes['drawer_anim'].items():
                        trackings_data['drawer_anim'][gp_obj] = {}
                        for gp_layer, anim_types in vb.formula_anim_nodes['drawer_anim'][gp_obj].items():
                            trackings_data['drawer_anim'][gp_obj][gp_layer] = {}
                            for anim_type, anim_nodes in vb.formula_anim_nodes['drawer_anim'][gp_obj][gp_layer].items():
                                trackings_data['drawer_anim'][gp_obj][gp_layer][anim_type] = []
                                for anim_node in anim_nodes:
                                    if anim_type == 'wave_anim':
                                        node1, node2 = anim_node
                                        trackings_data['drawer_anim'][gp_obj][gp_layer][anim_type].append((f"{node1.id_data.name}+-+{node1.name}", f"{node2.id_data.name}+-+{node2.name}"))
                                    else:
                                        trackings_data['drawer_anim'][gp_obj][gp_layer][anim_type].append(f"{anim_node.id_data.name}+-+{anim_node.name}")
                else:
                    trackings_data[obj_name] = {}
                    for anim_category, anim_types in anim_categories.items():
                        trackings_data[obj_name][anim_category] = {}
                        for anim_type, anim_nodes in anim_types.items():
                            trackings_data[obj_name][anim_category][anim_type] = []
                            if anim_type == 'wave_anim':
                                for anim_node in anim_nodes:
                                    node1, node2 = anim_node
                                    trackings_data[obj_name][anim_category][anim_type].append((f"{node1.id_data.name}+-+{node1.name}", f"{node2.id_data.name}+-+{node2.name}"))
                            else:
                                for anim_node in anim_nodes:
                                    trackings_data[obj_name][anim_category][anim_type].append(f"{anim_node.id_data.name}+-+{anim_node.name}")
        elif trackings == "formula_animsetting_status":
            trackings_data = vb.formula_animsetting_status
        elif trackings == "formula_morph_presets":
            for index, morph_group in vb.formula_morph_presets.items():
                if isinstance(morph_group, list):
                    trackings_data[index] = [f"{mg.id_data.name}" for mg in morph_group]
                else:
                    trackings_data[index] = f"{morph_group.id_data.name}"
        elif trackings == "gpencil_layer_nodes":
            for obj_name, layer_nodes  in vb.gpencil_layer_nodes.items():
                nodes_in_layer = {}
                for layer_name, layer_node in layer_nodes.items(): # the first is obj.name: node_tree, others are layer.name: layernode
                    nodes_in_layer[layer_name] = f"{layer_node.id_data.name}"
                trackings_data[obj_name] = nodes_in_layer
        elif trackings == "VARS_USED":
            trackings_data = list(vb.VARS_USED)
        elif trackings == "DYNAMIC_PARAMS":
            trackings_data = vb.DYNAMIC_PARAMS
        elif trackings == "plot_variable_tracking":
            var_tracking = vb.plot_variable_tracking['value']
            vars_tracking = vb.plot_variable_tracking['vars']
            params_tracking = vb.plot_variable_tracking['params']
            plot_tracking = {}
            for var_name, plots in vb.plot_variable_tracking['plot'].items():
                plot_tracking[var_name] = {}
                for (gp_obj, gp_layer), maths in plots.items():
                    plot_tracking[var_name][f'("{gp_obj.name}", "{gp_layer.name}")'] = maths
            trackings_data = {'value': var_tracking, 'plot': plot_tracking, 'vars': vars_tracking, 'params': params_tracking}
            #print(f"Saved plot_variable_tracking: {trackings_data}")
        elif trackings == "bg_grid_holder":
            trackings_data = vb.bg_grid_holder
        text_block.write(json.dumps(trackings_data))

# restore trackings when open file
@bpy.app.handlers.persistent
def restore_trackings(dummy):
    tracking_lists = ["formula_node_trees","formula_anim_nodes", "formula_animsetting_status", "gpencil_layer_nodes", "VARS_USED","DYNAMIC_PARAMS","plot_variable_tracking", "bg_grid_holder"]
    for trackings in tracking_lists:
        if trackings in bpy.data.texts:
            text_block = bpy.data.texts[trackings]
            try:
                trackings_data = json.loads(text_block.as_string())
                if trackings == "formula_node_trees":
                    vb.formula_node_trees.clear()
                    for obj_name, pages in trackings_data.items():
                        vb.formula_node_trees[obj_name] = []
                        for page in pages:
                            nodes_in_page = {}
                            for node_type, nodes in page.items():
                                nodes_in_page[node_type] = {}
                                for key_name, node_id in nodes.items():
                                    node_group_name, node_name = node_id.split("+-+")
                                    node = bpy.data.node_groups.get(node_group_name).nodes.get(node_name)
                                    if node:
                                        nodes_in_page[node_type][key_name] = node
                                    else:
                                        print(f"Node {node_name} not found in group {node_group_name} when restore trackings {trackings}")
                            vb.formula_node_trees[obj_name].append(nodes_in_page)
                elif trackings == "formula_anim_nodes":
                    vb.formula_anim_nodes.clear()
                    for obj_name, anim_categories in trackings_data.items():
                        if 'morph_anim' == obj_name:
                            vb.formula_anim_nodes['morph_anim'] = []
                            for item in trackings_data['morph_anim']:
                                for key_name, anim_morphs in item.items():
                                    anim_in_morph = []
                                    for anim_morph in anim_morphs:
                                        morph_node_name, mute_node_names, morph_item_ids = tuple(anim_morph)
                                        sourcegroup, node_name = morph_node_name.split("+-+")
                                        morph_node = bpy.data.node_groups.get(sourcegroup).nodes.get(node_name)
                                        mute_nodes = []
                                        for mute_node_name in mute_node_names:
                                            sourcegroup, node_name = mute_node_name.split("+-+")
                                            mute_node = bpy.data.node_groups.get(sourcegroup).nodes.get(node_name)
                                            if mute_node:
                                                mute_nodes.append(mute_node)
                                            else:
                                                print(f"Mute node {node_name} not found in group {sourcegroup} when restore trackings {trackings}")
                                        morph_items = []
                                        for morph_item_id in morph_item_ids:
                                            id_data_name, obj_id, page_idx, collection_idx, morph_idx = morph_item_id.split("+-+")
                                            morph_item = bpy.data.scenes[id_data_name].math_anim_morphSettings[obj_id].page_holder[int(page_idx)].morph_collection[int(collection_idx)].morph_setting[int(morph_idx)]
                                            if morph_item:
                                                morph_items.append(morph_item)
                                            else:
                                                print(f"Morph item {node_name} not found in group {sourcegroup} when restore trackings {trackings}")
                                        if morph_node:
                                            anim_in_morph.append((morph_node, mute_nodes, morph_items))
                                        else:
                                            print(f"Morph node {node_name} not found in group {sourcegroup} when restore trackings {trackings}")
                                    vb.formula_anim_nodes['morph_anim'].append({key_name: anim_in_morph})
                        elif 'group_anim' == obj_name:
                            vb.formula_anim_nodes['group_anim'] = {}
                            for anim_type, anim_groups in trackings_data['group_anim'].items():
                                vb.formula_anim_nodes['group_anim'][anim_type] = {}
                                for groupname, anim_nodes in anim_groups.items():
                                    if anim_type == 'wave_anim':
                                        animnode1_name, animnode2_name, node_names = tuple(anim_nodes)
                                        sourcegroup, node_name = animnode1_name.split("+-+")
                                        animnode1 = bpy.data.node_groups.get(sourcegroup).nodes.get(node_name)
                                        sourcegroup, node_name = animnode2_name.split("+-+")
                                        animnode2 = bpy.data.node_groups.get(sourcegroup).nodes.get(node_name)
                                        nodes = []
                                        for node_name in node_names:
                                            sourcegroup, node_name = node_name.split("+-+")
                                            node = bpy.data.node_groups.get(sourcegroup).nodes.get(node_name)
                                            if node:
                                                nodes.append(node)
                                            else:
                                                print(f"Anim node {node_name} not found in group {sourcegroup} when restore trackings {trackings}")
                                        vb.formula_anim_nodes['group_anim'][anim_type][groupname] = (animnode1, animnode2, nodes)
                                    else:
                                        animnode_name, node_names = tuple(anim_nodes)
                                        sourcegroup, node_name = animnode_name.split("+-+")
                                        animnode = bpy.data.node_groups.get(sourcegroup).nodes.get(node_name)
                                        nodes = []
                                        for node_name in node_names:
                                            sourcegroup, node_name = node_name.split("+-+")
                                            node = bpy.data.node_groups.get(sourcegroup).nodes.get(node_name)
                                            if node:
                                                nodes.append(node)
                                            else:
                                                print(f"Anim node {node_name} not found in group {sourcegroup} when restore trackings {trackings}")
                                        vb.formula_anim_nodes['group_anim'][anim_type][groupname] = (animnode, nodes)
                        elif 'indiv_anim' == obj_name:
                            vb.formula_anim_nodes['indiv_anim'] = {}
                            for anim_type, anim_groups in trackings_data['indiv_anim'].items():
                                vb.formula_anim_nodes['indiv_anim'][anim_type] = {}
                                for nodename, node_names in anim_groups.items():
                                    nodes = []
                                    for node_name in node_names:
                                        if anim_type == 'wave_anim':
                                            node1_name, node2_name = tuple(node_name)
                                            sourcegroup, ndname = node1_name.split("+-+")
                                            node1 = bpy.data.node_groups.get(sourcegroup).nodes.get(ndname)
                                            sourcegroup, ndname = node2_name.split("+-+")
                                            node2 = bpy.data.node_groups.get(sourcegroup).nodes.get(ndname)
                                            if node1 and node2:
                                                nodes.append((node1, node2))
                                            else:
                                                if not node1:
                                                    print(f"Anim node {node1_name} not found in group {sourcegroup} when restore trackings {trackings}")
                                                if not node2:
                                                    print(f"Anim node {node2_name} not found in group {sourcegroup} when restore trackings {trackings}")
                                        elif anim_type == 'flow_anim':
                                            nest_nodes = []
                                            for n_name in node_name:
                                                sourcegroup, ndname = n_name.split("+-+")
                                                n = bpy.data.node_groups.get(sourcegroup).nodes.get(ndname)
                                                if n:
                                                    nest_nodes.append(n)
                                                else:
                                                    print(f"Anim node {n_name} not found in group {sourcegroup} when restore trackings {trackings}")
                                            nodes.append(tuple(nest_nodes))
                                        else:
                                            sourcegroup, node_name = node_name.split("+-+")
                                            node = bpy.data.node_groups.get(sourcegroup).nodes.get(node_name)
                                            if node:
                                                nodes.append(node)
                                            else:
                                                print(f"Anim node {node_name} not found in group {sourcegroup} when restore trackings {trackings}")
                                    vb.formula_anim_nodes['indiv_anim'][anim_type][nodename] = nodes
                        elif 'plotter_anim' == obj_name:
                            vb.formula_anim_nodes['plotter_anim'] = {}
                            for gp_obj_name, gp_layers in trackings_data['plotter_anim'].items():
                                vb.formula_anim_nodes['plotter_anim'][gp_obj_name] = {}
                                for gp_layer_name, anim_types in gp_layers.items():
                                    vb.formula_anim_nodes['plotter_anim'][gp_obj_name][gp_layer_name] = {}
                                    for anim_type, node_names in anim_types.items():
                                        nodes = []
                                        for node_name in node_names:
                                            if anim_type == 'wave_anim':
                                                node1_name, node2_name = tuple(node_name)
                                                sourcegroup, nodename = node1_name.split("+-+")
                                                node1 = bpy.data.node_groups.get(sourcegroup).nodes.get(nodename)
                                                sourcegroup, nodename = node2_name.split("+-+")
                                                node2 = bpy.data.node_groups.get(sourcegroup).nodes.get(nodename)
                                                if node1 and node2:
                                                    nodes.append((node1, node2))
                                                else:
                                                    if not node1:
                                                        print(f"Anim node {node1_name} not found in grease pencil object {gp_obj_name} when restore trackings {trackings}")
                                                    if not node2:
                                                        print(f"Anim node {node2_name} not found in grease pencil object {gp_obj_name} when restore trackings {trackings}")
                                            else:
                                                sourcegroup, nodename = node_name.split("+-+")
                                                node = bpy.data.node_groups.get(sourcegroup).nodes.get(nodename)
                                                if node:
                                                    nodes.append(node)
                                                else:
                                                    print(f"Anim node {node_name} not found in grease pencil object {gp_obj_name} when restore trackings {trackings}")
                                        vb.formula_anim_nodes['plotter_anim'][gp_obj_name][gp_layer_name][anim_type] = nodes
                        elif 'drawer_anim' == obj_name:
                            vb.formula_anim_nodes['drawer_anim'] = {}
                            for gp_obj_name, gp_layers in trackings_data['drawer_anim'].items():
                                vb.formula_anim_nodes['drawer_anim'][gp_obj_name] = {}
                                for gp_layer_name, anim_types in gp_layers.items():
                                    vb.formula_anim_nodes['drawer_anim'][gp_obj_name][gp_layer_name] = {}
                                    for anim_type, node_names in anim_types.items():
                                        nodes = []
                                        for node_name in node_names:
                                            if anim_type == 'wave_anim':
                                                node1_name, node2_name = tuple(node_name)
                                                sourcegroup, nodename = node1_name.split("+-+")
                                                node1 = bpy.data.node_groups.get(sourcegroup).nodes.get(nodename)
                                                sourcegroup, nodename = node2_name.split("+-+")
                                                node2 = bpy.data.node_groups.get(sourcegroup).nodes.get(nodename)
                                                if node1 and node2:
                                                    nodes.append((node1, node2))
                                                else:
                                                    if not node1:
                                                        print(f"Anim node {node1_name} not found in grease pencil object {gp_obj_name} when restore trackings {trackings}")
                                                    if not node2:
                                                        print(f"Anim node {node2_name} not found in grease pencil object {gp_obj_name} when restore trackings {trackings}")
                                            else:
                                                sourcegroup, nodename = node_name.split("+-+")
                                                node = bpy.data.node_groups.get(sourcegroup).nodes.get(nodename)
                                                if node:
                                                    nodes.append(node)
                                                else:
                                                    print(f"Anim node {node_name} not found in grease pencil object {gp_obj_name} when restore trackings {trackings}")
                                        vb.formula_anim_nodes['drawer_anim'][gp_obj_name][gp_layer_name][anim_type] = nodes
                        else:
                            vb.formula_anim_nodes[obj_name] = {}
                            for anim_category, anim_types in anim_categories.items():
                                vb.formula_anim_nodes[obj_name][anim_category] = {}
                                for anim_type, anim_groups in anim_types.items():
                                    vb.formula_anim_nodes[obj_name][anim_category][anim_type] = []
                                    if anim_type == 'wave_anim':
                                        for anim_group in anim_groups:
                                            node1_name, node2_name = anim_group[0], anim_group[1]
                                            sourcegroup, node_name = node1_name.split("+-+")
                                            node1 = bpy.data.node_groups.get(sourcegroup).nodes.get(node_name)
                                            sourcegroup, node_name = node2_name.split("+-+")
                                            node2 = bpy.data.node_groups.get(sourcegroup).nodes.get(node_name)
                                            if node1 and node2:
                                                vb.formula_anim_nodes[obj_name][anim_category][anim_type].append((node1, node2))
                                            else:
                                                if not node1:
                                                    print(f"Anim node {node1_name} not found in group {sourcegroup} when restore trackings {trackings}")
                                                if not node2:
                                                    print(f"Anim node {node2_name} not found in group {sourcegroup} when restore trackings {trackings}")
                                    else:
                                        for anim_group_id in anim_groups:
                                            sourcegroup, node_name = anim_group_id.split("+-+")
                                            anim_node = bpy.data.node_groups.get(sourcegroup).nodes.get(node_name)
                                            if anim_node:
                                                vb.formula_anim_nodes[obj_name][anim_category][anim_type].append(anim_node)
                                            else:
                                                print(f"Anim group {anim_group_id} not found when restore trackings {trackings}")
                elif trackings == "formula_animsetting_status":
                    for key, value in trackings_data.items():
                        vb.formula_animsetting_status[key] = int(value)
                elif trackings == "formula_morph_presets":
                    vb.formula_morph_presets.clear()
                    print(f'{trackings_data=}')
                    for index, morph_groups in trackings_data.items():
                        if isinstance(morph_groups, list):
                            vb.formula_morph_presets[index] = []
                            for mg_id in morph_groups:
                                mg = bpy.data.node_groups.get(mg_id)
                                if mg:
                                    vb.formula_morph_presets[index].append(mg)
                                else:
                                    print(f"Morph group {mg_id} not found when restore trackings {trackings}")
                        else:
                            mg = bpy.data.node_groups.get(morph_groups)
                            if mg:
                                vb.formula_morph_presets[index] = mg
                            else:
                                print(f"Morph group {morph_groups} not found when restore trackings {trackings}")
                elif trackings == "gpencil_layer_nodes":
                    vb.gpencil_layer_nodes.clear()
                    for obj_name, layer_nodes in trackings_data.items():
                        vb.gpencil_layer_nodes[obj_name] = {}
                        for idx, (layer_name, layer_node_group_name) in enumerate(layer_nodes.items()):
                            layer_node_group = bpy.data.node_groups.get(layer_node_group_name)
                            if layer_node_group:
                                if idx == 0:
                                    # the first is the node_tree of the object
                                    vb.gpencil_layer_nodes[obj_name][layer_name] = layer_node_group
                                else:
                                    layer_node = layer_node_group.nodes.get(layer_name)
                                    if layer_node:
                                        vb.gpencil_layer_nodes[obj_name][layer_name] = layer_node
                                    else:
                                        print(f"Layer node {layer_name} not found in group {layer_node_group_name} when restore trackings {trackings}")
                            else:
                                print(f"Layer node group {layer_node_group_name} not found when restore trackings {trackings}")
                elif trackings == "VARS_USED":
                    vb.VARS_USED = set(trackings_data)
                elif trackings == "DYNAMIC_PARAMS":
                    vb.DYNAMIC_PARAMS = trackings_data
                elif trackings == "plot_variable_tracking":
                    vb.plot_variable_tracking['vars'] = trackings_data.get('vars', [])
                    vb.plot_variable_tracking['params'] = trackings_data.get('params', [])
                    vb.plot_variable_tracking['value'].clear()
                    for var_name, value_state in trackings_data['value'].items():
                        vb.plot_variable_tracking['value'][var_name] = tuple(value_state)
                    vb.plot_variable_tracking['plot'].clear()
                    for var_name, plots in trackings_data['plot'].items():
                        vb.plot_variable_tracking['plot'][var_name] = {}
                        for key, maths in plots.items():
                            gp_obj_name, gp_layer_name = ast.literal_eval(key)
                            gp_obj = bpy.data.objects.get(gp_obj_name)
                            if gp_obj:
                                gp_layer = gp_obj.data.layers.get(gp_layer_name)
                                if gp_layer:
                                    maths['functions'] = tuple(maths.get('functions', ()))
                                    maths['vars'] = tuple(maths.get('vars', ()))
                                    maths['params'] = tuple(maths.get('params', ()))
                                    vb.plot_variable_tracking['plot'][var_name][(gp_obj, gp_layer)] = maths
                                else:
                                    print(f"Grease pencil layer {gp_layer_name} not found in object {gp_obj_name} when restore trackings {trackings}")
                            else:
                                print(f"Grease pencil object {gp_obj_name} not found when restore trackings {trackings}")
                elif trackings == "bg_grid_holder":
                    vb.bg_grid_holder = trackings_data
            except Exception as e:
                print(f"Failed to restore {trackings} :{e}" )
            # remove the text block after restoring, keeping them for crash recovery purpose
            #if text_block:
            #    bpy.data.texts.remove(text_block)
    scene = bpy.context.scene
    var_names = { m.group(1) for var in vb.plot_variable_tracking['vars'] if (m := re.match(r"^math_var_(.+)_(min|max|resolution)$", var))}
    for var in var_names:
        prop_ids = {f"math_var_{var}_min", f"math_var_{var}_max", f"math_var_{var}_resolution"}
        for prop_id in prop_ids:
            try:
                getattr(scene, prop_id)
            except:
                register_dynamic_scene_props(var, type='var')
            setattr(scene, prop_id, vb.plot_variable_tracking['value'][prop_id][0])
    for param in vb.plot_variable_tracking['params']:
        prop_id = f"math_param_{param}"
        try:
            getattr(scene, prop_id)
        except:
            register_dynamic_scene_props(param, type='param')
        setattr(scene, prop_id, vb.plot_variable_tracking['value'][param][0])
