import os
import string
import glob
from sys import platform
from pathlib import Path
from . import helpers

def locate_ldraw():
    ldraw_folder_name = 'ldraw'

    # home = os.path.expanduser("~")
    home = str(Path.home())
    ldraw_path = os.path.join(home, ldraw_folder_name)
    if os.path.isdir(ldraw_path):
        return ldraw_path

    # Get list of possible ldraw installation directories for the platform
    if platform == "win32":
        ldrawPossibleDirectories = [
        	os.path.join(os.environ['USERPROFILE'], "LDraw"),
        	os.path.join(os.environ['USERPROFILE'], os.path.join("Desktop", "LDraw")),
        	os.path.join(os.environ['USERPROFILE'], os.path.join("Documents", "LDraw")),
            os.path.join(os.environ["ProgramFiles"], "LDraw"),
            os.path.join(os.environ["ProgramFiles(x86)"], "LDraw"),
            os.path.join(f"{Path.home().drive}:{os.path.sep}", "LDraw"),
        ]
    elif platform == "darwin":
        ldrawPossibleDirectories = [
            "~/ldraw/",
            "/Applications/LDraw/",
            "/Applications/ldraw/",
            "/usr/local/share/ldraw",
        ]
    else:  # Default to Linux if not Windows or Mac
        ldrawPossibleDirectories = [
            "~/LDraw",
            "~/ldraw",
            "~/.LDraw",
            "~/.ldraw",
            "/usr/local/share/ldraw",
        ]

    # Search possible directories
    ldraw_path = ""
    for dir in ldrawPossibleDirectories:
        dir = os.path.expanduser(dir)
        if platform == "win32":
            if os.path.isfile(os.path.join(dir, "LDConfig.ldr")):
                ldraw_path = dir
                break
            for drive_letter in string.ascii_lowercase:
                drive, dir_tail = os.path.splitdrive(dir)
                dir = os.path.join(os.path.join(f"{drive_letter}:{os.path.sep}", dir_tail))
                if os.path.isfile(os.path.join(dir, "LDConfig.ldr")):
                    ldraw_path = dir
                    break
            if ldraw_path != "":
                break
        else:
            if os.path.isfile(os.path.join(dir, "LDConfig.ldr")):
                ldraw_path = dir
                break

    # Search LDRAW_DIRECTORY environment variable
    if ldraw_path == "":
        ldrawDir = os.environ.get('LDRAW_DIRECTORY')
        if ldrawDir is not None:
            dir = os.path.expanduser(ldrawDir).rstrip()
            if os.path.isfile(os.path.join(dir, "LDConfig.ldr")):
                ldraw_path = dir

    return ldraw_path

def locate_studio_ldraw():
    ldraw_folder_name = 'ldraw'

    if platform == "linux" or platform == "linux2":
        pass
        # linux
    elif platform == "darwin":
        pass
        # OS X
    elif platform == "win32":
        studio_path = os.path.join(os.environ["ProgramFiles"], 'Studio 2.0', ldraw_folder_name)
        if os.path.isdir(studio_path):
            return studio_path

        studio_path = os.path.join(os.environ["ProgramFiles(x86)"], 'Studio 2.0', ldraw_folder_name)
        if os.path.isdir(studio_path):
            return studio_path

    return ""


class FileSystem:
    defaults = {}

    defaults['ldraw_path'] = locate_ldraw()
    ldraw_path = defaults['ldraw_path']

    defaults['studio_ldraw_path'] = locate_studio_ldraw()
    studio_ldraw_path = defaults['studio_ldraw_path']
    
    defaults['environment_file'] = ''
    environment_file = defaults['environment_file']

    defaults['custom_ldconfig_file'] = ''
    custom_ldconfig_file = defaults['custom_ldconfig_file']

    defaults['additional_search_paths'] = ''
    additional_search_paths = defaults['additional_search_paths']

    defaults['prefer_studio'] = False
    prefer_studio = defaults['prefer_studio']

    defaults['prefer_unofficial'] = False
    prefer_unofficial = defaults['prefer_unofficial']

    defaults['search_additional_paths'] = False
    search_additional_paths = defaults['search_additional_paths']

    defaults['use_archive_library'] = False
    use_archive_library = defaults['use_archive_library']

    defaults['resolution'] = 'Standard'
    resolution = defaults['resolution']

    search_dirs = []
    lowercase_paths = {}

    @classmethod
    def reset_caches(cls):
        cls.search_dirs = []
        cls.lowercase_paths = {}

    @staticmethod
    def locate_environment_file():
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                    "../io_scene_import_ldraw/loadldraw/background.exr".replace("/", os.path.sep)))
        if os.path.exists(file_path):
            return file_path
        return ""

    @staticmethod
    def locate_parameters_file():
        file_path = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                    "../io_scene_render_ldraw/config/LDrawParameters.lst".replace("/", os.path.sep)))
        if os.path.exists(file_path):
            return file_path
        print(f"DEBUG:  WARNING parameters_file not Found: {file_path}")
        return ""

    @classmethod
    def read_lgeo_colors(cls):
        filename = cls.locate_parameters_file()
        
        lgeo_colours = {}

        if  filename != "":
            with open(filename, "rt", encoding="utf_8") as parameters_file:
                for line in helpers.valid_lines(parameters_file):
                    line_split = line.replace(" ", "").rstrip().split(",")
                    item = line_split[0]
                    # LGEO is a parts library for rendering LEGO using the povray rendering software.
                    # It has a list of LEGO colours suitable for realistic rendering.
                    # I've extracted the following colours from the LGEO file: lg_color.inc
                    # LGEO is downloadable from http://ldraw.org/downloads-2/downloads.html
                    # We overwrite the standard LDraw colours if we have better LGEO colours.
                    if item == "lgeo_colour":
                        colour = ()
                        if helpers.valid_value(line_split[1]):
                            code = int(line_split[1])
                        else:
                            print(f"WARNING Colour code must be an integer: {line_split[1]}")

                        if helpers.valid_value((line_split[2:])):
                            colour = tuple(map(int, line_split[2:]))
                        else:
                            print(f"WARNING Colour tuple must be integers: {line_split[2:]}")

                        if colour:
                            lgeo_colours[code] = colour

        return lgeo_colours

    @classmethod
    def build_search_paths(cls, parent_filepath=None):
        cls.reset_caches()

        ldraw_roots = []

        # append top level file's directory
        # https://forums.ldraw.org/thread-24495-post-40577.html#pid40577
        # post discussing path order, this order was chosen
        # except that the current file's dir isn't scanned, only the current dir of the top level file
        # https://forums.ldraw.org/thread-24495-post-45340.html#pid45340
        if parent_filepath is not None:
            ldraw_roots.append(os.path.dirname(parent_filepath))

        if cls.prefer_studio:
            if cls.prefer_unofficial:
                ldraw_roots.append(os.path.join(cls.studio_ldraw_path, "unofficial"))
                ldraw_roots.append(os.path.join(cls.ldraw_path, "unofficial"))
                ldraw_roots.append(os.path.join(cls.studio_ldraw_path))
                ldraw_roots.append(os.path.join(cls.ldraw_path))
            else:
                ldraw_roots.append(os.path.join(cls.studio_ldraw_path))
                ldraw_roots.append(os.path.join(cls.ldraw_path))
                ldraw_roots.append(os.path.join(cls.studio_ldraw_path, "unofficial"))
                ldraw_roots.append(os.path.join(cls.ldraw_path, "unofficial"))
        else:
            if cls.prefer_unofficial:
                ldraw_roots.append(os.path.join(cls.ldraw_path, "unofficial"))
                ldraw_roots.append(os.path.join(cls.studio_ldraw_path, "unofficial"))
                ldraw_roots.append(os.path.join(cls.ldraw_path))
                ldraw_roots.append(os.path.join(cls.studio_ldraw_path))
            else:
                ldraw_roots.append(os.path.join(cls.ldraw_path))
                ldraw_roots.append(os.path.join(cls.studio_ldraw_path))
                ldraw_roots.append(os.path.join(cls.ldraw_path, "unofficial"))
                ldraw_roots.append(os.path.join(cls.studio_ldraw_path, "unofficial"))

        for root in ldraw_roots:
            path = root
            cls.append_search_path(path, root=True)

            path = os.path.join(root, "p")
            cls.append_search_path(path)

            if cls.resolution == "High":
                path = os.path.join(root, "p", "48")
                cls.append_search_path(path)
            elif cls.resolution == "Low":
                path = os.path.join(root, "p", "8")
                cls.append_search_path(path)

            path = os.path.join(root, "parts")
            cls.append_search_path(path)

            path = os.path.join(root, "parts", "textures")
            cls.append_search_path(path)

            path = os.path.join(root, "models")
            cls.append_search_path(path)

    # build a list of folders to search for parts
    # build a map of lowercase to actual filenames
    @classmethod
    def append_search_path(cls, path, root=False):
        cls.search_dirs.append(path)
        cls.append_lowercase_paths(path, '*')
        if root:
            return
        cls.append_lowercase_paths(path, '**/*')

    @classmethod
    def append_lowercase_paths(cls, path, pattern):
        files = glob.glob(os.path.join(path, pattern))
        for file in files:
            cls.lowercase_paths.setdefault(file.lower(), file)

    @classmethod
    def locate(cls, filename):
        part_path = filename.replace("\\", os.path.sep).replace("/", os.path.sep)
        part_path = os.path.expanduser(part_path)

        # full path was specified
        if os.path.isfile(part_path):
            return part_path

        for dir in cls.search_dirs:
            full_path = os.path.join(dir, part_path)
            full_path = cls.lowercase_paths.get(full_path.lower()) or full_path
            if os.path.isfile(full_path):
                return full_path

        # TODO: requests retrieve missing items from ldraw.org

        print(f"missing {filename}")
        return None
