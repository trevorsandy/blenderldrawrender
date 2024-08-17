import bpy
import bmesh
# _*_lp_lc_mod
from mathutils import Vector
from mathutils import Euler
# _*_mod_end

from .import_settings import ImportSettings
from .import_options import ImportOptions
from .blender_materials import BlenderMaterials
from .ldraw_file import LDrawFile
from .ldraw_node import LDrawNode
from .filesystem import FileSystem
from .ldraw_color import LDrawColor
from . import blender_camera
# _*_lp_lc_mod
from . import blender_light
# _*_mod_end

from . import helpers
from . import strings
from . import group
from . import ldraw_meta
from . import ldraw_object
from . import matrices
# _*_lp_lc_mod
from . import ldraw_props
# _*_mod_end


def do_import(filepath, color_code="16", return_mesh=False):
    # _*_lp_lc_mod
    #print(filepath)  # TODO: multiple filepaths?
    # _*_mod_end

    ImportSettings.apply_settings()

    BlenderMaterials.reset_caches()
    FileSystem.reset_caches()
    LDrawColor.reset_caches()
    LDrawFile.reset_caches()
    LDrawNode.reset_caches()
    group.reset_caches()
    ldraw_meta.reset_caches()
    ldraw_object.reset_caches()
    matrices.reset_caches()

    __scene_setup()

    FileSystem.build_search_paths(parent_filepath=filepath)
    LDrawFile.read_color_table()
    BlenderMaterials.create_blender_node_groups()

    ldraw_file = LDrawFile.get_file(filepath)
    if ldraw_file is None:
        return

    if ldraw_file.is_configuration():
        __load_materials(ldraw_file)
        return

    root_node = LDrawNode()
    root_node.is_root = True
    root_node.file = ldraw_file

    group.groups_setup(filepath)
    ldraw_meta.meta_step()

    # return root_node.load()
    obj = root_node.load(color_code=color_code, return_mesh=return_mesh)

    # s = {str(k): v for k, v in sorted(LDrawNode.geometry_datas2.items(), key=lambda ele: ele[1], reverse=True)}
    # helpers.write_json("gs2.json", s, indent=4)

    # _*_lp_lc_mod
    if not ldraw_object.top_empty is None:
        if ldraw_file.actual_part_type is None:
            ldraw_file.actual_part_type = 'Model'
        ldraw_props.set_props(ldraw_object.top_empty, ldraw_file, "16")
        mesh_objs = []
        top_obj = None

        for collection in bpy.data.collections:
            for top in collection.all_objects:
                if top.name == collection.name:
                    top_obj = top
                    mesh_objs = [mesh_obj for mesh_obj in top.children if mesh_obj.type == 'MESH']
                    break
            if mesh_objs and top_obj is not None:
                break

    if ImportOptions.add_environment or ImportOptions.position_camera:
        vertices = []
        if mesh_objs:
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY')
            for mesh_obj in mesh_objs:
                points = [mesh_obj.matrix_world @ Vector(v[:]) for v in mesh_obj.bound_box]
                vertices.extend(points)

            # Calculate our bounding box in global coordinate space
            bbox_min = Vector((0, 0, 0))
            bbox_max = Vector((0, 0, 0))

            bbox_min[0] = min(v[0] for v in vertices)
            bbox_min[1] = min(v[1] for v in vertices)
            bbox_min[2] = min(v[2] for v in vertices)
            bbox_max[0] = max(v[0] for v in vertices)
            bbox_max[1] = max(v[1] for v in vertices)
            bbox_max[2] = max(v[2] for v in vertices)

            bbox_ctr = (bbox_min + bbox_max) * 0.5
            offset_to_centre_model = Vector((-bbox_ctr.x, -bbox_ctr.y, -bbox_min.z))

            if top_obj:
                top_obj.location += offset_to_centre_model

            # Offset all points
            vertices = [v + offset_to_centre_model for v in vertices]
            offset_to_centre_model = Vector((0, 0, 0))
            
    if ImportOptions.position_camera:
        if ldraw_meta.cameras:
            imported_camera_name = ldraw_meta.cameras[0].name
            helpers.render_print(f"Positioning Camera: {imported_camera_name}")
        else:
            camera = bpy.context.scene.camera            
            if camera is not None:
                # Set up a default camera position and rotation
                helpers.render_print(f"Positioning Camera: {camera.data.name}")
                camera.location = Vector((6.5, -6.5, 4.75))
                camera.rotation_mode = 'XYZ'
                camera.rotation_euler = Euler((1.0471975803375244, 0.0, 0.7853981852531433), 'XYZ')
                # Must have at least three vertices to move the camera
                if len(vertices) >= 3:
                    render = bpy.context.scene.render
                    is_ortho = camera.data.type == 'ORTHO'
                    if is_ortho:
                        blender_camera.iterate_camera_position(camera, render, bbox_ctr, True, vertices)
                    else:
                        for i in range(20):
                            error = blender_camera.iterate_camera_position(camera, render, bbox_ctr, True, vertices)
                            if error < 0.001:
                                break
    # _*_mod_end
    
    if ImportOptions.meta_step:
        if ImportOptions.set_end_frame:
            bpy.context.scene.frame_end = ldraw_meta.current_frame + ImportOptions.frames_per_step
            bpy.context.scene.frame_set(bpy.context.scene.frame_end)

    # _*_lp_lc_mod
    # Get existing scene names
    scene_object_names = [x.name for x in bpy.context.scene.objects]

    # Remove default cube object
    cube_object = 'Cube'
    if cube_object in scene_object_names:
        cube = bpy.context.scene.objects[cube_object]
        if cube.location.length < 0.001:
            __unlink_from_scene(cube)

    # Remove default camera
    if ldraw_meta.cameras:
        camera = bpy.context.scene.camera
        if camera is not None:
            __unlink_from_scene(camera)

    # Remove default light
    if ldraw_meta.lights:
        light_object = 'Light'
        if light_object in scene_object_names:
            light = bpy.context.scene.objects[light_object]
            light_location = light.location - Vector((4.076245307922363, 1.0054539442062378, 5.903861999511719))
            if light_location.length < 0.001:
                __unlink_from_scene(light)
    # _*_mod_end

    max_clip_end = 0
    for camera in ldraw_meta.cameras:
        camera = blender_camera.create_camera(camera, empty=ldraw_object.top_empty, collection=group.top_collection)
        if bpy.context.scene.camera is None:
            if camera.data.clip_end > max_clip_end:
                max_clip_end = camera.data.clip_end
            bpy.context.scene.camera = camera
        helpers.render_print(f"Created Camera: {camera.data.name}")
        camera.parent = obj

    # _*_lp_lc_mod
    for light in ldraw_meta.lights:
        light = blender_light.create_light(light, empty=ldraw_object.top_empty, collection=group.top_collection)
        helpers.render_print(f"Created Light: {light.data.name}")
        light.parent = obj

    if bpy.context.screen is not None:
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    # space.shading.show_backface_culling = False
                    if space.type == "VIEW_3D":
                        if space.clip_end < max_clip_end:
                            space.clip_end = max_clip_end

    if ImportOptions.add_environment:
        __setup_environment()
    
    __setup_realistic_look()
    # _*_mod_end

    return obj


def __scene_setup():
    bpy.context.scene.eevee.use_ssr = True
    bpy.context.scene.eevee.use_ssr_refraction = True
    bpy.context.scene.eevee.use_taa_reprojection = True

    # https://blender.stackexchange.com/a/146838
    # TODO: use line art modifier with grease pencil object
    #  parts can't be in more than one group if those group's parent is targeted by the modifier
    #  groups and ungroup collections can't be under model.ldr collection or else the lines don't render
    #  studs, and maybe other intersecting geometry, may have broken lines
    #  checking "overlapping edges as contour" helps, applying edge split, scale, marking freestyle edge does not seem to make a difference
    if ImportOptions.use_freestyle_edges:
        bpy.context.scene.render.use_freestyle = True
        linesets = bpy.context.view_layer.freestyle_settings.linesets
        if len(linesets) < 1:
            linesets.new("LDraw LineSet")
        lineset = linesets[0]
        # lineset.linestyle.color = color.edge_color
        lineset.select_by_visibility = True
        lineset.select_by_edge_types = True
        lineset.select_by_face_marks = False
        lineset.select_by_collection = False
        lineset.select_by_image_border = False
        lineset.visibility = 'VISIBLE'
        lineset.edge_type_negation = 'INCLUSIVE'
        lineset.edge_type_combination = 'OR'
        lineset.select_silhouette = False
        lineset.select_border = False
        lineset.select_contour = False
        lineset.select_suggestive_contour = False
        lineset.select_ridge_valley = False
        lineset.select_crease = False
        lineset.select_edge_mark = True
        lineset.select_external_contour = False
        lineset.select_material_boundary = False

# _*_lp_lc_mod
def __unlink_from_scene(obj):
    if bpy.context.collection.objects.find(obj.name) >= 0:
        bpy.context.collection.objects.unlink(obj)
# _*_mod_end

def __load_materials(file):
    ImportOptions.meta_group = False
    ImportOptions.parent_to_empty = False
    ImportOptions.make_gaps = False

    # slope texture demonstration
    obj = do_import('3044.dat')
    if obj is not None:
        obj.location.x = 0.0
        obj.location.y = 5.0
        obj.location.z = 0.5

    # texmap demonstration
    obj = do_import('27062p01.dat')
    if obj is not None:
        obj.location.x = 3
        obj.location.y = 5

    # cloth demonstration
    obj = do_import('50231.dat')
    if obj is not None:
        obj.location.x = 6
        obj.location.y = 5

    colors = {}
    group_name = 'blank'
    for line in file.lines:
        clean_line = helpers.clean_line(line)
        strip_line = line.strip()

        if clean_line.startswith("0 // LDraw"):
            group_name = clean_line
            colors[group_name] = []
            continue

        if clean_line.startswith("0 !COLOUR "):
            colors[group_name].append(LDrawColor.parse_color(clean_line))
            continue

    j = 0
    for collection_name, codes in colors.items():
        scene_collection = group.get_scene_collection()
        collection = group.get_collection(collection_name, scene_collection)

        for i, color_code in enumerate(codes):
            bm = bmesh.new()

            monkey = True
            if monkey:
                prefix = 'monkey'
                bmesh.ops.create_monkey(bm)
            else:
                prefix = 'cube'
                bmesh.ops.create_cube(bm, size=1.0)

            helpers.ensure_bmesh(bm)

            for f in bm.faces:
                f.smooth = True

            mesh = bpy.data.meshes.new(f"{prefix}_{color_code}")
            mesh[strings.ldraw_color_code_key] = color_code

            material = BlenderMaterials.get_material(color_code, easy_key=True)

            # https://blender.stackexchange.com/questions/23905/select-faces-depending-on-material
            if material.name not in mesh.materials:
                mesh.materials.append(material)
            for face in bm.faces:
                face.material_index = mesh.materials.find(material.name)

            helpers.finish_bmesh(bm, mesh)
            helpers.finish_mesh(mesh)

            obj = bpy.data.objects.new(mesh.name, mesh)
            obj[strings.ldraw_filename_key] = file.name
            obj[strings.ldraw_color_code_key] = color_code

            obj.modifiers.new("Subdivision", type='SUBSURF')
            obj.location.x = i * 3
            obj.location.y = -j * 3

            color = LDrawColor.get_color(color_code)
            obj.color = color.linear_color_a

            group.link_obj(collection, obj)
        j += 1

# _*_lp_lc_mod
def __get_layers(scene):
    return scene.view_layers

def __get_layer_names(scene):
    return list(map((lambda x: x.name), __get_layers(scene)))

def __add_plane(location, size):
    parent = group.top_collection.name
    bpy.context.view_layer.active_layer_collection = \
    bpy.context.view_layer.layer_collection.children[parent]
    bpy.ops.mesh.primitive_plane_add(size=size, enter_editmode=False, location=location)

def __use_denoising(scene, denoising):
    if hasattr(__get_layers(scene)[0], "cycles"):
        __get_layers(scene)[0].cycles.use_denoising = denoising

def __setup_realistic_look():
    # Setup realistic look
    scene = bpy.context.scene
    render = scene.render

    # Use cycles render
    scene.render.engine = 'CYCLES'

    # Add environment texture for world
    if ImportOptions.add_environment and FileSystem.environment_file != "":
        scene.world.use_nodes = True
        nodes = scene.world.node_tree.nodes
        links = scene.world.node_tree.links
        world_node_names = list(map((lambda x: x.name), scene.world.node_tree.nodes))

        if 'LegoEnvMap' in world_node_names:
            env_tex = nodes['LegoEnvMap']
        else:
            env_tex          = nodes.new('ShaderNodeTexEnvironment')
            env_tex.location = (-250, 300)
            env_tex.name     = 'LegoEnvMap'
            env_tex.image    = bpy.data.images.load(FileSystem.environment_file, check_existing=True)

        if 'Background' in world_node_names:
            background = nodes['Background']
            links.new(env_tex.outputs[0], background.inputs[0])
    else:
        scene.world.color = (1.0, 1.0, 1.0)

    __use_denoising(scene, True)

    if (scene.cycles.samples < 400):
        scene.cycles.samples = 400
    if (scene.cycles.diffuse_bounces < 20):
        scene.cycles.diffuse_bounces = 20
    if (scene.cycles.glossy_bounces < 20):
        scene.cycles.glossy_bounces = 20

    bpy.context.scene.eevee.use_ssr = True
    bpy.context.scene.eevee.use_ssr_refraction = True
    bpy.context.scene.eevee.use_taa_reprojection = True       

# Check layer names to see if we were previously rendering instructions and change settings back.
    layer_names = __get_layer_names(scene)
    if ("SolidBricks" in layer_names) or ("TransparentBricks" in layer_names):
        render.use_freestyle = False

        # Change camera back to Perspective
        if scene.camera is not None:
            scene.camera.data.type = 'PERSP'

        # For Blender Render, reset to opaque background
        render.alpha_mode = 'SKY'

        # Turn off cycles transparency
        scene.cycles.film_transparent = False

        # Get the render/view layers we are interested in:
        layers = __get_layers(scene)

        # If we have previously added render layers for instructions look, re-enable any disabled render layers
        for i in range(len(layers)):
            layers[i].use = True

        # Un-name SolidBricks and TransparentBricks layers
        if "SolidBricks" in layer_names:
            layers.remove(layers["SolidBricks"])

        if "TransparentBricks" in layer_names:
            layers.remove(layers["TransparentBricks"])

        # Re-enable all layers
        for i in range(len(layers)):
            layers[i].use = True

        # Create Compositing Nodes
        scene.use_nodes = True

        # If scene nodes exist for compositing instructions look, remove them
        node_names = list(map((lambda x: x.name), scene.node_tree.nodes))
        if "Solid" in node_names:
            scene.node_tree.nodes.remove(scene.node_tree.nodes["Solid"])

        if "Trans" in node_names:
            scene.node_tree.nodes.remove(scene.node_tree.nodes["Trans"])

        if "Z Combine" in node_names:
            scene.node_tree.nodes.remove(scene.node_tree.nodes["Z Combine"])

        # Set up standard link from Render Layers to Composite
        if "Render Layers" in node_names:
            if "Composite" in node_names:
                rl = scene.node_tree.nodes["Render Layers"]
                zCombine = scene.node_tree.nodes["Composite"]

                links = scene.node_tree.links
                links.new(rl.outputs[0], zCombine.inputs[0])    

def __setup_environment():
    # Add ground plane with white material
    __add_plane((0, 0, 0), 100000 * ImportOptions.import_scale)

    blender_name = "Mat_LegoGroundPlane"
    # Reuse current material if it exists, otherwise create a new material
    if bpy.data.materials.get(blender_name) is None:
        material = bpy.data.materials.new(blender_name)
    else:
        material = bpy.data.materials[blender_name]

    # Use nodes
    material.use_nodes = True

    nodes = material.node_tree.nodes
    links = material.node_tree.links

    # Remove any existing nodes
    for n in nodes:
        nodes.remove(n)

    node = nodes.new('ShaderNodeBsdfDiffuse')
    node.location = 0, 5
    node.inputs['Color'].default_value = (1, 1, 1, 1)
    node.inputs['Roughness'].default_value = 1.0

    out = nodes.new('ShaderNodeOutputMaterial')
    out.location = 200, 0
    links.new(node.outputs[0], out.inputs[0])

    for obj in bpy.context.selected_objects:
        obj.name = "LegoGroundPlane"
        if obj.data.materials:
            obj.data.materials[0] = material
        else:
            obj.data.materials.append(material)
# _*_mod_end
