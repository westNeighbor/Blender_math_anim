'''
Copyright (C) 2025 Minghui Zhao
zhaominghui2011@gmail.com

Created by Minghui Zhao

    This is a blender addon to help animate math infer process in 3D viewport

bl_info = {
    "name": "Math Anim",
    "author": "Minghui Zhao",
    "version": (1, 0, 0),
    "blender": (4, 4, 0),
    "location": "View3D > Sidebar > Tool",
    "description": "Create animated 3D mathematical function plots",
    "doc_url": "https://github.com/westNeighbor/blender_math_anim",
    "tracker_url": "https://github.com/westNeighbor/blender_math_anim/issues",
    "category": "Animation",
}
'''

import bpy
import os
import re
import json

from .preferences  import *
from .ui import *
from .properties import *
from .properties_plotter import *
from .operations import *
from .drawer_ops import *
from .plotter_ops import *
from .handlers import *
from . import variables as vb
from .curve_anim_presets import *

def register():

    # preperties
    properties.register()
    properties_plotter.register()

    # preferences
    preferences.register()

    # operators
    operations.register()
    drawer_ops.register()
    plotter_ops.register()

    # anim curve presets
    curve_anim_presets.register()

    # ui
    ui.register()

    bpy.types.Scene.math_anim_plotter_props  = bpy.props.PointerProperty(type=MATH_ANIM_Plotter_Properties)
    bpy.types.Scene.math_anim_formula_props  = bpy.props.PointerProperty(type=MATH_ANIM_Formula_Properties)
    bpy.types.Scene.math_anim_optexcode      = bpy.props.PointerProperty(type=MATH_ANIM_OptexCode_Properties)
    bpy.types.Scene.math_anim_optexfile      = bpy.props.PointerProperty(type=MATH_ANIM_OptexFile_Properties)
    bpy.types.Scene.math_anim_typstcode      = bpy.props.PointerProperty(type=MATH_ANIM_TypstCode_Properties)
    bpy.types.Scene.math_anim_typstfile      = bpy.props.PointerProperty(type=MATH_ANIM_TypstFile_Properties)
    bpy.types.Scene.math_anim_pdffile        = bpy.props.PointerProperty(type=MATH_ANIM_PdfFile_Properties)
    bpy.types.Scene.math_anim_func_datafile  = bpy.props.PointerProperty(type=MATH_ANIM_FuncData_Properties)
    bpy.types.Scene.math_animSetting_status  = bpy.props.CollectionProperty(type=MATH_ANIM_AnimSetting_Status)
    bpy.types.Scene.math_anim_morphSettings  = bpy.props.CollectionProperty(type=MATH_ANIM_MorphObjContainer)
    bpy.types.Scene.math_anim_morph_targets  = bpy.props.CollectionProperty(type=MATH_ANIM_Morph_Targets)
    bpy.types.Scene.math_anim_morph_selected_idx  = bpy.props.CollectionProperty(type=MATH_ANIM_MorphSelectedIdx)
    bpy.types.Scene.math_anim_morphAnimSettings   = bpy.props.PointerProperty(type=MATH_ANIM_MorphAnimSettings)
    bpy.types.Scene.math_anim_individualSettings  = bpy.props.PointerProperty(type=MATH_ANIM_IndividualSettings)
    bpy.types.Scene.math_anim_gplayers       = bpy.props.PointerProperty(type=MATH_ANIM_GPLayers)
    bpy.types.Scene.math_anim_gpobjects      = bpy.props.PointerProperty(type=MATH_ANIM_GPObjects)
    bpy.types.Scene.math_anim_curve_gen_settings = bpy.props.CollectionProperty(type=MA_CURVE_ANIM_Settings)
    bpy.types.Scene.math_anim_ode_settings = bpy.props.PointerProperty(type=MATH_ANIM_ODE_Settings)

    # handlers
    register_handlers("register")

    update_panel_category(None, None)

def unregister():
    # handlers
    register_handlers("unregister")

    # preferences
    preferences.unregister()

    # ui
    ui.unregister()

    # anim curve presets
    curve_anim_presets.unregister()

    # operators
    plotter_ops.unregister()
    drawer_ops.unregister()
    operations.unregister()

    # preperties
    properties.unregister()
    properties_plotter.unregister()

    del bpy.types.Scene.math_anim_plotter_props
    del bpy.types.Scene.math_anim_formula_props
    del bpy.types.Scene.math_anim_optexcode
    del bpy.types.Scene.math_anim_optexfile
    del bpy.types.Scene.math_anim_typstcode
    del bpy.types.Scene.math_anim_typstfile
    del bpy.types.Scene.math_anim_pdffile
    del bpy.types.Scene.math_anim_func_datafile
    del bpy.types.Scene.math_animSetting_status
    del bpy.types.Scene.math_anim_morphSettings
    del bpy.types.Scene.math_anim_morph_selected_idx
    del bpy.types.Scene.math_anim_morphAnimSettings
    del bpy.types.Scene.math_anim_individualSettings
    del bpy.types.Scene.math_anim_gplayers
    del bpy.types.Scene.math_anim_gpobjects
    del bpy.types.Scene.math_anim_curve_gen_settings
    # delete dynamic properties
    for param in vb.plot_variable_tracking['params']:
        prop_id = f"math_param_{param}"
        if hasattr(bpy.types.Scene, prop_id):
            delattr(bpy.types.Scene, prop_id)
    var_names = { m.group(1) for var in vb.plot_variable_tracking['vars'] if (m := re.match(r"^math_var_(.+)_(min|max|resolution)$", var))}
    for var in var_names:
        prop_ids = {f"math_var_{var}_min", f"math_var_{var}_max", f"math_var_{var}_resolution"}
        for prop_id in prop_ids:
            if hasattr(bpy.types.Scene, prop_id):
                delattr(bpy.types.Scene, prop_id)

if __name__ == "__main__":
    try:
        unregister()
    except:
        pass

    register()
