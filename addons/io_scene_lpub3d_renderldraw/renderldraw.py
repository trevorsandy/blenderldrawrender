# -*- coding: utf-8 -*-
"""
Trevor SANDY
Last Update January 20, 2023
Copyright (c) 2020 - 2023 by Trevor SANDY

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

"""

"""
LPub3D Render LDraw

This file defines the LDraw render routines.
"""

import os
import sys
import bpy
import time
import datetime
from bpy_extras.io_utils import ExportHelper
from io_scene_lpub3d_importldraw import importldraw
from bpy.props import (StringProperty,
                       IntProperty,
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


def render_print(message):
    """Debug print with identification timestamp."""

    # Current timestamp (with milliseconds trimmed to two places)
    timestamp = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-4]

    message = "{0} [renderldraw] {1}".format(timestamp, message)
    sys.stdout.write("{0}\n".format(message))
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


class RenderLDrawOps(bpy.types.Operator, ExportHelper):
    """LPub3D Render LDraw - Render Operator."""

    bl_idname = "render_scene.lpub3drenderldraw"
    bl_description = "Render LDraw model (.png)"
    bl_label = "Render LDraw Model"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    image_file_name = 'rendered_ldraw_image.png'
    prefs_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../io_scene_lpub3d_importldraw'))
    prefs_file_path = os.path.join(prefs_directory, 'ImportLDrawPreferences.ini')
    image_directory = os.path.abspath(os.path.expanduser("~"))
    image_file_path = os.path.join(image_directory, image_file_name)

    temp_image_file = None
    task_status     = None

    # Define variables to register
    _start_time = None
    _timer      = None
    complete    = None
    stop        = None
    busy        = None
    tasks       = None

    # Preferences (used to confirm LDraw path and crop settings)
    prefs       = type('', (), {})()

    # Properties
    model_file: StringProperty(
        name="",
        description="Specify LDraw model file absolute file path - required",
        default=r""
    )

    blend_file: StringProperty(
        name="",
        description="Specify absolute file path to supplement blend file - optional",
        default=r"",
    )

    ldraw_path: StringProperty(
        name="",
        description="Full filepath to the LDraw Parts Library (download from http://www.ldraw.org)",
        default=r""
    )

    resolution_width: IntProperty(
        name="Resolution (X)",
        description="Specify the render resolution width (x) in pixels",
        default=800
    )

    resolution_height: IntProperty(
        name="Resolution (Y)",
        description="Specify the render resolution height (y) in pixels",
        default=600
    )

    render_percentage: IntProperty(
        name="Render Percentage",
        description="Specify the percentage of the render size at which to generate the image",
        default=100
    )

    overwrite_image: BoolProperty(
        name="Overwrite Rendered Image",
        description="Specify whether to overwrite an existing rendered image file.",
        default=False
    )

    blendfile_trusted: BoolProperty(
        name="Trusted Blend File",
        description="Specify whether to treat the .blend file as being loaded from a trusted source.",
        default=False
    )

    transparent_background: BoolProperty(
        name="Transparent Background",
        description="Specify whether to render a background  (affects 'Photo-realistic look only).",
        default=False
    )

    add_environment: BoolProperty(
        name="Add Environment",
        description="Adds a ground plane and environment texture (for realistic look only)",
        default=True
    )

    crop_image: BoolProperty(
        name="Crop Image",
        description="Crop the image border at opaque content. Requires transparent background set to True",
        default=False,
    )

    render_window: BoolProperty(
        name="Display Render Window",
        description="Specify whether to display the render window during Blender user interface image render",
        default=True
    )

    load_ldraw_model: BoolProperty(
        name="Load LDraw Model",
        description="Specify whether to load the specified LDraw model before rendering - default is True).",
        default=True
    )

    use_look: EnumProperty(
        name="Overall Look",
        description="Realism or Schematic look",
        default="normal",
        items=(
            ("normal", "Realistic Look", "Render to look realistic."),
            ("instructions", "Lego Instructions Look", "Render to look like the instruction book pictures."),
        )
    )

    search_additional_paths: BoolProperty(
        name="Search Additional Paths",
        description="Search additional LDraw paths (automatically set for fade previous steps and highlight step)",
        default=False
    )

    verbose: BoolProperty(
        name="Verbose Output",
        description="Output all messages while working, else only show warnings and errors",
        default=True
    )

    # Hidden properties
    cli_render: BoolProperty(
        default=False,
        options={'HIDDEN'}
    )

    import_only: BoolProperty(
        default=False,
        options={'HIDDEN'}
    )

    image_file: StringProperty(
        default=image_file_path,
        options={'HIDDEN'}
    )

    preferences_file: StringProperty(
        default=prefs_file_path,
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
    def complete(self, dummyfoo, dummyboo):
        self.complete = True

    def cancelled(self, dummyfoo, dummyboo):
        self.stop = True

    def releaseHandlers(self, context):
        bpy.app.handlers.render_pre.remove(self.pre)
        bpy.app.handlers.render_post.remove(self.post)
        bpy.app.handlers.render_cancel.remove(self.cancelled)
        bpy.app.handlers.render_complete.remove(self.complete)
        bpy.app.handlers.render_complete.remove(self.autocropImage)
        context.window_manager.event_timer_remove(self._timer)

    # Print function
    def debugPrint(self, message):
        """Debug print with identification timestamp."""

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
                    self.debugPrint("Rendered Image Size: w{0} x h{1}".format(pil_image.width, pil_image.height))

                    # Crop the image
                    pil_image = pil_image.crop(cropped_box)
                    self.debugPrint("Cropped Image Size:  w{0} x h{1}".format(pil_image.width, pil_image.height))

                    if pil_image:
                        with open(self.image_file, 'wb') as image_file:
                            pil_image.save(image_file, format='PNG')
                else:
                    self.task_status = "{0} 'Crop failed. Pillow package not installed.".format(os.path.basename(self.image_file))
            else:
                self.task_status = "Crop failed. Transparent Background and/or Add Environment settings not satisfied."

        now = time.time()

        if self.task_status is not None:
            self.report({'ERROR'}, "{0}. Elapsed Time: {1}".format(self.task_status, format_elapsed(now - self._start_time)))
        else:
            render_print("SUCCESS: {0} rendered. Elapsed Time: {1}".format(os.path.basename(self.image_file),format_elapsed(now - self._start_time)))

    # Render function
    def performRenderTask(self):
        """Render ldraw model."""

        if not self.cli_render:
            if not self.render_window:
                self.debugPrint("Performing Render Task Without Preview Window...")
            else:
                self.debugPrint("Performing Render Task With Preview Window...")

        if self.blend_file:
            self.debugPrint("Apply blend file {0} - Trusted: {1}".format(self.blend_file, self.blendfile_trusted))
            bpy.ops.wm.open_mainfile(filepath=self.blend_file, use_scripts=self.blendfile_trusted)
        # end if

        active_scene = bpy.context.scene
        if self.render_percentage is not None:
            active_scene.render.resolution_percentage = self.render_percentage
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
            self.report({'ERROR'}, "ERROR LDraw image “{}” already exists".format(self.image_file))
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
        self.debugPrint("Look:                {0}".format(self.use_look))
        self.debugPrint("Overwrite_Image:     {0}".format(self.overwrite_image))
        self.debugPrint("Trans_Background:    {0}".format(self.transparent_background))
        self.debugPrint("Add_Environment:     {0}".format(self.add_environment))
        self.debugPrint("Crop_Image:          {0}".format(self.crop_image))
        self.debugPrint("Search_Addl_Paths:   {0}".format(self.search_additional_paths))
        if not self.cli_render:
            self.debugPrint("Render_Window:       {0}".format(self.render_window))
        if not self.blend_file == "":
            self.debugPrint("Blendfile_Trusted:   {0}".format(self.blendfile_trusted))
            self.debugPrint("Blend_File:          {0}".format(self.blend_file))
        self.debugPrint("Verbose:             {0}".format(self.verbose))

    def setImportLDrawPreferences(self):
        """Import parameter settings when running from command line or LDraw file already loaded."""

        self.use_look                = importldraw.ImportLDrawOps.prefs.get('useLook',          self.use_look)
        self.overwrite_image         = importldraw.ImportLDrawOps.prefs.get('overwriteImage',   self.overwrite_image)
        self.transparent_background  = importldraw.ImportLDrawOps.prefs.get('transparentBackground', self.transparent_background)
        self.add_environment         = importldraw.ImportLDrawOps.prefs.get('addEnvironment',   self.add_environment)
        self.crop_image              = importldraw.ImportLDrawOps.prefs.get('cropImage',        self.crop_image)
        self.render_window           = importldraw.ImportLDrawOps.prefs.get('renderWindow',     self.render_window)
        self.blendfile_trusted       = importldraw.ImportLDrawOps.prefs.get('blendfileTrusted', self.blendfile_trusted)
        self.blend_file              = importldraw.ImportLDrawOps.prefs.get('blendFile',        self.blend_file)
        self.search_additional_paths = importldraw.ImportLDrawOps.prefs.get('searchAdditionalPaths', self.search_additional_paths)
        self.verbose                 = importldraw.ImportLDrawOps.prefs.get('verbose',          self.verbose)

        self.debugPrintPreferences()

    def draw(self, context):
        """Display render options."""

        layout = self.layout
        layout.use_property_split = True  # Active single-column layout

        box = layout.box()
        box.label(text="LDraw Render Options", icon='PREFERENCES')
        if not importldraw.loadldraw.ldrawModelLoaded and self.ldraw_path.__eq__(""):
            box.label(text="LDraw filepath:", icon='FILEBROWSER')
            box.prop(self, "ldraw_path")
        box.label(text="Model filepath:", icon='FILEBROWSER')
        box.prop(self, "model_file")
        box.label(text="Blend filepath:", icon='FILEBROWSER')
        box.prop(self, "blend_file")

        box.prop(self, "resolution_width")
        box.prop(self, "resolution_height")
        box.prop(self, "render_percentage")

        box.prop(self, "render_window")
        box.prop(self, "overwrite_image")
        box.prop(self, "blendfile_trusted")

        if not importldraw.loadldraw.ldrawModelLoaded:
            box.prop(self, "load_ldraw_model")
            box.prop(self, "use_look", expand=True)
            box.prop(self, "transparent_background")
            box.prop(self, "add_environment")
            box.prop(self, "crop_image")
            box.prop(self, "search_additional_paths")
            box.prop(self, "verbose")

    def invoke(self, context, event):
        """Setup render options."""

        if importldraw.loadldraw.ldrawModelLoaded:
            self.setImportLDrawPreferences()
            self.model_file = importldraw.loadldraw.ldrawModelFile
            self.image_file = self.model_file + ".png"
        else:
            self.prefs = importldraw.Preferences(self.preferences_file)

            self.ldraw_path              = self.prefs.get('ldrawDirectory',        importldraw.loadldraw.Configure.findDefaultLDrawDirectory())
            self.use_look                = self.prefs.get('useLook',               self.use_look)
            self.overwrite_image         = self.prefs.get('overwriteImage',        self.overwrite_image)
            self.transparent_background  = self.prefs.get('transparentBackground', self.transparent_background)
            self.add_environment         = self.prefs.get('addEnvironment',        self.add_environment)
            self.crop_image              = self.prefs.get('cropImage',             self.crop_image)
            self.render_window           = self.prefs.get('renderWindow',          self.render_window)
            self.blendfile_trusted       = self.prefs.get('blendfileTrusted',      self.blendfile_trusted)
            self.blend_file              = self.prefs.get('blendFile',             self.blend_file)
            self.search_additional_paths = self.prefs.get('searchAdditionalPaths', self.search_additional_paths)
            self.verbose                 = self.prefs.get('verbose',               self.verbose)

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
        """LPub3D Render LDraw model."""

        # Confirm minimum Blender version
        if bpy.app.version < (2, 80, 0):
            self.report({'ERROR'}, 'The RenderLDraw addon requires Blender 2.80 or greater.')
            return {'FINISHED'}

        if importldraw.loadldraw.ldrawModelLoaded:
            self.debugPrint("Preferences_File:    {0}".format(self.preferences_file))
            self.debugPrint("Model_File:          {0}".format(self.model_file))

        elif self.load_ldraw_model:
            self.debugPrint("-------------------------")
            self.debugPrint("Performing Load Task...")

            start_time = time.time()

            self.debugPrint("CLI_Render:          {0}".format(self.cli_render))
            self.debugPrint("Load_Ldraw_Model:    {0}".format(self.load_ldraw_model))
            self.debugPrint("Resolution_Width:    {0}".format(self.resolution_width))
            self.debugPrint("Resolution_Height:   {0}".format(self.resolution_height))
            self.debugPrint("Render_Percentage:   {0}".format(self.render_percentage))
            self.debugPrint("Preferences_File:    {0}".format(self.preferences_file))
            self.debugPrint("Model_File:          {0}".format(self.model_file))
            self.debugPrint("Image_File:          {0}".format(self.image_file))

            assert self.preferences_file.__ne__(""), "Preference file path not specified."
            assert self.image_file.__ne__(""), "Image file path not specified."
            assert self.model_file.__ne__(""), "Model file path not specified."
            if not self.cli_render:
                assert self.ldraw_path.__ne__(""), "LDraw library path not specified."
                self.prefs.set('ldrawDirectory',        self.ldraw_path)
                self.prefs.set('useLook',               self.use_look)
                self.prefs.set('overwriteImage',        self.overwrite_image)
                self.prefs.set('transparentBackground', self.transparent_background)
                self.prefs.set('addEnvironment',        self.add_environment)
                self.prefs.set('cropImage',             self.crop_image)
                self.prefs.set('renderWindow',          self.render_window)
                self.prefs.set('blendfileTrusted',      self.blendfile_trusted)
                self.prefs.set('blendFile',             self.blend_file)
                self.prefs.set('searchAdditionalPaths', self.search_additional_paths)
                self.prefs.set('verbose',               self.verbose)
                self.prefs.save()
                self.debugPrintPreferences()

            kwargs = {
                "preferencesFile": self.preferences_file,
                "modelFile": self.model_file
            }

            load_Result = bpy.ops.import_scene.lpub3dimportldraw('EXEC_DEFAULT', **kwargs)

            self.debugPrint("Load Task Result:    {0}".format(load_Result))

            # Check blend file and create if not exist
            """
            if self.cli_render and self.preferences_file:
                default_blend_file_directory = os.path.dirname(self.preferences_file)
                default_blend_file = os.path.abspath(os.path.join(default_blend_file_directory, 'lpub3d.blend'))
                if not os.path.exists(default_blend_file):
                    bpy.ops.wm.save_mainfile(filepath=default_blend_file)
                    self.debugPrint("Save default blend file to {0}".format(default_blend_file))
            """

            now = time.time()

            if load_Result == {'FINISHED'}:
                self.debugPrint("Imported '{0}' in {1}".format(os.path.basename(self.model_file),
                                                               format_elapsed(now - start_time)))
            else:
                self.report({'ERROR'}, "ERROR {0} import failed. Elapsed time {1}".
                            format(os.path.basename(self.model_file),
                                   format_elapsed(now - start_time)))

        if self.cli_render:
            self.debugPrint("-------------------------")
            self.debugPrint("Performing Headless Render Task...")

            # Register auto crop
            if not self.import_only:
                bpy.app.handlers.render_complete.append(self.autocropImage)

            # Get preferences properties from importldraw module
            if self.load_ldraw_model:
                self.setImportLDrawPreferences()

            # Render image
            if not self.import_only:
                self.performRenderTask()

            # Cleanup handler
            if not self.import_only:
                bpy.app.handlers.render_complete.remove(self.autocropImage)

            return {'FINISHED'}

        else:
            self.debugPrint("Performing GUI Render Task...")

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
            bpy.app.handlers.render_complete.append(self.complete)
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
                if len(self.tasks) and self.tasks[0] == 'RENDER_TASK':

                    self.performRenderTask()

                # Remove current task from list. Perform next task
                if len(self.tasks):
                    self.tasks.pop(0)

            # (busy)
            return {'PASS_THROUGH'}

        # (timer)
        return {"PASS_THROUGH"}
        # This is very important! If we used "RUNNING_MODAL", this new modal function
        # would prevent the use of the X button to cancel rendering, because this
        # button is managed by the modal function of the render operator,
        # not this new operator!
