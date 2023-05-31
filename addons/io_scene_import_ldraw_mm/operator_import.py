import bpy

import time
import os


from io_scene_render_ldraw.modelglobals import model_globals
from bpy_extras.io_utils import ImportHelper
from .import_settings import ImportSettings
from .ldraw_node import LDrawNode
from . import blender_import
from . import ldraw_part_types

class IMPORT_OT_do_ldraw_import(bpy.types.Operator, ImportHelper):
    """Import an LDraw model File"""

    bl_idname = "import_scene.lpub3d_import_ldraw_mm"
    bl_description = "Import LDraw model (.mpd/.ldr/.l3b/.dat)"
    bl_label = "Import LDraw"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    # Declarations
    filename_ext = ""
    ldraw_model_file_loaded = False

    # Preferences declaration
    prefs = ImportSettings.get_settings()

    filter_glob: bpy.props.StringProperty(
        name="Extensions",
        options={'HIDDEN'},
        default="*.mpd;*.ldr;*.dat",
    )

    filepath: bpy.props.StringProperty(
        name="File path",
        description="Filepath used for importing the file",
        maxlen=1024,
        subtype='FILE_PATH',
    )

    ldraw_path: bpy.props.StringProperty(
        name="LDraw path",
        description="Full filepath to the LDraw Parts Library (download from https://www.ldraw.org)",
        default=ImportSettings.get_setting('ldraw_path')
    )

    custom_ldconfig_file: bpy.props.StringProperty(
        name="Custom LDConfig",
        description="Full directory path to specified custom LDraw colours (LDConfig) file",
        default=ImportSettings.get_setting('custom_ldconfig_file'),
    )

    additional_search_paths: bpy.props.StringProperty(
        name="Additional search paths",
        description="Full directory paths, comma delimited, to additional LDraw search paths",
        default=ImportSettings.get_setting('additional_search_paths'),
    )

    environment_file: bpy.props.StringProperty(
        name="Environment file",
        description="Full file path to .exr environment texture file - specify if not using addon default",
        default=ImportSettings.get_setting('environment_file'),
    )

    add_environment: bpy.props.BoolProperty(
        name="Add environment",
        description="Adds a ground plane and environment texture",
        default=ImportSettings.get_setting('add_environment'),
    )

    studio_ldraw_path: bpy.props.StringProperty(
        name="Stud.io LDraw path",
        description="Full filepath to the Stud.io LDraw Parts Library (download from https://www.bricklink.com/v3/studio/download.page)",
        default=ImportSettings.get_setting('studio_ldraw_path'),
    )

    import_cameras: bpy.props.BoolProperty(
        name="Import cameras",
        description="Import camera definitions (from models authored in LPub3D or LeoCAD)",
        default=ImportSettings.get_setting('import_cameras'),
    )

    position_camera: bpy.props.BoolProperty(
        name="Position camera",
        description="Position the camera to show the whole model",
        default=ImportSettings.get_setting('position_camera'),
    )
    
    camera_border_percent: bpy.props.FloatProperty(
        name="Camera Border %",
        description="When positioning the camera, include a (percentage) border around the model in the render",
        default=ImportSettings.get_setting('camera_border_percent'),
        min=0.5,
    ) 
    
    import_lights: bpy.props.BoolProperty(
        name="Import lights",
        description="Import Light definitions (from models authored in LPub3D or LeoCAD)",
        default=ImportSettings.get_setting('import_lights'),
    )    

    prefer_studio: bpy.props.BoolProperty(
        name="Prefer Stud.io library",
        description="Search for parts in Stud.io library first",
        default=ImportSettings.get_setting('prefer_studio'),
    )

    prefer_unofficial: bpy.props.BoolProperty(
        name="Prefer unofficial parts",
        description="Search for unofficial parts first",
        default=ImportSettings.get_setting('prefer_unofficial'),
    )

    resolution: bpy.props.EnumProperty(
        name="Part resolution",
        description="Resolution of part primitives, ie. how much geometry they have",
        default=ImportSettings.get_setting('resolution'),
        items=(
            ("Low", "Low resolution primitives", "Import using low resolution primitives."),
            ("Standard", "Standard primitives", "Import using standard resolution primitives."),
            ("High", "High resolution primitives", "Import using high resolution primitives."),
        ),
    )

    use_colour_scheme: bpy.props.EnumProperty(
        name="Colour scheme options",
        description="Colour scheme options",
        default=ImportSettings.get_setting('use_colour_scheme'),
        items=[
            ("lgeo", "Realistic colours", "Uses the LGEO colour scheme for realistic colours."),
            ("ldraw", "Original LDraw colours", "Uses the standard LDraw colour scheme (LDConfig.ldr)."),
            ("alt", "Alternate LDraw colours", "Uses the alternate LDraw colour scheme (LDCfgalt.ldr)."),
            ("custom", "Custom LDraw colours", "Uses a user specified LDraw colour file.")
        ],
    )

    remove_doubles: bpy.props.BoolProperty(
        name="Remove doubles",
        description="Merge overlapping vertices",
        default=ImportSettings.get_setting('remove_doubles'),
    )

    merge_distance: bpy.props.FloatProperty(
        name="Merge distance",
        description="Maximum distance between elements to merge",
        default=ImportSettings.get_setting('merge_distance'),
        precision=3,
        min=0.0,
    )

    shade_smooth: bpy.props.BoolProperty(
        name="Shade smooth",
        description="Use flat or smooth shading for part faces",
        default=ImportSettings.get_setting('shade_smooth'),
    )

    display_logo: bpy.props.BoolProperty(
        name="Display logo",
        description="Display logo on studs. Requires unofficial parts library to be downloaded",
        default=ImportSettings.get_setting('display_logo'),
    )

    # cast items as list or "EnumProperty(..., default='logo3'): not found in enum members"
    # and a messed up menu
    chosen_logo: bpy.props.EnumProperty(
        name="Chosen logo",
        description="Use this logo on studs",
        default=ImportSettings.get_setting('chosen_logo'),
        items=list(((logo, logo, logo) for logo in ldraw_part_types.logos)),
    )

    smooth_type: bpy.props.EnumProperty(
        name="Smooth type",
        description="Use this strategy to smooth meshes",
        default=ImportSettings.get_setting('smooth_type'),
        items=(
            ("edge_split", "Edge split", "Use an edge split modifier"),
            ("auto_smooth", "Auto smooth", "Use auto smooth"),
            ("bmesh_split", "bmesh smooth", "Split during initial mesh processing"),
        ),
    )

    gap_target: bpy.props.EnumProperty(
        name="Gap target",
        description="Where to apply gap",
        default=ImportSettings.get_setting('gap_target'),
        items=(
            ("object", "Object", "Scale the object to create the gap"),
            ("mesh", "Mesh", "Transform the mesh to create the gap"),
        ),
    )

    gap_scale_strategy: bpy.props.EnumProperty(
        name="Gap strategy",
        description="How to scale the object to create the gap",
        default=ImportSettings.get_setting('gap_scale_strategy'),
        items=(
            ("object", "Object", "Apply gap directly to the object"),
            ("constraint", "Constraint", "Use a constraint, allowing the gap to easily be adjusted later"),
        ),
    )

    no_studs: bpy.props.BoolProperty(
        name="No studs",
        description="Don't import studs",
        default=ImportSettings.get_setting('no_studs'),
    )

    preserve_hierarchy: bpy.props.BoolProperty(
        name="Preserve file structure",
        description="Don't merge the constituent subparts and primitives into the top level part. Some parts may not render properly",
        default=ImportSettings.get_setting('preserve_hierarchy'),
    )

    parent_to_empty: bpy.props.BoolProperty(
        name="Parent to empty",
        description="Parent the model to an empty",
        default=ImportSettings.get_setting('parent_to_empty'),
    )

    import_scale: bpy.props.FloatProperty(
        name="Import scale",
        description="Scale the entire model by this amount",
        default=ImportSettings.get_setting('import_scale'),
        precision=2,
        min=0.01,
        max=1.00,
    )

    make_gaps: bpy.props.BoolProperty(
        name="Make gaps",
        description="Puts small gaps between parts",
        default=ImportSettings.get_setting('make_gaps'),
    )

    gap_scale: bpy.props.FloatProperty(
        name="Gap scale",
        description="Scale parts by this value to make gaps",
        default=ImportSettings.get_setting('gap_scale'),
        precision=3,
        min=0.0,
        max=1.0,
    )

    meta_bfc: bpy.props.BoolProperty(
        name="BFC",
        description="Process BFC meta commands",
        default=ImportSettings.get_setting('meta_bfc'),
    )

    meta_texmap: bpy.props.BoolProperty(
        name="TEXMAP",
        description="Process TEXMAP and DATA meta commands",
        default=ImportSettings.get_setting('meta_texmap'),
    )

    meta_print_write: bpy.props.BoolProperty(
        name="PRINT/WRITE",
        description="Process PRINT/WRITE meta command",
        default=ImportSettings.get_setting('meta_print_write'),
    )

    meta_group: bpy.props.BoolProperty(
        name="GROUP",
        description="Process GROUP meta commands",
        default=ImportSettings.get_setting('meta_group'),
    )

    meta_step: bpy.props.BoolProperty(
        name="STEP",
        description="Process STEP meta command",
        default=ImportSettings.get_setting('meta_step'),
    )

    meta_step_groups: bpy.props.BoolProperty(
        name="STEP Groups",
        description="Create collections for individual steps",
        default=ImportSettings.get_setting('meta_step_groups'),
    )

    meta_clear: bpy.props.BoolProperty(
        name="CLEAR",
        description="Process CLEAR meta command",
        default=ImportSettings.get_setting('meta_clear'),
    )

    meta_pause: bpy.props.BoolProperty(
        name="PAUSE",
        description="Process PAUSE meta command",
        default=ImportSettings.get_setting('meta_pause'),
    )

    meta_save: bpy.props.BoolProperty(
        name="SAVE",
        description="Process SAVE meta command",
        default=ImportSettings.get_setting('meta_save'),
    )

    set_end_frame: bpy.props.BoolProperty(
        name="Set step end frame",
        description="Set the end frame to the last step",
        default=ImportSettings.get_setting('set_end_frame'),
    )

    frames_per_step: bpy.props.IntProperty(
        name="Frames per step",
        description="Frames per step",
        default=ImportSettings.get_setting('frames_per_step'),
        min=1,
    )

    starting_step_frame: bpy.props.IntProperty(
        name="Starting step frame",
        options={'HIDDEN'},
        description="Frame to add the first STEP meta command",
        default=ImportSettings.get_setting('starting_step_frame'),
        min=1,
    )

    set_timeline_markers: bpy.props.BoolProperty(
        name="Set timeline markers",
        description="Set timeline markers for meta commands",
        default=ImportSettings.get_setting('set_timeline_markers'),
    )

    import_edges: bpy.props.BoolProperty(
        name="Import edges",
        description="Import edge meshes",
        default=ImportSettings.get_setting('import_edges'),
    )

    use_freestyle_edges: bpy.props.BoolProperty(
        name="Use Freestyle edges",
        description="Render LDraw edges using freestyle",
        default=ImportSettings.get_setting('use_freestyle_edges'),
    )

    treat_shortcut_as_model: bpy.props.BoolProperty(
        name="Treat shortcuts as models",
        options={'HIDDEN'},
        description="Split shortcut parts into their constituent pieces as if they were models",
        default=ImportSettings.get_setting('treat_shortcut_as_model'),
    )

    treat_models_with_subparts_as_parts: bpy.props.BoolProperty(
        name="Treat models with subparts as parts",
        options={'HIDDEN'},
        description=" ".join([
            "If true and a model has a subpart or primitive, treat it like a part by merging its constituent parts into one object.",
            "If false, add the subparts and primitives as parts of the model"
        ]),
        default=ImportSettings.get_setting('treat_models_with_subparts_as_parts'),
    )

    recalculate_normals: bpy.props.BoolProperty(
        name="Recalculate normals",
        description="Recalculate normals. Not recommended if BFC processing is active",
        default=ImportSettings.get_setting('recalculate_normals'),
    )

    triangulate: bpy.props.BoolProperty(
        name="Triangulate faces",
        description="Triangulate all faces",
        default=ImportSettings.get_setting('triangulate'),
    )

    profile: bpy.props.BoolProperty(
        name="Profile",
        description="Profile import performance",
        default=ImportSettings.get_setting('profile'),
    )

    bevel_edges: bpy.props.BoolProperty(
        name="Bevel edges",
        description="Bevel edges. Can cause some parts to render incorrectly",
        default=ImportSettings.get_setting('bevel_edges'),
    )

    bevel_weight: bpy.props.FloatProperty(
        name="Bevel weight",
        description="Bevel weight",
        default=ImportSettings.get_setting('bevel_weight'),
        precision=1,
        step=10,
        min=0.0,
        max=1.0,
    )

    bevel_width: bpy.props.FloatProperty(
        name="Bevel width",
        description="Bevel width",
        default=ImportSettings.get_setting('bevel_width'),
        precision=1,
        step=10,
        min=0.0,
        max=1.0,
    )

    bevel_segments: bpy.props.IntProperty(
        name="Bevel segments",
        description="Bevel segments",
        default=ImportSettings.get_setting('bevel_segments'),
    )

    search_additional_paths: bpy.props.BoolProperty(
        name="Search Additional Paths",
        description="Search additional LDraw paths (automatically set for fade previous steps and highlight step)",
        default=ImportSettings.get_setting('search_additional_paths'),
    )

    use_archive_library: bpy.props.BoolProperty(
        name="Use Archive Libraries",
        description="Add any archive (zip) libraries in the LDraw file path to the library search list",
        default=ImportSettings.get_setting('use_archive_library'),
    )

    verbose: bpy.props.BoolProperty(
        name="Verbose Output",
        description="Output all messages while working, else only show warnings and errors",
        default=ImportSettings.get_setting('verbose'),
    )

    preferences_file: bpy.props.StringProperty(
        default=r"",
        options={'HIDDEN'}
    )

    #def invoke(self, context, _event):
    #    context.window_manager.fileselect_add(self)
    #    ImportSettings.load_settings()
    #    return {'RUNNING_MODAL'}

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

        use_lpub_settings = False
        if self.preferences_file != "":
            ImportSettings.debugPrint("=====Import MM Settings====")
            ImportSettings.debugPrint(f"Preferences file:    {self.preferences_file}")
            use_lpub_settings = os.path.basename(self.preferences_file) != "ImportOptions.json"
        else:
            ImportSettings.debugPrint("=====Import LDraw MM=======")

        if use_lpub_settings:
            IMPORT_OT_do_ldraw_import.prefs = ImportSettings.get_ini_settings(self.preferences_file)
        else:
            IMPORT_OT_do_ldraw_import.prefs = ImportSettings.get_settings()

        # Initialize model globals
        self.ldraw_model_file_loaded = model_globals.LDRAW_MODEL_LOADED
        model_globals.init()

        self.ldraw_path               = IMPORT_OT_do_ldraw_import.prefs.get("ldraw_path", self.ldraw_path)
        self.studio_ldraw_path        = IMPORT_OT_do_ldraw_import.prefs.get("studio_ldraw_path", self.studio_ldraw_path)

        self.add_environment          = IMPORT_OT_do_ldraw_import.prefs.get("add_environment", self.add_environment)
        self.environment_file         = IMPORT_OT_do_ldraw_import.prefs.get("environment_file", self.environment_file)
        self.import_cameras           = IMPORT_OT_do_ldraw_import.prefs.get("import_cameras", self.import_cameras)
        self.position_camera          = IMPORT_OT_do_ldraw_import.prefs.get("position_camera", self.position_camera)
        self.camera_border_percent    = IMPORT_OT_do_ldraw_import.prefs.get("camera_border_percent", self.camera_border_percent)
        self.import_lights            = IMPORT_OT_do_ldraw_import.prefs.get("import_lights", self.import_lights)
        self.search_additional_paths  = IMPORT_OT_do_ldraw_import.prefs.get("search_additional_paths", self.search_additional_paths)

        self.custom_ldconfig_file     = IMPORT_OT_do_ldraw_import.prefs.get("custom_ldconfig_file",   self.custom_ldconfig_file)
        self.additional_search_paths  = IMPORT_OT_do_ldraw_import.prefs.get("additional_search_paths", self.additional_search_paths)

        self.prefer_studio           = IMPORT_OT_do_ldraw_import.prefs.get("prefer_studio", self.prefer_studio)
        self.prefer_unofficial       = IMPORT_OT_do_ldraw_import.prefs.get("prefer_unofficial", self.prefer_unofficial)
        self.use_colour_scheme       = IMPORT_OT_do_ldraw_import.prefs.get("use_colour_scheme", self.use_colour_scheme)
        self.resolution              = IMPORT_OT_do_ldraw_import.prefs.get("resolution", self.resolution)
        self.display_logo            = IMPORT_OT_do_ldraw_import.prefs.get("display_logo", self.display_logo)
        self.chosen_logo             = IMPORT_OT_do_ldraw_import.prefs.get("chosen_logo", self.chosen_logo)

        self.import_scale            = IMPORT_OT_do_ldraw_import.prefs.get("import_scale", self.import_scale)
        self.parent_to_empty         = IMPORT_OT_do_ldraw_import.prefs.get("parent_to_empty", self.parent_to_empty)
        self.make_gaps               = IMPORT_OT_do_ldraw_import.prefs.get("make_gaps", self.make_gaps)
        self.gap_scale               = IMPORT_OT_do_ldraw_import.prefs.get("gap_scale", self.gap_scale)
        self.gap_target              = IMPORT_OT_do_ldraw_import.prefs.get("gap_target", self.gap_target)
        self.gap_scale_strategy      = IMPORT_OT_do_ldraw_import.prefs.get("gap_scale_strategy", self.gap_scale_strategy)

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
        self.treat_models_with_subparts_as_parts = IMPORT_OT_do_ldraw_import.prefs.get("treat_models_with_subparts_as_parts", self.treat_models_with_subparts_as_parts)
        self.no_studs                = IMPORT_OT_do_ldraw_import.prefs.get("no_studs", self.no_studs)
        self.preserve_hierarchy      = IMPORT_OT_do_ldraw_import.prefs.get("preserve_hierarchy", self.preserve_hierarchy)

        self.profile                 = IMPORT_OT_do_ldraw_import.prefs.get("profile", self.profile)
        self.verbose                 = IMPORT_OT_do_ldraw_import.prefs.get("verbose", self.verbose)

        if self.preferences_file == "":

            IMPORT_OT_do_ldraw_import.prefs["ldraw_path"]              = self.ldraw_path
            IMPORT_OT_do_ldraw_import.prefs["studio_ldraw_path"]       = self.studio_ldraw_path

            IMPORT_OT_do_ldraw_import.prefs['add_environment']         = self.add_environment
            IMPORT_OT_do_ldraw_import.prefs['environment_file']        = self.environment_file
            IMPORT_OT_do_ldraw_import.prefs['import_cameras']          = self.import_cameras
            IMPORT_OT_do_ldraw_import.prefs['position_camera']         = self.position_camera
            IMPORT_OT_do_ldraw_import.prefs['camera_border_percent']   = self.camera_border_percent
            IMPORT_OT_do_ldraw_import.prefs['import_lights']           = self.import_lights
            IMPORT_OT_do_ldraw_import.prefs['search_additional_paths'] = self.search_additional_paths

            IMPORT_OT_do_ldraw_import.prefs['custom_ldconfig_file']    = self.custom_ldconfig_file
            IMPORT_OT_do_ldraw_import.prefs['additional_search_paths'] = self.additional_search_paths

            IMPORT_OT_do_ldraw_import.prefs["prefer_studio"]           = self.prefer_studio
            IMPORT_OT_do_ldraw_import.prefs["prefer_unofficial"]       = self.prefer_unofficial
            IMPORT_OT_do_ldraw_import.prefs["use_colour_scheme"]       = self.use_colour_scheme
            IMPORT_OT_do_ldraw_import.prefs["resolution"]              = self.resolution
            IMPORT_OT_do_ldraw_import.prefs["display_logo"]            = self.display_logo
            IMPORT_OT_do_ldraw_import.prefs["chosen_logo"]             = self.chosen_logo

            IMPORT_OT_do_ldraw_import.prefs["import_scale"]            = self.import_scale
            IMPORT_OT_do_ldraw_import.prefs["parent_to_empty"]         = self.parent_to_empty
            IMPORT_OT_do_ldraw_import.prefs["make_gaps"]               = self.make_gaps
            IMPORT_OT_do_ldraw_import.prefs["gap_scale"]               = self.gap_scale
            IMPORT_OT_do_ldraw_import.prefs["gap_target"]              = self.gap_target
            IMPORT_OT_do_ldraw_import.prefs["gap_scale_strategy"]      = self.gap_scale_strategy

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
            IMPORT_OT_do_ldraw_import.prefs["treat_models_with_subparts_as_parts"] = self.treat_models_with_subparts_as_parts
            IMPORT_OT_do_ldraw_import.prefs["no_studs"]                = self.no_studs
            IMPORT_OT_do_ldraw_import.prefs["preserve_hierarchy"]      = self.preserve_hierarchy

            IMPORT_OT_do_ldraw_import.prefs["profile"]                 = self.profile
            IMPORT_OT_do_ldraw_import.prefs["verbose"]                 = self.verbose

        if self.environment_file == "":
            IMPORT_OT_do_ldraw_import.prefs["environment_file"]        = ImportSettings.get_environment_file()
        else:
            IMPORT_OT_do_ldraw_import.prefs["environment_file"]        = self.environment_file

        assert self.filepath != "", "Model file path not specified."

        ImportSettings.save_settings(IMPORT_OT_do_ldraw_import.prefs)
        ImportSettings.apply_settings()

        model_globals.LDRAW_MODEL_FILE = self.filepath

        # wm = context.window_manager
        # self._timer = wm.event_timer_add(0.01, window=context.window)
        # wm.modal_handler_add(self)
        # self.__i = blender_import.do_import(bpy.path.abspath(self.filepath))
        # return {'RUNNING_MODAL'}

        # https://docs.python.org/3/library/profile.html
        load_result = None
        if self.profile:
            import cProfile
            import pstats

            from pathlib import Path
            prof_output = os.path.join(Path.home(), 'ldraw_import_mm.prof')

            with cProfile.Profile() as profiler:
                load_result = blender_import.do_import(bpy.path.abspath(self.filepath))
            stats = pstats.Stats(profiler)
            stats.sort_stats(pstats.SortKey.TIME)
            stats.print_stats()
            stats.dump_stats(filename=prof_output)
        else:
            load_result = blender_import.do_import(bpy.path.abspath(self.filepath))

        model_globals.LDRAW_MODEL_LOADED = True

        ImportSettings.debugPrint("=====Import MM Complete====")
        if load_result is None:
            ImportSettings.debugPrint("Import MM result: None")
        ImportSettings.debugPrint(f"Model file: {model_globals.LDRAW_MODEL_FILE}")
        ImportSettings.debugPrint(f"Part count: {LDrawNode.part_count}")
        end = time.perf_counter()
        elapsed = end - start
        ImportSettings.debugPrint(f"Elapsed time: {elapsed}")
        ImportSettings.debugPrint("===========================")
        ImportSettings.debugPrint("")

        return {'FINISHED'}

    # https://docs.blender.org/api/current/bpy.types.UILayout.html
    def draw(self, context):
        space_factor = 0.3

        layout = self.layout
        layout.use_property_split = True  # Active single-column layout

        box = layout.box()
        box.label(text="LDraw Import Options", icon='PREFERENCES')
        box.label(text="Import filepaths:", icon='FILEBROWSER')
        box.prop(self, "ldraw_path")
        box.prop(self, "custom_ldconfig_file")
        box.prop(self, "studio_ldraw_path")
        box.prop(self, "search_additional_paths")
        if not self.ldraw_model_file_loaded:
            box.prop(self, "environment_file")

        layout.separator(factor=space_factor)
        box.label(text="Import Options")
        box.prop(self, "add_environment")
        box.prop(self, "import_cameras")
        box.prop(self, "position_camera")
        box.prop(self, "camera_border_percent")
        box.prop(self, "import_lights")
        box.prop(self, "prefer_studio")
        box.prop(self, "prefer_unofficial")
        box.prop(self, "use_colour_scheme", expand=True)
        box.prop(self, "resolution", expand=True)
        box.prop(self, "display_logo")
        box.prop(self, "chosen_logo")
        box.prop(self, "use_freestyle_edges")

        layout.separator(factor=space_factor)
        box.label(text="Scaling Options")
        box.prop(self, "import_scale")
        box.prop(self, "parent_to_empty")
        box.prop(self, "make_gaps")
        box.prop(self, "gap_scale")
        box.prop(self, "gap_target", expand=True)
        box.prop(self, "gap_scale_strategy", expand=True)

        layout.separator(factor=space_factor)
        box.prop(self, "bevel_edges")
        box.prop(self, "bevel_weight")
        box.prop(self, "bevel_width")
        box.prop(self, "bevel_segments")        
        
        layout.separator(factor=space_factor)
        box.label(text="Cleanup Options")
        box.prop(self, "remove_doubles")
        box.prop(self, "merge_distance")
        box.prop(self, "smooth_type", expand=True)
        box.prop(self, "shade_smooth")
        box.prop(self, "recalculate_normals")
        box.prop(self, "triangulate")

        layout.separator(factor=space_factor)
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

        layout.separator(factor=space_factor)
        box.label(text="Extras")
        box.prop(self, "import_edges")
        box.prop(self, "treat_shortcut_as_model")
        box.prop(self, "treat_models_with_subparts_as_parts")
        box.prop(self, "no_studs")
        box.prop(self, "preserve_hierarchy")
        box.prop(self, "verbose")
        box.prop(self, "profile")        


def build_import_menu(self, context):
    self.layout.operator(IMPORT_OT_do_ldraw_import.bl_idname,
                         text="LPub3D Import LDraw MM (.mpd/.ldr/.l3b/.dat)")


classesToRegister = [
    IMPORT_OT_do_ldraw_import,
]

# https://wiki.blender.org/wiki/Reference/Release_Notes/2.80/Python_API/Addons
registerClasses, unregisterClasses = bpy.utils.register_classes_factory(classesToRegister)


def register():
    bpy.utils.register_class(IMPORT_OT_do_ldraw_import)
    bpy.types.TOPBAR_MT_file_import.prepend(build_import_menu)


def unregister():
    bpy.utils.unregister_class(IMPORT_OT_do_ldraw_import)
    bpy.types.TOPBAR_MT_file_import.remove(build_import_menu)


if __name__ == "__main__":
    register()
