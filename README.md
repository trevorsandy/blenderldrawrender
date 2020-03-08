## LPub3D Render LDraw Models with Blender ##

A [Blender](https://www.blender.org)&trade; add-on for importing and rendering [LDraw](http://www.ldraw.org)&trade; file format models and parts.

## Purpose ##
*LPub3D Import LDraw* imports [LEGO](https://www.lego.com/)® models into Blender. This addon is intended to support direct Blender integration with [LPub3D](https://trevorsandy.github.io/lpub3d).

This addon was designed to provide [LPub3D](https://trevorsandy.github.io/lpub3d) an autonomous module enabling the integrated import and render of LDraw [LEGO](https://www.lego.com/)® models using [Blender](https://www.blender.org)&trade;. However, it can be executed directly from the Blender GUI, CLI or your operating system command console.

It supports **.mpd**, **.ldr**, and **.dat** file formats.

The LDraw import sub-module is based on [Import LDraw](https://github.com/TobyLobster/ImportLDraw) by Toby Nelson (tobymnelson@gmail.com).

## Render Features ##
+ Available for Blender 2.80 and later (2.79 backport in progress).
+ **Mac**, **Windows** and **Linux** supported.
+ **MPD** file compatible.
+ **Render settings configurable** from LPub3D user interface.
+ **Monitor render progress** from LPub3D user interface or launch Blender and directly invoke render routine from manu item.
+ **Render Portable Network Graphics (.png)** image files.
+ **Crop images** with transparent background to their opaque bounds
+ **Specify transparent background** from render settings
+ **Specify blendfile** to load additional settings
+ **Specify exr 'environment' file** to load custom backdrop and ground plane

## Import Features ##
+ Available for Blender 2.80 and later (2.79 backport in progress).
+ **Mac**, **Windows** and **Linux** supported.
+ **MPD** file compatible.
+ **Import settings configurable** from LPub3D user interface.
+ **LeoCAD** groups and cameras (both perspective and orthographic) supported.
+ **LSynth** bendable parts supported (synthesized models).
+ **LDCad**  generated parts supported.
+ **Additional LDraw parts paths** can be specified.
+ **LGEO colours, sloped bricks and lighted bricks** can be custom configured via parameter (ini) file.
+ **Import and apply camera settings** from LPub3D generated LDraw content
+ **Import and apply light settings** from LPub3D generated LDraw content.
+ **Pointlignt**, **Sunlight**, **Spotlight** and **Arealight** sources available.
+ **LDraw archive (.zip) or disc library** supported. Archive libraries are auto detected when available at the specified LDraw directory path.
+ *Cycles* and *Blender Render* engines supported. It renders either engine from a single scene.
+ Import **Photorealistic** look, or **Instructions** look.
+ **Physically Based Realistic materials** - standard brick material, transparent, rubber, chrome, metal, pearlescent, glow-in-the-dark, glitter and speckle.
+ **Principled Shader supported** Uses Blender's 'Principled Shader' where available for optimal look (but still works well when unavailable).
+ **Accurate colour handling**. Correct colour space management is used so that e.g. black parts look black.
+ **Direct colours** supported.
+ **Back face culling** - fully parses all BFC information, for accurate normals.
+ **Linked duplicates** - Parts of the same type and colour can share the same mesh.
+ **Linked studs** - studs can also share the same mesh.
+ Studs can include the **LEGO logo** on them, adding extra geometry.
+ **Gaps between bricks** - Optionally adds a small space between each brick, as in real life.
+ **Smart face smoothing** - Uses Edge-Split Modifier and Sharp Edges derived from Ldraw lines, for smooth curved surfaces and sharp corners.
+ **Concave walls** - Optionally look as if each brick has very slightly concave walls (with the photorealistic renderer), which affects the look of light reflections.
+ **Light bricks** - Bricks that emit light are supported.
+ **Fast** - even large models can be imported in seconds.

### License ###

*LPub3D Render LDraw* is licensed under the [GPLv2](http://www.gnu.org/licenses/gpl-2.0.html) or any later version.

**LEGO**® is a registered trademark of the Lego Group<br clear=left>

Copyright (c) 2020 by Trevor SANDY
