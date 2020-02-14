# -*- coding: utf-8 -*-
"""Render LDraw GPLv2 license.

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
Render LDraw

This file defines the CLI load class.
"""

import os
import sys
import bpy
import time
import datetime
from bpy_extras.io_utils import ExportHelper
from bpy.props import StringProperty, BoolProperty, IntProperty

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
    # print("{0}".format(message))
    sys.stdout.write("{0}\n".format(message))

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
    """Render LDraw - Render Operator."""

    bl_idname = "render_scene.renderldraw"
    bl_description = "Render LDraw model as .png file"
    bl_label = "Render LDraw Models"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    prefs_directory = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../io_scene_importldraw'))
    prefs_file_path = os.path.join(prefs_directory, 'ImportLDrawPreferences.ini')
    image_directory = os.path.abspath(os.path.expanduser("~"))
    image_file_path = os.path.join(image_directory, 'blender_ldraw_image.png')

    node_name = None  # not used
    node_file = None  # not used
    scene_name = None  # not used

    # Define variables to register
    _timer = None
    tasks = None
    stop = None
    busy = None

    # Properties
    model_file: StringProperty(
        name="",
        description="Specify LDraw model file absolute file path - required",
        default=r""
    )

    blend_file: StringProperty(
        name="",
        description="Specify additional blend file absolute file path - optional",
        default=r"",
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

    render_window: BoolProperty(
        name="Display Render Window",
        description="Specify whether to display the render window",
        default=True
    )

    search_custom_parts: BoolProperty(
        name="Search Custom Parts",
        description="Add custom parts directory to search paths - automatically added for step fade or highlight",
        default=False
    )

    load_ldraw_model: BoolProperty(
        name="Load LDraw Model",
        description="Specify whether to load the specified LDraw model before rendering - default is True).",
        default=True
    )

    verbose: BoolProperty(
        name="Verbose Output",
        description="Output all messages while working, else only show warnings and errors",
        default=False
    )

    # Hidden properties
    cli_render: BoolProperty(
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
    # End Hidden properties

    # File type filter in file browser
    filename_ext = ".png"
    filter_glob: StringProperty(
        default="*.png",
        options={'HIDDEN'}
    )

    # Define handler functions. I use pre and post to know if Blender "is busy"
    def pre(self, dummy):
        self.busy = True

    def post(self, dummy):
        self.busy = False

    def cancelled(self, dummy):
        self.stop = True

    # Print function
    def debugPrint(self, message):
        """Debug print with identification timestamp."""

        if self.verbose:
            render_print(message)

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

        image_inputs = {}

        i = 0
        while True:
            i += 1
            """
            Not used--
            --input=«node-name»=«file-path»
            specifies an image file to load for a given compositor
            image node. Specify this as many times as necessary, once
            for each image node.
            node_name = TBD
            node_file = TBD
            """
            if not self.node_name or not self.node_file:
                break
            image_inputs[self.node_name] = self.node_file
        # end while

        if self.scene_name is not None:
            bpy.context.screen.scene = bpy.data.scenes[self.scene_name]
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
        if active_scene.node_tree is None and (len(image_inputs) > 0):
            self.report({'WARNING'}, "blendfile “{0}” does not have compositor nodes".format(self.blend_file))
        # end if
        if self.transparent_background and self.use_look == 'normal':
            if active_scene.render.engine == 'CYCLES':
                active_scene.render.image_settings.color_mode = 'RGBA'
                active_scene.render.film_transparent = True
        # end if

        if not self.overwrite_image and os.path.exists(self.image_file):
            self.report({'ERROR'}, "ERROR LDraw image “{}” already exists".format(self.image_file))
        else:
            start_time = time.time()

            if len(image_inputs) > 0:
                self.debugPrint("image_inputs = {!r}".format(image_inputs))  # debug
            # end if
            for input_name in image_inputs:
                input_node = active_scene.node_tree.nodes[input_name]
                if input_node.type != "IMAGE":
                    self.report({'WARNING'}, "node “{}” is not an image node".format(input_name))
                # end if
                input_node.image = bpy.data.images.load(image_inputs[input_name])
            # end for
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

            now = time.time()
            
            self.debugPrint("SUCCESS: {0} rendered in {1}".format(os.path.basename(self.image_file),
                                                           format_elapsed(now - start_time)))
        # end if (overwrite)

    def draw(self, context):
        """Display render options."""

        layout = self.layout
        layout.use_property_split = True  # Active single-column layout

        box = layout.box()
        box.label(text="LDraw Model Render Options", icon='PREFERENCES')
        box.label(text="Model filepath:", icon='FILEBROWSER')
        box.prop(self, "model_file")
        box.label(text="Blend filepath:", icon='FILEBROWSER')
        box.prop(self, "blend_file")

        box.prop(self, "resolution_width")
        box.prop(self, "resolution_height")
        box.prop(self, "render_percentage")
        box.prop(self, "overwrite_image")

        box.prop(self, "transparent_background")
        box.prop(self, "blendfile_trusted")
        box.prop(self, "render_window")
        box.prop(self, "search_custom_parts")
        box.prop(self, "load_ldraw_model")
        box.prop(self, "verbose")

    def invoke(self, context, event):
        """Setup render options."""

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

        self.debugPrint("-------------------------")
        self.debugPrint("Performing Import Task...")

        start_time = time.time()

        self.debugPrint("CLI_Render:          {0}".format(self.cli_render))
        self.debugPrint("Load_Ldraw_Model:    {0}".format(self.load_ldraw_model))
        self.debugPrint("Resolution_Width:    {0}".format(self.resolution_width))
        self.debugPrint("Resolution_Height:   {0}".format(self.resolution_height))
        self.debugPrint("Render_Percentage:   {0}".format(self.render_percentage))
        self.debugPrint("Search_Custom_Parts: {0}".format(self.search_custom_parts))
        self.debugPrint("Preferences_File:    {0}".format(self.preferences_file))
        self.debugPrint("Model_File:          {0}".format(self.model_file))
        self.debugPrint("Image_File:          {0}".format(self.image_file))
        
        if self.load_ldraw_model:
            assert self.preferences_file.__ne__("") ,"Preference file path not specified."
            assert self.image_file.__ne__("") ,"Image file path not specified."
            assert self.model_file.__ne__("") ,"Model file path not specified."
            kwargs = {
                "preferencesFile": self.preferences_file,
                "modelFile": self.model_file,
                "searchCustomParts": self.search_custom_parts,
                "cliRender": self.cli_render
            }
            self.load_Result = bpy.ops.import_scene.importldraw('EXEC_DEFAULT', **kwargs)
            self.debugPrint("Load Task Result:    {0}".format(self.load_Result))

        # Check blend file and create if not exist
        if self.cli_render and self.preferences_file:
            default_blend_file_directory = os.path.dirname(self.preferences_file)
            default_blend_file = os.path.abspath(os.path.join(default_blend_file_directory, 'lpub3d.blend'))
            if not os.path.exists(default_blend_file):
                bpy.ops.wm.save_mainfile(filepath=default_blend_file)
                self.debugPrint("Save default blend file to {0}".format(default_blend_file))


        now = time.time()

        if self.load_Result == {'FINISHED'}:
            self.debugPrint("Imported '{0}' in {1}".format(os.path.basename(self.model_file),
                                                    format_elapsed(now - start_time)))
        else:
            self.report({'ERROR'}, "ERROR {0} import failed. Elapsed time {1}".
                        format(os.path.basename(self.model_file),
                               format_elapsed(now - start_time)))

        if self.cli_render:
            self.debugPrint("-------------------------")
            self.debugPrint("Performing Headless Render Task...")
            
            # Get preferences properties from importldraw module
            if self.load_ldraw_model:
                from io_scene_importldraw import importldraw
                self.use_look               = importldraw.ImportLDrawOps.prefs.get('useLook', 'normal')
                self.overwrite_image        = importldraw.ImportLDrawOps.prefs.get('overwriteImage', self.overwrite_image)
                self.transparent_background = importldraw.ImportLDrawOps.prefs.get('transparentBackground', self.transparent_background)
                self.render_window          = importldraw.ImportLDrawOps.prefs.get('renderWindow', self.render_window)
                self.blendfile_trusted      = importldraw.ImportLDrawOps.prefs.get('blendfileTrusted', self.blendfile_trusted)
                self.blend_file             = importldraw.ImportLDrawOps.prefs.get('blendFile', "")

            self.debugPrint("Look:                {0}".format(self.use_look))
            self.debugPrint("Overwrite_Image:     {0}".format(self.overwrite_image))
            self.debugPrint("Trans_background:    {0}".format(self.transparent_background))
            self.debugPrint("Render_Window:       {0}".format(self.render_window))
            self.debugPrint("Blendfile_Trusted:   {0}".format(self.blendfile_trusted))
            self.debugPrint("Blend_File:          {0}".format(self.blend_file))

            self.performRenderTask()

            return {'FINISHED'}

        else:
            self.debugPrint("Performing GUI Render Task...")

            # Define the variables during execution. This allows us to define when called from a button
            self.stop = False
            self.busy = False

            # Set task(s)
            self.tasks = ['RENDER_TASK']
            # self.tasks = ['LOAD_TASK', 'RENDER_TASK']

            # Add the handlers
            bpy.app.handlers.render_pre.append(self.pre)
            bpy.app.handlers.render_post.append(self.post)
            bpy.app.handlers.render_cancel.append(self.cancelled)

            # The timer gets created and the modal handler is added to the window manager
            self._timer = context.window_manager.event_timer_add(0.5, window=context.window)
            context.window_manager.modal_handler_add(self)

            return {"RUNNING_MODAL"}

    def modal(self, context, event):
        """Render Modal."""

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.app.handlers.render_pre.remove(self.pre)
            bpy.app.handlers.render_post.remove(self.post)
            bpy.app.handlers.render_cancel.remove(self.cancelled)
            context.window_manager.event_timer_remove(self._timer)
            self.stop = True

            self.report({'WARNING'}, 'Render operation cancelled.')
            return {'CANCELLED'}

        if event.type == 'TIMER':  # This event is signaled every half a second and will start the render if available

            # If cancelled or no more tasks to render, finish.
            if True in (not self.tasks, self.stop is True):

                # We remove the handlers and the modal timer to clean everything
                bpy.app.handlers.render_pre.remove(self.pre)
                bpy.app.handlers.render_post.remove(self.post)
                bpy.app.handlers.render_cancel.remove(self.cancelled)
                context.window_manager.event_timer_remove(self._timer)

                self.debugPrint("Render operation finished.")
                return {"FINISHED"}

            elif self.busy is False:  # Not currently busy. Perform task.

                # Perform task
                if self.tasks[0] == 'RENDER_TASK':

                    self.performRenderTask()

                # end if (RENDER_TASK)

                # Remove current task from list. Perform next task
                self.tasks.pop(0)

            # (busy)
            return {'PASS_THROUGH'}

        # (timer)
        return {"PASS_THROUGH"}
        # This is very important! If we used "RUNNING_MODAL", this new modal function
        # would prevent the use of the X button to cancel rendering, because this
        # button is managed by the modal function of the render operator,
        # not this new operator!
