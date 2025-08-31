import mathutils


class PETexInfo:
    def __init__(self, point_min=None, point_max=None, point_diff=None, box_extents=None, matrix=None, matrix_inverse=None, image=None):
        self.point_min = point_min  # bottom corner of bounding box
        self.point_max = point_max  # top corner of bounding box
        self.point_diff = point_diff  # center of bounding box
        self.box_extents = box_extents
        self.matrix = matrix
        self.matrix_inverse = matrix_inverse
        self.image = image

    def clone(self):
        return PETexInfo(self.point_min, self.point_max, self.point_diff, self.box_extents, self.matrix, self.matrix_inverse, self.image)


class PETexmap:
    def __init__(self):
        self.texture = None
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

    @staticmethod
    def build_pe_texmap(ldraw_node, child_node, winding):
        # child_node is a 3 or 4 line
        clean_line = child_node.line
        _params = clean_line.split()[2:]

        vert_count = len(child_node.vertices)

        pe_texmap = None
        for pp in ldraw_node.pe_tex_info:
            p = pp.clone()

            # if we have uv data and a pe_tex_info, otherwise pass
            # # custom minifig head > 3626tex.dat (has no pe_tex) > 3626texpole.dat (has no uv data)
            if len(_params) == 15:  # use uvs provided in file
                pe_texmap = PETexmap()
                pe_texmap.texture = p.image

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

            elif p.matrix_inverse:
                if p.point_min is None: continue
                if p.point_max is None: continue
                if p.point_diff is None: continue
                if p.box_extents is None: continue

                # TODO: calculate uvs
                pe_texmap = PETexmap()
                pe_texmap.texture = p.image

                p.matrix = p.matrix or mathutils.Matrix.Identity(4)
                (translation, rotation, scale) = (ldraw_node.matrix @ p.matrix).decompose()

                p.box_extents = scale
                # if ldraw_node.pe_tex_next_shear:
                #     p.box_extents = scale * mathutils.Vector((p.point_diff.x / 2, 0.25, -p.point_diff.y / 2))

                mirroring = mathutils.Vector((1, 1, 1))
                for dim in range(3):
                    if scale[dim] < 0:
                        mirroring[dim] *= -1
                        p.box_extents[dim] *= -1

                rhs = mathutils.Matrix.LocRotScale(translation, rotation, mirroring)
                p.matrix = ldraw_node.matrix.inverted() @ rhs
                p.matrix_inverse = p.matrix.inverted()

                vertices = [p.matrix_inverse @ v for v in child_node.vertices]
                if winding == 'CW':
                    vertices.reverse()

                if not intersect(vertices, p.box_extents):
                    continue

                ab = vertices[1] - vertices[0]
                bc = vertices[2] - vertices[1]
                face_normal = ab.cross(bc).normalized()
                texture_normal = mathutils.Vector((0, -1, 0))  # "down"
                dot = face_normal.dot(texture_normal)
                if abs(dot) < 0.001: continue
                if dot < 0: continue

                for vert in vertices:
                    u = (vert.x - p.point_min.x) / p.point_diff.x
                    v = (vert.z - -p.point_min.y) / -p.point_diff.y
                    uv = mathutils.Vector((u, v))
                    pe_texmap.uvs.append(uv)

        return pe_texmap


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
            be = box_extents
            if i == 0:
                rhs = mathutils.Vector((0, -e.z, e.y))
                num = be.y * abs(e.z) + be.z * abs(e.y)
            elif i == 1:
                rhs = mathutils.Vector((e.z, 0, -e.x))
                num = be.x * abs(e.z) + be.z * abs(e.x)
            else:
                rhs = mathutils.Vector((-e.y, e.x, 0))
                num = be.x * abs(e.y) + be.y * abs(e.x)

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
