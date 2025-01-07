import os
import sys
import json
import copy
import datetime
import zipfile
import configparser
from pathlib import Path
from shutil import copyfile

class Preferences():
    """Marshall LDraw Blender addon settings."""

    __sectionKey = "TN"
    __sectionName = "ImportLDraw"
    __updateIni = False
    __configFile = None
    __timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-4]
    __importPath = os.path.abspath(os.path.join(Path(__file__).parent, "..", "io_scene_import_ldraw"))
    __importMMPath = os.path.abspath(os.path.join(Path(__file__).parent, "..", "io_scene_import_ldraw_mm"))
    __defaultPrefsFile = os.path.join(__importPath, "config", "ImportLDrawPreferences.ini")
    __defaultMMPrefsFile = os.path.join(__importMMPath, "config", "ImportOptions.json")
    __defaultConfigFile = os.path.join(os.path.dirname(__file__), "config", "LDrawRendererPreferences.ini")


    def __init__(self, configfile=None, prefsfile=None, sectionkey=None):
        if sectionkey.__ne__(None):
            self.__sectionKey = sectionkey
        if self.__sectionKey == "MM":
            self.__sectionName = "ImportLDrawMM"
        if prefsfile.__ne__(None) and os.path.isfile(prefsfile):
            self.__prefsFile = prefsfile
        elif self.__sectionKey == "TN":
            self.__prefsFile = self.__defaultPrefsFile
        elif self.__sectionKey == "MM":
            self.__prefsFile = self.__defaultMMPrefsFile
        
        assert self.__prefsFile != "", "Import Preferences file was not specified."

        if configfile.__ne__(None) and os.path.isfile(configfile):
            self.__configFile = configfile
        elif os.path.isfile(self.__defaultConfigFile):
            self.__configFile = self.__defaultConfigFile
        else:
            self.__configFile = self.__defaultPrefsFile

        assert self.__configFile != "", "Configuration Preferences file was not specified."

        self.__config = configparser.RawConfigParser()
        self.__prefsRead = self.__config.read(self.__configFile)
        if self.__prefsRead and self.__sectionName not in self.__config:
            self.__prefsRead = False

        # When self.__configFile includes attributes from an older version that has been
        # changed or removed, or if the Python addon version is newer than the version
        # defined in the calling application, the following attributes are updated.
        # Version 1.5 and later attribute updates:
        for section in self.__config.sections():
            if section == "ImportLDraw":
                addList = ['realgapwidth,0.0002', 'realscale,1.0']
                for addItem in addList:
                    pair = addItem.split(",")
                    if not self.__config.has_option(section, pair[0]):
                        self.__config.set(section, pair[0], str(pair[1]))
                        self.__updateIni = True
                popList = ['gapwidth', 'scale']
                for popItem in popList:
                    if self.__config.has_option(section, popItem):
                        self.__config[section].pop(popItem)
                        self.__updateIni = True
            elif section == "ImportLDrawMM":
                addList = ['studiocustompartspath,', 'scalestrategy,mesh']
                addList += ['casesensitivefilesystem,True'] if sys.platform == "linux" else ['casesensitivefilesystem,False']
                for addItem in addList:
                    pair = addItem.split(",")
                    if not self.__config.has_option(section, pair[0]):
                        if (len(pair) == 1):
                            pair.append('')
                        self.__config.set(section, pair[0], str(pair[1]))
                        self.__updateIni = True
                popList = ['preservehierarchy', 'treatmodelswithsubpartsasparts', 'colorstrategy', 'gapscalestrategy', 'gaptarget']
                for popItem in popList:
                    if self.__config.has_option(section, popItem):
                        self.__config[section].pop(popItem)
                        self.__updateIni = True

        if self.__updateIni:
            self.save_config_ini()

        self.__ini = self.__sectionName in self.__config

        self.__config_mm = {}

        if self.__sectionKey == "MM" and self.__ini:
            self.__config_mm = {
                'add_environment': self.__config[self.__sectionName]['addenvironment'],
                'additional_search_paths': self.__config[self.__sectionName]['additionalsearchpaths'],
                'bevel_edges': self.__config[self.__sectionName]['beveledges'],
                'bevel_segments': self.__config[self.__sectionName]['bevelsegments'],
                'bevel_weight': self.__config[self.__sectionName]['bevelweight'],
                'bevel_width': self.__config[self.__sectionName]['bevelwidth'],
                'blend_file': self.__config[self.__sectionName]['blendfile'],
                'blendfile_trusted': self.__config[self.__sectionName]['blendfiletrusted'],
                'camera_border_percent': self.__config[self.__sectionName]['cameraborderpercent'],
                'case_sensitive_filesystem': self.__config[self.__sectionName]['casesensitivefilesystem'],
                'chosen_logo': self.__config[self.__sectionName]['chosenlogo'],
                'crop_image': self.__config[self.__sectionName]['cropimage'],
                'custom_ldconfig_file': self.__config[self.__sectionName]['customldconfigfile'],
                'display_logo': self.__config[self.__sectionName]['displaylogo'],
                'environment_file': self.__config[self.__sectionName]['environmentfile'],
                'frames_per_step': self.__config[self.__sectionName]['framesperstep'],
                'gap_scale': self.__config[self.__sectionName]['gapscale'],
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
                'meta_texmap': self.__config[self.__sectionName]['metatexmap'],
                'no_studs': self.__config[self.__sectionName]['nostuds'],
                'overwrite_image': self.__config[self.__sectionName]['overwriteimage'],
                'parent_to_empty': self.__config[self.__sectionName]['parenttoempty'],
                'position_camera': self.__config[self.__sectionName]['positioncamera'],
                'prefer_studio': self.__config[self.__sectionName]['preferstudio'],
                'prefer_unofficial': self.__config[self.__sectionName]['preferunofficial'],
                'profile': self.__config[self.__sectionName]['profile'],
                'recalculate_normals': self.__config[self.__sectionName]['recalculatenormals'],
                'remove_doubles': self.__config[self.__sectionName]['removedoubles'],
                'render_percentage': self.__config[self.__sectionName]['renderpercentage'],
                'render_window': self.__config[self.__sectionName]['renderwindow'],
                'resolution': self.__config[self.__sectionName]['resolution'],
                'resolution_height': self.__config[self.__sectionName]['resolutionheight'],
                'resolution_width': self.__config[self.__sectionName]['resolutionwidth'],
                'scale_strategy': self.__config[self.__sectionName]['scalestrategy'],
                'search_additional_paths': self.__config[self.__sectionName]['searchadditionalpaths'],
                'set_end_frame': self.__config[self.__sectionName]['setendframe'],
                'set_timeline_markers': self.__config[self.__sectionName]['settimelinemarkers'],
                'shade_smooth': self.__config[self.__sectionName]['shadesmooth'],
                'smooth_type': self.__config[self.__sectionName]['smoothtype'],
                'starting_step_frame': self.__config[self.__sectionName]['startingstepframe'],
                'studio_custom_parts_path': self.__config[self.__sectionName]['studiocustompartspath'],
                'studio_ldraw_path': self.__config[self.__sectionName]['studioldrawpath'],
                'transparent_background': self.__config[self.__sectionName]['transparentbackground'],
                'treat_shortcut_as_model': self.__config[self.__sectionName]['treatshortcutasmodel'],
                'triangulate': self.__config[self.__sectionName]['triangulate'],
                'use_archive_library': self.__config[self.__sectionName]['usearchivelibrary'],
                'use_colour_scheme': self.__config[self.__sectionName]['usecolourscheme'],
                'use_freestyle_edges': self.__config[self.__sectionName]['usefreestyleedges'],
                'verbose': self.__config[self.__sectionName]['verbose']
            }
        else:
            self.__config_mm = self.read_json(self.__defaultMMPrefsFile)

        self.evaluate_ldraw_path()


    def evaluate_ldraw_path(self):
        if self.__sectionKey == "MM":
            key = "use_archive_library"
            use_archive_library = self.get_type(self.__config_mm[key])
        else:
            key = "usearchivelibrary"
            use_archive_library = self.__config.getboolean(self.__sectionName, key)
        if not use_archive_library:
            if self.__sectionKey == "MM":
                ldraw_path = self.__config_mm.get("ldraw_path")
            else:
                ldraw_path = self.__config.get(self.__sectionName, "ldrawdirectory")
            if ldraw_path != "":
                valid_config = os.path.isfile(os.path.join(ldraw_path,"LDConfig.ldr"))
                valid_primitive = os.path.isfile(os.path.join(ldraw_path, "p", "1-4cyli.dat"))
                if not valid_config and not valid_primitive:
                    for library_name in os.listdir(ldraw_path):
                        if library_name.endswith(".zip") or library_name.endswith(".bin"):
                            library_path = os.path.join(ldraw_path, library_name)
                            with zipfile.ZipFile(library_path) as library:
                                if "ldraw/LDConfig.ldr" in library.namelist() and \
                                    "ldraw/p/1-4cyli.dat" in library.namelist():
                                    use_archive_library = True
                                    break
                    if use_archive_library:
                        if self.__sectionKey == "MM":
                            self.__config_mm[key] = str(True) if self.__ini else True
                        else:
                            self.__config[self.__sectionName][key] = str(True)
                    else:
                        self.preferences_print(f"WARNING: '{ldraw_path}' may not be a valid LDraw library")


    def preferences_print(self, message, is_error=False):
        """Print output with identification timestamp."""
        message = f"{self.__timestamp} [renderldraw] {message}"
        if is_error:
            sys.stderr.write(f"{message}\n")
            sys.stderr.flush()
        else:
            sys.stdout.write(f"{message}\n")
            sys.stdout.flush()


    def get(self, option, default):
        if self.__sectionKey == "MM":
            return self.get_type(self.__config_mm[option])
        else:
            if not self.__prefsRead:
                return default
            if type(default) is bool:
                return self.__config.getboolean(self.__sectionName, option, fallback=default)
            elif type(default) is float:
                return self.__config.getfloat(self.__sectionName, option, fallback=default)
            elif type(default) is int:
                return self.__config.getint(self.__sectionName, option, fallback=default)
            else:
                return self.__config.get(self.__sectionName, option, fallback=default)


    def set(self, option, value):
        if self.__sectionKey == "MM":
            self.__config_mm[option] = str(value) if self.__ini else value
        else:
            if self.__sectionName not in self.__config:
                self.__config[self.__sectionName] = {}
            self.__config[self.__sectionName][option] = str(value)


    def save(self):
        """Save the current configuration settings."""
        if self.__sectionKey == "MM":
            self.__settings = {}
            for k, v in self.__config_mm.items():
                self.__settings[k] = self.get_type(v) if self.__ini else v
            return self.write_json()
        else:
            return self.write_ini()


    def save_config_ini(self):
        """Save LDraw configuration settings if attributes updated."""
        if self.__updateIni:
            savePrefsFile = self.__prefsFile
            self.__prefsFile = self.__configFile
            result = self.write_ini(configini=True)
            self.__prefsFile = savePrefsFile
            self.__updateIni = False
            return result


    def write_ini(self, configini=False):
        try:
            folder = os.path.dirname(self.__prefsFile)
            Path(folder).mkdir(parents=True, exist_ok=True)
            config = copy.deepcopy(self.__config)
            if not configini:
                for section in config.sections():
                    if section != self.__sectionName:
                        config.remove_section(section)
            with open(self.__prefsFile, 'w', encoding='utf-8', newline="\n") as configFile:
                config.write(configFile,False)
            return True
        except OSError as e:
            self.preferences_print(f"ERROR: Could not save INI preferences. I/O error({e.errno}): {e.strerror}", True)
        except Exception:
            self.preferences_print(f"ERROR: Could not save INI preferences. Unexpected error: {sys.exc_info()[0]}", True)
        return False


    def write_json(self):
        try:
            folder = os.path.dirname(self.__prefsFile)
            Path(folder).mkdir(parents=True, exist_ok=True)
            with open(self.__prefsFile, 'w', encoding='utf-8', newline="\n") as configFile:
                configFile.write(json.dumps(self.__settings, indent=2))
            return True
        except OSError as e:
            self.preferences_print(f"ERROR: Could not save JSON preferences. OS error({e.errno}): {e.strerror}", True)
        except Exception:
            self.preferences_print(f"ERROR: Could not save JSON preferences. Unexpected error: {sys.exc_info()[0]}", True)
        return False
    

    def read_json(self, filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return json.load(file)
        except Exception as e:
            self.preferences_print(f"ERROR: ({e})", True)
            import traceback
            print(traceback.format_exc())
            empty_config_mm = {}
            return empty_config_mm


    def copy_ldraw_parameters(self, ldraw_parameters_file, addon_ldraw_parameters_file):
        try:
            copyfile(ldraw_parameters_file, addon_ldraw_parameters_file)
        except IOError as e:
            self.preferences_print(f"WARNING: Could not Copy LDraw parameters. I/O error({e.errno}): {e.strerror}")


    def getEnvironmentFile(self):
        return os.path.abspath(os.path.join(self.__importPath, 'loadldraw', 'background.exr'))


    def getLSynthPath(self):
        return os.path.abspath(os.path.join(self.__importPath, 'lsynth'))


    def getLStudsPath(self):
        return os.path.abspath(os.path.join(self.__importPath, 'studs'))


    def get_type(self, x):
        if x == 'True':
            return True
        elif x == 'False':
            return False
        elif self.is_int(x):
            return int(x)
        elif self.is_float(x):
            return float(x)
        elif "\\" in x:
            return x.replace("\\\\", os.path.sep).replace("\\", os.path.sep)
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

    def importer(self):
        return self.__sectionName


if __name__ == "__main__":
    print("Marshall {0} LDraw Blender settings.".format(Preferences.importer()), end=f"\n{'-' * 34}\n")