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

import bpy

from . import renderldraw

bl_info = {
    "name": "Render LDraw",
    "description": "Render LDraw model as .png file",
    "author": "Trevor SANDY <trevor.sandy@gmail.com>",
    "version": (1, 0, 0),
    "blender": (2, 81, 0),
    "location": "Render",
    "warning": "",
    "wiki_url": "https://trevorsandy.github.io/lpub3d",
    "tracker_url": "https://github.com/trevorsandy/blenderldrawrender/issues",
    "category": "Render"
}


# Addon menu item
def menuRender(self, context):
    """Render menu listing label."""
    self.layout.operator(renderldraw.RenderLDrawOps.bl_idname,
                         text="Render LDraw Model (.png)",
                         icon='RENDER_RESULT')


# When enabling the addon.
def register():
    """Register Render LDraw."""
    bpy.utils.register_class(renderldraw.RenderLDrawOps)
    if hasattr(bpy.types, 'TOPBAR_MT_render'):
        # Blender 2.80
        bpy.types.TOPBAR_MT_render.prepend(menuRender)
    else:
        # Blender 2.79
        bpy.types.INFO_MT_render.prepend(menuRender)


# When disabling the addon.
def unregister():
    """Unregister Render LDraw."""
    bpy.utils.unregister_class(renderldraw.RenderLDrawOps)
    if hasattr(bpy.types, 'TOPBAR_MT_render'):
        # Blender 2.80
        bpy.types.TOPBAR_MT_render.remove(menuRender)
    else:
        # Blender 2.79
        bpy.types.INFO_MT_render.remove(menuRender)


if __name__ == "__main__":
    register()

    # bpy.ops.render_scene.renderldraw('INVOKE_DEFAULT') # Test call
