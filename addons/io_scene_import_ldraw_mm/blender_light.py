import mathutils
import math
import bpy

from .import_options import ImportOptions
from . import blender_lookat
from . import group

def create_light(light, empty=None, collection=None):
    blender_light = bpy.data.lights.new(light.name, light.type)

    blender_light.color                 = light.color
    blender_light.energy                = light.exponent
    blender_light.specular_factor       = light.specular
    blender_light.use_custom_distance   = light.use_cutoff
    blender_light.cutoff_distance       = light.cutoff_distance
    blender_light.use_shadow            = light.use_shadow
    blender_light.shadow_soft_size      = light.shadow_radius * ImportOptions.import_scale
    if light.type == 'SUN':
        blender_light.angle             = math.radians(light.sun_angle)
    if light.type == 'SPOT':
        blender_light.spot_size         = math.radians(light.spot_size)
        blender_light.spot_blend        = light.spot_blend
    if light.type == 'AREA':
        blender_light.shape             = light.shape
        if light.shape == 'RECTANGLE' or light.shape == 'ELLIPSE':
            blender_light.size          = light.area_size_x * ImportOptions.import_scale
            blender_light.size_y        = light.area_size_y * ImportOptions.import_scale
        else:
            blender_light.size          = light.size * ImportOptions.import_scale

    light.position[0] = light.position[0] * ImportOptions.import_scale
    light.position[1] = light.position[1] * ImportOptions.import_scale
    light.position[2] = light.position[2] * ImportOptions.import_scale

    obj = bpy.data.objects.new(light.name, blender_light)
    obj.name = light.name
    obj.location = light.position
    obj.hide_viewport = light.hidden
    obj.hide_render = light.hidden

    if collection is None:
        collection = bpy.context.scene.collection
    group.link_obj(collection, obj)

    # https://blender.stackexchange.com/a/72899
    # https://blender.stackexchange.com/a/154926
    # https://blender.stackexchange.com/a/29148
    # https://docs.blender.org/api/current/info_gotcha.html#stale-data
    # https://blenderartists.org/t/how-to-avoid-bpy-context-scene-update/579222/6
    # https://blenderartists.org/t/where-do-matrix-changes-get-stored-before-view-layer-update/1182838
    # when parenting, the location of the parented obj is affected by the transform of the empty
    # this undoes the transform of the empty
    obj.parent = empty
    bpy.context.view_layer.update()

    if obj.parent is not None:
        obj.matrix_parent_inverse = obj.parent.matrix_world.inverted()

    if light.rotation is not None:
        # transpose the rotation matrix and add the translation
        row0 = (light.rotation[0][0], light.rotation[1][0], light.rotation[2][0], light.position[0])
        row1 = (light.rotation[0][1], light.rotation[1][1], light.rotation[2][1], light.position[1])
        row2 = (light.rotation[0][2], light.rotation[1][2], light.rotation[2][2], light.position[2])
        row3 = (0, 0, 0, 1)
        obj.matrix_world = mathutils.Matrix((row0, row1, row2, row3))
    elif light.type != 'POINT':
        light.target_position[0] = light.target_position[0] * ImportOptions.import_scale
        light.target_position[1] = light.target_position[1] * ImportOptions.import_scale
        light.target_position[2] = light.target_position[2] * ImportOptions.import_scale
        blender_lookat.look_at(obj, light.target_position, light.up_vector)

    return obj

def get_light_location(location):

    return location - blender_lookat.get_vector()
