"""
Trevor SANDY
Last Update May 06, 2023
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
    "version": (1, 3, 6),
    "blender": (2, 82, 0),
    "location": "File > Import",
    "warning": "",
    "wiki_url": "https://github.com/trevorsandy/blenderldrawrender",
    "tracker_url": "https://github.com/trevorsandy/blenderldrawrender/issues",
    "category": "Import-Export"
    }

#############################################
# support reloading sub-modules
_modules_loaded = []
_modules = [
    'base64_handler',
    'blender_camera',
    'blender_import',
    'blender_light',
    'blender_lookat',
    'blender_materials',
    'definitions',
    'export_options',
    'filesystem',
    'geometry_data',
    'group',
    'helpers',
    'import_options',
    'import_settings',
    'ldraw_camera',
    'ldraw_colors',
    'ldraw_export',
    'ldraw_file',
    'ldraw_light',
    'ldraw_mesh',
    'ldraw_meta',
    'ldraw_node',
    'ldraw_object',
    'ldraw_part_types',
    'matrices',
    'pe_texmap',
    'special_bricks',
    'strings',
    'texmap'
]

# Reload previously loaded modules
if "bpy" in locals():
    from importlib import reload
    reload(ldraw_props)
    reload(operator_import)
    reload(operator_export)
    reload(operator_panel_ldraw)

    _modules_loaded[:] = [reload(module) for module in _modules_loaded]
    del reload
else:
    from . import ldraw_props
    from . import operator_import
    from . import operator_export
    from . import operator_panel_ldraw

# First import the modules
__import__(name=__name__, fromlist=_modules)
_namespace = globals()
_modules_loaded = [_namespace[name] for name in _modules]
del _namespace
# support reloading sub-modules
#############################################

import bpy


def register():
    ldraw_props.register()
    operator_import.register()
    operator_export.register()
    operator_panel_ldraw.register()


def unregister():
    ldraw_props.unregister()
    operator_import.unregister()
    operator_export.unregister()
    operator_panel_ldraw.unregister()


if __name__ == "__main__":
    register()
