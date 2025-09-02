## LPub3D Import LDraw Files into Blender ##

> A [Blender](https://www.blender.org)&trade; plug-in for importing [LDraw](http://www.ldraw.org)&trade; file format models and parts.

## History ##
This plug-in was adapted from [Import LDraw](https://github.com/TobyLobster/ImportLDraw) by Toby Nelson (tobymnelson@gmail.com) and was initially written in May 2016.

## Purpose ##
*LPub3D Import LDraw* imports [LEGO](https://www.lego.com/)® models into Blender. This addon is intended to support direct Blender integration with [LPub3D](https://trevorsandy.github.io/lpub3d)

It supports **.mpd**, **.ldr**, **.l3b**, and **.dat** file formats.

## Import Features ##
+ Works with Blender 2.81 up to at least Blender 4.5.1
+ **Mac**, **Windows** and **Linux** supported.
+ **MPD** file compatible.
+ **Import settings configurable** from LPub3D user interface.
+ **LeoCAD** groups and cameras (both perspective and orthographic) supported.
+ **LSynth** bendable parts supported (synthesized models).
+ **LDCad**  generated parts supported.
+ **Additional LDraw parts paths** can be specified.
+ **LGEO colours, sloped bricks and lighted bricks** can be custom configured via parameter (ini) file.
+ **Import and apply camera settings** from LPub3D generated LDraw content
+ **Import and apply light settings** from LPub3D generated LDraw content. Point and sunlight configurations available
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
+ **Parenting Minifigs** - Optionally make the parts of a minifig parented to each other, so e.g. rotating an arm also moves the hand with it.
+ **Fast** - even large models can be imported in seconds.

It was inspired by and initially based on code from [LDR-Importer](https://github.com/le717/LDR-Importer) but has since been completely rewritten.

## License ##

*LPub3D Import LDraw* is licensed under the [GPLv2](http://www.gnu.org/licenses/gpl-2.0.html) or any later version.

**LEGO**® is a registered trademark of the Lego Group<br clear=left>
