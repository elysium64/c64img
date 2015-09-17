"""
C64lib module holds all information needed to provide abstraction to low level
graphic related operation and conbertion in Python.
"""
import os
from collections import Counter
import logging

from PIL import Image
from PIL.ImageDraw import Draw

from c64img.path import get_modified_fname
from c64img.logger import Logger

# Palettes are organized with original C64 order:
# black, white, red, magenta, purple, green, dark blue, yellow,
# orange, brown, pink, dark gray, gray, light green, light blue, light gray

(BLACK, WHITE, RED, MAGENTA, PURPLE, GREEN, DARK_BLUE, YELLOW,
 ORANGE, BROWN, PINK, DARK_GRAY, GRAY, LIGHT_GREEN, LIGHT_BLUE,
 LIGHT_GRAY) = range(16)

PALETTES = {'Vice': ((0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF),
                     (0x9a, 0x53, 0x48), (0x8c, 0xc9, 0xd1),
                     (0x9b, 0x5a, 0xbb), (0x7b, 0xb7, 0x54),
                     (0x51, 0x42, 0xb1), (0xd8, 0xe2, 0x84),
                     (0xa0, 0x72, 0x35), (0x70, 0x5b, 0x00),
                     (0xc6, 0x89, 0x80), (0x69, 0x69, 0x69),
                     (0x92, 0x92, 0x92), (0xb9, 0xee, 0x99),
                     (0x8e, 0x82, 0xe1), (0xb9, 0xb9, 0xb9)),
            'Timanthes': ((0, 0, 0), (213, 213, 213),
                          (114, 53, 44), (101, 159, 166),
                          (115, 58, 145), (86, 141, 53),
                          (46, 35, 125), (174, 183, 94),
                          (119, 79, 30), (75, 60, 0),
                          (156, 99, 90), (71, 71, 71),
                          (107, 107, 107), (143, 194, 113),
                          (103, 93, 182), (143, 143, 143)),
            'Unknown': ((0x00, 0x00, 0x00), (0xff, 0xff, 0xff),
                        (0x88, 0x00, 0x00), (0xaa, 0xff, 0xee),
                        (0xcc, 0x44, 0xcc), (0x00, 0xcc, 0x55),
                        (0x00, 0x00, 0xaa), (0xee, 0xee, 0x77),
                        (0xdd, 0x88, 0x55), (0x66, 0x44, 0x00),
                        (0xff, 0x77, 0x77), (0x33, 0x33, 0x33),
                        (0x77, 0x77, 0x77), (0xaa, 0xff, 0x66),
                        (0x00, 0x88, 0xff), (0xbb, 0xbb, 0xbb)),
            'Pepto': ((0x00, 0x00, 0x00), (0xFF, 0xFF, 0xFF),
                      (0x68, 0x37, 0x2B), (0x70, 0xA4, 0xB2),
                      (0x6F, 0x3D, 0x86), (0x58, 0x8D, 0x43),
                      (0x35, 0x28, 0x79), (0xB8, 0xC7, 0x6F),
                      (0x6F, 0x4F, 0x25), (0x43, 0x39, 0x00),
                      (0x9A, 0x67, 0x59), (0x44, 0x44, 0x44),
                      (0x6C, 0x6C, 0x6C), (0x9A, 0xD2, 0x84),
                      (0x6C, 0x5E, 0xB5), (0x95, 0x95, 0x95))}
COLOR_SUBS = {BLACK: [DARK_GRAY, BROWN, DARK_BLUE],
              WHITE: [LIGHT_GRAY, LIGHT_GRAY],
              RED: [DARK_GRAY, GRAY, PURPLE],
              MAGENTA: [LIGHT_GRAY, GRAY, LIGHT_BLUE],
              PURPLE: [GRAY, DARK_GRAY, RED, ORANGE],
              GREEN: [GRAY, LIGHT_GRAY, YELLOW, LIGHT_GREEN],
              DARK_BLUE: [DARK_GRAY, BROWN, LIGHT_BLUE, BLACK],
              YELLOW: [LIGHT_GRAY, LIGHT_GREEN, WHITE],
              ORANGE: [GRAY, DARK_GRAY, PURPLE, BROWN],
              BROWN: [DARK_GRAY, DARK_BLUE, RED, BLACK],
              PINK: [GRAY, LIGHT_GRAY, GREEN, RED],
              DARK_GRAY: [GRAY, BROWN, DARK_BLUE, BLACK],
              GRAY: [LIGHT_GRAY, GREEN, LIGHT_BLUE, ORANGE, PURPLE, PINK],
              LIGHT_GREEN: [LIGHT_GRAY, YELLOW, WHITE],
              LIGHT_BLUE: [GRAY, LIGHT_GRAY, MAGENTA],
              LIGHT_GRAY: [LIGHT_GREEN, YELLOW, GRAY, WHITE]}
COLOR_NAMES = dict(enumerate(["Black", "White", "Red", "Magenta", "Purple",
                              "Green", "Dark blue", "Yellow", "Orange",
                              "Brown", "Pink", "Dark gray", "Gray",
                              "Light green", "Light blue", "Light gray"]))


class Char(object):
    """
    Char implementation
    """

    def __init__(self, log, prev=None, fix_clash=False):
        """
        Init. prev is the Char object which represents the same character in
        previous picture
        """
        self.background = None
        self.clash = False
        self.colors = {}
        self.max_colors = 2
        self.pixels = {}
        self.pixel_state = {0: False, 1: False}
        self.prev = prev
        self.log = log
        self._fix_clash = fix_clash

    def _analyze_color_map(self):
        """
        Check for the optimal color placement in char. This method may be run
        only on not clashed chars.
        """

        if self._check_clash():
            if not self._fix_clash:
                return
            self._fix_color_clash()

        if self.prev and self.prev.clash:
            return

        colors = Counter(self.pixels.values())
        self._compare_colors(colors)

    def get_binary_data(self):
        """
        Return binary data for the char
        """
        raise NotImplementedError

    def process(self, box, palette_map):
        """
        Store pixel/color information
        """
        for chry, chrx in sorted([(y, x)
                                  for x in range(box.size[0])
                                  for y in range(box.size[1])]):
            self.pixels[(chry, chrx)] = palette_map[box.getpixel((chrx, chry))]

        self._analyze_color_map()

    def _fix_color_clash(self):
        """
        Try to fix the color clashes by assigning excessed colors to existing
        in the char
        """
        colors = Counter(self.pixels.values())
        base = colors.most_common(self.max_colors)
        remapped_colors = {}
        index = self.max_colors

        if self.background is not None and self.background not in dict(base):
            index -= 1
            base = colors.most_common(index)
            base += [(self.background, 0)]

        for col, dummy in colors.most_common()[index:]:
            sub = _get_the_substitute(col, base)
            if sub is not None:
                self.log.debug("Using color '%s' instead '%s'",
                               COLOR_NAMES[sub],
                               COLOR_NAMES[col])
                remapped_colors[col] = sub
            elif self.background is not None:
                self.log.warning("Cannot remap color; using background - '%s'",
                                 COLOR_NAMES[self.background])
                remapped_colors[col] = self.background
            else:
                self.log.warning("Cannot remap color; using first - '%s'",
                                 COLOR_NAMES[base[0][0]])
                remapped_colors[col] = base[0][0]

        for coord, color in self.pixels.items():
            if color not in remapped_colors:
                continue
            self.pixels[coord] = remapped_colors[color]

        # Clashes are fixed (probably)
        self.clash = False

    def _check_clash(self):
        """
        Check color clash. max_colors is the maximum colors per char object
        """
        colors = Counter(self.pixels.values())

        if len(colors) > self.max_colors:
            self.clash = True

        if self.background is None:
            return self.clash

        if len(colors) == self.max_colors and self.background not in colors:
            self.clash = True

        return self.clash

    def _compare_colors_with_prev_char(self, colors, repeat=False):
        """
        Make a color map to the pixels comparing to the previous data
        """
        needs_repeat = False
        for color in colors:
            if color == self.background:
                continue
            if repeat:
                if color in self.colors:
                    continue

                for pair, taken in self.pixel_state.items():
                    if not taken:
                        self.pixel_state[pair] = True
                        self.colors[color] = pair
                        break
            elif self.prev and self.prev.colors.get(color, None) is not None:
                self.colors[color] = self.prev.colors[color]
                self.pixel_state[self.prev.colors[color]] = True
            else:
                needs_repeat = True

        return needs_repeat

    def _compare_colors(self, colors):
        """
        Make a color map to the pixels
        """
        if self._compare_colors_with_prev_char(colors):
            self._compare_colors_with_prev_char(colors, True)


class FullScreenImage(object):
    """
    Class represents full-screen image in unspecified C64 format
    """
    WIDTH = 320
    HEIGHT = 200
    LOGGER_NAME = 'PictureConverter'

    def __init__(self, fname, errors_action="none"):
        """
        Initialization. Fname is a full/relative path for a hires picture.
        errors_action can be one of "none", "save" and "show". In case of
        color clashes, it will do nothing, save picture with "_error" suffix
        or show it respectively.
        """
        self._errors_action = errors_action
        self._fname = fname
        self._palette_map = None
        self._save_map = {}
        self._src_image = None
        self.chars = {}
        self.data = {}
        self.log = Logger(self.LOGGER_NAME)()
        self.prev_chars = {}

    def save(self, filename, format_=None):
        """
        Save picture in one of the formats or as an executable prg.
        """
        if not self.data.get('bitmap'):
            if not self.convert():
                return 1

        if os.path.exists(filename):
            self.log.warning("File `%s' will be overwritten", filename)

        if self._save_map[format_](filename):
            return 0

    def set_bg_color(self, color):
        """
        Set custom color for background (as index)
        """
        self.log.info("Setting background color to: %d", color)
        self.data['background'] = color

    def set_border_color(self, color):
        """
        Set custom color for border (as index)
        """
        self.log.info("Setting border color to: %d", color)
        self.data['border'] = color

    def convert(self):
        """
        Convert image to binary data
        """
        if not self._load():
            return False

        if not self._check_dimensions():
            return False

        hist = self._src_image.histogram()
        self._colors_check(hist)
        self._find_best_palette_map()
        self._find_most_freq_color(hist)
        return self._fill_memory()

    def _load(self):
        """
        Load src image and store it under _src_image attribute.
        """
        try:
            img = Image.open(self._fname)
            img = img.convert("RGB").convert('P', palette=Image.ADAPTIVE,
                                             dither='none', colors=16)
            self._src_image = img
        except IOError:
            self.log.critical("Cannot open file `%s'. Exiting.", self._fname)
            if self.log.getEffectiveLevel() == logging.DEBUG:
                raise
            return False
        return True

    def _check_dimensions(self):
        """
        Check for image dimensions. If different from 320x200 return False
        """
        width, height = self._src_image.size

        if width == FullScreenImage.WIDTH and height == FullScreenImage.HEIGHT:
            return True

        return False

    def _find_most_freq_color(self, histogram):
        """
        Check for the most frequent color on the picture. Can be used to
        auto detect background/border colors.
        Value remembered in attribute data['most_freq_color'] is an
        index in the C64 palette (NOT the source image palette!).
        """
        pal = self._src_image.getpalette()
        pal = [tuple(pal[index:index + 3]) for index in xrange(0, len(pal),
                                                               3)]
        highest = sorted([(count, index)
                          for index, count in enumerate(histogram[:16])])[-1]
        self.data['most_freq_color'] = self._palette_map[pal[highest[1]]]

    def _colors_check(self, histogram):
        """
        Find out how many same colors do we have. Just an information to the
        user.
        """
        no_of_colors = len([col for col in histogram if col != 0])
        if no_of_colors < 2:
            self.log.warn("Picture have %d color(s). Result may be confusing.",
                          no_of_colors)
        else:
            self.log.info("Picture have %d colors", no_of_colors)

        return no_of_colors

    def _get_palette(self):
        """
        Return source image palette as RGB tuples
        """
        pal = self._src_image.getpalette()
        return [(pal[i], pal[i + 1], pal[i + 2]) for i in range(0, 16 * 3, 3)]

    def _fill_memory(self):
        """
        Create bitmap/screen-ram/color-ram colors if needed. Should be
        implemented in concrete implementation.
        """
        raise NotImplementedError()

    def _find_best_palette_map(self):
        """
        Try to match source image palette to predefined ones, and return name
        of the best matched palette and color map for current source image.
        """
        palettes_map = {}
        src_pal = self._get_palette()
        nearest_match = -1
        selected_palette = None

        for pal_name, pal in PALETTES.items():
            quality = 0
            palettes_map[pal_name] = {}
            for orig_color in src_pal:
                color2use, delta = _best_color_match(orig_color, pal)
                quality += delta
                palettes_map[pal_name][orig_color] = color2use
            if nearest_match < 0 or nearest_match > quality:
                nearest_match = quality
                selected_palette = pal_name

        if nearest_match == 0:
            self.log.info("Perfect palette match for %s-palette",
                          selected_palette)
        else:
            self.log.info("Quality: %d for %s-palette ", nearest_match,
                          selected_palette)

        self._palette_map = palettes_map[selected_palette]

    def _get_border(self):
        """
        Return border color index
        """
        border = self.data.get('border')
        if border is None:
            border = self.data.get('most_freq_color', 0)

        return border

    def _get_background(self):
        """
        Return background color index
        """
        background = self.data.get("background")
        if background is None:
            background = self.data.get("most_freq_color", 0)

        self.log.debug("Setting color '%s' as background.",
                       COLOR_NAMES[background])
        return background

    def _error_image_action(self, error_list, scaled=False):
        """
        Create image with hints of clashes. error_list contains coordinates of
        characters which encounters clashes. Picture is for overview only,so
        it is always have dimensions 320x200.
        """
        char_x_size = 1
        x_offset = 3
        if self._errors_action == "none":
            return

        image = self._src_image.copy().convert("RGBA")

        # TODO: refactor this crap below
        if scaled:
            image = image.resize((320, 200))

        if image.size[0] == 320:
            x_offset = 7
            if scaled:
                char_x_size = 2

        if image.size[0] == 160:
            char_x_size = 1

        image_map = image.copy()
        drawable = Draw(image_map)

        for chrx, chry in error_list:
            drawable.rectangle((chrx * char_x_size,
                                chry,
                                chrx * char_x_size + x_offset,
                                chry + 7),
                               outline="red")

        image = Image.blend(image, image_map, 0.65)
        del drawable

        if self._errors_action in ('save', 'grafx2'):
            file_obj = open(get_modified_fname(self._fname, 'png', '_error.'),
                            "wb")
            image.save(file_obj, "png")
            file_obj.close()
            if self._errors_action == 'grafx2':
                os.system("grafx2 %s %s" %
                          (self._fname, get_modified_fname(self._fname, 'png',
                                                           '_error.')))
        else:
            clashes = image.resize((640, 400))
            clashes.show()


def _get_the_substitute(color, base):
    """Return best match for provided color out of base and background"""
    sub_color = None
    index = 16
    for col, dummy in base:
        if col in COLOR_SUBS[color]:
            if COLOR_SUBS[color].index(col) < index:
                index = COLOR_SUBS[color].index(col)
                sub_color = col

    return sub_color


def _best_color_match(orig_color, colors):
    """
    Match provided color for closed match in colors list, and return it's
    index and delta (which indicates similarity)
    """
    delta = 0
    src_r, src_g, src_b = orig_color

    rgb_diff = 195075  # arbitrary number of maximum difference
    for idx, (pal_r, pal_g, pal_b) in enumerate(colors):
        partial_delta = (src_r - pal_r) ** 2 + \
                        (src_g - pal_g) ** 2 + (src_b - pal_b) ** 2

        if partial_delta == 0:  # bingo
            delta = partial_delta
            color2use = idx
            break

        if rgb_diff > partial_delta:
            rgb_diff = partial_delta
            delta = rgb_diff
            color2use = idx

    return color2use, delta
