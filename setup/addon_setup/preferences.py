import os
import sys
import json
import configparser
from pathlib import Path
from shutil import copyfile

from . import handle_fatal_error

class Preferences():
    """Marshall LDraw Blender settings."""

    __sectionkey = "TN"
    __sectionName = "ImportLDraw"

    def __init__(self, lpubpreferencesfile, preferencesfile, sectionkey):

        self.__sectionkey = sectionkey
        if self.__sectionkey == "MM":
            self.__sectionName = "ImportLDrawMM"
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
            handle_fatal_error(f"Could not save INI preferences. I/O error({e.errno}): {e.strerror}")
        except Exception:
            handle_fatal_error(f"Could not save INI preferences. Unexpected error: {sys.exc_info()[0]}")
        return False

    def write_json(self):
        try:
            folder = os.path.dirname(self.__prefsFilepath)
            Path(folder).mkdir(parents=True, exist_ok=True)
            with open(self.__prefsFilepath, 'w', encoding='utf-8', newline="\n") as configfile:
                configfile.write(json.dumps(self.__settings, indent=2))
            return True
        except OSError as e:
            print(f"Could not save JSON preferences. I/O error({e.errno}): {e.strerror}")
        except Exception:
            print(f"Could not save JSON preferences. Unexpected error: {sys.exc_info()[0]}")
        return False

    def copy_ldraw_parameters(self, ldraw_parameters_file, addon_ldraw_parameters_file):
        try:
            copyfile(ldraw_parameters_file, addon_ldraw_parameters_file)
        except IOError as e:
            print(f"Could not Copy LDraw parameters. I/O error({e.errno}): {e.strerror}")

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

    def importer(self):
        return self.__sectionName

if __name__ == "__main__":
    print("Marshall {0} LDraw Blender settings.".format(Preferences.importer()), end=f"\n{'-' * 34}\n")