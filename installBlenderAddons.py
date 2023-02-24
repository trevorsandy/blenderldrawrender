# -*- coding: utf-8 -*-
"""
Trevor SANDY
Last Update February 24, 2023
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
<blender path>/blender --background --python installBlenderAddons.py -- -xi

"""

import os
import sys
import subprocess
import argparse
import configparser
import json
from ast import literal_eval
from typing import Union, Set
from pathlib import Path
from shutil import rmtree
from shutil import copyfile
import addon_utils
import bpy


class BlenderArgumentParser(argparse.ArgumentParser):
    """Consume command line arguments after '--'"""

    def _argv_after_doubledash(self):
        try:
            arg_index = sys.argv.index("--")
            return sys.argv[arg_index+1:]  # arguments after '--'
        except ValueError as e:
            return []

    def parse_args(self):                # overrides superclass
        return super().parse_args(args=self._argv_after_doubledash())


class Preferences():
    """Import LDraw - Preferences"""

    __sectionName = 'ImportLDraw'

    def __init__(self, lpubpreferencesfile, preferencesfile, sectionkey):

        self.__sectionkey = sectionkey
        if self.__sectionkey == "MM":
            self.__sectionName = 'ImportLDrawMM'
        assert preferencesfile != "", "Preferences file path was not specified."
        self.__prefsFilepath = lpubpreferencesfile

        self.__config = configparser.RawConfigParser()
        self.__prefsRead = self.__config.read(self.__prefsFilepath)
        if self.__prefsRead and not self.__config[self.__sectionName]:
            self.__prefsRead = False

        for section in self.__config.sections():
            if section != self.__sectionName:
                self.__config.remove_section(section)

        self.__prefsFilepath = preferencesfile

        self.__default_settings = {}
        if self.__sectionkey == "MM":
            self.__settings = dict()
            self.__default_settings = {
                'add_environment': self.__config[self.__sectionName]['addenvironment'],
                'additional_search_paths': self.__config[self.__sectionName]['additionalsearchpaths'],
                'blend_file': self.__config[self.__sectionName]['blendfile'],
                'blendfile_trusted': self.__config[self.__sectionName]['blendfiletrusted'],
                'chosen_logo': self.__config[self.__sectionName]['chosenlogo'],
                'crop_image': self.__config[self.__sectionName]['cropimage'],
                'custom_ldconfig_file': self.__config[self.__sectionName]['customldconfigfile'],
                'display_logo': self.__config[self.__sectionName]['displaylogo'],
                'environment_file': self.__config[self.__sectionName]['environmentfile'],
                'frames_per_step': self.__config[self.__sectionName]['framesperstep'],
                'gap_scale': self.__config[self.__sectionName]['gapscale'],
                'gap_scale_strategy': self.__config[self.__sectionName]['gapscalestrategy'],
                'gap_target': self.__config[self.__sectionName]['gaptarget'],
                'import_cameras': self.__config[self.__sectionName]['importcameras'],
                'import_edges': self.__config[self.__sectionName]['importedges'],
                'import_lights': self.__config[self.__sectionName]['importlights'],
                'import_scale': self.__config[self.__sectionName]['importscale'],
                'ldraw_path': self.__config[self.__sectionName]['ldrawpath'],
                'make_gaps': self.__config[self.__sectionName]['makegaps'],
                'merge_distance': self.__config[self.__sectionName]['mergedistance'],
                'meta_bfc': self.__config[self.__sectionName]['metabfc'],
                'meta_clear': self.__config[self.__sectionName]['metaclear'],
                'meta_group': self.__config[self.__sectionName]['metagroup'],
                'meta_pause': self.__config[self.__sectionName]['metapause'],
                'meta_print_write': self.__config[self.__sectionName]['metaprintwrite'],
                'meta_save': self.__config[self.__sectionName]['metasave'],
                'meta_step': self.__config[self.__sectionName]['metastep'],
                'meta_step_groups': self.__config[self.__sectionName]['metastepgroups'],
                'no_studs': self.__config[self.__sectionName]['nostuds'],
                'overwrite_image': self.__config[self.__sectionName]['overwriteimage'],
                'parent_to_empty': self.__config[self.__sectionName]['parenttoempty'],
                'prefer_studio': self.__config[self.__sectionName]['preferstudio'],
                'prefer_unofficial': self.__config[self.__sectionName]['preferunofficial'],
                'preserve_hierarchy': self.__config[self.__sectionName]['preservehierarchy'],
                'profile': self.__config[self.__sectionName]['profile'],
                'recalculate_normals': self.__config[self.__sectionName]['recalculatenormals'],
                'remove_doubles': self.__config[self.__sectionName]['removedoubles'],
                'render_percentage': self.__config[self.__sectionName]['renderpercentage'],
                'render_window': self.__config[self.__sectionName]['renderwindow'],
                'resolution': self.__config[self.__sectionName]['resolution'],
                'resolution_height': self.__config[self.__sectionName]['resolutionheight'],
                'resolution_width': self.__config[self.__sectionName]['resolutionwidth'],
                'search_additional_paths': self.__config[self.__sectionName]['searchadditionalpaths'],
                'set_end_frame': self.__config[self.__sectionName]['setendframe'],
                'set_timeline_markers': self.__config[self.__sectionName]['settimelinemarkers'],
                'shade_smooth': self.__config[self.__sectionName]['shadesmooth'],
                'smooth_type': self.__config[self.__sectionName]['smoothtype'],
                'starting_step_frame': self.__config[self.__sectionName]['startingstepframe'],
                'studio_ldraw_path': self.__config[self.__sectionName]['studioldrawpath'],
                'transparent_background': self.__config[self.__sectionName]['transparentbackground'],
                'treat_models_with_subparts_as_parts': self.__config[self.__sectionName]['treatmodelswithsubpartsasparts'],
                'treat_shortcut_as_model': self.__config[self.__sectionName]['treatshortcutasmodel'],
                'triangulate': self.__config[self.__sectionName]['triangulate'],
                'use_colour_scheme': self.__config[self.__sectionName]['usecolourscheme'],
                'use_freestyle_edges': self.__config[self.__sectionName]['usefreestyleedges'],
                'verbose': self.__config[self.__sectionName]['verbose']
            }

    def set(self, option, value):
        if self.__sectionName not in self.__config:
            self.__config[self.__sectionName] = {}
        self.__config[self.__sectionName][option] = str(value)

    def save(self):
        if self.__sectionkey == "MM":
            self.__settings = {}
            for k, v in self.__default_settings.items():
                value = self.__config[self.__sectionName][k.replace("_", "").lower()]
                self.__settings[k] = self.evaluate_value(value)
            self.write_json()
        else:
            self.write_ini()

    def write_ini(self):
        try:
            folder = os.path.dirname(self.__prefsFilepath)
            Path(folder).mkdir(parents=True, exist_ok=True)
            with open(self.__prefsFilepath, 'w', encoding='utf-8', newline="\n") as configfile:
                self.__config.write(configfile)
            return True
        except OSError as e:
            print(f"WARNING: Could not save INI preferences. I/O error({e.errno}): {e.strerror}")
        except Exception:
            print(f"WARNING: Could not save INI preferences. Unexpected error: {sys.exc_info()[0]}")
        return False

    def write_json(self):
        try:
            folder = os.path.dirname(self.__prefsFilepath)
            Path(folder).mkdir(parents=True, exist_ok=True)
            with open(self.__prefsFilepath, 'w', encoding='utf-8', newline="\n") as configfile:
                configfile.write(json.dumps(self.__settings, indent=2))
            return True
        except OSError as e:
            print(f"WARNING: Could not save JSON preferences. I/O error({e.errno}): {e.strerror}")
        except Exception:
            print(f"WARNING: Could not save JSON preferences. Unexpected error: {sys.exc_info()[0]}")
        return False

    def copy_ldraw_parameters(self, ldraw_parameters_file, addon_ldraw_parameters_file):
        try:
            copyfile(ldraw_parameters_file, addon_ldraw_parameters_file)
        except IOError as e:
            print(f"WARNING: Could not Copy LDraw parameters. I/O error({e.errno}): {e.strerror}")

    def evaluate_value(self, x):
        if x == 'True':
            return True
        elif x == 'False':
            return False
        elif self.is_int(x):
            return int(x)
        elif self.is_float(x):
            return float(x)
        else:
            return x

    def is_float(self, x):
        try:
            f = float(x)
        except (TypeError, ValueError):
            return False
        else:
            return True

    def is_int(self, x):
        try:
            f = float(x)
            i = int(f)
        except (TypeError, ValueError):
            return False
        else:
            return f == i


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
        pipes = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        std_out, std_err = pipes.communicate()
        args = [pybin, "-m", "pip", "install", "--user",
                "--no-deps", "--no-warn-script-location", package]
        if pipes.returncode != 0:
            err_msg = f"ERROR: {std_err.strip()}. Code: {pipes.returncode}"
            raise Exception(err_msg)
        elif std_err:
            if "A new release of pip is available" in std_err.decode(sys.getfilesystemencoding()) or \
               "You are using pip version" in std_err.decode(sys.getfilesystemencoding()):
                args = [pybin, "-m", "pip", "install", "--user", "--upgrade",
                        "pip", "--no-deps", "--no-warn-script-location", package]
                print(f"INFO: Upgrading {package}...")
        else:
            print(f"INFO: Installing {package}...")
        #print("DEBUG INFO: PIP LIST: \n{0}.\n".format(std_out.decode(sys.getfilesystemencoding())))
        pipes = subprocess.Popen(
            args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        std_out, std_err = pipes.communicate()
        if pipes.returncode != 0:
            err_msg = f"ERROR: {std_err.strip()}. Code: {pipes.returncode}"
            raise Exception(err_msg)
        elif std_err:
            print(f"WARNING: {std_err.decode(sys.getfilesystemencoding())}")
        #print("DEBUG INFO: Install Package RESULT \n{0}\n.".format(std_out.decode(sys.getfilesystemencoding())))
    else:
        print(f"WARNING: Could not install {package} - pip module is not installed.")


def install_ldraw_addon(argv):
    """Install LDraw Render addons"""

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

    args = arg_parser.parse_args()

    # Confirm minimum Blender version
    is_blender_28_or_later = bpy.app.version >= (2, 82, 0)
    if not is_blender_28_or_later:
        print("ERROR: This addon requires Blender 2.80 or greater.")
        return {'FINISHED'}

    print("INFO: Installing LDraw Addon...")

    # Define path to LPub3D Import LDraw script
    install_script_path = os.getcwd()

    # Define path to LPub3D Import LDraw addon bundle
    install_addon_path: Union[bytes, str] = os.path.join(
        install_script_path, "addons")

    # Set the list of the addon bundles in the addon path.
    addon_file_list = sorted(os.listdir(install_addon_path))
    for addon_file in addon_file_list:
        print(f"ADDON FILE:         {addon_file}")
        addon_filepath = os.path.join(install_addon_path, addon_file)
        if is_blender_28_or_later:
            bpy.ops.preferences.addon_install(overwrite=True, filter_folder=True, target='DEFAULT',
                                              filepath=addon_filepath, filter_python=True, filter_glob='*.py;*.zip')

    # Set the list of addon modules in the LPub3D 'addons' folder.
    addon_module_list: Set[str] = {'io_scene_lpub3d_importldraw',
                                   'io_scene_lpub3d_importldraw_mm',
                                   'io_scene_lpub3d_renderldraw'}

    # Enable addon modules. addon_module
    for addon_module in addon_module_list:
        if addon_module == 'io_scene_lpub3d_importldraw' and (args.disable_ldraw_import or args.disable_ldraw_addons):
            for addon in bpy.context.preferences.addons:
                if addon.module == addon_module:
                    bpy.ops.preferences.addon_disable(module=addon_module)
                    print("INFO: LPub3D Import LDraw disabled")
                    break
            continue
        if addon_module == 'io_scene_lpub3d_importldraw_mm' and (args.disable_ldraw_import_mm or args.disable_ldraw_addons):
            for addon in bpy.context.preferences.addons:
                if addon.module == addon_module:
                    bpy.ops.preferences.addon_disable(module=addon_module)
                    print("INFO: LPub3D Import LDraw MM disabled")
                    break
            continue
        if addon_module == 'io_scene_lpub3d_renderldraw' and (args.disable_ldraw_render or args.disable_ldraw_addons):
            for addon in bpy.context.preferences.addons:
                if addon.module == addon_module:
                    bpy.ops.preferences.addon_disable(module=addon_module)
                    print("INFO: LPub3D Render LDraw disabled")
                    break
            continue
        print(f"ADDON MODULE ENABLED:   {addon_module}")
        bpy.ops.preferences.addon_enable(module=addon_module)

    # Save user preferences
    bpy.ops.wm.save_userpref()

    # Install Pillow
    install_package('Pillow')

    # Get 'LPub3D Render LDraw' addon version
    for addon in addon_utils.modules():
        if addon.bl_info.get("name", "") == "LPub3D Render LDraw":
            addon_version = addon.bl_info.get('version', (-1, -1, -1))
            print("ADDON VERSION: {0}".format(
                  ".".join(map(str, addon_version))))
            break

    # Addon installation folder
    blender_addons_path = bpy.utils.user_resource('SCRIPTS', path="addons")

    # Set LDraw directory in default preference file
    config_file = os.path.join(
        install_script_path, "config/LDrawRendererPreferences.ini")
    pref_file = os.path.join(
        blender_addons_path, "io_scene_lpub3d_importldraw/config/ImportLDrawPreferences.ini")
    prefs = Preferences(config_file.replace('/', os.path.sep),
                        pref_file.replace('/', os.path.sep), 'TN')
    ldraw_path = os.environ.get('LDRAW_DIRECTORY')
    if ldraw_path != "":
        prefs.set('ldrawdirectory', ldraw_path)
    prefs.save()
    pref_file = os.path.join(
        blender_addons_path, "io_scene_lpub3d_importldraw_mm/config/ImportOptions.json")
    prefs = Preferences(config_file.replace('/', os.path.sep),
                        pref_file.replace('/', os.path.sep), 'MM')
    if ldraw_path != "":
        prefs.set('ldrawpath', ldraw_path)
    prefs.save()

    # Copy LDraw Parameters
    ldraw_parameters_file = os.path.join(
        install_script_path, "config/BlenderLDrawParameters.lst")
    addon_ldraw_parameters_file = os.path.join(
        blender_addons_path, "io_scene_lpub3d_renderldraw/config/LDrawParameters.lst")
    prefs.copy_ldraw_parameters(ldraw_parameters_file, addon_ldraw_parameters_file)

    # Cleanup pycache
    for addon_module in addon_module_list:
        addon_module_path = os.path.join(blender_addons_path, addon_module)
        pycache_path = os.path.join(addon_module_path, '__pycache__')
        if os.path.isdir(pycache_path):
            rmtree(pycache_path)

    if (not args.disable_ldraw_import and not args.disable_ldraw_addons):
        # Export paths to standard out
        environment_file = os.path.join(
            blender_addons_path, "io_scene_lpub3d_importldraw/loadldraw/background.exr")
        lsynth_directory = os.path.join(
            blender_addons_path, "io_scene_lpub3d_importldraw/lsynth")
        studlogo_directory = os.path.join(
            blender_addons_path, "io_scene_lpub3d_importldraw/studs")
        print(f"DATA: ENVIRONMENT_FILE: {environment_file.replace('/', os.path.sep)}")
        print(f"DATA: LSYNTH_DIRECTORY: {lsynth_directory.replace('/', os.path.sep)}")
        print(f"DATA: STUDLOGO_DIRECTORY: {studlogo_directory.replace('/', os.path.sep)}")

    print("INFO: LDraw Addons installed.")


if __name__ == '__main__':
    install_ldraw_addon(sys.argv[1:])
