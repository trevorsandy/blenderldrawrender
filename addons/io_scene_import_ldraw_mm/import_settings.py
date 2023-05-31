from .import_options import ImportOptions
from .filesystem import FileSystem
from .ldraw_colors import LDrawColor
from . import helpers


class ImportSettings:
    settings = None

    filesystem_defaults = FileSystem.defaults
    ldraw_color_defaults = LDrawColor.defaults
    import_options_defaults = ImportOptions.defaults

    lpub3d_defaults = {
        'overwrite_image': True,
        'transparent_background': False,
        'crop_image': False,
        'render_window': True,
        'blendfile_trusted': False,
        'verbose': True,
        'profile': False,
        'resolution_width': 800,
        'resolution_height': 600,
        'render_percentage': 100,
        'blend_file': ''
    }

    default_settings = {**filesystem_defaults,
                        **ldraw_color_defaults,
                        **import_options_defaults,
                        **lpub3d_defaults}

    @classmethod
    def get_setting(cls, key):
        if cls.settings is None:
            cls.load_settings()

        setting = cls.settings.get(key)
        default = cls.default_settings.get(key)

        # ensure saved type is the same as the default type
        if type(setting) == type(default):
            return setting
        else:
            return default

    @classmethod
    def load_settings(cls):
        cls.settings = helpers.read_json('config', 'ImportOptions.json', cls.default_settings)

    @classmethod
    def save_settings(cls, has_settings):
        cls.settings = {}
        for k, v in cls.default_settings.items():
            cls.settings[k] = has_settings.get(k,v)
        helpers.write_json('config', 'ImportOptions.json', cls.settings)

    @classmethod
    def apply_settings(cls):
        for k, v in cls.filesystem_defaults.items():
            setattr(FileSystem, k, cls.settings[k])

        for k, v in cls.ldraw_color_defaults.items():
            setattr(LDrawColor, k, cls.settings[k])

        for k, v in cls.import_options_defaults.items():
            setattr(ImportOptions, k, cls.settings[k])

    @classmethod
    def get_settings(cls):
        cls.load_settings()
        return cls.settings

    @classmethod
    def get_environment_file(cls):
        return cls.default_settings.get('environment_file')

    @classmethod
    def get_ini_settings(cls, ini_settings_file):
        section_name = 'ImportLDrawMM'
        ini_settings = helpers.read_ini(ini_settings_file, cls.default_settings)
        assert ini_settings is not None, "INI Settings is not defined."
        for k, v in cls.default_settings.items():
            value = ini_settings[section_name][k.replace("_", "").lower()]
            cls.settings[k] = helpers.evaluate_value(value)
        return cls.settings

    @classmethod
    def debugPrint(cls, message):
        """Debug print"""

        if cls.settings.get('verbose'):
            helpers.render_print(message)
