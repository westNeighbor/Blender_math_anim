import bpy
from bpy.props import *
import numpy as np
from .plotter_ops import rebuild_dynamic_parameters, parser_sumprod
from . import variables as vb

class MATH_ANIM_Plotter_Properties(bpy.types.PropertyGroup):
    def updatePara(self, context):
        if self.math_mode == "FUNCDATA":
            return None
        math_function = None
        if self.math_mode == "PARAFUNCTION":
            math_function = f"{self.function_x} {self.function_y} {self.function_z}"
        elif self.math_mode == "EFUNCTION":
            math_function = self.math_function
        elif self.math_mode == "POLARFUNCTION":
            math_function = self.polar_function
        elif self.math_mode == "IFUNCTION":
            if '=' not in self.implicit_function:
                math_function = self.implicit_function
            else:
                left, right = self.implicit_function.split('=', 1)
                math_function = f"({left.strip()}) - ({right.strip()})"
        elif self.math_mode == "ODEFUNCTION":
            math_function = f"{self.ode_function_x} {self.ode_function_y} {self.ode_function_z}"

        if any(sub in math_function for sub in ['sum_', 'nansum_', 'prod_', 'nanprod_']):
            eval_function, param_function = parser_sumprod(math_function)
            rebuild_dynamic_parameters(context.scene, self.math_mode, param_function)
        else:
            rebuild_dynamic_parameters(context.scene, self.math_mode, math_function)

    def updateFunc(self, context):
        if not self.plot_ctl:
            return None
        gpobjects = context.scene.math_anim_gpobjects
        gplayers  = context.scene.math_anim_gplayers
        gp_obj = bpy.data.objects.get(gpobjects.gp_object)
        if gp_obj and gp_obj["math_anim_obj"]:
            gp_layer = gp_obj.data.layers.get(gplayers.gp_layer)
            if gp_layer:
                for var_name in vb.plot_variable_tracking['plot']:
                    maths =  vb.plot_variable_tracking['plot'][var_name].get((gp_obj, gp_layer), {})
                    if maths:
                        if maths['functions'][0] == 'PARAFUNCTION':
                            self.plot_func=f"x={maths['functions'][1]}, y={maths['functions'][2]}, z={maths['functions'][3]}"
                            if maths['plot_branch']:
                                self.branch_plot = maths['branch_axis']
                        elif maths['functions'][0] == 'ODEFUNCTION':
                            self.plot_func=f"dx/dt={maths['functions'][1]}, dy/dt={maths['functions'][2]}, dz/dt={maths['functions'][3]}"
                            if maths['plot_branch']:
                                self.branch_plot = maths['branch_axis']
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
                            self.plot_func=f"{maths['functions'][1]}"
                        break

    def updateTransform(self, context, prop="translation"):
        gpobjects = context.scene.math_anim_gpobjects
        gplayers  = context.scene.math_anim_gplayers
        gp_obj = bpy.data.objects.get(gpobjects.gp_object)
        if gp_obj and gp_obj["math_anim_obj"]:
            layer1 = gp_obj.data.layers.get(gplayers.gp_layer)
            update_layers = []
            if layer1:
                update_layers.append(layer1)
                names = layer1.name.rsplit('.', 1)
                if len(names)==2 and names[1] == 'axis':
                    layer2 = gp_obj.data.layers.get(names[0])
                    if layer2:
                        update_layers.append(layer2)
                else:
                    layer2 = gp_obj.data.layers.get(f"{layer1.name}.axis")
                    if layer2:
                        update_layers.append(layer2)
            for gp_layer in update_layers:
                if gp_obj["math_anim_obj"] in vb.gpencil_layer_nodes and gp_layer.name in vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]]:
                    if vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]][gp_layer.name].node_tree.nodes.get('Axis Labels'):
                        props = vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]][gp_layer.name].node_tree.nodes['Axis Labels'].node_tree.nodes['Transform Plotting']
                    else:
                        props = vb.gpencil_layer_nodes[gp_obj["math_anim_obj"]][gp_layer.name].node_tree.nodes['Transform Plotting']
                    if prop == "translation":
                        props.inputs['Translation'].default_value = self.plot_translation
                    elif prop == "rotation":
                        props.inputs['Rotation'].default_value = self.plot_rotation
                    elif prop == "scale":
                        props.inputs['Scale'].default_value = self.plot_scale

    def updateTranslation(self, context):
        self.updateTransform(context, prop="translation")

    def updateRotation(self, context):
        self.updateTransform(context, prop="rotation")

    def updateScale(self, context):
        self.updateTransform(context, prop="scale")

    math_extra_num_vars: IntProperty(
        name="Reserved Extra Number of Variables",
        default=10,
        min=0,
        description=("Reserved extra number of variable names for math functions \n"
                     "x0,x1,x2,...,x9 will be treated as variables besides x if set to 10 \n"
                     "similarly for y,z,u,v,t,θ"
                     )
    )

    polar_function: StringProperty(
        name="r(θ), r(u) or r(t)",
        default="cos(2*θ)",
        description=("Polar Function to plot, variable priority θ > u > t \n"
                     "Use same variable or params with other plots will be controled together\n"
                     "The variable can be θ, θ[1-9], t, t[1-9], u, u[1-9] if you need independent variable for each plot"
                     ),
        update=updatePara
    )
    math_function: StringProperty(
        name="f(x,y) or f(u,v) or f(t)",
        default="sin(x+a)*cos(y*b)+c",
        description=("Explicit Function to plot, variable priority x=y > u=v > t \n"
                     "Use same variables or params with other plots will be controled together\n"
                     "The variable can be x,y, [x,y][1-9], u,v, [u,v][1-9], t, t[1-9] if you need independent variables for each plot"
                     ),
        update=updatePara
    )
    self_iteration: BoolProperty(
        name="Self Iteration",
        default=False,
        description=("Whether to use self iteration for explicit function. \n"
                      "The self iteration will use the previous value to calculate the next value. \n"
                      "It plot the iterations vs the values for normal functions,\n"
                      "While for complex function plot real vs imaginary part, one can aslo plot iteration vs branch"
        ),
        update=updatePara,
    )
    implicit_function: StringProperty(
        name="f(x,y,[z])=0 or f(u,v,[w])=0",
        default="x**2+(y-(x**2)**(1/3))**2-1=0",
        description=("Implicit Function to plot, variable priority x=y=z > u=v=w \n"
                     "Use same params with other plots will be controled together\n"
                     "The variable can be x,y,z, [x,y,z][1-9], u,v,w, [u,v,w][1-9]"
                     ),
        update=updatePara
    )
    function_x: StringProperty(
        name="x(t) or x(u,v)",
        default="cos(a*t)",
        description=("Parametric function for X axis, variable priority u=v > t \n"
                     "Use same variables or params with other plots will be controled together\n"
                     "The variable can be u,v, u,v[1-9], t, t[1-9] if you need independent variables for each plot"
                     ),
        update=updatePara,
    )
    function_y: StringProperty(
        name="y(t) or y(u,v)",
        default="sin(t+b)",
        description=("Parametric function for Y axis, variable priority u=v > t \n"
                     "Use same variables or params with other plots will be controled together\n"
                     "The variable can be u,v, u,v[1-9], t, t[1-9] if you need independent variables for each plot"),
        update=updatePara,
    )
    function_z: StringProperty(
        name="z(t) or z(u,v)",
        default="0",
        description=("Parametric function for Z axis, variable priority u=v > t \n"
                     "Use same variables or params with other plots will be controled together\n"
                     "The variable can be u,v, u,v[1-9], t, t[1-9] if you need independent variables for each plot"),
        update=updatePara,
    )
    ode_function_x: StringProperty(
        name="dx/dt = f(x,[y,z,t]) or du/dt=f(u,[v,w,t])",
        default="a*(y-x)",
        description=("ODE function for x[u] branch, variable priority x=y=z, u=v=w \n"
                     "Use same params with other plots will be controled together\n"
                     "The variable can be x,y,z, [x,y,z][1-9], u,v,w, [u,v,w][1-9]"
                     ),
        update=updatePara,
    )
    ode_function_y: StringProperty(
        name="dy/dt = f(x,[y,z,t]) or dv/dt=f(u,[v,w,t])",
        default="x*(b-z)-y",
        description=("ODE function for y[v] branch, variable priority x=y=z, u=v=w \n"
                     "Use same params with other plots will be controled together\n"
                     "The variable can be x,y,z, [x,y,z][1-9], u,v,w, [u,v,w][1-9]"
                     ),
        update=updatePara,
    )
    ode_function_z: StringProperty(
        name="dz/dt = f(x,[y,z,t]) or dw/dt=f(u,[v,w,t])",
        default="x*y-c*z",
        description=("ODE function for z[w] branch, variable priority x=y=z, u=v=w \n"
                     "Use same params with other plots will be controled together\n"
                     "The variable can be x,y,z, [x,y,z][1-9], u,v,w, [u,v,w][1-9]"
                     ),
        update=updatePara,
    )

    ode_solver: EnumProperty(
        name="ODE Solver method",
        description ="Choose the ODE solver method for ODE plots, options are: RK4, RK45",
        items=[
            ("RK4", "Fixed step RK4", "Fast fixed step ODE solver, good for smooth curve \n"
                                       "May not work well for stiff or rapid change systems \n"
                                       "Decrese step size too much could be slow."),
            ("RK45", "Adaptive step RK45", "Automatic step size adjustment for stiff or rapid change \n"
                                           "Often more accurate for same computation time if system has varying scales\n"
                                           "computes two solutions every step so slower per step."),
            ("DIFFSOL", "Diffsol Methods", "Methods from pydiffsol package, which should be more robust and stable \n"
                                           "They provide BDF and RK solvers with more flexible adjustments \n"
                                           "Check https://github.com/martinjrobins/diffsol and https://github.com/alexallmont/pydiffsol"),
        ],
        default="RK45",
    )
    ds_solver_type: EnumProperty(
        name="Diffsol Solver Method",
        description="Choose the diffsol method if ODE solver is set to DIFFSOL",
        items=[("bdf", "BDF Method", "Backward Differentiation Formula, good for stiff systems"),
               ("esdirk34", "Runge-Kutta Method (esdirk34)", "Explicit Runge-Kutta method, good for non-stiff systems"),
               ("tr_bdf2", "BDF Method (tr_bdf2)", "Trapezoidal Backward Differentiation Formula of order 2 (TR-BDF2) method for moderately stiff stystems"),
               ("tsit45", "Runge-Kutta Method (tsit45)", "Tsitouras 4/5th order Explicit Runge-Kutta (TSIT45) method for non-stiff systems")],
        default="esdirk34",
    )
    ds_linear_solver_type: EnumProperty(
        name="Diffsol Linear Solver Type",
        description="Choose the diffsol linear solver type if ODE solver is set to DIFFSOL",
        items=[("lu", "LU", "use LU decomposition linear solver (dense or sparse as appropriate)"),
               ("klu", "KLU", "use KLU sparse linear solver")],
        default="lu",
    )
    ds_matrix_type: EnumProperty(
        name="Diffsol Matrix Type",
        description=("Choose the diffsol matrix type if ODE solver is set to DIFFSOL and solver type is LU \n"
                     "For small systems, dense matrix is usually faster, for large systems with sparse jacobian, sparse matrix is more efficient"
                     ),
        items=[("nalgebra_dense", "Nalgebra Dense", "dense matrix using nalgebra crate"),
               ("faer_dense", "Faer Dense", "dense matrix using faer crate"),
               ("faer_sparse", "Faer Sparse", "sparse matrix using faer crate")],
        default="nalgebra_dense",
    )
    ds_has_stop: BoolProperty(
        name="Diffsol has stop condition",
        description=("Whether the diffsol solver has stop condition, if checked, you can set the stop condition in the ODE function,\n"
                    "check the Bouncing Ball example https://pydiffsol.readthedocs.io/en/latest/examples/bouncing_ball.html"
                    ),
        default=False,
    )
    ds_stop_function: StringProperty(
        name="Diffsol Stop Function",
        default="x-1",
        description=("The stop function for diffsol solver if has_stop is checked,\n"
                     "the solver will stop when this function is zero and start over with current state if final time is not reached, \n"
                     "for example x-1 will stop when x reaches 1"
                     ),
    )
    ds_use_dt: BoolProperty(
        name="Diffsol use fixed dt",
        description=("Whether to use fixed dt for diffsol solver, if not checked, the solver will use adaptive time stepping based on the chosen method's error control"),
        default=False,
    )
    ds_reset_function: StringProperty(
        name="Diffsol Reset State Function",
        default="x+1e-12, -0.8*y,",
        description=("The function to update the state for diffsol solver at stop,\n"
                     "it should match the number of variables, for example, you have variables of x, y, z,\n"
                     "then you need to use ',' to separate three state update function\n"
                     "also need give a small positive value like 1e-12 to avoid the solver stuck \n"
                     "at the stop condition when reset to the same state, for example: x+1e-12, -0.8*y, z"),
    )
    ds_hybrid_model: StringProperty(name="Diffsol Hybrid Model", default="", description="The functions change for hybrid model in diffsol, separated by ',', coordinate with `stop` ")

    def updatePlot(self, context):
        pass
    plot_branch: BoolProperty(
        name="Plot Branch",
        default=False,
        description=("For ODE or parametric function, \n"
                    "check this to plot the branch (x,y,z) with parameter range,\n"
                    "for example t vs x, or (u,v) vs x."
                     ),
        update=updatePlot,
    )
    branch_axis: EnumProperty(
        items=[('x', 'x', ''), ('y', 'y', ''), ('z', 'z', ''), ('compose', 'compose', '')],
        default='x',
        name="Branch Axis",
        description="Choose the axis to plot the branch against for ODE or parametric functions",
        update=updatePlot,
    )
    branch_plot: StringProperty(
        name="Branch",
        default="",
        description="The branch plot if plot_branch is checked",
    )
    branch_compose: StringProperty(
        name="Branch Compose",
        default="x+y+z",
        description="Compose branches to plot",
    )

    plot_func: StringProperty(
        name="Current Plot Function",
        default="",
        description="Current plot's function",
    )

    plot_ctl: BoolProperty(
        name="Current Plot Control",
        default=False,
        description="Current plot's paramters and variables control for the plotting layers",
        update=updateFunc,
    )

    plot_translation: FloatVectorProperty(
        name="Translation Plotting",
        default = (0.0, 0.0, 0.0),
        subtype = 'TRANSLATION',
        description="Translation plotting (including axis)",
        update=updateTranslation,
    )

    plot_rotation: FloatVectorProperty(
        name="Rotate Plotting",
        default = (0.0, 0.0, 0.0),
        subtype = 'EULER',
        description="Rotate plotting (including axis)",
        update=updateRotation,
    )

    plot_scale: FloatVectorProperty(
        name="Scale Plotting",
        subtype = 'XYZ',
        default = (1.0, 1.0, 1.0),
        description="Scale plotting (including axis)",
        update=updateScale,
    )

    plot_fixedsize: BoolProperty(
        name="Fixed the Plotting Size",
        default = False,
        description="Fixed plotting (including axis) size",
    )

    plot_size: FloatVectorProperty(
        name="Fixed Size Plotting",
        default = (2.0, 2.0, 2.0),
        subtype = 'TRANSLATION',
        description="Fixed plotting (including axis) size",
    )

    math_mode: EnumProperty(
        name="Mode",
        description ="Choose the math function type to plot, options are: EFUNCTION, PARAFUNCTION, POLARFUNCTION, ODEFUNCTION, IFUNCTION, FUNCDATA",
        items=[
            ("EFUNCTION", "Explicit Function", "z,y=f(x, y), f(u,v) or f(t), variable priority x=y > u=v > t. \n"
                                                "The plot dimension = number of variables, for example: \n"
                                                "f(x,y) = 1 plot 1D x = 1, \n"
                                                "f(x,y) = 0*x +1, plot 2D y=1, \n"
                                                "f(x,y) = 0*(x+y) + 1 plot 3D z=1 \n"
                                                "For others, like xz plane plot z = 2*x, go to parametric function."),
            ("PARAFUNCTION", "Parametric Function", "x,y,z=f(u,v) or f(t), variable priority u=v > t"),
            ("POLARFUNCTION", "Polar Function", "r=r(θ), r(u) or r(t), variable priority θ > u > t"),
            ("ODEFUNCTION", "ODE Function", "dx[y,z]/dt=f(x,[y,z]), du[v,w]/dt=f(u,[v,w]), variable priority x=y=z > u=v=w \n"
                                            "Just for explicit given system dx[y,z]/dt = f(t,x,[y,z]) \n"
                                            "And linearly implicit systems A(t,x,[y,z])dx[y,z]/dt = g(t,x,[y,z]) \n"
                                            "Currently just my own written simple solvers, \n"
                                            "may use scipy solvers in the future"),
            ("IFUNCTION", "Implicit Function", "F(x,y,[z])=0, F(u,v,[w])=0, variable priority x=y=z > u=v=w \n"
                                                      "Use my own written functions to estimate the curve/surface\n"
                                                      "May fail for complex functions or disconnected curves/surfaces or with sharp corners"),
            #("CUSTOMFUNCSOLVER", "Custom Function Solver", "Use your own function solver, follow the template \n"),
            ("FUNCDATA", "Function Data", "Use your own function data, only first 3 columns will be used for x,y,z \n"),
        ],
        default="EFUNCTION",
        update=updatePara,
    )

class MATH_ANIM_ODE_Settings(bpy.types.PropertyGroup):
    def update_ode_t0(self, context):
        gp_obj = bpy.data.objects.get(context.scene.math_anim_gpobjects.gp_object)
        if gp_obj:
            gp_layer = gp_obj.data.layers.get(context.scene.math_anim_gplayers.gp_layer)
            if gp_layer:
                if vb.plot_variable_tracking['plot']['dt'][(gp_obj, gp_layer)]['ode_t0'] != self.ode_t0:
                    for param in vb.plot_variable_tracking['plot']:
                        if vb.plot_variable_tracking['plot'][param].get((gp_obj, gp_layer)):
                            vb.plot_variable_tracking['plot'][param][(gp_obj, gp_layer)]['ode_t0'] = self.ode_t0
                    vb.plot_variable_tracking['value']['dt'] = (getattr(context.scene, 'math_param_dt'), True)
                bpy.ops.math_anim.create_plot(update_tag=True)
    def update_ode_t1(self, context):
        gp_obj = bpy.data.objects.get(context.scene.math_anim_gpobjects.gp_object)
        if gp_obj:
            gp_layer = gp_obj.data.layers.get(context.scene.math_anim_gplayers.gp_layer)
            if gp_layer:
                if vb.plot_variable_tracking['plot']['dt'][(gp_obj, gp_layer)]['ode_t1'] != self.ode_t1:
                    for param in vb.plot_variable_tracking['plot']:
                        if vb.plot_variable_tracking['plot'][param].get((gp_obj, gp_layer)):
                            vb.plot_variable_tracking['plot'][param][(gp_obj, gp_layer)]['ode_t1'] = self.ode_t1
                    vb.plot_variable_tracking['value']['dt'] = (getattr(context.scene, 'math_param_dt'), True)
                bpy.ops.math_anim.create_plot(update_tag=True)
    def update_ode_dt(self, context):
        gp_obj = bpy.data.objects.get(context.scene.math_anim_gpobjects.gp_object)
        if gp_obj:
            gp_layer = gp_obj.data.layers.get(context.scene.math_anim_gplayers.gp_layer)
            if gp_layer:
                if vb.plot_variable_tracking['plot']['dt'][(gp_obj, gp_layer)]['ode_dt'] != self.ode_dt:
                    for param in vb.plot_variable_tracking['plot']:
                        if vb.plot_variable_tracking['plot'][param].get((gp_obj, gp_layer)):
                            vb.plot_variable_tracking['plot'][param][(gp_obj, gp_layer)]['ode_dt'] = self.ode_dt
                    vb.plot_variable_tracking['value']['dt'] = (getattr(context.scene, 'math_param_dt'), True)
                bpy.ops.math_anim.create_plot(update_tag=True)
    def update_ode_ds_use_dt(self, context):
        gp_obj = bpy.data.objects.get(context.scene.math_anim_gpobjects.gp_object)
        if gp_obj:
            gp_layer = gp_obj.data.layers.get(context.scene.math_anim_gplayers.gp_layer)
            if gp_layer:
                if vb.plot_variable_tracking['plot']['dt'][(gp_obj, gp_layer)]['ds_use_dt'] != self.ds_use_dt:
                    for param in vb.plot_variable_tracking['plot']:
                        if vb.plot_variable_tracking['plot'][param].get((gp_obj, gp_layer)):
                            vb.plot_variable_tracking['plot'][param][(gp_obj, gp_layer)]['ds_use_dt'] = self.ds_use_dt
                    vb.plot_variable_tracking['value']['dt'] = (getattr(context.scene, 'math_param_dt'), True)
                bpy.ops.math_anim.create_plot(update_tag=True)
    ode_t0: FloatProperty(
        name="t0",
        default=0.0,
        update=update_ode_t0,
    )
    ode_t1: FloatProperty(
        name="t1",
        default=10.0,
        update=update_ode_t1,
    )
    ode_dt: FloatProperty(
        name="dt",
        default=0.02,
        update=update_ode_dt,
    )
    ds_use_dt: BoolProperty(
        name="use fixed dt",
        description=("Whether to use fixed dt for diffsol solver, if not checked, the solver will use adaptive time stepping based on the chosen method's error control"),
        default=False,
        update=update_ode_ds_use_dt,
    )
    ode_solver: StringProperty()
    branch_compose: StringProperty()

class MATH_ANIM_DataPathItem(bpy.types.PropertyGroup):
    path: bpy.props.StringProperty(name="File Path", description="data file to plot, only first 3 columns will be used for x,y,z")
    selected: bpy.props.BoolProperty(name="Selected", default=True, description="Select to use")  # Multi-selection
    delim: bpy.props.StringProperty(name="Delimiter", default=" ", description="Only single char is supported, default is space")  # Separator

class MATH_ANIM_FuncData_Properties(bpy.types.PropertyGroup):
    paths: bpy.props.CollectionProperty(type=MATH_ANIM_DataPathItem)
    active_index: bpy.props.IntProperty(default=-1)

classes = (
    MATH_ANIM_Plotter_Properties,
    MATH_ANIM_DataPathItem,
    MATH_ANIM_FuncData_Properties,
    MATH_ANIM_ODE_Settings,
)

register, unregister = bpy.utils.register_classes_factory(classes)
