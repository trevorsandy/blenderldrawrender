"""
Trevor SANDY
Last Update Febryary 12, 2023
Copyright (c) 2023 by Matthew Morrison
Copyright (c) 2023 by Trevor SANDY

LPub3D Import LDraw GPLv2 license.

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

Adapted from LDraw Handler for Blender by 
Matthew Morrison [cuddlyogre] - cuddlyogre@gmail.com
"""

bl_info = {
    "name": "LPub3D Import LDraw MM",
    "description": "Import LDraw models in .mpd .ldr .l3b and .dat formats",
    "author": "Matthew Morrison <cuddlyogre@gmail.com>, Trevor SANDY <trevor.sandy@gmail.com>",
    "version": (1, 3, 5),
    "blender": (2, 82, 0),
    "location": "File > Import",
    "warning": "",
    "wiki_url": "https://github.com/trevorsandy/blenderldrawrender",
    "tracker_url": "https://github.com/trevorsandy/blenderldrawrender/issues",
    "category": "Import-Export"
    }

#############################################
# support reloading sub-modules
if "bpy" in locals():
    import importlib
    importlib.reload(ldraw_props)
    importlib.reload(operator_import)
else:
    from . import ldraw_props
    from . import operator_import
# support reloading sub-modules
#############################################

import bpy


def register():
    ldraw_props.register()
    operator_import.register()


def unregister():
    ldraw_props.unregister()
    operator_import.unregister()


if __name__ == "__main__":
    register()
