# -*- coding: utf-8 -*-
"""
Trevor SANDY
Last Update January 23, 2023
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
<blender path>/blender --background --python installBlenderAddons.py

"""

import os
import sys
import argparse
import subprocess
import configparser

from typing import Union, Set

import addon_utils
import bpy

class BlenderArgumentParser(argparse.ArgumentParser):
    """Consume command line arguments after '--'"""
    def _argv_after_doubledash(self):
        try:
            arg_index = sys.argv.index("--")
            return sys.argv[arg_index+1:] # arguments after '--'
        except ValueError as e:
            return []

    def parse_args(self):                # overrides superclass
        return super().parse_args(args=self._argv_after_doubledash())

class Preferences():
    """Import LDraw - Preferences"""

    __sectionName   = 'importldraw'

    def __init__(self, preferencesfile):
        if preferencesfile.__ne__(""):
            self.__prefsFilepath = preferencesfile
            print("INFO: Preferences file:    {0}".format(self.__prefsFilepath))

        self.__config = configparser.RawConfigParser()
        self.__prefsRead = self.__config.read(self.__prefsFilepath)
        if self.__prefsRead and not self.__config[Preferences.__sectionName]:
            self.__prefsRead = False

    def set(self, option, value):
        if not (Preferences.__sectionName in self.__config):
            self.__config[Preferences.__sectionName] = {}
        self.__config[Preferences.__sectionName][option] = str(value)

    def save(self):
        try:
            with open(self.__prefsFilepath, 'w') as configfile:
                self.__config.write(configfile)
            return True
        except Exception:
            e = sys.exc_info()[0]
            print("WARNING: Could not save preferences. {0}".format(e))
            return False

def install_package(package):
    """Install Pillow module"""

    import importlib
    package_spec = importlib.util.find_spec("pip")
    is_blender_291_or_later = bpy.app.version >= (2, 91, 0)
    if package_spec is not None:

        import pip
        if is_blender_291_or_later:
            pybin = sys.executable
        else:
            pybin = bpy.app.binary_path_python
        
        args = [pybin, "-m", "pip", "list"]
        pipes = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        std_out, std_err = pipes.communicate()
        args = [pybin, "-m", "pip", "install", "--user", "--no-deps", "--no-warn-script-location", package]
        if pipes.returncode != 0:
            err_msg = f"ERROR: {0}. Code: {1}".format(std_err.strip(), pipes.returncode)
            raise Exception(err_msg)
        elif len(std_err):
            if "A new release of pip available" in std_err.decode(sys.getfilesystemencoding()) or \
               "You are using pip version" in std_err.decode(sys.getfilesystemencoding()):
                args = [pybin, "-m", "pip", "install", "--user", "--upgrade", "pip", "--no-deps", "--no-warn-script-location", package]
                print("INFO: Upgrading {0}...".format(package))
        else:
            print("INFO: Installing {0}...".format(package))
        #print("DEBUG INFO: PIP LIST: \n{0}.\n".format(std_out.decode(sys.getfilesystemencoding())))
        pipes = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        std_out, std_err = pipes.communicate()
        if pipes.returncode != 0:
            err_msg = f"ERROR: {0}. Code: {1}".format(std_err.strip(), pipes.returncode)
            raise Exception(err_msg)
        elif len(std_err):
            print("WARNING: {0}".format(std_err.decode(sys.getfilesystemencoding())))
        #print("DEBUG INFO: Install Package RESULT \n{0}\n.".format(std_out.decode(sys.getfilesystemencoding())))
    else:
        print("WARNING: Could not install {0} - pip module is not installed.".format(package))

def install_ldraw_addon(argv):
    """Install LDraw Render addons"""
    
    arg_parser = BlenderArgumentParser(description='Install LPub3D Blender addon.')
    arg_parser.add_argument("-r", "--disable_ldraw_render", action="store_true", help="Disable the LPub3D render addon menu action in Blender")
    arg_parser.add_argument("-i", "--disable_ldraw_import", action="store_true", help="Disable the LPub3D import addon menu action in Blender")
    arg_parser.add_argument("-a", "--disable_ldraw_addons", action="store_true", help="Disable the LPub3D import and render addon menu actions in Blender")

    args = arg_parser.parse_args()

    # Confirm minimum Blender version
    is_blender_28_or_later = bpy.app.version >= (2, 80, 0)
    if not is_blender_28_or_later:
        print("ERROR: This addon requires Blender 2.80 or greater.")
        return {'FINISHED'}

    print("INFO: Installing LDraw Addon...")

    # Define path to LPub3D Import LDraw script
    path_to_script_dir = os.getcwd()

    # Define path to LPub3D Import LDraw addon bundle
    path_to_addon_dir: Union[bytes, str] = os.path.join(path_to_script_dir, "addons")

    # Set the list of the addon bundles in the addon path.
    addon_file_list = sorted(os.listdir(path_to_addon_dir))
    for addon_file in addon_file_list:
        print("ADDON FILE:         {0}".format(addon_file))
        path_to_addon = os.path.join(path_to_addon_dir, addon_file)
        if is_blender_28_or_later:
            bpy.ops.preferences.addon_install(overwrite=True, filter_folder=True, target='DEFAULT',
                                              filepath=path_to_addon, filter_python=True, filter_glob='*.py;*.zip')
        else:
            bpy.ops.wm.addon_install(overwrite=True, filter_folder=True, target='DEFAULT',
                                     filepath=path_to_addon, filter_python=True, filter_glob='*.py;*.zip')    

    # Set the list of addon modules in the LPub3D 'addons' folder.
    addon_module_list: Set[str] = {'io_scene_lpub3d_importldraw', 'io_scene_lpub3d_renderldraw'}

    # Enable addon modules. addon_module
    for addon_module in addon_module_list:
        if addon_module == "io_scene_lpub3d_importldraw" and (args.disable_ldraw_import or args.disable_ldraw_addons):
            for mod in addon_utils.modules():
                if mod.bl_info.get("name", "") == "LPub3D Import LDraw":
                    bpy.ops.preferences.addon_disable(module=addon_module)
                    break
            print("INFO: LPub3D Import LDraw disabled")
            continue
        if addon_module == "io_scene_lpub3d_renderldraw" and (args.disable_ldraw_render or args.disable_ldraw_addons):
            for mod in addon_utils.modules():
                if mod.bl_info.get("name", "") == "LPub3D Render LDraw":
                    bpy.ops.preferences.addon_disable(module=addon_module)
                    break
            print("INFO: LPub3D Render LDraw disabled")
            continue
        print("ADDON MODULE ENABLED:   {0}".format(addon_module))
        if is_blender_28_or_later:
            bpy.ops.preferences.addon_enable(module=addon_module)
        else:
            bpy.ops.wm.addon_enable(module=addon_module)

    # Save user preferences
    bpy.ops.wm.save_userpref()

    # Install Pillow
    install_package('Pillow')

    # Get 'LPub3D Render LDraw' addon version
    for mod in addon_utils.modules():
        if mod.bl_info.get("name", "") == "LPub3D Render LDraw":
            addon_version = mod.bl_info.get('version', (-1, -1, -1))
            print("ADDON VERSION: {0}".format(".".join(map(str, addon_version))))
            break

    # Set LDraw directory in default preference file
    blender_addons_path = bpy.utils.user_resource('SCRIPTS', path="addons")
    pref_file = os.path.join(blender_addons_path, "io_scene_lpub3d_importldraw/ImportLDrawPreferences.ini")
    prefs = Preferences(pref_file.replace("/", os.path.sep))
    ldraw_path = os.environ.get('LDRAW_DIRECTORY')
    if ldraw_path.__ne__(""):
        prefs.set('ldrawDirectory', ldraw_path)
        prefs.save()

    # Export paths to standard out
    environment_file   = os.path.join(blender_addons_path, "io_scene_lpub3d_importldraw/loadldraw/background.exr")
    lsynth_directory   = os.path.join(blender_addons_path, "io_scene_lpub3d_importldraw/lsynth")
    studlogo_directory = os.path.join(blender_addons_path, "io_scene_lpub3d_importldraw/studs")
    print("DATA: ENVIRONMENT_FILE: {0}".format(environment_file.replace("/", os.path.sep)))
    print("DATA: LSYNTH_DIRECTORY: {0}".format(lsynth_directory).replace("/", os.path.sep))
    print("DATA: STUDLOGO_DIRECTORY: {0}".format(studlogo_directory).replace("/", os.path.sep))

    print("INFO: LDraw Addons installed.")


if __name__ == '__main__':
    install_ldraw_addon(sys.argv[1:])
