#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Image2c64 <https://bitbucket.org/gryf/image2c64>

This program converts virtually any image supported by PIL to C64 hires or
multicolor formats. Best results are achived with filetypes PNG or GIF.

Inspired on PNG2HIRES v0.2 gfx format converter /enthusi (onslaught)

As an input 320x200 (multicolor or hires) or 160x200 (mutlicolor) picture is
expected. Mutlicolor pictures will be scaled down to 160x200. Picture will be
converted to 16 colors. During that process some information can be lost, if
used more than 16 colors.

Requirements:
    - Python 2.7
    - Image (PIL) module <http://www.pythonware.com/products/pil/>

Changes:
    2012-11-20 Added executable output format for multicolor
    2012-11-19 Added multicolor support, changes to the docstrings
    2012-11-18 First public release

Author: Roman 'gryf' Dobosz <gryf73@gmail.com>
Date: 2012-11-20
Version: 1.2
Licence: BSD
"""
import sys
import os
from argparse import ArgumentParser, RawDescriptionHelpFormatter
import logging

import Image
from ImageDraw import Draw


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
        self._fname = fname
        self._errors_action = errors_action
        self._error_image = None
        self._src_image = None
        self.log = Logger(self.LOGGER_NAME)()
        self._data = {}
        self._save_map = {}

    def save(self, filename, format_=None):
        """
        Save picture in one of the formats or as an executable prg.
        """
        if not self._data.get('bitmap'):
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
        self._data['background'] = color

    def set_border_color(self, color):
        """
        Set custom color for border (as index)
        """
        self.log.info("Setting border color to: %d", color)
        self._data['border'] = color

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

    def _find_most_freq_color(self, histogram, palette_map):
        """
        Check for the most frequent color on the picture. Can be used to
        auto detect background/border colors.
        Value remembered in attribute _data['most_freq_color'] is an
        index in the C64 palette (NOT the source image palette!).
        """
        pal = self._src_image.getpalette()
        pal = [tuple(pal[index:index + 3]) for index in xrange(0, len(pal),
                                                               3)]
        highest = (0, 0)

        for index, count in enumerate(histogram[:16]):
            if count > highest[1]:
                highest = (index, count)

        self._data['most_freq_color'] = palette_map[pal[highest[0]]]

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
        palette_map = self._get_best_palette_map()
        self._find_most_freq_color(hist, palette_map)
        return self._fill_memory(pal_map=palette_map)

    def _get_palette(self):
        """
        Return source image palette as RGB tuples
        """
        pal = self._src_image.getpalette()
        return [(pal[i], pal[i + 1], pal[i + 2]) for i in range(0, 16 * 3, 3)]

    def _fill_memory(self, pal_map=None):
        """
        Create bitmap/screen-ram/color-ram colors if needed. Should be
        implemented in concrete implementation.
        """
        raise NotImplementedError()

    def _get_displayer(self):
        """
        Return displayer code. Here it is only a stub. Should be implemented
        for concrete implementations.
        """
        raise NotImplementedError()

    def _get_best_palette_map(self):
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

        return palettes_map[selected_palette]

    def _get_border(self):
        """
        Return border color index
        """
        border = self._data.get('border')
        if border is None:
            border = self._data.get('most_freq_color', 0)

        return border

    def _get_background(self):
        """
        Return background color index
        """
        background = self._data.get("background")
        if background is None:
            background = self._data.get("most_freq_color", 0)

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

    def _fill_memory(self, pal_map=None):
        """
        Create bitmap, screen-ram, color-ram and error map as a picture if
        needed.
        """
        self._data["bitmap"] = []
        self._data["screen-ram"] = []
        self._data["color-ram"] = []
        self._data["background"] = self._get_background()
        pairs = ((0, 1), (1, 0), (1, 1))

        error_list = []

        for chry, chrx in [(chry, chrx)
                           for chry in range(0, self._src_image.size[1], 8)
                           for chrx in range(0, self._src_image.size[0], 4)]:

            box = self._src_image.crop((chrx, chry,
                                        chrx + 4, chry + 8)).convert("RGB")
            char_colors = []

            for y__ in range(8):
                line = 0
                clash = False
                for x__ in range(4):
                    bits = None
                    actual_color = pal_map[box.getpixel((x__, y__))]
                    if actual_color == self._data["background"]:
                        bits = (0, 0)
                    elif actual_color not in [idx[0] for idx in char_colors]:
                        if len(char_colors) == 3:
                            clash = True
                            bits = (0, 0)
                        else:
                            char_colors.append((actual_color,
                                                pairs[len(char_colors)]))

                    if not bits:
                        bits = [idx[1] for idx in char_colors if
                                idx[0] == actual_color][0]

                    line += bits[0] * 2 ** (7 - x__ * 2)
                    line += bits[1] * 2 ** (7 - (x__ * 2 + 1))

                self._data["bitmap"].append(line)

            while len(char_colors) < 3:
                char_colors.append((self._data["background"], (0, 0)))

            self._data["screen-ram"].append(char_colors[0][0] * 16 +
                                            char_colors[1][0])
            self._data["color-ram"].append(char_colors[2][0])

            if clash:
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
        file_obj.write("".join([chr(col) for col in self._data["screen-ram"]]))
        file_obj.write(3096 * chr(0))
        file_obj.write("".join([chr(col) for col in self._data["color-ram"]]))
        file_obj.write(24 * chr(0))
        file_obj.write("".join([chr(byte) for byte in self._data["bitmap"]]))
        file_obj.close()
        self.log.info("Saved executable under `%s' file", filename)
        return True

    def _save_koala(self, filename):
        """
        Save as Koala format
        """
        file_obj = open(filename, "wb")
        file_obj.write("%c%c" % (0x00, 0x60))

        for char in self._data['bitmap']:
            file_obj.write("%c" % char)

        for char in self._data["screen-ram"]:
            file_obj.write("%c" % char)

        for char in self._data["color-ram"]:
            file_obj.write("%c" % char)

        file_obj.write(chr(self._data["background"]))

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
            for char in self._data['bitmap']:
                file_obj.write("%c" % char)

        with open(filename + "_screen.raw", "w") as file_obj:
            for char in self._data["screen-ram"]:
                file_obj.write("%c" % char)

        with open(filename + "_color-ram.raw", "w") as file_obj:
            for char in self._data["color-ram"]:
                file_obj.write("%c" % char)

        with open(filename + "_bg.raw", "w") as file_obj:
            file_obj.write(chr(self._data["background"]))

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

    def _fill_memory(self, pal_map=None):
        """
        Create bitmap/screen and error map as a picture if needed.
        """
        self._data["bitmap"] = []
        self._data["screen-ram"] = []

        error_list = []

        clash = 0

        for chry, chrx in [(chry, chrx)
                           for chry in range(0, self._src_image.size[1], 8)
                           for chrx in range(0, self._src_image.size[0], 8)]:

            box = self._src_image.crop((chrx, chry,
                                        chrx + 8, chry + 8)).convert("RGB")
            char_col = []

            for y__ in range(8):
                line = 0
                for x__ in range(8):
                    colnow = pal_map[box.getpixel((x__, y__))]

                    if colnow not in char_col:
                        char_col.append(colnow)

                    colptr = char_col.index(colnow)
                    line += colptr * 2 ** (7 - x__)

                self._data["bitmap"].append(line)

            if len(char_col) == 1:
                char_col.append(char_col[0])

            self._data["screen-ram"].append(char_col[1] * 16 + char_col[0])
            if len(char_col) > 2:
                clash = 1
                error_list.append((chrx, chry))
                self.log.error("Too many colors per block in char %d, %d near"
                               " x=%d, y=%d.", chrx, chry,
                               chrx * 8 + 4, chry * 8 + 4)

        if clash:
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
        file_obj.write("".join([chr(col) for col in self._data["screen-ram"]]))
        file_obj.write(4120 * chr(0))
        file_obj.write("".join([chr(byte) for byte in self._data["bitmap"]]))
        file_obj.close()
        self.log.info("Saved executable under `%s' file", filename)
        return True

    def _save_ash(self, filename):
        """
        Save as Art Studio hires
        """
        file_obj = open(filename, "wb")
        file_obj.write("%c%c" % (0x00, 0x20))

        for char in self._data['bitmap']:
            file_obj.write("%c" % char)

        for char in self._data["screen-ram"]:
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
                                    for col in self._data["screen-ram"]]))

        with open(filename + "_bitmap.raw", "wb") as file_obj:
            file_obj.write("".join([chr(byte)
                                    for byte in self._data["bitmap"]]))

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


def multiconv(arguments):
    """
    Convert to multicolor picture
    """
    mutli_conv = MultiConverter(arguments.filename, arguments.errors)
    if arguments.border is not None:
        mutli_conv.set_border_color(arguments.border)
    if arguments.background is not None:
        mutli_conv.set_bg_color(arguments.background)
    mutli_conv.log.set_verbose(arguments.verbose, arguments.quiet)

    filename, format_ = resolve_name(arguments)
    mutli_conv.save(filename, format_)


def hiresconv(arguments):
    """
    Convert to hires picture
    """
    hires_conv = HiresConverter(arguments.filename, arguments.errors)
    if arguments.border is not None:
        hires_conv.set_border_color(arguments.border)
    hires_conv.log.set_verbose(arguments.verbose, arguments.quiet)

    filename, format_ = resolve_name(arguments)
    hires_conv.save(filename, format_)


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


def resolve_name(arguments):
    """
    Return right name and format for an output file.
    """
    if arguments.output:
        filename = arguments.output
    else:
        filename = get_modified_fname(arguments.filename, "prg")

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
                        "same filename as original with appropriate extension")
    PARSER.add_argument('filename')

    GROUP = PARSER.add_mutually_exclusive_group()
    GROUP.add_argument("-q", "--quiet", help='please, be quiet. Adding more '
                       '"q" will decrease verbosity', action="count",
                       default=0)
    GROUP.add_argument("-v", "--verbose", help='be verbose. Adding more "v" '
                       'will increase verbosity', action="count", default=0)

    ARGS = PARSER.parse_args()
    F_MAP[ARGS.format](ARGS)
