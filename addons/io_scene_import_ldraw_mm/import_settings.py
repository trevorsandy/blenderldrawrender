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
        'resolution_width': 800,
        'resolution_height': 600,
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

    @classmethod
    def set_setting(cls, k, v):
        cls.settings[k] = v

    @classmethod
    def load_settings(cls):
        cls.settings = helpers.read_json(cls.settings_path, cls.default_settings)

	# _*_lp_lc_mod
    @classmethod
    def save_settings(cls, has_settings):
        cls.settings = {}
        for k, v in cls.default_settings.items():
            _lst = None
            _v = has_settings.get(k,v)
            if k == 'chosen_logo':
                _lst = ImportOptions.chosen_logo_choices
            elif k == 'color_strategy':
                _lst = ImportOptions.color_strategy_choices
            elif k == 'gap_scale_strategy':
                _lst = ImportOptions.gap_scale_strategy_choices
            elif k == 'gap_target':
                _lst = ImportOptions.gap_target_choices
            elif k == 'smooth_type':
                _lst = ImportOptions.smooth_type_choices
            elif k == 'use_colour_scheme':
                _lst = LDrawColor.use_colour_scheme_choices
            elif k == 'resolution':
                _lst = FileSystem.resolution_choices
            if _lst is not None:
                for i, tp in enumerate(_lst):
                    if tp[0] == _v:
                        _v = i
                        break
            cls.settings[k] = _v
        helpers.write_json(cls.settings_path, cls.settings)
    # _*_mod_end

    @classmethod
    def apply_settings(cls):
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
    # _*_mod_end
