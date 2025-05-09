import bpy
import mathutils

from . import matrices
from .import_options import ImportOptions
from .pe_texmap import PETexInfo, PETexmap
from .texmap import TexMap
from .geometry_data import FaceData
from . import group
from . import helpers
from . import ldraw_camera
# _*_lp_lc_mod
from . import ldraw_light
# _*_mod_end


current_frame = 0
current_step = 0
cameras = []
camera = None
# _*_lp_lc_mod
lights = []
light = None
# _*_mod_end


def reset_caches():
    global current_frame
    global current_step
    global cameras
    global camera
# _*_lp_lc_mod    
    global lights
    global light
# _*_mod_end

    current_frame = 0
    current_step = 0
    cameras.clear()
    camera = None
# _*_lp_lc_mod
    lights.clear()
    light = None
# _*_mod_end

def meta_bfc(ldraw_node, child_node, matrix, local_cull, winding, invert_next, accum_invert):
    clean_line = child_node.line
    _params = clean_line.split()[2:]

    # https://www.ldraw.org/article/415.html#processing
    if ldraw_node.bfc_certified is not False:
        if ldraw_node.bfc_certified is None and "NOCERTIFY" not in _params:
            ldraw_node.bfc_certified = True

        if "CERTIFY" in _params:
            ldraw_node.bfc_certified = True

        if "NOCERTIFY" in _params:
            ldraw_node.bfc_certified = False

        """
        https://www.ldraw.org/article/415.html#rendering
        Degenerate Matrices. Some orientation matrices do not allow calculation of a determinate.
        This calculation is central to BFC processing. If an orientation matrix for a subfile is
        degenerate, then culling will not be possible for that subfile.

        https://math.stackexchange.com/a/792591
        A singular matrix, also known as a degenerate matrix, is a square matrix whose determinate is zero.
        https://www.algebrapracticeproblems.com/singular-degenerate-matrix/
        A singular (or degenerate) matrix is a square matrix whose inverse matrix cannot be calculated.
        Therefore, the determinant of a singular matrix is equal to 0.
        """
        if matrix.determinant() == 0:
            ldraw_node.bfc_certified = False

    if "CLIP" in _params:
        local_cull = True

    if "NOCLIP" in _params:
        local_cull = False

    if "CCW" in _params:
        if accum_invert:
            winding = "CW"
        else:
            winding = "CCW"

    if "CW" in _params:
        if accum_invert:
            winding = "CCW"
        else:
            winding = "CW"

    if "INVERTNEXT" in _params:
        invert_next = True

    """
    https://www.ldraw.org/article/415.html#rendering
    If the rendering engine does not detect and adjust for reversed matrices, the winding of all polygons in
    the subfile will be switched, causing the subfile to be rendered incorrectly.

    The typical method of determining that an orientation matrix is reversed is to calculate the determinant of
    the matrix. If the determinant is negative, then the matrix has been reversed.

    The typical way to adjust for matrix reversals is to switch the expected winding of the polygon vertices.
    That is, if the file specifies the winding as CW and the orientation matrix is reversed, the rendering
    program would proceed as if the winding is CCW.

    The INVERTNEXT option also reverses the winding of the polygons within the subpart or primitive.
    If the matrix applied to the subpart or primitive has itself been reversed the INVERTNEXT processing
    is done IN ADDITION TO the automatic inversion - the two effectively cancelling each other out.
    """
    if matrix.determinant() < 0:
        if not invert_next:
            if winding == "CW":
                winding = "CCW"
            else:
                winding = "CW"

    return local_cull, winding, invert_next


def meta_step():
    global current_step
    global current_frame

    if not ImportOptions.meta_step:
        return

    first_frame = (ImportOptions.starting_step_frame + ImportOptions.frames_per_step)
    current_step_frame = (ImportOptions.frames_per_step * current_step)
    current_frame = first_frame + current_step_frame
    current_step += 1

    if ImportOptions.set_timeline_markers:
        bpy.context.scene.timeline_markers.new("STEP", frame=current_frame)

    if ImportOptions.meta_step_groups:
        collection_name = f"{group.top_collection.name} Steps"
        host_collection = group.top_collection
        steps_collection = group.get_collection(collection_name, host_collection)
        helpers.hide_obj(steps_collection)

        collection_name = f"Step {str(current_step)}"
        host_collection = steps_collection
        step_collection = group.get_collection(collection_name, host_collection)
        group.current_step_group = step_collection


def do_meta_step(obj):
    if ImportOptions.meta_step:
        helpers.hide_obj(obj)
        obj.keyframe_insert(data_path="hide_render", frame=ImportOptions.starting_step_frame)
        obj.keyframe_insert(data_path="hide_viewport", frame=ImportOptions.starting_step_frame)

        helpers.show_obj(obj)
        obj.keyframe_insert(data_path="hide_render", frame=current_frame)
        obj.keyframe_insert(data_path="hide_viewport", frame=current_frame)


def meta_save():
    if ImportOptions.meta_save:
        if ImportOptions.set_timeline_markers:
            bpy.context.scene.timeline_markers.new("SAVE", frame=current_frame)


def meta_clear():
    if ImportOptions.meta_clear:
        if ImportOptions.set_timeline_markers:
            bpy.context.scene.timeline_markers.new("CLEAR", frame=current_frame)
        if group.top_collection is not None:
            for obj in group.top_collection.all_objects:
                helpers.hide_obj(obj)
                obj.keyframe_insert(data_path="hide_render", frame=current_frame)
                obj.keyframe_insert(data_path="hide_viewport", frame=current_frame)


def meta_print(child_node):
    if ImportOptions.meta_print_write:
        print(child_node.meta_args["message"])


def meta_group(child_node):
    if ImportOptions.meta_group:
        if child_node.meta_command == "group_def":
            meta_group_def(child_node)
        elif child_node.meta_command == "group_nxt":
            meta_group_nxt(child_node)
        elif child_node.meta_command == "group_begin":
            meta_group_begin(child_node)
        elif child_node.meta_command == "group_end":
            meta_group_end()


def meta_group_def(child_node):
    group.collection_id_map[child_node.meta_args["id"]] = child_node.meta_args["name"]
    name = group.collection_id_map[child_node.meta_args["id"]]
    collection_name = f"{group.top_collection.name} {name}"
    host_collection = group.groups_collection
    group.get_collection(collection_name, host_collection)


def meta_group_nxt(child_node):
    group.stored_collection = group.next_collection
    collection = None
    if child_node.meta_args["id"] in group.collection_id_map:
        name = group.collection_id_map[child_node.meta_args["id"]]
        collection_name = f"{group.top_collection.name} {name}"
        collection = bpy.data.collections.get(collection_name)
    group.next_collection = collection
    group.end_next_collection = True


def meta_group_begin(child_node):
    if group.next_collection is not None:
        group.next_collections.append(group.next_collection)

    name = child_node.meta_args["name"]
    collection_name = f"{group.top_collection.name} {name}"
    host_collection = group.groups_collection
    collection = group.get_collection(collection_name, host_collection)
    group.next_collection = collection

    if len(group.next_collections) > 0:
        host_collection = group.next_collections[-1]
        group.link_child(collection, host_collection)
    # else:
    #     host_collection = group.top_collection
    #     group.link_child(collection, host_collection)


def meta_group_end():
    if len(group.next_collections) > 0:
        group.next_collection = group.next_collections.pop()
    else:
        group.next_collection = None


def meta_root_group_nxt(ldraw_node, child_node):
    if ImportOptions.meta_group:
        if ldraw_node.is_root and child_node.meta_command != "group_nxt":
            if group.end_next_collection:
                group.next_collection = None


# _*_lp_lc_mod
def meta_lp_lc_camera(child_node, matrix):
    if not ImportOptions.import_cameras:
        return
    # _*_mod_end

    global cameras
    global camera

    clean_line = child_node.line
    _params = clean_line.lower().split()[3:]

    # _*_lp_lc_mod
    is_lpub_meta = clean_line.startswith("0 !LPUB ")
    # _*_mod_end

    if camera is None:
        camera = ldraw_camera.LDrawCamera()

    # https://www.leocad.org/docs/meta.html
    # "Camera commands can be grouped in the same line"
    # _params = _params[1:] at the end bumps promotes _params[2] to _params[1]
    while len(_params) > 0:
        if _params[0] == "fov":
            camera.fov = float(_params[1])
            _params = _params[2:]
        elif _params[0] == "znear":
            camera.z_near = float(_params[1])
            _params = _params[2:]
        elif _params[0] == "zfar":
            camera.z_far = float(_params[1])
            _params = _params[2:]
        elif _params[0] == "position":
            (x, y, z) = map(float, _params[1:4])
            # _*_lp_lc_mod
            if is_lpub_meta:
                vector = matrix @ mathutils.Vector((x, y, z))
            else:
                vector = matrix @ mathutils.Vector((x, y, z)) @ matrices.rotation_matrix
            # _*_mod_end
            camera.position = vector
            _params = _params[4:]
        elif _params[0] == "target_position":
            (x, y, z) = map(float, _params[1:4])
            # _*_lp_lc_mod
            if is_lpub_meta:
                vector = matrix @ mathutils.Vector((x, y, z))
            else:
                vector = matrix @ mathutils.Vector((x, y, z)) @ matrices.rotation_matrix
            # _*_mod_end
            camera.target_position = vector
            _params = _params[4:]
        elif _params[0] == "up_vector":
            (x, y, z) = map(float, _params[1:4])
            # _*_lp_lc_mod
            if is_lpub_meta:
                vector = matrix @ mathutils.Vector((x, y, z))
            else:
                vector = matrix @ mathutils.Vector((x, y, z)) @ matrices.rotation_matrix
            # _*_mod_end
            camera.up_vector = vector
            _params = _params[4:]
        elif _params[0] == "orthographic":
            camera.orthographic = True
            _params = _params[1:]
        elif _params[0] == "hidden":
            camera.hidden = True
            _params = _params[1:]
        elif _params[0] == "name":
            # "0 !LEOCAD CAMERA NAME Camera  2".split("NAME ")[1] => "Camera  2"
            # "NAME Camera  2".split("NAME ")[1] => "Camera  2"
            name_args = clean_line.split("NAME ")
            # _*_lp_lc_mod
            camera.name = "Imported {0}".format(name_args[1])
            # _*_mod_end

            # By definition this is the last of the parameters
            _params = []

            cameras.append(camera)
            camera = None
        else:
            _params = _params[1:]

# _*_lp_lc_mod
def meta_lp_lc_light(child_node, matrix):
    if not ImportOptions.import_lights:
        return

    global lights
    global light
    
    clean_line = child_node.line
    _params = helpers.get_params(clean_line, lowercase=True)[3:]

    is_lpub_meta = clean_line.startswith("0 !LPUB ")

    if light is None:
        light = ldraw_light.LDrawLight()
    # "Light commands can be grouped in the same line"
    # _params = _params[1:] at the end bumps promotes _params[2] to _params[1]
    while len(_params) > 0:
        if _params[0] == "position":
            (x, y, z) = map(float, _params[1:4])
            if is_lpub_meta:
                vector = matrix @ mathutils.Vector((x, y, z))
            else:
                vector = matrix @ mathutils.Vector((x, y, z)) @ matrices.rotation_matrix
            light.position = vector
            _params = _params[4:]
        elif _params[0] == "target_position":
            (x, y, z) = map(float, _params[1:4])
            if is_lpub_meta:
                vector = matrix @ mathutils.Vector((x, y, z))
            else:
                vector = matrix @ mathutils.Vector((x, y, z)) @ matrices.rotation_matrix
            light.target_position = vector
            _params = _params[4:]
        elif _params[0] == "rotation":
            (x1, y1, z1, x2, y2, z2, x3, y3, z3) = map(float, _params[1:10])
            light.target_position = light.matrix44ToEulerAngles(mathutils.Matrix((
                (x1, y1, z1, 0),(x2, y2, z2, 0),(x3, y3, z3, 0),
                (light.position.x, light.position.y, light.position.z, 1))))
            _params = _params[10:]
        elif _params[0] == "color" or _params[0] == "color_rgb":
            light.color = mathutils.Vector(
                (float(_params[1]), float(_params[2]), float(_params[3])))
            _params = _params[4:]
        elif _params[0] == "blender_power" or _params[0] == "power" or _params[0] == "strength":
            light.exponent = float(_params[1])
            _params = _params[2:]
        elif  _params[0] == "blender_sun_angle" or  _params[0] == "blender_directional_angle" or _params[0] == "angle":
            light.sun_angle = ImportOptions.import_scale * float(_params[1])
            _params = _params[2:]
        elif _params[0] == "blender_point_radius" or _params[0] == "blender_spot_radius" or _params[0] == "radius":
            light.shadow_radius = float(_params[1])
            _params = _params[2:]
        elif _params[0] == "spot_cone_angle" or _params[0] == "spot_size":
            light.spot_size = float(_params[1])
            _params = _params[2:]
        elif _params[0] == "spot_blend":
            light.spot_blend = float(_params[1])
            _params = _params[2:]
        elif _params[0] == "spot_penumbra_angle":
            penumbra_angle = float(_params[1])
            if penumbra_angle > 0:
                light.spot_blend = penumbra_angle / light.spot_size
            _params = _params[2:]
        elif _params[0] == "area_size" or _params[0] == "size":
            light.size = float(_params[1])
            _params = _params[2:]
        elif _params[0] == "area_size_x" or _params[0] == "width":
            light.area_size_x = float(_params[1])
            _params = _params[2:]
        elif _params[0] == "area_size_y" or _params[0] == "height":
            light.area_size_y = float(_params[1])
            _params = _params[2:]
        elif _params[0] == "area_shape" or _params[0] == "shape":
            light.shape = _params[1].upper().strip()
            _params = _params[2:]
        elif _params[0] == "blender_specular" or _params[0] == "specular":
            light.specular = float(_params[1])
            _params = _params[2:]
        elif _params[0] == "blender_cutoff_distance" or _params[0] == "cutoff_distance":
            light.use_cutoff = True
            light.cutoff_distance = float(_params[1])
            _params = _params[2:]
        elif _params[0] == "shadowless":
            light.use_shadow = False
            _params = _params[1:]
        elif _params[0] == "type":
            light.type = _params[1].upper().strip()
            _params = _params[2:]
        elif _params[0] == "name":
            name_args = clean_line.split("NAME ")
            light.name = "Imported {0}".format(name_args[1])

            # By definition this is the last of the light parameters
            _params = []

            lights.append(light)
            light = None
        else:
            _params = _params[1:]
# _*_mod_end

# https://www.ldraw.org/documentation/ldraw-org-file-format-standards/language-extension-for-texture-mapping.html
def meta_texmap(ldraw_node, child_node, matrix):
    if not ImportOptions.meta_texmap:
        return

    clean_line = child_node.line

    if ldraw_node.texmap_start:
        if clean_line == "0 !TEXMAP FALLBACK":
            ldraw_node.texmap_fallback = True
        elif clean_line == "0 !TEXMAP END":
            set_texmap_end(ldraw_node)
    elif clean_line.startswith("0 !TEXMAP START ") or clean_line.startswith("0 !TEXMAP NEXT "):
        if clean_line.startswith("0 !TEXMAP START "):
            ldraw_node.texmap_start = True
        elif clean_line.startswith("0 !TEXMAP NEXT "):
            ldraw_node.texmap_next = True
        ldraw_node.texmap_fallback = False

        method = clean_line.split()[3]

        new_texmap = TexMap(method=method)
        if new_texmap.is_planar():
            _params = clean_line.split(maxsplit=13)  # planar

            (x1, y1, z1, x2, y2, z2, x3, y3, z3) = map(float, _params[4:13])

            texture_params = helpers.parse_csv_line(_params[13], 2)
            texture = texture_params[0]
            glossmap = texture_params[1]
            if glossmap == "":
                glossmap = None

            new_texmap.parameters = [
                matrix @ mathutils.Vector((x1, y1, z1)),
                matrix @ mathutils.Vector((x2, y2, z2)),
                matrix @ mathutils.Vector((x3, y3, z3)),
            ]
            new_texmap.texture = texture
            new_texmap.glossmap = glossmap
        elif new_texmap.is_cylindrical():
            _params = clean_line.split(maxsplit=14)  # cylindrical

            (x1, y1, z1, x2, y2, z2, x3, y3, z3, a) = map(float, _params[4:14])

            texture_params = helpers.parse_csv_line(_params[14], 2)
            texture = texture_params[0]
            glossmap = texture_params[1]
            if glossmap == "":
                glossmap = None

            new_texmap.parameters = [
                matrix @ mathutils.Vector((x1, y1, z1)),
                matrix @ mathutils.Vector((x2, y2, z2)),
                matrix @ mathutils.Vector((x3, y3, z3)),
                a,
            ]
            new_texmap.texture = texture
            new_texmap.glossmap = glossmap
        elif new_texmap.is_spherical():
            _params = clean_line.split(maxsplit=15)  # spherical

            (x1, y1, z1, x2, y2, z2, x3, y3, z3, a, b) = map(float, _params[4:15])

            texture_params = helpers.parse_csv_line(_params[15], 2)
            texture = texture_params[0]
            glossmap = texture_params[1]
            if glossmap == "":
                glossmap = None

            new_texmap.parameters = [
                matrix @ mathutils.Vector((x1, y1, z1)),
                matrix @ mathutils.Vector((x2, y2, z2)),
                matrix @ mathutils.Vector((x3, y3, z3)),
                a,
                b,
            ]
            new_texmap.texture = texture
            new_texmap.glossmap = glossmap

        if ldraw_node.texmap is not None:
            ldraw_node.texmaps.append(ldraw_node.texmap)
        ldraw_node.texmap = new_texmap


def set_texmap_end(ldraw_node):
    try:
        ldraw_node.texmap = ldraw_node.texmaps.pop()
    except IndexError as e:
        print(e)
        import traceback
        print(traceback.format_exc())
        ldraw_node.texmap = None

    ldraw_node.texmap_start = False
    ldraw_node.texmap_next = False
    ldraw_node.texmap_fallback = False


# PE_TEX_PATH is the nth line of types 1,3,4
# can be any number of subfile lines - n n n n
# each n is the nth 1,3,4 at that line in that file of the hierarchy
# if final number is a subfile, treat it like a -1 for that file
# if final number is a polygon, apply it to that polygon

# apply to all lines of this file and subfiles that have uv coordinates in their polygon definitions
# 0 PE_TEX_PATH -1
# 0 PE_TEX_INFO PNGBASE64==

# the same function as -1 but for the subfile at line 0
# 0 PE_TEX_PATH 0
# 0 PE_TEX_INFO PNGBASE64==

# for the subfile at index 5, then at index 0 of that subfile
# 0 PE_TEX_PATH 5 0
# 0 PE_TEX_INFO -0.5346 -0.1464 2.2554 3.1670 0.8638 -1.5619 2.4660 -0.0307 -2.4765 12.9236 -0.0535 13.1611 -4.1933 16.2951 8.3761 3.6621 PNGBASE64==

# for the subfile at index 5, then at index 4 of that subfile, apply a shear matrix
# 0 PE_TEX_PATH 5 4
# 0 PE_TEX_NEXT_SHEAR
# 0 PE_TEX_INFO 0.6682 7.2554 13.4921 -3.9588 -1.0797 1.9523 -40.5715 0.2365 -24.6051 -16.5249 0.2054 16.5954 15.5934 18.4983 19.7776 12.8449 PNGBASE64==

# PE_TEX_INFO PNGBASE64== is applied to all lines, including subfiles, that have uv coordinates, should only follow path -1
# PE_TEX_INFO x,y,z,a,b,c,d,e,f,g,h,i,bl/tl,tr/br PNGBASE64== defines a bounding box and its transformation. intersection determines how the uvs will be unwrapped
# multiple PE_TEX_INFO will only respect the most recent one
# if no matrix, identity @ rotation?

# this doesn't work well with some very distorted texture applications
# PE_TEX_NEXT_SHEAR is unknown
# this may be where PE_TEX_NEXT_SHEAR comes in
# is there a hardcoded or programmatically determined shear matrix?
def meta_pe_tex(ldraw_node, child_node):
    if child_node.meta_command == "pe_tex_path":
        meta_pe_tex_path(ldraw_node, child_node)
        ldraw_node.pe_tex_next_shear = False
    elif child_node.meta_command == "pe_tex_info":
        meta_pe_tex_info(ldraw_node, child_node)
        ldraw_node.pe_tex_next_shear = False
    elif child_node.meta_command == "pe_tex_next_shear":
        ldraw_node.pe_tex_next_shear = True


def meta_pe_tex_path(ldraw_node, child_node):
    clean_line = child_node.line
    _params = clean_line.split()[2:]

    ldraw_node.current_pe_tex_path = int(_params[0])
    if len(_params) == 2:
        ldraw_node.current_subfile_pe_tex_path = int(_params[1])


def meta_pe_tex_info(ldraw_node, child_node):
    if ldraw_node.current_pe_tex_path is None:
        return

    clean_line = child_node.line
    _params = clean_line.split()[2:]

    pe_tex_info = PETexInfo()

    from . import base64_handler
    base64_str = _params[-1]
    image = base64_handler.named_png_from_base64_str(f"{ldraw_node.file.name}_{ldraw_node.current_pe_tex_path}.png", base64_str)
    pe_tex_info.image = image.name

    if len(_params) == 17:
        # defines a bounding box and its transformation
        # this doesn't work well with some very distorted texture applications
        # this also may be where PE_TEX_NEXT_SHEAR comes in
        params = _params

        (x, y, z, a, b, c, d, e, f, g, h, i) = map(float, _params[0:12])
        matrix = mathutils.Matrix((
            (a, b, c, x),
            (d, e, f, y),
            (g, h, i, z),
            (0, 0, 0, 1)
        ))

        # this is the original transformation of the bounding box
        _inverse_matrix = matrix.inverted()

        point_min = mathutils.Vector((0, 0))
        point_max = mathutils.Vector((0, 0))
        point_min.x = float(params[12])
        point_min.y = float(params[13])
        point_max.x = float(params[14])
        point_max.y = float(params[15])
        point_diff = point_max - point_min
        box_extents = 0.5 * mathutils.Vector((1, 1))

        pe_tex_info.point_min = point_min.freeze()
        pe_tex_info.point_max = point_max.freeze()
        pe_tex_info.point_diff = point_diff.freeze()
        pe_tex_info.box_extents = box_extents.freeze()
        pe_tex_info.matrix = matrix.freeze()
        pe_tex_info.matrix_inverse = _inverse_matrix.freeze()

    if ldraw_node.current_subfile_pe_tex_path is not None:
        ldraw_node.subfile_pe_tex_infos.setdefault(ldraw_node.current_pe_tex_path, {})
        ldraw_node.subfile_pe_tex_infos[ldraw_node.current_pe_tex_path].setdefault(ldraw_node.current_subfile_pe_tex_path, [])
        ldraw_node.subfile_pe_tex_infos[ldraw_node.current_pe_tex_path][ldraw_node.current_subfile_pe_tex_path].append(pe_tex_info)
    else:
        ldraw_node.pe_tex_infos.setdefault(ldraw_node.current_pe_tex_path, [])
        ldraw_node.pe_tex_infos[ldraw_node.current_pe_tex_path].append(pe_tex_info)

    if ldraw_node.current_pe_tex_path == -1:
        ldraw_node.pe_tex_info = ldraw_node.pe_tex_infos[ldraw_node.current_pe_tex_path]


def meta_edge(child_node, color_code, matrix, geometry_data):
    vertices = [matrix @ v for v in child_node.vertices]

    geometry_data.add_edge_data(
        vertices=vertices,
        color_code=color_code,
    )


def meta_face(ldraw_node, child_node, color_code, matrix, geometry_data, winding, texmap):
    vertices = FaceData.handle_vertex_winding(child_node, matrix, winding)
    pe_texmap = PETexmap.build_pe_texmap(ldraw_node, child_node, winding)

    geometry_data.add_face_data(
        vertices=vertices,
        color_code=color_code,
        texmap=texmap,
        pe_texmap=pe_texmap,
    )


def meta_line(child_node, color_code, matrix, geometry_data):
    vertices = [matrix @ v for v in child_node.vertices]

    geometry_data.add_line_data(
        vertices=vertices,
        color_code=color_code,
    )
