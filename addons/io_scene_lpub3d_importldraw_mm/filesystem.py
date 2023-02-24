import os
import string
import glob
from sys import platform
from pathlib import Path


class FileSystem:
    defaults = {}

    defaults['ldraw_path'] = ''
    ldraw_path = defaults['ldraw_path']

    defaults['studio_ldraw_path'] = ''
    studio_ldraw_path = defaults['studio_ldraw_path']

    defaults['prefer_studio'] = False
    prefer_studio = defaults['prefer_studio']

    defaults['prefer_unofficial'] = False
    prefer_unofficial = defaults['prefer_unofficial']

    defaults['resolution'] = 'Standard'
    resolution = defaults['resolution']

    __search_paths = []
    __lowercase_paths = {}

    @classmethod
    def reset_caches(cls):
        cls.__search_paths = []
        cls.__lowercase_paths = {}

    @staticmethod
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
                "C:\\LDraw",
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
                    dir = os.path.join(os.path.join(f"{drive_letter}:\\", dir_tail))
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


    @staticmethod
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

    @classmethod
    def build_search_paths(cls, parent_filepath=None):
        cls.reset_caches()

        # https://forums.ldraw.org/thread-24495-post-40577.html#pid40577
        # append top level file's directory
        if parent_filepath is not None:
            cls.__append_search_path((os.path.dirname(parent_filepath), '**/*'))
            cls.__append_search_path((os.path.dirname(parent_filepath), '*'))

        if cls.prefer_studio:
            cls.__append_search_path((os.path.join(cls.studio_ldraw_path), '*'))
            cls.__append_search_path((os.path.join(cls.ldraw_path), '*'))
        else:
            cls.__append_search_path((os.path.join(cls.ldraw_path), '*'))
            cls.__append_search_path((os.path.join(cls.studio_ldraw_path), '*'))

        ldraw_roots = list()

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
            cls.__append_search_path((os.path.join(root, "models"), '**/*'))
            cls.__append_search_path((os.path.join(root, "models"), '*'))

            cls.__append_search_path((os.path.join(root, "parts", "textures"), '**/*'))
            cls.__append_search_path((os.path.join(root, "parts", "textures"), '*'))

            cls.__append_search_path((os.path.join(root, "parts"), '**/*'))
            cls.__append_search_path((os.path.join(root, "parts"), '*'))

            if cls.resolution == "High":
                cls.__append_search_path((os.path.join(root, "p", "48"), '**/*'))
                cls.__append_search_path((os.path.join(root, "p", "48"), '*'))
            elif cls.resolution == "Low":
                cls.__append_search_path((os.path.join(root, "p", "8"), '**/*'))
                cls.__append_search_path((os.path.join(root, "p", "8"), '*'))

            cls.__append_search_path((os.path.join(root, "p"), '**/*'))
            cls.__append_search_path((os.path.join(root, "p"), '*'))

        cls.__lowercase_paths = {}
        for path in cls.__search_paths:
            for file in glob.glob(os.path.join(path[0], path[1])):
                cls.__lowercase_paths[file.lower()] = file

    @classmethod
    def __append_search_path(cls, path):
        # if path[0] != "" and os.path.isdir(path[0]):
        cls.__search_paths.append(path)

    @classmethod
    def locate(cls, filename):
        part_path = filename.replace("\\", os.path.sep).replace("/", os.path.sep)
        part_path = os.path.expanduser(part_path)

        # full path was specified
        if os.path.isfile(part_path):
            return part_path

        for path in cls.__search_paths:
            full_path = os.path.join(path[0], part_path)
            full_path = cls.__lowercase_paths.get(full_path.lower()) or full_path
            if os.path.isfile(full_path):
                return full_path

        # TODO: requests retrieve missing items from ldraw.org

        print(f"missing {filename}")
        return None
