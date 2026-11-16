import bpy
import sys
import os
import subprocess
from .utils import save_dict_to_file, build_file_path_dict
from .variables import font_save_file

class FontPathItem(bpy.types.PropertyGroup):
    path: bpy.props.StringProperty(name="Path", subtype='FILE_PATH')

class FONTPATH_UL_List(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if item:
            layout.label(text=item.path)

class FONTPATH_OT_Add(bpy.types.Operator):
    """Open File Manager to Select a Path"""
    bl_idname = "math_anim.fontpath_add"
    bl_label = "Add Path"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        new_path = prefs.paths.add()
        new_path.path = self.filepath
        prefs.active_index = len(prefs.paths) - 1
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class FONTPATH_OT_Remove(bpy.types.Operator):
    """Remove the selected path"""
    bl_idname = "math_anim.fontpath_remove"
    bl_label = "Remove Path"

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        if prefs.paths and 0 <= prefs.active_index < len(prefs.paths):
            prefs.paths.remove(prefs.active_index)
            prefs.active_index = max(0, prefs.active_index - 1)
        return {'FINISHED'}

class Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    panel_category: bpy.props.StringProperty(
        name="Panel Category",
        default="Tool",
        description="Category to show up the addon in the viewport N Panel, restart to take effect",
    )
    paths: bpy.props.CollectionProperty(type=FontPathItem)
    active_index: bpy.props.IntProperty(default=-1)
    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.label(text="Make sure read my Github readme before start!")
        col.label(text="The Addon works with PDF file's natural layout, font path are required for accurate consistency")
        col.label(text="Native support for PDF and typst. Setup latex(optex) path for latex(optex) support.")
        col.label(text="Only .otf and .ttf fonts supported, make sure your documents are produced with them.")

        col.separator()
        col.separator()
        col.label(text='Font Paths (required):')
        row = layout.row()
        col = row.column()
        # Box for the path list
        col.template_list("FONTPATH_UL_List", "", self, "paths", self, "active_index")

        # Buttons on the right
        col = row.column(align=True)
        col.operator("math_anim.fontpath_add", text="", icon="ADD")   # Add Path
        col.operator("math_anim.fontpath_remove", text="", icon="REMOVE")  # Remove Path

        col = layout.column(align=True)
        col.operator("math_anim.build_font_libs")
        col.separator()
        col.separator()
        col.label(text='Presets (optional):')
        props = context.scene.math_anim_formula_props
        col.prop(props, "optex_preset", text='Optex preset')
        col.prop(props, "typst_preset", text='Typst preset')
        col.separator()
        props = context.scene.math_anim_plotter_props
        col.prop(props, "math_extra_num_vars", text='Extra Vars')
        # give option to set category of the Addon in the N Panel
        col.separator()
        col.separator()
        col.prop(self, "panel_category", text='N Panel Location')
        col.separator()
        col.separator()

class BuildFontLibs(bpy.types.Operator):
    bl_idname = "math_anim.build_font_libs"
    bl_label = "Build Font Lib"
    bl_description = "Scan all subdirectories from the provided Font Path for .otf and .ttf fonts and build a font library"

    def execute(self, context):
        prefs = context.preferences.addons[__package__].preferences
        if not prefs.paths:
            self.report({"WARNING"},"No paths for fonts lib to be built, add paths first!!!")
            return {'CANCELLED'}
        font_path_dicts = {}
        for font_path in prefs.paths:
            font_path_dict = build_file_path_dict(font_path.path)
            font_path_dicts = {**font_path_dicts, **font_path_dict}
        if font_path_dicts:
            save_dict_to_file(font_save_file, font_path_dicts)
            self.report({"INFO"},"Fonts lib built are done.")
            return {'FINISHED'}
        else:
            self.report({"WARNING"},"No .otf or .ttf fonts found! No fonts lib are built.")
            return {'FINISHED'}

        return {'FINISHED'}

classes = (
    FontPathItem,
    FONTPATH_UL_List,
    FONTPATH_OT_Add,
    FONTPATH_OT_Remove,
    BuildFontLibs,
    Preferences,
)
register, unregister = bpy.utils.register_classes_factory(classes)
