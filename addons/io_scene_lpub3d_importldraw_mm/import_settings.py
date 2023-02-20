from .import_options import ImportOptions
from .filesystem import FileSystem
from .ldraw_colors import LDrawColor
from . import helpers


class ImportSettings:
    settings = {}

    filesystem_defaults = {
        'ldraw_path': FileSystem.locate_ldraw(),
        'studio_ldraw_path': FileSystem.locate_studio_ldraw(),
        'envoronment_file': FileSystem.locate_environment_file(),
        'custom_ldconfig_file': FileSystem.defaults['custom_ldconfig_file'],
        'additional_search_paths': FileSystem.defaults['additional_search_paths'],
        'search_additional_paths': FileSystem.defaults['search_additional_paths'],
        'prefer_studio': FileSystem.defaults['prefer_studio'],
        'use_archive_library': FileSystem.defaults['use_archive_library'],
        'prefer_studio': FileSystem.defaults['prefer_studio'],
        'resolution': FileSystem.defaults['resolution'],
    }

    ldraw_color_defaults = {
        'use_alt_colors': LDrawColor.defaults['use_alt_colors'],
    }

    import_options_defaults = {
        'remove_doubles': ImportOptions.defaults['remove_doubles'],
        'merge_distance': ImportOptions.defaults['merge_distance'],
        'shade_smooth': ImportOptions.defaults['shade_smooth'],
        'display_logo': ImportOptions.defaults['display_logo'],
        'chosen_logo': ImportOptions.defaults['chosen_logo'],
        'make_gaps': ImportOptions.defaults['make_gaps'],
        'gap_scale': ImportOptions.defaults['gap_scale'],
        'no_studs': ImportOptions.defaults['no_studs'],
        'set_timeline_markers': ImportOptions.defaults['set_timeline_markers'],
        'meta_bfc': ImportOptions.defaults['meta_bfc'],
        'meta_group': ImportOptions.defaults['meta_group'],
        'meta_print_write': ImportOptions.defaults['meta_print_write'],
        'meta_step': ImportOptions.defaults['meta_step'],
        'meta_step_groups': ImportOptions.defaults['meta_step_groups'],
        'meta_clear': ImportOptions.defaults['meta_clear'],
        'meta_pause': ImportOptions.defaults['meta_pause'],
        'meta_save': ImportOptions.defaults['meta_save'],
        'set_end_frame': ImportOptions.defaults['set_end_frame'],
        'frames_per_step': ImportOptions.defaults['frames_per_step'],
        'starting_step_frame': ImportOptions.defaults['starting_step_frame'],
        'smooth_type': ImportOptions.defaults['smooth_type'],
        'import_edges': ImportOptions.defaults['import_edges'],
        'import_cameras': ImportOptions.defaults['import_cameras'],
        'import_lights': ImportOptions.defaults['import_lights'],
        'add_environment': ImportOptions.defaults['add_environment'],
        'use_freestyle_edges': ImportOptions.defaults['use_freestyle_edges'],
        'import_scale': ImportOptions.defaults['import_scale'],
        'parent_to_empty': ImportOptions.defaults['parent_to_empty'],
        'gap_target': ImportOptions.defaults['gap_target'],
        'gap_scale_strategy': ImportOptions.defaults['gap_scale_strategy'],
        'treat_shortcut_as_model': ImportOptions.defaults['treat_shortcut_as_model'],
        'treat_models_with_subparts_as_parts': ImportOptions.defaults['treat_models_with_subparts_as_parts'],
        'recalculate_normals': ImportOptions.defaults['recalculate_normals'],
        'triangulate': ImportOptions.defaults['triangulate'],
        'preserve_hierarchy': ImportOptions.defaults['preserve_hierarchy'],
    }

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
    def debugPrint(cls, message):
        """Debug print"""

        if cls.settings.get('verbose'):
            helpers.render_print(message)

    @classmethod
    def get_setting(cls, key):
        if cls.settings is None:
            cls.load_settings()

        value = cls.settings.get(key)
        default = cls.default_settings.get(key)

        # ensure saved type is the same as the default type
        if type(value) == type(default):
            return value
        else:
            return default

    @classmethod
    def get_environment_file(cls):
        return cls.default_settings.get('environment_file')

    @classmethod
    def get_ini_settings(cls, ini_settings_file):
        section_name = 'importLDrawMM'
        ini_settings = helpers.read_ini(ini_settings_file, cls.default_settings)
        assert ini_settings is not None, "INI Settings is not defined."
        for k, v in cls.default_settings.items():
            value = ini_settings[section_name][k.replace("_", "").lower()]
            cls.settings[k] = helpers.evaluate_value(value)
        return cls.settings

    @classmethod
    def load_settings(cls):
        cls.settings = helpers.read_json('config', 'ImportOptions.json', cls.default_settings)

    @classmethod
    def get_settings(cls):
        cls.load_settings()
        return cls.settings

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
