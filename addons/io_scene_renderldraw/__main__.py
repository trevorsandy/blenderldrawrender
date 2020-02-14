# -*- coding: utf-8 -*-
"""Render LDraw GPLv2 license.

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.

"""

"""
Render LDraw

Blender load and render LDraw model.

Command arguments:
--resolution_width  [-w] <integer>: Specify the resolution width (x) in pixels
--resolution_height [-h] <integer>: Specify the resolution height (x) in pixels
--render_percentage [-p] <integer>: Specify the percentage of the render size at which to generate the image
--preferences_file       <string>:  Specify the blender preferences file absolute file path
--model_file        [-m] <string>:  Specify the rendered image file absolute file path
--rendered_file     [-r] <string>:  Specify the rendered image file absolute file path

Module call (to run):
<blender path>/blender 
--background 
lpub3d.blend 
--python-expr 
"import bpy; bpy.ops.render_scene.renderldraw" 
--
--resolution_width 800
--resolution_height 600
--render_percentage 100
--preferences_file "BlenderPreferences.ini"
--model_file "LDrawModel.mpd"
--rendered_file "LDrawModel.png"

Note: The trailing ' -- ' denotes the end of the Blender command and the beginning 
      of the arguments passed to the renderldraw addon. 

"""

import bpy
import sys
import argparse

from pprint import pprint
pprint(sys.path)

blend_file = None
cli_render = True

sargv = sys.argv
print('SYSTEM ARGUMENTS:    {0}'.format(sargv))

"""
    DEBUG - Disabled for Blender Testing
if '--' not in sargv:
    raise ValueError('You must pass the LDraw render arguments on the command line after ` -- `')

pargv = sargv[sargv.index('--') + 1:]

if len(pargv) == 0:
    raise ValueError('No LDraw render arguments detected.')
"""

parser = argparse.ArgumentParser(
    description='Render LDraw model.'
)
parser.add_argument(
    '--resolution_width',
    '-w',
    help='an integer specifying the resolution width (x) in pixels',
    type=int,
    default=1280
)
parser.add_argument(
    '--resolution_height',
    '-h',
    help='an integer specifying the resolution height (y) in pixels',
    type=int,
    default=720
)
parser.add_argument(
    '--render_percentage',
    '-p',
    help='an integer specifying the percentage of the render size at which to generate the image',
    type=int,
    default=100
)
parser.add_argument(
    '--preferences_file',
    help='a string specifying the blender preferences file absolute file path',
    type=str,
    default='C:\Users\Trevor\Projects\build-LPub3DNext-Desktop_Qt_5_11_3_MSVC2015_32bit-Debug\mainApp\32bit_debug\3rdParty\Blender\config\BlenderPreferences.ini'
)
parser.add_argument(
    '--model_file',
    '-m',
    help='a string specifying the rendered image file absolute file path',
    type=str,
    default='C:\Users\Trevor\Desktop\LPub\Checks\LPub3D\tmp\csi_blender.ldr'
)
parser.add_argument(
    '--rendered_file',
    '-f',
    help='a string specifying the rendered image file absolute file path',
    type=str,
    default='C:\Users\Trevor\Desktop\LPub\Checks\LPub3D\blender\build_checks_1_0_0_0_1_0_0_0_1_1_1240_150_DPI_1_30_23_45_0_0_0_0_0_0_REL.png'
)

args = parser.parse_args(pargv)
print('PARSED ARGUMENTS:    {0}'.format(args))

status = None

loadResult = bpy.ops.import_scene.importldraw(
    'INVOKE_DEFAULT',
    args.preferences_file,
    args.model_file)

if loadResult == {'FINISHED'}:
    renderResult = bpy.ops.render_scene.renderldraw(
        'INVOKE_DEFAULT',
        args.resolution_width,
        args.resolution_height,
        args.render_percentage,
        args.rendered_file,
        blend_file,
        cli_render)
    if renderResult == {'FINISHED'}:
        status = "SUCCESS\n"
    else:
        status = 'ERROR - LDraw model render failed. Nothing rendered\n'
else:
    status = 'ERROR - LDraw model load failed. Nothing rendered\n'

sys.stdout.write(status)

bpy.ops.wm.quit_blender()
