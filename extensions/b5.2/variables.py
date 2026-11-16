# global variables to hold updated data
import os
from asteval import Interpreter
font_save_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts_dict.json")
font_path_dict = {}
openBracketChars = {
        "⎡": "23A1",
        "⎢": "23A2",
        "⎣": "23A3",
        "⎤": "23A4",
        "⎥": "23A5",
        "⎦": "23A6",
        "⎛": "239B",
        "⎜": "239C",
        "⎝": "239D",
        "⎞": "239E",
        "⎟": "239F",
        "⎠": "23A0",
        "⎧": "23A7",
        "⎨": "23A8",
        "⎩": "23A9",
        "⎫": "23AB",
        "⎬": "23AC",
        "⎭": "23AD"
}
specialChars = {"√": "221A"}
bracketsReplace = {
        "{":{"top": "⎧", "middle": "⎨", "bottom": "⎩"},
        "}":{"top": "⎫", "middle": "⎬", "bottom": "⎭"},
        "[":{"top": "⎡", "middle": "⎢", "bottom": "⎣"},
        "]":{"top": "⎤", "middle": "⎥", "bottom": "⎦"},
        "(":{"top": "⎛", "middle": "⎜", "bottom": "⎝"},
        ")":{"top": "⎞", "middle": "⎟", "bottom": "⎠"}
}
formula_node_trees = {} # storing all the char's nodes for math objects, obj: [{'text_nodes': {node.name: node, ...}, {'stroke_nodes': {node.name: node, ...}}, {'fill_nodes': {node.name: node, ...}} }] where [pages]
formula_anim_nodes = {} # storing all the animgroups for math objects, obj: {'text_anim': {'anim_type': [animgroup, ...]}, 'stroke_anim': {'anim_type': [animgroup, ...]}, 'fill_anim': {'anim_type': [animgroup, ...]}}
formula_animsetting_status = {} # storing all the animgroup settings show up or hide status in UI, {animgroup.name: status_prop_index}
formula_morph_presets = {} # key: curve_morph_anim_nodegroup, corresponding to number of morph targets
_enum_targets = [] # must have reference for dynamic EnumProperty update, see https://docs.blender.org/api/current/bpy.props.html#bpy.props.EnumProperty for the bug
_enum_morphs = [] # must have reference for dynamic EnumProperty update, see https://docs.blender.org/api/current/bpy.props.html#bpy.props.EnumProperty for the bug
_enum_items = [] # must have reference for dynamic EnumProperty update, see https://docs.blender.org/api/current/bpy.props.html#bpy.props.EnumProperty for the bug
_enum_gplayers = []
_enum_gpobjects = []
gpencil_layer_nodes = {} # obj.name: {{obj.name: node_tree}, {layer.name: layernode}...}, note that the first stores the node_tree

# for plotter
math_fns = set(Interpreter().symtable.keys())
VARS_USED = set() # var_name
DYNAMIC_PARAMS = {} # param_name: scene.math_param_param_name
plot_variable_tracking = {'value': {}, 'plot': {}, 'vars': [], 'params': []} # 'value': {var_name: (value, update_or_not), ...}, 'plot': {var_name: {(object, layer): {'functions': (math_mode, math_function), 'vars': (var, ...), 'params': (param,...)}, ...}, ...}, 'vars': [var_name, ...], 'params': [param_name, ...]
bg_grid_holder = {} # sourcegroup_name: node_name
_x_vals, _y_vals, _z_vals = [], [], []
