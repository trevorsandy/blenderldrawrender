# -*- coding: utf-8 -*-
"""
Trevor SANDY
Last Update May 05, 2023
Copyright (c) 2020 - 2023 by Trevor SANDY

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
<blender path>/blender --background --python install_blender_ldraw_addons.py -- -xi

"""

import os
import sys
import json

import traceback
import addon_utils

from pathlib import Path
from shutil import rmtree
from pathlib import Path

import bpy

setup_dir = Path(__file__).parent / "setup"
sys.path.append(str(setup_dir))

import addon_setup

from addon_setup.preferences import Preferences
from addon_setup.arguments import BlenderArgumentParser
from addon_setup import handle_fatal_error

def install_ldraw_addon(argv):
    """Install LDraw Render addons"""

    # Confirm minimum Blender version
    is_blender_28_or_later = bpy.app.version >= (2, 80, 0)
    if not is_blender_28_or_later:
        handle_fatal_error("This addon requires Blender 2.80 or greater.")
        return {'FINISHED'}

    print("INFO: Installing LDraw Addon...")

    arg_parser = BlenderArgumentParser(
        description='Install LPub3D Blender addon.')
    arg_parser.add_argument("-xr", "--disable_ldraw_render", action="store_true",
                            help="Disable the LPub3D render addon menu action in Blender")
    arg_parser.add_argument("-xi", "--disable_ldraw_import", action="store_true",
                            help="Disable the LPub3D import addon menu action in Blender")
    arg_parser.add_argument("-xm", "--disable_ldraw_import_mm", action="store_true",
                            help="Disable the LPub3D import addon menu action in Blender")
    arg_parser.add_argument("-xa", "--disable_ldraw_addons", action="store_true",
                            help="Disable the LPub3D import and render addon menu actions in Blender")

    options = arg_parser.parse_args()

    addons_to_load=tuple(map(lambda x: (Path(x["load_dir"]), x["module_name"]),
                                        json.loads(os.environ['ADDONS_TO_LOAD'])))

    # Perform addon linking and load
    try:
        addon_setup.launch(addons_to_load, options)
    except Exception as e:
        if type(e) is not SystemExit:
            traceback.print_exc()
            sys.exit()

    # Get 'LPub3D Render LDraw' addon version
    for addon in addon_utils.modules():
        if addon.bl_info.get("name", "") == "LPub3D Render LDraw":
            addon_version = addon.bl_info.get('version', (-1, -1, -1))
            print("ADDON VERSION: {0}".format(".".join(map(str, addon_version))))
            break

    # Addon installation folder
    blender_addons_path = bpy.utils.user_resource('SCRIPTS', path="addons")

    # Define path to LPub3D Import LDraw script
    install_script_path = os.getcwd()

    # Set LDraw directory in default preference file
    ldraw_path = os.environ.get('LDRAW_DIRECTORY')

    # Set user preferences file from LPub3D Blender settings
    config_file = os.path.join(
        install_script_path, "setup/addon_setup/config/LDrawRendererPreferences.ini")

    # Set LDraw parameters file
    ldraw_parameters_file = os.path.join(
        install_script_path, "setup/addon_setup/config/BlenderLDrawParameters.lst")

    # Save user preferences and LDraw directory to ImportLDraw
    pref_file = os.path.join(
        blender_addons_path, "io_scene_lpub3d_importldraw/config/ImportLDrawPreferences.ini")
    prefs = Preferences(config_file.replace('/', os.path.sep),
                        pref_file.replace('/', os.path.sep), 'TN')
    if ldraw_path != "":
        prefs.set('ldrawdirectory', ldraw_path)
    prefs.save()

    # Save user preferences and LDraw directory to ImportLDrawMM
    pref_file = os.path.join(
        blender_addons_path, "io_scene_lpub3d_importldraw_mm/config/ImportOptions.json")
    prefs = Preferences(config_file.replace('/', os.path.sep),
                        pref_file.replace('/', os.path.sep), 'MM')
    if ldraw_path != "":
        prefs.set('ldrawpath', ldraw_path)
    prefs.save()

    # Save LDraw parameters to ImportLDraw
    addon_ldraw_parameters_file = os.path.join(
        blender_addons_path, "io_scene_lpub3d_renderldraw/config/LDrawParameters.lst")
    prefs.copy_ldraw_parameters(ldraw_parameters_file, addon_ldraw_parameters_file)

    # Cleanup pycache
    for addon_path, addon_module in addons_to_load:
        pycache_path = os.path.join(addon_path, '__pycache__')
        if os.path.isdir(pycache_path):
            rmtree(pycache_path)

    # Export setup paths
    if (not options.disable_ldraw_import and not options.disable_ldraw_addons):
        environment_file = os.path.join(
            blender_addons_path, "io_scene_lpub3d_importldraw/loadldraw/background.exr")
        lsynth_directory = os.path.join(
            blender_addons_path, "io_scene_lpub3d_importldraw/lsynth")
        studlogo_directory = os.path.join(
            blender_addons_path, "io_scene_lpub3d_importldraw/studs")
        print(f"DATA: ENVIRONMENT_FILE: {environment_file.replace('/', os.path.sep)}")
        print(f"DATA: LSYNTH_DIRECTORY: {lsynth_directory.replace('/', os.path.sep)}")
        print(f"DATA: STUDLOGO_DIRECTORY: {studlogo_directory.replace('/', os.path.sep)}")

    # Finish
    print("INFO: LPub3D LDraw Addons v{0} installed.".format(".".join(map(str, addon_version))))

if __name__ == '__main__':
    install_ldraw_addon(sys.argv[1:])