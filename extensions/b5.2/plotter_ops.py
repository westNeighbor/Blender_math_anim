import bpy
import math
import re
import uuid
import numpy as np
from .operations import MATH_OT_CreateFormula
from . import variables as vb
from bpy.props import FloatProperty, IntProperty, StringProperty
#import numexpr as ne
from asteval import Interpreter
import math
from .geonodes import import_anim_nodegroups, create_node
from .utils import ErrorMessageBox
from .eqn_solver import make_ode_derivs, make_implicit_func, solve_ode_adaptive, solve_ode_rk4, auto_solve_implicit
from rust_fastmath import solve_expr_ode_rk4, solve_expr_ode_adaptive
import pydiffsol as ds

def calculate_bezier_circle(radius=1.0, num_segments=8):
    angle_step = 2 * math.pi / num_segments  # Step size

    # Constant to determine control point distance
    control_distance = (4 / 3) * math.tan(math.pi / (2 * num_segments))

    control_points = []
    left_handles   = []
    right_handles  = []
    for i in range(num_segments):
        # Start and end angles for the segment
        start_angle = i * angle_step
        control_point = (radius * math.cos(start_angle), radius * math.sin(start_angle), 0.0)
        # Control points
        control_right = (control_point[0] - control_distance * radius * math.sin(start_angle),
                          control_point[1] + control_distance * radius * math.cos(start_angle), 0.0)
        control_left = (control_point[0] + control_distance * radius * math.sin(start_angle),
                          control_point[1] - control_distance * radius * math.cos(start_angle), 0.0)

        # Append points
        control_points.append(control_point)
        left_handles.append(control_left)
        right_handles.append(control_right)

    return control_points, left_handles, right_handles

def recommended_tick_count(values, target_ticks=5, max_ticks=10):
    if len(values) < 2:
        return 2

    vmin, vmax = min(values), max(values)
    span = abs(vmax - vmin)
    if span == 0:
        return 2

    rough_step = span / target_ticks

    # Find a "nice" step size (1, 2, 2.5, 5, 10, etc.)
    if math.isnan(np.log10(rough_step)):
        ErrorMessageBox(message="Cannot compute nice tick count due to NaN values. Probably invalid math encountered, check your variable range to make sure the math valid.", title="Warning", icon='WARNING_LARGE')
        return 2
    if math.isinf(np.log10(rough_step)):
        ErrorMessageBox(message="Cannot compute nice tick count due to inf values. Check your variable range to make sure the math valid.", title="Warning", icon='WARNING_LARGE')
        return 2
    magnitude = 10 ** int(np.floor(np.log10(rough_step)))
    candidates = [1, 2, 2.5, 5, 10]
    best_step = min(candidates, key=lambda x: abs(rough_step - x * magnitude))
    step = best_step * magnitude

    tick_count = int(np.ceil(span / step)) + 1
    return min(max(2, tick_count), max_ticks)

def nice_number(value, round_=True):
    """
    Rounds value to a "nice" number (1, 2, 5, 10, etc.)
    """
    if math.isnan(math.log10(value)):
        #ErrorMessageBox(message="Cannot compute nice tick count due to NaN values.", title="Warning", icon='WARNING_LARGE')
        exponent = 1
    elif math.isinf(math.log10(value)):
        #ErrorMessageBox(message="Cannot compute nice tick count due to inf values.", title="Warning", icon='WARNING_LARGE')
        exponent = 1
    else:
        exponent = math.floor(math.log10(value))
    fraction = value / (10 ** exponent)

    if round_:
        if fraction < 1.5:
            nice = 1
        elif fraction < 3:
            nice = 2
        elif fraction < 7:
            nice = 5
        else:
            nice = 10
    else:
        if fraction <= 1:
            nice = 1
        elif fraction <= 2:
            nice = 2
        elif fraction <= 5:
            nice = 5
        else:
            nice = 10

    return nice * 10**exponent

def pretty_axis_ticks(data, n_ticks=5):
    """
    Given a list of numbers, returns nice axis ticks.
    """
    dmin, dmax = min(data), max(data)
    range_ = dmax - dmin

    if range_ == 0:
        range_ = abs(dmin) if dmin != 0 else 1

    step = nice_number(range_ / (n_ticks - 1), round_=True)
    if math.isnan(dmin/step):
        #ErrorMessageBox(message="Cannot compute nice axis ticks due to NaN values.", title="Warning", icon='WARNING_LARGE')
        return [0.0, 1.0]
    if math.isinf(dmin/step):
        #ErrorMessageBox(message="Cannot compute nice axis ticks due to inf values.", title="Warning", icon='WARNING_LARGE')
        return [0.0, 1.0]
    graph_min = math.floor(dmin / step) * step
    graph_max = math.ceil(dmax / step) * step

    ticks = []
    val = graph_min
    while val <= graph_max + 1e-10:
        ticks.append(round(val, 10))  # rounding to avoid floating point weirdness
        val += step

    return ticks

def extract_param_names(math_mode, expression):
    if math_mode == 'PARAFUNCTION':
        vb.VARS_USED.clear()
        vb.VARS_USED = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) & ({'u', 'v'} | {f'{x}{n}' for x in ['u', 'v'] for n in range(bpy.context.scene.math_anim_plotter_props.math_extra_num_vars)})
        if not vb.VARS_USED:
            vb.VARS_USED = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) & ({'t'} | {f't{n}' for n in range(bpy.context.scene.math_anim_plotter_props.math_extra_num_vars)})
        if len(vb.VARS_USED) > 2:
            ErrorMessageBox(message=f"Up to 2 variables are supported , but you have ({vb.VARS_USED}). \n"
                                    f"Will proceed with variables: {list(vb.VARS_USED)[:2]}\n"
                                    f"Change the function to make it clear.",
                            title="Too many variables!!!", icon='WARNING_LARGE')
            vb.VARS_USED = set(list(vb.VARS_USED)[:2])
        if not vb.VARS_USED:
            vb.VARS_USED = {'t'}
        vb.VARS_USED = set(sorted(vb.VARS_USED))
        return sorted(set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) - vb.VARS_USED - vb.math_fns)
    elif math_mode == 'POLARFUNCTION':
        vb.VARS_USED.clear()
        vb.VARS_USED = set(re.findall(r"\b[a-zA-Z_|θ][a-zA-Z0-9_]*\b", expression)) & ({'θ'} | {f'θ{n}' for n in range(bpy.context.scene.math_anim_plotter_props.math_extra_num_vars)})
        if not vb.VARS_USED:
            vb.VARS_USED = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) & ({'u'} | {f'u{n}' for n in range(bpy.context.scene.math_anim_plotter_props.math_extra_num_vars)})
        if not vb.VARS_USED:
            vb.VARS_USED = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) & ({'t'} | {f't{n}' for n in range(bpy.context.scene.math_anim_plotter_props.math_extra_num_vars)})
        if len(vb.VARS_USED) > 1:
            ErrorMessageBox(message=f"Only 1 variable is supported , but you have ({vb.VARS_USED}). \n"
                                    f"Will proceed with variables: {list(vb.VARS_USED)[:1]}\n"
                                    f"Change the function to make it clear.",
                            title="Too many variables!!!", icon='WARNING_LARGE')
            vb.VARS_USED = set(list(vb.VARS_USED)[:1])
        if not vb.VARS_USED:
            vb.VARS_USED = {'t'}
        vb.VARS_USED = set(sorted(vb.VARS_USED))
        return sorted(set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) - vb.VARS_USED - vb.math_fns)
    elif math_mode == 'EFUNCTION':
        vb.VARS_USED.clear()
        vb.VARS_USED = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) & ({'x', 'y', 'z'} | {f'{x}{n}' for x in ['x', 'y', 'z'] for n in range(bpy.context.scene.math_anim_plotter_props.math_extra_num_vars)})
        if not vb.VARS_USED:
            vb.VARS_USED = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) & ({'u', 'v', 'w'} | {f'{x}{n}' for x in ['u', 'v', 'w'] for n in range(bpy.context.scene.math_anim_plotter_props.math_extra_num_vars)})
        if not vb.VARS_USED:
            vb.VARS_USED = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) & ({'t'} | {f't{n}' for n in range(bpy.context.scene.math_anim_plotter_props.math_extra_num_vars)})
        if bpy.context.scene.math_anim_plotter_props.self_iteration:
            if len(vb.VARS_USED) > 1:
                ErrorMessageBox(message=f"For self-iteration, only 1 variable is supported , but you have ({vb.VARS_USED}). \n"
                                        f"Will proceed with variables: {list(vb.VARS_USED)[:1]}\n"
                                        f"Change the function to make it clear.",
                                title="Too many variables!!!", icon='WARNING_LARGE')
                vb.VARS_USED = set(list(vb.VARS_USED)[:1])
        if len(vb.VARS_USED) > 2:
            ErrorMessageBox(message=f"Up to 2 variables are supported , but you have ({vb.VARS_USED}). \n"
                                    f"Will proceed with variables: {list(vb.VARS_USED)[:2]}\n"
                                    f"Change the function to make it clear.",
                            title="Too many variables!!!", icon='WARNING_LARGE')
            vb.VARS_USED = set(list(vb.VARS_USED)[:2])
        if not vb.VARS_USED:
            vb.VARS_USED = {'t'}
        vb.VARS_USED = set(sorted(vb.VARS_USED))
        return sorted(set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) - vb.VARS_USED - vb.math_fns)
    elif math_mode == 'IFUNCTION':
        # reserve step, n_steps as parameters for implicit function solver
        # step: step size along curve/surface; n_steps: number of points to trace
        reserved_params = {'step', 'n_steps'}
        vb.VARS_USED.clear()
        vb.VARS_USED = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) & ({'x', 'y', 'z'} | {f'{x}{n}' for x in ['x', 'y', 'z'] for n in range(bpy.context.scene.math_anim_plotter_props.math_extra_num_vars)})
        if not vb.VARS_USED:
            vb.VARS_USED = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) & ({'u', 'v', 'w'} | {f'{x}{n}' for x in ['u', 'v', 'w'] for n in range(bpy.context.scene.math_anim_plotter_props.math_extra_num_vars)})
        if len(vb.VARS_USED) > 3:
            ErrorMessageBox(message=f"Up to 3 variables are supported , but you have ({vb.VARS_USED}). \n"
                                    f"Change the function's variables to make it clear.",
                            title="Too many variables!!!", icon='WARNING_LARGE')
        param_check = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) & reserved_params
        if param_check:
            ErrorMessageBox(message=f"Reserved parameters {param_check} are used, change them to other names.",
                            title="Use reserved parameters!!!", icon='WARNING_LARGE')
        if not vb.VARS_USED:
            ErrorMessageBox(message=f"No variables are detected, check your function!!!",
                            title="No variables!!!", icon='WARNING_LARGE')
        vb.VARS_USED = set(sorted(vb.VARS_USED))
        return sorted(set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) - vb.VARS_USED - vb.math_fns - reserved_params)
    elif math_mode == 'ODEFUNCTION':
        # reserve t0, t1 as time span, x0[u0], y0[v0], z0[w0] as initial conditions, all these are parameters
        vb.VARS_USED.clear()
        vb.VARS_USED = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) & ({'x', 'y', 'z', 't'} |  {f'{x}{n}' for x in ['x', 'y', 'z'] for n in range(bpy.context.scene.math_anim_plotter_props.math_extra_num_vars)})
        if len(vb.VARS_USED) > 3:
            ErrorMessageBox(message=f"Up to 3 variables are supported , but you have ({vb.VARS_USED}). \n"
                                    f"Change the function's variables to make it clear.",
                            title="Too many variables!!!", icon='WARNING_LARGE')
        reserved_params = {'t0', 't1', 'dt'} | {f'{v}0' for v in vb.VARS_USED}
        param_check = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) & reserved_params
        if param_check:
            ErrorMessageBox(message=f"Reserved parameters {param_check} are used, change them to other names.",
                            title="Use reserved parameters!!!", icon='WARNING_LARGE')
        if not vb.VARS_USED:
            vb.VARS_USED = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) & ({'u', 'v', 'w', 't'} |  {f'{x}{n}' for x in ['u', 'v', 'w'] for n in range(bpy.context.scene.math_anim_plotter_props.math_extra_num_vars)})
            if len(vb.VARS_USED) > 3:
                ErrorMessageBox(message=f"Up to 3 variables are supported , but you have ({vb.VARS_USED}). \n"
                                        f"Change the function's variables to make it clear.",
                                title="Too many variables!!!", icon='WARNING_LARGE')
            reserved_params = {'t0', 't1', 'dt'} | {f'{v}0' for v in vb.VARS_USED}
            param_check = set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) & reserved_params
            if param_check:
                ErrorMessageBox(message=f"Reserved parameters {param_check} are used, change them to other names.",
                                title="Use reserved parameters!!!", icon='WARNING_LARGE')
        if not vb.VARS_USED:
            ErrorMessageBox(message=f"No variables are detected, check your function!!!",
                            title="No variables!!!", icon='WARNING_LARGE')
        vb.VARS_USED = set(sorted(vb.VARS_USED))
        return sorted(set(re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", expression)) - vb.VARS_USED - vb.math_fns - reserved_params)
    else:
        vb.VARS_USED.clear()
        return []

def get_param_value(scene, name):
    return getattr(scene, f"math_param_{name}", 0.0)

def get_var_value(scene, name):
    return getattr(scene, name, 0.0)

def evaluate_expr(expr, local_dict):
    aeval = Interpreter()
    aeval.symtable.update(local_dict)
    try:
        return aeval(expr)
    except:
        return 0.0

def find_matching_paren(s, start):
    depth = 0
    for i in range(start, len(s)):
        if s[i] == '(':
            depth += 1
        elif s[i] == ')':
            depth -= 1
            if depth == 0:
                return i
    raise ValueError("Unmatched parenthesis")

# A parser to convert sum_{i=start}^{end}(expr) and prod_{i=start}^{end}(expr) into python list comprehension with sum() or prod() which can be evaluated by asteval, also return a string of parameters and variables used in the expr
def parser_sumprod(expr):
    local_params = set()
    local_vars = set()
    build_param_expr = None
    i = 0
    while i < len(expr):
        match = re.search(r'(sum|prod)_\{(\w)=([\w\d]+)\}\^\{(?:\w=)?([\w\d]+)\}\(', expr[i:])
        if not match:
            break

        full_start = i + match.start()
        full_end = i + match.end()
        op, var, start, end = match.groups()
        local_vars.add(var)
        if not start.isnumeric():
            local_params.add(start)
        if not end.isnumeric():
            local_params.add(end)

        paren_start = full_end - 1
        paren_end = find_matching_paren(expr, paren_start)
        inner_expr = expr[paren_start + 1:paren_end]

        # Recursively convert the inner expression
        converted_inner, build_param_expr = parser_sumprod(inner_expr.strip())
        list_comp = f"[{converted_inner} for {var} in range({start}, {end}+1)]"
        replaced = None
        if op == 'sum':
            replaced = f"sum({list_comp}, axis=0)"
        elif op == 'nansum':
            replaced = f"nansum({list_comp}, axis=0)"
        elif op == 'prod':
            replaced = f"prod({list_comp}, axis=0)"
        elif op == 'nanprod':
            replaced = f"nanprod({list_comp}, axis=0)"

        if expr[:full_start]:
            if build_param_expr is None:
                build_param_expr = expr[:full_start]
            else:
                build_param_expr = f'{build_param_expr} + {expr[:full_start]}'
        sumprod_function = re.match(r'(sum|nansum|prod|nanprod)', converted_inner)
        if not sumprod_function:
            if build_param_expr is None:
                build_param_expr = converted_inner
            else:
                build_param_expr = f'{build_param_expr} + {converted_inner}'
        if expr[paren_end + 1:]:
            if build_param_expr is None:
                build_param_expr = expr[paren_end + 1:]
            else:
                build_param_expr = f'{build_param_expr} + {expr[paren_end + 1:]}'

        expr = expr[:full_start] + replaced + expr[paren_end + 1:]
        i = full_start + len(replaced)

    for param in local_params:
        if build_param_expr is None:
            build_param_expr = param
        else:
            build_param_expr = f'{build_param_expr} + {param}'
    for var in local_vars:
        build_param_expr = re.sub(rf'\b{var}\b', '1', build_param_expr)

    # the expr is a python evaluable expression, the build_param_expr is a string of parameters and variablesused in the expr which is used to extract variables and parameters
    return expr, build_param_expr

def update_scene_plot(self, context):
    # clean those don't exist anymore
    for param in vb.plot_variable_tracking['plot']:
        remove_keys = []
        for carrier, functions in vb.plot_variable_tracking['plot'][param].items():
            gp_obj, gp_layer = carrier[0], carrier[1]
            try:
                if not gp_obj.name or not gp_layer.name:
                    remove_keys.append((gp_obj, gp_layer))
            except:
                remove_keys.append((gp_obj, gp_layer))
        for key in remove_keys:
            vb.plot_variable_tracking['plot'][param].pop(key, None)
    for param in vb.plot_variable_tracking['params']:
        param_id = f'math_param_{param}'
        try:
            getattr(context.scene, param_id)
        except:
            continue
        if getattr(context.scene, param_id) != vb.plot_variable_tracking['value'][param][0]:
            vb.plot_variable_tracking['value'][param] = (getattr(context.scene, param_id), True)
            bpy.ops.math_anim.create_plot(update_tag=True)
        props = context.scene.math_anim_plotter_props
        if props.math_mode == 'EFUNCTION' and props.self_iteration:
            aeval = Interpreter()
            if np.iscomplexobj(aeval(context.scene.math_param_iter_init)):
                exclude_params = ['iter_init', 'n_iter']
                if param not in exclude_params and param in vb.DYNAMIC_PARAMS:
                    if not isinstance(getattr(context.scene, param_id), bpy.types.StringProperty):
                        delattr(bpy.types.Scene, param_id)
                        setattr(
                            bpy.types.Scene,
                            param_id,
                            StringProperty(
                                name=param,
                                default="0 + 0j",
                                update=update_scene_plot,
                                #update=update_scene_plot(var),
                            )
                        )
    for var_id in vb.plot_variable_tracking['vars']:
        try:
            getattr(context.scene, var_id)
        except:
            continue
        if getattr(context.scene, var_id) != vb.plot_variable_tracking['value'][var_id][0]:
            vb.plot_variable_tracking['value'][var_id] = (getattr(context.scene, var_id), True)
            bpy.ops.math_anim.create_plot(update_tag=True)


def rebuild_dynamic_parameters(scene, math_mode, math_function):

    if math_mode == 'ODEFUNCTION':
        if "g_i[N]" in math_function:
            math_function = math_function.replace("g_i[N]", "")
            scene.math_anim_plotter_props.ode_solver = "DIFFSOL"
            scene.math_anim_plotter_props.ds_has_stop = True
    param_names = extract_param_names(math_mode, math_function)
    if math_mode == 'ODEFUNCTION':
        for var in vb.VARS_USED:
            param_names.append(f'{var}0')
        param_names.extend(['t0', 't1', 'dt'])
    elif math_mode == 'IFUNCTION':
        param_names.extend(['step', 'n_steps'])
    elif math_mode == 'EFUNCTION':
        if scene.math_anim_plotter_props.self_iteration:
            param_names.extend(["n_iter", 'iter_init'])

    vb.DYNAMIC_PARAMS.clear()
    new_params = 0
    for param in param_names:
        if param not in vb.plot_variable_tracking['params']:
            vb.plot_variable_tracking['params'].append(param)
        new_scene_prop, scene_prop_id = register_dynamic_scene_props(param, type='param')
        new_params += new_scene_prop
        vb.DYNAMIC_PARAMS[param] = scene_prop_id[0]
        if new_params == 1: # update once is enough for new params
            vb.plot_variable_tracking['value'][param] = (getattr(scene, scene_prop_id[0]), True)
        else:
            vb.plot_variable_tracking['value'][param] = (getattr(scene, scene_prop_id[0]), False)

    new_vars = 0
    for var in vb.VARS_USED:
        prop_ids = {f"math_var_{var}_min", f"math_var_{var}_max", f"math_var_{var}_resolution"}
        for prop_id in prop_ids:
            if prop_id not in vb.plot_variable_tracking['vars']:
                vb.plot_variable_tracking['vars'].append(prop_id)
        new_scene_prop, scene_prop_id = register_dynamic_scene_props(var, type='var')
        new_vars += new_scene_prop
        for prop_id in scene_prop_id:
            if new_params == 0 and new_vars == 1: # update once is enough for new variables
                vb.plot_variable_tracking['value'][prop_id] = (getattr(scene, prop_id), True)
            else:
                vb.plot_variable_tracking['value'][prop_id] = (getattr(scene, prop_id), False)

    return param_names, new_params, new_vars

def register_dynamic_scene_props(var, type='var'):
    int_params = {'i','j','k','l','m','n', 'n_steps', "n_iter"} | {f'{x}{n}' for x in ['i','j','k','l','m','n'] for n in range(bpy.context.scene.math_anim_plotter_props.math_extra_num_vars)}
    reserved_params_default = {'t0':0.0, 't1':10.0, 'dt':0.02, 'step':0.010, 'n_steps':250, 'n_iter':100}
    scene = bpy.types.Scene
    new_scene_prop, scene_prop_id = False, []
    if type == 'param':
        prop_id = f"math_param_{var}"
        if not hasattr(scene, prop_id):
            if var == "iter_init":
                setattr(
                    bpy.types.Scene,
                    prop_id,
                    StringProperty(
                        name=var,
                        default="0.5",
                        update=update_scene_plot,
                        #update=update_scene_plot(var),
                    )
                )
            elif var in int_params:
                setattr(
                    bpy.types.Scene,
                    prop_id,
                    IntProperty(
                        name=var,
                        default=reserved_params_default[var] if var in reserved_params_default else 1,
                        update=update_scene_plot,
                        #update=update_scene_plot(var),
                    )
                )
            else:
                setattr(
                    bpy.types.Scene,
                    prop_id,
                    FloatProperty(
                        name=var,
                        default=reserved_params_default[var] if var in reserved_params_default else 1.0,
                        update=update_scene_plot,
                        #update=update_scene_plot(var),
                        precision=3 if var in {'step', 'dt'} else 2,
                    )
                )
            new_scene_prop = True
        scene_prop_id.append(prop_id)
    if type == 'var':
        prop_ids = {f"math_var_{var}_min":{'name': f'{var}_min', 'default':-np.pi}, f"math_var_{var}_max":{'name': f'{var}_max', 'default':np.pi}, f"math_var_{var}_resolution":{'name': f'{var}_resolution', 'default':100}}
        for i, (prop_id, value) in enumerate(prop_ids.items()):
            if not hasattr(scene, prop_id):
                if i<2:
                    setattr(
                        bpy.types.Scene,
                        prop_id,
                        FloatProperty(
                            name=value['name'],
                            default=value['default'],
                            update=update_scene_plot,
                            #update=update_scene_plot(prop_id),
                        )
                    )
                else:
                    setattr(
                        bpy.types.Scene,
                        prop_id,
                        IntProperty(
                            name=value['name'],
                            default=value['default'],
                            update=update_scene_plot,
                            #update=update_scene_plot(prop_id),
                            min=2,
                            max=10000,
                        )
                    )
                new_scene_prop = True
            scene_prop_id.append(prop_id)
    return new_scene_prop, scene_prop_id

class MATH_OT_CreatePlotter(bpy.types.Operator):
    bl_idname = "math_anim.create_plot"
    bl_label = "Create Math Plot"
    bl_description = "Add a new plotting as a new layer"
    bl_options = {'REGISTER', 'UNDO'}

    update_tag: bpy.props.BoolProperty(default=False) # create a new plot if False, For True, it can update the current plot with update_current_layer=True, otherwise, it will update all plots with the same param if param changes
    update_current_layer: bpy.props.BoolProperty(default=False) # update the current layer
    layer_name: bpy.props.StringProperty(default="") # if create a new plot, can give a name
    use_data: bpy.props.BoolProperty(default=False) # using data to plot instead of function plot
    use_data_file: bpy.props.BoolProperty(default=False) # load data file to plot instead of function plot

    def invoke(self, context, event):
        # clean those don't exist anymore
        for param in vb.plot_variable_tracking['plot']:
            remove_keys = []
            for carrier, functions in vb.plot_variable_tracking['plot'][param].items():
                gp_obj, gp_layer = carrier[0], carrier[1]
                if not gp_obj or not gp_layer:
                    remove_keys.append((gp_obj, gp_layer))
            for key in remove_keys:
                vb.plot_variable_tracking['plot'][param].pop(key, None)

        node_groups = ['GP Material', 'Layer Select', 'Axis Labels', 'Finalize Curves']
        for group_name in node_groups:
            if bpy.data.node_groups.get(group_name) is None:
                import_anim_nodegroups([group_name])
                bpy.data.node_groups[group_name].use_fake_user = True

        return self.execute(context)

    def execute(self, context):
        gp_obj = bpy.data.objects.get(context.scene.math_anim_gpobjects.gp_object)
        if not gp_obj:
            self.report({'INFO'}, "To take effect on a plot, need to choose the corresponding object.")
            return {'CANCELLED'}
        scene = context.scene
        props = scene.math_anim_plotter_props
        active_layer = gp_obj.data.layers.active
        if not (self.update_tag and not self.update_current_layer):
            gp_layer = None
            if self.use_data_file:
                if len(scene.math_anim_func_datafile.paths)==0:
                    self.report({'WARNING'}, "No data files found, add data files to plot.")
                    return {'CANCELLED'}
            elif self.use_data:
                if not vb._x_vals or not vb._y_vals or not vb._z_vals:
                    self.report({'WARNING'}, "No data to plot, first passing data to vb._x_vals, vb._y_vals, vb._z_vals, then plot.")
                    return {'CANCELLED'}
            if self.update_tag == False: # create new layer for plot
                if props.math_mode == 'POLARFUNCTION' and len(vb.VARS_USED)!=1:
                    self.report({'WARNING'}, f"For polarfunction only 1 variable allowed, but you give {vb.VARS_USED}")
                    return {'CANCELLED'}
                layer_name = "plotting"
                if self.layer_name:
                    layer_name = self.layer_name
                gp_layer = gp_obj.data.layers.new(layer_name)
                #gp_layer['_ma_uid'] = str(uuid.uuid4())
                gp_layer.use_lights = False
                scene.math_anim_gplayers.gp_layer = gp_layer.name
                active_layer = gp_layer
            elif self.update_tag == True and self.update_current_layer == True:
                # update the current layer
                if props.math_mode == 'POLARFUNCTION' and len(vb.VARS_USED)!=1:
                    self.report({'WARNING'}, f"For polarfunction only 1 variable allowed, but you give {vb.VARS_USED}")
                    return {'CANCELLED'}
                gp_layer = gp_obj.data.layers.get(scene.math_anim_gplayers.gp_layer)
                if not gp_layer or gp_layer.name.split('.')[-1] == 'axis':
                    self.report({'INFO'}, "To take effect on a plot, need to choose the corresponding plotting layer.")
                    return {'CANCELLED'}
                else:
                    # Remove old plot
                    for frame in gp_layer.frames:
                        if frame.frame_number != 1:
                            continue
                        gp_layer.frames.remove(frame.frame_number)
                    # also need to remove the old plot variable tracking
                    for param in vb.plot_variable_tracking['plot']:
                        remove_keys = []
                        for carrier, functions in vb.plot_variable_tracking['plot'][param].items():
                            obj, layer = carrier[0], carrier[1]
                            if gp_obj==obj and gp_layer==layer:
                                remove_keys.append((gp_obj, gp_layer))
                                break
                        for key in remove_keys:
                            vb.plot_variable_tracking['plot'][param].pop(key, None)
                active_layer = gp_layer

            if self.use_data_file:
                x_vals, y_vals, z_vals = [], [], []
                for file in scene.math_anim_func_datafile.paths:
                    try:
                        data = np.loadtxt(file.path, delimiter=file.delim)
                        nrow, ncol = data.shape
                        x_vals.append(data[:,0].tolist())
                        if ncol==1:
                            y_vals.append([0.0]*nrow)
                            z_vals.append([0.0]*nrow)
                        elif ncol==2:
                            y_vals.append(data[:,1].tolist())
                            z_vals.append([0.0]*nrow)
                        else:
                            y_vals.append(data[:,1].tolist())
                            z_vals.append(data[:,2].tolist())
                    except:
                        self.report({'WARNING'}, f"Cannot load data from file: {file.path}")
                obj, layer, x_labels, y_labels, z_labels,size_x,size_y,size_z, normalize_factor = self.add_plotting(context, x_vals, y_vals, z_vals, gp_obj, gp_layer)
                if not self.update_tag:
                    bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels,x_size=size_x,y_size=size_y,z_size=size_z)
                else:
                    bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels, update_layer=layer.name,x_size=size_x,y_size=size_y,z_size=size_z)
                return {'FINISHED'}
            elif self.use_data:
                obj, layer, x_labels, y_labels, z_labels,size_x,size_y,size_z, normalize_factor = self.add_plotting(context, vb._x_vals, vb._y_vals, vb._z_vals, gp_obj, gp_layer)
                if not self.update_tag:
                    bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels,x_size=size_x,y_size=size_y,z_size=size_z)
                else:
                    bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels, update_layer=layer.name,x_size=size_x,y_size=size_y,z_size=size_z)
                return {'FINISHED'}
            param_names = set(vb.DYNAMIC_PARAMS.keys())
            update_param = None
            for i, param in enumerate(param_names):
                if param not in vb.plot_variable_tracking['plot']:
                    vb.plot_variable_tracking['plot'][param] = {}
                if props.math_mode == 'PARAFUNCTION':
                    vb.plot_variable_tracking['plot'][param][(gp_obj, gp_layer)] = {
                        'functions': (props.math_mode, props.function_x, props.function_y, props.function_z), 'params': tuple(param_names), 'vars': tuple(vb.VARS_USED),
                        'plot_branch': props.plot_branch, 'branch_axis': props.branch_axis, 'branch_compose': props.branch_compose}
                elif props.math_mode == 'POLARFUNCTION':
                    vb.plot_variable_tracking['plot'][param][(gp_obj, gp_layer)] = {'functions': (props.math_mode, props.polar_function), 'params': tuple(param_names), 'vars': tuple(vb.VARS_USED)}
                elif props.math_mode == 'EFUNCTION':
                    vb.plot_variable_tracking['plot'][param][(gp_obj, gp_layer)] = {'functions': (props.math_mode, props.math_function), 'params': tuple(param_names), 'vars': tuple(vb.VARS_USED)}
                elif props.math_mode == 'IFUNCTION':
                    math_function = ''
                    if '=' not in props.implicit_function:
                        math_function = props.implicit_function
                    else:
                        left, right = props.implicit_function.split('=', 1)
                        math_function = f"({left.strip()}) - ({right.strip()})"
                    vb.plot_variable_tracking['plot'][param][(gp_obj, gp_layer)] = {'functions': (props.math_mode, math_function), 'params': tuple(param_names), 'vars': tuple(vb.VARS_USED)}
                elif props.math_mode == 'ODEFUNCTION':
                    vb.plot_variable_tracking['plot'][param][(gp_obj, gp_layer)] = {
                        'functions': (props.math_mode, props.ode_function_x, props.ode_function_y, props.ode_function_z), 'params': tuple(param_names), 'vars': tuple(vb.VARS_USED),
                        'ode_solver': props.ode_solver, 'ode_dt': getattr(scene, 'math_param_dt'),
                        'ode_t0': getattr(scene, "math_param_t0"), 'ode_t1': getattr(scene, "math_param_t1"),
                        'plot_branch': props.plot_branch, 'branch_axis': props.branch_axis,
                        'branch_compose': props.branch_compose,
                        'ds_solver_type': props.ds_solver_type, 'ds_linear_solver_type': props.ds_linear_solver_type,
                        'ds_matrix_type': props.ds_matrix_type, 'ds_use_dt': props.ds_use_dt,
                        'ds_has_stop': props.ds_has_stop, 'ds_stop_function': props.ds_stop_function,
                        'ds_reset_function': props.ds_reset_function,
                        }
                update_param = param

            for i, var in enumerate(vb.VARS_USED):
                prop_ids = {f"math_var_{var}_min", f"math_var_{var}_max", f"math_var_{var}_resolution"}
                for prop_id in prop_ids:
                    if prop_id not in vb.plot_variable_tracking['plot']:
                        vb.plot_variable_tracking['plot'][prop_id] = {}
                    if props.math_mode == 'PARAFUNCTION':
                        vb.plot_variable_tracking['plot'][prop_id][(gp_obj, gp_layer)] = {
                            'functions': (props.math_mode, props.function_x, props.function_y, props.function_z), 'params': tuple(param_names), 'vars': tuple(vb.VARS_USED),
                            'plot_branch': props.plot_branch, 'branch_axis': props.branch_axis, 'branch_compose': props.branch_compose}
                    elif props.math_mode == 'POLARFUNCTION':
                        vb.plot_variable_tracking['plot'][prop_id][(gp_obj, gp_layer)] = {'functions': (props.math_mode, props.polar_function), 'params': tuple(param_names), 'vars': tuple(vb.VARS_USED)}
                    elif props.math_mode == 'EFUNCTION':
                        vb.plot_variable_tracking['plot'][prop_id][(gp_obj, gp_layer)] = {'functions': (props.math_mode, props.math_function), 'params': tuple(param_names), 'vars': tuple(vb.VARS_USED)}
                    if not update_param:
                        update_param = prop_id
            if update_param:
                vb.plot_variable_tracking['value'][update_param] = (vb.plot_variable_tracking['value'][update_param][0], True)

        # update plots
        for param in vb.plot_variable_tracking['value']:
            if not vb.plot_variable_tracking['value'][param][1]:
                continue
            if param not in vb.plot_variable_tracking['plot']:
                continue
            for carrier, plots in vb.plot_variable_tracking['plot'][param].items():
                gp_obj, gp_layer = carrier[0], carrier[1]
                try:
                    if not gp_obj.name or not gp_layer.name:
                        continue
                except:
                    continue
                for frame in gp_layer.frames:
                    if frame.frame_number != 1:
                        continue
                    gp_layer.frames.remove(frame.frame_number)
                math_mode = plots['functions'][0]
                param_names = plots['params']
                param_values = { p: get_param_value(scene, p) for p in param_names }
                var_names = plots['vars']
                if math_mode == 'PARAFUNCTION':
                    plot_branch = plots['plot_branch']
                    branch_axis = plots['branch_axis']
                    branch_compose = plots['branch_compose']
                    function_x, function_y, function_z = plots['functions'][1], plots['functions'][2], plots['functions'][3]
                    if (not function_x) and (not function_y) and (not function_z):
                        self.report({'WARNING'}, "No function detected. Add one first.")
                        return {'CANCELLED'}

                    # Evaluate functions
                    eval_values = {'x':{'func': function_x, 'values':None},'y':{'func': function_y, 'values':None},'z':{'func': function_z, 'values':None}}
                    if any(sub in f'{function_x} {function_y} {function_z}' for sub in ['sum_', 'nansum_', 'prod_', 'nanprod_']):
                        eval_function_x, _ = parser_sumprod(f'{function_x}')
                        eval_function_y, _ = parser_sumprod(f'{function_y}')
                        eval_function_z, _ = parser_sumprod(f'{function_z}')
                        eval_values = {'x':{'func': eval_function_x, 'values':None},'y':{'func': eval_function_y, 'values':None},'z':{'func': eval_function_z, 'values':None}}
                    for axis in eval_values:
                        if eval_values[axis]['func']:
                            if len(var_names)==1: # one variable
                                t_var = list(var_names)[0]
                                t_min, t_max, t_resolution = getattr(scene, f'math_var_{t_var}_min'), getattr(scene, f'math_var_{t_var}_max'), getattr(scene, f'math_var_{t_var}_resolution')
                                t_values = np.linspace(t_min, t_max, t_resolution)
                                if set(re.findall(r'\b{}\b'.format(t_var), eval_values[axis]['func'])):
                                    eval_values[axis]['values'] = evaluate_expr(eval_values[axis]['func'], {'{}'.format(t_var): t_values, **param_values}).tolist()
                                else:
                                    value = evaluate_expr(eval_values[axis]['func'], {**param_values})
                                    eval_values[axis]['values'] = [value]*len(t_values)
                            else: # u, v as variables
                                vars_used = list(var_names)
                                var_values = [None]*len(var_names)
                                for i, var in enumerate(var_names):
                                    var_min = getattr(scene, f'math_var_{var}_min')
                                    var_max = getattr(scene, f'math_var_{var}_max')
                                    resolution = getattr(scene, f'math_var_{var}_resolution')
                                    var_values[i] = np.linspace(var_min, var_max, resolution)
                                varu_id = vars_used[0]
                                varv_id = vars_used[1]
                                u_values = var_values[0]
                                v_values = var_values[1]
                                u_vals, v_vals = np.meshgrid(u_values, v_values)
                                v_vals2, u_vals2 = np.meshgrid(v_values, u_values)
                                eval_vals, eval_vals2 = None, None
                                if not set(re.findall(r'\b(?:{}|{})\b'.format(re.escape(varu_id), re.escape(varv_id)), eval_values[axis]['func'])):
                                    eval_vals = evaluate_expr(eval_values[axis]['func'], {**param_values})
                                    eval_vals = [[eval_vals]*len(u_vals[0]) for _ in range(len(u_vals))]
                                    eval_vals2 = evaluate_expr(eval_values[axis]['func'], {**param_values})
                                    eval_vals2 = [[eval_vals2]*len(u_vals2[0]) for _ in range(len(u_vals2))]
                                    eval_vals.extend(eval_vals2)
                                else:
                                    eval_vals = evaluate_expr(eval_values[axis]['func'], {f'{varu_id}': u_vals, f'{varv_id}': v_vals, **param_values}).tolist()
                                    eval_vals2 = evaluate_expr(eval_values[axis]['func'], {f'{varu_id}': u_vals2, f'{varv_id}': v_vals2, **param_values}).tolist()
                                    eval_vals.extend(eval_vals2)
                                eval_values[axis]['values'] = eval_vals
                        else:
                            pass
                            #eval_values[axis]['values'] = [0.0]*len(t_values)

                    x_values, y_values, z_values = eval_values['x']['values'], eval_values['y']['values'], eval_values['z']['values']
                    if plot_branch:
                        if len(var_names)==1: # one variable
                            x_values, y_values, z_values = t_values.tolist(), [0.0]*len(y_values), [0.0]*len(z_values)
                            if branch_axis == 'x':
                                y_values = eval_values['x']['values']
                            elif branch_axis == 'y':
                                y_values = eval_values['y']['values']
                            elif branch_axis == 'z':
                                y_values = eval_values['z']['values']
                            elif branch_axis == 'compose':
                                y_values = evaluate_expr(branch_compose, {'x': eval_values['x']['values'],'y': eval_values['y']['values'], 'z': eval_values['z']['values']}).tolist()
                        elif len(var_names)==2:
                            x_values, y_values, z_values = [i.tolist() for i in u_vals] + [i.tolist() for i in u_vals2], [i.tolist() for i in v_vals] + [i.tolist() for i in v_vals2], [0.0]*len(z_values)
                            if branch_axis == 'x':
                                z_values = eval_values['x']['values']
                            elif branch_axis == 'y':
                                z_values = eval_values['y']['values']
                            elif branch_axis == 'z':
                                z_values = eval_values['z']['values']
                            elif branch_axis == 'compose':
                                z_values = evaluate_expr(branch_compose, {'x': eval_values['x']['values'],'y': eval_values['y']['values'], 'z': eval_values['z']['values']}).tolist()
                    obj, layer, x_labels, y_labels, z_labels, size_x, size_y, size_z, normalize_factor = self.add_plotting(context, x_values, y_values, z_values, gp_obj, gp_layer)
                    if not self.update_tag:
                        bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels,x_size=size_x,y_size=size_y,z_size=size_z)
                    else:
                        bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels, update_layer=layer.name,x_size=size_x,y_size=size_y,z_size=size_z)
                elif math_mode == 'POLARFUNCTION':
                    polar_function = plots['functions'][1]
                    if not polar_function:
                        self.report({'WARNING'}, "No function detected. Add one first.")
                        return {'CANCELLED'}
                    if any(sub in polar_function for sub in ['sum_', 'nansum_', 'prod_', 'nanprod_']):
                        polar_function, param_function = parser_sumprod(polar_function)
                    var = list(var_names)[0]
                    var_min = getattr(scene, f'math_var_{var}_min')
                    var_max = getattr(scene, f'math_var_{var}_max')
                    resolution = getattr(scene, f'math_var_{var}_resolution')
                    theta_values = np.linspace(var_min, var_max, resolution)
                    if set(re.findall(r'\b{}\b'.format(var), polar_function)):
                        r_values = evaluate_expr(polar_function, {f'{var}': theta_values, **param_values})
                    else:
                        r_values = [evaluate_expr(polar_function, {**param_values}) for _ in theta_values]
                    x_values = r_values*np.cos(theta_values)
                    y_values = r_values*np.sin(theta_values)
                    x_values = x_values.tolist()
                    y_values = y_values.tolist()
                    z_values = [0.0]*len(x_values)
                    obj, layer, x_labels, y_labels, z_labels,size_x,size_y,size_z, normalize_factor = self.add_plotting(context, x_values, y_values, z_values, gp_obj, gp_layer, math_mode)
                    if not self.update_tag:
                        bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels,x_size=size_x,y_size=size_y,z_size=size_z, math_mode=math_mode)
                    else:
                        bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels, update_layer=layer.name,x_size=size_x,y_size=size_y,z_size=size_z, math_mode=math_mode)
                elif math_mode == 'EFUNCTION':
                    math_function = plots['functions'][1]
                    if not math_function:
                        self.report({'WARNING'}, "No function detected. Add one first.")
                        return {'CANCELLED'}
                    if any(sub in math_function for sub in ['sum_', 'nansum_', 'prod_', 'nanprod_']):
                        math_function, param_function = parser_sumprod(math_function)
                    if props.self_iteration:
                        iter_init = getattr(scene, 'math_param_iter_init')
                        n_iter = getattr(scene, 'math_param_n_iter')
                        aeval = Interpreter()
                        is_complex = np.iscomplexobj(aeval(iter_init))
                        iter_values = [aeval(iter_init)]
                        use_param_values = {k:aeval(v) for k,v in param_values.items() if k!='iter_init' and k!='n_iter'}
                        for _ in range(n_iter):
                            value = evaluate_expr(math_function, {f'{var_names[0]}': iter_values[-1], **use_param_values})
                            iter_values.append(value)
                        x_values = list(range(n_iter+1))
                        y_values = iter_values
                        if is_complex:
                            x_values = [np.real(v) for v in iter_values]
                            y_values = [np.imag(v) for v in iter_values]
                        z_values = [0.0]*len(x_values)
                        obj, layer, x_labels, y_labels, z_labels,size_x,size_y,size_z, normalize_factor = self.add_plotting(context, x_values, y_values, z_values, gp_obj, gp_layer)
                        if not self.update_tag:
                            bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels,x_size=size_x,y_size=size_y,z_size=size_z)
                        else:
                            bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels, update_layer=layer.name,x_size=size_x,y_size=size_y,z_size=size_z)
                    else:
                        vars_used = list(var_names)
                        var_values = [None]*len(var_names)
                        for i, var in enumerate(var_names):
                            # Generate parameter space
                            var_min = getattr(scene, f'math_var_{var}_min')
                            var_max = getattr(scene, f'math_var_{var}_max')
                            resolution = getattr(scene, f'math_var_{var}_resolution')
                            var_values[i] = np.linspace(var_min, var_max, resolution)
                        if len(var_names) == 1:
                            var_id = vars_used[0]
                            x_values = var_values[0]
                            if set(re.findall(r'\b{}\b'.format(var_id), math_function)):
                                y_values = evaluate_expr(math_function, {f'{var_id}': x_values, **param_values}).tolist()
                                x_values = x_values.tolist()
                                z_values = [0.0]*len(x_values)
                            else:
                                y_values = x_values.tolist()
                                value = evaluate_expr(math_function, {**param_values})
                                x_values = [value]*len(x_values)
                                z_values = [0.0]*len(x_values)
                            obj, layer, x_labels, y_labels, z_labels,size_x,size_y,size_z, normalize_factor = self.add_plotting(context, x_values, y_values, z_values, gp_obj, gp_layer)
                            if not self.update_tag:
                                bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels,x_size=size_x,y_size=size_y,z_size=size_z)
                            else:
                                bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels, update_layer=layer.name,x_size=size_x,y_size=size_y,z_size=size_z)
                        elif len(var_names) == 2:
                            varx_id = vars_used[0]
                            vary_id = vars_used[1]
                            x_values = var_values[0]
                            y_values = var_values[1]
                            x_vals, y_vals = np.meshgrid(x_values, y_values)
                            y_vals2, x_vals2 = np.meshgrid(y_values, x_values)
                            z_vals, z_vals2 = None, None
                            if set(re.findall(r'\b(?:{}|{})\b'.format(re.escape(varx_id), re.escape(vary_id)), math_function)):
                                z_vals = evaluate_expr(math_function, {f'{varx_id}': x_vals, f'{vary_id}': y_vals, **param_values}).tolist()
                                z_vals2 = evaluate_expr(math_function, {f'{varx_id}': x_vals2, f'{vary_id}': y_vals2, **param_values}).tolist()
                                z_vals.extend(z_vals2)
                            else:
                                z_vals = evaluate_expr(math_function, {**param_values})
                                z_vals = [[z_vals]*len(x_vals[0]) for _ in range(len(x_vals))]
                                z_vals2 = evaluate_expr(math_function, {**param_values})
                                z_vals2 = [[z_vals2]*len(x_vals2[0]) for _ in range(len(x_vals2))]
                                z_vals.extend(z_vals2)
                            x_vals = x_vals.tolist()
                            y_vals = y_vals.tolist()
                            x_vals.extend(x_vals2.tolist())
                            y_vals.extend(y_vals2.tolist())
                            obj, layer, x_labels, y_labels, z_labels,size_x,size_y,size_z, normalize_factor = self.add_plotting(context, x_vals, y_vals, z_vals, gp_obj, gp_layer)
                            if not self.update_tag:
                                bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels,x_size=size_x,y_size=size_y,z_size=size_z)
                            else:
                                bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels, update_layer=layer.name,x_size=size_x,y_size=size_y,z_size=size_z)
                elif math_mode == 'ODEFUNCTION':
                    plot_branch = plots['plot_branch']
                    branch_axis = plots['branch_axis']
                    branch_compose = plots['branch_compose']
                    ode_solver = plots['ode_solver']
                    ode_t0 = plots['ode_t0']
                    ode_t1 = plots['ode_t1']
                    ode_dt = plots['ode_dt']
                    ds_use_dt = plots['ds_use_dt']
                    if not props.plot_ctl:
                        obj = bpy.data.objects.get(context.scene.math_anim_gpobjects.gp_object)
                        if obj is gp_obj:
                            layer = obj.data.layers.get(context.scene.math_anim_gplayers.gp_layer)
                            if layer == gp_layer:
                                ode_t0 = getattr(scene, 'math_param_t0')
                                ode_t1 = getattr(scene, 'math_param_t1')
                                ode_dt = getattr(scene, 'math_param_dt')
                                ds_use_dt = props.ds_use_dt
                    var_names = [var_name for var_name in sorted(var_names) if var_name != 't']
                    exprs = [(var, plots['functions'][i+1])  for i, var in enumerate(var_names)]
                    y0 = {var: getattr(scene, f'math_param_{var}0') for var in var_names }
                    t_span = (ode_t0, ode_t1)
                    if ode_solver == 'RK45':
                        ts, ys = solve_expr_ode_adaptive(exprs, param_values, y0, t_span, ode_dt, tol=1e-3, dt_min=1e-3, dt_max=0.1, safety_factor=0.84, max_growth_factor=2.0)
                    elif ode_solver == 'RK4':
                        ts, ys = solve_expr_ode_rk4(exprs, param_values, y0, t_span, ode_dt)
                    elif ode_solver == 'DIFFSOL':
                        ds_has_stop = plots['ds_has_stop']
                        ds_stop_function = plots['ds_stop_function']
                        ds_matrix_type = plots['ds_matrix_type']
                        ds_linear_solver_type = plots['ds_linear_solver_type']
                        ds_solver_type = plots['ds_solver_type']
                        ds_reset_function = plots['ds_reset_function']
                        remove_names = ['t0', 't1', 'dt'] + [f'{var}0' for var in var_names]
                        for name in remove_names:
                            param_values.pop(name, None)
                        if ds_has_stop and ds_stop_function:
                            ode_code = f"""
                            {' '.join(f"{name} {{ {value} }}" for name, value in param_values.items()) }
                            u_i {{
                                {' '.join(f"{name} = {value},"  for name, value in y0.items())}
                            }}
                            F_i {{
                                {' '.join(f"{expr}," for var, expr in exprs)}
                            }}
                            stop_i {{
                                {ds_stop_function}
                            }}
                            reset_i {{
                                {ds_reset_function}
                            }}
                            """
                            if "g_i[N]" in f"{props.ode_function_x} {props.ode_function_y} {props.ode_function_z}":
                                ode_code = f"""
                                {' '.join(f"{name} {{ {value} }}" for name, value in param_values.items()) }
                                u_i {{
                                    {' '.join(f"{name} = {value},"  for name, value in y0.items())}
                                }}
                                g_i {{
                                    {props.ds_hybrid_model}
                                }}
                                F_i {{
                                    {' '.join(f"{expr}," for var, expr in exprs)}
                                }}
                                stop_i {{
                                    {ds_stop_function}
                                }}
                                reset_i {{
                                    {ds_reset_function}
                                }}
                                """
                        else:
                            ode_code = f"""
                            {' '.join(f"{name} {{ {value} }}" for name, value in param_values.items()) }
                            u_i {{
                                {' '.join(f"{name} = {value},"  for name, value in y0.items())}
                            }}
                            F_i {{
                                {' '.join(f"{expr}," for var, expr in exprs)}
                            }}
                            """
                        #print(f"ODE code:\n{ode_code}")
                        ode = ds.Ode(code=ode_code, matrix_type=ds.MatrixType.from_str(ds_matrix_type), linear_solver=ds.LinearSolverType.from_str(ds_linear_solver_type), ode_solver=ds.OdeSolverType.from_str(ds_solver_type))
                        params = np.array([])
                        if ds_use_dt:
                            t_eval = np.arange(t_span[0], t_span[1]+1e-12, ode_dt)
                            solution = ode.solve_dense(params, t_eval)
                        else:
                            solution = ode.solve(params, t_span[-1])

                        ts = solution.ts.T
                        ys = solution.ys.T

                    if ys.shape[1] == 1:
                        x_vals = ts.tolist()
                        y_vals = ys[:,0].tolist()
                        z_vals = [0.0]*len(x_vals)
                    elif ys.shape[1] == 2:
                        x_vals = ys[:,0].tolist()
                        y_vals = ys[:,1].tolist()
                        z_vals = [0.0]*len(x_vals)
                    else:
                        x_vals, y_vals, z_vals = ys.T

                    if plot_branch:
                        x_vals = ts.tolist()
                        y_vals = [0.0]*len(x_vals)
                        z_vals = [0.0]*len(x_vals)
                        if branch_axis == 'x':
                            y_vals = ys[:,0].tolist()
                        elif branch_axis == 'y':
                            if ys.shape[1] > 1:
                                y_vals = ys[:,1].tolist()
                        elif branch_axis == 'z':
                            if ys.shape[1] > 2:
                                y_vals = ys[:,2].tolist()
                        elif branch_axis == 'compose':
                            y_vals = evaluate_expr(branch_compose, {'x': ys[:,0], 'y': ys[:,1] if ys.shape[1]>1 else 0, 'z': ys[:,2] if ys.shape[1]>2 else 0}).tolist()

                    obj, layer, x_labels, y_labels, z_labels,size_x,size_y,size_z, normalize_factor = self.add_plotting(context, x_vals, y_vals, z_vals, gp_obj, gp_layer)
                    if not self.update_tag:
                        bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels,x_size=size_x,y_size=size_y,z_size=size_z)
                    else:
                        bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels, update_layer=layer.name,x_size=size_x,y_size=size_y,z_size=size_z)
                elif math_mode == 'IFUNCTION':
                    expr = plots['functions'][1]
                    if not expr:
                        self.report({'WARNING'}, "No function detected. Add one first.")
                        return {'CANCELLED'}
                    var_names = [var_name for var_name in sorted(var_names)]
                    implicit_func = make_implicit_func(expr, param_values, var_names)
                    step, n_steps = getattr(scene, 'math_param_step'), getattr(scene, 'math_param_n_steps')
                    if len(var_names) < 2 or len(var_names) > 3:
                        self.report({'WARNING'}, f"For implicit function, only 2 or 3 variables are allowed, but you give {var_names}")
                        return {'CANCELLED'}
                    if len(var_names) == 2:
                        x_vals, y_vals = auto_solve_implicit(implicit_func, dim=len(var_names), domain=((getattr(scene, f'math_var_{var_names[0]}_min'), getattr(scene, f'math_var_{var_names[0]}_max'), getattr(scene, f'math_var_{var_names[0]}_resolution')), (getattr(scene, f'math_var_{var_names[1]}_min'), getattr(scene, f'math_var_{var_names[1]}_max'),getattr(scene, f'math_var_{var_names[1]}_resolution'))), step=step, n_steps=n_steps)
                        z_vals = [0.0]*len(x_vals)
                    elif len(var_names) == 3:
                        x_vals, y_vals, z_vals = auto_solve_implicit(implicit_func, dim=len(var_names), domain=((getattr(scene, f'math_var_{var_names[0]}_min'), getattr(scene, f'math_var_{var_names[0]}_max'), getattr(scene, f'math_var_{var_names[0]}_resolution')), (getattr(scene, f'math_var_{var_names[1]}_min'), getattr(scene, f'math_var_{var_names[1]}_max'),getattr(scene, f'math_var_{var_names[1]}_resolution')), (getattr(scene, f'math_var_{var_names[2]}_min'), getattr(scene, f'math_var_{var_names[2]}_max'), getattr(scene, f'math_var_{var_names[2]}_resolution'))), step=step, n_steps=n_steps)
                    obj, layer, x_labels, y_labels, z_labels,size_x,size_y,size_z, normalize_factor = self.add_plotting(context, x_vals, y_vals, z_vals, gp_obj, gp_layer)
                    if not self.update_tag:
                        bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels,x_size=size_x,y_size=size_y,z_size=size_z)
                    else:
                        bpy.ops.math_anim.update_morph_objects(x_labels=x_labels,y_labels=y_labels,z_labels=z_labels, update_layer=layer.name,x_size=size_x,y_size=size_y,z_size=size_z)
                else:
                    self.report({'INFO'}, f"Unknown math mode {math_mode}.")
            if f'math_var_' in param:
                vb.plot_variable_tracking['value'][param] = (getattr(scene, param), False)
            else:
                vb.plot_variable_tracking['value'][param] = (getattr(scene, f'math_param_{param}'), False)

        context.scene.math_anim_gplayers.gp_layer = active_layer.name
        # at the end, clean vars and params that are not used anymore
        not_used_params = []
        for param in vb.plot_variable_tracking['plot'].keys():
            if f'math_var_' in param:
                var = (m := re.match(r"^math_var_(.+)_(min|max|resolution)$", param)) and m.group(1)
                if not vb.plot_variable_tracking['plot'][param] and (var not in vb.VARS_USED):
                    not_used_params.append(param)
            else:
                if not vb.plot_variable_tracking['plot'][param] and (param not in vb.DYNAMIC_PARAMS):
                    not_used_params.append(param)
        for param in not_used_params:
            if param in vb.plot_variable_tracking['vars']:
                vb.plot_variable_tracking['vars'].remove(param)
            if param in vb.plot_variable_tracking['params']:
                vb.plot_variable_tracking['params'].remove(param)
            if param in vb.plot_variable_tracking['value'].keys():
                vb.plot_variable_tracking['value'].pop(param, None)
            if f'math_var_' in param:
                if hasattr(scene, param):
                    delattr(bpy.types.Scene, param)
            else:
                if hasattr(scene, f'math_param_{param}'):
                    delattr(bpy.types.Scene, f'math_param_{param}')
        return {'FINISHED'}

    # for axis, 0,1,2 for x,y,z,  for axis components 0,1,2 for axis line,head,ticks, curve_type mainly for bezier
    def add_strokes(self, gp_layer, x, y, z, axis=-1, axis_comps=-1, curve_type='POLY'):
        gp_frame = None
        if len(gp_layer.frames) == 0:
            gp_frame = gp_layer.frames.new(1)
        else:
            gp_frame = gp_layer.frames[0]

        # Get current points
        num_points = gp_frame.drawing.attributes.domain_size('POINT')
        positions = gp_frame.drawing.attributes['position']
        # Create new positions array with correct size
        new_size = num_points + len(x)
        positions_data = np.zeros(new_size * 3, dtype=np.float32)
        # Get existing positions if any
        if num_points > 0:
            positions.data.foreach_get('vector', positions_data[:num_points*3])
        # Add new positions
        if curve_type == 'BEZIER':
            new_positions = np.array([[x[i][0], y[i][0], z[i][0]] for i in range(len(x))], dtype=np.float32).flatten()
            positions_data[num_points*3:] = new_positions
            # left/right Handles
            left_handle = gp_frame.drawing.attributes.get('handle_left')
            if not left_handle:
                left_handle = gp_frame.drawing.attributes.new('handle_left', 'FLOAT_VECTOR', 'POINT')
            left_handle_data = np.zeros(new_size*3, dtype=np.float32)
            if num_points > 0:
                left_handle.data.foreach_get('vector', left_handle_data[:num_points*3])
            new_positions = np.array([[x[i][1], y[i][1], z[i][1]] for i in range(len(x))], dtype=np.float32).flatten()
            left_handle_data[num_points*3:] = new_positions

            right_handle = gp_frame.drawing.attributes.get('handle_right')
            if not right_handle:
                right_handle = gp_frame.drawing.attributes.new('handle_right', 'FLOAT_VECTOR', 'POINT')
            right_handle_data = np.zeros(new_size*3, dtype=np.float32)
            if num_points > 0:
                right_handle.data.foreach_get('vector', right_handle_data[:num_points*3])
            new_positions = np.array([[x[i][2], y[i][2], z[i][2]] for i in range(len(x))], dtype=np.float32).flatten()
            right_handle_data[num_points*3:] = new_positions
        else:
            new_positions = np.array([[x[i], y[i], z[i]] for i in range(len(x))], dtype=np.float32).flatten()
            positions_data[num_points*3:] = new_positions

        # Handle radii
        radii = gp_frame.drawing.attributes.get('radius')
        if not radii:
            radii = gp_frame.drawing.attributes.new('radius', 'FLOAT', 'POINT')
        radii_data = np.zeros(new_size, dtype=np.float32)
        if num_points > 0:
            radii.data.foreach_get('value', radii_data[:num_points])
        radii_data[num_points:] = 0.005
        if axis_comps == 1:
            radii_data[num_points:] = 0.008
        if axis_comps == 2:
            radii_data[num_points:] = 0.003
        if axis_comps == 4:
            radii_data[num_points:] = 0.003

        # Adding axis indication
        if axis >= 0:
            axis_type = gp_frame.drawing.attributes.get('axis')
            if not axis_type:
                axis_type = gp_frame.drawing.attributes.new('axis', 'INT', 'CURVE')
            type_size = gp_frame.drawing.attributes.domain_size('CURVE')
            type_data1 = np.zeros(type_size+1, dtype=np.int32)
            if type_size > 0:
                axis_type.data.foreach_get('value', type_data1[:type_size])
            type_data1[type_size:] = axis

        # Adding axis_comps for axis
        if axis_comps >= 0:
            axis_subtype = gp_frame.drawing.attributes.get('axis_subtype')
            if not axis_subtype:
                axis_subtype = gp_frame.drawing.attributes.new('axis_subtype', 'INT', 'CURVE')
            type_size = gp_frame.drawing.attributes.domain_size('CURVE')
            type_data2 = np.zeros(type_size+1, dtype=np.int32)
            if type_size > 0:
                axis_subtype.data.foreach_get('value', type_data2[:type_size])
            type_data2[type_size:] = axis_comps

        # Add new strokes and update data
        gp_frame.drawing.add_strokes(sizes=[len(x)])
        if curve_type == 'BEZIER':
            stroke_index = len(gp_frame.drawing.strokes)-1
            gp_frame.drawing.set_types(type=curve_type, indices=[stroke_index])
            gp_frame.drawing.strokes[stroke_index].cyclic = True
            left_handle = gp_frame.drawing.attributes['handle_left']
            left_handle.data.foreach_set('vector', left_handle_data)
            right_handle = gp_frame.drawing.attributes['handle_right']
            right_handle.data.foreach_set('vector', right_handle_data)

        # must reclaim the attributes when the drawing changes, like, adding or deleting points
        positions = gp_frame.drawing.attributes['position']
        radii = gp_frame.drawing.attributes['radius']
        positions.data.foreach_set('vector', positions_data)
        radii.data.foreach_set('value', radii_data)
        if axis >= 0:
            axis_type = gp_frame.drawing.attributes.get('axis')
            axis_type.data.foreach_set('value', type_data1)
        if axis_comps >= 0:
            axis_subtype = gp_frame.drawing.attributes.get('axis_subtype')
            axis_subtype.data.foreach_set('value', type_data2)

    def add_plotting(self, context, x, y, z, gp_obj, gp_layer, math_mode=None):
        if not gp_obj or not gp_layer:
            return None
        x_labels, y_labels, z_labels = '', '', ''
        label_size = [0.4, 0.4, 0.4]
        normalize_factor = [1.0, 1.0, 1.0]
        # plotting
        flat_x, flat_y, flat_z = None, None, None
        if isinstance(x[0], list):
            for i in range(len(x)):
                points_x, points_y, points_z = x[i], y[i], z[i]
                self.add_strokes(gp_layer, points_x, points_y, points_z)
                if i==0:
                    flat_x = x[i]
                    flat_y = y[i]
                    flat_z = z[i]
                else:
                    flat_x.extend(x[i])
                    flat_y.extend(y[i])
                    flat_z.extend(z[i])
        else:
            self.add_strokes(gp_layer, x, y, z)
            flat_x = x
            flat_y = y
            flat_z = z

        # axis, adding attribute to spline, 0 for axis, 1 for axis head, 2 for ticks
        axis_layer = gp_obj.data.layers.get(f'{gp_layer.name}.axis')
        if axis_layer:
            for frame in axis_layer.frames:
                if frame.frame_number != 1:
                    continue
                axis_layer.frames.remove(frame.frame_number)
        else:
            axis_layer = gp_obj.data.layers.new(f'{gp_layer.name}.axis')
            axis_layer.use_lights = False
        polar_rings = [0.0]
        for i, axis in enumerate([flat_x, flat_y, flat_z]):
            axis_min, axis_max = min(axis), max(axis)
            if axis_min > 0.0:
                axis = np.insert(axis, 0, 0.0)
            if axis_max < 0.0:
                axis = np.append(axis, 0.0)
            n_ticks = recommended_tick_count(axis)
            tick_points = pretty_axis_ticks(axis, n_ticks)
            if len(tick_points) < 2:
                continue
            tick_gap = tick_points[1] - tick_points[0]
            label_size[i] = tick_gap
            normalize_factor[i] = max(axis) - min(axis)
            if math_mode == 'POLARFUNCTION':
                unique_abs_list = sorted(set(abs(value) for value in tick_points if abs(value)>0))
                if polar_rings[-1] < unique_abs_list[-1]:
                    polar_rings = unique_abs_list
                continue
            extension = max(0.25, tick_gap/4.0)
            # main axis lines
            point_pos = {0:[0.0, 0.0], 1:[0.0, 0.0], 2:[0.0, 0.0]}
            point_pos[i] = [tick_points[0]-extension, tick_points[-1]+extension]
            normalize_factor[i] = point_pos[i][1] - point_pos[i][0]
            self.add_strokes(axis_layer, point_pos[0], point_pos[1], point_pos[2], i, 0)
            # main axis arrow head
            length, angle = 0.2, 22.5
            x2 = tick_points[-1]+extension
            x1 = x2 - length*math.cos(math.radians(angle))
            x3 = x2 - length*math.cos(math.radians(angle))
            y1 = length*math.sin(math.radians(angle))
            y3 = -1.0*length*math.sin(math.radians(angle))
            if i ==0:
                point_pos = {0:[x1, x2, x3], 1:[y1, 0.0, y3], 2:[0.0, 0.0, 0.0]}
            elif i==1:
                point_pos = {0:[y1, 0.0, y3], 1:[x1, x2, x3], 2:[0.0, 0.0, 0.0]}
            elif i==2:
                point_pos = {0:[y1, 0.0, y3], 1:[0.0, 0.0, 0.0], 2:[x1, x2, x3]}
            self.add_strokes(axis_layer, point_pos[0], point_pos[1], point_pos[2], i, 1)
            # ticks
            length = 0.1*tick_gap
            for tick in tick_points:
                point_pos = {0:[0.0, 0.0], 1:[0.0, 0.0], 2:[0.0, 0.0]}
                point_pos[i] = [tick, tick]
                if i==0:
                    point_pos[1] = [0.0, length]
                    x_labels = f'{tick}' if not x_labels else f'{x_labels}+|+{tick}'
                else:
                    point_pos[0] = [0.0, length]
                    if i==1:
                        y_labels = f'{tick}' if not y_labels else f'{y_labels}+|+{tick}'
                    else:
                        z_labels = f'{tick}' if not z_labels else f'{z_labels}+|+{tick}'
                self.add_strokes(axis_layer, point_pos[0], point_pos[1], point_pos[2], i, 2)

        if math_mode == 'POLARFUNCTION':
            label_size = [polar_rings[-1]-polar_rings[-2] if len(polar_rings)>1 else polar_rings[-1] for _ in range(3)]
            line_x, line_y, line_z = [0], [0], [0]
            # rings and strips
            for ring_idx, ring in enumerate(polar_rings):
                control_points, left_handles, right_handles = calculate_bezier_circle(ring,8)
                line_x.append(ring)
                line_y.append(0)
                line_z.append(0)
                ring_x, ring_y, ring_z = [], [], []
                for point_idx, point in enumerate(control_points):
                    ring_x.append((point[0], left_handles[point_idx][0], right_handles[point_idx][0]))
                    ring_y.append((point[1], left_handles[point_idx][1], right_handles[point_idx][1]))
                    ring_z.append((point[2], left_handles[point_idx][2], right_handles[point_idx][2]))
                # rings
                if ring_idx < len(polar_rings)-1:
                    self.add_strokes(axis_layer, ring_x, ring_y, ring_z, 1, 4, 'BEZIER')
                else:
                    self.add_strokes(axis_layer, ring_x, ring_y, ring_z, 1, 0, 'BEZIER')
                    for point_idx, point in enumerate(control_points):
                        y_labels = '0' if point_idx == 0 else f'{y_labels}+|+{point_idx}pi/{len(control_points)}'
                        x, y, z = [0.0, point[0]], [0.0, point[1]], [0.0, point[2]]
                        # trips
                        if point_idx == 0:
                            self.add_strokes(axis_layer, x, y, z, 0, 0)
                        else:
                            self.add_strokes(axis_layer, x, y, z, 0, 4)
                        # ring ticks
                        x, y, z = [point[0], point[0]], [point[1], point[1]], [point[2], point[2]]
                        self.add_strokes(axis_layer, x, y, z, 1, 2)
            # strip ticks
            for i, x_i in enumerate(line_x):
                x_labels = f'{x_i}' if i == 0 else f'{x_labels}+|+{x_i}'
                x, y, z = [x_i, x_i], [0.0, 0.0], [0.0, 0.0]
                self.add_strokes(axis_layer, x, y, z, 0, 2)

        bpy.data.grease_pencils[gp_obj.data.name].stroke_depth_order = '3D'
        resize = 0.25
        return gp_obj, gp_layer, x_labels, y_labels, z_labels, label_size[0]*resize, label_size[1]*resize, label_size[2]*resize, normalize_factor

class MATH_OT_PATH_FuncDataAddPath(bpy.types.Operator):
    """Add a new path"""
    bl_idname = "math_anim.funcdata_addpath"
    bl_label = "Add Function Data Path"
    bl_description = "Add Function's Data Path for plotting"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        funcdata_paths = context.scene.math_anim_func_datafile
        new_item = funcdata_paths.paths.add()
        new_item.path = self.filepath
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class MATH_OT_PATH_FuncDataRemovePath(bpy.types.Operator):
    """Remove selected paths"""
    bl_idname = "math_anim.funcdata_removepath"
    bl_label = "Remove Selected Items"
    bl_description = "Remove Selected Items"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        funcdata_paths = context.scene.math_anim_func_datafile
        # Get all selected paths
        selected_items = [i for i, item in enumerate(funcdata_paths.paths) if item.selected]
        # Remove from highest index to lowest to avoid shifting issues
        for index in sorted(selected_items, reverse=True):
            funcdata_paths.paths.remove(index)

        return {'FINISHED'}

class MATH_OT_AddBloom(bpy.types.Operator):
    bl_idname = "math_anim.add_bloom"
    bl_label = "Add bloom effect"
    bl_description = "Add bloom effect through composite nodes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        context.view_layer.use_pass_z = True
        context.view_layer.use_pass_grease_pencil = True
        context.scene.grease_pencil_settings.aa_samples = 6
        context.scene.camera.data.clip_end = 10000
        if not context.scene.compositing_node_group:
            scene_nodetree = bpy.data.node_groups.new("CompositTree", "CompositorNodeTree")
            context.scene.compositing_node_group = scene_nodetree
            render_layers = scene_nodetree.nodes.new("CompositorNodeRLayers")
            glare = scene_nodetree.nodes.new("CompositorNodeGlare")
            glare.inputs['Type'].default_value = 'Bloom'
            output = scene_nodetree.nodes.new(type='NodeGroupOutput')
            render_layers.location[0] -= 3.0 * render_layers.width
            glare.location[0] -= 1.5 * glare.width
            scene_nodetree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
            scene_nodetree.links.new(glare.outputs[0], output.inputs[0])
            scene_nodetree.links.new(render_layers.outputs[0], glare.inputs[0])
        else:
            self.report({'INFO'}, "Compositing node group already exists.")
        if isinstance(context.space_data, bpy.types.SpaceView3D):
            context.space_data.shading.type = 'RENDERED'
            context.space_data.shading.use_compositor = 'ALWAYS'
        else:
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.spaces.active.shading.type = 'RENDERED'
                    area.spaces.active.shading.use_compositor = 'ALWAYS'
        return {'FINISHED'}

class MATH_OT_AddBGGrid(bpy.types.Operator):
    bl_idname = "math_anim.add_bg_grid"
    bl_label = "Add Background Grid"
    bl_description = "Add a background grid to mimic Viewport 3D sense of space"
    bl_options = {'REGISTER', 'UNDO'}

    def invoke(self, context, event):
        node_groups = ['Background Grid', 'Layer Select']
        for group_name in node_groups:
            if bpy.data.node_groups.get(group_name) is None:
                import_anim_nodegroups([group_name])
                bpy.data.node_groups[group_name].use_fake_user = True
        return self.execute(context)

    def execute(self, context):
        if vb.bg_grid_holder:
            self.report({'INFO'}, "Background grid already exists.")
            return {'CANCELLED'}
        bpy.ops.math_anim.add_gp_obj(obj_name="Plotter", geomd_category='PLOTTER')
        gp_obj = context.active_object
        layer_name = 'bg_grid'
        bpy.data.grease_pencils[gp_obj.data.name].layers['Layer'].name = layer_name
        node_group = gp_obj.modifiers['plotterGeoNodes'].node_group
        bggrid_node, _, _ = create_node(node_group, "GeometryNodeGroup", -500, -100, 0, 0)
        bggrid_node.node_tree = bpy.data.node_groups['Background Grid']
        bggrid_node.name = bggrid_node.node_tree.name
        node_group.nodes['Layer'].name = layer_name
        node_group.nodes[layer_name].label = layer_name
        node_group.nodes[layer_name].inputs['Layer Name'].default_value = layer_name
        node_group.nodes[layer_name].inputs['Color Strength'].default_value = 1.0
        node_group.links.new(node_group.nodes['Group Input'].outputs['Geometry'], bggrid_node.inputs['Geometry'])
        node_group.links.new(bggrid_node.outputs['Geometry'], node_group.nodes['GP Material'].inputs['Geometry'])
        vb.bg_grid_holder[bggrid_node.id_data.name] = bggrid_node.name
        bpy.ops.math_anim.update_morph_objects()
        return {'FINISHED'}

class MATH_OT_DelBGGrid(bpy.types.Operator):
    bl_idname = "math_anim.del_bg_grid"
    bl_label = "Remove Background Grid"
    bl_description = "Remove a background grid"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for group_name, node_name in  vb.bg_grid_holder.items():
            node_group = bpy.data.node_groups.get(group_name)
            if node_group:
                node = node_group.nodes.get(node_name)
                if node:
                    node_group.nodes.remove(node)
                    node_group.links.new(node_group.nodes['Group Input'].outputs['Geometry'], node_group.nodes['GP Material'].inputs['Geometry'])
                    vb.bg_grid_holder.pop(group_name, None)
                    #bpy.ops.math_anim.update_morph_objects()
                    return {'FINISHED'}
        vb.bg_grid_holder.clear()
        return {'CANCELLED'}

classes = (
    MATH_OT_CreatePlotter,
    MATH_OT_PATH_FuncDataAddPath,
    MATH_OT_PATH_FuncDataRemovePath,
    MATH_OT_AddBloom,
    MATH_OT_AddBGGrid,
    MATH_OT_DelBGGrid,
)
register, unregister = bpy.utils.register_classes_factory(classes)
