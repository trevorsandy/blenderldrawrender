# -*- coding: utf-8 -*-
"""LPub3D Import LDraw GPLv2 license.

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

# Import From Files - See PR https://github.com/TobyLobster/ImportLDraw/pull/49/
if "bpy" in locals():
    import importlib
    importlib.reload(importldraw)
else:
    from . import importldraw

import bpy

bl_info = {
    "name": "LPub3D Import LDraw",
    "description": "Import LDraw models in .mpd .ldr .l3b and .dat formats",
    "author": "Trevor SANDY <trevor.sandy@gmail.com>",
    "version": (1, 1, 0),
    "blender": (2, 81, 0),
    "location": "File > Import",
    "warning": "",
    "wiki_url": "https://github.com/trevorsandy/blenderldrawrender",
    "tracker_url": "https://github.com/trevorsandy/blenderldrawrender/issues",
    "category": "Import-Export"
    }


def menuImport(self, context):
    """Import menu listing label."""
    self.layout.operator(importldraw.ImportLDrawOps.bl_idname,
                         text="LPub3D Import LDraw (.mpd/.ldr/.l3b/.dat)")


def register():
    """Register Menu Listing."""
    bpy.utils.register_class(importldraw.ImportLDrawOps)
    if hasattr(bpy.types, 'TOPBAR_MT_file_import'):
        # Blender 2.80
        bpy.types.TOPBAR_MT_file_import.prepend(menuImport)
    else:
        # Blender 2.79
        bpy.types.INFO_MT_file_import.prepend(menuImport)


def unregister():
    """Unregister Menu Listing."""
    bpy.utils.unregister_class(importldraw.ImportLDrawOps)
    if hasattr(bpy.types, 'TOPBAR_MT_file_import'):
        # Blender 2.80
        bpy.types.TOPBAR_MT_file_import.remove(menuImport)
    else:
        # Blender 2.79
        bpy.types.INFO_MT_file_import.remove(menuImport)

if __name__ == "__main__":
    register()
    
    # bpy.ops.import_scene.lpub3dimportldraw('INVOKE_DEFAULT') # Test call
