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
    blender_light.data.angle            = math.radians(light.sun_angle)
    blender_light.data.shadow_soft_size = light.shadow_radius
    blender_light.data.spot_size        = math.radians(light.spot_size)
    blender_light.data.spot_blend       = light.spot_blend
    blender_light.data.shape            = light.shape
    if light.type == 'AREA' and (light.shape == 'RECTANGLE' or light.shape == 'ELLIPSE'):
        blender_light.data.size         = light.area_size_x
        blender_light.data.size_y       = light.area_size_y
    else:
        blender_light.data.size         = light.size

    light.position[0] = light.position[0] * ImportOptions.import_scale
    light.position[1] = light.position[1] * ImportOptions.import_scale
    light.position[2] = light.position[2] * ImportOptions.import_scale

    light.target_position[0] = light.target_position[0] * ImportOptions.import_scale
    light.target_position[1] = light.target_position[1] * ImportOptions.import_scale
    light.target_position[2] = light.target_position[2] * ImportOptions.import_scale

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
    # when parenting the location of the parented obj is affected by the transform of the empty
    # this undoes the transform of the empty
    obj.parent = empty
    bpy.context.view_layer.update()
    if obj.parent is not None:
        obj.matrix_parent_inverse = obj.parent.matrix_world.inverted()

    if light.type != 'POINT':
        blender_lookat.look_at(obj, light.target_position, light.dummy)

    return obj

def get_light_location(location):

    return location - blender_lookat.get_vector()
