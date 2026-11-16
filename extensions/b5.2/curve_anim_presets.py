import bpy
import random
import math
import re
import os
import json

PRESET_FILE = os.path.join(os.path.expanduser("~"), "curve_anim_presets.json")

def add_curve_preset(curve_anim_setting, curve_node):
    item = curve_anim_setting.add()
    item.name = f"{curve_node.id_data.name}**{curve_node.name}"
    item.node_tree = curve_node.id_data.name
    item.curve_node = curve_node.name

def del_curve_preset(curve_anim_setting, curve_node):
    remove_idx = -1
    for idx, item in enumerate(curve_anim_setting):
        if item.name == f"{curve_node.id_data.name}**{curve_node.name}":
            remove_idx = idx
            break
    if remove_idx >= 0:
        curve_anim_setting.remove(remove_idx)
# ------------------------------
# Preset Curves
# ------------------------------

EASING_PRESETS = {
    "linear": [0.0, 1.0],
    "ease": [0.25, 0.1, 0.25, 1.0],
    "ease-in": [0.42, 0.0, 1.0, 1.0],
    "ease-out": [0.0, 0.0, 0.58, 1.0],
    "ease-in-out": [0.42, 0.0, 0.58, 1.0],

    # Sine
    "ease-in-sine": [0.12, 0.0, 0.39, 0.0],
    "ease-out-sine": [0.61, 1.0, 0.88, 1.0],
    "ease-in-out-sine": [0.37, 0.0, 0.63, 1.0],

    # Quad
    "ease-in-quad": [0.11, 0.0, 0.5, 0.0],
    "ease-out-quad": [0.5, 1.0, 0.89, 1.0],
    "ease-in-out-quad": [0.45, 0.0, 0.55, 1.0],

    # Cubic
    "ease-in-cubic": [0.32, 0.0, 0.67, 0.0],
    "ease-out-cubic": [0.33, 1.0, 0.68, 1.0],
    "ease-in-out-cubic": [0.65, 0.0, 0.35, 1.0],

    # Quart
    "ease-in-quart": [0.5, 0.0, 0.75, 0.0],
    "ease-out-quart": [0.25, 1.0, 0.5, 1.0],
    "ease-in-out-quart": [0.76, 0.0, 0.24, 1.0],

    # Quint
    "ease-in-quint": [0.64, 0.0, 0.78, 0.0],
    "ease-out-quint": [0.22, 1.0, 0.36, 1.0],
    "ease-in-out-quint": [0.83, 0.0, 0.17, 1.0],

    # Expo
    "ease-in-expo": [0.7, 0.0, 0.84, 0.0],
    "ease-out-expo": [0.16, 1.0, 0.3, 1.0],
    "ease-in-out-expo": [0.87, 0.0, 0.13, 1.0],

    # Circ
    "ease-in-circ": [0.55, 0.0, 1.0, 0.45],
    "ease-out-circ": [0.0, 0.55, 0.45, 1.0],
    "ease-in-out-circ": [0.85, 0.0, 0.15, 1.0],

    # Back
    "ease-in-back": [0.36, 0.0, 0.66, -0.56],
    "ease-out-back": [0.34, 1.56, 0.64, 1.0],
    "ease-in-out-back": [0.68, -0.6, 0.32, 1.6],

    # Elastic
    "ease-out-elastic": [
        0, -0.0003, -0.0012, -0.0014, -0.0005, 0.001, 0.0022, 0.0021, 0.0003,
        -0.0023, -0.0039, -0.003, 0.0005, 0.0048, 0.0067, 0.0039, -0.0028,
        -0.0094, -0.0108, -0.0042, 0.0078, 0.0176, 0.0167, 0.0025, -0.0182,
        -0.0312, -0.024, 0.0043, 0.0383, 0.0532, 0.0313, -0.0222, -0.0753,
        -0.0865, -0.0336, 0.0625, 0.1404, 0.1334, 0.0198, -0.1456, -0.25,
        -0.1922, 0.0345, 0.3066, 0.4258, 0.25, -0.1775, -0.6027, -0.6923,
        -0.269, 0.5, 1.269, 1.6923, 1.6027, 1.1775, 0.75, 0.5742, 0.6934,
        0.9655, 1.1922, 1.25, 1.1456, 0.9802, 0.8666, 0.8596, 0.9375,
        1.0336, 1.0865, 1.0753, 1.0222, 0.9688, 0.9468, 0.9617, 0.9957,
        1.024, 1.0313, 1.0182, 0.9975, 0.9833, 0.9824, 0.9922, 1.0042,
        1.0108, 1.0094, 1.0028, 0.9961, 0.9933, 0.9952, 0.9995, 1.003,
        1.0039, 1.0023, 0.9997, 0.9979, 0.9978, 0.999, 1.0005, 1.0014,
        1.0012, 1.0003, 1],

    # Bounce
    "ease-out-bounce": [
        0.0, 0.3, 0.55, 0.7, 0.85, 0.95, 1.0, 0.97, 1.0, 0.99, 1.0, 1.0]
}

# ------------------------------
# Utilities
# ------------------------------

def parse_css_easing(css_input):
    if isinstance(css_input, list):
        return css_input
    if not isinstance(css_input, str):
        return None
    css_string = css_input.strip().lower()
    if css_string.startswith("cubic-bezier("):
        match = re.match(
            r"cubic-bezier\(([-+]?\d*\.?\d+),\s*([-+]?\d*\.?\d+),\s*([-+]?\d*\.?\d+),\s*([-+]?\d*\.?\d+)\)",
            css_string
        )
        if match:
            return [float(match.group(i)) for i in range(1, 5)]
        return None
    if css_string.startswith("linear("):
        numbers = re.findall(r"[-+]?\d*\.?\d+", css_string)
        values = [float(n) for n in numbers]
        return values if len(values) >= 2 else None
    return EASING_PRESETS.get(css_string, None)

def make_positions(num, randomize=False):
    if num <= 1:
        return [0.0]
    if randomize:
        return sorted(random.random() for _ in range(num))
    return [i / (num - 1) for i in range(num)]

def random_curve(num_points, min_val, max_val):
    return [random.uniform(min_val, max_val) for _ in range(num_points)]

# ------------------------------
# Curve Generators
# ------------------------------
def finalize_curve(values, invert_vert, invert_horiz):
    x_positions = make_positions(len(values))

    if invert_vert:
        values = [1 - v for v in values]

    if invert_horiz:
        x_positions = [1 - x for x in x_positions]

    return x_positions, values

def generate_wiggle_curve(freq=3, amp=0.5, decay=0.0, invert_vert=False, invert_horiz=False):

    values = []
    num_points = freq * 20 + 1

    for i in range(num_points):
        t = i / (num_points - 1)

        envelope = (1 - t) if decay > 0 else 1
        envelope = envelope ** (1 + decay)

        y = 0.5 + math.sin(t * freq * 2 * math.pi) * amp * envelope
        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_shake_curve(intensity=0.3, freq=20, invert_vert=False, invert_horiz=False):

    values = []
    num_points = freq + 2

    for i in range(num_points):
        t = i / (num_points - 1)

        y = 0.5 + (random.random() - 0.5) * 2 * intensity * (1 - t)
        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_bounce_ease(bounces=4, strength=1.0, invert_vert=False, invert_horiz=False):

    values = []
    num_points = bounces * 15 + 2

    for i in range(num_points):
        t = i / (num_points - 1)

        y = abs(math.sin(t * bounces * math.pi)) * (1 - t) * strength
        y = 1 - y

        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_overshoot_curve(strength=1.5, freq=3, invert_vert=False, invert_horiz=False):

    values = []
    num_points = freq * 20 + 2

    for i in range(num_points):
        t = i / (num_points - 1)

        y = 1 + math.sin(t * freq * math.pi) * (1 - t) * strength
        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_smooth_curve(power=2.0, invert_vert=False, invert_horiz=False):

    values = []
    num_points = 50

    for i in range(num_points):
        t = i / (num_points - 1)

        y = t ** power / (t ** power + (1 - t) ** power)
        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_triangle_curve(freq=3, amp=0.5, invert_vert=False, invert_horiz=False):

    values = []
    num_points = freq * 20 + 1

    for i in range(num_points):
        t = i / (num_points - 1)

        y = abs((t * freq % 1) - 0.5) * 2
        y = 0.5 + (y - 0.5) * amp

        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_decay_curve(rate=5.0, invert_vert=False, invert_horiz=False):

    values = []
    num_points = 50

    for i in range(num_points):
        t = i / (num_points - 1)

        y = 1 - math.exp(-rate * t)
        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_spiral_curve(freq=6, decay=2.0, invert_vert=False, invert_horiz=False):

    values = []
    num_points = freq * 25 + 1

    for i in range(num_points):
        t = i / (num_points - 1)

        amp = (1 - t) ** decay
        y = 0.5 + math.sin(t * freq * 2 * math.pi) * amp

        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_glitch_curve(intensity=0.8, blocks=20, invert_vert=False, invert_horiz=False):

    values = []

    for i in range(blocks):
        val = 0.5 + (random.random() - 0.5) * intensity
        values.extend([val, val])

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_rollercoaster_curve(peaks=3, height=1.2, invert_vert=False, invert_horiz=False):

    values = []
    num_points = peaks * 30 + 1

    for i in range(num_points):
        t = i / (num_points - 1)

        y = math.sin(t * peaks * math.pi) * height * (1 - t)
        y = 0.5 + y

        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_impact_curve(force=2.0, recoil=0.3, invert_vert=False, invert_horiz=False):

    values = []
    num_points = 50

    for i in range(num_points):
        t = i / (num_points - 1)

        if t < 0.2:
            y = t * force
        else:
            y = 1 + math.sin((t - 0.2) * 10) * recoil * (1 - t)

        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_interference_curve(freq1=3, freq2=7, invert_vert=False, invert_horiz=False):

    values = []
    num_points = 100

    for i in range(num_points):
        t = i / (num_points - 1)

        y = (
            math.sin(t * freq1 * 2 * math.pi) +
            0.5 * math.sin(t * freq2 * 2 * math.pi)
        )

        y = 0.5 + y * 0.3
        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_pulse_curve(pulses=5, sharpness=10, invert_vert=False, invert_horiz=False):

    values = []
    num_points = pulses * 40 + 1

    for i in range(num_points):
        t = i / (num_points - 1)

        y = math.sin(t * pulses * math.pi)
        y = abs(y) ** sharpness

        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_freeze_curve(hold=0.5, invert_vert=False, invert_horiz=False):

    values = []
    num_points = 60

    for i in range(num_points):
        t = i / (num_points - 1)

        if t < hold:
            y = 0.0
        else:
            y = (t - hold) / (1 - hold)

        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_gravity_curve(power=3.0, invert_vert=False, invert_horiz=False):

    values = []
    num_points = 50

    for i in range(num_points):
        t = i / (num_points - 1)

        y = 1 - (1 - t) ** power
        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_drift_curve(strength=0.2, invert_vert=False, invert_horiz=False):

    values = [0.5]
    num_points = 100

    for i in range(1, num_points):
        step = (random.random() - 0.5) * strength
        values.append(values[-1] + step)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_magnetic_curve(sharpness=8.0, invert_vert=False, invert_horiz=False):

    values = []
    num_points = 60

    for i in range(num_points):
        t = i / (num_points - 1)
        y = 1 / (1 + math.exp(-sharpness * (t - 0.7)))
        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_yoyo_curve(pulls=3, decay=1.5, invert_vert=False, invert_horiz=False):

    values = []
    num_points = pulls * 30 + 1

    for i in range(num_points):
        t = i / (num_points - 1)

        amp = (1 - t) ** decay
        y = 0.5 + math.sin(t * pulls * 2 * math.pi) * amp

        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_explosion_curve(force=5.0, decay=4.0, invert_vert=False, invert_horiz=False):

    values = []
    num_points = 60

    for i in range(num_points):
        t = i / (num_points - 1)

        y = (t * force) * math.exp(-decay * t)
        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_climb_curve(steps=5, slip=0.2, invert_vert=False, invert_horiz=False):

    values = []
    current = 0.0

    for i in range(steps):
        values.append(current)
        current += 1.0 / steps
        values.append(current - slip)

    values.append(1.0)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_sawtooth_curve(freq=4, invert_vert=False, invert_horiz=False):

    values = []
    num_points = freq * 30 + 1

    for i in range(num_points):
        t = i / (num_points - 1)

        y = (t * freq) % 1
        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_target_lock_curve(freq=5, decay=3.0, invert_vert=False, invert_horiz=False):

    values = []
    num_points = freq * 30 + 1

    for i in range(num_points):
        t = i / (num_points - 1)

        y = 1 + math.sin(t * freq * 2 * math.pi) * math.exp(-decay * t)
        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_plateau_curve(hold_start=0.3, hold_end=0.7, invert_vert=False, invert_horiz=False):

    values = []
    num_points = 60

    for i in range(num_points):
        t = i / (num_points - 1)

        if t < hold_start:
            y = t / hold_start
        elif t < hold_end:
            y = 1.0
        else:
            y = 1.0 - (t - hold_end) / (1 - hold_end)

        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_noise_burst_curve(num_points=80, strength=0.4, decay=2.0, invert_vert=False, invert_horiz=False):

    values = []

    for i in range(num_points):
        t = i / (num_points - 1)

        noise = (random.random() - 0.5) * 2
        y = 0.5 + noise * strength * (1 - t) ** decay

        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_step_noise_curve(freq=10, strength=0.4, decay=2.0, invert_vert=False, invert_horiz=False):

    values = []
    num_points = 100

    block_size = max(1, num_points // freq)

    current_val = 0.5

    for i in range(num_points):
        t = i / (num_points - 1)

        # change value every block
        if i % block_size == 0:
            current_val = 0.5 + (random.random() - 0.5) * 2 * strength

        y = current_val * (1 - t) ** decay + 0.5 * (1 - (1 - t) ** decay)
        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_smooth_noise_curve(freq=10, strength=0.4, decay=2.0, invert_vert=False, invert_horiz=False):

    values = []
    num_points = 200

    # generate key points
    key_count = freq + 1
    keys = [0.5 + (random.random() - 0.5) * 2 * strength for _ in range(key_count)]

    for i in range(num_points):
        t = i / (num_points - 1)

        # map t → segment
        pos = t * freq
        idx = int(pos)
        frac = pos - idx

        # linear interpolation
        y = keys[idx] * (1 - frac) + keys[min(idx+1, freq)] * frac

        # apply decay envelope
        y = y * (1 - t) ** decay + 0.5 * (1 - (1 - t) ** decay)

        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_mirror_curve(freq=2, power=2.0, invert_vert=False, invert_horiz=False):

    values = []
    num_points = freq * 40 + 1  # more freq → more points

    for i in range(num_points):
        t = i / (num_points - 1)

        # repeat segments
        local_t = (t * freq) % 1

        if local_t < 0.5:
            y = (local_t * 2) ** power
        else:
            y = (1 - (local_t - 0.5) * 2) ** power

        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def generate_energy_curve(power=4.0, invert_vert=False, invert_horiz=False):

    values = []
    num_points = 60

    for i in range(num_points):
        t = i / (num_points - 1)

        y = t ** power
        values.append(y)

    return finalize_curve(values, invert_vert, invert_horiz)

def apply_envelope(values, strength=1.0):
    n = len(values)
    return [
        v * ((1 - i/(n-1)) ** strength)
        for i, v in enumerate(values)
    ]

def generate_spring_curve(bounce, strength, invert_vert=False, invert_horiz=False):
    values = []
    num_points = bounce * 2 + 1
    for i in range(num_points):
        sign = -1 if i % 2 == 0 else 1
        y = sign * (strength ** i)
        if invert_vert:
            y *= -1
        values.append(y)
    x_positions = make_positions(len(values))
    if invert_horiz:
        x_positions = [1 - x for x in x_positions]
    return x_positions, values

def generate_elastic_curve(bounce, strength, invert_vert=False, invert_horiz=False):
    values = []
    x_positions = []
    amp = (strength * 2.0) ** 1.2
    num_points = bounce * 10 + 2
    for i in range(num_points):
        t = i / (num_points - 1)
        if t == 0:
            y = 0.0
        elif t == 1:
            y = 1.0
        else:
            p = 1.0 / bounce
            s = p / 4
            if t < 0.5:
                t2 = t * 2
                y = -0.5 * (2 ** (10 * (t2 - 1)) *
                            math.sin((t2 - 1 - s) * (2 * math.pi) / p)) * amp
            else:
                t2 = t * 2 - 1
                y = (2 ** (-10 * t2) *
                     math.sin((t2 - s) * (2 * math.pi) / p)) * amp * 0.5 + 1
        values.append(y)
        x_positions.append(t)
    mid_left = num_points // 2 - 1
    mid_right = num_points // 2
    values[mid_left] -= strength
    values[mid_right] += strength
    if invert_vert:
        values = [1 - v for v in values]
    if invert_horiz:
        x_positions = [1 - x for x in x_positions]
    return x_positions, values

def generate_bounce_curve(bounces=5, invert_vert=False):
    num_points = bounces * 10 + 10
    values = []
    for i in range(num_points):
        t = i / (num_points - 1)
        y = abs(math.sin(t * bounces * math.pi) * (1 - t) ** 2)
        values.append(y)
    if invert_vert:
        values = values[::-1]
    x_positions = make_positions(num_points)
    return x_positions, values

def generate_stairs_curve(steps=10, invert_horiz=False):
    values = []
    x_positions = []
    for i in range(steps):
        step_height = i / steps
        start_x = i / steps
        end_x = (i + 1) / steps
        x_positions.append(start_x)
        values.append(step_height)
        x_positions.append(end_x - 1e-6)
        values.append(step_height)
    x_positions.append(1.0)
    values.append(1.0)
    if invert_horiz:
        x_positions = [1 - x for x in x_positions]
    return x_positions, values

def generate_peaks_curve(peaks_count=2, peak_max=1.0, peaks_randomizer=0.0):
    values = []
    for i in range(peaks_count):
        if peaks_randomizer <= 0.0:
            p = peak_max
        else:
            min_factor = max(0.0, 1.0 - peaks_randomizer)
            p = peak_max * (min_factor + (peaks_randomizer * random.random()))
        values.append(0.0)
        values.append(0.0)
        values.append(p)
        values.append(p)

    values.append(0.0)
    values.append(0.0)
    x_positions = make_positions(len(values))
    return x_positions, values

def remap_values(values, new_min=0.0, new_max=1.0, clamp=True):
    vmin = min(values)
    vmax = max(values)

    if vmax - vmin < 1e-8:
        return [new_min for _ in values]

    scale = (new_max - new_min) / (vmax - vmin)

    remapped = [new_min + (v - vmin) * scale for v in values]

    if clamp:
        remapped = [max(new_min, min(new_max, v)) for v in remapped]

    return remapped

def remap_centered(values, amplitude=1.0, center=0.0, clamp=False, clamp_range=(-1.0, 1.0)):
    vmax = max(abs(v) for v in values)

    if vmax < 1e-8:
        result = [center for _ in values]
    else:
        scale = amplitude / vmax
        result = [center + v * scale for v in values]

    if clamp:
        lo, hi = clamp_range
        result = [max(lo, min(hi, v)) for v in result]

    return result

# ------------------------------
# Save/Load preset helpers
# ------------------------------

def save_curve_to_file(preset_dict):
    presets = []
    if os.path.exists(PRESET_FILE):
        try:
            with open(PRESET_FILE, "r") as f:
                presets = json.load(f)
        except Exception:
            presets = []
    # remove any existing with same name
    presets = [p for p in presets if p.get('name') != preset_dict.get('name')]
    presets.append(preset_dict)
    try:
        with open(PRESET_FILE, "w") as f:
            json.dump(presets, f, indent=4)
    except Exception:
        pass

def get_available_presets():
    if not os.path.exists(PRESET_FILE):
        return []
    try:
        with open(PRESET_FILE, "r") as f:
            presets = json.load(f)
            return [p.get('name', "") for p in presets if 'name' in p]
    except Exception:
        return []

def load_curve_from_file(name):
    if not os.path.exists(PRESET_FILE):
        return None
    try:
        with open(PRESET_FILE, "r") as f:
            presets = json.load(f)
    except Exception:
        return None
    for p in presets:
        if p.get('name') == name:
            return p
    return None

# ------------------------------
# Core generation function
# ------------------------------

def generate_curve_from_settings(curve_setting):
    s = curve_setting
    preset = s.curve_source

    if preset == 'RANDOM':
        values = random_curve(s.num_points_random, s.min_val_random, s.max_val_random)
        x_positions = make_positions(s.num_points_random, s.random_position)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'WIGGLE':
        x_positions, values = generate_wiggle_curve(s.wiggle_freq, s.wiggle_amp, s.wiggle_decay, s.wiggle_invert_vert, s.wiggle_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'SHAKE':
        x_positions, values = generate_shake_curve(s.shake_intensity, s.shake_freq, s.shake_invert_vert, s.shake_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'BOUNCE_EASE':
        x_positions, values = generate_bounce_ease(s.bounce_ease_bounces, s.bounce_ease_strength, s.bounce_ease_invert_vert, s.bounce_ease_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'OVERSHOOT':
        x_positions, values = generate_overshoot_curve(s.overshoot_strength, s.overshoot_freq, s.overshoot_invert_vert, s.overshoot_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'SMOOTH_CURVE':
        x_positions, values = generate_smooth_curve(s.smooth_power, s.smooth_invert_vert, s.smooth_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'TRIANGLE_WAVE':
        x_positions, values = generate_triangle_curve(s.triangle_freq, s.triangle_amp, s.triangle_invert_vert, s.triangle_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'DECAY':
        x_positions, values = generate_decay_curve(s.decay_rate, s.decay_invert_vert, s.decay_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'SPIRAL_DECAY':
        x_positions, values = generate_spiral_curve(s.spiral_freq, s.spiral_decay, s.spiral_invert_vert, s.spiral_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'GLITCH':
        x_positions, values = generate_glitch_curve(s.glitch_intensity, s.glitch_blocks, s.glitch_invert_vert, s.glitch_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'ROLLERCOASTER':
        x_positions, values = generate_rollercoaster_curve(s.rollercoaster_peaks, s.rollercoaster_height, s.rollercoaster_invert_vert, s.rollercoaster_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'IMPACT':
        x_positions, values = generate_impact_curve(s.impact_force, s.impack_recoil, s.impact_invert_vert, s.impact_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'WAVE_INTERFERENCE':
        x_positions, values = generate_interference_curve(s.interference_freq1, s.interference_freq2, s.interference_invert_vert, s.interference_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'PULSE':
        x_positions, values = generate_pulse_curve(s.pulse_pulses, s.pulse_sharpness, s.pulse_invert_vert, s.pulse_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'FREEZE':
        x_positions, values = generate_freeze_curve(s.freeze_hold, s.freeze_invert_vert, s.freeze_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'GRAVITY':
        x_positions, values = generate_gravity_curve(s.gravity_power, s.gravity_invert_vert, s.gravity_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'DRIFT':
        x_positions, values = generate_drift_curve(s.drift_strength, s.drift_invert_vert, s.drift_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'MAGNETIC_SNAP':
        x_positions, values = generate_magnetic_curve(s.magnetic_sharpness, s.magnetic_invert_vert, s.magnetic_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'YOYO':
        x_positions, values = generate_yoyo_curve(s.yoyo_pulls, s.yoyo_decay, s.yoyo_invert_vert, s.yoyo_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'EXPLOSION':
        x_positions, values = generate_explosion_curve(s.explosion_force, s.explosion_decay, s.explosion_invert_vert, s.explosion_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'CLIMB':
        x_positions, values = generate_climb_curve(s.climb_steps, s.climb_slip, s.climb_invert_vert, s.climb_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'SAWTOOTH':
        x_positions, values = generate_sawtooth_curve(s.sawtooth_freq, s.sawtooth_invert_vert, s.sawtooth_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'TARGET_LOCK':
        x_positions, values = generate_target_lock_curve(s.target_lock_freq, s.target_lock_decay, s.target_lock_invert_vert, s.target_lock_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'EASE_PLATEAU':
        x_positions, values = generate_plateau_curve(s.ease_plateau_hold_start, s.ease_plateau_hold_end, s.ease_plateau_invert_vert, s.ease_plateau_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'NOISE_BURST':
        x_positions, values = generate_noise_burst_curve(s.noise_burst_points, s.noise_burst_strength, s.noise_burst_decay, s.noise_burst_invert_vert, s.noise_burst_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'STEP_NOISE':
        x_positions, values = generate_step_noise_curve(s.step_noise_freq, s.step_noise_strength, s.step_noise_decay, s.step_noise_invert_vert, s.step_noise_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'SMOOTH_NOISE':
        x_positions, values = generate_smooth_noise_curve(s.smooth_noise_freq, s.smooth_noise_strength, s.smooth_noise_decay, s.smooth_noise_invert_vert, s.smooth_noise_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'MIRROR':
        x_positions, values = generate_mirror_curve(s.mirror_freq, s.mirror_power, s.mirror_invert_vert, s.mirror_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'ENERGY':
        x_positions, values = generate_energy_curve(s.energy_power, s.energy_invert_vert, s.energy_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'SPRING':
        x_positions, values = generate_spring_curve(s.bounce, s.strength, s.invert_vert, s.invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'ELASTIC':
        x_positions, values = generate_elastic_curve(s.elastic_bounce, s.elastic_strength, False, s.elastic_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'BOUNCE':
        x_positions, values = generate_bounce_curve(s.bounce_amount, s.bounce_invert_vert)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'STAIRS':
        x_positions, values = generate_stairs_curve(s.steps_count, s.stairs_invert_horiz)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'CUSTOM':
        values = parse_css_easing(s.css_string)
        if not values or len(values) < 2:
            return {'CANCELLED'}
        x_positions = make_positions(len(values))
        if s.css_invert_horiz:
            x_positions = [1 - x for x in x_positions]
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'PRESET':
        values = parse_css_easing(EASING_PRESETS.get(s.preset_name))
        if not values or len(values) < 2:
            return {'CANCELLED'}
        x_positions = make_positions(len(values))
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'PEAKS':
        x_positions, values = generate_peaks_curve(s.peaks_count, s.peaks_max_value, s.peaks_randomizer)
        if s.apply_envelope:
            values = apply_envelope(values, strength=s.envelope_strength)
        if s.remap_range:
            values = remap_values(values, new_min=s.remap_min, new_max=s.remap_max, clamp=s.remap_clamp)
        if s.remap_center_line:
            values = remap_centered(values, amplitude=s.remap_amplitude, center=s.remap_center, clamp=s.remap_clamp_center, clamp_range=s.remap_clamp_range)
    elif preset == 'SAVELOAD':
        return {'CANCELLED'}
    else:
        return {'CANCELLED'}
    if values:
        min_val, max_val = min(values), max(values)
    else:
        min_val, max_val = 0.0, 1.0

    curve_node = None
    if bpy.data.node_groups.get(s.node_tree):
        curve_node = bpy.data.node_groups[s.node_tree].nodes.get(s.curve_node)
    if curve_node is None:
        return {'CANCELLED'}
    mapping = curve_node.mapping.curves[0]

    # adjust number of points
    while len(mapping.points) < len(values):
        # create a new point
        last = mapping.points[-1]
        mapping.points.new(last.location.x, last.location.y)
    while len(mapping.points) > len(values):
        mapping.points.remove(mapping.points[-1])

    # assign values and handles (use_vector_handles applies to all sources)
    for point, x, y in zip(mapping.points, x_positions, values):
        point.location.x = x
        point.location.y = y
        if s.use_vector_handles:
            # set to VECTOR where possible
            if hasattr(point, "handle_type"):
                try:
                    point.handle_type = 'VECTOR'
                except Exception:
                    pass
            else:
                if hasattr(point, "handle_left_type"):
                    try:
                        point.handle_left_type = 'VECTOR'
                    except Exception:
                        pass
                if hasattr(point, "handle_right_type"):
                    try:
                        point.handle_right_type = 'VECTOR'
                    except Exception:
                        pass
        else:
            # set to AUTO where possible
            if hasattr(point, "handle_type"):
                try:
                    point.handle_type = 'AUTO'
                except Exception:
                    pass
            else:
                if hasattr(point, "handle_left_type"):
                    try:
                        point.handle_left_type = 'AUTO'
                    except Exception:
                        pass
                if hasattr(point, "handle_right_type"):
                    try:
                        point.handle_right_type = 'AUTO'
                    except Exception:
                        pass

    curve_node.mapping.clip_min_y = min_val
    curve_node.mapping.clip_max_y = max_val
    curve_node.mapping.extend = 'HORIZONTAL'
    try:
        curve_node.mapping.update()
        curve_node.mapping.reset_view()
    except Exception:
        pass
    return {'FINISHED'}

# ------------------------------
# Save/Load operators and menu
# ------------------------------

class MA_CURVE_ANIM_OT_load_preset(bpy.types.Operator):
    bl_label = "Load Saved Curves"
    bl_idname = "ma_curve_anim.load_preset"

    curve_setting: bpy.props.StringProperty()

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def execute(self, context):
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        presets = get_available_presets()
        if not presets:
            layout.label(text="No curves saved")
        else:
            for p in presets:
                op = layout.operator("ma_curve_anim.select_preset", text=p)
                op.curve_setting = self.curve_setting
                op.preset_name = p

class MA_CURVE_ANIM_OT_select_preset(bpy.types.Operator):
    bl_idname = "ma_curve_anim.select_preset"
    bl_label = "Select Saved Curve"

    preset_name: bpy.props.StringProperty()
    curve_setting: bpy.props.StringProperty()
    def execute(self, context):
        s = context.scene.math_anim_curve_gen_settings.get(self.curve_setting)
        if not s:
            self.report({'WARNING'}, 'No curve setting found')
            return {'CANCELLED'}
        s.SelectedCurve = self.preset_name

        # load saved curve data
        curve_data = load_curve_from_file(self.preset_name)
        if not curve_data:
            return {'CANCELLED'}

        # get selected float curve node
        if bpy.data.node_groups.get(s.node_tree):
            curve_node = bpy.data.node_groups[s.node_tree].nodes.get(s.curve_node)
        if not curve_node:
            return {'CANCELLED'}
        mapping = curve_node.mapping.curves[0]

        points = curve_data.get('points', [])
        if not points:
            return {'CANCELLED'}

        x_positions = [p[0] for p in points]
        values = [p[1] for p in points]

        # adjust number of points
        while len(mapping.points) < len(values):
            last = mapping.points[-1]
            mapping.points.new(last.location.x, last.location.y)
        while len(mapping.points) > len(values):
            mapping.points.remove(mapping.points[-1])

        # assign points
        for point, x, y in zip(mapping.points, x_positions, values):
            point.location.x = x
            point.location.y = y
            # handles
            if s.use_vector_handles:
                if hasattr(point, "handle_type"):
                    try:
                        point.handle_type = 'VECTOR'
                    except Exception:
                        pass
                else:
                    if hasattr(point, "handle_left_type"):
                        try:
                            point.handle_left_type = 'VECTOR'
                        except Exception:
                            pass
                    if hasattr(point, "handle_right_type"):
                        try:
                            point.handle_right_type = 'VECTOR'
                        except Exception:
                            pass
            else:
                if hasattr(point, "handle_type"):
                    try:
                        point.handle_type = 'AUTO'
                    except Exception:
                        pass
                else:
                    if hasattr(point, "handle_left_type"):
                        try:
                            point.handle_left_type = 'AUTO'
                        except Exception:
                            pass
                    if hasattr(point, "handle_right_type"):
                        try:
                            point.handle_right_type = 'AUTO'
                        except Exception:
                            pass

        # update clip
        try:
            curve_node.mapping.clip_min_y = min(values) if values else 0.0
            curve_node.mapping.clip_max_y = max(values) if values else 1.0
        except Exception:
            pass

        # force update
        try:
            curve_node.mapping.update()
            curve_node.mapping.reset_view()
        except Exception:
            pass
        try:
            tree.update_tag()
        except Exception:
            pass

        # force redraw
        for area in context.screen.areas:
            if area.type == 'NODE_EDITOR':
                area.tag_redraw()

        return {'FINISHED'}

class MA_CURVE_ANIM_OT_save_preset(bpy.types.Operator):
    bl_idname = "ma_curve_anim.save_preset"
    bl_label = "Save Current Curve"
    preset_name: bpy.props.StringProperty(name="Preset Name")
    curve_setting: bpy.props.StringProperty()
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "preset_name")

    def execute(self, context):
        # find selected float curve node
        s = context.scene.math_anim_curve_gen_settings.get(self.curve_setting)
        if not s:
            self.report({'WARNING'}, "No curve setting found")
            return {'CANCELLED'}
        node_tree = bpy.data.node_groups.get(s.node_tree)
        if node_tree:
            curve_node = node_tree.nodes.get(s.curve_node)
        if not node_tree:
            self.report({'WARNING'}, "No node tree found")
            return {'CANCELLED'}
        if not curve_node:
            self.report({'WARNING'}, "Select a FloatCurve node to save")
            return {'CANCELLED'}
        mapping = curve_node.mapping.curves[0]
        points = []
        for p in mapping.points:
            points.append([float(p.location.x), float(p.location.y)])
        if not points:
            self.report({'WARNING'}, "No points to save")
            return {'CANCELLED'}
        save_curve_to_file({"name": self.preset_name, "points": points})
        self.report({'INFO'}, f"Curve '{self.preset_name}' saved.")
        return {'FINISHED'}

# ------------------------------
# Operator
# ------------------------------

class MA_CURVE_ANIM_OT_GenerateCurve(bpy.types.Operator):
    bl_idname = "ma_curve_anim.generate_curve"
    bl_label = "Generate Curve"
    bl_options = {'REGISTER', 'UNDO'}

    curve_setting: bpy.props.StringProperty()
    def execute(self, context):
        s = context.scene.math_anim_curve_gen_settings.get(self.curve_setting)
        if s:
            if bpy.data.node_groups.get(s.node_tree):
                curve_node = bpy.data.node_groups[s.node_tree].nodes.get(s.curve_node)
                if curve_node:
                    generate_curve_from_settings(s)
                else:
                    self.report({"WARNING"}, "No curve node selected!")
            else:
                self.report({"WARNING"}, "No curve node selected!")
        return {'FINISHED'}

def draw_curve_ui(layout, curve_setting):
        s = curve_setting
        op = layout.operator("ma_curve_anim.generate_curve", icon='FCURVE')
        op.curve_setting = s.name
        grid = layout.grid_flow(columns=3, align=True)
        grid.prop(s, "curve_source", text="Curve Source")

        if s.curve_source != 'SAVELOAD':
            layout.prop(s, "auto_refresh", text="Auto Refresh")
            layout.prop(s, "use_vector_handles")

        if s.curve_source == 'CUSTOM':
            layout.prop(s, "css_string")
            layout.prop(s, "css_invert_horiz")
        elif s.curve_source == 'PRESET':
            layout.prop(s, "preset_name")
        elif s.curve_source == 'WIGGLE':
            layout.prop(s, "wiggle_freq", slider=True, text="Frequency")
            layout.prop(s, "wiggle_amp", slider=True, text="Amplitude")
            layout.prop(s, "wiggle_decay", slider=True, text="Decay")
            layout.prop(s, "wiggle_invert_vert", text="Invert Vertically")
            layout.prop(s, "wiggle_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'SHAKE':
            layout.prop(s, "shake_intensity", slider=True, text="Intensity")
            layout.prop(s, "shake_freq", slider=True, text="Frequency")
            layout.prop(s, "shake_invert_vert", text="Invert Vertically")
            layout.prop(s, "shake_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'BOUNCE_EASE':
            layout.prop(s, "bounce_ease_bounces", slider=True, text="Bounces")
            layout.prop(s, "bounce_ease_strength", slider=True, text="Strength")
            layout.prop(s, "bounce_ease_invert_vert", text="Invert Vertically")
            layout.prop(s, "bounce_ease_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'OVERSHOOT':
            layout.prop(s, "overshoot_strength", slider=True, text="Strength")
            layout.prop(s, "overshoot_freq", slider=True, text="Frequency")
            layout.prop(s, "overshoot_invert_vert", text="Invert Vertically")
            layout.prop(s, "overshoot_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'SMOOTH_CURVE':
            layout.prop(s, "smooth_power", slider=True, text="Smoothness")
            layout.prop(s, "smooth_invert_vert", text="Invert Vertically")
            layout.prop(s, "smooth_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'TRIANGLE_WAVE':
            layout.prop(s, "triangle_freq", slider=True, text="Frequency")
            layout.prop(s, "triangle_amp", slider=True, text="Amplitude")
            layout.prop(s, "triangle_invert_vert", text="Invert Vertically")
            layout.prop(s, "triangle_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'DECAY':
            layout.prop(s, "decay_rate", slider=True, text="Decay Rate")
            layout.prop(s, "decay_invert_vert", text="Invert Vertically")
            layout.prop(s, "decay_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'SPIRAL_DECAY':
            layout.prop(s, "spiral_freq", slider=True, text="Frequency")
            layout.prop(s, "spiral_decay", slider=True, text="Decay")
            layout.prop(s, "spiral_invert_vert", text="Invert Vertically")
            layout.prop(s, "spiral_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'GLITCH':
            layout.prop(s, "glitch_intensity", slider=True, text="Intensity")
            layout.prop(s, "glitch_blocks", slider=True, text="Blocks")
            layout.prop(s, "glitch_invert_vert", text="Invert Vertically")
            layout.prop(s, "glitch_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'ROLLERCOASTER':
            layout.prop(s, "rollercoaster_peaks", slider=True, text="Peaks")
            layout.prop(s, "rollercoaster_height", slider=True, text="Height")
            layout.prop(s, "rollercoaster_invert_vert", text="Invert Vertically")
            layout.prop(s, "rollercoaster_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'IMPACT':
            layout.prop(s, "impact_force", slider=True, text="Force")
            layout.prop(s, "impack_recoil", slider=True, text="Recoil")
            layout.prop(s, "impact_invert_vert", text="Invert Vertically")
            layout.prop(s, "impact_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'WAVE_INTERFERENCE':
            layout.prop(s, "interference_freq1", slider=True, text="Frequency 1")
            layout.prop(s, "interference_freq2", slider=True, text="Frequency 2")
            layout.prop(s, "interference_invert_vert", text="Invert Vertically")
            layout.prop(s, "interference_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'PULSE':
            layout.prop(s, "pulse_pulses", slider=True, text="Pulses")
            layout.prop(s, "pulse_sharpness", slider=True, text="Sharpness")
            layout.prop(s, "pulse_invert_vert", text="Invert Vertically")
            layout.prop(s, "pulse_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'FREEZE':
            layout.prop(s, "freeze_hold", slider=True, text="Hold Time")
            layout.prop(s, "freeze_invert_vert", text="Invert Vertically")
            layout.prop(s, "freeze_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'GRAVITY':
            layout.prop(s, "gravity_power", slider=True, text="Gravity Power")
            layout.prop(s, "gravity_invert_vert", text="Invert Vertically")
            layout.prop(s, "gravity_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'DRIFT':
            layout.prop(s, "drift_strength", slider=True, text="Drift Strength")
            layout.prop(s, "drift_invert_vert", text="Invert Vertically")
            layout.prop(s, "drift_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'MAGNETIC_SNAP':
            layout.prop(s, "magnetic_sharpness", slider=True, text="Sharpness")
            layout.prop(s, "magnetic_invert_vert", text="Invert Vertically")
            layout.prop(s, "magnetic_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'YOYO':
            layout.prop(s, "yoyo_pulls", slider=True, text="Pulls")
            layout.prop(s, "yoyo_decay", slider=True, text="Decay")
            layout.prop(s, "yoyo_invert_vert", text="Invert Vertically")
            layout.prop(s, "yoyo_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'EXPLOSION':
            layout.prop(s, "explosion_force", slider=True, text="Force")
            layout.prop(s, "explosion_decay", slider=True, text="Decay")
            layout.prop(s, "explosion_invert_vert", text="Invert Vertically")
            layout.prop(s, "explosion_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'CLIMB':
            layout.prop(s, "climb_steps", slider=True, text="Steps")
            layout.prop(s, "climb_slip", slider=True, text="Slip")
            layout.prop(s, "climb_invert_vert", text="Invert Vertically")
            layout.prop(s, "climb_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'SAWTOOTH':
            layout.prop(s, "sawtooth_freq", slider=True, text="Frequency")
            layout.prop(s, "sawtooth_invert_vert", text="Invert Vertically")
            layout.prop(s, "sawtooth_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'TARGET_LOCK':
            layout.prop(s, "target_lock_freq", slider=True, text="Frequency")
            layout.prop(s, "target_lock_decay", slider=True, text="Decay")
            layout.prop(s, "target_lock_invert_vert", text="Invert Vertically")
            layout.prop(s, "target_lock_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'EASE_PLATEAU':
            layout.prop(s, "ease_plateau_hold_start", slider=True, text="Hold Start")
            layout.prop(s, "ease_plateau_hold_end", slider=True, text="Hold End")
            layout.prop(s, "ease_plateau_invert_vert", text="Invert Vertically")
            layout.prop(s, "ease_plateau_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'NOISE_BURST':
            layout.prop(s, "noise_burst_points", slider=True, text="Points")
            layout.prop(s, "noise_burst_strength", slider=True, text="Strength")
            layout.prop(s, "noise_burst_decay", slider=True, text="Decay")
            layout.prop(s, "noise_burst_invert_vert", text="Invert Vertically")
            layout.prop(s, "noise_burst_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'STEP_NOISE':
            layout.prop(s, "step_noise_freq", slider=True, text="Frequency")
            layout.prop(s, "step_noise_strength", slider=True, text="Strength")
            layout.prop(s, "step_noise_decay", slider=True, text="Decay")
            layout.prop(s, "step_noise_invert_vert", text="Invert Vertically")
            layout.prop(s, "step_noise_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'SMOOTH_NOISE':
            layout.prop(s, "smooth_noise_freq", slider=True, text="Frequency")
            layout.prop(s, "smooth_noise_strength", slider=True, text="Strength")
            layout.prop(s, "smooth_noise_decay", slider=True, text="Decay")
            layout.prop(s, "smooth_noise_invert_vert", text="Invert Vertically")
            layout.prop(s, "smooth_noise_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'MIRROR':
            layout.prop(s, "mirror_freq", slider=True, text="Frequency")
            layout.prop(s, "mirror_power", slider=True, text="Power")
            layout.prop(s, "mirror_invert_vert", text="Invert Vertically")
            layout.prop(s, "mirror_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'ENERGY':
            layout.prop(s, "energy_power", slider=True, text="Energy Power")
            layout.prop(s, "energy_invert_vert", text="Invert Vertically")
            layout.prop(s, "energy_invert_horiz", text="Invert Horizontally")
        elif s.curve_source == 'SPRING':
            layout.prop(s, "bounce", slider=True)
            layout.prop(s, "strength", slider=True)
            layout.prop(s, "invert_vert")
            layout.prop(s, "invert_horiz")
        elif s.curve_source == 'ELASTIC':
            layout.prop(s, "elastic_bounce", slider=True)
            layout.prop(s, "elastic_strength", slider=True)
            layout.prop(s, "elastic_invert_horiz")
        elif s.curve_source == 'BOUNCE':
            layout.prop(s, "bounce_amount", slider=True)
            layout.prop(s, "bounce_invert_vert")
        elif s.curve_source == 'STAIRS':
            layout.prop(s, "steps_count", slider=True)
            layout.prop(s, "stairs_invert_horiz")
        elif s.curve_source == 'PEAKS':
            layout.prop(s, "peaks_max_value", slider=True)
            layout.prop(s, "peaks_randomizer", slider=True)
            layout.prop(s, "peaks_count", slider=True)
        elif s.curve_source == 'RANDOM':
            layout.prop(s, "num_points_random", slider=True)
            layout.prop(s, "min_val_random", slider=True)
            layout.prop(s, "max_val_random", slider=True)
            layout.prop(s, "random_position")
        elif s.curve_source == 'SAVELOAD':
            row = layout.row(align=True)
            op = row.operator("ma_curve_anim.save_preset", icon='ADD')
            op.curve_setting = s.name
            op = row.operator("ma_curve_anim.load_preset", text="Load", icon='IMPORT')
            op.curve_setting = s.name
        layout.prop(s, "apply_envelope", text="Apply Envelope")
        if s.apply_envelope:
            layout.prop(s, "envelope_strength", slider=True, text="Envelope Strength")
        layout.prop(s, "remap_range", text="Remap Range")
        if s.remap_range:
            row = layout.row(align=True)
            row.prop(s, "remap_min", text="Min")
            row.prop(s, "remap_max", text="Max")
            icon = 'CHECKBOX_HLT' if s.remap_clamp else 'CHECKBOX_DEHLT'
            row.prop(s, "remap_clamp", text="", icon=icon, icon_only=True)
        layout.prop(s, "remap_center_line", text="Remap Center")
        if s.remap_center_line:
            row = layout.row(align=True)
            row.prop(s, "remap_center", text="Center")
            row.prop(s, "remap_amplitude", text="Amplitude")
            icon = 'CHECKBOX_HLT' if s.remap_clamp_center else 'CHECKBOX_DEHLT'
            row.prop(s, "remap_clamp_center", text="", icon=icon, icon_only=True)
            if s.remap_clamp_center:
                row = layout.row(align=True)
                row.prop(s, "remap_clamp_range", text="Clamp Range")

# ------------------------------
# Properties
# ------------------------------
class MA_CURVE_ANIM_Settings(bpy.types.PropertyGroup):
    node_tree: bpy.props.StringProperty()
    curve_node: bpy.props.StringProperty()
    def _settings_update(self, context):
        if self.auto_refresh:
            if bpy.data.node_groups.get(self.node_tree):
                curve_node = bpy.data.node_groups[self.node_tree].nodes.get(self.curve_node)
                if curve_node:
                    generate_curve_from_settings(self)
    curve_source: bpy.props.EnumProperty(
        name="Curve Source",
        items=[
            ('WIGGLE', "Wiggle", "👉 smooth sine wiggle, optional decay"),
            ('SHAKE', "Shake", "👉 chaotic shaking, decays over time"),
            ('BOUNCE_EASE', "Bounce ease", "👉 classic UI bounce to rest"),
            ('OVERSHOOT', "Overshoot", "👉 overshoots above 1, then settles"),
            ('SMOOTH_CURVE', "Smooth curve", "👉 very clean animation curve"),
            ('TRIANGLE_WAVE', "Triangle Wave", "👉 sharp repeating motion"),
            ('DECAY', "Decay", "👉 fast start → slow settle"),
            ('SPIRAL_DECAY', "Spiral Decay", "👉 feels like tightening spring"),
            ('GLITCH', "Glitch", "👉 great for UI / tech effects"),
            ('ROLLERCOASTER', "Rollcoaster", "👉 big peaks → small dips"),
            ('IMPACT', "Impact", "👉 fast hit + bounce back"),
            ('WAVE_INTERFERENCE', "Wave Interference", "👉 organic / chaotic smooth motion"),
            ('PULSE', "Pluse", "👉 sharp spikes like heartbeat / signal"),
            ('FREEZE', "Freeze and Release", "👉 nothing → sudden motion"),
            ('GRAVITY', "Reverse Gravity", "👉 natural acceleration feel"),
            ('DRIFT', "Chaotic Drift", "👉 random walk motion"),
            ('MAGNETIC_SNAP', "Magnetic Snap", "👉 feels like snapping into place"),
            ('YOYO', "Yo-Yo", "👉 oscillates around center, shrinking"),
            ('EXPLOSION', "Explosion", "👉 sharp peak early, then fade"),
            ('CLIMB', "Climb and Slip", "👉 progress with little failures"),
            ('SAWTOOTH', "Sawtooth", "👉 repeating ramp motion"),
            ('TARGET_LOCK', "Target Lock", "👉 overshoot → settle exactly"),
            ('EASE_PLATEAU', "Ease Plateau", "👉 pause in the middle"),
            ('NOISE_BURST', "Noise Burst", "👉 chaotic → calm"),
            ('STEP_NOISE', "Step Noise", "👉 discrete frequency bands of noise"),
            ('SMOOTH_NOISE', "Smooth Noise", "👉 smooth frequency noise"),
            ('MIRROR', "Mirror", "👉 symmetric rise/fall"),
            ('ENERGY', "Energy Build-UP", "👉 dramatic acceleration"),
            ('SPRING', "Spring", ""),
            ('ELASTIC', "Elastic", ""),
            ('BOUNCE', "Bounce", ""),
            ('STAIRS', "Stairs", ""),
            ('PEAKS', "Peaks", ""),
            ('RANDOM', "Random", ""),
            ('PRESET', "Preset", ""),
            ('CUSTOM', "Custom", ""),
            ('SAVELOAD', "Save/Load", ""),
        ],
        default='WIGGLE',
        update=_settings_update,
    )

    auto_refresh: bpy.props.BoolProperty(
        name="Auto Refresh",
        description="When enabled, the curve updates automatically when properties change",
        default=True,
        update=_settings_update,
    )

    use_vector_handles: bpy.props.BoolProperty(
        name="Use Vector Handles",
        default=False,
        description="Set point handles to VECTOR instead of AUTO",
        update=_settings_update,
    )

    # Preset / Custom
    preset_name: bpy.props.EnumProperty(
        name="Preset",
        items=[(k, k.replace("-", " ").title(), "") for k in EASING_PRESETS.keys()],
        default='linear',
        update=_settings_update,
    )
    css_string: bpy.props.StringProperty(
        name="Custom CSS",
        default="linear(0, 1)",
        update=_settings_update,
    )
    css_invert_horiz: bpy.props.BoolProperty(
        name="Invert Horizontally",
        default=False,
        update=_settings_update,
    )

    # Random
    num_points_random: bpy.props.IntProperty(
        name="Points",
        default=6,
        min=2,
        max=128,
        update=_settings_update,
    )
    min_val_random: bpy.props.FloatProperty(
        name="Min Value",
        default=-1.0,
        min=-1.0,
        max=0.0,
        update=_settings_update,
    )
    max_val_random: bpy.props.FloatProperty(
        name="Max Value",
        default=1.0,
        min=0.0,
        max=1.0,
        update=_settings_update,
    )
    random_position: bpy.props.BoolProperty(
        name="Random Position",
        default=False,
        update=_settings_update,
    )

    # wiggle
    wiggle_freq: bpy.props.IntProperty(
        name="Wiggle Frequency",
        default=3,
        min=1,
        max=50,
        update=_settings_update,
    )
    wiggle_amp: bpy.props.FloatProperty(
        name="Wiggle Amplitude",
        default=0.5,
        min=0.01,
        max=20.0,
        update=_settings_update,
    )
    wiggle_decay: bpy.props.FloatProperty(
        name="Wiggle Decay",
        default=0.0,
        min=0.0,
        max=20.0,
        update=_settings_update,
    )
    wiggle_invert_vert: bpy.props.BoolProperty(
        name="Wiggle Invert Vertically",
        default=False,
        update=_settings_update,
    )
    wiggle_invert_horiz: bpy.props.BoolProperty(
        name="Wiggle Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    #shake
    shake_intensity: bpy.props.FloatProperty(
        name="Shake Intensity",
        default=0.3,
        min=0.01,
        max=1.0,
        update=_settings_update,
    )
    shake_freq: bpy.props.IntProperty(
        name="Shake Frequency",
        default=20,
        min=1,
        max=1000,
        update=_settings_update,
    )
    shake_invert_vert: bpy.props.BoolProperty(
        name="Shake Invert Vertically",
        default=False,
        update=_settings_update,
    )
    shake_invert_horiz: bpy.props.BoolProperty(
        name="Shake Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    #bounce ease
    bounce_ease_bounces: bpy.props.IntProperty(
        name="Bounce Ease Bounces",
        default=4,
        min=1,
        max=20,
        update=_settings_update,
    )
    bounce_ease_strength: bpy.props.FloatProperty(
        name="Bounce Ease Strength",
        default=1.0,
        min=0.01,
        max=20.0,
        update=_settings_update,
    )
    bounce_ease_invert_vert: bpy.props.BoolProperty(
        name="Bounce Ease Invert Vertically",
        default=False,
        update=_settings_update,
    )
    bounce_ease_invert_horiz: bpy.props.BoolProperty(
        name="Bounce Ease Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # overshoot
    overshoot_strength: bpy.props.FloatProperty(
        name="Overshoot Strength",
        default=1.5,
        min=0.01,
        max=20.0,
        update=_settings_update,
    )
    overshoot_freq: bpy.props.IntProperty(
        name="Overshoot Frequency",
        default=3,
        min=1,
        max=20,
        update=_settings_update,
    )
    overshoot_invert_vert: bpy.props.BoolProperty(
        name="Overshoot Invert Vertically",
        default=False,
        update=_settings_update,
    )
    overshoot_invert_horiz: bpy.props.BoolProperty(
        name="Overshoot Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # smooth curve
    smooth_power: bpy.props.FloatProperty(
        name="Smooth Power",
        default=2.0,
        min=0.01,
        max=20.0,
        update=_settings_update,
    )
    smooth_invert_vert: bpy.props.BoolProperty(
        name="Smooth Invert Vertically",
        default=False,
        update=_settings_update,
    )
    smooth_invert_horiz: bpy.props.BoolProperty(
        name="Smooth Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # triangle wave
    triangle_freq: bpy.props.IntProperty(
        name="Triangle Frequency",
        default=3,
        min=1,
        max=20,
        update=_settings_update,
    )
    triangle_amp: bpy.props.FloatProperty(
        name="Triangle Amplitude",
        default=0.5,
        min=0.01,
        max=20.0,
        update=_settings_update,
    )
    triangle_invert_vert: bpy.props.BoolProperty(
        name="Triangle Invert Vertically",
        default=False,
        update=_settings_update,
    )
    triangle_invert_horiz: bpy.props.BoolProperty(
        name="Triangle Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # decay
    decay_rate: bpy.props.FloatProperty(
        name="Decay Rate",
        default=5.0,
        min=0.01,
        max=50.0,
        update=_settings_update,
    )
    decay_invert_vert: bpy.props.BoolProperty(
        name="Decay Invert Vertically",
        default=False,
        update=_settings_update,
    )
    decay_invert_horiz: bpy.props.BoolProperty(
        name="Decay Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # Spiral
    spiral_freq: bpy.props.IntProperty(
        name="Spiral Frequency",
        default=3,
        min=1,
        max=20,
        update=_settings_update,
    )
    spiral_decay: bpy.props.FloatProperty(
        name="Spiral Decay",
        default=2.0,
        min=0.0,
        max=20.0,
        update=_settings_update,
    )
    spiral_invert_vert: bpy.props.BoolProperty(
        name="Spiral Invert Vertically",
        default=False,
        update=_settings_update,
    )
    spiral_invert_horiz: bpy.props.BoolProperty(
        name="Spiral Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    glitch_intensity: bpy.props.FloatProperty(
        name="Glitch Intensity",
        default=0.8,
        min=0.01,
        max=10.0,
        update=_settings_update,
    )
    glitch_blocks: bpy.props.IntProperty(
        name="Glitch Blocks",
        default=20,
        min=2,
        max=50,
        update=_settings_update,
    )
    glitch_invert_vert: bpy.props.BoolProperty(
        name="Glitch Invert Vertically",
        default=False,
        update=_settings_update,
    )
    glitch_invert_horiz: bpy.props.BoolProperty(
        name="Glitch Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # rollercoaster
    rollercoaster_peaks: bpy.props.IntProperty(
        name="Rollercoaster Peaks",
        default=3,
        min=1,
        max=30,
        update=_settings_update,
    )
    rollercoaster_height: bpy.props.FloatProperty(
        name="Rollercoaster Height",
        default=1.2,
        min=0.01,
        max=20.0,
        update=_settings_update,
    )
    rollercoaster_invert_vert: bpy.props.BoolProperty(
        name="Rollercoaster Invert Vertically",
        default=False,
        update=_settings_update,
    )
    rollercoaster_invert_horiz: bpy.props.BoolProperty(
        name="Rollercoaster Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    impact_force: bpy.props.FloatProperty(
        name="Impact Force",
        default=5.0,
        min=-10.0,
        max=20.0,
        update=_settings_update,
    )
    impack_recoil: bpy.props.FloatProperty(
        name="Impact Recoil",
        default=0.3,
        min=0.0,
        max=10.0,
        update=_settings_update,
    )
    impact_invert_vert: bpy.props.BoolProperty(
        name="Impact Invert Vertically",
        default=False,
        update=_settings_update,
    )
    impact_invert_horiz: bpy.props.BoolProperty(
        name="Impact Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # interference
    interference_freq1: bpy.props.IntProperty(
        name="Interference Frequency 1",
        default=3,
        min=1,
        max=50,
        update=_settings_update,
    )
    interference_freq2: bpy.props.IntProperty(
        name="Interference Frequency 2",
        default=7,
        min=1,
        max=50,
        update=_settings_update,
    )
    interference_invert_vert: bpy.props.BoolProperty(
        name="Interference Invert Vertically",
        default=False,
        update=_settings_update,
    )
    interference_invert_horiz: bpy.props.BoolProperty(
        name="Interference Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # pulse
    pulse_pulses: bpy.props.IntProperty(
        name="Pulse Pulses",
        default=5,
        min=1,
        max=50,
        update=_settings_update,
    )
    pulse_sharpness: bpy.props.FloatProperty(
        name="Pulse Sharpness",
        default=10,
        min=0.01,
        max=50,
        update=_settings_update,
    )
    pulse_invert_vert: bpy.props.BoolProperty(
        name="Pulse Invert Vertically",
        default=False,
        update=_settings_update,
    )
    pulse_invert_horiz: bpy.props.BoolProperty(
        name="Pulse Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # freeze
    freeze_hold: bpy.props.FloatProperty(
        name="Freeze Hold",
        default=0.5,
        min=0.0,
        max=1.0,
        update=_settings_update,
    )
    freeze_invert_vert: bpy.props.BoolProperty(
        name="Freeze Invert Vertically",
        default=False,
        update=_settings_update,
    )
    freeze_invert_horiz: bpy.props.BoolProperty(
        name="Freeze Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # gravity
    gravity_power: bpy.props.FloatProperty(
        name="Gravity Power",
        default=3.0,
        min=0.01,
        max=30.0,
        update=_settings_update,
    )
    gravity_invert_vert: bpy.props.BoolProperty(
        name="Gravity Invert Vertically",
        default=False,
        update=_settings_update,
    )
    gravity_invert_horiz: bpy.props.BoolProperty(
        name="Gravity Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # drift
    drift_strength: bpy.props.FloatProperty(
        name="Drift Strength",
        default=0.2,
        min=0.01,
        max=1.0,
        update=_settings_update,
    )
    drift_invert_vert: bpy.props.BoolProperty(
        name="Drift Invert Vertically",
        default=False,
        update=_settings_update,
    )
    drift_invert_horiz: bpy.props.BoolProperty(
        name="Drift Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # Magnetic snap
    magnetic_sharpness: bpy.props.FloatProperty(
        name="Magnetic Sharpness",
        default=8.0,
        min=0.01,
        max=50.0,
        update=_settings_update,
    )
    magnetic_invert_vert: bpy.props.BoolProperty(
        name="Magnetic Invert Vertically",
        default=False,
        update=_settings_update,
    )
    magnetic_invert_horiz: bpy.props.BoolProperty(
        name="Magnetic Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # Yo-Yo
    yoyo_pulls: bpy.props.IntProperty(
        name="Yo-Yo Pulls",
        default=3,
        min=1,
        max=20,
        update=_settings_update,
    )
    yoyo_decay: bpy.props.FloatProperty(
        name="Yo-Yo Decay",
        default=1.5,
        min=0.0,
        max=20.0,
        update=_settings_update,
    )
    yoyo_invert_vert: bpy.props.BoolProperty(
        name="Yo-Yo Invert Vertically",
        default=False,
        update=_settings_update,
    )
    yoyo_invert_horiz: bpy.props.BoolProperty(
        name="Yo-Yo Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # Explosion
    explosion_force: bpy.props.FloatProperty(
        name="Explosion Force",
        default=5.0,
        min=0.01,
        max=20.0,
        update=_settings_update,
    )
    explosion_decay: bpy.props.FloatProperty(
        name="Explosion Decay",
        default=4.0,
        min=0.0,
        max=20.0,
        update=_settings_update,
    )
    explosion_invert_vert: bpy.props.BoolProperty(
        name="Explosion Invert Vertically",
        default=False,
        update=_settings_update,
    )
    explosion_invert_horiz: bpy.props.BoolProperty(
        name="Explosion Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # Climb and Slip
    climb_steps: bpy.props.IntProperty(
        name="Climb Steps",
        default=5,
        min=1,
        max=20,
        update=_settings_update,
    )
    climb_slip: bpy.props.FloatProperty(
        name="Climb and Slip",
        default=0.3,
        min=0.0,
        max=2.0,
        update=_settings_update,
    )
    climb_invert_vert: bpy.props.BoolProperty(
        name="Climb Invert Vertically",
        default=False,
        update=_settings_update,
    )
    climb_invert_horiz: bpy.props.BoolProperty(
        name="Climb Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # Sawtooth
    sawtooth_freq: bpy.props.IntProperty(
        name="Sawtooth Frequency",
        default=4,
        min=1,
        max=20,
        update=_settings_update,
    )
    sawtooth_invert_vert: bpy.props.BoolProperty(
        name="Sawtooth Invert Vertically",
        default=False,
        update=_settings_update,
    )
    sawtooth_invert_horiz: bpy.props.BoolProperty(
        name="Sawtooth Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # Target Lock
    target_lock_freq: bpy.props.IntProperty(
        name="Target Lock Frequency",
        default=5,
        min=1,
        max=20,
        update=_settings_update,
    )
    target_lock_decay: bpy.props.FloatProperty(
        name="Target Lock Decay",
        default=3.0,
        min=0.0,
        max=20.0,
        update=_settings_update,
    )
    target_lock_invert_vert: bpy.props.BoolProperty(
        name="Target Lock Invert Vertically",
        default=False,
        update=_settings_update,
    )
    target_lock_invert_horiz: bpy.props.BoolProperty(
        name="Target Lock Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # Ease Plateau
    ease_plateau_hold_start: bpy.props.FloatProperty(
        name="Ease Plateau Hold Start",
        default=0.3,
        min=0.0,
        max=1.0,
        update=_settings_update,
    )
    ease_plateau_hold_end: bpy.props.FloatProperty(
        name="Ease Plateau Hold End",
        default=0.7,
        min=0.0,
        max=1.0,
        update=_settings_update,
    )
    ease_plateau_invert_vert: bpy.props.BoolProperty(
        name="Ease Plateau Invert Vertically",
        default=False,
        update=_settings_update,
    )
    ease_plateau_invert_horiz: bpy.props.BoolProperty(
        name="Ease Plateau Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # Noise Burst
    noise_burst_points: bpy.props.IntProperty(
        name="Noise Burst Points",
        default=50,
        min=1,
        max=100,
        update=_settings_update,
    )
    noise_burst_strength: bpy.props.FloatProperty(
        name="Noise Burst Strength",
        default=0.4,
        min=0.01,
        max=20.0,
        update=_settings_update,
    )
    noise_burst_decay: bpy.props.FloatProperty(
        name="Noise Burst Decay",
        default=2.0,
        min=0.0,
        max=20.0,
        update=_settings_update,
    )
    noise_burst_invert_vert: bpy.props.BoolProperty(
        name="Noise Burst Invert Vertically",
        default=False,
        update=_settings_update,
    )
    noise_burst_invert_horiz: bpy.props.BoolProperty(
        name="Noise Burst Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # Step Noise
    step_noise_freq: bpy.props.IntProperty(
        name="Step Noise Frequency",
        default=5,
        min=1,
        max=50,
        update=_settings_update,
    )
    step_noise_strength: bpy.props.FloatProperty(
        name="Step Noise Strength",
        default=0.5,
        min=0.01,
        max=20.0,
        update=_settings_update,
    )
    step_noise_decay: bpy.props.FloatProperty(
        name="Step Noise Decay",
        default=2.0,
        min=0.0,
        max=20.0,
        update=_settings_update,
    )
    step_noise_invert_vert: bpy.props.BoolProperty(
        name="Step Noise Invert Vertically",
        default=False,
        update=_settings_update,
    )
    step_noise_invert_horiz: bpy.props.BoolProperty(
        name="Step Noise Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # Smooth Noise
    smooth_noise_freq: bpy.props.IntProperty(
        name="Smooth Noise Frequency",
        default=5,
        min=1,
        max=50,
        update=_settings_update,
    )
    smooth_noise_strength: bpy.props.FloatProperty(
        name="Smooth Noise Strength",
        default=0.5,
        min=0.01,
        max=20.0,
        update=_settings_update,
    )
    smooth_noise_decay: bpy.props.FloatProperty(
        name="Smooth Noise Decay",
        default=2.0,
        min=0.0,
        max=20.0,
        update=_settings_update,
    )
    smooth_noise_invert_vert: bpy.props.BoolProperty(
        name="Smooth Noise Invert Vertically",
        default=False,
        update=_settings_update,
    )
    smooth_noise_invert_horiz: bpy.props.BoolProperty(
        name="Smooth Noise Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # Mirror
    mirror_freq: bpy.props.IntProperty(
        name="Mirror Frequency",
        default=2,
        min=1,
        max=20,
        update=_settings_update,
    )
    mirror_power: bpy.props.FloatProperty(
        name="Mirror Power",
        default=2.0,
        min=0.01,
        max=20.0,
        update=_settings_update,
    )
    mirror_invert_vert: bpy.props.BoolProperty(
        name="Mirror Invert Vertically",
        default=False,
        update=_settings_update,
    )
    mirror_invert_horiz: bpy.props.BoolProperty(
        name="Mirror Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # Energy Build-Up
    energy_power: bpy.props.FloatProperty(
        name="Energy Power",
        default=4.0,
        min=0.01,
        max=20.0,
        update=_settings_update,
    )
    energy_invert_vert: bpy.props.BoolProperty(
        name="Energy Invert Vertically",
        default=False,
        update=_settings_update,
    )
    energy_invert_horiz: bpy.props.BoolProperty(
        name="Energy Invert Horizontally",
        default=False,
        update=_settings_update,
    )
    # Spring
    bounce: bpy.props.IntProperty(
        name="Bounce",
        default=5,
        min=1,
        max=30,
        update=_settings_update,
    )
    strength: bpy.props.FloatProperty(
        name="Strength",
        default=0.5,
        min=0.0,
        max=1.0,
        update=_settings_update,
    )
    invert_vert: bpy.props.BoolProperty(
        name="Invert Vertically",
        default=False,
        update=_settings_update,
    )
    invert_horiz: bpy.props.BoolProperty(
        name="Invert Horizontally",
        default=False,
        update=_settings_update,
    )

    # Elastic
    elastic_bounce: bpy.props.IntProperty(
        name="Bounce",
        default=5,
        min=1,
        max=30,
        update=_settings_update,
    )
    elastic_strength: bpy.props.FloatProperty(
        name="Strength",
        default=0.5,
        min=0.0,
        max=1.0,
        update=_settings_update,
    )
    elastic_invert_horiz: bpy.props.BoolProperty(
        name="Invert Horizontally",
        default=False,
        update=_settings_update,
    )

    # Bounce
    bounce_amount: bpy.props.IntProperty(
        name="Bounces",
        default=5,
        min=1,
        max=20,
        update=_settings_update,
    )
    bounce_invert_vert: bpy.props.BoolProperty(
        name="Invert Vertically",
        default=False,
        update=_settings_update,
    )

    # Stairs
    steps_count: bpy.props.IntProperty(
        name="Steps Counter",
        default=10,
        min=2,
        max=50,
        update=_settings_update,
    )
    stairs_invert_horiz: bpy.props.BoolProperty(
        name="Invert Horizontally",
        default=False,
        update=_settings_update,
    )

    # Peaks
    peaks_count: bpy.props.IntProperty(
        name="Peaks Count",
        default=2,
        min=1,
        max=50,
        update=_settings_update,
    )
    peaks_max_value: bpy.props.FloatProperty(
        name="Peaks Max Value",
        default=1.0,
        min=0.0,
        max=1.0,
        update=_settings_update,
    )
    peaks_randomizer: bpy.props.FloatProperty(
        name="Peaks Randomizer",
        default=0.0,
        min=0.0,
        max=1.0,
        description="0 = all peaks at max value; 1 = peaks randomized down to near 0",
        update=_settings_update,
    )
    remap_range: bpy.props.BoolProperty(default=True, update=_settings_update)
    remap_min: bpy.props.FloatProperty(default=0.0, update=_settings_update)
    remap_max: bpy.props.FloatProperty(default=1.0, update=_settings_update)
    remap_clamp: bpy.props.BoolProperty(default=False, update=_settings_update)
    remap_center_line: bpy.props.BoolProperty(default=False, update=_settings_update)
    remap_amplitude: bpy.props.FloatProperty(default=1.0, update=_settings_update)
    remap_center: bpy.props.FloatProperty(default=0.0, update=_settings_update)
    remap_clamp_center: bpy.props.BoolProperty(default=False, update=_settings_update)
    remap_clamp_range: bpy.props.FloatVectorProperty(size=2, default=(-1.0, 1.0), update=_settings_update)
    apply_envelope: bpy.props.BoolProperty(default=False, update=_settings_update)
    envelope_strength: bpy.props.FloatProperty(default=1.0, min=0.0, max=20.0, update=_settings_update)

    # Save/Load
    SelectedCurve: bpy.props.StringProperty(name="Selected Curve", default="")

# ------------------------------
# Registration
# ------------------------------

classes = (
    MA_CURVE_ANIM_Settings,
    MA_CURVE_ANIM_OT_GenerateCurve,
    MA_CURVE_ANIM_OT_select_preset,
    MA_CURVE_ANIM_OT_load_preset,
    MA_CURVE_ANIM_OT_save_preset,
)

register, unregister = bpy.utils.register_classes_factory(classes)
