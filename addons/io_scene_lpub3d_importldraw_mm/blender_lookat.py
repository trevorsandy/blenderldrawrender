import mathutils

def look_at(obj, target_location, up_vector):

    # back vector is a vector pointing from the target to the object
    back = obj.location - target_location
    back = back.normalized()

    # If our back and up vectors are very close to pointing the same way (or opposite),
    # choose a different up_vector
    if abs(back.dot(up_vector)) > 0.9999:
        up_vector = mathutils.Vector((0.0, 0.0, 1.0))
        if abs(back.dot(up_vector)) > 0.9999:
            up_vector = mathutils.Vector((1.0, 0.0, 0.0))

    right = up_vector.cross(back)
    right = right.normalized()

    up = back.cross(right)
    up = up.normalized()

    obj.matrix_world = mathutils.Matrix((
        [right[0], up[0], back[0], obj.location[0]],
        [right[1], up[1], back[1], obj.location[1]],
        [right[2], up[2], back[2], obj.location[2]],
        [0.0, 0.0, 0.0, 1.0],
    ))

def get_vector():

    return mathutils.Vector((4.076245307922363, 1.0054539442062378, 5.903861999511719))
