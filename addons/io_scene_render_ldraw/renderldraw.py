# -*- coding: utf-8 -*-
"""
Trevor SANDY
Last Update December 31, 2024
Copyright (c) 2020 - 2025 by Trevor SANDY

LPub3D Render LDraw GPLv2 license.

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software Foundation,
Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.


LPub3D Render LDraw

This file defines the LDraw render routines.
"""

import os
import sys
import bpy
import time
import datetime
from .preferences import Preferences;
from .modelglobals import model_globals
from bpy_extras.io_utils import ImportHelper
from io_scene_import_ldraw.importldraw import ImportLDrawOps
from io_scene_import_ldraw.importldraw import loadldraw
from io_scene_import_ldraw_mm.operator_import import ImportSettings
from io_scene_import_ldraw_mm import filesystem
from bpy.props import (StringProperty,
                       IntProperty,
                       FloatProperty,
                       EnumProperty,
                       BoolProperty
                       )

units = (
    # sequence of quadruples, first element is multiplier to apply to
    # previous quadruple, or nr of seconds for first quadruple, second
    # element is abbreviated unit name, third element is singular unit
    # name, fourth element is plural unit name.
    (1, "s", "second", "seconds"),
    (60, "m", "minute", "minutes"),
    (60, "h", "hour", "hours"),
    (24, "d", "day", "days"),
    (7, "wk", "week", "weeks"))

def render_print(message, is_error=False):
    """Print output with identification timestamp."""

    # Current timestamp (with milliseconds trimmed to two places)
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-4]

    message = f"{timestamp} [renderldraw] {message}"

    if is_error:
        sys.stderr.write(f"{message}\n")
        sys.stderr.flush()
    else:
        sys.stdout.write(f"{message}\n")
        sys.stdout.flush()

def format_elapsed(interval, long_form=False, seconds_places=3):
    """
    Returns an accurate indication of the specified interval in seconds.
    long_form indicates whether to display the units in long form or short form,
    while seconds_places indicates the number of decimal places to use for showing
    the seconds.
    """
    unitindex = 0
    result = ""
    while True:
        if unitindex == len(units):
            break
        unit = units[unitindex]
        if unitindex + 1 < len(units):
            factor = units[unitindex + 1][0]
            place = interval % factor
        else:
            factor = None
            place = interval

        place = "{:.{places}f}{}".format(
            place,
            (unit[1], " " + unit[2:4][place != 1])[long_form],
            places=(0, seconds_places)[unitindex == 0]
        )
        result = (
                place
                +
                ("", (" ", (", ", " and ")[unitindex == 1])[long_form])[unitindex > 0]
                +
                result
        )
        if factor is None:
            break
        interval //= factor
        if interval == 0:
            break
        unitindex += 1
    # end while
    return result

# end format_elapsed


class RenderLDrawOps(bpy.types.Operator, ImportHelper):
    """Render LDraw - Render Operator."""

    bl_idname = "render_scene.lpub3d_render_ldraw"
    bl_description = "Render LDraw model (.png)"
    bl_label = "Render LDraw Model"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    prefs = type('', (), {})()
    image_file_name = 'rendered_ldraw_image.png'
    image_directory = os.path.abspath(os.path.expanduser('~'))
    image_file_path = os.path.join(image_directory, image_file_name)
    config_file = os.path.join(os.path.dirname(__file__), "config", "LDrawRendererPreferences.ini")
    blender_addons_path = bpy.utils.user_resource('SCRIPTS', path="addons")

    ldraw_model_loaded = False

    temp_image_file = None
    task_status     = None

    # Define variables to register
    _start_time = None
    _timer      = None
    complete    = None
    stop        = None
    busy        = None
    tasks       = None

    use_ldraw_import = True
    for addon in bpy.context.preferences.addons:
        if addon.module == 'io_scene_import_ldraw_mm':
            use_ldraw_import = False
            break
        if addon.module == 'io_scene_import_ldraw':
            use_ldraw_import = True
            break
    
    if not use_ldraw_import:
        prefs = Preferences(None, None, "MM")
        preferences_folder = os.path.join(blender_addons_path, "io_scene_import_ldraw_mm", "config")
    else:
        prefs = Preferences(None, None, "TN")
        preferences_folder = os.path.join(blender_addons_path, "io_scene_import_ldraw", "config")

    model_file: StringProperty(
        name="",
        description="Specify LDraw model file absolute file path - required",
        default=r""
    )

    blend_file: StringProperty(
        name="",
        description="Specify absolute file path to supplement blend file - optional",
        default=prefs.get('blendfile', r"") if use_ldraw_import else prefs.get('blend_file', r"")
    )

    ldraw_path: StringProperty(
        name="",
        description="Full filepath to the LDraw Parts Library (download from http://www.ldraw.org)",
        default=prefs.get('ldrawdirectory', r"") if use_ldraw_import else prefs.get('ldraw_path', r"")
    )

    resolution_width: IntProperty(
        name="Resolution (X)",
        description="Specify the render resolution width (x) in pixels",
        default=prefs.get('resolutionwidth', 800) if use_ldraw_import else prefs.get('resolution_width', 800)
    )

    resolution_height: IntProperty(
        name="Resolution (Y)",
        description="Specify the render resolution height (y) in pixels",
        default=prefs.get('resolutionheight', 600) if use_ldraw_import else prefs.get('resolution_height', 600)
    )

    render_percentage: FloatProperty(
        name="Render Percentage",
        description="Specify the percentage of the render size at which to generate the image",
        default=prefs.get('renderpercentage', 100.0) if use_ldraw_import else prefs.get('render_percentage', 100.0)
    )

    overwrite_image: BoolProperty(
        name="Overwrite Rendered Image",
        description="Specify whether to overwrite an existing rendered image file.",
        default=prefs.get('overwriteimage', False) if use_ldraw_import else prefs.get('overwrite_image', False)
    )

    blendfile_trusted: BoolProperty(
        name="Trusted Blend File",
        description="Specify whether to treat the .blend file as being loaded from a trusted source.",
        default=prefs.get('blendfiletrusted', False) if use_ldraw_import else prefs.get('blendfile_trusted', False)
    )

    transparent_background: BoolProperty(
        name="Transparent Background",
        description="Specify whether to render a background  (affects 'Photo-realistic look only).",
        default=prefs.get('transparentbackground', False) if use_ldraw_import else prefs.get('transparent_background', False)
    )

    add_environment: BoolProperty(
        name="Add Environment",
        description="Adds a ground plane and environment texture (for realistic look only)",
        default=prefs.get('addenvironment', True) if use_ldraw_import else prefs.get('add_environment', False)
    )

    crop_image: BoolProperty(
        name="Crop Image",
        description="Crop the image border at opaque content. Requires transparent background set to True",
        default=prefs.get('cropimage', False) if use_ldraw_import else prefs.get('crop_image', False),
    )

    render_window: BoolProperty(
        name="Display Render Window",
        description="Specify whether to display the render window during Blender user interface image render",
        default=prefs.get('renderwindow', True) if use_ldraw_import else prefs.get('render_window', True)
    )

    use_look: EnumProperty(
        name="Overall Look",
        description="Realism or Schematic look",
        default=prefs.get('uselook', 'normal') if use_ldraw_import else 'normal',
        items=(
            ("normal", "Realistic Look", "Render to look realistic."),
            ("instructions", "Lego Instructions Look", "Render to look like the instruction book pictures."),
        )
    )

    search_additional_paths: BoolProperty(
        name="Search Additional Paths",
        description="Search additional LDraw paths (automatically set for fade previous steps and highlight step)",
        default=prefs.get('searchadditionalpaths', False) if use_ldraw_import else prefs.get('search_additional_paths', False)
    )

    verbose: BoolProperty(
        name="Verbose Output",
        description="Output all messages while working, else only show warnings and errors",
        default=prefs.get('verbose', True)
    )

    load_ldraw_model: BoolProperty(
        name="Load LDraw Model",
        description="Specify whether to load the specified LDraw model before rendering - default is True).",
        default=True
    )

    # Hidden properties
    use_ldraw_import_mm: BoolProperty(
        default=not bool(use_ldraw_import),
        options={'HIDDEN'}
    )

    cli_render: BoolProperty(
        default=False,
        options={'HIDDEN'}
    )

    import_only: BoolProperty(
        default=False,
        options={'HIDDEN'}
    )

    environment_file: StringProperty(
        name="",
        default=prefs.get('environmentfile', r"") if use_ldraw_import else prefs.get('environment_file', r""),
        options={'HIDDEN'}
    )

    image_file: StringProperty(
        default=image_file_path,
        options={'HIDDEN'}
    )
    
    preferences_file: StringProperty(
        default=config_file,
        options={'HIDDEN'}
    )

    # File type filter in file browser
    filename_ext = ".png"
    filter_glob: StringProperty(
        default="*.png",
        options={'HIDDEN'}
    )
    # End Hidden properties

    # Define handler functions. I use pre and post to know if Blender "is busy"
    def pre(self, dummyfoo, dummyboo):
        self.busy = True

    # Post is triggered after each frame
    def post(self, dummyfoo, dummyboo):
        self.busy = False

    # Complete is triggered after the entire render job
    def completed(self, dummyfoo, dummyboo):
        self.complete = True

    def cancelled(self, dummyfoo, dummyboo):
        self.stop = True

    def releaseHandlers(self, context):
        bpy.app.handlers.render_pre.remove(self.pre)
        bpy.app.handlers.render_post.remove(self.post)
        bpy.app.handlers.render_cancel.remove(self.cancelled)
        bpy.app.handlers.render_complete.remove(self.completed)
        bpy.app.handlers.render_complete.remove(self.autocropImage)
        context.window_manager.event_timer_remove(self._timer)

    # Print function
    def debugPrint(self, message):
        """Debug print"""

        if self.verbose:
            render_print(message)

    def autocropImage(self, dummyfoo, dummyboo):
        """Crop images with transparent background on opaque bounds"""

        self.task_status = None
        if self.crop_image:
            if self.transparent_background and not self.add_environment:
                import importlib
                package_spec = importlib.util.find_spec("PIL")
                if package_spec is not None:
                    from PIL import Image

                    # Get the opaque bounding box
                    pil_image = Image.open(self.image_file)
                    cropped_box = pil_image.convert("RGBa").getbbox()
                    self.debugPrint(f"Rendered Image Size: w{pil_image.width} x h{pil_image.height}")

                    # Crop the image
                    pil_image = pil_image.crop(cropped_box)
                    self.debugPrint(f"Cropped Image Size:  w{pil_image.width} x h{pil_image.height}")

                    if pil_image:
                        with open(self.image_file, 'wb') as image_file:
                            pil_image.save(image_file, format='PNG')
                else:
                    self.task_status = f"{os.path.basename(self.image_file)} 'Crop failed. Pillow package not installed."
            else:
                self.task_status = "Crop failed. Transparent Background and/or Add Environment settings not satisfied."

        now = time.time()

        if self.task_status is not None:
            self.report({'ERROR'}, f"{self.task_status}. Elapsed Time: {format_elapsed(now - self._start_time)}")
        else:
            render_print(f"SUCCESS: {os.path.basename(self.image_file)} rendered. Elapsed Time: {format_elapsed(now - self._start_time)}")

    # Render function
    def performRenderTask(self):
        """Render ldraw model."""

        if not self.cli_render:
            if not self.render_window:
                self.debugPrint("Performing Render Task Without Preview Window...")
            else:
                self.debugPrint("Performing Render Task With Preview Window...")

        if self.blend_file:
            self.debugPrint(f"Apply blend file {self.blend_file} - Trusted: {self.blendfile_trusted}")
            bpy.ops.wm.open_mainfile(filepath=self.blend_file, use_scripts=self.blendfile_trusted)
        # end if

        active_scene = bpy.context.scene
        if self.render_percentage is not None:
            active_scene.render.resolution_percentage = int(self.render_percentage)
        # end if
        if self.resolution_width is not None:
            active_scene.render.resolution_x = self.resolution_width
        # end if
        if self.resolution_height is not None:
            active_scene.render.resolution_y = self.resolution_height
        # end if
        if self.crop_image and self.add_environment:
            self.report({'WARNING'}, "'Crop Image' specified but 'Add Environment' is set to True")
        # end if
        if self.crop_image and not self.transparent_background:
            self.report({'WARNING'}, "'Crop Image' specified but 'Transparent Background' is set to False")
        # end if
        if self.transparent_background and self.use_look == 'normal':
            if active_scene.render.engine == 'CYCLES':
                active_scene.render.image_settings.color_mode = 'RGBA'
                active_scene.render.film_transparent = True
        # end if

        if not self.overwrite_image and os.path.exists(self.image_file):
            self.report({'ERROR'}, f"ERROR LDraw image '{self.image_file}' already exists")
        else:
            self._start_time = time.time()

            if self.filepath:
                self.image_file = self.filepath
            elif not self.image_file:
                self.image_file = self.image_file_path
            # end if

            active_scene.render.image_settings.file_format = "PNG"
            active_scene.render.filepath = self.image_file

            # Set display mode
            if self.cli_render or not self.render_window:
                bpy.ops.render.render('EXEC_DEFAULT', write_still=True)
            else:
                bpy.ops.render.render('INVOKE_DEFAULT', write_still=True)
            # end if

        # end if (overwrite)

    def debugPrintPreferences(self):
        self.debugPrint("-------------------------")
        if self.use_ldraw_import:
            self.debugPrint(f"Look:                {self.use_look}")
        if self.load_ldraw_model:
            self.debugPrint(f"Resolution_Width:    {self.resolution_width}")
            self.debugPrint(f"Resolution_Height:   {self.resolution_height}")
            self.debugPrint(f"Render_Percentage:   {self.render_percentage}")
        self.debugPrint(f"Add_Environment:     {self.add_environment}")
        self.debugPrint(f"Overwrite_Image:     {self.overwrite_image}")
        self.debugPrint(f"Trans_Background:    {self.transparent_background}")
        self.debugPrint(f"Crop_Image:          {self.crop_image}")
        if not self.cli_render:
            self.debugPrint(f"Render_Window:       {self.render_window}")
        if not self.blend_file == "":
            self.debugPrint(f"Blendfile_Trusted:   {self.blendfile_trusted}")
            self.debugPrint(f"Blend_File:          {self.blend_file}")
        if not self.environment_file == "" and self.add_environment:
            self.debugPrint(f"Environment_File:    {self.environment_file}")

    def setImportLDrawPreferences(self):
        """Import parameter settings when running from command line or LDraw file already loaded."""

        if self.use_ldraw_import_mm:
            if self.ldraw_model_loaded:
                self.resolution_width        = ImportSettings.get_setting("resolution_width")
                self.resolution_height       = ImportSettings.get_setting("resolution_height")
                self.render_percentage       = ImportSettings.get_setting("render_percentage")
                self.search_additional_paths = ImportSettings.get_setting("search_additional_paths")
            self.add_environment         = ImportSettings.get_setting('add_environment')
            self.overwrite_image         = ImportSettings.get_setting("overwrite_image")
            self.transparent_background  = ImportSettings.get_setting("transparent_background")
            self.crop_image              = ImportSettings.get_setting("crop_image")
            self.render_window           = ImportSettings.get_setting("render_window")
            self.blendfile_trusted       = ImportSettings.get_setting("blendfile_trusted")
            self.blend_file              = ImportSettings.get_setting("blend_file")
            self.verbose                 = ImportSettings.get_setting("verbose")
        elif self.use_ldraw_import:
            if self.ldraw_model_loaded:
                self.resolution_width        = ImportLDrawOps.prefs.get('resolutionwidth',  self.resolution_width)
                self.resolution_height       = ImportLDrawOps.prefs.get('resolutionheight', self.resolution_height)
                self.render_percentage       = ImportLDrawOps.prefs.get('renderpercentage', self.render_percentage)
                self.search_additional_paths = ImportLDrawOps.prefs.get('searchadditionalpaths', self.search_additional_paths)
            self.use_look                = ImportLDrawOps.prefs.get('uselook',          self.use_look)
            self.add_environment         = ImportLDrawOps.prefs.get('addenvironment',   self.add_environment)
            self.overwrite_image         = ImportLDrawOps.prefs.get('overwriteimage',   self.overwrite_image)
            self.transparent_background  = ImportLDrawOps.prefs.get('transparentbackground', self.transparent_background)
            self.crop_image              = ImportLDrawOps.prefs.get('cropimage',        self.crop_image)
            self.render_window           = ImportLDrawOps.prefs.get('renderwindow',     self.render_window)
            self.blendfile_trusted       = ImportLDrawOps.prefs.get('blendfiletrusted', self.blendfile_trusted)
            self.blend_file              = ImportLDrawOps.prefs.get('blendfile',        self.blend_file)
            self.verbose                 = ImportLDrawOps.prefs.get('verbose',          self.verbose)
        self.debugPrintPreferences()

    def draw(self, context):
        """Display render options."""

        layout = self.layout
        layout.use_property_split = True  # Active single-column layout

        box = layout.box()
        box.label(text="LDraw Render Options", icon='PREFERENCES')
        if not self.ldraw_model_loaded and self.ldraw_path == "":
            box.label(text="LDraw Parts Folder:", icon='FILEBROWSER')
            box.prop(self, "ldraw_path")
        box.label(text="Model File:", icon='FILEBROWSER')
        box.prop(self, "model_file")
        if not self.ldraw_model_loaded:
            box.label(text="Environment File:", icon='FILEBROWSER')
            box.prop(self, "environment_file")
        box.label(text="Supplemental Blend File:", icon='FILEBROWSER')
        box.prop(self, "blend_file")

        box.prop(self, "resolution_width")
        box.prop(self, "resolution_height")
        box.prop(self, "render_percentage")

        box.prop(self, "render_window")
        box.prop(self, "overwrite_image")
        box.prop(self, "blendfile_trusted")

        if not self.ldraw_model_loaded:
            box.prop(self, "use_ldraw_import_mm")
            box.prop(self, "load_ldraw_model")

        if not self.use_ldraw_import_mm:
            box.prop(self, "use_look", expand=True)

        box.prop(self, "add_environment")
        box.prop(self, "transparent_background")
        box.prop(self, "crop_image")
        box.prop(self, "verbose")

    def invoke(self, context, event):
        """Setup render options."""

        self.debugPrint("-------------------------")
        self.debugPrint("Performing GUI Render Task...")
        self.debugPrint("-------------------------")

        self.use_ldraw_import = not bool(self.use_ldraw_import_mm)

        if self.use_ldraw_import_mm:
            RenderLDrawOps.prefs      = ImportSettings.get_settings()
            self.ldraw_path           = RenderLDrawOps.prefs.get('ldraw_path', filesystem.locate_ldraw())
            if model_globals.LDRAW_MODEL_LOADED:
                self.ldraw_model_loaded = True
                self.load_ldraw_model = False
        elif self.use_ldraw_import:
            import_preferences_file   = os.path.join(self.preferences_folder, 'ImportLDrawPreferences.ini')
            RenderLDrawOps.prefs      = Preferences(import_preferences_file.replace('/', os.path.sep))
            self.ldraw_path           = RenderLDrawOps.prefs.get('ldrawdirectory', loadldraw.Configure.findDefaultLDrawDirectory())
            if model_globals.LDRAW_MODEL_LOADED:
                self.ldraw_model_loaded = True
                self.load_ldraw_model = False

        if self.use_ldraw_import_mm:
            self.debugPrint("Use_LDraw_Import_MM: True")
        elif self.use_ldraw_import:
            self.debugPrint("Use_LDraw_Import:    True")
        self.debugPrint(f"Import_Only:         {self.import_only}")
        self.debugPrint(f"CLI_Render:          {self.cli_render}")
        self.debugPrint(f"Load_LDraw_Model:    {self.load_ldraw_model}")
        self.debugPrint(f"Search_Addl_Paths:   {self.search_additional_paths}")

        if self.ldraw_model_loaded:
            self.model_file = model_globals.LDRAW_MODEL_FILE
            self.image_file = model_globals.LDRAW_IMAGE_FILE
            if self.image_file == "":
                self.image_file = self.model_file + '.png'
            self.debugPrint(f"Loaded Model File:   {self.model_file}")
            self.setImportLDrawPreferences()
            self.debugPrint(f"Image_File:          {self.image_file}")
        else:
            if self.use_ldraw_import_mm:
                self.add_environment         = RenderLDrawOps.prefs.get('add_environment',         self.add_environment)
                self.environment_file        = RenderLDrawOps.prefs.get('environment_file',        self.environment_file)
                self.overwrite_image         = RenderLDrawOps.prefs.get('overwrite_image',         self.overwrite_image)
                self.transparent_background  = RenderLDrawOps.prefs.get('transparent_background',  self.transparent_background)
                self.crop_image              = RenderLDrawOps.prefs.get('crop_image',              self.crop_image)
                self.render_window           = RenderLDrawOps.prefs.get('render_window',           self.render_window)
                self.blendfile_trusted       = RenderLDrawOps.prefs.get('blendfile_trusted',       self.blendfile_trusted)
                self.blend_file              = RenderLDrawOps.prefs.get('blend_file',              self.blend_file)
                self.search_additional_paths = RenderLDrawOps.prefs.get('search_additional_paths', self.search_additional_paths)
                self.verbose                 = RenderLDrawOps.prefs.get('verbose',                 self.verbose)
            elif self.use_ldraw_import:
                self.use_look                = RenderLDrawOps.prefs.get('uselook',               self.use_look)
                self.add_environment         = RenderLDrawOps.prefs.get('addenvironment',        self.add_environment)
                self.environment_file        = RenderLDrawOps.prefs.get('environmentfile',       self.environment_file)
                self.overwrite_image         = RenderLDrawOps.prefs.get('overwriteimage',        self.overwrite_image)
                self.transparent_background  = RenderLDrawOps.prefs.get('transparentbackground', self.transparent_background)
                self.crop_image              = RenderLDrawOps.prefs.get('cropimage',             self.crop_image)
                self.render_window           = RenderLDrawOps.prefs.get('renderwindow',          self.render_window)
                self.blendfile_trusted       = RenderLDrawOps.prefs.get('blendfiletrusted',      self.blendfile_trusted)
                self.blend_file              = RenderLDrawOps.prefs.get('blendfile',             self.blend_file)
                self.search_additional_paths = RenderLDrawOps.prefs.get('searchadditionalpaths', self.search_additional_paths)
                self.verbose                 = RenderLDrawOps.prefs.get('verbose',               self.verbose)

        if not self.filepath:
            blend_filepath = context.blend_data.filepath
            if not blend_filepath:
                blend_filepath = self.image_file
            else:
                blend_filepath = os.path.splitext(blend_filepath)[0]

            self.filepath = blend_filepath

        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        """Render LDraw model."""

        # Confirm minimum Blender version
        if bpy.app.version < (2, 82, 0):
            self.report({'ERROR'}, 'The RenderLDraw addon requires Blender 2.82 or greater.')
            return {'FINISHED'}

        self.use_ldraw_import = not bool(self.use_ldraw_import_mm)

        self.debugPrint("-------------------------")
        if self.cli_render:
            self.debugPrint("Performing Headless Render Task...")
            self.debugPrint("-------------------------")

        import_preferences_file = ""
        if self.use_ldraw_import_mm:
            import_preferences_file = os.path.join(self.preferences_folder, 'ImportOptions.json')
            if model_globals.LDRAW_MODEL_LOADED:
                self.load_ldraw_model = False
                RenderLDrawOps.prefs  = ImportSettings.get_settings()
        elif self.use_ldraw_import:
            import_preferences_file = os.path.join(self.preferences_folder, 'ImportLDrawPreferences.ini')
            if model_globals.LDRAW_MODEL_LOADED:
                self.load_ldraw_model = False
                RenderLDrawOps.prefs  = Preferences(import_preferences_file.replace('\\', os.path.sep).replace('/', os.path.sep))

        if not self.load_ldraw_model:
            self.model_file       = model_globals.LDRAW_MODEL_FILE
            self.image_file       = model_globals.LDRAW_IMAGE_FILE
        
        self.debugPrint(f"Preferences_File:    {self.preferences_file}")
        self.debugPrint(f"Model_File:          {self.model_file}")
        self.debugPrint(f"Image_File:          {self.image_file}")
        self.debugPrint(f"Verbose:             {self.verbose}")

        if self.load_ldraw_model:
            assert self.preferences_file != "", "Preference file path not specified."

            start_time = time.time()

            self.debugPrint("-------------------------")
            if self.cli_render:
                self.debugPrint("Performing Headless Load Task...")
            else:
                self.debugPrint("Performing GUI Load Task...")
            self.debugPrint("-------------------------")
            if self.use_ldraw_import_mm:
                self.debugPrint("Use_LDraw_Import_MM: True")
            elif self.use_ldraw_import:
                self.debugPrint("Use_LDraw_Import: True")
            self.debugPrint(f"Import_Only:         {self.import_only}")
            self.debugPrint(f"CLI_Render:          {self.cli_render}")
            self.debugPrint(f"Load_LDraw_Model:    {self.load_ldraw_model}")
            self.debugPrint(f"Search_Addl_Paths:   {self.search_additional_paths}")
            self.debugPrint(f"Image_File:          {self.image_file}")

            # Load LDraw Preferences
            if self.use_ldraw_import_mm:
                RenderLDrawOps.prefs = Preferences(self.preferences_file, import_preferences_file, "MM")
                self.ldraw_path = RenderLDrawOps.prefs.get('ldraw_path', filesystem.locate_ldraw())
            elif self.use_ldraw_import:
                RenderLDrawOps.prefs = Preferences(self.preferences_file, import_preferences_file, "TN")
                self.ldraw_path = RenderLDrawOps.prefs.get('ldrawdirectory', loadldraw.Configure.findDefaultLDrawDirectory())

            assert self.ldraw_path != "", "LDraw library path not specified."
            assert self.image_file != "", "Image file path not specified."
            assert self.model_file != "", "Model file path not specified."

            if self.use_ldraw_import_mm:
                RenderLDrawOps.prefs.set('search_additional_paths', self.search_additional_paths)
                if self.cli_render:
                    self.add_environment = RenderLDrawOps.prefs.get('add_environment', self.add_environment)
                else:
                    RenderLDrawOps.prefs.set('add_environment',         self.add_environment)
                    RenderLDrawOps.prefs.set('environment_file',        self.environment_file)
                    RenderLDrawOps.prefs.set('ldraw_path',              self.ldraw_path)
                    RenderLDrawOps.prefs.set('overwrite_image',         self.overwrite_image)
                    RenderLDrawOps.prefs.set('transparent_background',  self.transparent_background)
                    RenderLDrawOps.prefs.set('crop_image',              self.crop_image)
                    RenderLDrawOps.prefs.set('render_window',           self.render_window)
                    RenderLDrawOps.prefs.set('blendfile_trusted',       self.blendfile_trusted)
                    RenderLDrawOps.prefs.set('blend_file',              self.blend_file)
                    RenderLDrawOps.prefs.set('verbose',                 self.verbose)
            elif self.use_ldraw_import:
                RenderLDrawOps.prefs.set('searchadditionalpaths', self.search_additional_paths)
                if self.cli_render:
                    self.add_environment = RenderLDrawOps.prefs.get('addenvironment', self.add_environment)
                else:
                    RenderLDrawOps.prefs.set('searchadditionalpaths', self.search_additional_paths)
                    RenderLDrawOps.prefs.set('uselook',               self.use_look)
                    RenderLDrawOps.prefs.set('addenvironment',        self.add_environment)
                    RenderLDrawOps.prefs.set('environmentfile',       self.environment_file)
                    RenderLDrawOps.prefs.set('ldrawdirectory',        self.ldraw_path)
                    RenderLDrawOps.prefs.set('overwriteimage',        self.overwrite_image)
                    RenderLDrawOps.prefs.set('transparentbackground', self.transparent_background)
                    RenderLDrawOps.prefs.set('cropimage',             self.crop_image)
                    RenderLDrawOps.prefs.set('renderwindow',          self.render_window)
                    RenderLDrawOps.prefs.set('blendfiletrusted',      self.blendfile_trusted)
                    RenderLDrawOps.prefs.set('blendfile',             self.blend_file)
                    RenderLDrawOps.prefs.set('verbose',               self.verbose)

            RenderLDrawOps.prefs.save()

            self.debugPrintPreferences()

            if self.use_ldraw_import_mm:
                kwargs = {'filepath': self.model_file, 'renderLDraw': True}
                load_result = bpy.ops.import_scene.lpub3d_import_ldraw_mm('EXEC_DEFAULT', **kwargs)
            elif self.use_ldraw_import:
                kwargs = {'modelFile': self.model_file, 'renderLDraw': True}
                load_result = bpy.ops.import_scene.lpub3d_import_ldraw('EXEC_DEFAULT', **kwargs)

            if self.cli_render:
                model_globals.LDRAW_IMAGE_FILE = self.image_file

            # Check blend file and create if not exist
            #if self.cli_render and self.preferences_file:
            #    default_blend_file_directory = os.path.dirname(self.preferences_file)
            #    default_blend_file = os.path.abspath(os.path.join(default_blend_file_directory, 'lpub3d.blend'))
            #    if not os.path.exists(default_blend_file):
            #        bpy.ops.wm.save_mainfile(filepath=default_blend_file)
            #        self.debugPrint("Save default blend file to {0}".format(default_blend_file))

            now = time.time()

            if load_result != {'FINISHED'}:
                self.report({'ERROR'}, f"ERROR - import '{os.path.basename(self.model_file)}' failed with result {load_result}. Elapsed time {format_elapsed(now - start_time)}")

        if self.cli_render:
            if not self.import_only:
                # Get preferences properties from import module
                if self.load_ldraw_model:
                    self.setImportLDrawPreferences()

                # Register auto crop
                bpy.app.handlers.render_complete.append(self.autocropImage)

                # Render image
                self.performRenderTask()

                # Cleanup handler
                bpy.app.handlers.render_complete.remove(self.autocropImage)

            return {'FINISHED'}

        self.setImportLDrawPreferences()

        # Define the variables during execution. This allows us to define when called from a button
        self.complete = False
        self.stop     = False
        self.busy     = False

        # Set task(s)
        self.tasks = ['RENDER_TASK']
        # self.tasks = ['LOAD_TASK', 'RENDER_TASK']

        # Add the handlers
        bpy.app.handlers.render_pre.append(self.pre)
        bpy.app.handlers.render_post.append(self.post)
        bpy.app.handlers.render_cancel.append(self.cancelled)
        bpy.app.handlers.render_complete.append(self.completed)
        bpy.app.handlers.render_complete.append(self.autocropImage)

        # The timer gets created and the modal handler is added to the window manager
        self._timer = context.window_manager.event_timer_add(0.5, window=context.window)
        context.window_manager.modal_handler_add(self)

        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        """Render Modal."""

        if event.type in {'ESC'}:

            self.report({'WARNING'}, 'Render operation cancelled.')

            self.releaseHandlers(context)

            self.stop = True

            return {'CANCELLED'}

        if event.type == 'TIMER':  # This event is signaled every half a second and will start the render if available

            # If cancelled or no more tasks to render, finish.
            if True in (not self.tasks and self.complete is True, self.stop is True):

                # We remove the handlers and the modal timer to clean everything
                self.releaseHandlers(context)

                self.debugPrint("Render operation finished.")
                return {"FINISHED"}

            elif self.busy is False:  # Not currently busy. Perform task.

                # Perform task
                if self.tasks and self.tasks[0] == 'RENDER_TASK':

                    self.performRenderTask()

                # Remove current task from list. Perform next task
                if self.tasks:
                    self.tasks.pop(0)

            # (busy)
            return {'PASS_THROUGH'}

        # (timer)
        return {"PASS_THROUGH"}
        # This is very important! If we used "RUNNING_MODAL", this new modal function
        # would prevent the use of the X button to cancel rendering, because this
        # button is managed by the modal function of the render operator,
        # not this new operator!
