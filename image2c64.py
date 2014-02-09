#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
image2c64 v2.0 converts virtually any image supported by Pillow to C64 hires
or multicolor formats. Best results are achived with filetypes PNG or GIF.
"""
import sys
import os
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import logging
from collections import Counter

from PIL import Image
from PIL.ImageDraw import Draw


# Palettes are organized with original C64 order:
# black, white, red, magenta, purple, green, dark blue, yellow,
# orange, brown, pink, dark gray, gray, light green, light blue, light gray
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


class Logger(object):
    """
    Logger class with output on console only
    """
    def __init__(self, logger_name):
        """
        Initialize named logger
        """
        self._log = logging.getLogger(logger_name)
        self.setup_logger()
        self._log.set_verbose = self.set_verbose

    def __call__(self):
        """
        Calling this object will return configured logging.Logger object with
        additional set_verbose() method.
        """
        return self._log

    def set_verbose(self, verbose_level, quiet_level):
        """
        Change verbosity level. Default level is warning.
        """
        self._log.setLevel(logging.WARNING)

        if quiet_level:
            self._log.setLevel(logging.ERROR)
            if quiet_level > 1:
                self._log.setLevel(logging.CRITICAL)

        if verbose_level:
            self._log.setLevel(logging.INFO)
            if verbose_level > 1:
                self._log.setLevel(logging.DEBUG)

    def setup_logger(self):
        """
        Create setup instance and make output meaningful :)
        """
        if self._log.handlers:
            # need only one handler
            return

        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.set_name("console")
        console_formatter = logging.Formatter("%(levelname)s: %(message)s")
        console_handler.setFormatter(console_formatter)
        self._log.addHandler(console_handler)
        self._log.setLevel(logging.WARNING)


class Char(object):
    """
    Char implementation
    """

    def __init__(self, prev=None):
        """
        Init. prev is the Char object which represents the same character in
        previous picture
        """
        self.clash = False
        self.colors = {}
        self.max_colors = 2
        self.pixels = {}
        self.prev = prev

    def _analyze_color_map(self):
        """
        Check for the optimal color placement in char. This method may be run
        only on not clashed chars.
        """

        if self._check_clash():
            return

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

    def _check_clash(self):
        """
        Check color clash. max_colors is the maximum colors per char object
        """
        if len(set([x for x in self.pixels.values()])) > self.max_colors:
            self.clash = True
        return self.clash

    def _compare_colors_with_prev_char(self, colors, repeat=False):
        """
        Make a color map to the pixels comparing to the previous data
        """
        raise NotImplementedError

    def _compare_colors(self, colors):
        """
        Make a color map to the pixels
        """
        if self._compare_colors_with_prev_char(colors):
            self._compare_colors_with_prev_char(colors, True)


class HiresChar(Char):
    """
    Hires char implementation
    """

    def __init__(self, mfc, prev=None):
        """
        Init. prev is the Char object which represents the same character
        in previous picture. Mfc stands for most frequent color, which will be
        preferred as a background for a character, if exists in char colors.
        """
        super(HiresChar, self).__init__(prev)
        self._mfc = mfc
        self.pixel_state = {0: False, 1: False}

    def get_binary_data(self):
        """
        Return binary data for the char
        """
        result = {"bitmap": [], "screen_ram": 0}

        for row in zip(*[iter(sorted(self.pixels))] * 8):
            char_line = 0
            for idx, pixel in enumerate(row):
                bit_ = self.colors.get(self.pixels[pixel], self._mfc)
                char_line += bit_ * 2 ** (7 - idx)
            result['bitmap'].append(char_line)

        colors = dict([(y, x) for x, y in self.colors.items()])
        result['screen-ram'] = colors.get(0, self._mfc)
        if 1 in colors:
            result['screen-ram'] += colors[1] * 16
        return result

    def _compare_colors_with_prev_char(self, colors, repeat=False):
        """
        Make a color map to the pixels comparing to the previous data
        """
        needs_repeat = False
        if repeat:
            if self._mfc in colors and not self.pixel_state[0] \
                    and not self.pixel_state[1]:
                self.pixel_state[0] = True
                self.colors[self._mfc] = 0

        for color in colors:
            if repeat:
                for value, taken in self.pixel_state.items():
                    if not taken and color not in self.colors.values():
                        self.pixel_state[value] = True
                        self.colors[color] = value
                        break
            elif self.prev and self.prev.colors.get(color, None) is not None:
                self.colors[color] = self.prev.colors[color]
                self.pixel_state[self.prev.colors[color]] = True
            else:
                needs_repeat = True

        return needs_repeat


class MultiChar(Char):
    """Char implementation for multicolor mode."""

    def __init__(self, background, prev=None):
        """
        Init. prev is the Char object which represents the same character
        in previous picture
        """
        super(MultiChar, self).__init__(prev)
        self.background = background
        self.max_colors = 4
        self.pairs = {(0, 1): False,
                      (1, 0): False,
                      (1, 1): False}

    def _analyze_color_map(self):
        """
        Check for the optimal color placement in char. This method may be run
        only on not clashed chars. Background color should be always
        available.
        """
        self.colors[self.background] = (0, 0)
        super(MultiChar, self)._analyze_color_map()

    def get_binary_data(self):
        """
        Return binary data for the char
        """
        result = {"bitmap": [], "screen-ram": 0, "color-ram": 0}

        for row in zip(*[iter(sorted(self.pixels))] * 4):
            char_line = 0
            for idx, pixel in enumerate(row):
                bits = self.colors.get(self.pixels[pixel], (0, 0))
                char_line += bits[0] * 2 ** (7 - idx * 2)
                char_line += bits[1] * 2 ** (6 - idx * 2)
            result["bitmap"].append(char_line)

        colors = dict([(y, x) for x, y in self.colors.items()])
        col1 = colors.get((0, 1), colors.get((0, 0))) * 16
        col2 = colors.get((1, 0), colors.get((0, 0)))

        result["screen-ram"] = col1 + col2
        result["color-ram"] = colors.get((1, 1), colors.get((0, 0)))

        return result

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

                for pair, taken in self.pairs.items():
                    if not taken:
                        self.pairs[pair] = True
                        self.colors[color] = pair
                        break
            elif self.prev and self.prev.colors.get(color, None) is not None:
                self.colors[color] = self.prev.colors[color]
                self.pairs[self.prev.colors[color]] = True
            else:
                needs_repeat = True

        return needs_repeat


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
            if not self._convert():
                return False

        if os.path.exists(filename):
            self.log.warning("File `%s' will be overwritten", filename)

        return self._save_map[format_](filename)

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
            self.log.critical("Cannot open file `%s'. Exiting." % self._fname)
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
        highest = (0, 0)

        for index, count in enumerate(histogram[:16]):
            if count > highest[1]:
                highest = (index, count)

        self.data['most_freq_color'] = self._palette_map[pal[highest[0]]]

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

    def _convert(self):
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
                color2use, delta = best_color_match(orig_color, pal)
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

        return background

    def _error_image_action(self, error_list, scaled=False):
        """
        Create image with hints of clashes. error_list contains coordinates of
        characters which encounters clashes. Picture is for overview only,so
        it is always have dimensions 320x200.
        """
        char_x_size = 1
        if self._errors_action == "none":
            return

        image = self._src_image.copy().convert("RGBA")
        if scaled:
            image = image.resize((320, 200))
            char_x_size = 2

        image_map = image.copy()
        drawable = Draw(image_map)

        for chrx, chry in error_list:
            drawable.rectangle((chrx * char_x_size, chry,
                                chrx * char_x_size + 7, chry + 7),
                               outline="red")

        image = Image.blend(image, image_map, 0.65)
        del drawable

        if self._errors_action == 'save':
            file_obj = open(get_modified_fname(self._fname, 'png', '_error.'),
                            "wb")
            image.save(file_obj, "png")
            file_obj.close()
        else:
            clashes = image.resize((640, 400))
            clashes.show()


class MultiConverter(FullScreenImage):
    """
    Convert bitmap graphic in png/gif/probably other formats supported by
    PIL prepared as multicolor image into executable C64 prg file suitable
    to transfer to real thing or run in emulator.
    """
    WIDTH = 160
    HEIGHT = 200
    LOGGER_NAME = "MultiConverter"

    def __init__(self, fname, errors_action="none"):
        """
        Initialization
        """
        super(MultiConverter, self).__init__(fname, errors_action)
        self._save_map = {"prg": self._save_prg,
                          "raw": self._save_raw,
                          "multi": self._save_koala,  # sane default
                          "koala": self._save_koala}

    def _load(self):
        """
        Load source image and store it under _src_image attribute.
        Shrink it if needed to 160x200 pixels.
        """
        if super(MultiConverter, self)._load():
            if self._src_image.size == (320, 200):
                self._src_image = self._src_image.resize((160, 200))
            return True
        return False

    def _check_dimensions(self):
        """
        Check for image dimensions. If different from 320x200 or 160x200
        return False
        """
        result = super(MultiConverter, self)._check_dimensions()

        width, height = self._src_image.size
        if width == MultiConverter.WIDTH and height == MultiConverter.HEIGHT:
            return True

        if not result:
            self.log.error("Wrong picture dimensions: %dx%d", width, height)
        return result

    def _get_displayer(self):
        """
        Get displayer for multicolor picture (based on kickassembler example)
        """
        border = chr(self._get_border())
        background = chr(self._get_background())
        displayer = ["\x01\x08\x0b\x08\n\x00\x9e2064\x00\x00\x00\x00\x00\x00"
                     "\xa98\x8d\x18\xd0\xa9\xd8\x8d\x16\xd0\xa9;\x8d\x11\xd0"
                     "\xa9", border, "\x8d \xd0\xa9", background, "\x8d!\xd0"
                     "\xa2\x00\xbd\x00\x1c\x9d\x00\xd8\xbd\x00\x1d\x9d\x00"
                     "\xd9\xbd\x00\x1e\x9d\x00\xda\xbd\x00\x1f\x9d\x00\xdb"
                     "\xe8\xd0\xe5LF\x08"]

        return "".join(displayer)

    def _fill_memory(self):
        """
        Create bitmap, screen-ram, color-ram and error map as a picture if
        needed.
        """
        self.data["bitmap"] = []
        self.data["screen-ram"] = []
        self.data["color-ram"] = []
        self.data["background"] = self._get_background()
        self.data["chars"] = []

        error_list = []

        # get every char (4x8 pixels) starting from upper left corner
        for chry, chrx in [(chry, chrx)
                           for chry in range(0, self._src_image.size[1], 8)
                           for chrx in range(0, self._src_image.size[0], 4)]:

            box = self._src_image.crop((chrx, chry,
                                        chrx + 4, chry + 8)).convert("RGB")

            char = MultiChar(self.data["background"],
                             self.prev_chars.get((chry, chrx)))
            char.process(box, self._palette_map)
            self.chars[(chry, chrx)] = char

            char_data = char.get_binary_data()
            self.data['bitmap'].extend(char_data['bitmap'])
            self.data['screen-ram'].append(char_data['screen-ram'])
            self.data['color-ram'].append(char_data['color-ram'])

            if char.clash:
                error_list.append((chrx, chry))
                self.log.error("Too many colors per block in char %d, %d near"
                               " x=%d, y=%d.", chrx, chry, chrx * 8 + 4,
                               chry * 8 + 4)

        if error_list:
            self._error_image_action(error_list, True)
            return False

        self.log.info("Conversion successful.")
        return True

    def _save_prg(self, filename):
        """
        Save executable version of the picture
        """
        file_obj = open(filename, "wb")
        file_obj.write(self._get_displayer())
        file_obj.write(951 * chr(0))
        file_obj.write("".join([chr(col) for col in self.data["screen-ram"]]))
        file_obj.write(3096 * chr(0))
        file_obj.write("".join([chr(col) for col in self.data["color-ram"]]))
        file_obj.write(24 * chr(0))
        file_obj.write("".join([chr(byte) for byte in self.data["bitmap"]]))
        file_obj.close()
        self.log.info("Saved executable under `%s' file", filename)
        return True

    def _save_koala(self, filename):
        """
        Save as Koala format
        """
        file_obj = open(filename, "wb")
        file_obj.write("%c%c" % (0x00, 0x60))

        for char in self.data['bitmap']:
            file_obj.write("%c" % char)

        for char in self.data["screen-ram"]:
            file_obj.write("%c" % char)

        for char in self.data["color-ram"]:
            file_obj.write("%c" % char)

        file_obj.write(chr(self.data["background"]))

        border = self._get_border()
        file_obj.write("%c" % border)
        file_obj.close()
        self.log.info("Saved in Koala format under `%s' file", filename)
        return True

    def _save_raw(self, filename):
        """
        Save as raw data
        """

        with open(filename + "_bitmap.raw", "w") as file_obj:
            for char in self.data['bitmap']:
                file_obj.write("%c" % char)

        with open(filename + "_screen.raw", "w") as file_obj:
            for char in self.data["screen-ram"]:
                file_obj.write("%c" % char)

        with open(filename + "_color-ram.raw", "w") as file_obj:
            for char in self.data["color-ram"]:
                file_obj.write("%c" % char)

        with open(filename + "_bg.raw", "w") as file_obj:
            file_obj.write(chr(self.data["background"]))

        self.log.info("Saved in raw format under `%s_*' files", filename)
        return True


class HiresConverter(FullScreenImage):
    """
    Convert bitmap graphic in png/gif/probably other formats supported by
    PIL into executable C64 prg file suitable to transfer to real thing or
    run in emulator.
    """
    LOGGER_NAME = "HiresConverter"

    def __init__(self, fname, errors_action="none"):
        """
        Initialization
        """
        super(HiresConverter, self).__init__(fname, errors_action)
        self._save_map = {"prg": self._save_prg,
                          "raw": self._save_raw,
                          "hires": self._save_ash,  # make sane default
                          "art-studio-hires": self._save_ash}

    def _get_displayer(self):
        """
        Get displayer for hires picture
        """
        border = "%c" % self._get_border()
        displayer = ["\x01\x08\x0b\x08\x0a\x00\x9e\x32\x30\x36\x34\x00"
                     "\x00\x00\x00\x00\x00\x78\xa9", border, "\x8d\x20\xd0\xa9"
                     "\x00\x8d\x21\xd0\xa9\xbb\x8d\x11\xd0\xa9\x3c\x8d"
                     "\x18\xd0\x4c\x25\x08"]
        return "".join(displayer)

    def _fill_memory(self):
        """
        Create bitmap/screen and error map as a picture if needed.
        """
        self.data["bitmap"] = []
        self.data["screen-ram"] = []
        error_list = []

        for chry, chrx in [(chry, chrx)
                           for chry in range(0, self._src_image.size[1], 8)
                           for chrx in range(0, self._src_image.size[0], 8)]:

            box = self._src_image.crop((chrx, chry,
                                        chrx + 8, chry + 8)).convert("RGB")

            char = HiresChar(self.data['most_freq_color'],
                             self.prev_chars.get((chry, chrx)))
            char.process(box, self._palette_map)
            self.chars[(chry, chrx)] = char

            char_data = char.get_binary_data()
            self.data['bitmap'].extend(char_data['bitmap'])
            self.data['screen-ram'].append(char_data['screen-ram'])

            if char.clash:
                error_list.append((chrx, chry))
                self.log.error("Too many colors per block in char %d, %d near"
                               " x=%d, y=%d.", chrx, chry,
                               chrx * 8 + 4, chry * 8 + 4)

        if error_list:
            self._error_image_action(error_list)
            return False

        self.log.info("Conversion successful.")
        return True

    def _save_prg(self, filename):
        """
        Save executable version of the picture
        """
        file_obj = open(filename, "wb")
        file_obj.write(self._get_displayer())
        file_obj.write(984 * chr(0))
        file_obj.write("".join([chr(col) for col in self.data["screen-ram"]]))
        file_obj.write(4120 * chr(0))
        file_obj.write("".join([chr(byte) for byte in self.data["bitmap"]]))
        file_obj.close()
        self.log.info("Saved executable under `%s' file", filename)
        return True

    def _save_ash(self, filename):
        """
        Save as Art Studio hires
        """
        file_obj = open(filename, "wb")
        file_obj.write("%c%c" % (0x00, 0x20))

        for char in self.data['bitmap']:
            file_obj.write("%c" % char)

        for char in self.data["screen-ram"]:
            file_obj.write("%c" % char)

        border = self._get_border()
        file_obj.write("%c" % border)
        file_obj.write("\x00\x00\x00\x00\x00\x00")
        file_obj.close()
        self.log.info("Saved in Art Studio Hires format under `%s' file",
                      filename)
        return True

    def _save_raw(self, filename):
        """
        Save raw data
        """
        with open(filename + "_screen.raw", "wb") as file_obj:
            file_obj.write("".join([chr(col)
                                    for col in self.data["screen-ram"]]))

        with open(filename + "_bitmap.raw", "wb") as file_obj:
            file_obj.write("".join([chr(byte)
                                    for byte in self.data["bitmap"]]))

        self.log.info("Saved raw data under `%s_*' files", filename)
        return True

    def _check_dimensions(self):
        """
        Check for image dimensions. Same as in superclass, needed for feedback
        only.
        """
        result = super(HiresConverter, self)._check_dimensions()
        width, height = self._src_image.size

        if not result:
            self.log.error("Wrong picture dimensions: %dx%d", width, height)

        return result


def get_modified_fname(fname, ext, suffix='.'):
    """
    Change the name of provided filename to different. Suffix should contain
    dot, since it is last part of the filename and dot should separate it
    from extension. If not, dot will be added automatically.
    """
    path, _ = os.path.splitext(fname)
    if not (suffix.endswith(".") or ext.startswith(".")):
        ext = "." + ext
    return "".join([path, suffix, ext])


def convert(arguments, converter_class):
    """
    Convert pictures
    """
    last = conv = None
    for fname in arguments.filename:
        if conv:
            last = conv

        conv = converter_class(fname, arguments.errors)

        if last:
            conv.prev_chars = last.chars

        if arguments.border is not None:
            conv.set_border_color(arguments.border)

        # note, that for hires pictures it doesn't make sense, and will be
        # ignored.
        if arguments.background is not None:
            conv.set_bg_color(arguments.background)

        conv.log.set_verbose(arguments.verbose, arguments.quiet)

        filename, format_ = resolve_name(arguments, fname)
        conv.save(filename, format_)


def best_color_match(orig_color, colors):
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


def resolve_name(arguments, fname):
    """
    Return right name and format for an output file.
    """
    if arguments.output:
        if len(arguments.filename) > 1:
            if not os.path.exists(arguments.output):
                os.mkdir(arguments.output)
            if not os.path.isdir(arguments.output):
                raise IOError("Path `%s' is not directory" % arguments.output)
            filename = os.path.join(arguments.output,
                                    get_modified_fname(fname, "prg"))
        else:
            filename = arguments.output
    else:
        filename = get_modified_fname(fname, "prg")

    format_ = arguments.format

    if arguments.executable:

        format_ = "prg"
        _, ext = os.path.splitext(filename)
        if ext != ".prg":
            filename = get_modified_fname(filename, "prg")

    if arguments.raw:

        format_ = "raw"
        filename, ext = os.path.splitext(filename)

    return filename, format_


def multiconv(arguments):
    """
    Convert to multicolor picture
    """
    convert(arguments, MultiConverter)


def hiresconv(arguments):
    """
    Convert to hires picture
    """
    convert(arguments, HiresConverter)


if __name__ == "__main__":

    F_MAP = {"art-studio-hires": hiresconv,
             "hires": hiresconv,
             "koala": multiconv,
             "multi": multiconv}

    PARSER = ArgumentParser(description=__doc__,
                            formatter_class=RawDescriptionHelpFormatter)
    PARSER.add_argument("-b", "--border", help="set color number for border, "
                        "default: most frequent color", type=int,
                        choices=range(16))
    PARSER.add_argument("-g", "--background", help="set color number for "
                        "background", type=int, choices=range(16))
    PARSER.add_argument("-e", "--errors", help="save errormap under the "
                        "same name with '_error' suffix, show it or don't do "
                        "anything (conversion stops anyway)", default="none",
                        choices=("show", "save", "none"))
    PARSER.add_argument("-f", "--format", help="format of output file, this "
                        "option is mandatory", choices=F_MAP.keys(),
                        required=True)
    GROUP = PARSER.add_mutually_exclusive_group()
    GROUP.add_argument("-x", "--executable", help="produce C64 executable as"
                       " 'prg' file", action="store_true")
    GROUP.add_argument("-r", "--raw", help="produce raw files with only the "
                       "data. Useful for include in assemblers",
                       action="store_true")
    PARSER.add_argument("-o", "--output", help="output filename, default: "
                        "same filename as original with appropriate extension"
                        ". If multiple files provided as the input, output "
                        "will be treated as the directory")
    PARSER.add_argument('filename', nargs="+")

    GROUP = PARSER.add_mutually_exclusive_group()
    GROUP.add_argument("-q", "--quiet", help='please, be quiet. Adding more '
                       '"q" will decrease verbosity', action="count",
                       default=0)
    GROUP.add_argument("-v", "--verbose", help='be verbose. Adding more "v" '
                       'will increase verbosity', action="count", default=0)

    ARGS = PARSER.parse_args()
    F_MAP[ARGS.format](ARGS)
