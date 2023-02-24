import mathutils

class LDrawLight:
    """Data about a light"""

    def __init__(self):
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
        self.color            = mathutils.Vector((1.0, 1.0, 1.0))
        self.position         = mathutils.Vector((0.0, 0.0, 0.0))
        self.target_position  = mathutils.Vector((1.0, 0.0, 0.0))
        self.dummy            = mathutils.Vector((0.0, 1.0, 0.0)) # up_vector placeholder
