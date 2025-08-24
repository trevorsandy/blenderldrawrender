import mathutils
import math


class LDrawLight:
    """Data about a light"""

    def __init__(self):
        self.hidden           = False
        self.name             = 'Light'
        self.type             = 'POINT'
        self.shape            = 'SQUARE'
        self.sun_angle        = 0.0
        self.shadow_radius    = 0.0
        self.spot_blend       = 0.0
        self.area_size_x      = 0.0
        self.area_size_y      = 0.0
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
        self.up_vector        = mathutils.Vector((0.0, 1.0, 0.0))
        self.rotation         = None

