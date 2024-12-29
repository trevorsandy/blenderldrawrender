import os.path

from .import_options import ImportOptions
from .filesystem import FileSystem
from .ldraw_color import LDrawColor
from . import helpers


class ImportSettings:
    settings_path = os.path.join('config', 'ImportOptions.json')
    settings = None

    filesystem_defaults = FileSystem.defaults
    ldraw_color_defaults = LDrawColor.defaults
    import_options_defaults = ImportOptions.defaults
	# _*_lp_lc_mod    
    lpub3d_defaults = {
        'overwrite_image': True,
        'transparent_background': False,
        'crop_image': False,
        'render_window': True,
        'blendfile_trusted': False,
        'verbose': True,
        'profile': False,
        'resolution_width': 1280,
        'resolution_height': 720,
        'render_percentage': 100,
        'blend_file': ''
    }
    # _*_mod_end

	# _*_lp_lc_mod
    default_settings = {
        **filesystem_defaults,
        **ldraw_color_defaults,
        **import_options_defaults,
        **lpub3d_defaults
    }
    # _*_mod_end

    @classmethod
    def settings_dict(cls, key):
        return {
            "get": lambda self: cls.get_setting(key),
            "set": lambda self, value: cls.set_setting(key, value),
        }

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
    def __setattr__(cls, key, value):
        cls.settings[key] = value

    # _*_lp_lc_mod
    @classmethod
    def __get_setting_tuple__(cls, key):
        _tuple = None
        if key == 'chosen_logo':
            _tuple = ImportOptions.chosen_logo_choices
        elif key == 'scale_strategy':
            _tuple = ImportOptions.scale_strategy_choices
        elif key == 'smooth_type':
            _tuple = ImportOptions.smooth_type_choices
        elif key == 'use_colour_scheme':
            _tuple = LDrawColor.use_colour_scheme_choices
        elif key == 'resolution':
            _tuple = FileSystem.resolution_choices
        return _tuple

    @classmethod
    def set_setting(cls, k, v):
        _lst = cls.__get_setting_tuple__(k)
        if _lst:
            for i, tp in enumerate(_lst):
                if v == tp[0]:
                    v = i
                    break
        cls.settings[k] = v

    @classmethod
    def load_settings(cls):
        cls.settings = {}
        has_settings = helpers.read_json(cls.settings_path, cls.default_settings)
        for k, v in cls.default_settings.items():
            _lst = cls.__get_setting_tuple__(k)
            _v = has_settings.get(k,v)
            if _lst:
                for i, tp in enumerate(_lst):
                    if _v == tp[0]:
                        v = i
                        break
            else:
                v = _v
            cls.settings[k] = v

    @classmethod
    def save_settings(cls, has_settings):
        settings = {}
        for k, v in cls.default_settings.items():
            _lst = cls.__get_setting_tuple__(k)
            _v = has_settings.get(k,v)
            if _lst:
                for i, tp in enumerate(_lst):
                    if _v == i:
                        v = tp[0]
                        break
            else:
                v = _v
            settings[k] = v
        helpers.write_json(cls.settings_path, settings, indent=4)
    # _*_mod_end

    @classmethod
    def apply_settings(cls, save_settings=False):
        if save_settings:
            cls.save_settings(cls.settings)

        for k, v in cls.filesystem_defaults.items():
            setattr(FileSystem, k, cls.settings[k])

        for k, v in cls.ldraw_color_defaults.items():
            setattr(LDrawColor, k, cls.settings[k])

        for k, v in cls.import_options_defaults.items():
            setattr(ImportOptions, k, cls.settings[k])

	# _*_lp_lc_mod
    @classmethod
    def get_settings(cls):
        cls.load_settings()
        return cls.settings
    
    @classmethod
    def get_enum(cls, key, value=None):
        setting = None
        _lst = cls.__get_setting_tuple__(key)
        if _lst:
            _v = cls.settings.get(key)
            for i, tp in enumerate(_lst):
                if value is not None:
                    if _v == tp[0]:
                        setting = i
                        break
                else:
                    if _v == i:
                        setting = tp[0]
                        break
    
        if setting is None and value is not None:
            setting = value

        return setting

    @classmethod
    def get_environment_file(cls):
        return cls.default_settings.get('environment_file')

    @classmethod
    def debugPrint(cls, message, is_error=False):
        """Debug print"""

        if cls.settings.get('verbose'):
            helpers.render_print(message, is_error)
    # _*_mod_end
