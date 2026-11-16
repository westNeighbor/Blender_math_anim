import pymupdf
import json
import subprocess
import glob
import os
import bpy
import platform
import shutil
import typst
import unicodedata
from collections import Counter

####------------------------------------------------### help functions
def ErrorMessageBox(message, title, icon="ERROR"):
    def draw(self, context):
        self.layout.label(text=message)
    bpy.context.window_manager.popup_menu(draw, title=title, icon=icon)

def get_font_name(file_path): # get font name
    font_name, family_name, is_math = "", "", False
    try:
        from fontTools.ttLib import TTFont
        # load the font
        font = TTFont(file_path, lazy=True)
        is_math = 'MATH' in font.keys()
    except Exception as e:
        ErrorMessageBox(f"{file_path} open failed, ignore this font!", str(e), "WARNING_LARGE")
        return font_name, family_name, is_math

    # get font name
    for record in font['name'].names:
        if record.nameID not in (1, 6):
            continue
        # 1: Font Family Name, 4: Full Font Name, 6: PostScript Name, etc, use nameID 1 when setting fonts in Typst, use nameID 6 when embedding fonts in PDF, use nameID 4 when need a human readable full name
        encoding = 'mac_roman' if record.platformID ==1 else 'utf-16-be'
        try:
            value = record.string.decode(encoding).replace('\x00', '')
        except UnicodeDecodeError as e:
            value = record.string.decode('utf-16-be', errors='ignore').replace('\x00', '')
            ErrorMessageBox(f"couldn't decode the font name from {file_path}, ingore this font!", str(e), "WARNING_LARGE")
        if record.nameID == 1:
            family_name = value
        elif record.nameID == 6:
            font_name = value
            break

    return str(font_name), str(family_name), is_math

def get_unicode_name(char=""):
    unicode_name = ""
    # get char unicode name
    if char:
        try:
            unicode_name = unicodedata.name(char)
        except:
            pass
    return unicode_name

def load_dict_from_file(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        dictionary = json.load(file)
    return dictionary

def save_dict_to_file(file_path, dictionary):
    with open(file_path, 'w', encoding="utf-8") as file:
        json.dump(dictionary, file, ensure_ascii=False, indent=4)

def build_file_path_dict(root_dir):
    file_dict = {}
    for subdir, _, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith(('.otf', '.ttf')):
                full_path = os.path.join(subdir, file)
                full_path = full_path.replace('\\', '/')
                font_name, family_name, is_math = get_font_name(full_path)
                if font_name:
                    _, extension = os.path.splitext(file.lower())
                    file_dict[f"{font_name}{extension}"] = {}
                    file_dict[f"{font_name}{extension}"]['path'] =  full_path
                    file_dict[f"{font_name}{extension}"]['family'] =  family_name
                    file_dict[f"{font_name}{extension}"]['is_math'] =  is_math
    return file_dict

def extract_text_and_shape(pdf_path):
    # Open the PDF file
    pdf_document = pymupdf.open(pdf_path)

    # Iterate through pages
    math_texts = []
    math_strokes = [] # for drawing strokes
    math_fills = [] # for drawing fills
    color_list = {"line": [], "fill": []} # for later material creatation
    for page_num in range(pdf_document.page_count):
        page = pdf_document[page_num]
        page_width = page.rect.width
        page_height = page.rect.height
        scale_page_width = 20.0
        text = page.get_text("rawdict", flags = pymupdf.TEXTFLAGS_RAWDICT | pymupdf.TEXT_ACCURATE_BBOXES)  # Extract text in dictionary format, some math symbols will be composite of char + strokes, so need handle this situations
        drawings = page.get_cdrawings() # Extract shapes (type 's' for strokes, type 'f' for fills)

        m_chars = []
        coord_x = []
        coord_y = []
        for block in text["blocks"]:
            if block['type'] != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    font = span["font"]
                    font_size = (span["size"]/page_width)*scale_page_width
                    color = span.get("color", 0)  # Default color is black if not provided
                    alpha = span.get("alpha", 255.0)
                    alpha = round(alpha/255.0, 4)

                    # Extract each character
                    chars = span["chars"]
                    for char in chars:
                        if char['c'].strip():  # Ignore whitespace characters
                            # Get character Unicode value
                            unicode_value = ord(char['c'])

                            # Get character position
                            origin_xy = char["origin"]
                            bbox_h = ((char["bbox"][3]-char["bbox"][1])/page_width)*scale_page_width
                            bbox_w = ((char["bbox"][2]-char["bbox"][0])/page_width)*scale_page_width
                            coord_x.append(origin_xy[0])
                            coord_y.append(origin_xy[1])
                            x = ((origin_xy[0]-coord_x[0])/page_width)*scale_page_width # shift first to 0
                            y = ((coord_y[0]-origin_xy[1])/page_width)*scale_page_width # shift first to 0
                            ur_x = ((char['bbox'][2]-coord_x[0])/page_width)*scale_page_width # upper right corner
                            ur_y = ((coord_y[0]-char['bbox'][3])/page_width)*scale_page_width # upper right corner

                            # Extract the color as an RGBA value
                            red = round(((color & 0xFF0000) >> 16)/255.0, 4)
                            green = round(((color & 0x00FF00) >> 8)/255.0, 4)
                            blue = round((color & 0x0000FF)/255.0, 4)
                            unicode = f"{unicode_value:04X}"
                            if len(unicode)>4:
                                unicode = f"{unicode:0>8}"
                            m_chars.append({"char": char['c'], "unicode": unicode, "font": font, "fontsize": font_size, "bbox_h": bbox_h,"bbox_w": bbox_w, "location": (x, y), "color": (red, green, blue, alpha), "ur_corner": (ur_x, ur_y)}) # last item is upper right corner point
                            color_list['line'].append((red, green, blue, alpha))
                            #print(f"char: {char['c']}, fontsize: {font_size}, bbox_h: {bbox_h}, bbox_w: {bbox_w},origin: ({origin_xy[0]}, {origin_xy[1]})")

        math_texts.append(m_chars)

        strokes = []
        fills = []
        for drawing in drawings:
            if drawing['type'] == 's': #or drawing['type'] == 'fs':
                r,g,b = drawing.get("color",(0.0,0.0,0.0))
                r = round(r, 4)
                g = round(g, 4)
                b = round(b, 4)
                alpha = drawing.get("stroke_opacity", 1.0)
                alpha = round(alpha, 4)
                line_width = (drawing["width"]/page_width)*scale_page_width
                control_points = []
                left_handles = []
                right_handles = []
                item_len = len(drawing['items'])
                first_item = drawing['items'][0]
                h_line = False
                v_line = False
                if first_item[0] == 'l':
                    h_line = (first_item[1][1] == first_item[2][1]) # horizontal or vertical line
                    v_line = (first_item[1][0] == first_item[2][0]) # horizontal or vertical line
                if first_item[0] == 're':
                    x1, y1, x2, y2 = first_item[1]
                    points = [ ((x1-coord_x[0])/page_width)*scale_page_width, ((coord_y[0]-y1)/page_width)*scale_page_width, ((x2-coord_x[0])/page_width)*scale_page_width, ((coord_y[0]-y2)/page_width)*scale_page_width ]
                    control_points = [(points[0],points[1], 0.0), (points[2],points[1], 0.0), (points[2],points[3], 0.0), (points[0],points[3], 0.0)]
                    strokes.append({'type': 're', 'color': (r, g, b, alpha), 'control_points': control_points, 'left_handles': left_handles, 'right_handles': right_handles})
                    color_list['line'].append((r, g, b, alpha))
                elif first_item[0] == 'qu':
                    points = first_item[1]
                    points = [(((x-coord_x[0])/page_width)*scale_page_width, ((coord_y[0]-y)/page_width)*scale_page_width, 0.0) for x, y in points]
                    control_points = [points[0], points[1], points[3], points[2]]
                    strokes.append({'type': 're', 'color': (r, g, b, alpha), 'control_points': control_points, 'left_handles': left_handles, 'right_handles': right_handles})
                    color_list['line'].append((r, g, b, alpha))
                elif item_len == 1 and first_item[0] == 'l' and (h_line or v_line): # just vertial or horizontal line case
                    points = first_item[1:]
                    points = [(((x-coord_x[0])/page_width)*scale_page_width, ((coord_y[0]-y)/page_width)*scale_page_width, 0.0) for x, y in points]
                    if h_line: # horizontal line
                        control_points.extend([(points[0][0], points[0][1]-line_width/2.0, 0.0), (points[1][0], points[1][1]-line_width/2.0, 0.0), (points[1][0], points[1][1]+line_width/2.0, 0.0), (points[0][0], points[0][1]+line_width/2.0, 0.0)])
                    else: # vertical line
                        control_points.extend([(points[1][0]-line_width/2.0, points[1][1], 0.0), (points[1][0]+line_width/2.0, points[1][1], 0.0), (points[0][0]+line_width/2.0, points[0][1], 0.0), (points[0][0]-line_width/2.0, points[0][1], 0.0)])
                    strokes.append({'type': 'line', 'color': (r, g, b, alpha), 'control_points': control_points, 'left_handles': left_handles, 'right_handles': right_handles})
                    color_list['line'].append((r, g, b, alpha))

                else:
                    for i in range(item_len):
                        item = drawing['items'][i]
                        if item[0] == 'l': # line
                            points = item[1:]
                            points = [(((x-coord_x[0])/page_width)*scale_page_width, ((coord_y[0]-y)/page_width)*scale_page_width, 0.0) for x, y in points]
                            if i == 0:
                                control_points.extend(points)
                                left_handles.extend(points)
                                right_handles.extend(points)
                            else:
                                control_points.append(points[1])
                                right_handles.append(points[1])
                                left_handles.append(points[1])
                        elif item[0] == 'c': # curve
                            points = item[1:]
                            points = [(((x-coord_x[0])/page_width)*scale_page_width, ((coord_y[0]-y)/page_width)*scale_page_width, 0.0) for x, y in points]
                            if i == 0:
                                control_points.extend([points[0], points[3]])
                                left_handles.extend([points[0], points[2]])
                                right_handles.extend([points[1], points[3]])
                            else:
                                control_points.append(points[3])
                                right_handles[-1] = points[1]
                                left_handles.append(points[2])
                                right_handles.append(points[3])
                        else:
                            print(f"unhandled shape type for stroke: {item[0]}")
                    strokes.append({'type': 'curve', 'color': (r, g, b, alpha), 'control_points': control_points, 'left_handles': left_handles, 'right_handles': right_handles, 'line_width': line_width})
                    color_list['line'].append((r, g, b, alpha))
            elif drawing['type'] == 'f' or drawing['type'] == 'fs':
                r,g,b = drawing.get("fill", (0.0, 0.0, 0.0))
                r = round(r, 4)
                g = round(g, 4)
                b = round(b, 4)
                alpha = drawing.get("fill_opacity", 1.0)
                alpha = round(alpha, 4)
                if drawing['items'][0][0] == 're': # rectangle
                    item = drawing['items'][0]
                    x1, y1, x2, y2 = item[1]
                    points = [ ((x1-coord_x[0])/page_width)*scale_page_width, ((coord_y[0]-y1)/page_width)*scale_page_width, ((x2-coord_x[0])/page_width)*scale_page_width, ((coord_y[0]-y2)/page_width)*scale_page_width ]
                    control_points = [(points[0],points[1], 0.0), (points[2],points[1], 0.0), (points[2],points[3], 0.0), (points[0],points[3], 0.0)]
                    fills.append({'type': 'rect', 'color': (r, g, b, alpha), 'points': control_points})
                    color_list['fill'].append((r, g, b, alpha))
                elif drawing['items'][0][0] == 'qu': # quad
                    item = drawing['items'][0]
                    points = item[1]
                    points = [(((x-coord_x[0])/page_width)*scale_page_width, ((coord_y[0]-y)/page_width)*scale_page_width, 0.0) for x, y in points]
                    control_points = [points[0], points[1], points[3], points[2]]
                    fills.append({'type': 'quad', 'color': (r, g, b, alpha), 'points': control_points})
                    color_list['fill'].append((r, g, b, alpha))
                elif drawing['items'][0][0] == 'l' or drawing['items'][0][0] == 'c':
                    control_points = []
                    left_handles = []
                    right_handles = []
                    item_len = len(drawing['items'])
                    for i in range(item_len):
                        item = drawing['items'][i]
                        if item[0] == 'l': # line
                            points = item[1:]
                            points = [(((x-coord_x[0])/page_width)*scale_page_width, ((coord_y[0]-y)/page_width)*scale_page_width, 0.0) for x, y in points]
                            if i == 0:
                                control_points.extend(points)
                                left_handles.extend(points)
                                right_handles.extend(points)
                            else:
                                control_points.append(points[1])
                                right_handles.append(points[1])
                                left_handles.append(points[1])
                        elif item[0] == 'c': # curve
                            points = item[1:]
                            points = [(((x-coord_x[0])/page_width)*scale_page_width, ((coord_y[0]-y)/page_width)*scale_page_width, 0.0) for x, y in points]
                            if i == 0:
                                control_points.extend([points[0], points[3]])
                                left_handles.extend([points[0], points[2]])
                                right_handles.extend([points[1], points[3]])
                            else:
                                control_points.append(points[3])
                                right_handles[-1] = points[1]
                                left_handles.append(points[2])
                                right_handles.append(points[3])
                        else:
                            print(f"unhandled shape type for mix 'l' and 'c' of fill: {item[0]}")
                    fills.append({'type': 'curve', 'color': (r, g, b, alpha), 'control_points': control_points, 'left_handles': left_handles, 'right_handles': right_handles})
                    color_list['fill'].append((r, g, b, alpha))
                else:
                    print(f"unhandled shape type for fill: {drawing['items'][0][0]}")
            else:
                print(f"unhandled drawing type: {drawing['type']}")

        math_strokes.append(strokes)
        math_fills.append(fills)

    if color_list['line']:
        color_list['line'] = dict(Counter(color_list['line']))
        color_list['line'] = dict(sorted(color_list['line'].items(), key=lambda item: item[1], reverse=True))
    if color_list['fill']:
        color_list['fill'] = dict(Counter(color_list['fill']))
        color_list['fill'] = dict(sorted(color_list['fill'].items(), key=lambda item: item[1], reverse=True))

    return math_texts, math_strokes, math_fills, color_list

# Compile latex math formula to pdf
def compile_tex(self, context, contents, mode, font, temp_dir, source_type=0):

    math_texts = []
    strokes = []
    fills = []
    colors = {}
    # Set current directory to temp_directory
    current_dir = os.getcwd()
    os.chdir(temp_dir)
    temp_dir = os.path.realpath(temp_dir)

    # Create temp latex or typst file with specified preamble.
    temp_file_name = temp_dir + os.sep + 'temp'
    if source_type < 2:
        temp = open(temp_file_name + '.txt', "a")
        if source_type == 0:
            formula_props = context.scene.math_anim_formula_props
            default_preamble = f'\\fontfam[{formula_props.optex_fontfam}]\n\\setff{{-liga}}\\currvar\n\\nopagenumbers\n\\magnification=1200\n'
            temp.write(default_preamble)
        elif source_type == 1:
            default_preamble = '#set text(ligatures: false)\n'
            temp.write(default_preamble)

        # Add latex code to temp.txt and close the file.
        for i in range(len(contents)):
            if mode[i]:
                contents[i] = contents[i].replace('\\\\', '\\')  # escape backslashes
                if source_type == 0:
                    temp.write('\n $$ \n' + contents[i] + '\n $$ \n')
                else:
                    if font[i]:
                        localfont = font[i].rsplit('.', 1)[0]  # remove file extension
                        temp.write(f'#[\n#show math.equation: set text(font: "{localfont}", ligatures: false)\n$\n{contents[i]}\n$\n]')
                    else:
                        temp.write('\n $ \n' + contents[i] + '\n $ \n')
            else:
                contents[i] = contents[i].replace('\\n', '\n')  # escape backslashes
                if font[i]:
                    localfont = font[i].rsplit('.', 1)[0]  # remove file extension
                    if source_type == 0:
                        temp.write(f'\n {{\\font \\localfont = {{{localfont}}} at 12pt \n \\localfont {contents[i]} \n}} \n')
                    else:
                        temp.write(f'#[#set text(font: "{localfont}", ligatures: false) \n{contents[i]}\n] \n\n')
                else:
                    temp.write("\n" + contents[i] + "\n")
        if source_type == 0:
            temp.write('\\bye')
        temp.close()
    elif source_type < 4:
        shutil.copy(contents[0], temp_file_name + '.txt')
    else:
        shutil.copy(contents[0], temp_file_name + '.pdf')

    # Try to compile temp.tex and create an pdf file
    optex_path = shutil.which("optex")
    if not optex_path:
        if platform.system() in ("Darwin", "Linux"):
            shell = os.environ.get("SHELL")
            if shell is not None:
                # -l = login, -i = interactive, -c = run command
                result = subprocess.run(
                [shell, "-ilc", "echo $PATH"],
                capture_output=True, text=True
            )
            shell_path = result.stdout.strip()
            if shell_path:
                os.environ["PATH"] = shell_path + os.pathsep + os.environ["PATH"]
    local_env = os.environ.copy()
    try:
        if source_type == 0 or source_type == 2:
            print("optex processing ...")
            optex_path = shutil.which("optex")
            tex_process = subprocess.run(["optex", "-interaction=nonstopmode", temp_file_name + '.txt'], env=local_env, text=True, stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
            print("optex process done")
        elif source_type == 1 or source_type == 3:
            print("typst processing ...")
            typst.compile(f"{temp_file_name}.txt", output=f"{temp_file_name}.pdf")
            print("typst process done")
        pdf_file_list = glob.glob(temp_file_name + ".pdf")

        if len(pdf_file_list) == 0:
            if source_type == 0 or source_type == 2:
                self.report({"ERROR"},
                             "Compiling failed, check the optex output below." + "\n" +
                             "Tex return code " + str(tex_process.returncode) + "\n" +
                             "Tex error message: " + str(tex_process.stdout) + "\n"
                         )
            elif source_type == 1 or source_type == 3:
                self.report({"ERROR"}, "typst compile failed, check your code!")
            else:
                self.report({"ERROR"}, "No pdf file!")

        else:
            math_texts, strokes, fills, colors = extract_text_and_shape(pdf_file_list[0])
            print("Finished analysis the layout of text and shapes.")

    except FileNotFoundError as e:
        ErrorMessageBox("Please check that LaTeX(optex) is installed on your system and its path is correct.", "Compilation Error")
    except subprocess.CalledProcessError as e:
        ErrorMessageBox("Please check your LaTeX(optex) code for errors" + "\n" +
                        "Return code: " + str(e.returncode) + " " + str(e.output) + "\n",
                        "Compilation Error")
    finally:
        os.chdir(current_dir)
        return math_texts, strokes, fills, colors
####------------------------------------------------### end of help functions
