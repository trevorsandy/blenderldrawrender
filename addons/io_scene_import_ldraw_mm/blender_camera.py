# _*_lp_lc_mod
import sys
# _*_mod_end
import math
# _*_lp_lc_mod
from mathutils import Vector
import bpy
# _*_mod_end

from .import_options import ImportOptions
# _*_lp_lc_mod
from . import blender_lookat
# _*_mod_end
from . import group


def create_camera(camera, empty=None, collection=None):
    blender_camera = bpy.data.cameras.new(camera.name)

    blender_camera.sensor_fit = "VERTICAL"
    # camera.sensor_height = self.fov
    blender_camera.lens_unit = "FOV"
    blender_camera.angle = math.radians(camera.fov)  # self.fov * 3.1415926 / 180.0
    blender_camera.clip_start = camera.z_near
    blender_camera.clip_end = camera.z_far

    blender_camera.clip_start = blender_camera.clip_start * ImportOptions.import_scale
    blender_camera.clip_end = blender_camera.clip_end * ImportOptions.import_scale

    camera.position[0] = camera.position[0] * ImportOptions.import_scale
    camera.position[1] = camera.position[1] * ImportOptions.import_scale
    camera.position[2] = camera.position[2] * ImportOptions.import_scale

    camera.target_position[0] = camera.target_position[0] * ImportOptions.import_scale
    camera.target_position[1] = camera.target_position[1] * ImportOptions.import_scale
    camera.target_position[2] = camera.target_position[2] * ImportOptions.import_scale

    camera.up_vector[0] = camera.up_vector[0] * ImportOptions.import_scale
    camera.up_vector[1] = camera.up_vector[1] * ImportOptions.import_scale
    camera.up_vector[2] = camera.up_vector[2] * ImportOptions.import_scale

    if camera.orthographic:
        distance = camera.position - camera.target_position
        dist_target_to_camera = distance.length
        blender_camera.ortho_scale = dist_target_to_camera / 1.92
        blender_camera.type = "ORTHO"
    else:
        blender_camera.type = "PERSP"

    obj = bpy.data.objects.new(camera.name, blender_camera)
    obj.name = camera.name
    obj.location = camera.position
    obj.hide_viewport = camera.hidden
    obj.hide_render = camera.hidden

    if collection is None:
        collection = group.get_scene_collection()
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
    # _*_lp_lc_mod
    blender_lookat.look_at(obj, camera.target_position, camera.up_vector)
    # _*_mod_end

    return obj

# _*_lp_lc_mod
# **************************************************************************************
def iterate_camera_position(camera, render, vcentre3d, move_camera, vertices):

    bpy.context.view_layer.update()

    minX = sys.float_info.max
    maxX = -sys.float_info.max
    minY = sys.float_info.max
    maxY = -sys.float_info.max

    # Calculate matrix to take 3d points into normalised camera space
    modelview_matrix = camera.matrix_world.inverted()

    get_depsgraph_method = getattr(bpy.context, "evaluated_depsgraph_get", None)
    if callable(get_depsgraph_method):
        depsgraph = get_depsgraph_method()
    else:
        depsgraph = bpy.context.depsgraph
    projection_matrix = camera.calc_matrix_camera(
        depsgraph,
        x=render.resolution_x,
        y=render.resolution_y,
        scale_x=render.pixel_aspect_x,
        scale_y=render.pixel_aspect_y)

    mp_matrix = projection_matrix @ modelview_matrix
    mpinv_matrix = mp_matrix.copy()
    mpinv_matrix.invert()

    is_ortho = bpy.context.scene.camera.data.type == 'ORTHO'

    # Convert 3d points to camera space, calculating the min and max extents in 2d normalised camera space.
    min_dist_to_camera = sys.float_info.max
    for point in vertices:
        p1 = mp_matrix @ Vector((point.x, point.y, point.z, 1))
        if is_ortho:
            point2d = (p1.x, p1.y)
        elif abs(p1.w) < 1e-8:
            continue
        else:
            point2d = (p1.x / p1.w, p1.y / p1.w)
        minX = min(point2d[0], minX)
        minY = min(point2d[1], minY)
        maxX = max(point2d[0], maxX)
        maxY = max(point2d[1], maxY)
        disttocamera = (point - camera.location).length
        min_dist_to_camera = min(min_dist_to_camera, disttocamera)

    # helpers.render_print("minX,maxX: " + ('%.5f' % minX) + "," + ('%.5f' % maxX))
    # helpers.render_print("minY,maxY: " + ('%.5f' % minY) + "," + ('%.5f' % maxY))

    # Calculate distance d from camera to centre of the model
    d = (vcentre3d - camera.location).length

    # Which axis is filling most of the display?
    largest_span = max(maxX - minX, maxY - minY)

    # Force option to be in range
    camera_border_percent = min((ImportOptions.camera_border_percent / 100.0), 0.99999)

    # How far should the camera be away from the object?
    # Zoom in or out to make the coverage close to 1 
    # (or 1-border if theres a border amount specified)
    scale = largest_span / (2 - 2 * camera_border_percent)
    desired_min_dist_to_camera = scale * min_dist_to_camera

    # Adjust d to be the change in distance from the centre of the object
    offsetD = min_dist_to_camera - desired_min_dist_to_camera

    # Calculate centre of object on screen
    centre2d = Vector(((minX + maxX) * 0.5, (minY + maxY) * 0.5))

    # Get the forward vector of the camera
    temp_matrix = camera.matrix_world.copy()
    temp_matrix.invert()
    forwards4d = -temp_matrix[2]
    forwards3d = Vector((forwards4d.x, forwards4d.y, forwards4d.z))

    # Transform the 2d centre of object back into 3d space
    if is_ortho:
        centre3d = mpinv_matrix @ Vector((centre2d.x, centre2d.y, 0, 1))
        centre3d = Vector((centre3d.x, centre3d.y, centre3d.z))

        # Move centre3d a distance d from the camera plane
        v = centre3d - camera.location
        dist = v.dot(forwards3d)
        centre3d = centre3d + (d - dist) * forwards3d
    else:
        centre3d = mpinv_matrix @ Vector((centre2d.x, centre2d.y, -1, 1))
        centre3d = Vector((centre3d.x / centre3d.w, centre3d.y / centre3d.w, centre3d.z / centre3d.w))

        # Make sure the 3d centre of the object is distance d from the camera location
        forwards = centre3d - camera.location
        forwards.normalize()
        centre3d = camera.location + d * forwards

    # Get the centre of the viewing area in 3d space at distance d from the camera
    # This is where we want to move the object to
    origin3d = camera.location + d * forwards3d

    if move_camera:
        if is_ortho:
            offset3d = (centre3d - origin3d)

            camera.data.ortho_scale *= scale
        else:
            # How much do we want to move the camera?
            # We want to move the camera by the same amount as if we moved the centre of the object to the centre of the viewing area.
            # In practice, this is not completely accurate, since the perspective projection changes the objects silhouette in 2d space
            # when we move the camera, but it's close in practice. We choose to move it conservatively by 93% of our calculated amount,
            # a figure obtained by some quick practical observations of the convergence on a few test models.
            offset3d = 0.93 * (centre3d - origin3d) + offsetD * forwards3d
        # helpers.render_print("offset3d: " + ('%.5f' % offset3d.x) + "," + ('%.5f' % offset3d.y) + "," + ('%.5f' % offset3d.z) + " length:" + ('%.5f' % offset3d.length))
        # helpers.render_print("move by: " + ('%.5f' % offset3d.length))
        camera.location += Vector((offset3d.x, offset3d.y, offset3d.z))
        return offset3d.length

    return 0.0
# _*_mod_end
