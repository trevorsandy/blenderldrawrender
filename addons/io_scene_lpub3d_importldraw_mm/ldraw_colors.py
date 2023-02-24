"""Parses and stores a table of color / material definitions. Converts color space."""

import math
import struct

try:
    from . import helpers
except ImportError as e:
    import helpers


class LDrawColor:
    defaults = {}

    defaults['use_colour_scheme'] = 'lgeo'
    use_colour_scheme = defaults['use_colour_scheme']

    __colors = {}
    __bad_color = None

    @classmethod
    def reset_caches(cls):
        cls.__colors = {}
        cls.__bad_color = None

    def __init__(self):
        self.name = None
        self.code = None
        self.color = None
        self.color_d = None
        self.color_a = None
        self.edge_color = None
        self.edge_color_d = None
        self.alpha = None
        self.luminance = None
        self.material_name = None
        self.material_color = None
        self.material_alpha = None
        self.material_luminance = None
        self.material_fraction = None
        self.material_vfraction = None
        self.material_size = None
        self.material_minsize = None
        self.material_maxsize = None

    @classmethod
    def parse_color(cls, _params):
        color = LDrawColor()
        color.parse_color_params(_params)
        cls.__colors[color.code] = color
        return color.code

    # get colors loaded from ldconfig if they exist
    # otherwise convert the color code to a usable color and return that
    # if all that fails, create and send bad_color
    @classmethod
    def get_color(cls, color_code):
        if color_code in cls.__colors:
            return cls.__colors[color_code]

        hex_digits = cls.__extract_hex_digits(color_code)

        if hex_digits is None:
            # 10220 - Volkswagen T1 Camper Van.mpd -> 97122.dat uses an int color code 4294967295 which is 0xffffffff in hex
            try:
                hex_digits = cls.__extract_hex_digits(hex(int(color_code)))
            except ValueError as e:
                print(e)

        if hex_digits is not None:
            alpha = ''
            # FFFFFF == 6 means no alpha
            # FFFFFFFF == 8 means alpha
            # 1009022 == #f657e -> ValueError
            if len(hex_digits) == 8:
                alpha_val = struct.unpack("B", bytes.fromhex(hex_digits[6:8]))[0]
                alpha = f"ALPHA {alpha_val}"

            clean_line = f"0 !COLOUR {color_code} CODE {color_code} VALUE #{hex_digits} EDGE #333333 {alpha}"
            _params = helpers.get_params(clean_line, "0 !COLOUR ")
            try:
                color_code = cls.parse_color(_params)
                return cls.__colors[color_code]
            except ValueError as e:
                print(e)

        if cls.__bad_color is None:
            clean_line = f"0 !COLOUR Bad_Color CODE {color_code} VALUE #FF0000 EDGE #00FF00"
            _params = helpers.get_params(clean_line, "0 !COLOUR ")
            color_code = cls.parse_color(_params)
            cls.__bad_color = cls.__colors[color_code]

        print(f"Bad color code: {color_code}")
        return cls.__colors[cls.__bad_color.code]

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


    @classmethod
    def lighten_rgba(cls, color, scale):
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

    def parse_color_params(self, _params, linear=True):
        # name CODE x VALUE v EDGE e required
        # 0 !COLOUR Black CODE 0 VALUE #1B2A34 EDGE #2B4354

        name = _params[0]
        self.name = name

        # Tags are case-insensitive.
        # https://www.ldraw.org/article/299
        lparams = [x.lower() for x in _params]

        i = lparams.index("code")
        code = lparams[i + 1]
        self.code = code

        i = lparams.index("value")
        value = lparams[i + 1]
        rgb = self.__get_rgb_color_value(value, linear)
        self.color = rgb
        self.color_d = rgb + (1.0,)

        i = lparams.index("edge")
        edge = lparams[i + 1]
        e_rgb = self.__get_rgb_color_value(edge, linear)
        self.edge_color = e_rgb
        self.edge_color_d = e_rgb + (1.0,)

        # [ALPHA a] [LUMINANCE l] [ CHROME | PEARLESCENT | RUBBER | MATTE_METALLIC | METAL | MATERIAL <params> ]
        alpha = 255
        if "alpha" in lparams:
            i = lparams.index("alpha")
            alpha = int(lparams[i + 1])
        self.alpha = alpha / 255
        self.color_a = rgb + (self.alpha,)

        luminance = 0
        if "luminance" in lparams:
            i = lparams.index("luminance")
            luminance = int(lparams[i + 1])
        self.luminance = luminance

        material_name = None
        for _material in ["chrome", "pearlescent", "rubber", "matte_metallic", "metal"]:
            if _material in lparams:
                material_name = _material
                break
        self.material_name = material_name

        # MATERIAL SPECKLE VALUE #898788 FRACTION 0.4               MINSIZE 1    MAXSIZE 3
        # MATERIAL GLITTER VALUE #FFFFFF FRACTION 0.8 VFRACTION 0.6 MINSIZE 0.02 MAXSIZE 0.1
        if "material" in lparams:
            i = lparams.index("material")
            material_parts = lparams[i:]

            material_name = material_parts[1]
            self.material_name = material_name

            i = lparams.index("value")
            material_value = lparams[i + 1]
            material_rgba = self.__get_rgb_color_value(material_value, linear)
            self.material_color = material_rgba

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

    @staticmethod
    def __is_int(s):
        try:
            int(s)
            return True
        except ValueError:
            return False

    @classmethod
    def __get_rgb_color_value(cls, value, linear=True):
        hex_digits = cls.__extract_hex_digits(value)[0:6]
        if linear:
            return cls.__hex_digits_to_linear_rgb(hex_digits)
        else:
            return cls.__hex_digits_to_srgb(hex_digits)

    @classmethod
    def __extract_hex_digits(cls, value):
        # the normal format of color values
        if value.startswith('#'):  # '#efefefff'
            return value[1:]

        # some color codes in 973psr.dat are just hex values for the desired color, such as 0x24C4C45
        if value.lower().startswith('0x2'):  # '0x24C4C45ff'
            return value[3:]

        # some color codes are ints that need to be converted to hex -> hex(intval) == '0xFFFFFFFF'
        if value.lower().startswith('0x'):  # '0xffffffff'
            return value[2:]

        return None

    @classmethod
    def __hex_digits_to_linear_rgb(cls, hex_digits):
        srgb = cls.__hex_digits_to_srgb(hex_digits)
        linear_rgb = cls.__srgb_to_linear_rgb(srgb)
        return linear_rgb[0], linear_rgb[1], linear_rgb[2]

    @staticmethod
    def __hex_to_rgb(hex_digits):
        return struct.unpack("BBB", bytes.fromhex(hex_digits))

    @staticmethod
    def __rgb_to_srgb(ints):
        srgb = tuple([val / 255 for val in ints])
        return srgb

    @classmethod
    def __hex_digits_to_srgb(cls, hex_digits):
        # String is "RRGGBB" format
        int_tuple = cls.__hex_to_rgb(hex_digits)
        return cls.__rgb_to_srgb(int_tuple)

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


if __name__ == "__main__":
    print(LDrawColor.get_color('#efefef').color_a)
    print(LDrawColor.get_color('#efefef55').color_a)
    print(LDrawColor.get_color("0x2062E92").color_a)
    print(LDrawColor.get_color("0x2062E9255").color_a)
    print(LDrawColor.get_color('4294967295').color_a)
    print(LDrawColor.get_color('#f657e').color_a)
