#!/usr/bin/env python
"""
Tests for c64img.multi module
This is part of the c64img project <https://bitbucket.org/gryf/image2c64>

Author: Roman 'gryf' Dobosz <gryf73@gmail.com>
Licence: BSD
"""
import os
from unittest import TestCase, main
from tempfile import mkstemp

from PIL import Image

from c64img import multi


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

    def critical(*args, **kwargs):
        return

    def getEffectiveLevel(self):
        return 30  # warn


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


class TestMultiChar(TestCase):
    """
    Test multicolor Char class
    """
    def setUp(self):
        """set up"""
        self.log = LogMock()

    def test___init(self):
        """
        Test Char initialization
        """
        char = multi.MultiChar(self.log, {0: (0, 0)})
        self.assertEqual(char.max_colors, 4)
        self.assertEqual(char.pixel_state, {(0, 1): False,
                                            (1, 0): False,
                                            (1, 1): False})

    def test_get_binary_data(self):
        """
        Test get_binary_data method
        """
        char = multi.MultiChar(self.log, {0: (0, 0)})
        char.pixels = {(0, 0): 0, (0, 1): 1, (0, 2): 2, (0, 3): 3,
                       (1, 0): 0, (1, 1): 1, (1, 2): 2, (1, 3): 3}
        char._analyze_color_map()
        result = char.get_binary_data()
        self.assertEqual(result['bitmap'], [57, 0b111001])  # 57 for all
        self.assertEqual(result['screen-ram'], 50)
        self.assertEqual(result['color-ram'], 1)

        # last pixel with the clash - should fall back to background color
        char.pixels = {(0, 0): 0, (0, 1): 1, (0, 2): 2, (0, 3): 3,
                       (1, 0): 0, (1, 1): 1, (1, 2): 2, (1, 3): 3,
                       (2, 0): 0, (2, 1): 1, (2, 2): 2, (2, 3): 3,
                       (3, 0): 0, (3, 1): 1, (3, 2): 2, (3, 3): 3,
                       (4, 0): 0, (4, 1): 1, (4, 2): 2, (4, 3): 3,
                       (5, 0): 0, (5, 1): 1, (5, 2): 2, (5, 3): 3,
                       (6, 0): 0, (6, 1): 1, (6, 2): 2, (6, 3): 3,
                       (7, 0): 0, (7, 1): 1, (7, 2): 2, (7, 3): 9}
        result = char.get_binary_data()
        self.assertEqual(result['bitmap'], [57, 57, 57, 57, 57, 57, 57,
                                            0b111000])
        self.assertEqual(result['screen-ram'], 50)
        self.assertEqual(result['color-ram'], 1)

    def test_analyze_color_map(self):
        """
        Test _analyze_color_map method
        """
        char = multi.MultiChar(self.log, {0: (0, 0)})
        # simulate clash
        char.max_colors = 1
        char.pixels[(0, 0)] = 1
        char.pixels[(0, 1)] = 2
        char._analyze_color_map()
        self.assertEqual(char.colors[0], (0, 0))

        # simulate previous image clash
        char.clash = False
        char.max_colors = 2
        char.prev = multi.MultiChar(self.log, {0: (0, 0)})
        char.prev.clash = True
        char._analyze_color_map()
        self.assertEqual(char.colors[0], (0, 0))
        self.assertEqual(len(char.colors), 1)

    def test__compare_colors_with_prev_char(self):
        """
        Test _compare_colors_with_prev_char method. This method is responsible
        for creating new mapping for multicolor bit pairs in conjunction with
        corresponding colors.
        """
        char = multi.MultiChar(self.log, {0: (0, 0)})
        colors = {0: 16,
                  1: 4,
                  2: 5,
                  3: 7}

        # The default case. No previous picture stored, no colors to compare
        # with. None colors were stored.
        self.assertTrue(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pixel_state, {(1, 0): False,
                                            (0, 1): False,
                                            (1, 1): False})
        self.assertEqual(char.colors, {})

        # So it needs to rerun, colors are recognized and remembered.
        self.assertFalse(char._compare_colors_with_prev_char(colors, True))
        self.assertEqual(char.pixel_state, {(1, 0): True,
                                            (0, 1): True,
                                            (1, 1): True})
        self.assertEqual(char.colors, {1: (0, 1), 2: (1, 0), 3: (1, 1)})

        # 1. Ideal case. Colors for previous and current character in char
        # boundary are the same. No need to rerun checks.
        char = multi.MultiChar(self.log, {0: (0, 0)})
        prev = multi.MultiChar(self.log, {0: (0, 0)})
        prev.colors = {1: (0, 1), 2: (1, 0), 3: (1, 1)}
        char.prev = prev
        self.assertFalse(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pixel_state, {(1, 0): True,
                                            (0, 1): True,
                                            (1, 1): True})
        self.assertEqual(char.colors, {1: (0, 1), 2: (1, 0), 3: (1, 1)})

        # 2. Mixed colors/pixel pairs. Color indices are matching fine. Colors
        # and pairs from previous character should be propagated into current
        # char.
        char = multi.MultiChar(self.log, {0: (0, 0)})
        prev = multi.MultiChar(self.log, {0: (0, 0)})
        prev.colors = {3: (0, 1), 1: (1, 0), 2: (1, 1)}
        char.prev = prev
        self.assertFalse(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pixel_state, {(1, 0): True,
                                            (0, 1): True,
                                            (1, 1): True})
        self.assertEqual(char.colors, {3: (0, 1), 1: (1, 0), 2: (1, 1)})

        # 3. Mixed colors/pixel pairs. One color index differ. Colors and
        # pairs from previous character should be propagated into current
        # char, the mismatch color should be replaced by current one.
        char = multi.MultiChar(self.log, {0: (0, 0)})
        prev = multi.MultiChar(self.log, {0: (0, 0)})
        prev.colors = {3: (0, 1), 4: (1, 0), 2: (1, 1)}
        char.prev = prev
        self.assertTrue(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pixel_state, {(1, 0): False,
                                            (0, 1): True,
                                            (1, 1): True})
        self.assertEqual(char.colors, {3: (0, 1), 2: (1, 1)})
        self.assertFalse(char._compare_colors_with_prev_char(colors, True))
        self.assertEqual(char.pixel_state, {(1, 0): True,
                                            (0, 1): True,
                                            (1, 1): True})
        self.assertEqual(char.colors, {3: (0, 1), 2: (1, 1), 1: (1, 0)})

        # 4. Mixed colors/pixel pairs. One color index match. Colors and
        # pairs from previous character should be propagated into current
        # char, the mismatch colors should be replaced by current ones.
        char = multi.MultiChar(self.log, {0: (0, 0)})
        prev = multi.MultiChar(self.log, {6: (0, 0)})
        prev.colors = {4: (0, 1), 3: (1, 0), 5: (1, 1)}
        char.prev = prev
        self.assertTrue(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pixel_state, {(1, 0): True,
                                            (0, 1): False,
                                            (1, 1): False})
        self.assertEqual(char.colors, {3: (1, 0)})
        self.assertFalse(char._compare_colors_with_prev_char(colors, True))
        self.assertEqual(char.pixel_state, {(1, 0): True,
                                            (0, 1): True,
                                            (1, 1): True})
        self.assertEqual(char.colors, {3: (1, 0), 1: (0, 1), 2: (1, 1)})

        # 5. Worst case scenario. None of the colors from previous char
        # matches. Get the current colors.
        char = multi.MultiChar(self.log, {0: (0, 0)})
        prev = multi.MultiChar(self.log, {6: (0, 0)})
        prev.colors = {4: (0, 1), 5: (1, 0), 6: (1, 1)}
        char.prev = prev
        self.assertTrue(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pixel_state, {(1, 0): False,
                                            (0, 1): False,
                                            (1, 1): False})
        self.assertEqual(char.colors, {})
        self.assertFalse(char._compare_colors_with_prev_char(colors, True))
        self.assertEqual(char.pixel_state, {(1, 0): True,
                                            (0, 1): True,
                                            (1, 1): True})
        self.assertEqual(char.colors, {1: (0, 1), 2: (1, 0), 3: (1, 1)})

    def test__fix_color_clash(self):
        """Test for repait color clash"""
        bg = 0  # black
        col1 = 1  # white
        col2 = 2  # red
        col3 = 3  # magenta
        clash = 4  # purple

        char = multi.MultiChar(self.log, {bg: (0, 0)}, prev=None,
                               fix_clash=True)

        char.pixels = {(0, 0): bg, (0, 1): col1, (0, 2): col2, (0, 3): col3,
                       (1, 0): bg, (1, 1): col1, (1, 2): col2, (1, 3): col3,
                       (2, 0): bg, (2, 1): col1, (2, 2): col2, (2, 3): col3,
                       (3, 0): bg, (3, 1): col1, (3, 2): col2, (3, 3): col3,
                       (4, 0): bg, (4, 1): col1, (4, 2): col2, (4, 3): col3,
                       (5, 0): bg, (5, 1): col1, (5, 2): col2, (5, 3): col3,
                       (6, 0): bg, (6, 1): col1, (6, 2): col2, (6, 3): col3,
                       (7, 0): bg, (7, 1): col1, (7, 2): col2, (7, 3): clash}

        char._analyze_color_map()
        self.assertEqual(char.pixels[(7, 3)], col2)

        c1 = 3  # magenta
        c2 = 4  # purple
        c3 = 5  # green
        c4 = 6  # d.blue

        char = multi.MultiChar(self.log, {bg: (0, 0)}, prev=None,
                               fix_clash=True)
        char.pixels = {(0, 0): c1, (0, 1): c2, (0, 2): c3, (0, 3): c4,
                       (1, 0): c1, (1, 1): c2, (1, 2): c3, (1, 3): c4,
                       (2, 0): c1, (2, 1): c2, (2, 2): c3, (2, 3): c4,
                       (3, 0): c1, (3, 1): c2, (3, 2): c3, (3, 3): c4,
                       (4, 0): c1, (4, 1): c2, (4, 2): c3, (4, 3): c4,
                       (5, 0): c1, (5, 1): c2, (5, 2): c3, (5, 3): c4,
                       (6, 0): c1, (6, 1): c2, (6, 2): c3, (6, 3): c4,
                       (7, 0): c1, (7, 1): c2, (7, 2): c3, (7, 3): c4}

        char._analyze_color_map()
        for idx in range(8):
            self.assertEqual(char.pixels[(idx, 0)], c1)
            self.assertEqual(char.pixels[(idx, 1)], c2)
            self.assertEqual(char.pixels[(idx, 2)], c3)
            self.assertEqual(char.pixels[(idx, 3)], bg)

        c1 = 1  # white - clash
        c2 = 2  # red
        c3 = 5  # green
        c4 = 3  # magenta

        char = multi.MultiChar(self.log, {bg: (0, 0)}, prev=None,
                               fix_clash=True)
        char.pixels = {(0, 0): c1, (0, 1): c2, (0, 2): c3, (0, 3): c4,
                       (1, 0): c1, (1, 1): c2, (1, 2): c3, (1, 3): c4,
                       (2, 0): c1, (2, 1): c2, (2, 2): c3, (2, 3): c4,
                       (3, 0): bg, (3, 1): c2, (3, 2): c3, (3, 3): c4,
                       (4, 0): bg, (4, 1): c2, (4, 2): c3, (4, 3): c4,
                       (5, 0): bg, (5, 1): c2, (5, 2): c3, (5, 3): c4,
                       (6, 0): bg, (6, 1): c2, (6, 2): c3, (6, 3): c4,
                       (7, 0): bg, (7, 1): c2, (7, 2): c3, (7, 3): c4}

        char._analyze_color_map()
        for idx in range(8):
            self.assertEqual(char.pixels[(idx, 0)], bg)
            self.assertEqual(char.pixels[(idx, 1)], c2)
            self.assertEqual(char.pixels[(idx, 2)], c3)
            self.assertEqual(char.pixels[(idx, 3)], c4)


class TestMulticolor(TestCase):
    """
    Tests for multicolor conversion
    """
    def test__check_dimensions(self):
        """
        Test of dimensions of the input images
        """
        for fname in (CROP_V, CROP_H, CROP_BOTH):
            obj = multi.MultiConverter(fname)
            obj.log.error = lambda *x: None  # suppress log
            obj._load()
            self.assertFalse(obj._check_dimensions())

        for fname in (CLASH_H, CLASH_M, COLORS_256, COLORS_1, COLORS_2,
                      COLORS_256_U16, HIRES, MULTI_320, CLASH_M2, MULTI,
                      PAL_PEPTO, PAL_TIMANTHES, PAL_UNKNOWN, PAL_VICE):
            obj = multi.MultiConverter(fname)
            obj._load()
            self.assertTrue(obj._check_dimensions(), fname)

    def test__load(self):
        """
        Test custom load function
        """
        obj = multi.MultiConverter(MULTI)
        self.assertEqual(obj._load(), True)
        self.assertEqual(obj._src_image.size[0], 160)

        obj = multi.MultiConverter(MULTI_320)
        self.assertEqual(obj._load(), True)
        self.assertEqual(obj._src_image.size[0], 160)

        obj = multi.MultiConverter("nofile")
        obj.log = LogMock()
        self.assertEqual(obj._load(), False)
        self.assertEqual(obj._src_image, None)

    def test_save(self):
        """
        Test for save methods
        """
        fdesc, fname = mkstemp(suffix=".prg")
        os.close(fdesc)
        os.unlink(fname)

        obj = multi.MultiConverter(MULTI_320)
        self.assertEqual(obj.save(fname, "prg"), 0)

        self.assertTrue(os.path.exists(fname))
        self.assertEqual(os.stat(fname).st_size, 14145)
        os.unlink(fname)

        fdesc, fname = mkstemp(suffix=".prg")
        os.close(fdesc)
        os.unlink(fname)

        obj = multi.MultiConverter(MULTI)
        self.assertEqual(obj.save(fname, "koala"), 0)

        self.assertTrue(os.path.exists(fname))
        self.assertEqual(os.stat(fname).st_size, 10004)
        os.unlink(fname)

        obj = multi.MultiConverter(CLASH_M)
        self.assertEqual(obj.save(fname, "koala"), 1)

        obj = multi.MultiConverter(CLASH_M2)
        self.assertEqual(obj.save(fname, "koala"), 1)

        obj = multi.MultiConverter(MULTI)
        self.assertEqual(obj.save(fname, "raw"), 0)

        self.assertTrue(os.path.exists(fname + "_bg.raw"))
        self.assertTrue(os.path.exists(fname + "_bitmap.raw"))
        self.assertTrue(os.path.exists(fname + "_color-ram.raw"))
        self.assertTrue(os.path.exists(fname + "_screen.raw"))

        self.assertEqual(os.stat(fname + "_bg.raw").st_size, 1)
        self.assertEqual(os.stat(fname + "_bitmap.raw").st_size, 8000)
        self.assertEqual(os.stat(fname + "_color-ram.raw").st_size, 1000)
        self.assertEqual(os.stat(fname + "_screen.raw").st_size, 1000)
        os.unlink(fname + "_bg.raw")
        os.unlink(fname + "_bitmap.raw")
        os.unlink(fname + "_color-ram.raw")
        os.unlink(fname + "_screen.raw")

        obj = multi.MultiConverter(CLASH_M)
        self.assertEqual(obj.save(fname, "raw"), 1)

        obj = multi.MultiConverter(CLASH_M2)
        self.assertEqual(obj.save(fname, "raw"), 1)


if __name__ == "__main__":
    main()
