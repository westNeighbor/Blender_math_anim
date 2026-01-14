<div align="center">

# Blender3D Math Animation Addon 

</div>

Inspired by [3Blue1Brown Manim](https://github.com/3b1b/manim) for science explainatory, I create this 
tool for the same purpose based on Blender which is much fancier and more powerful to unlock your 
creativity. It is very intuitive to use for those who don't have code based skills. If you are familiar 
with Blender, the unleashing power will enable you amaze the world.

If you like the project, please give me a star! ⭐
#### **Version for Blender 4.4 will be released at 100 ⭐, and for Blender 5.0 at 200 ⭐.  Share to unlock early releases** 😏 

## Overview
The main purpose of this addon is to provide an easy and straightfoward but powerful and fancy tool to make 
scientific knowledge animations, especially for math and physics etc. To make it lightweight, I choose the Grease 
Pencil system; another reason is that it's native to Drawing which makes it perfect choice to add drawing 
functionality. 

The math function plotting is pretty fast unless you give too much resolution. Explicit, parametric and polar 
functions are supported. It automatically detects variables and parameters with live update when their values 
change. The supported math functions come with the `asteval` package, which can be checked by 
`asteval.Interpreter().symtable.keys()` after `import asteval` in the python console.

The math formula typeset is extracted from compiled PDF, and then arrange them using Geometry Nodes char by char. 
A lot of Geometry nodes will be used if you have many chars, so this part can be slow. It supports PDF directly or 
you can type [Typst](https://github.com/typst/typst) or [Optex](https://github.com/olsak/OpTeX)(Latex) code or 
upload files, it will automatically compile them to PDF. To make things easier, only modern `.ttf` and `.otf` fonts 
are supported, the outdated Latex fonts like afm, pfm are not supported, that's why I limit the Latex engine to 
Optex. You can use LuaLaTex or XeLatex with `.otf` or `.ttf` fonts configured to compile to PDF for the addon to 
use. The addon **Preference** will build all available fonts dictionary once you provide the fonts' path.

The Drawing function enables you express your ideas freely by drawing or hand writing. With drawing tablet or iPad 
you can do anything.

The preset animations can be used across all parts and it's easy to extend or add your own if you're are familiar 
with Geometry Nodes. Of course, all things can be keyframed to animate which is super super super easy. Last, you 
can morph between or across plots, texts and drawings which is super cool.

The decision to choose Grease Pencil as the carrier of plots, texts and drawings mainly because it is lightweight, 
better for morph animations, but the cons are obvious, it is not as fancy as mesh in 3D scenes, especially for 
overlapping, the fill is not working correctly in 3D rendering yet. Hopefully, Blender can improve it with time. 
<!--
There are some awesome existing tools and addons, like [blender\_typst\_importer](https://github.com/kolibril13/blender_typst_importer) to help people, but they all lack deep features like predefined animations and single 
function orientation. Tool like [Manim](https://github.com/3b1b/manim) is very good, but it's still require 
efforts to learn code and could take quite some time to achieve what your want. 
-->

## Features
- Fast function plotting and animation, support explicit, parametric and polar functions. Automatically detect 
  variables and parameters. Same parameters can be used across different functions and do the controls. New fast  
  solvers of first order ODEs and implicit functions are implemented.
- Support different ways to compile math formula, Typst, Latex(Optex) and PDF. Easy preset animations to config.
- Support free drawing and writing.
- Morph Animation works among all types, between and across plotting, text, free drawing.
- Super easy to extend and add your own animations 
- Cool visual effects including Bloom, Glow, Rim, Shadow, etc...

## Installation And Setup
Before installation:
- [Typst](https://github.com/typst/typst) as a python package is shipped with the addon, but you'd better have 
  it in your system to test the fonts.
    - `typst fonts` will list available fonts for `Typst` use.
      ```bash
      #set text(ligatures: false) //disable ligatures for text
      ```
- You need to install Latex [Optex](https://github.com/olsak/OpTeX?tab=readme-ov-file) package if you plan to use 
  it. Then install fonts you will use.
    - It will automatically download fonts when you setup in your tex file, for example, save the following code 
      to op-demo.tex and run `optex op-demo.tex`, it will automatically download the `stix` font. 
      ```bash
      \fontfam[stix] %new computer modern, lmfonts, stix, xits, xtixtwo, dejavu
      \setff{-liga}\currvar %disable ligatures for text, otherwise, ff, fl, fi, fj, ffi, etc  will be treated as single chars
      \nopagenumbers
      $$
      e^\alpha \sum_{k=0}^\infty (\cos\beta_k + i\sin\beta_k)\sqrt{2}\int_{-\infty}^{\infty}dx\mbffraka
      $$
      \bye
      ```
    - Recommend to download all the list fonts. Available [Optex fonts](https://petr.olsak.net/ftp/olsak/optex/op-catalog.pdf)

Now:
- `Edit -> Preference -> Get Extensions -> Install from Disk...`, locate the zip file to install.
    ![Install](resources/installation.png)
- After installation, click `Add-ons` and find `Math Anim` which is this addon, and open the panel go to lower, you 
  need to add the font paths to build fonts' library, only `.otf` and `.ttf` fonts are used. You need to add the 
  Typst and Latex font paths if you plan to use them.
- Optional, you can give presets of Optex or Typst which is helpful for later use, if empty, they will not show 
  up in the addon UI.
- You also can set the N Panel Location of the addon UI, it will take effect after reopen. Default it's under Tool
  category which is better if you use Drawing cause in Draw Mode some convenient tools are available there.
    ![Setup](resources/preference_setup.png)
- You're ready to use.

## Usage
### 1. Function Plotter 
1. Select the function mode. 
2. Type the function, hit `Enter`. 
   - Variables and parameters are automatically detected. 
   - Adjust variables' ranges and parameters' values as needed.
3. Choose a plotter object, or you can create one by `Add Plotter` button if there is none.
4. Add a plotting by `Add plotting` button. 
5. Further adjust the plotting's properties, like variables's ranges, parameters' values, color, thickness, etc. 
And you can add preset animations to the plotting.

| Function Plot | With Plotting |
|---------|---------|
| ![Plot](resources/functions01.png) | ![Add Plotting](resources/functions02.png) |

**Limitations and Notes:**
- For explicit functions, polar functions, parametric functions, the supported experssions are based on 
  [`asteval`](https://lmfit.github.io/asteval/basics.html) package; for implicit functions, the expressions are 
  based on [`numexpr`](https://numexpr.readthedocs.io/en/latest/user_guide.html) package; for ODEs, the expressions 
  are based on [`meval`](https://docs.rs/meval/latest/meval/) package. The main reason to use different packages for
  different types of functions is performance consideration. Their operatons and functions supports are different 
  though major parts are same, for example, in `meval` (ODEs), `^` for power while `asteval` and `numexpr` using 
  `**`, so please check their operations and functions supports if you have problem.
- Be careful when choose parameter names, like `e`, `pi`, `inf`, `nan` are reserved names in the above packages and 
  they having meanings or stand for constant values, don't use them as parameter names.
- For both variables and parameters, same name will be linked across different functions, so you can control them
  together by using same name. 
- For variables, each name I preset 10 to use, like `x, x0, x1, ..., x9` for `x`, so you can use different 
  variables to control independently in the function expression.

### 2. Formula Text
1. Select the formula source.
2. Type the formula and hit `Enter` or upload the file. Click `Create Formula` button to get the formula.
3. Adjust the formula's properties, like color, thickness, etc. And you can add preset animations to the formula.
![Formula](resources/formulas.png)

**Limitations and Notes:**
- Remember to adjust both `text` and `stroke` due to some chars are composed by both.
- Performance could be slow if there are many chars or strokes or fills due to many geometry nodes are used.

### 3. Free Drawer
1. Select a drawing object or you create one by `Add Drawer` button if there is none.
2. Select the drawing layer; click `Draw Mode`, start to draw; click again after drawing is done to go back normal mode.
3. Adjust the drawing's properties, like color, thickness, etc. And you can add preset animations to the drawing.
![Free Drawing](resources/freedrawing.png)

**Limitations and Notes:**
- Remember to `Update Layer Tree` when you add or delete layers manually.
- Remember to exit **Draw** mode when finish drawing. 

### 4. Morph Anim
1. Click `Morph Setup` button to config the morph animations.
2. In the popup window, select the source and target objects, and choose the morph type.
3. Config the Morph chain, click `OK` button to add morph animations.
4. Adjust the morphing properties.
![Morph Setup](resources/morph_setup.png)

## Features to be added
* Solvers for linearly implicit functions and higher order ODEs.
    * Linear implicit functions of first order ODE.
    * Second order ODE.
* Support different types of plots, like bar plot, chart plot, etc...
    * Just need to integrate my another addon [dataVis_3D](https://github.com/westNeighbor/dataVis_3D).
* Geometry shape sets to plot.
    * Circle, Ellipse, etc...
    * Field plot like vector field, scalar field.
* Improve formula generation performance.
* More preset animations.


## Tutorials
Check my tutorials for detailed explanation on YouTube.

| Tutorial -- Overview | Tutorial -- Function Plotting | Tutorial -- Formula Generation |
|---------|---------|---------|
| [![Tutorial -- Overview](https://img.youtube.com/vi/6Ml6nkW8yKk/hqdefault.jpg)](https://youtu.be/6Ml6nkW8yKk) | [![Tutorial -- Function Plotting](https://img.youtube.com/vi/6QsGyOwBRRM/hqdefault.jpg)](https://youtu.be/6QsGyOwBRRM) | [![Tutorial -- Formula Generation](https://img.youtube.com/vi/UrocI9kgmuQ/hqdefault.jpg)](https://youtu.be/UrocI9kgmuQ) |
| Tutorial -- Free Drawing | Tutorial -- Morphing | |
| [![Tutorial -- Free Drawing](https://img.youtube.com/vi/zeyOdYxH2f8/hqdefault.jpg)](https://youtu.be/zeyOdYxH2f8) | [![Tutorial -- Morphing](https://img.youtube.com/vi/jnUytybWhrc/hqdefault.jpg)](https://youtu.be/jnUytybWhrc) | |

Check my social posts
| TikTok [@math_flow7](https://www.tiktok.com/@math_flow7) | BiliBili [@罗刹国落选村花](https://b23.tv/KdlEALL) | |
|---------|---------|---------|
| <a href="https://www.tiktok.com/@math_flow7"><img src="resources/tiktok_accountqrcode.JPG" width="150" alt="TikTok QR"></a>&nbsp;&nbsp;&nbsp; | <a href="https://b23.tv/KdlEALL"><img src="resources/bilibili_accountqrcode.JPG" width="150" alt="BiliBili QR"></a> | |

## 💖 Support

If it’s useful to you, please consider support its development:

| PayPal Link | PayPal QR Code| Alipay QR Code|
|---------|---------|---------|
| [![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://www.paypal.me/eastNeighbor) | <img src="resources/paypal_qrcode.png" width="150" > | <img src="resources/alipay_qrcode.jpg" width="150" > |


Thank you for your support!

## Bug Report
Use **Issues** to report bugs. 

## 🌟 Star History
[![Star History Chart](https://api.star-history.com/svg?repos=westNeighbor/Blender_math_anim&type=Date)](https://star-history.com/#westNeighbor/Blender_math_anim&Date)

##  License 
This project is licensed under the [![License](https://img.shields.io/github/license/westNeighbor/Blender_math_anim)](LICENSE).
