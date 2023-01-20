# -*- coding: utf-8 -*-
"""
Trevor SANDY
Last Update January 17, 2023
Copyright (c) 2020 - 2023 by Trevor SANDY

LPub3D Import LDraw GPLv2 license.

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
LPub3D Import LDraw

This file defines the importer for Blender.
It stores and recalls preferences for the importer.
The execute() function kicks off the import process.
The python module loadldraw does the actual work.

Adapted from Import LDraw by Toby Nelson - tobymnelson@gmail.com
"""

# Import From Files - See PR https://github.com/TobyLobster/ImportLDraw/pull/49/
if "bpy" in locals():
    import importlib
    importlib.reload(loadldraw)
else:
    from .loadldraw import loadldraw

import configparser
import sys
import os
import bpy
from bpy.props import (StringProperty,
                       FloatProperty,
                       IntProperty,
                       EnumProperty,
                       BoolProperty
                       )
from bpy_extras.io_utils import ImportHelper

"""
Default preferences file:

[DEFAULT]

[importldraw]
blendFile                     =
customLDConfigFile            =
additionalSearchDirectories   =
ldrawDirectory                =
lsynthDirectory               =
studLogoDirectory             =
addEnvironment                = True
bevelEdges                    = True
bevelWidth                    = 0.5
blendfileTrusted              = False
cameraBorderPercentage        = 0.5
curvedWalls                   = True
defaultColour                 = 4
flattenHierarchy              = False
gaps                          = False
gapsWidth                     = 0.01
importCameras                 = True
instanceStuds                 = False
linkParts                     = True
logoStudVersion               = 4
numberNodes                   = True
overwriteExistingMaterials    = False
overwriteExistingMeshes       = False
overwriteImage                = True
positionCamera                = True
positionObjectOnGroundAtOrigin= True
removeDoubles                 = True
renderWindow                  = False
resolution                    = Standard
resolveNormals                = guess
scale                         = 0.01
smoothShading                 = True
transparentBackground         = True
useColourScheme               = lego
useLogoStuds                  = False
useLook                       = normal
useLSynthParts                = True
useUnofficialParts            = True
verbose                       = 0
"""


class Preferences():
    """LPub3D Import LDraw - Preferences"""

    __sectionName = 'importldraw'

    def __init__(self, preferencesfile):
        if preferencesfile.__ne__(""):
            self.__prefsFilepath = preferencesfile
            loadldraw.debugPrint("-----Import Settings-----")
            loadldraw.debugPrint("Preferences file:    {0}".format(self.__prefsFilepath))
        else:
            self.__prefsPath = os.path.dirname(__file__)
            self.__prefsFilepath = os.path.join(self.__prefsPath, "ImportLDrawPreferences.ini")

        self.__config = configparser.RawConfigParser()
        self.__prefsRead = self.__config.read(self.__prefsFilepath)
        if self.__prefsRead and not self.__config[Preferences.__sectionName]:
            self.__prefsRead = False

    def get(self, option, default):
        if not self.__prefsRead:
            return default

        if type(default) is bool:
            return self.__config.getboolean(Preferences.__sectionName, option, fallback=default)
        elif type(default) is float:
            return self.__config.getfloat(Preferences.__sectionName, option, fallback=default)
        elif type(default) is int:
            return self.__config.getint(Preferences.__sectionName, option, fallback=default)
        else:
            return self.__config.get(Preferences.__sectionName, option, fallback=default)

    def set(self, option, value):
        if not (Preferences.__sectionName in self.__config):
            self.__config[Preferences.__sectionName] = {}
        self.__config[Preferences.__sectionName][option] = str(value)

    def save(self):
        try:
            with open(self.__prefsFilepath, 'w') as configfile:
                self.__config.write(configfile)
            return True
        except Exception:
            # Fail gracefully
            e = sys.exc_info()[0]
            loadldraw.debugPrint("WARNING: Could not save preferences. {0}".format(e))
            return False


def colourSchemeCallback(customldconfig):
    """LPub3D Import LDraw - Colour scheme items"""

    items = [
        ("lgeo", "Realistic colours", "Uses the LGEO colour scheme for realistic colours."),
        ("ldraw", "Original LDraw colours", "Uses the standard LDraw colour scheme (LDConfig.ldr)."),
        ("alt", "Alternate LDraw colours", "Uses the alternate LDraw colour scheme (LDCfgalt.ldr)."),
    ]

    if customldconfig.__ne__(""):
        items.append(("custom", "Custom LDraw colours", "Uses a user specified LDraw colour file."))

    return items


class ImportLDrawOps(bpy.types.Operator, ImportHelper):
    """LPub3D Import LDraw - Import Operator."""

    bl_idname = "import_scene.lpub3dimportldraw"
    bl_description = "Import LDraw model (.mpd/.ldr/.l3b/.dat)"
    bl_label = "Import LDraw Model"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    # Initialize the preferences system
    prefs = Preferences("")

    # Properties - specified from preferences function
    ldrawPath: StringProperty(
        name="",
        description="Full filepath to the LDraw Parts Library (download from http://www.ldraw.org)",
        default=prefs.get("ldrawDirectory", loadldraw.Configure.findDefaultLDrawDirectory())
    )

    importScale: FloatProperty(
        name="Scale",
        description="Image percentage scale for its pixel resolution (enter between .01 and 1)",
        default=prefs.get("scale", 0.01)
    )

    resPrims: EnumProperty(
        name="Resolution of part primitives",
        description="Resolution of part primitives, ie. how much geometry they have",
        default=prefs.get("resolution", "Standard"),
        items=(
            ("Standard", "Standard primitives", "Import using standard resolution primitives."),
            ("High", "High resolution primitives", "Import using high resolution primitives."),
            ("Low", "Low resolution primitives", "Import using low resolution primitives.")
        )
    )

    look: EnumProperty(
        name="Overall Look",
        description="Realism or Schematic look",
        default=prefs.get("useLook", "normal"),
        items=(
            ("normal", "Realistic Look", "Render to look realistic."),
            ("instructions", "Lego Instructions Look", "Render to look like the instruction book pictures."),
        )
    )

    colourScheme: EnumProperty(
        name="Colour scheme options",
        description="Colour scheme options",
        default=prefs.get("useColourScheme", "lgeo"),
        items=colourSchemeCallback(prefs.get("customLDConfigFile", ""))
    )

    logoStudVersion: EnumProperty(
        name="Stud Logo Version",
        description="Which version of the stud logo to use",
        default=prefs.get("logoStudVersion", "4"),
        items=(
            ("4", "Rounded (4)", "Rounded logo lettering geometry"),
            ("3", "Flat (3)", "Flat logo lettering geometry"),
            ("5", "Subtle Rounded (5)", "Subtle rounded logo lettering geometry"),
        )
    )

    smoothParts: BoolProperty(
        name="Smooth faces and edge-split",
        description="Smooth faces and add an edge-split modifier",
        default=prefs.get("smoothShading", True)
    )

    addGaps: BoolProperty(
        name="Add space between each part:",
        description="Add a small space between each part",
        default=prefs.get("gaps", False)
    )

    gapsSize: FloatProperty(
        name="Space",
        description="Amount of space between each part",
        default=prefs.get("gapWidth", 0.01)
    )

    curvedWalls: BoolProperty(
        name="Use curved wall normals",
        description="Makes surfaces look slightly concave",
        default=prefs.get("curvedWalls", True)
    )

    addSubsurface: BoolProperty(
        name="Add subsurface",
        description="Adds subsurface to principled shader",
        default=prefs.get("addSubsurface", True)
    )

    importCameras: BoolProperty(
        name="Import cameras",
        description="Import camera definitions (from models authored in LeoCAD)",
        default=prefs.get("importCameras", True)
    )

    importLights: BoolProperty(
        name="Import lights",
        description="Import Light definitions (from models authored in LPub3D)",
        default=prefs.get("importLights", True)
    )

    linkParts: BoolProperty(
        name="Link identical parts",
        description="Identical parts (of the same type and colour) share the same mesh",
        default=prefs.get("linkParts", True)
    )

    numberNodes: BoolProperty(
        name="Number each object",
        description="Each object has a five digit prefix eg. 00001_car. This keeps the list in it's proper order",
        default=prefs.get("numberNodes", True)
    )

    positionOnGround: BoolProperty(
        name="Put model on ground at origin",
        description="The object is centred at the origin, and on the ground plane",
        default=prefs.get("positionObjectOnGroundAtOrigin", True)
    )

    flatten: BoolProperty(
        name="Flatten tree",
        description="In Scene Outliner, all parts are placed directly below the root - there's no tree of submodels",
        default=prefs.get("flattenHierarchy", False)
    )

    useUnofficialParts: BoolProperty(
        name="Include unofficial parts",
        description="Additionally searches for parts in the <ldraw-dir>/unofficial/ directory",
        default=prefs.get("useUnofficialParts", True)
    )

    useLogoStuds: BoolProperty(
        name="Show 'LEGO' logo on studs",
        description="Shows the LEGO logo on each stud (at the expense of some extra geometry and import time)",
        default=prefs.get("useLogoStuds", False)
    )

    instanceStuds: BoolProperty(
        name="Make individual studs",
        description="Creates a Blender Object for each and every stud (WARNING: can be slow to import and edit in "
                    "Blender if there are lots of studs)",
        default=prefs.get("instanceStuds", False)
    )

    resolveNormals: EnumProperty(
        name="Resolve ambiguous normals option",
        description="Some older LDraw parts have faces with ambiguous normals, this specifies what do do with them",
        default=prefs.get("resolveNormals", "guess"),
        items=(
            ("guess", "Recalculate Normals", "Uses Blender's Recalculate Normals to get a consistent set of normals."),
            ("double", "Two faces back to back",
             "Two faces are added with their normals pointing in opposite directions."),
        )
    )

    bevelEdges: BoolProperty(
        name="Bevel edges",
        description="Adds a Bevel modifier for rounding off sharp edges",
        default=prefs.get("bevelEdges", True)
    )

    bevelWidth: FloatProperty(
        name="Bevel Width",
        description="Width of the bevelled edges",
        default=prefs.get("bevelWidth", 0.5)
    )

    addEnvironment: BoolProperty(
        name="Add Environment",
        description="Adds a ground plane and environment texture (for realistic look only)",
        default=prefs.get("addEnvironment", True)
    )

    positionCamera: BoolProperty(
        name="Position the camera",
        description="Position the camera to show the whole model",
        default=prefs.get("positionCamera", True)
    )

    cameraBorderPercentage: FloatProperty(
        name="Camera Border %",
        description="When positioning the camera, include a (percentage) border around the model in the render",
        default=prefs.get("cameraBorderPercentage", 5.0)
    )

    customLDConfigPath: StringProperty(
        name="",
        description="Full directory path to specified custom LDraw colours (LDConfig) file",
        default=prefs.get("customLDConfigFile", r"")
    )

    additionalSearchPaths: StringProperty(
        name="",
        description="Full directory paths, comma delimited, to additional LDraw search paths",
        default=prefs.get("additionalSearchDirectories", "")
    )

    studLogoPath: StringProperty(
        name="",
        description="Full directory path to LDraw stud logo primitives - specify if unofficial parts not used",
        default=prefs.get("studLogoDirectory", r"")
    )

    lsynthPath: StringProperty(
        name="",
        description="Full directory path to LSynth primitives - specify if not using blender module default",
        default=prefs.get("lsynthDirectory", r"")
    )

    environmentPath: StringProperty(
        name="",
        description="Full file path to .exr environment texture file - specify if not using default bundled in addon",
        default=prefs.get("environmentFile", r"")
    )

    defaultColour: StringProperty(
        name="Default Colour",
        description="Sets the default part colour",
        default=prefs.get("defaultColour", "4")
    )

    useLSynthParts: BoolProperty(
        name="Use LSynth for Flex Parts",
        description="Source used to create flexible parts",
        default=prefs.get("useLSynthParts", True)
    )

    overwriteExistingMaterials: BoolProperty(
        name="Use Existing Material",
        description="Overwrite existing material with the same name",
        default=prefs.get("overwriteExistingMaterials", True)
    )

    overwriteExistingMeshes: BoolProperty(
        name="Use Existing Mesh",
        description="Overwrite existing mesh with the same name",
        default=prefs.get("overwriteExistingMeshes", False)
    )

    removeDoubles: BoolProperty(
        name="No Duplicate Verticies",
        description="Remove duplicate vertices (recommended)",
        default=prefs.get("removeDoubles", True)
    )

    searchAdditionalPaths: BoolProperty(
        name="Search Additional Paths",
        description="Search additional LDraw paths (automatically set for fade previous steps and highlight step)",
        default=False
    )

    verbose: BoolProperty(
        name="Verbose Output",
        description="Output all messages while working, else only show warnings and errors",
        default=prefs.get("verbose", True)
    )

    # Hidden properties
    preferencesFile: StringProperty(
        default=r"",
        options={'HIDDEN'}
    )

    parameterFile: StringProperty(
        default=prefs.get("parameterFile", r""),
        options={'HIDDEN'}
    )

    modelFile: StringProperty(
        default=r"",
        options={'HIDDEN'}
    )

    # File type filter in file browser
    filename_ext = ".ldr"
    filter_glob: StringProperty(
        default="*.mpd;*.ldr;*.l3b;*.dat",
        options={'HIDDEN'}
    )

    # End Hidden properties

    def draw(self, context):
        """Display import options."""

        layout = self.layout
        layout.use_property_split = True  # Active single-column layout

        box = layout.box()
        box.label(text="LDraw Import Options", icon='PREFERENCES')
        box.label(text="LDraw filepath:", icon='FILEBROWSER')
        box.prop(self, "ldrawPath")
        box.prop(self, "importScale")
        box.prop(self, "look", expand=True)
        box.prop(self, "colourScheme", expand=True)
        box.prop(self, "addEnvironment")
        box.prop(self, "positionCamera")
        box.prop(self, "cameraBorderPercentage")

        box.prop(self, "importCameras")
        box.prop(self, "importLights")

        box.prop(self, "useLogoStuds")
        box.prop(self, "logoStudVersion", expand=True)
        box.prop(self, "instanceStuds")

        box.prop(self, "resPrims", expand=True)
        box.prop(self, "smoothParts")
        box.prop(self, "addSubsurface")
        box.prop(self, "bevelEdges")
        box.prop(self, "bevelWidth")
        box.prop(self, "addGaps")
        box.prop(self, "gapsSize")
        box.prop(self, "curvedWalls")
        box.prop(self, "linkParts")

        box.prop(self, "positionOnGround")
        box.prop(self, "numberNodes")
        box.prop(self, "flatten")

        box.label(text="Resolve Ambiguous Normals:", icon='ORIENTATION_NORMAL')
        box.prop(self, "resolveNormals", expand=True)

        box.prop(self, "useUnofficialParts")
        box.prop(self, "searchAdditionalPaths")
        box.prop(self, "verbose")

    def execute(self, context):
        """Start the import process."""

        # Confirm minimum Blender version
        if bpy.app.version < (2, 80, 0):
            self.report({'ERROR'}, 'The ImportLDraw addon requires Blender 2.80 or greater.')
            return {'FINISHED'}

        # Reinitialize the preferences system using specified ini
        if self.preferencesFile.__ne__(""):

            ImportLDrawOps.prefs = Preferences(self.preferencesFile)
            loadldraw.debugPrint("-----Import Settings-----")
            loadldraw.debugPrint("Preferences file:    {0}".format(self.preferencesFile))
            loadldraw.debugPrint("Model file:          {0}".format(self.modelFile))
            loadldraw.debugPrint("-------------------------")

            # Update properties with the reinitialized preferences
            self.addEnvironment          = ImportLDrawOps.prefs.get("addEnvironment",       self.addEnvironment)
            self.addGaps                 = ImportLDrawOps.prefs.get("gaps",                 self.addGaps)
            self.additionalSearchPaths   = ImportLDrawOps.prefs.get("additionalSearchDirectories", self.additionalSearchPaths)
            self.addSubsurface           = ImportLDrawOps.prefs.get("addSubsurface",        self.addSubsurface)
            self.bevelEdges              = ImportLDrawOps.prefs.get("bevelEdges",           self.bevelEdges)
            self.bevelWidth              = ImportLDrawOps.prefs.get("bevelWidth",           self.bevelWidth)
            self.cameraBorderPercentage  = ImportLDrawOps.prefs.get("cameraBorderPercentage", self.cameraBorderPercentage)
            self.colourScheme            = ImportLDrawOps.prefs.get("useColourScheme",      self.colourScheme)
            self.curvedWalls             = ImportLDrawOps.prefs.get("curvedWalls",          self.curvedWalls)
            self.customLDConfigPath      = ImportLDrawOps.prefs.get("customLDConfigFile",   self.customLDConfigPath)
            self.defaultColour           = ImportLDrawOps.prefs.get("defaultColour",        self.defaultColour)
            self.environmentPath         = ImportLDrawOps.prefs.get("environmentFile",      self.environmentPath)
            self.flatten                 = ImportLDrawOps.prefs.get("flattenHierarchy",     self.flatten)
            self.gapsSize                = ImportLDrawOps.prefs.get("gapWidth",             self.gapsSize)
            self.importCameras           = ImportLDrawOps.prefs.get("importCameras",        self.importCameras)
            self.importLights            = ImportLDrawOps.prefs.get("importLights",         self.importLights)
            self.importScale             = ImportLDrawOps.prefs.get("scale",                self.importScale)
            self.instanceStuds           = ImportLDrawOps.prefs.get("instanceStuds",        self.instanceStuds)
            self.ldrawPath               = ImportLDrawOps.prefs.get("ldrawDirectory",       self.ldrawPath)
            self.linkParts               = ImportLDrawOps.prefs.get("linkParts",            self.linkParts)
            self.logoStudVersion         = ImportLDrawOps.prefs.get("logoStudVersion",      self.logoStudVersion)
            self.look                    = ImportLDrawOps.prefs.get("useLook",              self.look)
            self.lsynthPath              = ImportLDrawOps.prefs.get("lsynthDirectory",      self.lsynthPath)
            self.numberNodes             = ImportLDrawOps.prefs.get("numberNodes",          self.numberNodes)
            self.overwriteExistingMaterials = ImportLDrawOps.prefs.get("overwriteExistingMaterials", self.overwriteExistingMaterials)
            self.overwriteExistingMeshes = ImportLDrawOps.prefs.get("overwriteExistingMeshes", self.overwriteExistingMeshes)
            self.parameterFile           = ImportLDrawOps.prefs.get("parameterFile",        self.parameterFile)
            self.positionCamera          = ImportLDrawOps.prefs.get("positionCamera",       self.positionCamera)
            self.positionOnGround        = ImportLDrawOps.prefs.get("positionObjectOnGroundAtOrigin", self.positionOnGround)
            self.removeDoubles           = ImportLDrawOps.prefs.get("removeDoubles",        self.removeDoubles)
            self.resolveNormals          = ImportLDrawOps.prefs.get("resolveNormals",       self.resolveNormals)
            self.resPrims                = ImportLDrawOps.prefs.get("resolution",           self.resPrims)
            self.searchAdditionalPaths   = ImportLDrawOps.prefs.get("searchAdditionalPaths", self.searchAdditionalPaths)
            self.smoothParts             = ImportLDrawOps.prefs.get("smoothShading",        self.smoothParts)
            self.studLogoPath            = ImportLDrawOps.prefs.get("studLogoDirectory",    self.studLogoPath)
            self.useLogoStuds            = ImportLDrawOps.prefs.get("useLogoStuds",         self.useLogoStuds)
            self.useLSynthParts          = ImportLDrawOps.prefs.get("useLSynthParts",       self.useLSynthParts)
            self.useUnofficialParts      = ImportLDrawOps.prefs.get("useUnofficialParts",   self.useUnofficialParts)
            self.verbose                 = ImportLDrawOps.prefs.get("verbose",              self.verbose)

            if self.colourScheme == "custom":
                assert self.customLDConfigPath.__ne__(""), "Custom LDraw colour (LDConfig) file path not specified."

                # Read current preferences from the UI and save them
        else:
            ImportLDrawOps.prefs.get("customLDConfigFile",     self.customLDConfigPath)
            ImportLDrawOps.prefs.get("environmentFile",        self.environmentPath)
            ImportLDrawOps.prefs.set("addEnvironment",         self.addEnvironment)
            ImportLDrawOps.prefs.set("addSubsurface",          self.addSubsurface)
            ImportLDrawOps.prefs.set("bevelEdges",             self.bevelEdges)
            ImportLDrawOps.prefs.set("bevelWidth",             self.bevelWidth)
            ImportLDrawOps.prefs.set("cameraBorderPercentage", self.cameraBorderPercentage)
            ImportLDrawOps.prefs.set("curvedWalls",            self.curvedWalls)
            ImportLDrawOps.prefs.set("flattenHierarchy",       self.flatten)
            ImportLDrawOps.prefs.set("gaps",                   self.addGaps)
            ImportLDrawOps.prefs.set("gapWidth",               self.gapsSize)
            ImportLDrawOps.prefs.set("importCameras",          self.importCameras)
            ImportLDrawOps.prefs.set("importLights",           self.importLights)
            ImportLDrawOps.prefs.set("instanceStuds",          self.instanceStuds)
            ImportLDrawOps.prefs.set("ldrawDirectory",         self.ldrawPath)
            ImportLDrawOps.prefs.set("linkParts",              self.linkParts)
            ImportLDrawOps.prefs.get("logoStudVersion",        self.logoStudVersion)
            ImportLDrawOps.prefs.set("lsynthDirectory",        self.lsynthPath)
            ImportLDrawOps.prefs.set("numberNodes",            self.numberNodes)
            ImportLDrawOps.prefs.set("positionCamera",         self.positionCamera)
            ImportLDrawOps.prefs.set("positionObjectOnGroundAtOrigin", self.positionOnGround)
            ImportLDrawOps.prefs.set("resolution",             self.resPrims)
            ImportLDrawOps.prefs.set("resolveNormals",         self.resolveNormals)
            ImportLDrawOps.prefs.set("scale",                  self.importScale)
            ImportLDrawOps.prefs.set("searchAdditionalPaths",  self.searchAdditionalPaths)
            ImportLDrawOps.prefs.set("smoothShading",          self.smoothParts)
            ImportLDrawOps.prefs.set("studLogoDirectory",      self.studLogoPath)
            ImportLDrawOps.prefs.set("useColourScheme",        self.colourScheme)
            ImportLDrawOps.prefs.set("useLogoStuds",           self.useLogoStuds)
            ImportLDrawOps.prefs.set("useLook",                self.look)
            ImportLDrawOps.prefs.set("useUnofficialParts",     self.useUnofficialParts)
            ImportLDrawOps.prefs.set("verbose",                self.verbose)
            ImportLDrawOps.prefs.save()

        # Set bpy related variables here since it isn't available immediately on Blender startup
        loadldraw.isBlender28OrLater = hasattr(bpy.app, "version") and bpy.app.version >= (2, 80)
        loadldraw.hasCollections = hasattr(bpy.data, "collections")

        # Set import options and import
        loadldraw.Options.addBevelModifier            = self.bevelEdges and not loadldraw.Options.instructionsLook
        loadldraw.Options.addGroundPlane              = self.addEnvironment
        loadldraw.Options.addSubsurface               = self.addSubsurface
        loadldraw.Options.addWorldEnvironmentTexture  = self.addEnvironment
        loadldraw.Options.bevelWidth                  = self.bevelWidth
        loadldraw.Options.cameraBorderPercent         = self.cameraBorderPercentage / 100.0
        loadldraw.Options.createInstances             = self.linkParts
        loadldraw.Options.curvedWalls                 = self.curvedWalls
        loadldraw.Options.defaultColour               = self.defaultColour
        loadldraw.Options.edgeSplit                   = self.smoothParts  # Edge split is appropriate only if we are smoothing
        loadldraw.Options.flattenHierarchy            = self.flatten
        loadldraw.Options.gaps                        = self.addGaps
        loadldraw.Options.gapWidth                    = self.gapsSize
        loadldraw.Options.importCameras               = self.importCameras
        loadldraw.Options.importLights                = self.importLights
        loadldraw.Options.instanceStuds               = self.instanceStuds
        loadldraw.Options.instructionsLook            = self.look == "instructions"
        loadldraw.Options.logoStudVersion             = self.logoStudVersion
        loadldraw.Options.numberNodes                 = self.numberNodes
        loadldraw.Options.overwriteExistingMaterials  = self.overwriteExistingMaterials
        loadldraw.Options.overwriteExistingMeshes     = self.overwriteExistingMeshes
        loadldraw.Options.parameterFile               = self.parameterFile
        loadldraw.Options.positionCamera              = self.positionCamera
        loadldraw.Options.positionObjectOnGroundAtOrigin = self.positionOnGround
        loadldraw.Options.removeDoubles               = self.removeDoubles
        loadldraw.Options.resolution                  = self.resPrims
        loadldraw.Options.resolveAmbiguousNormals     = self.resolveNormals
        loadldraw.Options.scale                       = self.importScale
        loadldraw.Options.searchAdditionalPaths       = self.searchAdditionalPaths
        loadldraw.Options.smoothShading               = self.smoothParts
        loadldraw.Options.useColourScheme             = self.colourScheme
        loadldraw.Options.useLogoStuds                = self.useLogoStuds
        loadldraw.Options.useLSynthParts              = self.useLSynthParts
        loadldraw.Options.useUnofficialParts          = self.useUnofficialParts
        loadldraw.Options.verbose                     = self.verbose

        loadldraw.Options.additionalSearchDirectories = self.additionalSearchPaths
        loadldraw.Options.customLDConfigFile          = self.customLDConfigPath

        assert self.ldrawPath, "LDraw library path not specified."
        loadldraw.Options.ldrawDirectory              = self.ldrawPath

        if not self.environmentPath:
            loadldraw.Options.environmentFile = os.path.join(os.path.dirname(__file__), "loadldraw/background.exr")
        else:
            loadldraw.Options.environmentFile         = self.environmentPath
        if not self.lsynthPath:
            loadldraw.Options.LSynthDirectory = os.path.join(os.path.dirname(__file__), "lsynth")
        else:
            loadldraw.Options.LSynthDirectory         = self.lsynthPath
        if not self.studLogoPath:
            loadldraw.Options.studLogoDirectory = os.path.join(os.path.dirname(__file__), "studs")
        else:
            loadldraw.Options.studLogoDirectory       = self.studLogoPath

        if self.filepath:
            self.modelFile                            = self.filepath

        loadldraw.loadFromFile(self, self.modelFile)

        return {"FINISHED"}

