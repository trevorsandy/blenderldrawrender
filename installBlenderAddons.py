# -*- coding: utf-8 -*-
"""
Trevor SANDY
Last Update February 06, 2020
Copyright (c) 2020 by Trevor SANDY

LPub3D Blender LDraw Addon GPLv2 license.

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

Install LPub3D Blender Addon

This file defines the routines to install the LPub3D Blender Addon.

To Run:
- Navigate to script directory:
<LPub3D User Directory>/3rdParty/Blender
- Execute command
<blender path>/blender --background --python installBlenderAddons.py

"""

import os
import bpy
import addon_utils

from typing import Union, Set


def install_addons():
    # Capture installed version
    tup = 0
    if hasattr(bpy.app, "version"):
        tup = bpy.app.version
    isBlender28OrLater = tup >= (2, 80)

    # Define path to Import LDraw script
    path_to_script_dir = os.getcwd()

    # Define path to Import LDraw add-on bundle
    path_to_addon_dir: Union[bytes, str] = os.path.join(path_to_script_dir, "addons")

    # Define a list of the files in this add-on folder.
    file_list = sorted(os.listdir(path_to_addon_dir))

    for file in file_list:
        print('ADDON FILE:         ' + file)

    # Specify the path of each addon.
    for file in file_list:
        path_to_file = os.path.join(path_to_addon_dir, file)
        if isBlender28OrLater:
            bpy.ops.preferences.addon_install(overwrite=True, filter_folder=True, target='DEFAULT',
                                              filepath=path_to_file, filter_python=True, filter_glob='*.py;*.zip')
        else:
            bpy.ops.wm.addon_install(overwrite=True, filter_folder=True, target='DEFAULT',
                                     filepath=path_to_file, filter_python=True, filter_glob='*.py;*.zip')

    # Specify which add-ons to enable.
    enable_these_addons: Set[str] = {'io_scene_importldraw', 'io_scene_renderldraw'}

    # Enable addons.
    for string in enable_these_addons:
        print('ENABLE THIS ADDON:   ' + string)
        if isBlender28OrLater:
            bpy.ops.preferences.addon_enable(module=string)
        else:
            bpy.ops.wm.addon_enable(module=string)

    # Save user preferences
    bpy.ops.wm.save_userpref()

    # Get 'Render LDraw' addon version
    for mod in addon_utils.modules():
        if mod.bl_info.get("name", "") == "Render LDraw":
            version = mod.bl_info.get('version', (-1, -1, -1))
            print("ADDON VERSION:      {0}".format(".".join(map(str, version))))
            break


if __name__ == '__main__':
    install_addons()
