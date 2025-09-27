import mathutils
from .geometry_data import FaceData


class PETexPath:
    def __init__(self):
        self.tex_path = None
        self.tex_infos = []
        self.tex_info = None

    def build_pe_texmap(self, ldraw_node, child_node, winding):
        # child_node is a 3 or 4 line
        clean_line = child_node.line
        _params = clean_line.split()[2:]

        vert_count = len(child_node.vertices)

        pe_texmaps = []

        for tex_info in self.tex_infos:
            # if we have uv data and a pe_tex_info, otherwise pass
            # # custom minifig head > 3626tex.dat (has no pe_tex) > 3626texpole.dat (has no uv data)
            if len(_params) == 15:  # use uvs provided in file
                pe_texmap = PETexmap()
                pe_texmap.image_name = tex_info.image_name

                for i in range(vert_count):
                    if vert_count == 3:
                        x = round(float(_params[i * 2 + 9]), 3)
                        y = round(float(_params[i * 2 + 10]), 3)
                        uv = mathutils.Vector((x, y))
                        pe_texmap.uvs.append(uv)
                    elif vert_count == 4:
                        x = round(float(_params[i * 2 + 11]), 3)
                        y = round(float(_params[i * 2 + 12]), 3)
                        uv = mathutils.Vector((x, y))
                        pe_texmap.uvs.append(uv)

                pe_texmaps.append(pe_texmap)

            elif tex_info.matrix is not None:
                pe_texmap = PETexmap()
                pe_texmap.image_name = tex_info.image_name

                (translation, rotation, box_extents) = (ldraw_node.matrix @ tex_info.matrix).decompose()
                # print(tex_info.camera_origin)

                # this is almost certainly not how it's supposed to be handled, but the end result is the same
                box_extents *= 10

                mirroring = mathutils.Vector((1, 1, 1))
                for dim in range(3):
                    if box_extents[dim] < 0:
                        mirroring[dim] *= -1
                        box_extents[dim] *= -1

                rhs = mathutils.Matrix.LocRotScale(translation, rotation, mirroring)

                matrix = ldraw_node.matrix.inverted() @ rhs
                matrix_inverse = matrix.inverted()

                vertices = [matrix_inverse @ v for v in child_node.vertices]

                if winding == "CW":
                    if vert_count == 3:
                        vertices = [
                            vertices[0],
                            vertices[2],
                            vertices[1],
                        ]
                    elif vert_count == 4:
                        vertices = [
                            vertices[0],
                            vertices[3],
                            vertices[2],
                            vertices[1],
                        ]
                        FaceData.fix_bowties(vertices)

                if not intersect(vertices, box_extents):
                    continue

                ab = vertices[1] - vertices[0]
                bc = vertices[2] - vertices[1]
                face_normal = ab.cross(bc).normalized()

                texture_normal = mathutils.Vector((0, -1, 0))
                dot = face_normal.dot(texture_normal)
                if dot <= 0.001:
                    continue

                # TODO: camera_origin is a camera that is looking at the mesh
                #  only unwrap the faces the camera can actually see, not every face that points toward the camera
                dot = face_normal.dot(tex_info.camera_origin)
                if dot <= 0.001:
                    continue

                for vert in vertices:
                    u = (vert.x - tex_info.point_min.x) / tex_info.point_diff.x
                    v = (vert.z - -tex_info.point_min.y) / -tex_info.point_diff.y
                    uv = mathutils.Vector((u, v))
                    pe_texmap.uvs.append(uv)

                pe_texmaps.append(pe_texmap)

        return pe_texmaps


class PETexInfo:
    def __init__(self):
        self.next_shear = False
        self.matrix = None
        self.matrix_inverse = None
        self.image_name = None

        self.point_min = None  # bottom corner of bounding box
        self.point_max = None  # top corner of bounding box
        self.point_diff = None  # center of bounding box
        self.camera_origin = None  # center of bounding box


class PETexmap:
    def __init__(self):
        self.image_name = None
        self.uvs = []

    def uv_unwrap_face(self, bm, face):
        if not self.uvs:
            return

        uv_layer = bm.loops.layers.uv.verify()
        uvs = {}
        for i, loop in enumerate(face.loops):
            p = loop.vert.co.copy().freeze()
            if p not in uvs:
                uvs[p] = self.uvs[i]
            loop[uv_layer].uv = uvs[p]


def intersect(polygon, box_extents):
    match polygon:
        case [a, b, c]:
            pass
        case [a, b, c, d]:
            return intersect([a, b, c], box_extents) or intersect([c, d, a], box_extents)
        case _:
            raise ValueError

    edges = [b - a, c - b, a - c]
    for i in range(3):
        for j in range(3):
            e = edges[j]
            ex = e.x
            ey = e.y
            ez = e.z

            be = box_extents
            bx = be.x
            by = be.y
            bz = be.z

            if i == 0:
                rhs = mathutils.Vector((0, -ez, ey))
                num = by * abs(ez) + bz * abs(ey)
            elif i == 1:
                rhs = mathutils.Vector((ez, 0, -ex))
                num = bx * abs(ez) + bz * abs(ex)
            elif i == 2:
                rhs = mathutils.Vector((-ey, ex, 0))
                num = bx * abs(ey) + by * abs(ex)

            dot_products = [v.dot(rhs) for v in (a, b, c)]
            miximum = max(-max(dot_products), min(dot_products))
            if miximum > num:
                return False

    for dim in range(3):
        coords = (a[dim], b[dim], c[dim])
        if max(coords) < -box_extents[dim] or min(coords) > box_extents[dim]:
            return False

    normal = edges[0].cross(edges[1])
    abs_normal = mathutils.Vector(abs(v) for v in normal.to_tuple())
    return normal.dot(a) <= abs_normal.dot(box_extents)
