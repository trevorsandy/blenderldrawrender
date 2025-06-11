# -*- coding: utf-8 -*-
"""
Trevor SANDY
Last Update June 09, 2025
Copyright (c) 2020 - 2025 by Trevor SANDY

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

LPub3D Install Blender LDraw Addon

This file defines the routines to install the Blender LDraw Addon.

To Run (Windows example):
- Prerequisites
    - Blender 2.82 or later
- Open Windows command terminal (cmd.exe) and navigate to this script directory.
- Set Environment Variables
    - Update <Path>, then copy and paste the the optional environment variables into the console as needed.
    - If LDRAW_DIRECTORY is not set, the installation routine will attempt to locate the LDraw path.
- Execute Command
    - <Blender Path>/blender --background --python install_blender_ldraw_addons.py -- <optional arguments>
    - Example: C:\\Users\\Trevor\\Graphics\\blender-4.3.2-windows-x64\\blender.exe --background --python install_blender_ldraw_addons.py -- --disable_ldraw_import_mm
- Optional Environment Variables:
    - SET ADDONS_TO_LOAD=[{"load_dir":"<Path>\\blenderldrawrender\\addons\\io_scene_import_ldraw","module_name":"io_scene_import_ldraw"},{"load_dir":"<Path>\\blenderldrawrender\\addons\\io_scene_import_ldraw_mm","module_name":"io_scene_import_ldraw_mm"},{"load_dir":"<Path>\\blenderldrawrender\\addons\\io_scene_render_ldraw","module_name":"io_scene_render_ldraw"}]
    - SET LDRAW_DIRECTORY=<Path>\\LDraw (Note: Avoid using an LDraw path that include spaces)
- Optional Arguments:
    -xr, --disable_ldraw_render    Disable the LDraw render addon menu action in Blender
    -xi, --disable_ldraw_import    Disable the LDraw import addon menu action in Blender
    -xm, --disable_ldraw_import_mm Disable the LDraw import addon menu action in Blender
    -xa, --disable_ldraw_addons    Disable the LDraw import and render addon menu actions in Blender
    -lc, --leocad                  Specify if the Blender LDraw install script caller is LeoCAD
"""

import os
import sys
import json

import traceback
import addon_utils

from pathlib import Path
from shutil import rmtree

import bpy

parent_dir = Path(__file__).parent

sys.path.append(str(os.path.join(parent_dir, "setup")))
sys.path.append(str(os.path.join(parent_dir, "addons")))

import addon_setup
from addon_setup.arguments import BlenderArgumentParser
from io_scene_render_ldraw.preferences import Preferences


def install_ldraw_addon(argv):
    """Install LDraw Render addons"""

    print("INFO: Installing LDraw Addon...")

    arg_parser = BlenderArgumentParser(
        description='Install Blender LDraw addon.')
    arg_parser.add_argument("-xr", "--disable_ldraw_render", action="store_true",
                            help="Disable the LDraw render addon menu action in Blender")
    arg_parser.add_argument("-xi", "--disable_ldraw_import", action="store_true",
                            help="Disable the LDraw import addon menu action in Blender")
    arg_parser.add_argument("-xm", "--disable_ldraw_import_mm", action="store_true",
                            help="Disable the LDraw import addon menu action in Blender")
    arg_parser.add_argument("-xa", "--disable_ldraw_addons", action="store_true",
                            help="Disable the LDraw import and render addon menu actions in Blender")
    arg_parser.add_argument("-lc", "--leocad", action="store_true",
                    	    help="Specify if the Blender LDraw install script caller is LeoCAD")
    options = arg_parser.parse_args()

    # Process addons to load
    env_addons = os.environ.get("ADDONS_TO_LOAD")
    if env_addons is None:
        addon_path = os.path.join(parent_dir, "addons")
        default_addons = [
            {"load_dir":f"{os.path.join(addon_path,'io_scene_import_ldraw')}","module_name":"io_scene_import_ldraw"},
            {"load_dir":f"{os.path.join(addon_path,'io_scene_import_ldraw_mm')}","module_name":"io_scene_import_ldraw_mm"},
            {"load_dir":f"{os.path.join(addon_path,'io_scene_render_ldraw')}","module_name":"io_scene_render_ldraw"}
        ]
    addons_to_load=tuple(map(lambda x: (Path(x["load_dir"]), x["module_name"]),
                                        json.loads(env_addons) if env_addons is not None else default_addons))
    assert addons_to_load is not None, "No LDraw addons specified."

    # Required package list - add package, e.g. "debugpy", as needed
    required_packages = ["requests", "pillow"]

    # Perform addon linking and load
    try:
        addon_setup.launch(addons_to_load, options, required_packages)
    except Exception as e:
        if type(e) is not SystemExit:
            traceback.print_exc()
            sys.exit()

    # Get 'Blender LDraw Render' addon version
    for addon in addon_utils.modules():
        if addon.__name__ == addons_to_load[0][1]:
            addon_version = addon.bl_info.get("version", (-1, -1, -1))
            print("ADDON VERSION: {0}".format(".".join(map(str, addon_version))))
            break

    # Addon installation folder
    blender_addons_path = bpy.utils.user_resource("SCRIPTS", path="addons")

    # Set LDraw renderer preferences ini file path
    config_file = os.path.join(
        blender_addons_path, "io_scene_render_ldraw", "config", "LDrawRendererPreferences.ini")

    # Set Background environment file
    environment_file = os.path.join(
        blender_addons_path, "io_scene_import_ldraw", "loadldraw", "background.exr")

    # Save LDraw preferences and LDraw directory to ImportLDrawMM
    pref_file = os.path.join(
        blender_addons_path, "io_scene_import_ldraw_mm", "config", "ImportOptions.json")
    prefs = Preferences(config_file, pref_file, 'MM')
    prefs.set('environment_file', environment_file)
    prefs.save()

    # Save LDraw preferences and LDraw directory to ImportLDraw
    pref_file = os.path.join(
        blender_addons_path, "io_scene_import_ldraw", "config", "ImportLDrawPreferences.ini")
    prefs = Preferences(config_file, pref_file, 'TN')
    prefs.set('environmentfile', environment_file)
    lsynth_directory = os.path.join(
        blender_addons_path, "io_scene_import_ldraw", "lsynth")
    prefs.set('lsynthdirectory', lsynth_directory)
    studlogo_directory = os.path.join(
        blender_addons_path, "io_scene_import_ldraw", "studs")
    prefs.set('studlogodirectory', studlogo_directory)
    prefs.save()

    # Enaure LDraw directory is set
    ldraw_path = prefs.get('ldrawdirectory', "")
    assert ldraw_path != "", "LDraw library path not specified."

    # Cleanup pycache
    for addon_path in map(lambda item: item[0], addons_to_load):
        pycache_path = os.path.join(addon_path, '__pycache__')
        if os.path.isdir(pycache_path):
            rmtree(pycache_path)

    # Export setup paths
    if (not options.disable_ldraw_import and not options.disable_ldraw_addons):
        print(f"DATA: ENVIRONMENT_FILE: {environment_file}")
        print(f"DATA: LSYNTH_DIRECTORY: {lsynth_directory}")
        print(f"DATA: STUDLOGO_DIRECTORY: {studlogo_directory}")

    # Finish
    print("INFO: Blender LDraw Addons v{0} installed.".format(".".join(map(str, addon_version))))

if __name__ == '__main__':
    install_ldraw_addon(sys.argv[1:])
