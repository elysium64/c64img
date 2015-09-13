#!/usr/bin/env python
"""
Tests for c64img.hires module
This is part of the c64img project <https://bitbucket.org/gryf/image2c64>

Author: Roman 'gryf' Dobosz <gryf73@gmail.com>
Licence: BSD
"""
import os
from unittest import TestCase, main
from tempfile import mkstemp

from PIL import Image

from c64img import hires


Image.Image.show = lambda x: None


def get_image_path(image_name):
    return os.path.join(os.path.dirname(__file__), "test_images", image_name)


CLASH_H = get_image_path("clash.hires.png")
CLASH_M = get_image_path("clash.multi.png")
CLASH_M2 = get_image_path("clash.multi.160.png")
COLORS_256 = get_image_path("colors.256.png")
PAL_PEPTO = get_image_path("colors.pepto.png")
PAL_TIMANTHES = get_image_path("colors.timanthes.png")
PAL_UNKNOWN = get_image_path("colors.unknown.png")
PAL_VICE = get_image_path("colors.vice.png")
CROP_BOTH = get_image_path("crop.251x187.png")
CROP_H = get_image_path("crop.319x200.png")
CROP_V = get_image_path("crop.320x199.png")
COLORS_1 = get_image_path("hires_1c.png")
COLORS_2 = get_image_path("hires_2c.png")
COLORS_256_U16 = get_image_path("hires_256_16p.png")  # 256 defined, uniq 16
HIRES = get_image_path("hires.png")
MULTI = get_image_path("multi.160x200.png")
MULTI_320 = get_image_path("multi.320x200.png")


class LogMock(object):
    """Mock logger class"""

    def warning(*args, **kwargs):
        return

    def debug(*args, **kwargs):
        return


class Interceptor(object):
    """
    Interceptor class for function call detection
    """
    def __init__(self):
        """
        Init.
        """
        self.call = 0
        self.repeat = False

    def __call__(self, dummy1, dummy2=False):
        """
        Call attribute is increased every time, instance is called
        """
        self.call += 1
        return self.repeat


class TestHiresChar(TestCase):
    """
    Test hires Char class
    """
    def setUp(self):
        """set up"""
        self.log = LogMock()

    def test_get_binary_data(self):
        """
        Test get_binary_data method
        """
        char = hires.HiresChar(self.log)
        char.pixels = {(0, 0): 1, (0, 1): 0, (0, 2): 1, (0, 3): 0,
                       (0, 4): 0, (0, 5): 1, (0, 6): 0, (0, 7): 1}
        char._analyze_color_map()
        result = char.get_binary_data()
        self.assertEqual(result['bitmap'], [0b10100101])
        self.assertEqual(result['screen-ram'], 0x10)

        # last pixel with the clash - should fall back to background color
        char.pixels = {(0, 0): 1, (0, 1): 0, (0, 2): 1, (0, 3): 0,
                       (0, 4): 0, (0, 5): 1, (0, 6): 0, (0, 7): 1,
                       (1, 0): 1, (1, 1): 0, (1, 2): 1, (1, 3): 0,
                       (1, 4): 0, (1, 5): 1, (1, 6): 0, (1, 7): 1,
                       (2, 0): 1, (2, 1): 0, (2, 2): 1, (2, 3): 0,
                       (2, 4): 0, (2, 5): 1, (2, 6): 0, (2, 7): 1,
                       (3, 0): 1, (3, 1): 0, (3, 2): 1, (3, 3): 0,
                       (3, 4): 0, (3, 5): 1, (3, 6): 0, (3, 7): 1,
                       (4, 0): 1, (4, 1): 0, (4, 2): 1, (4, 3): 0,
                       (4, 4): 0, (4, 5): 1, (4, 6): 0, (4, 7): 1,
                       (5, 0): 1, (5, 1): 0, (5, 2): 1, (5, 3): 0,
                       (5, 4): 0, (5, 5): 1, (5, 6): 0, (5, 7): 1,
                       (6, 0): 1, (6, 1): 0, (6, 2): 1, (6, 3): 0,
                       (6, 4): 0, (6, 5): 1, (6, 6): 0, (6, 7): 1,
                       (7, 0): 1, (7, 1): 0, (7, 2): 1, (7, 3): 0,
                       (7, 4): 0, (7, 5): 1, (7, 6): 0, (7, 7): 2}
        char._fix_clash = True
        char._analyze_color_map()
        result = char.get_binary_data()
        self.assertEqual(result['bitmap'], [165, 165, 165, 165, 165, 165, 165,
                                            0b10100100])
        self.assertEqual(result['screen-ram'], 0x10)

    def test__compare_colors_with_prev_char(self):
        """
        Test _compare_colors_with_prev_char method. This method is responsible
        for creating new mapping for multicolor bit pairs in conjunction with
        corresponding colors.
        """
        char = hires.HiresChar(self.log)
        colors = {8: 50, 9: 14}

        # The default case. No previous picture stored, no colors to compare
        # with. None colors were stored.
        self.assertTrue(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pixel_state, {0: False, 1: False})
        self.assertEqual(char.colors, {})

        # So it needs to rerun, colors are recognized and remembered.
        self.assertFalse(char._compare_colors_with_prev_char(colors, True))
        self.assertEqual(char.pixel_state, {0: True, 1: True})
        self.assertEqual(char.colors, {8: 0, 9: 1})

        # 1. Ideal case. Colors for previous and current character in char
        # boundary are the same. No need to rerun checks.
        char = hires.HiresChar(self.log)
        prev = hires.HiresChar(self.log)
        prev.colors = {8: 0, 9: 1}
        char.prev = prev
        self.assertFalse(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pixel_state, {0: True, 1: True})
        self.assertEqual(char.colors, {8: 0, 9: 1})

        # 2. Mixed colors/pixel pairs. Color indices are matching fine. Colors
        # and pairs from previous character should be propagated into current
        # char.
        char = hires.HiresChar(self.log)
        prev = hires.HiresChar(self.log)
        prev.colors = {9: 1, 8: 0}
        char.prev = prev
        self.assertFalse(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pixel_state, {0: True, 1: True})
        self.assertEqual(char.colors, {9: 1, 8: 0})

        # 3. Mixed colors/pixel pairs. One color index differ. Tho other color
        # from previous character should be propagated into current char,
        # the mismatch color should be replaced by current one.
        char = hires.HiresChar(self.log)
        prev = hires.HiresChar(self.log)
        prev.colors = {5: 1, 9: 0}
        char.prev = prev
        self.assertTrue(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pixel_state, {0: True, 1: False})
        self.assertEqual(char.colors, {9: 0})
        self.assertFalse(char._compare_colors_with_prev_char(colors, True))
        self.assertEqual(char.pixel_state, {0: True, 1: True})
        self.assertEqual(char.colors, {9: 0, 8: 1})

        # 5. Worst case scenario. None of the colors from previous char
        # matches. Get the current colors.
        char = hires.HiresChar(self.log)
        prev = hires.HiresChar(self.log)
        prev.colors = {5: 1, 6: 0}
        char.prev = prev
        self.assertTrue(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pixel_state, {0: False, 1: False})
        self.assertEqual(char.colors, {})
        self.assertFalse(char._compare_colors_with_prev_char(colors, True))
        self.assertEqual(char.pixel_state, {0: True, 1: True})
        self.assertEqual(char.colors, {9: 1, 8: 0})

    def test__fix_color_clash(self):
        """Test for repait color clash"""
        char = hires.HiresChar(self.log, prev=None, fix_clash=True)
        char.pixels = {(0, 0): 2, (0, 1): 1, (0, 2): 1, (0, 3): 7,
                       (0, 4): 2, (0, 5): 2, (0, 6): 3, (0, 7): 4}
        char._analyze_color_map()
        self.assertEqual(char.pixels,
                         {(0, 0): 2, (0, 1): 1, (0, 2): 1, (0, 3): 1,
                          (0, 4): 2, (0, 5): 2, (0, 6): 2, (0, 7): 2})


class TestHires(TestCase):
    """
    Tests for hires conversion
    """

    def test__check_dimensions(self):
        """
        Test of dimensions of the input images
        """
        for fname in (CROP_V, CROP_H, CROP_BOTH, CLASH_M2, MULTI, PAL_PEPTO,
                      PAL_TIMANTHES, PAL_UNKNOWN, PAL_VICE):
            obj = hires.HiresConverter(fname)
            obj.log.error = lambda *x: None  # suppress log
            obj._load()
            self.assertFalse(obj._check_dimensions())

        for fname in (CLASH_H, CLASH_M, COLORS_256, COLORS_1, COLORS_2,
                      COLORS_256_U16, HIRES, MULTI_320):
            obj = hires.HiresConverter(fname)
            obj._load()
            self.assertTrue(obj._check_dimensions())

    def test__fill_memory(self):
        """
        Test for _fill_memory method
        """
        obj = hires.HiresConverter(HIRES)
        obj._load()
        hist = obj._src_image.histogram()
        obj._colors_check(hist)
        obj._find_best_palette_map()
        obj._find_most_freq_color(hist)
        self.assertEqual(obj._fill_memory(), True)

        obj = hires.HiresConverter(COLORS_1)
        obj._load()
        hist = obj._src_image.histogram()
        obj.log.warn = lambda x, y: None  # suppress log
        obj._colors_check(hist)
        obj._find_best_palette_map()
        obj._find_most_freq_color(hist)
        self.assertEqual(obj._fill_memory(), True)

        obj = hires.HiresConverter(CLASH_H)
        obj._load()
        hist = obj._src_image.histogram()
        obj._colors_check(hist)
        obj._find_best_palette_map()
        obj._find_most_freq_color(hist)
        self.assertEqual(obj._fill_memory(), False)

    def test__get_displayer(self):
        """
        Test for _get_displayer method
        """
        obj = hires.HiresConverter(HIRES)
        border = chr(0)
        displayer = ["\x01\x08\x0b\x08\x0a\x00\x9e\x32\x30\x36\x34\x00"
                     "\x00\x00\x00\x00\x00\x78\xa9", border, "\x8d\x20\xd0\xa9"
                     "\x00\x8d\x21\xd0\xa9\xbb\x8d\x11\xd0\xa9\x3c\x8d"
                     "\x18\xd0\x4c\x25\x08"]
        self.assertEqual(obj._get_displayer(), "".join(displayer))
        border = chr(10)
        displayer[1] = border
        obj.set_border_color(10)
        self.assertEqual(obj._get_displayer(), "".join(displayer))

    def test_save(self):
        """
        Test for save method (and all _save... submethods)
        """
        fdesc, fname = mkstemp(suffix=".prg")
        os.close(fdesc)

        obj = hires.HiresConverter(HIRES)
        obj.log.warning = lambda *x: None  # suppress log
        self.assertEqual(obj.save(fname, "prg"), 0)

        self.assertTrue(os.path.exists(fname))
        self.assertEqual(os.stat(fname).st_size, 14145)
        os.unlink(fname)

        fdesc, fname = mkstemp(suffix=".prg")
        os.close(fdesc)

        obj = hires.HiresConverter(HIRES)
        obj.log.warning = lambda *x: None  # suppress log
        self.assertEqual(obj.save(fname, "art-studio-hires"), 0)

        self.assertTrue(os.path.exists(fname))
        self.assertEqual(os.stat(fname).st_size, 9009)
        os.unlink(fname)

        obj = hires.HiresConverter(CLASH_H)
        self.assertEqual(obj.save(fname, "art-studio-hires"), 1)

        obj = hires.HiresConverter(HIRES)
        self.assertEqual(obj.save(fname, "raw"), 0)

        self.assertTrue(os.path.exists(fname + "_bitmap.raw"))
        self.assertTrue(os.path.exists(fname + "_screen.raw"))

        self.assertEqual(os.stat(fname + "_bitmap.raw").st_size, 8000)
        self.assertEqual(os.stat(fname + "_screen.raw").st_size, 1000)
        os.unlink(fname + "_bitmap.raw")
        os.unlink(fname + "_screen.raw")


if __name__ == "__main__":
    main()
