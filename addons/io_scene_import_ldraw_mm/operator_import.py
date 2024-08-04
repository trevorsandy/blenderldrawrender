import bpy

import time
import os

# _*_lp_lc_mod
from io_scene_render_ldraw.modelglobals import model_globals
from bpy_extras.io_utils import ImportHelper
# _*_mod_end
from .import_settings import ImportSettings
from .import_options import ImportOptions
from .filesystem import FileSystem
from .ldraw_node import LDrawNode
# _*_lp_lc_mod
from .ldraw_color import LDrawColor
# _*_mod_end
from . import blender_import

# _*_lp_lc_mod
class IMPORT_OT_do_ldraw_import(bpy.types.Operator, ImportHelper):
# _*_mod_end
    """Import an LDraw model File"""
    # _*_lp_lc_mod
    bl_idname = "import_scene.lpub3d_import_ldraw_mm"
    bl_description = "Import LDraw model (.mpd/.ldr/.l3b/.dat)"
    # _*_mod_end
    bl_label = "Import LDraw"
    # _*_lp_lc_mod
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    # Declarations
    # _*_mod_end
    filename_ext = ""
    # _*_lp_lc_mod
    ldraw_model_file_loaded = False
    prefs = ImportSettings.get_settings()
    # _*_mod_end

    filter_glob: bpy.props.StringProperty(
        name="Extensions",
        options={'HIDDEN'},
        default="*.mpd;*.ldr;*.dat",
    )

    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Filepath used for importing the file",
        maxlen=1024,
        subtype='FILE_PATH',
    )

    ldraw_path: bpy.props.StringProperty(
        name="LDraw path",
        description="Full filepath to the LDraw Parts Library (download from https://www.ldraw.org)",
        **ImportSettings.settings_dict('ldraw_path'),
    )

    studio_ldraw_path: bpy.props.StringProperty(
        name="Stud.io LDraw path",
        description="Full filepath to the Stud.io LDraw Parts Library (download from https://www.bricklink.com/v3/studio/download.page)",
        **ImportSettings.settings_dict('studio_ldraw_path'),
    )

    studio_custom_parts_path: bpy.props.StringProperty(
        name="Stud.io CustomParts path",
        description="Full filepath to the CustomParts path",
        **ImportSettings.settings_dict('studio_custom_parts_path'),
    )

    # _*_lp_lc_mod
    additional_search_paths: bpy.props.StringProperty(
        name="Additional search paths",
        description="Full directory paths, comma delimited, to additional LDraw search paths",
        **ImportSettings.settings_dict('additional_search_paths'),
    )

    custom_ldconfig_file: bpy.props.StringProperty(
        name="Custom LDConfig",
        description="Full directory path to specified custom LDraw colours (LDConfig) file",
        **ImportSettings.settings_dict('custom_ldconfig_file'),
    )

    environment_file: bpy.props.StringProperty(
        name="Environment file",
        description="Full file path to .exr environment texture file - specify if not using addon default",
        **ImportSettings.settings_dict('environment_file'),
    )

    add_environment: bpy.props.BoolProperty(
        name="Add environment",
        description="Adds a ground plane and environment texture",
        **ImportSettings.settings_dict('add_environment'),
    )

    import_cameras: bpy.props.BoolProperty(
        name="Import cameras",
        description="Import camera definitions (from models authored in LPub3D or LeoCAD)",
        **ImportSettings.settings_dict('import_cameras'),
    )

    position_camera: bpy.props.BoolProperty(
        name="Position camera",
        description="Position the camera to show the whole model",
        **ImportSettings.settings_dict('position_camera'),
    )

    camera_border_percent: bpy.props.FloatProperty(
        name="Camera Border %",
        description="When positioning the camera, include a (percentage) border around the model in the render",
        **ImportSettings.settings_dict('camera_border_percent'),
        min=0.5,
    )

    import_lights: bpy.props.BoolProperty(
        name="Import lights",
        description="Import Light definitions (from models authored in LPub3D or LeoCAD)",
        **ImportSettings.settings_dict('import_lights'),
    )
    # _*_mod_end

    prefer_studio: bpy.props.BoolProperty(
        name="Prefer Stud.io library",
        description="Search for parts in Stud.io library first",
        **ImportSettings.settings_dict('prefer_studio'),
    )

    case_sensitive_filesystem: bpy.props.BoolProperty(
        name="Case-sensitive filesystem",
        description="Filesystem is case sensitive",
        **ImportSettings.settings_dict('case_sensitive_filesystem'),
    )

    prefer_unofficial: bpy.props.BoolProperty(
        name="Prefer unofficial parts",
        description="Search for unofficial parts first",
        **ImportSettings.settings_dict('prefer_unofficial'),
    )

    resolution: bpy.props.EnumProperty(
        name="Part resolution",
        description="Resolution of part primitives, ie. how much geometry they have",
        **ImportSettings.settings_dict('resolution'),
        items=FileSystem.resolution_choices,
    )

    # _*_lp_lc_mod
    use_colour_scheme: bpy.props.EnumProperty(
        name="Colour scheme options",
        description="Colour scheme options",
        **ImportSettings.settings_dict('use_colour_scheme'),
        items=LDrawColor.use_colour_scheme_choices,
    )
    # _*_mod_end

    remove_doubles: bpy.props.BoolProperty(
        name="Remove doubles",
        description="Merge overlapping vertices",
        **ImportSettings.settings_dict('remove_doubles'),
    )

    merge_distance: bpy.props.FloatProperty(
        name="Merge distance",
        description="Maximum distance between elements to merge",
        **ImportSettings.settings_dict('merge_distance'),
        precision=3,
        min=0.0,
    )

    shade_smooth: bpy.props.BoolProperty(
        name="Shade smooth",
        description="Shade smooth",
        **ImportSettings.settings_dict('shade_smooth'),
    )

    display_logo: bpy.props.BoolProperty(
        name="Display logo",
        description="Display logo on studs. Requires unofficial parts library to be downloaded",
        **ImportSettings.settings_dict('display_logo'),
    )

    chosen_logo: bpy.props.EnumProperty(
        name="Chosen logo",
        description="Use this logo on studs",
        **ImportSettings.settings_dict('chosen_logo'),
        items=ImportOptions.chosen_logo_choices,
    )

    smooth_type: bpy.props.EnumProperty(
        name="Smooth type",
        description="Use this strategy to smooth meshes",
        **ImportSettings.settings_dict('smooth_type'),
        items=ImportOptions.smooth_type_choices,
    )

    no_studs: bpy.props.BoolProperty(
        name="No studs",
        description="Don't import studs",
        **ImportSettings.settings_dict('no_studs'),
    )

    parent_to_empty: bpy.props.BoolProperty(
        name="Parent to empty",
        description="Parent the model to an empty",
        **ImportSettings.settings_dict('parent_to_empty'),
    )

    scale_strategy: bpy.props.EnumProperty(
        name="Scale strategy",
        description="How to apply import scaling",
        **ImportSettings.settings_dict('scale_strategy'),
        items=ImportOptions.scale_strategy_choices,
    )

    import_scale: bpy.props.FloatProperty(
        name="Import scale",
        description="Scale the entire model by this amount",
        **ImportSettings.settings_dict('import_scale'),
        precision=4,
        min=0.0001,
        max=1.00,
    )

    make_gaps: bpy.props.BoolProperty(
        name="Make gaps",
        description="Puts small gaps between parts",
        **ImportSettings.settings_dict('make_gaps'),
    )

    gap_scale: bpy.props.FloatProperty(
        name="Gap scale",
        description="Scale parts by this value to make gaps",
        **ImportSettings.settings_dict('gap_scale'),
        precision=3,
        min=0.0,
        max=1.0,
    )

    meta_bfc: bpy.props.BoolProperty(
        name="BFC",
        description="Process BFC meta commands",
        **ImportSettings.settings_dict('meta_bfc'),
    )

    meta_texmap: bpy.props.BoolProperty(
        name="TEXMAP",
        description="Process TEXMAP and DATA meta commands",
        **ImportSettings.settings_dict('meta_texmap'),
    )

    meta_print_write: bpy.props.BoolProperty(
        name="PRINT/WRITE",
        description="Process PRINT/WRITE meta command",
        **ImportSettings.settings_dict('meta_print_write'),
    )

    meta_group: bpy.props.BoolProperty(
        name="GROUP",
        description="Process GROUP meta commands",
        **ImportSettings.settings_dict('meta_group'),
    )

    meta_step: bpy.props.BoolProperty(
        name="STEP",
        description="Process STEP meta command",
        **ImportSettings.settings_dict('meta_step'),
    )

    meta_step_groups: bpy.props.BoolProperty(
        name="STEP Groups",
        description="Create collections for individual steps",
        **ImportSettings.settings_dict('meta_step_groups'),
    )

    meta_clear: bpy.props.BoolProperty(
        name="CLEAR",
        description="Process CLEAR meta command",
        **ImportSettings.settings_dict('meta_clear'),
    )

    meta_pause: bpy.props.BoolProperty(
        name="PAUSE",
        description="Process PAUSE meta command",
        **ImportSettings.settings_dict('meta_pause'),
    )

    meta_save: bpy.props.BoolProperty(
        name="SAVE",
        description="Process SAVE meta command",
        **ImportSettings.settings_dict('meta_save'),
    )

    set_end_frame: bpy.props.BoolProperty(
        name="Set step end frame",
        description="Set the end frame to the last step",
        **ImportSettings.settings_dict('set_end_frame'),
    )

    frames_per_step: bpy.props.IntProperty(
        name="Frames per step",
        description="Frames per step",
        **ImportSettings.settings_dict('frames_per_step'),
        min=1,
    )

    starting_step_frame: bpy.props.IntProperty(
        name="Starting step frame",
        options={'HIDDEN'},
        description="Frame to add the first STEP meta command",
        **ImportSettings.settings_dict('starting_step_frame'),
        min=1,
    )

    set_timeline_markers: bpy.props.BoolProperty(
        name="Set timeline markers",
        description="Set timeline markers for meta commands",
        **ImportSettings.settings_dict('set_timeline_markers'),
    )

    import_edges: bpy.props.BoolProperty(
        name="Import edges",
        description="Import edge meshes",
        **ImportSettings.settings_dict('import_edges'),
    )

    use_freestyle_edges: bpy.props.BoolProperty(
        name="Use Freestyle edges",
        description="Render LDraw edges using freestyle",
        **ImportSettings.settings_dict('use_freestyle_edges'),
    )

    treat_shortcut_as_model: bpy.props.BoolProperty(
        name="Treat shortcuts as models",
        options={'HIDDEN'},
        description="Split shortcut parts into their constituent pieces as if they were models",
        **ImportSettings.settings_dict('treat_shortcut_as_model'),
    )

    recalculate_normals: bpy.props.BoolProperty(
        name="Recalculate normals",
        description="Recalculate normals. Not recommended if BFC processing is active",
        **ImportSettings.settings_dict('recalculate_normals'),
    )

    triangulate: bpy.props.BoolProperty(
        name="Triangulate faces",
        description="Triangulate all faces",
        **ImportSettings.settings_dict('triangulate'),
    )

    # _*_lp_lc_mod
    profile: bpy.props.BoolProperty(
        name="Profile",
        description="Profile import performance",
        **ImportSettings.settings_dict('profile'),
    )
    # _*_mod_end

    bevel_edges: bpy.props.BoolProperty(
        name="Bevel edges",
        description="Bevel edges. Can cause some parts to render incorrectly",
        **ImportSettings.settings_dict('bevel_edges'),
    )

    bevel_weight: bpy.props.FloatProperty(
        name="Bevel weight",
        description="Bevel weight",
        **ImportSettings.settings_dict('bevel_weight'),
        precision=1,
        step=10,
        min=0.0,
        max=1.0,
    )

    bevel_width: bpy.props.FloatProperty(
        name="Bevel width",
        description="Bevel width",
        **ImportSettings.settings_dict('bevel_width'),
        precision=1,
        step=10,
        min=0.0,
        max=1.0,
    )

    bevel_segments: bpy.props.IntProperty(
        name="Bevel segments",
        description="Bevel segments",
        **ImportSettings.settings_dict('bevel_segments'),
    )

	# _*_lp_lc_mod
    search_additional_paths: bpy.props.BoolProperty(
        name="Search Additional Paths",
        description="Search additional LDraw paths (automatically set for fade previous steps and highlight step)",
        **ImportSettings.settings_dict('search_additional_paths'),
    )

    use_archive_library: bpy.props.BoolProperty(
        name="Use Archive Libraries",
        description="Add any archive (zip) libraries in the LDraw file path to the library search list",
        **ImportSettings.settings_dict('use_archive_library'),
    )

    verbose: bpy.props.BoolProperty(
        name="Verbose Output",
        description="Output all messages while working, else only show warnings and errors",
        **ImportSettings.settings_dict('verbose'),
    )

    preferences_file: bpy.props.StringProperty(
        default=r"",
        options={'HIDDEN'}
    )

    #def invoke(self, context, _event):
    #    context.window_manager.fileselect_add(self)
    #    ImportSettings.load_settings()
    #    return {'RUNNING_MODAL'}
    # _*_mod_end

    # _timer = None
    # __i = 0
    #
    # def modal(self, context, event):
    #     if event.type in {'RIGHTMOUSE', 'ESC'}:
    #         self.cancel(context)
    #         return {'CANCELLED'}
    #
    #     if event.type == 'TIMER':
    #         try:
    #             for i in range(10000):
    #                 next(self.__i)
    #         except StopIteration as e:
    #             self.cancel(context)
    #
    #     return {'PASS_THROUGH'}
    #
    # def cancel(self, context):
    #     wm = context.window_manager
    #     wm.event_timer_remove(self._timer)

    def execute(self, context):
        start = time.perf_counter()

        # bpy.ops.object.mode_set(mode='OBJECT')

        # _*_lp_lc_mod
        print("")
        use_lpub_settings = False
        if self.preferences_file != "":
            ImportSettings.debugPrint("=====Import MM Settings====")
            ImportSettings.debugPrint(f"Preferences file:    {self.preferences_file}")
            use_lpub_settings = str(os.path.basename(self.preferences_file)).endswith(".ini")
            if use_lpub_settings:
                IMPORT_OT_do_ldraw_import.prefs = ImportSettings.get_ini_settings(self.preferences_file)
        else:
            ImportSettings.debugPrint("=====Import LDraw MM=======")

        # Initialize model globals
        self.ldraw_model_file_loaded = model_globals.LDRAW_MODEL_LOADED
        model_globals.init()

        if use_lpub_settings or self.preferences_file != "":

            self.ldraw_path              = IMPORT_OT_do_ldraw_import.prefs.get("ldraw_path", self.ldraw_path)
            self.studio_ldraw_path       = IMPORT_OT_do_ldraw_import.prefs.get("studio_ldraw_path", self.studio_ldraw_path)
            self.studio_custom_parts_path= IMPORT_OT_do_ldraw_import.prefs.get("studio_custom_parts_path", self.studio_custom_parts_path)

            self.add_environment         = IMPORT_OT_do_ldraw_import.prefs.get("add_environment", self.add_environment)
            self.environment_file        = IMPORT_OT_do_ldraw_import.prefs.get("environment_file", self.environment_file)
            self.import_cameras          = IMPORT_OT_do_ldraw_import.prefs.get("import_cameras", self.import_cameras)
            self.position_camera         = IMPORT_OT_do_ldraw_import.prefs.get("position_camera", self.position_camera)
            self.camera_border_percent   = IMPORT_OT_do_ldraw_import.prefs.get("camera_border_percent", self.camera_border_percent)
            self.import_lights           = IMPORT_OT_do_ldraw_import.prefs.get("import_lights", self.import_lights)
            self.search_additional_paths = IMPORT_OT_do_ldraw_import.prefs.get("search_additional_paths", self.search_additional_paths)
            self.case_sensitive_filesystem = IMPORT_OT_do_ldraw_import.prefs.get("case_sensitive_filesystem", self.case_sensitive_filesystem)            

            self.custom_ldconfig_file    = IMPORT_OT_do_ldraw_import.prefs.get("custom_ldconfig_file",   self.custom_ldconfig_file)
            self.additional_search_paths = IMPORT_OT_do_ldraw_import.prefs.get("additional_search_paths", self.additional_search_paths)

            self.prefer_studio           = IMPORT_OT_do_ldraw_import.prefs.get("prefer_studio", self.prefer_studio)
            self.prefer_unofficial       = IMPORT_OT_do_ldraw_import.prefs.get("prefer_unofficial", self.prefer_unofficial)
            self.use_colour_scheme       = IMPORT_OT_do_ldraw_import.prefs.get("use_colour_scheme", self.use_colour_scheme)
            self.resolution              = IMPORT_OT_do_ldraw_import.prefs.get("resolution", self.resolution)
            self.display_logo            = IMPORT_OT_do_ldraw_import.prefs.get("display_logo", self.display_logo)
            self.chosen_logo             = IMPORT_OT_do_ldraw_import.prefs.get("chosen_logo", self.chosen_logo)

            self.scale_strategy          = IMPORT_OT_do_ldraw_import.prefs.get("scale_strategy", self.scale_strategy)
            self.import_scale            = IMPORT_OT_do_ldraw_import.prefs.get("import_scale", self.import_scale)
            self.parent_to_empty         = IMPORT_OT_do_ldraw_import.prefs.get("parent_to_empty", self.parent_to_empty)
            self.make_gaps               = IMPORT_OT_do_ldraw_import.prefs.get("make_gaps", self.make_gaps)
            self.gap_scale               = IMPORT_OT_do_ldraw_import.prefs.get("gap_scale", self.gap_scale)

            self.bevel_edges             = IMPORT_OT_do_ldraw_import.prefs.get("bevel_edges", self.bevel_edges)
            self.bevel_weight            = IMPORT_OT_do_ldraw_import.prefs.get("bevel_weight", self.bevel_weight)
            self.bevel_width             = IMPORT_OT_do_ldraw_import.prefs.get("bevel_width", self.bevel_width)
            self.bevel_segments          = IMPORT_OT_do_ldraw_import.prefs.get("bevel_segments", self.bevel_segments)

            self.remove_doubles          = IMPORT_OT_do_ldraw_import.prefs.get("remove_doubles", self.remove_doubles)
            self.merge_distance          = IMPORT_OT_do_ldraw_import.prefs.get("merge_distance", self.merge_distance)
            self.smooth_type             = IMPORT_OT_do_ldraw_import.prefs.get("smooth_type", self.smooth_type)
            self.shade_smooth            = IMPORT_OT_do_ldraw_import.prefs.get("shade_smooth", self.shade_smooth)
            self.recalculate_normals     = IMPORT_OT_do_ldraw_import.prefs.get("recalculate_normals", self.recalculate_normals)
            self.triangulate             = IMPORT_OT_do_ldraw_import.prefs.get("triangulate", self.triangulate)

            self.meta_bfc                = IMPORT_OT_do_ldraw_import.prefs.get("meta_bfc", self.meta_bfc)
            self.meta_texmap             = IMPORT_OT_do_ldraw_import.prefs.get("meta_texmap", self.meta_texmap)
            self.meta_group              = IMPORT_OT_do_ldraw_import.prefs.get("meta_group", self.meta_group)
            self.meta_print_write        = IMPORT_OT_do_ldraw_import.prefs.get("meta_print_write", self.meta_print_write)
            self.meta_step               = IMPORT_OT_do_ldraw_import.prefs.get("meta_step", self.meta_step)
            self.meta_step_groups        = IMPORT_OT_do_ldraw_import.prefs.get("meta_step_groups", self.meta_step_groups)
            self.starting_step_frame     = IMPORT_OT_do_ldraw_import.prefs.get("starting_step_frame", self.starting_step_frame)
            self.frames_per_step         = IMPORT_OT_do_ldraw_import.prefs.get("frames_per_step", self.frames_per_step)
            self.set_end_frame           = IMPORT_OT_do_ldraw_import.prefs.get("set_end_frame", self.set_end_frame)
            self.meta_clear              = IMPORT_OT_do_ldraw_import.prefs.get("meta_clear", self.meta_clear)
            #self.meta_pause              = IMPORT_OT_do_ldraw_import.prefs.get("meta_pause", self.meta_pause)
            self.meta_save               = IMPORT_OT_do_ldraw_import.prefs.get("meta_save", self.meta_save )
            self.set_timeline_markers    = IMPORT_OT_do_ldraw_import.prefs.get("set_timeline_markers", self.set_timeline_markers)

            self.use_freestyle_edges     = IMPORT_OT_do_ldraw_import.prefs.get("use_freestyle_edges", self.use_freestyle_edges)
            self.import_edges            = IMPORT_OT_do_ldraw_import.prefs.get("import_edges", self.import_edges)
            self.treat_shortcut_as_model = IMPORT_OT_do_ldraw_import.prefs.get("treat_shortcut_as_model", self.treat_shortcut_as_model)
            self.no_studs                = IMPORT_OT_do_ldraw_import.prefs.get("no_studs", self.no_studs)

            self.profile                 = IMPORT_OT_do_ldraw_import.prefs.get("profile", self.profile)
            self.verbose                 = IMPORT_OT_do_ldraw_import.prefs.get("verbose", self.verbose)

        if self.preferences_file == "":

            IMPORT_OT_do_ldraw_import.prefs["ldraw_path"]              = self.ldraw_path
            IMPORT_OT_do_ldraw_import.prefs["studio_ldraw_path"]       = self.studio_ldraw_path
            IMPORT_OT_do_ldraw_import.prefs["studio_custom_parts_path"]= self.studio_custom_parts_path

            IMPORT_OT_do_ldraw_import.prefs['add_environment']         = self.add_environment
            IMPORT_OT_do_ldraw_import.prefs['environment_file']        = self.environment_file
            IMPORT_OT_do_ldraw_import.prefs['import_cameras']          = self.import_cameras
            IMPORT_OT_do_ldraw_import.prefs['position_camera']         = self.position_camera
            IMPORT_OT_do_ldraw_import.prefs['camera_border_percent']   = self.camera_border_percent
            IMPORT_OT_do_ldraw_import.prefs['import_lights']           = self.import_lights
            IMPORT_OT_do_ldraw_import.prefs['search_additional_paths'] = self.search_additional_paths
            IMPORT_OT_do_ldraw_import.prefs['case_sensitive_filesystem'] = self.case_sensitive_filesystem            

            IMPORT_OT_do_ldraw_import.prefs['custom_ldconfig_file']    = self.custom_ldconfig_file
            IMPORT_OT_do_ldraw_import.prefs['additional_search_paths'] = self.additional_search_paths

            IMPORT_OT_do_ldraw_import.prefs["prefer_studio"]           = self.prefer_studio
            IMPORT_OT_do_ldraw_import.prefs["prefer_unofficial"]       = self.prefer_unofficial
            IMPORT_OT_do_ldraw_import.prefs["use_colour_scheme"]       = self.use_colour_scheme
            IMPORT_OT_do_ldraw_import.prefs["resolution"]              = self.resolution
            IMPORT_OT_do_ldraw_import.prefs["display_logo"]            = self.display_logo
            IMPORT_OT_do_ldraw_import.prefs["chosen_logo"]             = self.chosen_logo

            IMPORT_OT_do_ldraw_import.prefs["scale_strategy"]          = self.scale_strategy
            IMPORT_OT_do_ldraw_import.prefs["import_scale"]            = self.import_scale
            IMPORT_OT_do_ldraw_import.prefs["parent_to_empty"]         = self.parent_to_empty
            IMPORT_OT_do_ldraw_import.prefs["make_gaps"]               = self.make_gaps
            IMPORT_OT_do_ldraw_import.prefs["gap_scale"]               = self.gap_scale

            IMPORT_OT_do_ldraw_import.prefs["bevel_edges"]             = self.bevel_edges
            IMPORT_OT_do_ldraw_import.prefs["bevel_weight"]            = self.bevel_weight
            IMPORT_OT_do_ldraw_import.prefs["bevel_width"]             = self.bevel_width
            IMPORT_OT_do_ldraw_import.prefs["bevel_segments"]          = self.bevel_segments

            IMPORT_OT_do_ldraw_import.prefs["remove_doubles"]          = self.remove_doubles
            IMPORT_OT_do_ldraw_import.prefs["merge_distance"]          = self.merge_distance
            IMPORT_OT_do_ldraw_import.prefs["smooth_type"]             = self.smooth_type
            IMPORT_OT_do_ldraw_import.prefs["shade_smooth"]            = self.shade_smooth
            IMPORT_OT_do_ldraw_import.prefs["recalculate_normals"]     = self.recalculate_normals
            IMPORT_OT_do_ldraw_import.prefs["triangulate"]             = self.triangulate

            IMPORT_OT_do_ldraw_import.prefs["meta_bfc"]                = self.meta_bfc
            IMPORT_OT_do_ldraw_import.prefs["meta_texmap"]             = self.meta_texmap
            IMPORT_OT_do_ldraw_import.prefs["meta_group"]              = self.meta_group
            IMPORT_OT_do_ldraw_import.prefs["meta_print_write"]        = self.meta_print_write
            IMPORT_OT_do_ldraw_import.prefs["meta_step"]               = self.meta_step
            IMPORT_OT_do_ldraw_import.prefs["meta_step_groups"]        = self.meta_step_groups
            IMPORT_OT_do_ldraw_import.prefs["starting_step_frame"]     = self.starting_step_frame
            IMPORT_OT_do_ldraw_import.prefs["frames_per_step"]         = self.frames_per_step
            IMPORT_OT_do_ldraw_import.prefs["set_end_frame"]           = self.set_end_frame
            IMPORT_OT_do_ldraw_import.prefs["meta_clear"]              = self.meta_clear
           #IMPORT_OT_do_ldraw_import.prefs["meta_pause"]             = self.meta_pause
            IMPORT_OT_do_ldraw_import.prefs["meta_save"]               = self.meta_save
            IMPORT_OT_do_ldraw_import.prefs["set_timeline_markers"]    = self.set_timeline_markers

            IMPORT_OT_do_ldraw_import.prefs["use_freestyle_edges"]     = self.use_freestyle_edges
            IMPORT_OT_do_ldraw_import.prefs["import_edges"]            = self.import_edges
            IMPORT_OT_do_ldraw_import.prefs["treat_shortcut_as_model"] = self.treat_shortcut_as_model
            IMPORT_OT_do_ldraw_import.prefs["no_studs"]                = self.no_studs

            IMPORT_OT_do_ldraw_import.prefs["profile"]                 = self.profile
            IMPORT_OT_do_ldraw_import.prefs["verbose"]                 = self.verbose

        if self.environment_file == "":
            IMPORT_OT_do_ldraw_import.prefs["environment_file"]        = ImportSettings.get_environment_file()
        else:
            IMPORT_OT_do_ldraw_import.prefs["environment_file"]        = self.environment_file

        assert self.filepath != "", "Model file path not specified."

        ImportSettings.save_settings(IMPORT_OT_do_ldraw_import.prefs)
        # _*_mod_end

        # _*_lp_lc_mod
        model_globals.LDRAW_MODEL_FILE = self.filepath
        # _*_mod_end

        # wm = context.window_manager
        # self._timer = wm.event_timer_add(0.01, window=context.window)
        # wm.modal_handler_add(self)
        # self.__i = blender_import.do_import(bpy.path.abspath(self.filepath))
        # return {'RUNNING_MODAL'}

        # https://docs.python.org/3/library/profile.html
        # _*_lp_lc_mod
        load_result = None
        # _*_mod_end
        if self.profile:
            import cProfile
            import pstats

            from pathlib import Path
            # _*_lp_lc_mod
            prof_output = os.path.join(Path.home(), 'ldraw_import_mm.prof')
            # _*_mod_end

            with cProfile.Profile() as profiler:
                # _*_lp_lc_mod
                load_result = blender_import.do_import(bpy.path.abspath(self.filepath))
                # _*_mod_end
            stats = pstats.Stats(profiler)
            stats.sort_stats(pstats.SortKey.TIME)
            stats.print_stats()
            stats.dump_stats(filename=prof_output)
        else:
            # _*_lp_lc_mod
            load_result = blender_import.do_import(bpy.path.abspath(self.filepath))

        model_globals.LDRAW_MODEL_LOADED = True
        # _*_mod_end

        print("")
        # _*_lp_lc_mod
        ImportSettings.debugPrint("=====Import MM Complete====")
        if load_result is None:
            ImportSettings.debugPrint("Import MM result: None")
        ImportSettings.debugPrint(f"Model file: {model_globals.LDRAW_MODEL_FILE}")
        ImportSettings.debugPrint(f"Part count: {LDrawNode.part_count}")
        # _*_mod_end
        end = time.perf_counter()
        # _*_lp_lc_mod
        elapsed = end - start
        ImportSettings.debugPrint(f"Elapsed time: {elapsed}")
        ImportSettings.debugPrint("===========================")
        # _*_mod_end

        return {'FINISHED'}

    # https://docs.blender.org/api/current/bpy.types.UILayout.html
    def draw(self, context):
        space_factor = 0.3

        layout = self.layout
        # _*_lp_lc_mod
        layout.use_property_split = True  # Active single-column layout
        # _*_mod_end

        # _*_lp_lc_mod
        box = layout.box()
        box.label(text="LDraw Import Options", icon='PREFERENCES')
        box.label(text="Import filepaths:", icon='FILEBROWSER')
        box.prop(self, "ldraw_path")
        box.prop(self, "custom_ldconfig_file")
        box.prop(self, "studio_ldraw_path")
        box.prop(self, "studio_custom_parts_path")
        box.prop(self, "search_additional_paths")
        box.prop(self, "case_sensitive_filesystem")
        if not self.ldraw_model_file_loaded:
            box.prop(self, "environment_file")
        # _*_mod_end

        layout.separator(factor=space_factor)
        box.label(text="Import Options")
        # _*_lp_lc_mod        
        box.prop(self, "add_environment")
        box.prop(self, "import_cameras")
        box.prop(self, "position_camera")
        box.prop(self, "camera_border_percent")
        box.prop(self, "import_lights")
        box.prop(self, "prefer_studio")
        box.prop(self, "prefer_unofficial")
        # _*_mod_end        
        box.prop(self, "use_colour_scheme", expand=True)
        box.prop(self, "resolution", expand=True)
        box.prop(self, "display_logo")
        box.prop(self, "chosen_logo")
        box.prop(self, "use_freestyle_edges")
        box.prop(self, "parent_to_empty")

        layout.separator(factor=space_factor)
        box.label(text="Scaling Options")
        box.prop(self, "scale_strategy")
        box.prop(self, "import_scale")
        box.prop(self, "make_gaps")
        box.prop(self, "gap_scale")

        layout.separator(factor=space_factor)
        box.label(text="Bevel Options")
        box.prop(self, "bevel_edges")
        box.prop(self, "bevel_weight")
        box.prop(self, "bevel_width")
        box.prop(self, "bevel_segments")

        layout.separator(factor=space_factor)
        # _*_lp_lc_mod
        box.label(text="Cleanup Options")
        box.prop(self, "remove_doubles")
        box.prop(self, "merge_distance")
        box.prop(self, "smooth_type", expand=True)
        box.prop(self, "shade_smooth")
        box.prop(self, "recalculate_normals")
        box.prop(self, "triangulate")
        # _*_mod_end

        layout.separator(factor=space_factor)
        # _*_lp_lc_mod
        box.label(text="Meta Commands")
        box.prop(self, "meta_bfc")
        box.prop(self, "meta_texmap")
        box.prop(self, "meta_group")
        box.prop(self, "meta_print_write")
        box.prop(self, "meta_step")
        box.prop(self, "meta_step_groups")
        box.prop(self, "frames_per_step")
        box.prop(self, "set_end_frame")
        box.prop(self, "meta_clear")
        # box.prop(self, "meta_pause")
        box.prop(self, "meta_save")
        box.prop(self, "set_timeline_markers")
        # _*_mod_end

        layout.separator(factor=space_factor)
        # _*_lp_lc_mod
        box.label(text="Extras")
        box.prop(self, "import_edges")
        box.prop(self, "treat_shortcut_as_model")
        box.prop(self, "no_studs")
        box.prop(self, "verbose")
        box.prop(self, "profile")
        # _*_mod_end


def build_import_menu(self, context):
    # _*_lp_lc_mod
    self.layout.operator(IMPORT_OT_do_ldraw_import.bl_idname,
                         text="LPub3D Import LDraw MM (.mpd/.ldr/.l3b/.dat)")
    # _*_mod_end


classesToRegister = [
    IMPORT_OT_do_ldraw_import,
]

# https://wiki.blender.org/wiki/Reference/Release_Notes/2.80/Python_API/Addons
registerClasses, unregisterClasses = bpy.utils.register_classes_factory(classesToRegister)


def register():
    bpy.utils.register_class(IMPORT_OT_do_ldraw_import)
    # _*_lp_lc_mod
    bpy.types.TOPBAR_MT_file_import.prepend(build_import_menu)
    # _*_mod_end


def unregister():
    bpy.utils.unregister_class(IMPORT_OT_do_ldraw_import)
    bpy.types.TOPBAR_MT_file_import.remove(build_import_menu)


if __name__ == "__main__":
    register()
