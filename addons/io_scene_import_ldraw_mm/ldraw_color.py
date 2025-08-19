"""Parses and stores a table of color / material definitions. Converts color space."""

import math
import struct
from collections import namedtuple

try:
    from . import helpers
except ImportError as e:
    print(e)
    import traceback
    print(traceback.format_exc())
    import helpers

BlendColor = namedtuple("BlendColor", "r g b")
blend_colors = [
    BlendColor(51, 51, 51),
    BlendColor(0, 51, 178),
    BlendColor(0, 127, 51),
    BlendColor(0, 181, 166),
    BlendColor(204, 0, 0),
    BlendColor(255, 51, 153),
    BlendColor(102, 51, 0),
    BlendColor(153, 153, 153),
    BlendColor(102, 102, 88),
    BlendColor(0, 128, 255),
    BlendColor(51, 255, 102),
    BlendColor(171, 253, 249),
    BlendColor(255, 0, 0),
    BlendColor(255, 176, 204),
    BlendColor(255, 229, 0),
    BlendColor(255, 255, 255),
]


class LDrawColor:
    defaults = {}

    # _*_lp_lc_mod
    use_colour_scheme_choices = (
        ("lgeo", "Realistic colours", "Uses the LGEO colour scheme for realistic colours."),
        ("ldraw", "Original LDraw colours", "Uses the standard LDraw colour scheme (LDConfig.ldr)."),
        ("alt", "Alternate LDraw colours", "Uses the alternate LDraw colour scheme (LDCfgalt.ldr)."),
        ("custom", "Custom LDraw colours", "Uses a user specified LDraw colour file.")
    )

    defaults["use_colour_scheme"] = 0
    use_colour_scheme = defaults["use_colour_scheme"]

    @staticmethod
    def  use_colour_scheme_value():
        return LDrawColor.use_colour_scheme_choices[LDrawColor.use_colour_scheme][0]
    # _*_mod_end

    __colors = {}
    __bad_color = None

    materials = ["chrome", "pearlescent", "rubber", "matte_metallic", "metal"]

    @classmethod
    def reset_caches(cls):
        cls.__colors.clear()
        cls.__bad_color = None

    def __init__(self):
        self.name = None
        self.code = None

        self.color_hex = None
        self.color = None
        self.color_i = None
        self.color_d = None
        self.color_a = None

        self.linear_color = None
        self.linear_color_i = None
        self.linear_color_d = None
        self.linear_color_a = None

        self.edge_color_hex = None
        self.edge_color = None
        self.edge_color_i = None
        self.edge_color_d = None

        self.linear_edge_color = None
        self.linear_edge_color_i = None
        self.linear_edge_color_d = None

        self.alpha = None
        self.luminance = None
        self.material_name = None
        self.material_fabric = None

        self.material_color_hex = None
        self.material_color = None
        self.material_color_i = None

        self.linear_material_color = None
        self.linear_material_color_i = None

        self.material_alpha = None
        self.material_luminance = None
        self.material_fraction = None
        self.material_vfraction = None
        self.material_size = None
        self.material_minsize = None
        self.material_maxsize = None

    @classmethod
    def parse_color(cls, clean_line):
        color = LDrawColor()
        color.parse_color_params(clean_line)
        cls.__colors[color.code] = color
        return color.code

    def parse_color_params(self, clean_line):
        # name CODE x VALUE v EDGE e required
        # 0 !COLOUR Black CODE 0 VALUE #1B2A34 EDGE #2B4354

        # Tags are case-insensitive.
        # https://www.ldraw.org/article/299
        _params = clean_line.split()[2:]
        lparams = clean_line.lower().split()[2:]

        name = _params[0]
        self.name = name

        i = lparams.index("code")
        code = lparams[i + 1]
        self.code = code

        i = lparams.index("value")
        value = lparams[i + 1]
        self.color_hex = value

        rgb = self.__get_rgb_color_value(value, linear=False)
        self.color = rgb
        self.color_i = tuple(round(i * 255) for i in rgb)
        self.color_d = rgb + (1.0,)

        lrgb = self.__get_rgb_color_value(value, linear=True)
        self.linear_color = lrgb
        self.linear_color_i = tuple(round(i * 255) for i in lrgb)
        self.linear_color_d = lrgb + (1.0,)

        i = lparams.index("edge")
        edge = lparams[i + 1]
        self.edge_color_hex = edge

        e_rgb = self.__get_rgb_color_value(edge, linear=False)
        self.edge_color = e_rgb
        self.edge_color_i = tuple(round(i * 255) for i in e_rgb)
        self.edge_color_d = e_rgb + (1.0,)

        le_rgb = self.__get_rgb_color_value(edge, linear=True)
        self.linear_edge_color = le_rgb
        self.linear_edge_color_i = tuple(round(i * 255) for i in le_rgb)
        self.linear_edge_color_d = le_rgb + (1.0,)

        # [ALPHA a] [LUMINANCE l] [ CHROME | PEARLESCENT | RUBBER | MATTE_METALLIC | METAL | MATERIAL <params> ]
        alpha = 255
        if "alpha" in lparams:
            i = lparams.index("alpha")
            alpha = int(lparams[i + 1])
        self.alpha = alpha / 255

        self.color_a = rgb + (self.alpha,)
        self.linear_color_a = lrgb + (self.alpha,)

        luminance = 0
        if "luminance" in lparams:
            i = lparams.index("luminance")
            luminance = int(lparams[i + 1])
        self.luminance = luminance

        material_name = None
        for _material in self.materials:
            if _material in lparams:
                material_name = _material
                break
        self.material_name = material_name

        # MATERIAL SPECKLE VALUE #898788 FRACTION 0.4               MINSIZE 1    MAXSIZE 3
        # MATERIAL GLITTER VALUE #FFFFFF FRACTION 0.8 VFRACTION 0.6 MINSIZE 0.02 MAXSIZE 0.1
        # MATERIAL FABRIC [VELVET | CANVAS | STRING | FUR]
        if "material" in lparams:
            i = lparams.index("material")
            material_parts = lparams[i:]

            material_name = material_parts[1]
            self.material_name = material_name

            if "fabric" in material_name:
                i = lparams.index("fabric")
                material_fabric = material_parts[i + 1]
            self.material_fabric = material_fabric
            
            material_value = "000000"
            if "value" in material_parts:
                i = lparams.index("value")
                material_value = lparams[i + 1]
            self.material_color_hex = material_value

            material_rgb = self.__get_rgb_color_value(material_value, linear=False)
            self.material_color = material_rgb
            self.material_color_i = tuple(round(i * 255) for i in material_rgb)

            lmaterial_rgb = self.__get_rgb_color_value(material_value, linear=True)
            self.linear_material_color = lmaterial_rgb
            self.linear_material_color_i = tuple(round(i * 255) for i in lmaterial_rgb)

            material_alpha = 255
            if "alpha" in material_parts:
                i = material_parts.index("alpha")
                material_alpha = int(material_parts[i + 1])
            self.material_alpha = material_alpha / 255

            material_luminance = 0
            if "luminance" in material_parts:
                i = material_parts.index("luminance")
                material_luminance = int(material_parts[i + 1])
            self.material_luminance = material_luminance

            material_minsize = 0.0
            material_maxsize = 0.0
            if "size" in material_parts:
                i = material_parts.index("size")
                material_minsize = float(material_parts[i + 1])
                material_maxsize = float(material_parts[i + 1])

            if "minsize" in material_parts:
                i = material_parts.index("minsize")
                material_minsize = float(material_parts[i + 1])

            if "maxsize" in material_parts:
                i = material_parts.index("maxsize")
                material_maxsize = float(material_parts[i + 1])
            self.material_minsize = material_minsize
            self.material_maxsize = material_maxsize

            material_fraction = 0.0
            if "fraction" in material_parts:
                i = material_parts.index("fraction")
                material_fraction = float(material_parts[i + 1])
            self.material_fraction = material_fraction

            material_vfraction = 0.0
            if "vfraction" in material_parts:
                i = material_parts.index("vfraction")
                material_vfraction = float(material_parts[i + 1])
            self.material_vfraction = material_vfraction

    # get colors loaded from ldconfig if they exist
    # otherwise convert the color code to a usable color and return that
    # if all that fails, create and send bad_color
    @classmethod
    def get_color(cls, color_code):
        if color_code in cls.__colors:
            return cls.__colors[color_code]

        hex_digits = None

        if hex_digits is None:
            hex_digits = cls.parse_blended_color(color_code)

        if hex_digits is None:
            hex_digits = cls.parse_int_color(color_code)

        if hex_digits is None:
            hex_digits = cls.__extract_hex_digits(color_code)

        if hex_digits is not None:
            try:
                # FFFFFF == 6 means no alpha
                # FFFFFFFF == 8 means alpha
                # 1009022 == #f657e -> ValueError
                alpha = ''
                if len(hex_digits) == 8:
                    alpha_val = struct.unpack("B", bytes.fromhex(hex_digits[6:8]))[0]
                    alpha = f"ALPHA {alpha_val}"

                clean_line = f"0 !COLOUR {color_code} CODE {color_code} VALUE #{hex_digits} EDGE #333333 {alpha}"
                color_code = cls.parse_color(clean_line)
                return cls.__colors[color_code]
            except Exception as e:
                print(e)
                import traceback
                print(traceback.format_exc())

        print(f"Bad color code: {color_code}")
        color_code = '99999'
        if cls.__bad_color is None:
            clean_line = f"0 !COLOUR Bad_Color CODE {color_code} VALUE #FF0000 EDGE #00FF00"
            color_code = cls.parse_color(clean_line)
            cls.__bad_color = cls.__colors[color_code]

        return cls.__colors[color_code]

    # n1 = (nb - 256) / 16
    # n2 = (nb - 256) mod 16
    # n1 is the index of input colour 1
    # nb is the index of the blended color
    # n2 is the index of input colour 2
    # Rb = (R1 + R2) / 2
    # Gb = (G1 + G2) / 2
    # Bb = (B1 + B2) / 2
    # Rb, Gb, Bb are the red, green, and blue components of the blended colour
    # R1, G1, B1 are the red, green, and blue components of the first input colour
    # R2, G2, B2 are the red, green, and blue components of the second input colour.
    @classmethod
    def parse_blended_color(cls, color_code):
        hex_digits = None

        try:
            # https://www.ldraw.org/article/218.html#blendcolour

            # blended_color_code
            nb = int(color_code)

            n1 = (nb - 256) // 16
            n2 = (nb - 256) % 16

            # https://forums.ldraw.org/thread-15259-post-15261.html#pid15261
            # A = (nb - 256) >> 4
            # B = (nb - 256) & 0x0F

            c1 = blend_colors[n1]
            c2 = blend_colors[n2]

            # fc1 = Color(c1.r / 255, c1.g / 255, c1.b / 255)
            # fc2 = Color(c2.r / 255, c2.g / 255, c2.b / 255)
            #
            # a = hex(c1.r)
            # b = hex(c1.g)
            # c = hex(c1.b)
            #
            # aa = hex(c2.r)
            # bb = hex(c2.g)
            # cc = hex(c2.b)
            #
            # # https://stackoverflow.com/a/2269841
            # hc1 = f"0x{'{0:#0{1}x}'.format(c1.r, 4)[2:]}{'{0:#0{1}x}'.format(c1.g, 4)[2:]}{'{0:#0{1}x}'.format(c1.b, 4)[2:]}"
            # hc2 = f"0x{'{0:#0{1}x}'.format(c2.r, 4)[2:]}{'{0:#0{1}x}'.format(c2.g, 4)[2:]}{'{0:#0{1}x}'.format(c2.b, 4)[2:]}"

            r1 = c1.r
            r2 = c2.r

            g1 = c1.g
            g2 = c2.g

            b1 = c1.b
            b2 = c2.b

            rb = (r1 + r2) // 2
            gb = (g1 + g2) // 2
            bb = (b1 + b2) // 2

            bcolor = BlendColor(rb, gb, bb)
            # bicolor = Color(rb / 255, gb / 255, bb / 255)
            hbcolor = f"0x{hex(bcolor.r)[2:]}{hex(bcolor.g)[2:]}{hex(bcolor.b)[2:]}"
            hex_digits = cls.__extract_hex_digits(hbcolor)
        except ValueError as e:
            print(e)
            import traceback
            print(traceback.format_exc())
            # color code is not an int
        except IndexError as e:
            print(e)
            import traceback
            print(traceback.format_exc())
            # color code indices are not in the colors list
            print(color_code)
            from inspect import currentframe, getframeinfo
            frameinfo = getframeinfo(currentframe())
            print(frameinfo.filename, frameinfo.lineno)

        return hex_digits

    # nb is the index of the blended colour
    # n1 is the index of the first input colour
    # n2 is the index of the second input colour
    @classmethod
    def get_blended_color_code(cls, n1, n2):
        nb = n1 * 16 + n2 + 256
        return nb

    @classmethod
    def parse_int_color(cls, color_code):
        hex_digits = None

        # 10220 - Volkswagen T1 Camper Van.mpd -> 97122.dat uses an int color code 4294967295 which is 0xffffffff in hex
        try:
            icolor_code = int(color_code)
            hicolor_code = hex(icolor_code)
            hex_digits = cls.__extract_hex_digits(hicolor_code)
        except ValueError as e:
            print(e)
            import traceback
            print(traceback.format_exc())

        return hex_digits

    # _*_lp_lc_mod
    @classmethod
    def __overwrite_color(cls, code, color):
        cls.__colors[str(code)].color = color

    @classmethod
    def set_lgeo_colors(cls, lgeo_colors):
        if len(lgeo_colors):
            for code, color in lgeo_colors.items():
                cls.__overwrite_color(code,(color[0] / 255, color[1] / 255, color[2] / 255))
        else:
            cls.__overwrite_color(  0, ( 33 / 255,  33 / 255,  33 / 255))
            cls.__overwrite_color(  1, ( 13 / 255, 105 / 255, 171 / 255))
            cls.__overwrite_color(  2, ( 40 / 255, 127 / 255,  70 / 255))
            cls.__overwrite_color(  3, (  0 / 255, 143 / 255, 155 / 255))
            cls.__overwrite_color(  4, (196 / 255,  40 / 255,  27 / 255))
            cls.__overwrite_color(  5, (205 / 255,  98 / 255, 152 / 255))
            cls.__overwrite_color(  6, ( 98 / 255,  71 / 255,  50 / 255))
            cls.__overwrite_color(  7, (161 / 255, 165 / 255, 162 / 255))
            cls.__overwrite_color(  8, (109 / 255, 110 / 255, 108 / 255))
            cls.__overwrite_color(  9, (180 / 255, 210 / 255, 227 / 255))
            cls.__overwrite_color( 10, ( 75 / 255, 151 / 255,  74 / 255))
            cls.__overwrite_color( 11, ( 85 / 255, 165 / 255, 175 / 255))
            cls.__overwrite_color( 12, (242 / 255, 112 / 255,  94 / 255))
            cls.__overwrite_color( 13, (252 / 255, 151 / 255, 172 / 255))
            cls.__overwrite_color( 14, (245 / 255, 205 / 255,  47 / 255))
            cls.__overwrite_color( 15, (242 / 255, 243 / 255, 242 / 255))
            cls.__overwrite_color( 17, (194 / 255, 218 / 255, 184 / 255))
            cls.__overwrite_color( 18, (249 / 255, 233 / 255, 153 / 255))
            cls.__overwrite_color( 19, (215 / 255, 197 / 255, 153 / 255))
            cls.__overwrite_color( 20, (193 / 255, 202 / 255, 222 / 255))
            cls.__overwrite_color( 21, (224 / 255, 255 / 255, 176 / 255))
            cls.__overwrite_color( 22, (107 / 255,  50 / 255, 123 / 255))
            cls.__overwrite_color( 23, ( 35 / 255,  71 / 255, 139 / 255))
            cls.__overwrite_color( 25, (218 / 255, 133 / 255,  64 / 255))
            cls.__overwrite_color( 26, (146 / 255,  57 / 255, 120 / 255))
            cls.__overwrite_color( 27, (164 / 255, 189 / 255,  70 / 255))
            cls.__overwrite_color( 28, (149 / 255, 138 / 255, 115 / 255))
            cls.__overwrite_color( 29, (228 / 255, 173 / 255, 200 / 255))
            cls.__overwrite_color( 30, (172 / 255, 120 / 255, 186 / 255))
            cls.__overwrite_color( 31, (225 / 255, 213 / 255, 237 / 255))
            cls.__overwrite_color( 32, (  0 / 255,  20 / 255,  20 / 255))
            cls.__overwrite_color( 33, (123 / 255, 182 / 255, 232 / 255))
            cls.__overwrite_color( 34, (132 / 255, 182 / 255, 141 / 255))
            cls.__overwrite_color( 35, (217 / 255, 228 / 255, 167 / 255))
            cls.__overwrite_color( 36, (205 / 255,  84 / 255,  75 / 255))
            cls.__overwrite_color( 37, (228 / 255, 173 / 255, 200 / 255))
            cls.__overwrite_color( 38, (255 / 255,  43 / 255,   0 / 225))
            cls.__overwrite_color( 40, (166 / 255, 145 / 255, 130 / 255))
            cls.__overwrite_color( 41, (170 / 255, 229 / 255, 255 / 255))
            cls.__overwrite_color( 42, (198 / 255, 255 / 255,   0 / 255))
            cls.__overwrite_color( 43, (193 / 255, 223 / 255, 240 / 255))
            cls.__overwrite_color( 44, (150 / 255, 112 / 255, 159 / 255))
            cls.__overwrite_color( 46, (247 / 255, 241 / 255, 141 / 255))
            cls.__overwrite_color( 47, (252 / 255, 252 / 255, 252 / 255))
            cls.__overwrite_color( 52, (156 / 255, 149 / 255, 199 / 255))
            cls.__overwrite_color( 54, (255 / 255, 246 / 255, 123 / 255))
            cls.__overwrite_color( 57, (226 / 255, 176 / 255,  96 / 255))
            cls.__overwrite_color( 65, (236 / 255, 201 / 255,  53 / 255))
            cls.__overwrite_color( 66, (202 / 255, 176 / 255,   0 / 255))
            cls.__overwrite_color( 67, (255 / 255, 255 / 255, 255 / 255))
            cls.__overwrite_color( 68, (243 / 255, 207 / 255, 155 / 255))
            cls.__overwrite_color( 69, (142 / 255,  66 / 255, 133 / 255))
            cls.__overwrite_color( 70, (105 / 255,  64 / 255,  39 / 255))
            cls.__overwrite_color( 71, (163 / 255, 162 / 255, 164 / 255))
            cls.__overwrite_color( 72, ( 99 / 255,  95 / 255,  97 / 255))
            cls.__overwrite_color( 73, (110 / 255, 153 / 255, 201 / 255))
            cls.__overwrite_color( 74, (161 / 255, 196 / 255, 139 / 255))
            cls.__overwrite_color( 77, (220 / 255, 144 / 255, 149 / 255))
            cls.__overwrite_color( 78, (246 / 255, 215 / 255, 179 / 255))
            cls.__overwrite_color( 79, (255 / 255, 255 / 255, 255 / 255))
            cls.__overwrite_color( 80, (140 / 255, 140 / 255, 140 / 255))
            cls.__overwrite_color( 82, (219 / 255, 172 / 255,  52 / 255))
            cls.__overwrite_color( 84, (170 / 255, 125 / 255,  85 / 255))
            cls.__overwrite_color( 85, ( 52 / 255,  43 / 255, 117 / 255))
            cls.__overwrite_color( 86, (124 / 255,  92 / 255,  69 / 255))
            cls.__overwrite_color( 89, (155 / 255, 178 / 255, 239 / 255))
            cls.__overwrite_color( 92, (204 / 255, 142 / 255, 104 / 255))
            cls.__overwrite_color(100, (238 / 255, 196 / 255, 182 / 255))
            cls.__overwrite_color(115, (199 / 255, 210 / 255,  60 / 255))
            cls.__overwrite_color(134, (174 / 255, 122 / 255,  89 / 255))
            cls.__overwrite_color(135, (171 / 255, 173 / 255, 172 / 255))
            cls.__overwrite_color(137, (106 / 255, 122 / 255, 150 / 255))
            cls.__overwrite_color(142, (220 / 255, 188 / 255, 129 / 255))
            cls.__overwrite_color(148, ( 62 / 255,  60 / 255,  57 / 255))
            cls.__overwrite_color(151, ( 14 / 255,  94 / 255,  77 / 255))
            cls.__overwrite_color(179, (160 / 255, 160 / 255, 160 / 255))
            cls.__overwrite_color(183, (242 / 255, 243 / 255, 242 / 255))
            cls.__overwrite_color(191, (248 / 255, 187 / 255,  61 / 255))
            cls.__overwrite_color(212, (159 / 255, 195 / 255, 233 / 255))
            cls.__overwrite_color(216, (143 / 255,  76 / 255,  42 / 255))
            cls.__overwrite_color(226, (253 / 255, 234 / 255, 140 / 255))
            cls.__overwrite_color(232, (125 / 255, 187 / 255, 221 / 255))
            cls.__overwrite_color(256, ( 33 / 255,  33 / 255,  33 / 255))
            cls.__overwrite_color(272, ( 32 / 255,  58 / 255,  86 / 255))
            cls.__overwrite_color(273, ( 13 / 255, 105 / 255, 171 / 255))
            cls.__overwrite_color(288, ( 39 / 255,  70 / 255,  44 / 255))
            cls.__overwrite_color(294, (189 / 255, 198 / 255, 173 / 255))
            cls.__overwrite_color(297, (170 / 255, 127 / 255,  46 / 255))
            cls.__overwrite_color(308, ( 53 / 255,  33 / 255,   0 / 255))
            cls.__overwrite_color(313, (171 / 255, 217 / 255, 255 / 255))
            cls.__overwrite_color(320, (123 / 255,  46 / 255,  47 / 255))
            cls.__overwrite_color(321, ( 70 / 255, 155 / 255, 195 / 255))
            cls.__overwrite_color(322, (104 / 255, 195 / 255, 226 / 255))
            cls.__overwrite_color(323, (211 / 255, 242 / 255, 234 / 255))
            cls.__overwrite_color(324, (196 / 255,   0 / 255,  38 / 255))
            cls.__overwrite_color(326, (226 / 255, 249 / 255, 154 / 255))
            cls.__overwrite_color(330, (119 / 255, 119 / 255,  78 / 255))
            cls.__overwrite_color(334, (187 / 255, 165 / 255,  61 / 255))
            cls.__overwrite_color(335, (149 / 255, 121 / 255, 118 / 255))
            cls.__overwrite_color(366, (209 / 255, 131 / 255,   4 / 255))
            cls.__overwrite_color(373, (135 / 255, 124 / 255, 144 / 255))
            cls.__overwrite_color(375, (193 / 255, 194 / 255, 193 / 255))
            cls.__overwrite_color(378, (120 / 255, 144 / 255, 129 / 255))
            cls.__overwrite_color(379, ( 94 / 255, 116 / 255, 140 / 255))
            cls.__overwrite_color(383, (224 / 255, 224 / 255, 224 / 255))
            cls.__overwrite_color(406, (  0 / 255,  29 / 255, 104 / 255))
            cls.__overwrite_color(449, (129 / 255,   0 / 255, 123 / 255))
            cls.__overwrite_color(450, (203 / 255, 132 / 255,  66 / 255))
            cls.__overwrite_color(462, (226 / 255, 155 / 255,  63 / 255))
            cls.__overwrite_color(484, (160 / 255,  95 / 255,  52 / 255))
            cls.__overwrite_color(490, (215 / 255, 240 / 255,   0 / 255))
            cls.__overwrite_color(493, (101 / 255, 103 / 255,  97 / 255))
            cls.__overwrite_color(494, (208 / 255, 208 / 255, 208 / 255))
            cls.__overwrite_color(496, (163 / 255, 162 / 255, 164 / 255))
            cls.__overwrite_color(503, (199 / 255, 193 / 255, 183 / 255))
            cls.__overwrite_color(504, (137 / 255, 135 / 255, 136 / 255))
            cls.__overwrite_color(511, (250 / 255, 250 / 255, 250 / 255))
    # _*_mod_end

    @classmethod
    def __get_rgb_color_value(cls, value, linear=True):
        hex_digits = cls.__extract_hex_digits(value)[0:6]  # skip alpha value if hex_digits length == 8
        if linear:
            return cls.__hex_digits_to_linear_rgb(hex_digits)
        else:
            return cls.__hex_digits_to_srgb(hex_digits)

    @classmethod
    def __extract_hex_digits(cls, value):
        # the normal format of color values
        if value.startswith("#"):  # "#efefefff"
            return value[1:]

        # some color codes in 973psr.dat are just hex values for the desired color, such as 0x24C4C45
        if value.lower().startswith("0x2"):  # "0x24C4C45ff"
            return value[3:]

        # some color codes are ints that need to be converted to hex -> hex(intval) == "0xFFFFFFFF"
        if value.lower().startswith("0x"):  # "0xffffffff"
            return value[2:]

        return None

    @classmethod
    def __hex_digits_to_linear_rgb(cls, hex_digits):
        srgb = cls.__hex_digits_to_srgb(hex_digits)
        linear_rgb = cls.__srgb_to_linear_rgb(srgb)
        return linear_rgb[0], linear_rgb[1], linear_rgb[2]

    @classmethod
    def __hex_digits_to_srgb(cls, hex_digits):
        # String is "RRGGBB" format
        int_tuple = cls.__hex_to_rgb(hex_digits)
        return cls.__rgb_to_srgb(int_tuple)

    @staticmethod
    def __hex_to_rgb(hex_digits):
        return struct.unpack("BBB", bytes.fromhex(hex_digits))

    @staticmethod
    def __rgb_to_srgb(ints):
        srgb = tuple([val / 255 for val in ints])
        return srgb

    @classmethod
    def __srgb_to_linear_rgb(cls, srgb_color):
        (sr, sg, sb) = srgb_color
        r = cls.__srgb_to_rgb_value(sr)
        g = cls.__srgb_to_rgb_value(sg)
        b = cls.__srgb_to_rgb_value(sb)
        return r, g, b

    @staticmethod
    def __srgb_to_rgb_value(value):
        # See https://en.wikipedia.org/wiki/SRGB#The_reverse_transformation
        if value < 0.04045:
            return value / 12.92
        return ((value + 0.055) / 1.055) ** 2.4

    @staticmethod
    def lighten_rgba(color, scale):
        # Moves the linear RGB values closer to white
        # scale = 0 means full white
        # scale = 1 means color stays same
        color = (
            (1.0 - color[0]) * scale,
            (1.0 - color[1]) * scale,
            (1.0 - color[2]) * scale,
            color[3]
        )
        return (
            helpers.clamp(1.0 - color[0], 0.0, 1.0),
            helpers.clamp(1.0 - color[1], 0.0, 1.0),
            helpers.clamp(1.0 - color[2], 0.0, 1.0),
            color[3]
        )

    # wp-content/plugins/woocommerce/includes/wc-formatting-functions.php
    # line 779
    @staticmethod
    def __is_dark(color):
        r = color[0]
        g = color[1]
        b = color[2]

        # Measure the perceived brightness of color
        brightness = math.sqrt(0.299 * r * r + 0.587 * g * g + 0.114 * b * b)

        # Dark colors have white lines
        return brightness < 0.02


# https://stackoverflow.com/a/74601731
def print_colored(string, r, g, b):
    print(f"\033[38;2;{r};{g};{b}m{string}\033[0m")


if __name__ == "__main__":
    print(LDrawColor.get_color('#efefef').color_a)
    print(LDrawColor.get_color('#efefef55').color_a)
    print(LDrawColor.get_color("0x2062E92").color_a)
    print(LDrawColor.get_color("0x2062E9255").color_a)
    print(LDrawColor.get_color('4294967295').color_a)
    print(LDrawColor.get_color('#f657e').color_a)

    # taken from Datsville
    print(LDrawColor.get_color("0x2F05C00").color_a)
    print(LDrawColor.get_color("0x2F03C00").color_a)
    print(LDrawColor.get_color('258').color_a)  # blended color code
    print(LDrawColor.get_color('382').color_a)  # blended color code
    print(LDrawColor.get_color('487').color_a)  # blended color code

    string = '258'
    c = LDrawColor.get_color(string).color_i
    print_colored(string, c[0], c[1], c[2])

    string = '382'
    c = LDrawColor.get_color(string).color_i
    print_colored(string, c[0], c[1], c[2])

    string = '487'
    c = LDrawColor.get_color(string).color_i
    print_colored(string, c[0], c[1], c[2])
