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

import Image
Image.Image.show = lambda x: None

from image2c64 import FullScreenImage, HiresConverter, MultiConverter, Logger
from image2c64 import PALETTES, get_modified_fname, best_color_match
from image2c64 import resolve_name

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


class TestLogger(TestCase):
    """
    Test Logger class
    """
    def test___init(self):
        """
        Test logger object creation
        """
        log = Logger("foo")
        self.assertTrue(isinstance(log, Logger))
        # since logger.Logging is mocked here we will have DummyLogger
        # instance
        self.assertTrue(isinstance(log(), logging.Logger))  # DummyLogger))
        self.assertEqual(log().handlers[0].name, 'console')

    def test__setup_logger(self):
        """
        Test setup logger method
        """
        log = Logger("foo")
        self.assertEqual(len(log().handlers), 1)
        log.setup_logger()
        self.assertEqual(len(log().handlers), 1)
        self.assertEqual(log().handlers[0].name, 'console')
        self.assertEqual(log().getEffectiveLevel(), logging.WARNING)

    def test_set_verbose(self):
        """
        Test for changing verbosity level
        """
        log = Logger("foo")()

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
        self.assertRaises(TypeError, FullScreenImage)
        obj = FullScreenImage(MULTI_320)
        self.assertEqual(obj._fname, MULTI_320)
        self.assertEqual(obj._errors_action, "none")
        self.assertEqual(obj._error_image, None)
        self.assertEqual(obj._src_image, None)
        self.assertTrue(isinstance(obj.log, logging.Logger))
        self.assertEqual(obj._data, {})

    def test__check_dimensions(self):
        """
        Test of dimensions of the input images
        """
        for fname in (CROP_V, CROP_H, CROP_BOTH, CLASH_M2, MULTI, PAL_PEPTO,
                      PAL_TIMANTHES, PAL_UNKNOWN, PAL_VICE):
            obj = FullScreenImage(fname)
            obj.log.error = lambda *x: None  # suppress log
            obj._load()
            self.assertFalse(obj._check_dimensions())

        for fname in (CLASH_H, CLASH_M, COLORS_256, COLORS_1, COLORS_2,
                      COLORS_256_U16, HIRES, MULTI_320):
            obj = FullScreenImage(fname)
            obj._load()
            self.assertTrue(obj._check_dimensions())

    def test__load(self):
        """
        Test of loading images
        """
        self.assertTrue(FullScreenImage(HIRES)._load())
        obj = FullScreenImage("nofile")
        obj.log.critical = lambda x: None  # suppress log
        self.assertFalse(obj._load())

    def test__colors_check(self):
        """
        Test _colors_check method
        """
        obj = FullScreenImage(COLORS_256)
        obj._load()
        histogram = obj._src_image.histogram()
        # even if input image have 256 colors, internally it will be converted
        # to 16 colors.
        self.assertEqual(obj._colors_check(histogram), 16)

        obj = FullScreenImage(COLORS_1)
        obj.log.warn = lambda x, y: None  # suppress log
        obj._load()
        histogram = obj._src_image.histogram()
        self.assertEqual(obj._colors_check(histogram), 1)

        obj = FullScreenImage(COLORS_2)
        obj._load()
        histogram = obj._src_image.histogram()
        self.assertEqual(obj._colors_check(histogram), 2)

    def test__get_displayer(self):
        """
        Test _get_displayer stub
        """
        obj = FullScreenImage(COLORS_256)
        self.assertRaises(NotImplementedError, obj._get_displayer)

    def test__convert(self):
        """
        Test _convert process
        """
        obj = FullScreenImage("nofile")
        obj.log.critical = lambda x: None  # suppress log
        self.assertFalse(obj._convert())

        obj = FullScreenImage(COLORS_256)
        self.assertRaises(NotImplementedError, obj._convert)

        obj = FullScreenImage(CROP_BOTH)
        self.assertFalse(obj._convert())

    def test__get_best_palette_map(self):
        """
        Test for method _get_best_palette_map
        """
        obj = FullScreenImage(COLORS_1)
        obj._load()
        palette_map = obj._get_best_palette_map()
        self.assertEqual(palette_map, {(0, 0, 0): 0})

        obj = FullScreenImage(COLORS_2)
        obj._load()
        palette_map = obj._get_best_palette_map()
        histogram = obj._src_image.histogram()
        obj._find_most_freq_color(histogram, palette_map)

        self.assertEqual(obj._data['most_freq_color'], 11)

    def test__find_most_freq_color(self):
        """
        Test for method _find_most_freq_color
        """
        obj = FullScreenImage(COLORS_2)
        self.assertEqual(obj._data.get('most_freq_color'), None)

        obj._load()
        palette_map = obj._get_best_palette_map()
        histogram = obj._src_image.histogram()
        obj._find_most_freq_color(histogram, palette_map)

        self.assertEqual(obj._data['most_freq_color'], 11)

        obj = FullScreenImage(COLORS_1)
        self.assertEqual(obj._data.get('most_freq_color'), None)

        obj._load()
        palette_map = obj._get_best_palette_map()
        histogram = obj._src_image.histogram()
        obj._find_most_freq_color(histogram, palette_map)

        self.assertEqual(obj._data['most_freq_color'], 0)

    def test__get_palette(self):
        """
        Test _get_palette method
        """
        obj = FullScreenImage(PAL_PEPTO)
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
        obj = FullScreenImage(PAL_PEPTO)
        obj._load()
        palette_map = obj._get_best_palette_map()
        self.assertEqual(palette_map, {(184, 199, 111): 7, (154, 210, 132): 13,
                                       (112, 164, 178): 3, (88, 141, 67): 5,
                                       (0, 0, 0): 0, (108, 94, 181): 14,
                                       (68, 68, 68): 11, (154, 103, 89): 10,
                                       (67, 57, 0): 9, (53, 40, 121): 6,
                                       (111, 79, 37): 8, (108, 108, 108): 12,
                                       (111, 61, 134): 4, (255, 255, 255): 1,
                                       (104, 55, 43): 2, (149, 149, 149): 15})

        obj = FullScreenImage(PAL_VICE)
        obj._load()
        palette_map = obj._get_best_palette_map()
        self.assertEqual(palette_map, {(182, 89, 0): 9, (0, 142, 0): 5,
                                       (147, 81, 182): 4, (56, 255, 52): 5,
                                       (154, 154, 154): 15, (0, 81, 158): 6,
                                       (134, 134, 134): 12, (0, 182, 182): 14,
                                       (255, 109, 109): 10, (0, 0, 0): 0,
                                       (85, 85, 85): 11, (109, 121, 255): 14,
                                       (213, 223, 124): 7, (255, 255, 255): 1,
                                       (109, 52, 0): 9, (207, 0, 0): 2})

        obj = FullScreenImage(PAL_TIMANTHES)
        obj._load()
        palette_map = obj._get_best_palette_map()
        self.assertEqual(palette_map, {(103, 93, 182): 14,
                                       (143, 194, 113): 13,
                                       (86, 141, 53): 5, (174, 183, 94): 7,
                                       (101, 159, 166): 3, (143, 143, 143): 15,
                                       (156, 100, 90): 10, (115, 58, 145): 4,
                                       (0, 0, 0): 0, (71, 71, 71): 11,
                                       (75, 60, 0): 9, (114, 53, 44): 2,
                                       (107, 107, 107): 12, (119, 79, 30): 8,
                                       (213, 213, 213): 1, (46, 35, 125): 6})

        obj = FullScreenImage(PAL_UNKNOWN)
        obj._load()
        palette_map = obj._get_best_palette_map()
        self.assertEqual(palette_map, {(91, 50, 8): 9, (130, 130, 130): 12,
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
        obj = FullScreenImage(HIRES)
        obj._load()
        self.assertRaises(NotImplementedError, obj._fill_memory)

    def test_save(self):
        """
        Test save method
        """
        obj = FullScreenImage(HIRES)
        obj._load()
        self.assertRaises(NotImplementedError, obj.save, "fn")

    def test_attributes(self):
        """
        Test settting background/border colors
        """
        obj = FullScreenImage(HIRES)
        self.assertEqual(obj._data, {})

        obj.set_border_color(12)
        self.assertEqual(obj._data, {'border': 12})

        obj.set_bg_color(11)
        self.assertEqual(obj._data, {'background': 11, 'border': 12})

        obj.set_border_color(1)
        self.assertEqual(obj._data, {'background': 11, 'border': 1})

        obj.set_bg_color(0)
        self.assertEqual(obj._data, {'background': 0, 'border': 1})

    def test__get_border(self):
        """
        Test for _get_border method
        """
        obj = FullScreenImage(HIRES)
        self.assertEqual(obj._get_border(), 0)

        obj._load()
        palette_map = obj._get_best_palette_map()
        histogram = obj._src_image.histogram()
        obj._find_most_freq_color(histogram, palette_map)
        self.assertEqual(obj._get_border(), 0)

        obj = FullScreenImage(COLORS_256)
        obj.set_border_color(12)
        self.assertEqual(obj._get_border(), 12)

        obj = FullScreenImage(COLORS_256)
        self.assertEqual(obj._get_border(), 0)

        obj._load()
        palette_map = obj._get_best_palette_map()
        histogram = obj._src_image.histogram()
        obj._find_most_freq_color(histogram, palette_map)
        self.assertEqual(obj._get_border(), 5)
        obj.set_border_color(7)
        self.assertEqual(obj._get_border(), 7)

    def test_set_bg_color(self):
        """
        Test set_bg_color method
        """
        obj = FullScreenImage(HIRES)
        self.assertEqual(obj._data.get('background'), None)
        obj.set_bg_color(15)
        self.assertEqual(obj._data.get('background'), 15)

    def test_set_border_color(self):
        """
        Test set_border_color method
        """
        obj = FullScreenImage(HIRES)
        self.assertEqual(obj._data.get('border'), None)
        obj.set_border_color(14)
        self.assertEqual(obj._data.get('border'), 14)

    def test__error_image_action(self):
        """
        Test for _error_image_action method
        """
        error_img = os.path.join(os.path.dirname(__file__),
                                 get_modified_fname(MULTI, 'png', '_error.'))

        if os.path.exists(error_img):
            os.unlink(error_img)

        obj = MultiConverter(MULTI)
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

        obj = MultiConverter(MULTI)
        obj._load()
        obj._errors_action = "show"
        obj._error_image_action([(0, 0)], True)

        error_img = os.path.join(os.path.dirname(__file__),
                                 get_modified_fname(MULTI_320, 'png',
                                                    '_error.'))

        if os.path.exists(error_img):
            os.unlink(error_img)

        obj = MultiConverter(MULTI_320)
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

        obj = MultiConverter(MULTI_320)
        obj._load()
        obj._errors_action = "show"
        obj._error_image_action([(0, 0)])

        error_img = os.path.join(os.path.dirname(__file__),
                                 get_modified_fname(HIRES, 'png', '_error.'))

        if os.path.exists(error_img):
            os.unlink(error_img)

        obj = HiresConverter(HIRES)
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

        obj = HiresConverter(MULTI)
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
            obj = HiresConverter(fname)
            obj.log.error = lambda *x: None  # suppress log
            obj._load()
            self.assertFalse(obj._check_dimensions())

        for fname in (CLASH_H, CLASH_M, COLORS_256, COLORS_1, COLORS_2,
                      COLORS_256_U16, HIRES, MULTI_320):
            obj = HiresConverter(fname)
            obj._load()
            self.assertTrue(obj._check_dimensions())

    def test__fill_memory(self):
        """
        Test for _fill_memory method
        """
        obj = HiresConverter(HIRES)
        obj._load()
        hist = obj._src_image.histogram()
        obj._colors_check(hist)
        palette_map = obj._get_best_palette_map()
        self.assertEqual(obj._fill_memory(pal_map=palette_map), True)

        obj = HiresConverter(COLORS_1)
        obj._load()
        hist = obj._src_image.histogram()
        obj.log.warn = lambda x, y: None  # suppress log
        obj._colors_check(hist)
        palette_map = obj._get_best_palette_map()
        self.assertEqual(obj._fill_memory(pal_map=palette_map), True)

        obj = HiresConverter(CLASH_H)
        obj._load()
        hist = obj._src_image.histogram()
        obj._colors_check(hist)
        palette_map = obj._get_best_palette_map()
        self.assertEqual(obj._fill_memory(pal_map=palette_map), False)

    def test__get_displayer(self):
        """
        Test for _get_displayer method
        """
        obj = HiresConverter(HIRES)
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

        obj = HiresConverter(HIRES)
        obj.log.warning = lambda *x: None  # suppress log
        self.assertEqual(obj.save(fname, "prg"), True)

        self.assertTrue(os.path.exists(fname))
        self.assertEqual(os.stat(fname).st_size, 14145)
        os.unlink(fname)

        fdesc, fname = mkstemp(suffix=".prg")
        os.close(fdesc)

        obj = HiresConverter(HIRES)
        obj.log.warning = lambda *x: None  # suppress log
        self.assertEqual(obj.save(fname, "art-studio-hires"), True)

        self.assertTrue(os.path.exists(fname))
        self.assertEqual(os.stat(fname).st_size, 9009)
        os.unlink(fname)

        obj = HiresConverter(CLASH_H)
        self.assertEqual(obj.save(fname, "art-studio-hires"), False)


class TestMulticolor(TestCase):
    """
    Tests for multicolor conversion
    """
    def test__check_dimensions(self):
        """
        Test of dimensions of the input images
        """
        for fname in (CROP_V, CROP_H, CROP_BOTH):
            obj = MultiConverter(fname)
            obj.log.error = lambda *x: None  # suppress log
            obj._load()
            self.assertFalse(obj._check_dimensions())

        for fname in (CLASH_H, CLASH_M, COLORS_256, COLORS_1, COLORS_2,
                      COLORS_256_U16, HIRES, MULTI_320, CLASH_M2, MULTI,
                      PAL_PEPTO, PAL_TIMANTHES, PAL_UNKNOWN, PAL_VICE):
            obj = MultiConverter(fname)
            obj._load()
            self.assertTrue(obj._check_dimensions(), fname)

    def test__load(self):
        """
        Test custom load function
        """
        obj = MultiConverter(MULTI)
        self.assertEqual(obj._load(), True)
        self.assertEqual(obj._src_image.size[0], 160)

        obj = MultiConverter(MULTI_320)
        self.assertEqual(obj._load(), True)
        self.assertEqual(obj._src_image.size[0], 160)

        obj = MultiConverter("nofile")
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

        obj = MultiConverter(MULTI_320)
        self.assertEqual(obj.save(fname, "prg"), True)

        self.assertTrue(os.path.exists(fname))
        self.assertEqual(os.stat(fname).st_size, 14145)
        os.unlink(fname)

        fdesc, fname = mkstemp(suffix=".prg")
        os.close(fdesc)
        os.unlink(fname)

        obj = MultiConverter(MULTI)
        self.assertEqual(obj.save(fname, "koala"), True)

        self.assertTrue(os.path.exists(fname))
        self.assertEqual(os.stat(fname).st_size, 10004)
        os.unlink(fname)

        obj = MultiConverter(CLASH_M)
        self.assertEqual(obj.save(fname, "koala"), False)

        obj = MultiConverter(CLASH_M2)
        self.assertEqual(obj.save(fname, "koala"), False)


class TestMisc(TestCase):
    """
    Test helper functions
    """
    def test_get_modified_fname(self):
        """
        Test get_modified_fname function.
        """
        self.assertEqual(get_modified_fname(HIRES, "png", "_foo"),
                         "test_images/hires_foo.png")
        self.assertEqual(get_modified_fname(HIRES, ".png", "_foo"),
                         "test_images/hires_foo.png")
        self.assertEqual(get_modified_fname(HIRES, "png", "_foo."),
                         "test_images/hires_foo.png")

    def test_best_color_match(self):
        """
        Test best_color_match helper function.
        """
        # perfect match
        idx, delta = best_color_match((0, 0, 0), PALETTES['Pepto'])
        self.assertEqual(idx, 0)
        self.assertEqual(delta, 0)

        # almost there
        idx, delta = best_color_match((2, 0, 0), PALETTES['Pepto'])
        self.assertEqual(idx, 0)
        self.assertEqual(delta, 4)

        idx, delta = best_color_match((254, 254, 254), PALETTES['Pepto'])
        self.assertEqual(idx, 1)
        self.assertEqual(delta, 3)

        # quite distorted: after all we got gray - which have values
        # 68, 68, 68
        idx, delta = best_color_match((86, 66, 86), PALETTES['Pepto'])
        self.assertEqual(idx, 11)
        self.assertEqual(delta, 652)

        # one value lower and now we got dark gray - which have values
        # 68, 68, 68
        idx, delta = best_color_match((85, 85, 85), PALETTES['Pepto'])
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

        args = Obj()
        args.filename = "foo"
        args.format = "hires"
        args.output = None
        args.executable = False
        self.assertEqual(resolve_name(args), ("foo.prg", "hires"))

        args.output = "bar"
        self.assertEqual(resolve_name(args), ("bar", "hires"))

        args.executable = True
        self.assertEqual(resolve_name(args), ("bar.prg", "prg"))


if __name__ == "__main__":
    main()
