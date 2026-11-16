# for ODE and implicit equation solving
import numpy as np
import numexpr as ne
from .utils import ErrorMessageBox

# ODE function builder (numexpr optimized)
def make_ode_derivs(exprs, params, variables):
    """
    Build a fast ODE derivative function using numexpr.
    """
    var_count = len(variables)
    def derivs(t, state):
        # Create a single local dict shared for all expressions
        local_vars = {**params, 't': t}
        for i in range(var_count):
            local_vars[variables[i]] = state[i]
        # Evaluate all expressions
        return np.array([ne.evaluate(expr, local_dict=local_vars) for expr in exprs], dtype=float)
    return derivs


# Optimized adaptive solver (Runge-Kutta 5(4) Fehlberg)
def solve_ode_adaptive(derivs, y0, t_span, dt=0.02, tol=1e-4, dt_min=1e-4, dt_max=0.1):
    t0, t1 = t_span
    t = t0
    y = np.array(y0, dtype=float)

    t_vals = [t]
    y_vals = [y.copy()]

    n = len(y)
    k = np.zeros((6, n))
    y4 = np.zeros_like(y)
    y5 = np.zeros_like(y)

    while t < t1:
        if t + dt > t1:
            dt = t1 - t

        k[0] = derivs(t, y)
        k[1] = derivs(t + dt/4, y + dt/4 * k[0])
        k[2] = derivs(t + 3*dt/8, y + dt*(3*k[0]/32 + 9*k[1]/32))
        k[3] = derivs(t + 12*dt/13, y + dt*(1932*k[0]/2197 - 7200*k[1]/2197 + 7296*k[2]/2197))
        k[4] = derivs(t + dt, y + dt*(439*k[0]/216 - 8*k[1] + 3680*k[2]/513 - 845*k[3]/4104))
        k[5] = derivs(t + dt/2, y + dt*(-8*k[0]/27 + 2*k[1] - 3544*k[2]/2565 + 1859*k[3]/4104 - 11*k[4]/40))

        # 4th and 5th order estimates
        y4[:] = y + dt * (25*k[0]/216 + 1408*k[2]/2565 + 2197*k[3]/4104 - k[4]/5)
        y5[:] = y + dt * (16*k[0]/135 + 6656*k[2]/12825 + 28561*k[3]/56430 - 9*k[4]/50 + 2*k[5]/55)

        # Error estimate
        err = np.max(np.abs(y5 - y4))
        if err < tol:
            t += dt
            y[:] = y5
            t_vals.append(t)
            y_vals.append(y.copy())

        # Adaptive step
        s = 2.0 if err == 0 else 0.84 * (tol * dt / (2*err))**0.25
        dt = min(max(s * dt, dt_min), dt_max)

    return np.array(t_vals), np.array(y_vals)

# ✅ Fast fixed-step RK4 integrator
def solve_ode_rk4(derivs, y0, t_span, dt=0.01):
    """
    Fast fixed-step RK4 integrator.
    Args:
        derivs : function(t, y) -> np.ndarray
        y0 : initial state (list or np.ndarray)
        t_span : (t0, t1)
        dt : step size
    """
    t0, t1 = t_span
    t_values = np.arange(t0, t1 + dt, dt)
    n_steps = len(t_values)
    y = np.zeros((n_steps, len(y0)), dtype=float)
    y[0] = y0

    for i in range(n_steps - 1):
        t = t_values[i]
        yi = y[i]
        k1 = derivs(t, yi)
        k2 = derivs(t + dt/2, yi + dt/2 * k1)
        k3 = derivs(t + dt/2, yi + dt/2 * k2)
        k4 = derivs(t + dt, yi + dt * k3)
        y[i+1] = yi + dt * (k1 + 2*k2 + 2*k3 + k4) / 6

    return t_values, y

# ------------------------------------------------------------
# 1️⃣  Build numexpr-based implicit function
# ------------------------------------------------------------
def make_implicit_func(expr, params, variables):
    """
    Build an implicit function from a string expression using numexpr.
    """
    def func(values):
        # Merge parameters + variables into one dict
        local_vars = {**params}
        for var, val in zip(variables, values):
            local_vars[var] = val
        return float(ne.evaluate(expr, local_vars))

    # Optional: allow vectorized call for performance
    def func_vec(values_array):
        # values_array: shape (N, len(variables))
        local_vars = {**params}
        for i, var in enumerate(variables):
            local_vars[var] = values_array[:, i]
        return ne.evaluate(expr, local_vars)

    func.vec = func_vec
    return func

# ------------------------------------------------------------
# 2️⃣  Optimized implicit solver with backtracking + curvature-adaptive step
# ------------------------------------------------------------
def auto_solve_implicit(f, dim=2, domain=None, step=0.01, n_steps=200,
                        tol_start=1e-2, eps=1e-3, cov_eps=1e-4):
    """
    Automatically trace f(x,y)=0 (2D) or f(x,y,z)=0 (3D).
    Optimized for numexpr-based functions, with:
      - backtracking Newton corrector
      - curvature-adaptive step size
    """

    # internal tuning parameters (kept local so signature unchanged)
    STEP_MIN_FACTOR = 1e-3   # step_min = step * STEP_MIN_FACTOR
    STEP_MAX_FACTOR = 50.0   # step_max = step * STEP_MAX_FACTOR
    BACKTRACK_SCALES = (1.0, 0.5, 0.25, 0.125)  # try these predictor scales when corrector fails
    MAX_BACKTRACK_ATTEMPTS = len(BACKTRACK_SCALES)
    NEWTON_MAX_ITERS = 8
    CURVATURE_REDUCE_ANGLE = 0.35  # radians; if angle > this -> reduce step
    CURVATURE_INCREASE_ANGLE = 0.02  # if angle < this -> slowly increase step
    STEP_INCREASE_FACTOR = 1.1
    STEP_DECREASE_FACTOR = 0.5

    # --- Numeric gradient using central difference ---
    def grad_2d(x, y):
        dfx = (f([x + eps, y]) - f([x - eps, y])) * 0.5 / eps
        dfy = (f([x, y + eps]) - f([x, y - eps])) * 0.5 / eps
        return np.array([dfx, dfy])

    def grad_3d(x, y, z):
        dfx = (f([x + eps, y, z]) - f([x - eps, y, z])) * 0.5 / eps
        dfy = (f([x, y + eps, z]) - f([x, y - eps, z])) * 0.5 / eps
        dfz = (f([x, y, z + eps]) - f([x, y, z - eps])) * 0.5 / eps
        return np.array([dfx, dfy, dfz])

    # --- Vectorized coarse start search (faster if f.vec exists) ---
    def find_start_2d():
        xs = np.linspace(domain[0][0], domain[0][1], domain[0][2])
        ys = np.linspace(domain[1][0], domain[1][1], domain[1][2])
        X, Y = np.meshgrid(xs, ys)
        pts = np.stack([X.ravel(), Y.ravel()], axis=1)
        vals = f.vec(pts)
        mask = np.abs(vals) < tol_start
        if np.any(mask):
            return refine_start_2d(pts[mask][0])
        ErrorMessageBox(message=f"No starting point found in domain ({domain}).\n"
                                f"Change the domain range or grid size to find a starting point.",
                        title="No starting point found!!!", icon='WARNING_LARGE')

    def refine_start_2d(values, max_iter=10):
        x, y = values
        for _ in range(max_iter):
            g = grad_2d(x, y)
            fval = f([x, y])
            gnorm2 = np.dot(g, g)
            if gnorm2 < cov_eps:
                break
            correction = fval * g / gnorm2
            x, y = np.array([x, y]) - correction
        return [x, y]

    def find_start_3d():
        xs = np.linspace(domain[0][0], domain[0][1], domain[0][2])
        ys = np.linspace(domain[1][0], domain[1][1], domain[1][2])
        zs = np.linspace(domain[2][0], domain[2][1], domain[2][2])
        # sample in slices to avoid huge memory for dense 3D grids
        for k in range(0, len(zs), max(1, len(zs)//6)):
            Zk = zs[k]
            X, Y = np.meshgrid(xs, ys)
            pts = np.stack([X.ravel(), Y.ravel(), np.full(X.size, Zk)], axis=1)
            vals = f.vec(pts)
            mask = np.abs(vals) < tol_start
            if np.any(mask):
                return refine_start_3d(pts[mask][0])
        # last resort: try full grid (may be heavy)
        X, Y, Z = np.meshgrid(xs, ys, zs)
        pts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1)
        vals = f.vec(pts)
        mask = np.abs(vals) < tol_start
        if np.any(mask):
            return refine_start_3d(pts[mask][0])
        ErrorMessageBox(message=f"No starting point found in domain ({domain}).\n"
                                f"Change the domain range or grid size to find a starting point.",
                        title="No starting point found!!!", icon='WARNING_LARGE')

    def refine_start_3d(values, max_iter=10):
        x, y, z = values
        for _ in range(max_iter):
            g = grad_3d(x, y, z)
            fval = f([x, y, z])
            gnorm2 = np.dot(g, g)
            if gnorm2 < cov_eps:
                break
            correction = fval * g / gnorm2
            x, y, z = np.array([x, y, z]) - correction
        return [x, y, z]

    # ----------------------
    # Corrector with backtracking helper (works for both 2D and 3D)
    # ----------------------
    def corrector_with_backtracking(p_pred):
        """
        p_pred: numpy array of length dim (predicted point)
        returns: (p_corr, success)
        tries smaller predictor steps via scaling if Newton does not converge
        """
        p_pred = np.asarray(p_pred, dtype=float)
        for scale in BACKTRACK_SCALES[:MAX_BACKTRACK_ATTEMPTS]:
            p = p_pred.copy()
            converged = False
            for _ in range(NEWTON_MAX_ITERS):
                if dim == 2:
                    g = grad_2d(p[0], p[1])
                    fval = f([p[0], p[1]])
                else:
                    g = grad_3d(p[0], p[1], p[2])
                    fval = f([p[0], p[1], p[2]])
                gnorm2 = np.dot(g, g)
                if gnorm2 <= 1e-18:
                    break
                # Newton-like correction along gradient (project f onto grad)
                p = p - scale * (fval * g / gnorm2)
                if abs(fval) < cov_eps:
                    converged = True
                    break
            if converged:
                return p, True
        return p, False

    # ----------------------
    # 2D tracing
    # ----------------------
    if dim == 2:
        x, y = find_start_2d()
        xs, ys = [x], [y]

        # local adaptive step variables
        step_local = float(step)
        step_min = max(step * STEP_MIN_FACTOR, 1e-12)
        step_max = max(step * STEP_MAX_FACTOR, step_local * 2.0)

        for _ in range(n_steps):
            g = grad_2d(x, y)
            gnorm = np.linalg.norm(g)
            if gnorm < cov_eps:
                break
            tangent = np.array([-g[1], g[0]])
            tnorm = np.linalg.norm(tangent)
            if tnorm == 0:
                break
            tangent /= tnorm

            # Predictor using current adaptive step
            p_pred = np.array([x, y]) + step_local * tangent

            # Corrector with backtracking (tries scaled corrections)
            p_corr, ok = corrector_with_backtracking(p_pred)
            if not ok:
                # reduce step and retry next loop iteration
                step_local = max(step_local * STEP_DECREASE_FACTOR, step_min)
                # if step too small, give up
                if step_local <= step_min * 1.01:
                    break
                continue

            x_pred, y_pred = p_corr[0], p_corr[1]

            # compute new tangent and adaptive step adjustment
            g_new = grad_2d(x_pred, y_pred)
            if np.linalg.norm(g_new) < 1e-16:
                # avoid divide by zero; accept and continue
                x, y = x_pred, y_pred
                xs.append(x); ys.append(y)
                continue

            tangent_new = np.array([-g_new[1], g_new[0]])
            tnew_norm = np.linalg.norm(tangent_new)
            if tnew_norm == 0:
                break
            tangent_new /= tnew_norm

            # curvature: angle between previous tangent (tangent) and tangent_new
            cosang = np.dot(tangent, tangent_new)
            cosang = np.clip(cosang, -1.0, 1.0)
            angle = np.arccos(cosang)

            # adjust step based on curvature
            if angle > CURVATURE_REDUCE_ANGLE:
                step_local = max(step_local * STEP_DECREASE_FACTOR, step_min)
            elif angle < CURVATURE_INCREASE_ANGLE:
                step_local = min(step_local * STEP_INCREASE_FACTOR, step_max)
            else:
                # small gentle relax to original step if possible
                step_local = min(max(step_local, step_min), step_max)

            # commit predicted point
            x, y = x_pred, y_pred
            xs.append(x)
            ys.append(y)

        return np.array(xs), np.array(ys)

    # ----------------------
    # 3D tracing
    # ----------------------
    elif dim == 3:
        x, y, z = find_start_3d()
        xs, ys, zs = [x], [y], [z]

        step_local = float(step)
        step_min = max(step * STEP_MIN_FACTOR, 1e-12)
        step_max = max(step * STEP_MAX_FACTOR, step_local * 2.0)

        # initial gradient and tangent basis choice
        g = grad_3d(x, y, z)
        if np.linalg.norm(g) < cov_eps:
            return np.array(xs), np.array(ys), np.array(zs)
        v = np.array([1.0, 0.0, 0.0])
        if np.allclose(np.cross(g, v), 0):
            v = np.array([0.0, 1.0, 0.0])
        tangent = np.cross(g, v)
        tnorm = np.linalg.norm(tangent)
        if tnorm == 0:
            return np.array(xs), np.array(ys), np.array(zs)
        tangent /= tnorm

        for _ in range(n_steps):
            p_pred = np.array([x, y, z]) + step_local * tangent

            # Corrector with backtracking
            p_corr, ok = corrector_with_backtracking(p_pred)
            if not ok:
                step_local = max(step_local * STEP_DECREASE_FACTOR, step_min)
                if step_local <= step_min * 1.01:
                    break
                continue

            x_pred, y_pred, z_pred = p_corr[0], p_corr[1], p_corr[2]

            # compute new gradient & tangent
            g_new = grad_3d(x_pred, y_pred, z_pred)
            if np.linalg.norm(g_new) < 1e-16:
                break

            # compute new tangent: choose cross of gradient and previous tangent to ensure tangent orthogonal to gradient
            tangent_new = np.cross(g_new, np.cross(tangent, g_new))
            tnew_norm = np.linalg.norm(tangent_new)
            if tnew_norm == 0:
                break
            tangent_new /= tnew_norm

            # curvature: angle between previous tangent and new tangent
            cosang = np.dot(tangent, tangent_new)
            cosang = np.clip(cosang, -1.0, 1.0)
            angle = np.arccos(cosang)

            if angle > CURVATURE_REDUCE_ANGLE:
                step_local = max(step_local * STEP_DECREASE_FACTOR, step_min)
            elif angle < CURVATURE_INCREASE_ANGLE:
                step_local = min(step_local * STEP_INCREASE_FACTOR, step_max)
            else:
                step_local = min(max(step_local, step_min), step_max)

            x, y, z = x_pred, y_pred, z_pred
            tangent = tangent_new
            xs.append(x); ys.append(y); zs.append(z)

        return np.array(xs), np.array(ys), np.array(zs)

    else:
        ErrorMessageBox(message=f"Dimension must be 2 or 3.\n"
                                f"But you give dim={dim}.",
                        title="Dim must be 2 or 3!!!", icon='WARNING_LARGE')
