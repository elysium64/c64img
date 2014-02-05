#!/usr/bin/env python
"""
Tests for Image2c64 <https://bitbucket.org/gryf/image2c64>

Author: Roman 'gryf' Dobosz <gryf73@gmail.com>
Date: 2012-11-20
Version: 1.3
Licence: BSD
"""
import os
from unittest import TestCase, main
import logging
from tempfile import mkstemp

from PIL import Image
Image.Image.show = lambda x: None

import image2c64

CLASH_H = "test_images/clash.hires.png"
CLASH_M = "test_images/clash.multi.png"
CLASH_M2 = "test_images/clash.multi.160.png"
COLORS_256 = "test_images/colors.256.png"
PAL_PEPTO = "test_images/colors.pepto.png"
PAL_TIMANTHES = "test_images/colors.timanthes.png"
PAL_UNKNOWN = "test_images/colors.unknown.png"
PAL_VICE = "test_images/colors.vice.png"
CROP_BOTH = "test_images/crop.251x187.png"
CROP_H = "test_images/crop.319x200.png"
CROP_V = "test_images/crop.320x199.png"
COLORS_1 = "test_images/hires_1c.png"
COLORS_2 = "test_images/hires_2c.png"
COLORS_256_U16 = "test_images/hires_256_16p.png"  # 256 defined, uniq 16
HIRES = "test_images/hires.png"
MULTI = "test_images/multi.160x200.png"
MULTI_320 = "test_images/multi.320x200.png"


class TestChar(TestCase):
    """
    Test Char class
    """
    def test___init(self):
        """
        Test Char initialization
        """
        self.assertRaises(TypeError, image2c64.Char)

        char = image2c64.Char(0)
        self.assertEqual(char.background, 0)
        self.assertEqual(char.clash, False)
        self.assertEqual(char.colors, {})
        self.assertEqual(char.max_colors, 2)
        self.assertEqual(char.pixels, {})
        self.assertEqual(char.prev, None)

        char = image2c64.Char(1, "foo")
        self.assertEqual(char.background, 1)
        self.assertEqual(char.prev, "foo")

    def test_analyze_color_map(self):
        """
        Test analyze_color_map method
        """
        char = image2c64.Char(0)
        # simulate clash
        char.max_colors = 1
        char.pixels[(0, 0)] = 1
        char.pixels[(0, 1)] = 2
        char.analyze_color_map()
        self.assertEqual(char.colors[0], (0, 0))

        # simulate previous image clash
        char.clash = False
        char.max_colors = 2
        char.prev = image2c64.Char(0)
        char.prev.clash = True
        char.analyze_color_map()
        self.assertEqual(char.colors[0], (0, 0))
        self.assertEqual(len(char.colors), 1)

        # finally, not implemented error caused by other method
        char.prev = None
        char.clash = False
        self.assertRaises(NotImplementedError, char.analyze_color_map)

    def test_get_binary_data(self):
        """
        Test get_binary_data method
        """
        char = image2c64.Char(0)
        self.assertRaises(NotImplementedError, char.get_binary_data)

    def test__check_clash(self):
        """
        Test _check_clash method
        """
        char = image2c64.Char(0)
        self.assertEqual(char._check_clash(), False)

    def test__compare_colors(self):
        """
        Test _compare_colors method
        """
        char = image2c64.Char(0)
        self.assertRaises(TypeError, char._compare_colors)
        self.assertRaises(NotImplementedError, char._compare_colors, None)


class TestMultiChar(TestCase):
    """
    Test Multicolor Char class
    """
    def test___init(self):
        """
        Test Char initialization
        """
        char = image2c64.MultiChar(0)
        self.assertEqual(char.max_colors, 4)
        self.assertEqual(char.pairs, {(0, 1): False,
                                      (1, 0): False,
                                      (1, 1): False})

    def test_get_binary_data(self):
        """
        Test get_binary_data method
        """
        char = image2c64.MultiChar(0)
        char.pixels = {(0, 0): 0, (0, 1): 1, (0, 2): 2, (0, 3): 3,
                       (1, 0): 0, (1, 1): 1, (1, 2): 2, (1, 3): 3}
        char.analyze_color_map()
        result = char.get_binary_data()
        self.assertEqual(result['bitmap'], [27, 0b011011])  # 27 for all
        self.assertEqual(result['screen-ram'], 18)
        self.assertEqual(result['color-ram'], 3)

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
        self.assertEqual(result['bitmap'], [27, 27, 27, 27, 27, 27, 27,
                                            0b011000])
        self.assertEqual(result['screen-ram'], 18)
        self.assertEqual(result['color-ram'], 3)

    def test__compare_colors(self):
        """
        Test _compare_colors method
        """
        class Interceptor(object):
            def __init__(self):
                self.call = 0
                self.repeat = False

            def __call__(self, dummy1, dummy2=False):
                self.call += 1
                return self.repeat

        iceptor = Interceptor()
        char = image2c64.MultiChar(0)
        char._compare_colors_with_prev_char = iceptor
        char._compare_colors(None)
        self.assertEqual(iceptor.call, 1)

        iceptor.repeat = True
        char._compare_colors(None)
        self.assertEqual(iceptor.call, 3)

    def test__compare_colors_with_prev_char(self):
        """
        Test _compare_colors_with_prev_char method. This method is responsible
        for creating new mapping for multicolor bit pairs in conjunction with
        corresponding colors.
        """
        char = image2c64.MultiChar(0)
        colors = {0: 16,
                  1: 4,
                  2: 5,
                  3: 7}

        # The default case. No previous picture stored, no colors to compare
        # with. None colors were stored.
        self.assertTrue(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pairs, {(1, 0): False,
                                      (0, 1): False,
                                      (1, 1): False})
        self.assertEqual(char.colors, {})

        # So it needs to rerun, colors are recognized and remembered.
        self.assertFalse(char._compare_colors_with_prev_char(colors, True))
        self.assertEqual(char.pairs, {(1, 0): True,
                                      (0, 1): True,
                                      (1, 1): True})
        self.assertEqual(char.colors, {1: (0, 1), 2: (1, 0), 3: (1, 1)})

        # 1. Ideal case. Colors for previous and current character in char
        # boundary are the same. No need to rerun checks.
        char = image2c64.MultiChar(0)
        prev = image2c64.MultiChar(0)
        prev.colors = {1: (0, 1), 2: (1, 0), 3: (1, 1)}
        char.prev = prev
        self.assertFalse(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pairs, {(1, 0): True,
                                      (0, 1): True,
                                      (1, 1): True})
        self.assertEqual(char.colors, {1: (0, 1), 2: (1, 0), 3: (1, 1)})

        # 2. Mixed colors/pixel pairs. Color indices are matching fine. Colors
        # and pairs from previous character should be propagated into current
        # char.
        char = image2c64.MultiChar(0)
        prev = image2c64.MultiChar(0)
        prev.colors = {3: (0, 1), 1: (1, 0), 2: (1, 1)}
        char.prev = prev
        self.assertFalse(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pairs, {(1, 0): True,
                                      (0, 1): True,
                                      (1, 1): True})
        self.assertEqual(char.colors, {3: (0, 1), 1: (1, 0), 2: (1, 1)})

        # 2. Mixed colors/pixel pairs. Color indices are matching fine. Colors
        # and pairs from previous character should be propagated into current
        # char.
        char = image2c64.MultiChar(0)
        prev = image2c64.MultiChar(0)
        prev.colors = {3: (0, 1), 1: (1, 0), 2: (1, 1)}
        char.prev = prev
        self.assertFalse(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pairs, {(1, 0): True,
                                      (0, 1): True,
                                      (1, 1): True})
        self.assertEqual(char.colors, {3: (0, 1), 1: (1, 0), 2: (1, 1)})

        # 3. Mixed colors/pixel pairs. One color index differ. Colors and
        # pairs from previous character should be propagated into current
        # char, the mismatch color should be replaced by current one.
        char = image2c64.MultiChar(0)
        prev = image2c64.MultiChar(0)
        prev.colors = {3: (0, 1), 4: (1, 0), 2: (1, 1)}
        char.prev = prev
        self.assertTrue(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pairs, {(1, 0): False,
                                      (0, 1): True,
                                      (1, 1): True})
        self.assertEqual(char.colors, {3: (0, 1), 2: (1, 1)})
        self.assertFalse(char._compare_colors_with_prev_char(colors, True))
        self.assertEqual(char.pairs, {(1, 0): True,
                                      (0, 1): True,
                                      (1, 1): True})
        self.assertEqual(char.colors, {3: (0, 1), 2: (1, 1), 1: (1, 0)})

        # 4. Mixed colors/pixel pairs. One color index match. Colors and
        # pairs from previous character should be propagated into current
        # char, the mismatch colors should be replaced by current ones.
        char = image2c64.MultiChar(0)
        prev = image2c64.MultiChar(6)
        prev.colors = {4: (0, 1), 3: (1, 0), 5: (1, 1)}
        char.prev = prev
        self.assertTrue(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pairs, {(1, 0): True,
                                      (0, 1): False,
                                      (1, 1): False})
        self.assertEqual(char.colors, {3: (1, 0)})
        self.assertFalse(char._compare_colors_with_prev_char(colors, True))
        self.assertEqual(char.pairs, {(1, 0): True,
                                      (0, 1): True,
                                      (1, 1): True})
        self.assertEqual(char.colors, {3: (1, 0), 1: (0, 1), 2: (1, 1)})

        # 5. Worst case scenario. None of the colors from previous char
        # matches. Get the current colors.
        char = image2c64.MultiChar(0)
        prev = image2c64.MultiChar(6)
        prev.colors = {4: (0, 1), 5: (1, 0), 6: (1, 1)}
        char.prev = prev
        self.assertTrue(char._compare_colors_with_prev_char(colors))
        self.assertEqual(char.pairs, {(1, 0): False,
                                      (0, 1): False,
                                      (1, 1): False})
        self.assertEqual(char.colors, {})
        self.assertFalse(char._compare_colors_with_prev_char(colors, True))
        self.assertEqual(char.pairs, {(1, 0): True,
                                      (0, 1): True,
                                      (1, 1): True})
        self.assertEqual(char.colors, {1: (0, 1), 2: (1, 0), 3: (1, 1)})


class TestLogger(TestCase):
    """
    Test Logger class
    """
    def test___init(self):
        """
        Test logger object creation
        """
        log = image2c64.Logger("foo")
        self.assertTrue(isinstance(log, image2c64.Logger))
        # since logger.Logging is mocked here we will have DummyLogger
        # instance
        self.assertTrue(isinstance(log(), logging.Logger))  # DummyLogger))
        self.assertEqual(log().handlers[0].name, 'console')

    def test__setup_logger(self):
        """
        Test setup logger method
        """
        log = image2c64.Logger("foo")
        self.assertEqual(len(log().handlers), 1)
        log.setup_logger()
        self.assertEqual(len(log().handlers), 1)
        self.assertEqual(log().handlers[0].name, 'console')
        self.assertEqual(log().getEffectiveLevel(), logging.WARNING)

    def test_set_verbose(self):
        """
        Test for changing verbosity level
        """
        log = image2c64.Logger("foo")()

        # Default levels are set to 0, which means only warnings are visible
        log.set_verbose(0, 0)
        self.assertEqual(log.getEffectiveLevel(), logging.WARNING)

        # more verbose
        log.set_verbose(1, 0)
        self.assertEqual(log.getEffectiveLevel(), logging.INFO)

        # even more verbose
        log.set_verbose(2, 0)
        self.assertEqual(log.getEffectiveLevel(), logging.DEBUG)

        # further verbosity doesn't make sense
        log.set_verbose(5, 0)
        self.assertEqual(log.getEffectiveLevel(), logging.DEBUG)

        # less verbose
        log.set_verbose(0, 1)
        self.assertEqual(log.getEffectiveLevel(), logging.ERROR)

        # even less verbose
        log.set_verbose(0, 2)
        self.assertEqual(log.getEffectiveLevel(), logging.CRITICAL)

        # smaller verbosity doesn't make sense
        log.set_verbose(0, 5)
        self.assertEqual(log.getEffectiveLevel(), logging.CRITICAL)

        # even though both values cannot be set at the same time (argparse
        # module is taking care about that), verbosity takes precedence over
        # quietness.
        log.set_verbose(5, 5)
        self.assertEqual(log.getEffectiveLevel(), logging.DEBUG)


class TestFullScreenImage(TestCase):
    """
    Test FullScreenImage class
    """
    def test___init(self):
        """
        Test initialization
        """
        self.assertRaises(TypeError, image2c64.FullScreenImage)
        obj = image2c64.FullScreenImage(MULTI_320)
        self.assertEqual(obj._fname, MULTI_320)
        self.assertEqual(obj._errors_action, "none")
        self.assertEqual(obj._src_image, None)
        self.assertTrue(isinstance(obj.log, logging.Logger))
        self.assertEqual(obj.data, {})

    def test__check_dimensions(self):
        """
        Test of dimensions of the input images
        """
        for fname in (CROP_V, CROP_H, CROP_BOTH, CLASH_M2, MULTI, PAL_PEPTO,
                      PAL_TIMANTHES, PAL_UNKNOWN, PAL_VICE):
            obj = image2c64.FullScreenImage(fname)
            obj.log.error = lambda *x: None  # suppress log
            obj._load()
            self.assertFalse(obj._check_dimensions())

        for fname in (CLASH_H, CLASH_M, COLORS_256, COLORS_1, COLORS_2,
                      COLORS_256_U16, HIRES, MULTI_320):
            obj = image2c64.FullScreenImage(fname)
            obj._load()
            self.assertTrue(obj._check_dimensions())

    def test__load(self):
        """
        Test of loading images
        """
        self.assertTrue(image2c64.FullScreenImage(HIRES)._load())
        obj = image2c64.FullScreenImage("nofile")
        obj.log.critical = lambda x: None  # suppress log
        self.assertFalse(obj._load())

    def test__colors_check(self):
        """
        Test _colors_check method
        """
        obj = image2c64.FullScreenImage(COLORS_256)
        obj._load()
        histogram = obj._src_image.histogram()
        # even if input image have 256 colors, internally it will be converted
        # to 16 colors.
        self.assertEqual(obj._colors_check(histogram), 16)

        obj = image2c64.FullScreenImage(COLORS_1)
        obj.log.warn = lambda x, y: None  # suppress log
        obj._load()
        histogram = obj._src_image.histogram()
        self.assertEqual(obj._colors_check(histogram), 1)

        obj = image2c64.FullScreenImage(COLORS_2)
        obj._load()
        histogram = obj._src_image.histogram()
        self.assertEqual(obj._colors_check(histogram), 2)

    def test__get_displayer(self):
        """
        Test _get_displayer stub
        """
        obj = image2c64.FullScreenImage(COLORS_256)
        self.assertRaises(NotImplementedError, obj._get_displayer)

    def test__convert(self):
        """
        Test _convert process
        """
        obj = image2c64.FullScreenImage("nofile")
        obj.log.critical = lambda x: None  # suppress log
        self.assertFalse(obj._convert())

        obj = image2c64.FullScreenImage(COLORS_256)
        self.assertRaises(NotImplementedError, obj._convert)

        obj = image2c64.FullScreenImage(CROP_BOTH)
        self.assertFalse(obj._convert())

    def test__get_best_palette_map(self):
        """
        Test for method _find_best_palette_map
        """
        obj = image2c64.FullScreenImage(COLORS_1)
        obj._load()
        obj._find_best_palette_map()
        self.assertEqual(obj._palette_map, {(0, 0, 0): 0})

        obj = image2c64.FullScreenImage(COLORS_2)
        obj._load()
        obj._find_best_palette_map()
        histogram = obj._src_image.histogram()
        obj._find_most_freq_color(histogram)

        self.assertEqual(obj.data['most_freq_color'], 11)

    def test__find_most_freq_color(self):
        """
        Test for method _find_most_freq_color
        """
        obj = image2c64.FullScreenImage(COLORS_2)
        self.assertEqual(obj.data.get('most_freq_color'), None)

        obj._load()
        obj._find_best_palette_map()
        histogram = obj._src_image.histogram()
        obj._find_most_freq_color(histogram)

        self.assertEqual(obj.data['most_freq_color'], 11)

        obj = image2c64.FullScreenImage(COLORS_1)
        self.assertEqual(obj.data.get('most_freq_color'), None)

        obj._load()
        obj._find_best_palette_map()
        histogram = obj._src_image.histogram()
        obj._find_most_freq_color(histogram)

        self.assertEqual(obj.data['most_freq_color'], 0)

    def test__get_palette(self):
        """
        Test _get_palette method
        """
        obj = image2c64.FullScreenImage(PAL_PEPTO)
        obj._load()

        ref_palette = set(((0, 0, 0), (53, 40, 121), (67, 57, 0),
                           (68, 68, 68), (88, 141, 67), (104, 55, 43),
                           (108, 94, 181), (108, 108, 108), (111, 61, 134),
                           (111, 79, 37), (112, 164, 178), (149, 149, 149),
                           (154, 103, 89), (154, 210, 132), (184, 199, 111),
                           (255, 255, 255)))

        # got 16 colors pepto palette ordered by lightness
        self.assertEqual(set(obj._get_palette()), ref_palette)

    def test__discover_best_palette(self):
        """
        Test _discover_best_palette method
        """
        obj = image2c64.FullScreenImage(PAL_PEPTO)
        obj._load()
        obj._find_best_palette_map()
        self.assertEqual(obj._palette_map,
                         {(184, 199, 111): 7, (154, 210, 132): 13,
                          (112, 164, 178): 3, (88, 141, 67): 5,
                          (0, 0, 0): 0, (108, 94, 181): 14,
                          (68, 68, 68): 11, (154, 103, 89): 10,
                          (67, 57, 0): 9, (53, 40, 121): 6,
                          (111, 79, 37): 8, (108, 108, 108): 12,
                          (111, 61, 134): 4, (255, 255, 255): 1,
                          (104, 55, 43): 2, (149, 149, 149): 15})

        obj = image2c64.FullScreenImage(PAL_VICE)
        obj._load()
        obj._find_best_palette_map()
        self.assertEqual(obj._palette_map,
                         {(182, 89, 0): 9, (0, 142, 0): 5,
                          (147, 81, 182): 4, (56, 255, 52): 5,
                          (154, 154, 154): 15, (0, 81, 158): 6,
                          (134, 134, 134): 12, (0, 182, 182): 14,
                          (255, 109, 109): 10, (0, 0, 0): 0,
                          (85, 85, 85): 11, (109, 121, 255): 14,
                          (213, 223, 124): 7, (255, 255, 255): 1,
                          (109, 52, 0): 9, (207, 0, 0): 2})

        obj = image2c64.FullScreenImage(PAL_TIMANTHES)
        obj._load()
        obj._find_best_palette_map()
        self.assertEqual(obj._palette_map,
                         {(103, 93, 182): 14,
                          (143, 194, 113): 13,
                          (86, 141, 53): 5, (174, 183, 94): 7,
                          (101, 159, 166): 3, (143, 143, 143): 15,
                          (156, 100, 90): 10, (115, 58, 145): 4,
                          (0, 0, 0): 0, (71, 71, 71): 11,
                          (75, 60, 0): 9, (114, 53, 44): 2,
                          (107, 107, 107): 12, (119, 79, 30): 8,
                          (213, 213, 213): 1, (46, 35, 125): 6})

        obj = image2c64.FullScreenImage(PAL_UNKNOWN)
        obj._load()
        obj._find_best_palette_map()
        self.assertEqual(obj._palette_map,
                         {(91, 50, 8): 9, (130, 130, 130): 12,
                          (230, 122, 122): 10, (0, 181, 181): 14,
                          (211, 211, 112): 7, (23, 63, 194): 6,
                          (49, 150, 49): 5, (79, 123, 255): 14,
                          (198, 0, 0): 2, (193, 90, 0): 9,
                          (160, 160, 160): 15, (178, 66, 178): 4,
                          (255, 255, 255): 1, (42, 232, 112): 5,
                          (85, 85, 85): 11, (0, 0, 0): 0})

    def test__fill_memory(self):
        """
        Test _fill_memory method
        """
        obj = image2c64.FullScreenImage(HIRES)
        obj._load()
        self.assertRaises(NotImplementedError, obj._fill_memory)

    def test_save(self):
        """
        Test save method
        """
        obj = image2c64.FullScreenImage(HIRES)
        obj._load()
        self.assertRaises(NotImplementedError, obj.save, "fn")

    def test_attributes(self):
        """
        Test settting background/border colors
        """
        obj = image2c64.FullScreenImage(HIRES)
        self.assertEqual(obj.data, {})

        obj.set_border_color(12)
        self.assertEqual(obj.data, {'border': 12})

        obj.set_bg_color(11)
        self.assertEqual(obj.data, {'background': 11, 'border': 12})

        obj.set_border_color(1)
        self.assertEqual(obj.data, {'background': 11, 'border': 1})

        obj.set_bg_color(0)
        self.assertEqual(obj.data, {'background': 0, 'border': 1})

    def test__get_border(self):
        """
        Test for _get_border method
        """
        obj = image2c64.FullScreenImage(HIRES)
        self.assertEqual(obj._get_border(), 0)

        obj._load()
        obj._find_best_palette_map()
        histogram = obj._src_image.histogram()
        obj._find_most_freq_color(histogram)
        self.assertEqual(obj._get_border(), 0)

        obj = image2c64.FullScreenImage(COLORS_256)
        obj.set_border_color(12)
        self.assertEqual(obj._get_border(), 12)

        obj = image2c64.FullScreenImage(COLORS_256)
        self.assertEqual(obj._get_border(), 0)

        obj._load()
        obj._find_best_palette_map()
        histogram = obj._src_image.histogram()
        obj._find_most_freq_color(histogram)
        self.assertEqual(obj._get_border(), 5)
        obj.set_border_color(7)
        self.assertEqual(obj._get_border(), 7)

    def test_set_bg_color(self):
        """
        Test set_bg_color method
        """
        obj = image2c64.FullScreenImage(HIRES)
        self.assertEqual(obj.data.get('background'), None)
        obj.set_bg_color(15)
        self.assertEqual(obj.data.get('background'), 15)

    def test_set_border_color(self):
        """
        Test set_border_color method
        """
        obj = image2c64.FullScreenImage(HIRES)
        self.assertEqual(obj.data.get('border'), None)
        obj.set_border_color(14)
        self.assertEqual(obj.data.get('border'), 14)

    def test__error_image_action(self):
        """
        Test for _error_image_action method
        """
        error_img = os.path.join(os.path.dirname(__file__),
                                 image2c64.get_modified_fname(MULTI, 'png', '_error.'))

        if os.path.exists(error_img):
            os.unlink(error_img)

        obj = image2c64.MultiConverter(MULTI)
        obj._load()
        result = obj._error_image_action([(0, 0)], True)
        self.assertEqual(result, None)

        obj._errors_action = "save"
        result = obj._error_image_action([(0, 0)], True)
        self.assertTrue(os.path.exists(error_img))
        os.unlink(error_img)

        # does nothing. maybe some refactoring needed for _error_image_action
        # method?
        obj._errors_action = "show"
        obj._error_image_action([(0, 0)], True)

        obj = image2c64.MultiConverter(MULTI)
        obj._load()
        obj._errors_action = "show"
        obj._error_image_action([(0, 0)], True)

        error_img = os.path.join(os.path.dirname(__file__),
                                 image2c64.get_modified_fname(MULTI_320, 'png',
                                                    '_error.'))

        if os.path.exists(error_img):
            os.unlink(error_img)

        obj = image2c64.MultiConverter(MULTI_320)
        obj._load()
        result = obj._error_image_action([(0, 0)])
        self.assertEqual(result, None)

        obj._errors_action = "save"
        result = obj._error_image_action([(0, 0)])
        self.assertTrue(os.path.exists(error_img))
        os.unlink(error_img)

        # does nothing. maybe some refactoring needed for _error_image_action
        # method?
        obj._errors_action = "show"
        obj._error_image_action([(0, 0)])

        obj = image2c64.MultiConverter(MULTI_320)
        obj._load()
        obj._errors_action = "show"
        obj._error_image_action([(0, 0)])

        error_img = os.path.join(os.path.dirname(__file__),
                                 image2c64.get_modified_fname(HIRES, 'png', '_error.'))

        if os.path.exists(error_img):
            os.unlink(error_img)

        obj = image2c64.HiresConverter(HIRES)
        obj._load()
        result = obj._error_image_action([(0, 0)])
        self.assertEqual(result, None)

        obj._errors_action = "save"
        result = obj._error_image_action([(0, 0)])
        self.assertTrue(os.path.exists(error_img))
        os.unlink(error_img)

        # does nothing. maybe some refactoring needed for _error_image_action
        # method?
        obj._errors_action = "show"
        obj._error_image_action([(0, 0)])

        obj = image2c64.HiresConverter(MULTI)
        obj._load()
        obj._errors_action = "show"
        obj._error_image_action([(0, 0)])


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
            obj = image2c64.HiresConverter(fname)
            obj.log.error = lambda *x: None  # suppress log
            obj._load()
            self.assertFalse(obj._check_dimensions())

        for fname in (CLASH_H, CLASH_M, COLORS_256, COLORS_1, COLORS_2,
                      COLORS_256_U16, HIRES, MULTI_320):
            obj = image2c64.HiresConverter(fname)
            obj._load()
            self.assertTrue(obj._check_dimensions())

    def test__fill_memory(self):
        """
        Test for _fill_memory method
        """
        obj = image2c64.HiresConverter(HIRES)
        obj._load()
        hist = obj._src_image.histogram()
        obj._colors_check(hist)
        obj._find_best_palette_map()
        self.assertEqual(obj._fill_memory(), True)

        obj = image2c64.HiresConverter(COLORS_1)
        obj._load()
        hist = obj._src_image.histogram()
        obj.log.warn = lambda x, y: None  # suppress log
        obj._colors_check(hist)
        obj._find_best_palette_map()
        self.assertEqual(obj._fill_memory(), True)

        obj = image2c64.HiresConverter(CLASH_H)
        obj._load()
        hist = obj._src_image.histogram()
        obj._colors_check(hist)
        obj._find_best_palette_map()
        self.assertEqual(obj._fill_memory(), False)

    def test__get_displayer(self):
        """
        Test for _get_displayer method
        """
        obj = image2c64.HiresConverter(HIRES)
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

        obj = image2c64.HiresConverter(HIRES)
        obj.log.warning = lambda *x: None  # suppress log
        self.assertEqual(obj.save(fname, "prg"), True)

        self.assertTrue(os.path.exists(fname))
        self.assertEqual(os.stat(fname).st_size, 14145)
        os.unlink(fname)

        fdesc, fname = mkstemp(suffix=".prg")
        os.close(fdesc)

        obj = image2c64.HiresConverter(HIRES)
        obj.log.warning = lambda *x: None  # suppress log
        self.assertEqual(obj.save(fname, "art-studio-hires"), True)

        self.assertTrue(os.path.exists(fname))
        self.assertEqual(os.stat(fname).st_size, 9009)
        os.unlink(fname)

        obj = image2c64.HiresConverter(CLASH_H)
        self.assertEqual(obj.save(fname, "art-studio-hires"), False)

        obj = image2c64.HiresConverter(HIRES)
        self.assertEqual(obj.save(fname, "raw"), True)

        self.assertTrue(os.path.exists(fname + "_bitmap.raw"))
        self.assertTrue(os.path.exists(fname + "_screen.raw"))

        self.assertEqual(os.stat(fname + "_bitmap.raw").st_size, 8000)
        self.assertEqual(os.stat(fname + "_screen.raw").st_size, 1000)
        os.unlink(fname + "_bitmap.raw")
        os.unlink(fname + "_screen.raw")


class TestMulticolor(TestCase):
    """
    Tests for multicolor conversion
    """
    def test__check_dimensions(self):
        """
        Test of dimensions of the input images
        """
        for fname in (CROP_V, CROP_H, CROP_BOTH):
            obj = image2c64.MultiConverter(fname)
            obj.log.error = lambda *x: None  # suppress log
            obj._load()
            self.assertFalse(obj._check_dimensions())

        for fname in (CLASH_H, CLASH_M, COLORS_256, COLORS_1, COLORS_2,
                      COLORS_256_U16, HIRES, MULTI_320, CLASH_M2, MULTI,
                      PAL_PEPTO, PAL_TIMANTHES, PAL_UNKNOWN, PAL_VICE):
            obj = image2c64.MultiConverter(fname)
            obj._load()
            self.assertTrue(obj._check_dimensions(), fname)

    def test__load(self):
        """
        Test custom load function
        """
        obj = image2c64.MultiConverter(MULTI)
        self.assertEqual(obj._load(), True)
        self.assertEqual(obj._src_image.size[0], 160)

        obj = image2c64.MultiConverter(MULTI_320)
        self.assertEqual(obj._load(), True)
        self.assertEqual(obj._src_image.size[0], 160)

        obj = image2c64.MultiConverter("nofile")
        obj.log.critical = lambda x: None  # suppress log
        self.assertEqual(obj._load(), False)
        self.assertEqual(obj._src_image, None)

    def test_save(self):
        """
        Test for save methods
        """
        fdesc, fname = mkstemp(suffix=".prg")
        os.close(fdesc)
        os.unlink(fname)

        obj = image2c64.MultiConverter(MULTI_320)
        self.assertEqual(obj.save(fname, "prg"), True)

        self.assertTrue(os.path.exists(fname))
        self.assertEqual(os.stat(fname).st_size, 14145)
        os.unlink(fname)

        fdesc, fname = mkstemp(suffix=".prg")
        os.close(fdesc)
        os.unlink(fname)

        obj = image2c64.MultiConverter(MULTI)
        self.assertEqual(obj.save(fname, "koala"), True)

        self.assertTrue(os.path.exists(fname))
        self.assertEqual(os.stat(fname).st_size, 10004)
        os.unlink(fname)

        obj = image2c64.MultiConverter(CLASH_M)
        self.assertEqual(obj.save(fname, "koala"), False)

        obj = image2c64.MultiConverter(CLASH_M2)
        self.assertEqual(obj.save(fname, "koala"), False)

        obj = image2c64.MultiConverter(MULTI)
        self.assertEqual(obj.save(fname, "raw"), True)

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

        obj = image2c64.MultiConverter(CLASH_M)
        self.assertEqual(obj.save(fname, "raw"), False)

        obj = image2c64.MultiConverter(CLASH_M2)
        self.assertEqual(obj.save(fname, "raw"), False)


class TestMisc(TestCase):
    """
    Test helper functions
    """
    def test_get_modified_fname(self):
        """
        Test get_modified_fname function.
        """
        self.assertEqual(image2c64.get_modified_fname(HIRES, "png", "_foo"),
                         "test_images/hires_foo.png")
        self.assertEqual(image2c64.get_modified_fname(HIRES, ".png", "_foo"),
                         "test_images/hires_foo.png")
        self.assertEqual(image2c64.get_modified_fname(HIRES, "png", "_foo."),
                         "test_images/hires_foo.png")

    def test_best_color_match(self):
        """
        Test best_color_match helper function.
        """
        # perfect match
        idx, delta = image2c64.best_color_match((0, 0, 0),
                                                image2c64.PALETTES['Pepto'])
        self.assertEqual(idx, 0)
        self.assertEqual(delta, 0)

        # almost there
        idx, delta = image2c64.best_color_match((2, 0, 0),
                                                image2c64.PALETTES['Pepto'])
        self.assertEqual(idx, 0)
        self.assertEqual(delta, 4)

        idx, delta = image2c64.best_color_match((254, 254, 254),
                                                image2c64.PALETTES['Pepto'])
        self.assertEqual(idx, 1)
        self.assertEqual(delta, 3)

        # quite distorted: after all we got gray - which have values
        # 68, 68, 68
        idx, delta = image2c64.best_color_match((86, 86, 86),
                                                image2c64.PALETTES['Pepto'])
        self.assertEqual(idx, 11)
        self.assertEqual(delta, 972)

        # one value lower and now we got dark gray - which have values
        # 68, 68, 68
        idx, delta = image2c64.best_color_match((85, 85, 85),
                                                image2c64.PALETTES['Pepto'])
        self.assertEqual(idx, 11)
        self.assertEqual(delta, 867)

    def test_resolve_name(self):
        """
        Test resolve_name function
        """
        class Obj(object):
            """
            Mock args class
            """
            def __init__(self):
                """
                Initialization
                """
                self.filename = "foo"
                self.format = "hires"
                self.output = None
                self.executable = False
                self.raw = False

        args = Obj()
        args.filename = ["foo"]
        args.format = "hires"
        args.output = None
        args.executable = False
        self.assertEqual(image2c64.resolve_name(args, args.filename[0]),
                         ("foo.prg", "hires"))

        args.output = "bar"
        self.assertEqual(image2c64.resolve_name(args, args.filename[0]),
                         ("bar", "hires"))

        args.executable = True
        self.assertEqual(image2c64.resolve_name(args, args.filename[0]),
                         ("bar.prg", "prg"))

        args.executable = False
        args.raw = True
        args.output = "bar.prg"
        self.assertEqual(image2c64.resolve_name(args, args.filename[0]),
                         ("bar", "raw"))

        args.output = "foo.hires"
        self.assertEqual(image2c64.resolve_name(args, args.filename[0]),
                         ("foo", "raw"))

        args.output = "foo.hires.png"
        self.assertEqual(image2c64.resolve_name(args, args.filename[0]),
                         ("foo.hires", "raw"))


if __name__ == "__main__":
    main()
