import os
import string
import glob
from sys import platform
from pathlib import Path
# _*_lp_lc_mod
from . import helpers
import zipfile
# _*_mod_end
import tempfile

def locate_ldraw():
    ldraw_folder_name = 'ldraw'

    # home = os.path.expanduser("~")
    home = str(Path.home())
    ldraw_path = os.path.join(home, ldraw_folder_name)
    if os.path.isdir(ldraw_path):
        return ldraw_path

    # _*_lp_lc_mod
    # Search LDRAW_DIRECTORY environment variable
    if ldraw_path == "":
        ldrawDir = os.environ.get('LDRAW_DIRECTORY')
        if ldrawDir is not None:
            dir = os.path.expanduser(ldrawDir).rstrip()
            if os.path.isfile(os.path.join(dir, "LDConfig.ldr")):
                ldraw_path = dir
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

    return ldraw_path
    # _*_mod_end

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


def locate_studio_custom_parts():
    if platform == "linux" or platform == "linux2":
        pass
        # linux
    elif platform == "darwin":
        pass
        # OS X
    elif platform == "win32":
        path = os.path.join(os.getenv('LOCALAPPDATA'), 'Stud.io', 'CustomParts')
        if os.path.isdir(path):
            return path

    return ""


def is_case_sensitive():
    # By default mkstemp() creates a file with
    # a name that begins with 'tmp' (lowercase)
    tmphandle, tmppath = tempfile.mkstemp()
    if os.path.exists(tmppath.upper()):
        return False
    else:
        return True


class FileSystem:
    defaults = {}

    defaults["ldraw_path"] = locate_ldraw()
    ldraw_path = defaults["ldraw_path"]

    defaults["studio_ldraw_path"] = locate_studio_ldraw()
    studio_ldraw_path = defaults["studio_ldraw_path"]

    defaults["studio_custom_parts_path"] = locate_studio_custom_parts()
    studio_custom_parts_path = defaults["studio_custom_parts_path"]

    defaults["prefer_studio"] = False
    prefer_studio = defaults["prefer_studio"]

    defaults["prefer_unofficial"] = False
    prefer_unofficial = defaults["prefer_unofficial"]

    defaults["case_sensitive_filesystem"] = is_case_sensitive()
    case_sensitive_filesystem = defaults["case_sensitive_filesystem"]

    # _*_lp_lc_mod
    defaults["environment_file"] = ''
    environment_file = defaults["environment_file"]

    defaults["custom_ldconfig_file"] = ''
    custom_ldconfig_file = defaults["custom_ldconfig_file"]

    defaults["additional_search_paths"] = ''
    additional_search_paths = defaults["additional_search_paths"]

    defaults["search_additional_paths"] = False
    search_additional_paths = defaults["search_additional_paths"]

    defaults["use_archive_library"] = False
    use_archive_library = defaults["use_archive_library"]
    # _*_mod_end

    resolution_choices = (
        ("Low", "Low resolution primitives", "Import using low resolution primitives."),
        ("Standard", "Standard primitives", "Import using standard resolution primitives."),
        ("High", "High resolution primitives", "Import using high resolution primitives."),
    )

    defaults["resolution"] = 1
    resolution = defaults["resolution"]

    @staticmethod
    def resolution_value():
        return FileSystem.resolution_choices[FileSystem.resolution][0]

    search_dirs = []
    lowercase_paths = {}

    # _*_lp_lc_mod
    @staticmethod
    def reset_caches():
        FileSystem.search_dirs.clear()
        FileSystem.lowercase_paths.clear()
        FileSystem.clear_archives()

    @staticmethod
    def get_basename(filename):
        return os.path.basename(filename)

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
        helpers.render_print(f"DEBUG:  WARNING parameters_file not Found: {file_path}")
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
                            helpers.render_print(f"WARNING Colour code must be an integer: {line_split[1]}")

                        if helpers.valid_value((line_split[2:])):
                            colour = tuple(map(int, line_split[2:]))
                        else:
                            helpers.render_print(f"WARNING Colour tuple must be integers: {line_split[2:]}")

                        if colour:
                            lgeo_colours[code] = colour

        return lgeo_colours
    
    # Cached dictionary of LDraw archive library objects
    # **************************************************************************************

    # List of archive library file paths
    archive_search_paths  = []

    # List of loaded archive library names
    __archive_names       = []
    
    # Dictionary list - holds populated archives
    __archives            = []

    # Library Dictionaries
    __official_archive    = {}
    __unofficial_archive  = {}

    archive_not_found     = -2
    all_libraries         = -1
    official_library      = 0
    unofficial_library    = 1

    is_initial_update      = True
    has_official_archive   = False
    has_unofficial_archive = False
    have_archive_libraries = False

    @staticmethod
    def loaded_archives():
        return FileSystem.__archive_names

    @staticmethod
    def clear_archives():
        FileSystem.has_official_archive = False
        FileSystem.has_unofficial_archive = False
        FileSystem.have_archive_libraries = False
        FileSystem.is_initial_update = True
        FileSystem.__official_archive = {}
        FileSystem.__unofficial_archive = {}
        del FileSystem.archive_search_paths[:]
        del FileSystem.__archive_names[:]
        del FileSystem.__archives[:]
        
    @staticmethod
    def get_encoding(bin_io_slice):
        # The file uses UCS-2 (UTF-16) Big Endian encoding
        if bin_io_slice == b'\xfe\xff\x00':
            return "utf_16_be"
        # The file uses UCS-2 (UTF-16) Little Endian
        elif bin_io_slice == b'\xff\xfe0':
            return "utf_16_le"
        # Use LDraw model standard UTF-8
        else:
            return "utf_8"

    @classmethod
    def archive_file_exists(cls, key):
        if key in cls.__official_archive:
            return cls.official_library
        elif key in cls.__unofficial_archive:
            return cls.unofficial_library
        else:
            return cls.archive_not_found

    @classmethod
    def get_archive(cls, key, library=all_libraries):
        if library != cls.all_libraries:
            if key in cls.__archives[library]:
                bin_io = cls.__archives[library][key]
                encoding = cls.get_encoding(bin_io[:3])
                return bin_io.decode(encoding)
            else:
                return None
        elif cls.prefer_unofficial:
            library = cls.unofficial_library
            if key not in cls.__archives[library]:
                library = cls.official_library
                if key not in cls.__archives[library]:
                    return None
            bin_io = cls.__archives[library][key]
            encoding = cls.get_encoding(bin_io[:3])
            return bin_io.decode(encoding)
        else:
            for library in cls.__archives:
                if key in library:
                    bin_io = library[key]
                    encoding = cls.get_encoding(bin_io[:3])
                    return bin_io.decode(encoding)
                else:
                    return None

    @classmethod
    def set_official_archive(cls, archive_name, library):
        cls.__official_archive = {key.lower(): library.read(key) for key in library.namelist()}
        cls.__archives.append(cls.__official_archive)
        cls.__archive_names.append(archive_name)
        cls.has_official_archive = True
        helpers.render_print(f"Load official archive library: {archive_name}")
    
    @classmethod
    def set_unofficial_archive(cls, archive_name, library):
        cls.__unofficial_archive = {key.lower(): library.read(key) for key in library.namelist()}
        cls.__archives.append(cls.__unofficial_archive)
        cls.__archive_names.append(archive_name)
        cls.has_unofficial_archive  = True
        cls.is_initial_update = False
        helpers.render_print(f"Load unofficial archive library: {archive_name}")

    @classmethod
    def update_unofficial_archive(cls, archive_name, library):
        dictionary = {key.lower(): library.read(key) for key in library.namelist()}
        cls.__unofficial_archive.update(dictionary)
        cls.__archive_names.append(archive_name)
        helpers.render_print(f"Load unofficial archive library: {archive_name}")
    
    @classmethod
    def archive_library_found(cls, path):
        for library_name in os.listdir(path):
            if (library_name.endswith(".zip") or library_name.endswith(".bin")) and \
                library_name not in cls.loaded_archives():
                library_path = os.path.join(path, library_name)
                with zipfile.ZipFile(library_path) as library:
                    if not cls.has_official_archive and \
                        "ldraw/LDConfig.ldr" in library.namelist() and \
                        "ldraw/p/1-4cyli.dat" in library.namelist():
                        cls.set_official_archive(library_name, library)
                    else:
                        try:
                            is_unofficial_library = \
                                next(pid for pid in library.namelist()
                                    if (pid.endswith(".dat") or pid.endswith(".ldr") or pid.endswith(".mpd")))
                        except StopIteration:
                            continue
                        else:
                            if is_unofficial_library is not None:
                                if cls.is_initial_update:
                                    cls.set_unofficial_archive(library_name, library)
                                else:
                                    cls.update_unofficial_archive(library_name, library)

        return FileSystem.has_official_archive or FileSystem.has_unofficial_archive
    # **************************************************************************************
    # _*_mod_end

    @classmethod
    def build_search_paths(cls, parent_filepath=None):
        ldraw_roots = []

        # _*_lp_lc_mod
        if cls.use_archive_library and not cls.have_archive_libraries:
            cls.have_archive_libraries = FileSystem.archive_library_found(cls.ldraw_path)
        # _*_mod_end

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
                ldraw_roots.append(os.path.join(cls.studio_custom_parts_path))
                ldraw_roots.append(os.path.join(cls.studio_ldraw_path))
                ldraw_roots.append(os.path.join(cls.ldraw_path))
            else:
                ldraw_roots.append(os.path.join(cls.studio_custom_parts_path))
                ldraw_roots.append(os.path.join(cls.studio_ldraw_path))
                ldraw_roots.append(os.path.join(cls.ldraw_path))
                ldraw_roots.append(os.path.join(cls.studio_ldraw_path, "unofficial"))
                ldraw_roots.append(os.path.join(cls.ldraw_path, "unofficial"))
        else:
            if cls.prefer_unofficial:
                ldraw_roots.append(os.path.join(cls.ldraw_path, "unofficial"))
                ldraw_roots.append(os.path.join(cls.studio_ldraw_path, "unofficial"))
                ldraw_roots.append(os.path.join(cls.ldraw_path))
                ldraw_roots.append(os.path.join(cls.studio_custom_parts_path))
                ldraw_roots.append(os.path.join(cls.studio_ldraw_path))
            else:
                ldraw_roots.append(os.path.join(cls.ldraw_path))
                ldraw_roots.append(os.path.join(cls.studio_custom_parts_path))
                ldraw_roots.append(os.path.join(cls.studio_ldraw_path))
                ldraw_roots.append(os.path.join(cls.ldraw_path, "unofficial"))
                ldraw_roots.append(os.path.join(cls.studio_ldraw_path, "unofficial"))
        # _*_lp_lc_mod
        if cls.have_archive_libraries:
            cls.archive_search_paths.append("ldraw")
            cls.archive_search_paths.append("ldraw/models")
            if cls.prefer_unofficial:
                cls.archive_search_paths.append("parts")
                cls.archive_search_paths.append("ldraw/parts")
                cls.archive_search_paths.append("parts/textures")
                cls.archive_search_paths.append("ldraw/parts/textures")
                cls.archive_search_paths.append("p")
                cls.archive_search_paths.append("ldraw/p")
                if cls.resolution_value() == "High":
                    cls.archive_search_paths.append("p/48")
                    cls.archive_search_paths.append("ldraw/p/48")
                elif cls.resolution_value() == "Low":
                    cls.archive_search_paths.append("p/8")
                    cls.archive_search_paths.append("ldraw/p/8")
            else:
                cls.archive_search_paths.append("ldraw/parts")
                cls.archive_search_paths.append("parts")
                cls.archive_search_paths.append("ldraw/parts/textures")
                cls.archive_search_paths.append("parts/textures")
                cls.archive_search_paths.append("ldraw/p")
                cls.archive_search_paths.append("p")
                if cls.resolution_value() == "High":
                    cls.archive_search_paths.append("ldraw/p/48")
                    cls.archive_search_paths.append("p/48")
                elif cls.resolution_value() == "Low":
                    cls.archive_search_paths.append("ldraw/p/8")
                    cls.archive_search_paths.append("p/8")

        if cls.search_additional_paths and cls.additional_search_paths != "":
            folder_list = ['parts', 'p']
            additional_paths = cls.additional_search_paths.replace("\"", "").strip().split(",")
            for additional_path in additional_paths:
                path = additional_path.replace("\\", os.path.sep).replace("/", os.path.sep).lower()
                if path not in cls.search_dirs and os.path.exists(path):
                    subfolders = [entry.name for entry in os.scandir(path) if entry.is_dir()]
                    if subfolders:
                        for folder in subfolders:
                            if folder in folder_list:
                                if os.path.join(path) not in ldraw_roots:
                                    ldraw_roots.append(os.path.join(path))
                                    helpers.render_print(f"Load additional LDraw root: {path}", False)
                            else:
                                sub_path = os.path.join(path, folder).lower()
                                sub_subfolders = [entry.name for entry in os.scandir(sub_path) if entry.is_dir()]
                                if sub_subfolders:
                                    for sub_folder in sub_subfolders:
                                        if sub_folder in folder_list:
                                            if os.path.join(sub_path) not in ldraw_roots:
                                                ldraw_roots.append(os.path.join(sub_path))
                                                helpers.render_print(f"Load additional LDraw root: {sub_path}", False)
                                        else:
                                            cls.append_search_path(os.path.join(sub_path, sub_folder))
                                            helpers.render_print(f"Load additional search path: {sub_path}", False)
                                else:
                                    cls.append_search_path(os.path.join(sub_path))
                                    helpers.render_print(f"Load additional search path: {sub_path}", False)
                    else:
                        cls.append_search_path(os.path.join(path))
                        helpers.render_print(f"Load additional search path: {path}", False)
        # _*_mod_end
                    
        for root in ldraw_roots:
            path = root
            cls.append_search_path(path, root=True)

            path = os.path.join(root, "p")
            cls.append_search_path(path)

            if cls.resolution_value() == "High":
                path = os.path.join(root, "p", "48")
                cls.append_search_path(path)
            elif cls.resolution_value() == "Low":
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
        if cls.case_sensitive_filesystem:
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
        part_path = str(filename).replace("\\", os.path.sep).replace("/", os.path.sep)
        part_path = os.path.expanduser(part_path)

        # full path was specified
        if os.path.isfile(part_path):
            return part_path

        for dir in cls.search_dirs:
            full_path = os.path.join(dir, part_path)
            if os.path.isfile(full_path):
                return full_path

            lc_path = full_path.lower()
            if lc_path in cls.lowercase_paths:
                full_path = cls.lowercase_paths.get(lc_path)

            if os.path.isfile(full_path):
                return full_path

        # _*_lp_lc_mod
        if cls.have_archive_libraries:
            for path in cls.archive_search_paths:
                archive_path = os.path.join(path, filename.lower()).replace("\\", "/")
                archive_library = cls.archive_file_exists(archive_path)
                
                if archive_library != cls.archive_not_found:
                    result_list = list([archive_library, archive_path])
                    return result_list
        # _*_mod_end
        
        # TODO: requests retrieve missing items from ldraw.org
        # _*_lp_lc_mod
        helpers.render_print(f"missing {filename}", True)
        # _*_mod_end
        return None
