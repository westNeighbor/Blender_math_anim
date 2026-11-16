import bpy
import os
from bpy.props import *
from .utils import ErrorMessageBox, load_dict_from_file
from . import variables as vb
from ._optexmath_data import _optex_candidates
from ._typstmath_data import _typst_candidates

class MATH_ANIM_OptexItem(bpy.types.PropertyGroup):
    def get_candidates(self, context, edit_text):
        # Filter the candidates based on the input text (case-insensitive search)
        if self.math:
            return [candidate for candidate, description in _optex_candidates if edit_text.lower() in candidate.lower()]
        else:
            return []
    path: bpy.props.StringProperty(
        name="Optex code",
        search=get_candidates,
    )
    selected: bpy.props.BoolProperty(name="Selected", default=True)  # Multi-selection
    math: bpy.props.BoolProperty(name="Math Mode", default=True)  # Math mode
    def get_fonts(self, context, edit_text):
        if not vb.font_path_dict:
            if os.path.exists(vb.font_save_file):
                vb.font_path_dict = load_dict_from_file(vb.font_save_file)
        # Get all available vector fonts in Blender
        fonts= []
        if vb.font_path_dict:
            if self.math:
                fonts = [(k, v["family"]) for k, v in vb.font_path_dict.items() if k and v["is_math"] and edit_text.lower() in k.lower()]
            else:
                fonts = [(k, v["family"]) for k, v in vb.font_path_dict.items() if k and edit_text.lower() in k.lower()]
        return fonts
    font: bpy.props.StringProperty(
        name="Font",
        description="Select a font for the contents, keep empty to use default font",
        search=get_fonts,
    )

class MATH_ANIM_TypstItem(bpy.types.PropertyGroup):
    def get_candidates(self, context, edit_text):
        # Filter the candidates based on the input text (case-insensitive search)
        if self.math:
            return [(candidate,description) for candidate, description in _typst_candidates if edit_text.lower() in candidate.lower()]
        else:
            return []
    path: bpy.props.StringProperty(
        name="Typst code",
        search=get_candidates,
    )
    selected: bpy.props.BoolProperty(name="Selected", default=True)  # Multi-selection
    math: bpy.props.BoolProperty(name="Math Mode", default=True)  # Math mode
    def get_fonts(self, context, edit_text):
        if not vb.font_path_dict:
            if os.path.exists(vb.font_save_file):
                vb.font_path_dict = load_dict_from_file(vb.font_save_file)
        # Get all available vector fonts in Blender
        fonts= []
        if vb.font_path_dict:
            if self.math:
                fonts = [(v["family"], k) for k, v in vb.font_path_dict.items() if k and v["is_math"] and edit_text.lower() in k.lower()]
            else:
                fonts = [(v["family"], k) for k, v in vb.font_path_dict.items() if k and edit_text.lower() in k.lower()]
        return fonts
    font: bpy.props.StringProperty(
        name="Font",
        description="Select a font for the contents, keep empty to use default font",
        search=get_fonts,
    )

class MATH_ANIM_PathItem(bpy.types.PropertyGroup):
    path: bpy.props.StringProperty(name="File Path")
    selected: bpy.props.BoolProperty(name="Selected", default=True)  # Multi-selection
    math: bpy.props.BoolProperty(name="Math Mode", default=True)  # Math mode

class MATH_ANIM_OptexCode_Properties(bpy.types.PropertyGroup):
    paths: bpy.props.CollectionProperty(type=MATH_ANIM_OptexItem)
    active_index: bpy.props.IntProperty(default=-1)

class MATH_ANIM_OptexFile_Properties(bpy.types.PropertyGroup):
    paths: bpy.props.CollectionProperty(type=MATH_ANIM_PathItem)
    active_index: bpy.props.IntProperty(default=-1)

class MATH_ANIM_TypstCode_Properties(bpy.types.PropertyGroup):
    paths: bpy.props.CollectionProperty(type=MATH_ANIM_TypstItem)
    active_index: bpy.props.IntProperty(default=-1)

class MATH_ANIM_TypstFile_Properties(bpy.types.PropertyGroup):
    paths: bpy.props.CollectionProperty(type=MATH_ANIM_PathItem)
    active_index: bpy.props.IntProperty(default=-1)

class MATH_ANIM_PdfFile_Properties(bpy.types.PropertyGroup):
    paths: bpy.props.CollectionProperty(type=MATH_ANIM_PathItem)
    active_index: bpy.props.IntProperty(default=-1)

class MATH_ANIM_Formula_Properties(bpy.types.PropertyGroup):
    optex_preset: bpy.props.StringProperty(
        name="Optex Preset",
        description="Enter formula using LaTeX-style notation",
        default=r"\Yellow \sqrt{x^2+x+20}\sqrt{5}{\Red\sum_{k=0}^\infty} e^{(\alpha+i\beta_k)} = e^\alpha \prod_{k=0}^\infty e^{i\beta_k} = \int_{-\infty}^{\infty}\sin(x)dx",
    )
    optex_fontfam: bpy.props.EnumProperty(
        name="Optex Font Family",
        description="Font family selection for Optex file",
        default="Latin Modern",
        items=[('Latin Modern','Latin Modern','TeX Gyre fonts based on Computer Modern' ),
                ('Termes','Termes','TeX Gyre Termes fonts based on Times' ),
                ('Heros','Heros','TeX Gyre Heros fonts based on Helvetical' ),
                ('Adventor','Adventor','TeX Gyre Adventor based on Avantgarde Book' ),
                ('Bonum','Bonum','TeX Tyre Bonum fonts based on Bookman' ),
                ('Pagella','Pagella','TeX Tyre Pagella fonts based on Palatino' ),
                ('Schola','Schola','TeX Tyre Schola fonts based on New Century' ),
                ('Cursor','Cursor','TeX Tyre Cursor fonts based on Courier' ),
                ('New Computer Modern','New Computer Modern','CM with Book variants, Cyrillic, Greek' ),
                ('STIX','STIX','Scientific and Technical Information Exchange fonts' ),
                ('XITS','XITS','A fork of STIX with Bold Math variant' ),
                ('STIXTwo','STIXTwo','Second version of STIX' ),
                ('Linux Libertine','Linux Libertine','Free fonts typically installed on systems' ),
                ('Libertinus','Libertinus','Free fonts derived from Linux Libertine' ),
                ('Gentium','Gentium','Serif free fonts, support Greek, Cyrillic, IPA' ),
                ('KP fonts','KP fonts','KP fonts -- Johannes Kepler project' ),
                ('DejaVu','DejaVu','Derived from the Vera fonts' ),
                ('Antykwa Torunska','Antykwa Torunska','Traditional Polish font family' ),
                ('Poltawski','Poltawski','Antykwa Poltawskiego, Polish Traditional font family' ),
                ('Alegreya','Alegreya','Humanist serif and sans serif family' ),
                ('Baskerville','Baskerville','Free variants of classical Baskerville' ),
                ('Baskervald','Baskervald','Free variants of classical Baskerville by ADF' ),
                ('Heuristica','Heuristica','Extends the Utopia font' ),
                ('Erewhon','Erewhon','Derived from Heuristica with slanted variants' ),
                ('EB Garamond','EB Garamond','Free variants of classical Garamond' ),
                ('Garamond Libre','Garamond Libre','Free, derived from old style font family' ),
                ('LibreCaslon','LibreCaslon','Libre Caslon Text, inspired by Caslon' ),
                ('Cabin','Cabin','Inspired by Gills typeface + touch of a modernism'),
                ('Source Pro','Source Pro','Adobe SourceSerifPro, SourceSansPro, SourceCodePro fonts'),
                ('Kerkis','Kerkis','Free Bookman alternative with Greek letters'),
                ('ComicNeue','ComicNeue','Comic Neue sans serif'),
                ('Overlock','Overlock','fonts simulate Overlock sewing technique'),
                ('Merriweather','Merriweather','Modern shapes, sharp serifs'),
                ('Roboto','Roboto','Geometric grotesk, thin variants included'),
                ('Raleway','Raleway','Elegant grotesk, nine weights in two variants'),
                ('Noto','Noto','Sans, serif, mono with multiple language support'),
                ('Kurier','Kurier','Two element sans serif typeface'),
                ('Iwona','Iwona','Sans serif typeface derived from Kurier'),
                ('Lato','Lato','Geometric grotesk, many weights'),
                ('Montserrat','Montserrat','Inspired from old posters in Montserat in Buenos Aires'),
                ('Technika','Technika','Fonts from visual style of CTU in Prague'),
                ('XCharter','XCharter','An extension of Bitstream Charter'),
                ('GFSBodoni','GFSBodoni','Based on Bodoni with greek letters'),
                ('fbb','fbb','Bembo-like fonts derived from Cardo'),
                ('ETbb','ETbb','ET Bembo old style serif fonts'),
                ('Eczar','Eczar','Serif, specific for Latin and Devanagari'),
                ('Fira','Fira','Humanist sans-serif, originally designed for Firefox OS'),
                ('Neohellenic','Neohellenic','Sans serif fonts with math and full Greek'),
                ('Inconsolata','Inconsolata','A monospaced font for code listing'),
                ('OldStandard','OldStandard','Inspired by a typeface most commonly used in old books'),
                ('Clara','Clara','Clara, a serif font family'),
                ('Culmus','Culmus','Hebrew roman, sans and mono fonts from the Culmus project'),
                ('Plex','Plex','IBM Plex font family'),
                ('Concrete','Concrete','Concrete fonts with math')
               ]
    )
    typst_preset: bpy.props.StringProperty(
        name="Typst Preset",
        description="Enter formula using Typst-style notation",
        default="",
    )
    formula_source: EnumProperty(
        name="Formula Source",
        default="Optex_Code",
        description="Sources for formula generation, options are: Optex_Code, Typst_Code, Optex_File, Typst_File, PDF_File",
        items=[('Optex_Code', "optex code", "Compile latex(optex) math formula"),
               ('Typst_Code', "typst code", "Compile typst math formula"),
               ('Optex_File', "optex file", "Compile latex(optex) file"),
               ('Typst_File', "typst file", "Compile typst file"),
               ('PDF_File', "PDF file", "Extract PDF contents")
              ]
    )
    anim_text: BoolProperty(
        name="Anim.Text",
        description="Add animation to the text part",
        default=True
    )
    anim_stroke: BoolProperty(
        name="Anim.Stroke",
        description="Add animation to the drawing stroke part",
        default=True
    )
    anim_fill: BoolProperty(
        name="Anim.Fill",
        description="Add animation to the drawing fill part",
        default=True
    )
    anim_style: EnumProperty(
        name="Anim.Style",
        description="Formula animation style, options are: GROW, WRITING, WAVE, FLOW, TRANSFORM",
        items=[
            ('GROW', "Grow Anim (preset)", "Simulate growing effect"),
            ('WRITING', "Writing Anim (preset)", "Simulate writing effect"),
            ('COLOR_FLOW', "Color Flow (preset)", "Simulate color flow effect"),
            ('WAVE', "Wave Anim (preset)", "Simulate wave effect"),
            ('FLOW', "Edge Flow (preset)", "Light flow on the edge"),
            ('TRANSFORM_ANIM', "Transform Anim (preset)", "Preset scale/offset/rotate anims"),
            ('TRANSFORM', "Transform", "Insert keyframe to add your self-defined animations!"),
       ]
    )
    anim_settings: EnumProperty(
        name="Anim.Settings",
        description="Animation settings, options are: TEXT, STROKE, FILL",
        items=[('TEXT', "Text", "Animation settings for text part"),
               ('STROKE', "Stroke", "Animation settings for drawing stroke part"),
               ('FILL', "Fill", "Animation settings for drawing fill part")]
    )
    wave_mode: BoolProperty(
        name="WaveAnim.Select",
        description="Select the wave anim in local or global mode",
        default=False,
    )

    formula_font: PointerProperty(
        name="FormulaFont.Select",
        description="Set the formula font",
        type=bpy.types.VectorFont,
    )

class MATH_ANIM_AnimSetting_Status(bpy.types.PropertyGroup):
    hide: BoolProperty(
        default=False
    )
    name = StringProperty(default="")

class MATH_ANIM_MorphItem(bpy.types.PropertyGroup):
    def updateMorphIdx(self, context):
        current_selected = context.scene.math_anim_morph_selected_idx[self.collection_idx]
        source_selected  = context.scene.math_anim_morph_selected_idx[0]
        if self.selected:
            if self.collection_idx != 0:
                if source_selected.context_selected_idx == 0:
                    self.selected = False
                    ErrorMessageBox('Select Morph Source first!', 'INFO', icon="INFO")
                    return None
            current_selected.context_selected_idx += 1
            current_selected.context_selected_len += 1
            for morph_obj in context.scene.math_anim_morphSettings:
                if self.obj_id == morph_obj.name:
                    page_holder = morph_obj.page_holder[self.page_idx]
                    for i in range(len(page_holder.morph_collection)):
                        if self.collection_idx != i:
                            page_holder.morph_collection[i].morph_setting[self.item_idx].draw_tag = False
                    break
        else:
            current_selected.context_selected_idx -= 1
            current_selected.context_selected_len -= 1
            if current_selected.context_selected_idx < 0:
                current_selected.context_selected_idx = 0
                current_selected.context_selected_len = 0
            for morph_obj in context.scene.math_anim_morphSettings:
                if self.obj_id == morph_obj.name:
                    page_holder = morph_obj.page_holder[self.page_idx]
                    for i in range(len(page_holder.morph_collection)):
                        if self.collection_idx != i:
                            page_holder.morph_collection[i].morph_setting[self.item_idx].draw_tag = True
                    break

        # make current select can't exceed the morph source
        if current_selected.context_selected_idx >  source_selected.context_selected_idx or current_selected.context_selected_len >=  source_selected.context_selected_idx:
            current_selected.context_selected_idx =  source_selected.context_selected_idx

        source_morph = None
        for morph_obj in context.scene.math_anim_morphSettings:
            if morph_obj.name == context.scene.math_anim_morph_targets[0].math_obj_targets:
                source_morph = morph_obj.page_holder[0].morph_collection[0].morph_setting[0]
                break
        self.morph_idx = source_morph.morph_last_idx + current_selected.context_selected_idx

    def updateInputs(self, context):
        if self.type == 'input':
            for morph_obj in context.scene.math_anim_morphSettings:
                if self.obj_id == morph_obj.name:
                    page_holder = morph_obj.page_holder[self.page_idx]
                    for i in range(len(page_holder.morph_collection)):
                        if self.collection_idx != i:
                            print(f'sync collection {i=}')
                            if page_holder.morph_collection[i].morph_setting[self.item_idx].inputs != self.inputs:
                                page_holder.morph_collection[i].morph_setting[self.item_idx].inputs = self.inputs


    selected: bpy.props.BoolProperty(
        name='Selected',
        default=False,
        update=updateMorphIdx,
    )
    keep: bpy.props.BoolProperty(
        name='Keep Origin',
        default=False
    )
    morph: bpy.props.BoolProperty(
        name='Morph',
        default=False
    )
    morph_idx: bpy.props.IntProperty(
        name='Morph Idx',
        default=-1,
    )
    morph_last_idx: bpy.props.IntProperty(
        name='Last Morph Idx',
        default=0
    )
    inputs: bpy.props.StringProperty(
        name='Input holdout',
        default='',
        update=updateInputs
    )
    type: bpy.props.StringProperty(
        name='Type',
        default='input'
    )
    item_idx: bpy.props.IntProperty(name="Item Index",default=0)
    page_idx: bpy.props.IntProperty(name="Page Index",default=0)
    collection_idx: bpy.props.IntProperty(name="Collection Index",default=0)
    obj_id: bpy.props.StringProperty(name="Object ID",default="")
    draw_tag: bpy.props.BoolProperty(
        name='Draw Tag',
        default=True
    )

class MATH_ANIM_Morph_Targets(bpy.types.PropertyGroup):
    vb._enum_targets.clear()
    def get_math_obj_targets(self, context):
        vb._enum_targets = [(obj["math_anim_obj"], obj.name, "") for obj in bpy.data.objects if obj.get("math_anim_obj") is not None]
        return vb._enum_targets

    def updateIdx(self, context):
        context.scene.math_anim_morph_selected_idx[self.collection_idx].context_selected_idx = 0
        context.scene.math_anim_morph_selected_idx[self.collection_idx].context_selected_len = 0

    math_obj_targets: bpy.props.EnumProperty(
        name='Morph Target List',
        items=get_math_obj_targets,
        update=updateIdx,
    )
    collection_idx: bpy.props.IntProperty(name="Tag",default=0)

class MATH_ANIM_MorphSettingContainer(bpy.types.PropertyGroup):
    morph_setting: bpy.props.CollectionProperty(type=MATH_ANIM_MorphItem, name="Morph Item List")

class MATH_ANIM_MorphCollectionContainer(bpy.types.PropertyGroup):
    morph_collection: bpy.props.CollectionProperty(type=MATH_ANIM_MorphSettingContainer, name="Morph Collection List")

class MATH_ANIM_MorphObjContainer(bpy.types.PropertyGroup):
    page_holder: bpy.props.CollectionProperty(type=MATH_ANIM_MorphCollectionContainer, name="Page Morph List")
    name: bpy.props.StringProperty(default="obj_name")

class MATH_ANIM_MorphSelectedIdx(bpy.types.PropertyGroup):
    context_selected_idx: bpy.props.IntProperty(default=0)
    context_selected_len: bpy.props.IntProperty(default=0)

class MATH_ANIM_MorphAnimSettings(bpy.types.PropertyGroup):
    def get_morph_settings(self, context):
        vb._enum_morphs = [('None', 'None', 'None', 0)]
        if 'morph_anim' in vb.formula_anim_nodes:
            vb._enum_morphs = [(list(item.keys())[0], list(item.keys())[0], "The settings for the morph anim chain", index) for index, item in enumerate(vb.formula_anim_nodes['morph_anim'])]
        return vb._enum_morphs

    def gp_morph_setter(self, value):
        self['anim_item'] = value

    def gp_morph_getter(self):
        value = self.get('anim_item')
        valid_values = [item[3] for item in self.get_morph_settings(bpy.context)]
        return value if value in valid_values else valid_values[-1]

    anim_item: bpy.props.EnumProperty(
        name='Morph Anim Settings',
        items=get_morph_settings,
        set=gp_morph_setter,
        get=gp_morph_getter,
    )

class MATH_ANIM_IndividualSettings(bpy.types.PropertyGroup):
    def get_individual_items(self, context):
        vb._enum_items.clear()
        if context.object and (context.object.get("math_anim_obj") is not None):
            formula_obj = context.object
            if formula_obj["math_anim_obj"] not in vb.formula_node_trees:
                return [('None', 'None', 'None')]
            for page_num in range(len(vb.formula_node_trees[formula_obj["math_anim_obj"]])):
                nodes = vb.formula_node_trees[formula_obj["math_anim_obj"]][page_num]
                types = ['text_nodes', 'stroke_nodes', 'fill_nodes']
                for node_type in types:
                    node_list = list(nodes[node_type].items())[1:]
                    for key_name, node in node_list[::-1]:
                        name = key_name[0] if node_type == 'text_nodes' else key_name
                        item = (f"{page_num}*.*{node_type}*.*{key_name}", f"{name}", "individual item")
                        vb._enum_items.append(item)
        return vb._enum_items

    node_item: bpy.props.EnumProperty(
        name='Individual Settings',
        items=get_individual_items,
    )
    option: bpy.props.EnumProperty(
        name = "Setting Options",
        description = "Choose to edit individual item settings or group settings, options are: INDIVIDUAL, GROUP",
        items=[("INDIVIDUAL", "Individual Settings", "Settings for single item"),
               ("GROUP", "Group Settings", "Settings for multiple items")
        ],
        default="INDIVIDUAL",
    )

class MATH_ANIM_GPObjects(bpy.types.PropertyGroup):
    def get_gp_objects(self, context):
        vb._enum_gpobjects.clear()
        i = 0
        for obj in bpy.data.objects:
            if obj.get("math_anim_obj") is not None:
                vb._enum_gpobjects.append((f'{obj.name}', f'{obj.name}', 'Grease pencil object', i))
                i += 1
        if not vb._enum_gpobjects:
            vb._enum_gpobjects = [("None", "None", "None", 0)]
        return vb._enum_gpobjects

    def gp_object_setter(self, value):
        self['gp_object'] = value

    def gp_object_getter(self):
        value = self.get('gp_object')
        valid_values = [item[3] for item in self.get_gp_objects(bpy.context)]
        return value if value in valid_values else valid_values[-1]

    def updatePlotFunc(self, context):
        gplayers  = context.scene.math_anim_gplayers
        plotter_props = context.scene.math_anim_plotter_props
        gp_obj = bpy.data.objects.get(self.gp_object)
        if gp_obj and gp_obj["math_anim_obj"]:
            gp_layer = gp_obj.data.layers.get(gplayers.gp_layer)
            if gp_layer:
                for var_name in vb.plot_variable_tracking['plot']:
                    maths =  vb.plot_variable_tracking['plot'][var_name].get((gp_obj, gp_layer), {})
                    if maths:
                        if maths['functions'][0] == 'PARAFUNCTION':
                            plotter_props.plot_func=f"x={maths['functions'][1]}, y={maths['functions'][2]}, z={maths['functions'][3]}"
                            if maths['plot_branch']:
                                plotter_props.branch_plot = maths['branch_axis']
                        elif maths['functions'][0] == 'ODEFUNCTION':
                            plotter_props.plot_func=f"dx/dt={maths['functions'][1]}, dy/dt={maths['functions'][2]}, dz/dt={maths['functions'][3]}"
                            if maths['plot_branch']:
                                plotter_props.branch_plot = maths['branch_axis']
                            ode_setting = context.scene.math_anim_ode_settings
                            if ode_setting.ode_dt != maths['ode_dt']:
                                ode_setting.ode_dt = maths['ode_dt']
                            if ode_setting.ode_t0 != maths['ode_t0']:
                                ode_setting.ode_t0 = maths['ode_t0']
                            if ode_setting.ode_t1 != maths['ode_t1']:
                                ode_setting.ode_t1 = maths['ode_t1']
                            if ode_setting.ds_use_dt != maths['ds_use_dt']:
                                ode_setting.ds_use_dt = maths['ds_use_dt']
                            ode_setting.ode_solver = maths['ode_solver']
                            ode_setting.branch_compose = maths['branch_compose']
                        else:
                            plotter_props.plot_func=f"{maths['functions'][1]}"
                        break
                # also update plotting transform to current layers
                if gp_obj["math_anim_obj"] in vb.gpencil_layer_nodes and gp_layer.name in vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]]:
                    if vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]][gp_layer.name].node_tree.nodes.get('Axis Labels'):
                        props = vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]][gp_layer.name].node_tree.nodes['Axis Labels'].node_tree.nodes['Transform Plotting']
                    else:
                        props = vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]][gp_layer.name].node_tree.nodes['Transform Plotting']
                    plotter_props.plot_translation = props.inputs['Translation'].default_value
                    plotter_props.plot_rotation = props.inputs['Rotation'].default_value
                    plotter_props.plot_scale = props.inputs['Scale'].default_value

    gp_object: bpy.props.EnumProperty(
        name='Grease Pencil Objects',
        items=get_gp_objects,
        description="Grease pencil objects to hold the drawing",
        set=gp_object_setter,
        get=gp_object_getter,
        update=updatePlotFunc,
    )
    settings: bpy.props.EnumProperty(
        name='Settings Option',
        items=[('OBJECT', 'Object Settings', 'Object Material Settings'),
               ('LAYER', 'Layer Settings', 'Layer Material Settings'),
               ('LAYER_ANIM', 'Layer Anim', 'Layer Animation Settings'),
              ],
        description="Select category to change settings, options are: OBJECT, LAYER, LAYER_ANIM",
    )

class MATH_ANIM_GPLayers(bpy.types.PropertyGroup):
    def get_gp_layers(self, context):
        vb._enum_gplayers.clear()
        gp_obj = bpy.data.objects.get(context.scene.math_anim_gpobjects.gp_object)
        if gp_obj is not None:
            for i, layer in enumerate(gp_obj.data.layers):
                vb._enum_gplayers.append((f'{layer.name}', f'{layer.name}', 'Grease pencil layer', i))
        if not vb._enum_gplayers:
            vb._enum_gplayers = [("None", "None", "None", 0)]
        return vb._enum_gplayers

    def updateMode(self, context):
        gp_obj = bpy.data.objects.get(context.scene.math_anim_gpobjects.gp_object)
        if gp_obj is not None:
            context.view_layer.objects.active = gp_obj
            gp_obj.select_set(True)
            if self.draw_mode:
                bpy.ops.object.mode_set(mode='PAINT_GREASE_PENCIL')
            else:
                bpy.ops.object.mode_set(mode='OBJECT')
        else:
            self.report({"WARNING"}, "Select an Grease Pencil object first!")

    def gp_layer_getter(self):
        gp_obj = bpy.data.objects.get(bpy.context.scene.math_anim_gpobjects.gp_object)
        if gp_obj and len(gp_obj.data.layers) > 0:
            active_layer = gp_obj.data.layers.active
            layers = list(gp_obj.data.layers)
            return layers.index(active_layer)
        return 0

    def gp_layer_setter(self, value):
        self['gp_layer'] = value
        gp_obj = bpy.data.objects.get(bpy.context.scene.math_anim_gpobjects.gp_object)
        if gp_obj and gp_obj.data.layers.get(self.gp_layer):
            gp_obj.data.layers.active = gp_obj.data.layers[value]

    def updatePlotFunc(self, context):
        gpobjects = context.scene.math_anim_gpobjects
        plotter_props = context.scene.math_anim_plotter_props
        gp_obj = bpy.data.objects.get(gpobjects.gp_object)
        if gp_obj and gp_obj["math_anim_obj"]:
            gp_layer = gp_obj.data.layers.get(self.gp_layer)
            if gp_layer:
                for var_name in vb.plot_variable_tracking['plot']:
                    maths =  vb.plot_variable_tracking['plot'][var_name].get((gp_obj, gp_layer), {})
                    if maths:
                        if maths['functions'][0] == 'PARAFUNCTION':
                            plotter_props.plot_func=f"x={maths['functions'][1]}, y={maths['functions'][2]}, z={maths['functions'][3]}"
                            if maths['plot_branch']:
                                plotter_props.branch_plot = maths['branch_axis']
                        elif maths['functions'][0] == 'ODEFUNCTION':
                            plotter_props.plot_func=f"dx/dt={maths['functions'][1]}, dy/dt={maths['functions'][2]}, dz/dt={maths['functions'][3]}"
                            if maths['plot_branch']:
                                plotter_props.branch_plot = maths['branch_axis']
                            ode_setting = context.scene.math_anim_ode_settings
                            if ode_setting.ode_dt != maths['ode_dt']:
                                ode_setting.ode_dt = maths['ode_dt']
                            if ode_setting.ode_t0 != maths['ode_t0']:
                                ode_setting.ode_t0 = maths['ode_t0']
                            if ode_setting.ode_t1 != maths['ode_t1']:
                                ode_setting.ode_t1 = maths['ode_t1']
                            if ode_setting.ds_use_dt != maths['ds_use_dt']:
                                ode_setting.ds_use_dt = maths['ds_use_dt']
                            ode_setting.ode_solver = maths['ode_solver']
                            ode_setting.branch_compose = maths['branch_compose']
                        else:
                            plotter_props.plot_func=f"{maths['functions'][1]}"
                        break
                # also update plotting transform to current layers
                if gp_obj["math_anim_obj"] in vb.gpencil_layer_nodes and gp_layer.name in vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]]:
                    if vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]][gp_layer.name].node_tree.nodes.get('Axis Labels'):
                        props = vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]][gp_layer.name].node_tree.nodes['Axis Labels'].node_tree.nodes['Transform Plotting']
                    else:
                        props = vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]][gp_layer.name].node_tree.nodes['Transform Plotting']
                    plotter_props.plot_translation = props.inputs['Translation'].default_value
                    plotter_props.plot_rotation = props.inputs['Rotation'].default_value
                    plotter_props.plot_scale = props.inputs['Scale'].default_value

    gp_layer: bpy.props.EnumProperty(
        name='Grease Pencil Layers',
        items=get_gp_layers,
        description="Grease pencil layer to be animated",
        get=gp_layer_getter,
        set=gp_layer_setter,
        update=updatePlotFunc,
    )

    draw_mode: BoolProperty(
        name="Draw Mode",
        description="Change to Draw Mode",
        default=False,
        update=updateMode,
    )
    axis_control: BoolProperty(
        name="Axis Control",
        description="Axis Detailed Control",
        default=False,
    )

classes = (
    MATH_ANIM_PathItem,
    MATH_ANIM_OptexItem,
    MATH_ANIM_TypstItem,
    MATH_ANIM_OptexCode_Properties,
    MATH_ANIM_OptexFile_Properties,
    MATH_ANIM_TypstCode_Properties,
    MATH_ANIM_TypstFile_Properties,
    MATH_ANIM_PdfFile_Properties,
    MATH_ANIM_Formula_Properties,
    MATH_ANIM_MorphItem,
    MATH_ANIM_MorphSettingContainer,
    MATH_ANIM_MorphCollectionContainer,
    MATH_ANIM_MorphObjContainer,
    MATH_ANIM_AnimSetting_Status,
    MATH_ANIM_Morph_Targets,
    MATH_ANIM_MorphSelectedIdx,
    MATH_ANIM_MorphAnimSettings,
    MATH_ANIM_IndividualSettings,
    MATH_ANIM_GPLayers,
    MATH_ANIM_GPObjects,
)
register, unregister = bpy.utils.register_classes_factory(classes)
