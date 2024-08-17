import mathutils
import math


class LDrawLight:
    """Data about a light"""

    def __init__(self):
        self.hidden           = False
        self.name             = 'Light'
        self.type             = 'POINT'
        self.shape            = 'SQUARE'
        self.factor_a         = 0.0
        self.factor_b         = 0.0
        self.size             = 0.25
        self.exponent         = 10
        self.specular         = 1.0
        self.spot_size        = 75        # degrees
        self.spot_blend       = 0.150
        self.cutoff_distance  = 40
        self.use_cutoff       = False
        self.use_shadow       = True
        self.color            = mathutils.Vector((1.0, 1.0, 1.0))
        self.position         = mathutils.Vector((0.0, 0.0, 0.0))
        self.target_position  = mathutils.Vector((1.0, 0.0, 0.0))
        self.dummy            = mathutils.Vector((0.0, 1.0, 0.0)) # up_vector placeholder

    def matrix44ToEulerAngles(self, matrix):
        """Convert LeoCAD ROTATION matrix to target_position euler angles"""

        sin_pitch = -matrix[0][2]
        cos_pitch = math.sqrt(1 - sin_pitch*sin_pitch)

        if (math.fabs(cos_pitch) > 0.0005):
            sin_roll = matrix[1][2] / cos_pitch
            cos_roll = matrix[2][2] / cos_pitch
            sin_yaw = matrix[0][1] / cos_pitch
            cos_yaw = matrix[0][0] / cos_pitch
        else:
            sin_roll = -matrix[2][1]
            cos_roll = matrix[1][1]
            sin_yaw = 0.0
            cos_yaw = 1.0

        euler_angles = mathutils.Vector((math.atan2(sin_roll, cos_roll), math.atan2(sin_pitch, cos_pitch), math.atan2(sin_yaw, cos_yaw)))

        if (euler_angles[0] < 0): euler_angles[0] += math.tau
        if (euler_angles[1] < 0): euler_angles[1] += math.tau
        if (euler_angles[2] < 0): euler_angles[2] += math.tau

        angles_in_degrees = mathutils.Vector((math.degrees(euler_angles[0]), math.degrees(euler_angles[1]), math.degrees(euler_angles[2])))

        return angles_in_degrees