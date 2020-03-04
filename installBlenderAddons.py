# -*- coding: utf-8 -*-
"""
Trevor SANDY
Last Update March 04, 2020
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
import subprocess
import configparser

from typing import Union, Set


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


def installPackage(package):
    """Install Pillow module"""

    import importlib
    package_spec = importlib.util.find_spec("pip")
    if package_spec is not None:
        print("INFO: Installing Pillow...")
        import pip
        pybin = bpy.app.binary_path_python
        subprocess.check_call([pybin, '-m', 'pip', 'install', '--user', '--no-deps', package])
    else:
        print("WARNING: Could not install {0} - pip module is not installed.".format(package))

def install_addons():
    """Install LDraw Render addons"""

    print("INFO: Installing Addons...")

    tup = 0
    if hasattr(bpy.app, "version"):
        tup = bpy.app.version
    is_blender_28_or_later = tup >= (2, 80)

    # Define path to LPub3D Import LDraw script
    path_to_script_dir = os.getcwd()

    # Define path to LPub3D Import LDraw add-on bundle
    path_to_addon_dir: Union[bytes, str] = os.path.join(path_to_script_dir, "addons")

    # Define a list of the files in this add-on folder.
    file_list = sorted(os.listdir(path_to_addon_dir))

    for file in file_list:
        print('ADDON FILE:         ' + file)

    # Specify the path of each addon.
    for file in file_list:
        path_to_file = os.path.join(path_to_addon_dir, file)
        if is_blender_28_or_later:
            bpy.ops.preferences.addon_install(overwrite=True, filter_folder=True, target='DEFAULT',
                                              filepath=path_to_file, filter_python=True, filter_glob='*.py;*.zip')
        else:
            bpy.ops.wm.addon_install(overwrite=True, filter_folder=True, target='DEFAULT',
                                     filepath=path_to_file, filter_python=True, filter_glob='*.py;*.zip')

    # Specify which add-ons to enable.
    enable_these_addons: Set[str] = {'io_scene_lpub3d_importldraw', 'io_scene_lpub3d_renderldraw'}

    # Enable addons.
    for string in enable_these_addons:
        print('ENABLE THIS ADDON:   ' + string)
        if is_blender_28_or_later:
            bpy.ops.preferences.addon_enable(module=string)
        else:
            bpy.ops.wm.addon_enable(module=string)

    # Save user preferences
    bpy.ops.wm.save_userpref()

    # Install Pillow
    installPackage('Pillow')

    # Get 'LPub3D Render LDraw' addon version
    for mod in addon_utils.modules():
        if mod.bl_info.get("name", "") == "LPub3D Render LDraw":
            version = mod.bl_info.get('version', (-1, -1, -1))
            print("ADDON VERSION: {0}".format(".".join(map(str, version))))
            break

    # Set LDraw directory in default preference file
    addons_path = bpy.utils.user_resource('SCRIPTS', "addons")
    pref_file = os.path.join(addons_path, "io_scene_lpub3d_importldraw/ImportLDrawPreferences.ini")
    prefs = Preferences(pref_file.replace("/", os.path.sep))
    ldraw_path = os.environ.get('LDRAW_DIRECTORY')
    if ldraw_path.__ne__(""):
        prefs.set('ldrawDirectory', ldraw_path)
        prefs.save()

    # Export paths partName = filename.replace("\\", os.path.sep)
    environment_file   = os.path.join(addons_path, "io_scene_lpub3d_importldraw/loadldraw/background.exr")
    lsynth_directory   = os.path.join(addons_path, "io_scene_lpub3d_importldraw/lsynth")
    studlogo_directory = os.path.join(addons_path, "io_scene_lpub3d_importldraw/studs")
    print("DATA: ENVIRONMENT_FILE: {0}".format(environment_file.replace("/", os.path.sep)))
    print("DATA: LSYNTH_DIRECTORY: {0}".format(lsynth_directory).replace("/", os.path.sep))
    print("DATA: STUDLOGO_DIRECTORY: {0}".format(studlogo_directory).replace("/", os.path.sep))

    print("INFO: LDraw Addons installed.")


if __name__ == '__main__':
    install_addons()
