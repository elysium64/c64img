#!/usr/bin/env python
"""
Tests for c64img module <https://bitbucket.org/gryf/base>

Author: Roman 'gryf' Dobosz <gryf73@gmail.com>
Date: 2012-11-20
Version: 1.3
Licence: BSD
"""
import os
from unittest import TestCase, main
import logging

from PIL import Image

from c64img import base


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


class TestChar(TestCase):
    """
    Test Char class
    """
    def setUp(self):
        """set up"""
        self.log = LogMock()

    def test___init(self):
        """
        Test Char initialization
        """
        char = base.Char(self.log)
        self.assertEqual(char.clash, False)
        self.assertEqual(char.colors, {})
        self.assertEqual(char.max_colors, 2)
        self.assertEqual(char.pixels, {})
        self.assertEqual(char.prev, None)

        char = base.Char(self.log, "foo")
        self.assertEqual(char.prev, "foo")

    def test__analyze_color_map(self):
        """
        Test _analyze_color_map method
        """
        char = base.Char(self.log, 0)
        # simulate clash
        char.max_colors = 1
        char.pixels[(0, 0)] = 1
        char.pixels[(0, 1)] = 2
        char._analyze_color_map()
        self.assertEqual(char.colors, {})

        # simulate previous image clash
        char.clash = False
        char.max_colors = 2
        char.prev = base.Char(self.log, 0)
        char.prev.clash = True
        char._analyze_color_map()
        self.assertEqual(char.colors, {})
        self.assertEqual(len(char.colors), 0)

    def test_get_binary_data(self):
        """
        Test get_binary_data method
        """
        char = base.Char(self.log, 0)
        self.assertRaises(NotImplementedError, char.get_binary_data)

    def test__check_clash(self):
        """
        Test _check_clash method
        """
        char = base.Char(self.log, 0)
        self.assertEqual(char._check_clash(), False)

    def test__compare_colors(self):
        """
        Test _compare_colors method
        """
        char = base.Char(self.log)
        self.assertRaises(TypeError, char._compare_colors)
        self.assertRaises(TypeError, char._compare_colors, None)
        char._compare_colors([])


class TestFullScreenImage(TestCase):
    """
    Test FullScreenImage class
    """
    def setUp(self):
        """setup"""
        self._system = os.system
        self.os_system_params = ""

        def _system(param):
            self.os_system_params = param

        os.system = _system

    def tearDown(self):
        """Restore stuff"""
        os.system = self._system

    def test___init(self):
        """
        Test initialization
        """
        self.assertRaises(TypeError, base.FullScreenImage)
        obj = base.FullScreenImage(MULTI_320)
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
            obj = base.FullScreenImage(fname)
            obj.log.error = lambda *x: None  # suppress log
            obj._load()
            self.assertFalse(obj._check_dimensions())

        for fname in (CLASH_H, CLASH_M, COLORS_256, COLORS_1, COLORS_2,
                      COLORS_256_U16, HIRES, MULTI_320):
            obj = base.FullScreenImage(fname)
            obj._load()
            self.assertTrue(obj._check_dimensions())

    def test__load(self):
        """
        Test of loading images
        """
        self.assertTrue(base.FullScreenImage(HIRES)._load())
        obj = base.FullScreenImage("nofile")
        self.assertFalse(obj._load())

        obj = base.FullScreenImage("/none/existing")
        self.assertFalse(obj._load())
        obj.log.setLevel(logging.DEBUG)
        self.assertRaises(IOError, obj._load)
        obj.log.setLevel(logging.WARNING)

    def test__colors_check(self):
        """
        Test _colors_check method
        """
        obj = base.FullScreenImage(COLORS_256)
        obj._load()
        histogram = obj._src_image.histogram()
        # even if input image have 256 colors, internally it will be converted
        # to 16 colors.
        self.assertEqual(obj._colors_check(histogram), 16)

        obj = base.FullScreenImage(COLORS_1)
        obj.log.warn = lambda x, y: None  # suppress log
        obj._load()
        histogram = obj._src_image.histogram()
        self.assertEqual(obj._colors_check(histogram), 1)

        obj = base.FullScreenImage(COLORS_2)
        obj._load()
        histogram = obj._src_image.histogram()
        self.assertEqual(obj._colors_check(histogram), 2)

    def test_convert(self):
        """
        Test convert process
        """
        obj = base.FullScreenImage("nofile")
        self.assertFalse(obj.convert())

        obj = base.FullScreenImage(COLORS_256)
        self.assertRaises(NotImplementedError, obj.convert)

        obj = base.FullScreenImage(CROP_BOTH)
        self.assertFalse(obj.convert())

    def test__get_best_palette_map(self):
        """
        Test for method _find_best_palette_map
        """
        obj = base.FullScreenImage(COLORS_1)
        obj._load()
        obj._find_best_palette_map()
        self.assertEqual(obj._palette_map, {(0, 0, 0): 0})

        obj = base.FullScreenImage(COLORS_2)
        obj._load()
        obj._find_best_palette_map()
        histogram = obj._src_image.histogram()
        obj._find_most_freq_color(histogram)

        self.assertEqual(obj.data['most_freq_color'], 11)

    def test__find_most_freq_color(self):
        """
        Test for method _find_most_freq_color
        """
        obj = base.FullScreenImage(COLORS_2)
        self.assertEqual(obj.data.get('most_freq_color'), None)

        obj._load()
        obj._find_best_palette_map()
        histogram = obj._src_image.histogram()
        obj._find_most_freq_color(histogram)

        self.assertEqual(obj.data['most_freq_color'], 11)

        obj = base.FullScreenImage(COLORS_1)
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
        obj = base.FullScreenImage(PAL_PEPTO)
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
        obj = base.FullScreenImage(PAL_PEPTO)
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

        obj = base.FullScreenImage(PAL_VICE)
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

        obj = base.FullScreenImage(PAL_TIMANTHES)
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

        obj = base.FullScreenImage(PAL_UNKNOWN)
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
        obj = base.FullScreenImage(HIRES)
        obj._load()
        self.assertRaises(NotImplementedError, obj._fill_memory)

    def test_save(self):
        """
        Test save method
        """
        obj = base.FullScreenImage(HIRES)
        obj._load()
        self.assertRaises(NotImplementedError, obj.save, "fn")

    def test_attributes(self):
        """
        Test settting background/border colors
        """
        obj = base.FullScreenImage(HIRES)
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
        obj = base.FullScreenImage(HIRES)
        self.assertEqual(obj._get_border(), 0)

        obj._load()
        obj._find_best_palette_map()
        histogram = obj._src_image.histogram()
        obj._find_most_freq_color(histogram)
        self.assertEqual(obj._get_border(), 0)

        obj = base.FullScreenImage(COLORS_256)
        obj.set_border_color(12)
        self.assertEqual(obj._get_border(), 12)

        obj = base.FullScreenImage(COLORS_256)
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
        obj = base.FullScreenImage(HIRES)
        self.assertEqual(obj.data.get('background'), None)
        obj.set_bg_color(15)
        self.assertEqual(obj.data.get('background'), 15)

    def test_set_border_color(self):
        """
        Test set_border_color method
        """
        obj = base.FullScreenImage(HIRES)
        self.assertEqual(obj.data.get('border'), None)
        obj.set_border_color(14)
        self.assertEqual(obj.data.get('border'), 14)

    def test__error_image_action(self):
        """
        Test for _error_image_action method
        """
        error_img = base.get_modified_fname(MULTI, 'png', '_error.')

        if os.path.exists(error_img):
            os.unlink(error_img)

        obj = base.FullScreenImage(MULTI)
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

        obj = base.FullScreenImage(MULTI)
        obj._load()
        obj._errors_action = "show"
        obj._error_image_action([(0, 0)], True)

        error_img = base.get_modified_fname(MULTI_320, 'png', '_error.')

        if os.path.exists(error_img):
            os.unlink(error_img)

        obj = base.FullScreenImage(MULTI_320)
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

        obj = base.FullScreenImage(MULTI_320)
        obj._load()
        obj._errors_action = "show"
        obj._error_image_action([(0, 0)])

        error_img = base.get_modified_fname(HIRES, 'png', '_error.')

        if os.path.exists(error_img):
            os.unlink(error_img)

        obj = base.FullScreenImage(HIRES)
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

        obj = base.FullScreenImage(MULTI)
        obj._load()
        obj._errors_action = "show"
        obj._error_image_action([(0, 0)])

        # Test the grafx2 option
        error_img = base.get_modified_fname(MULTI_320, 'png', '_error.')
        obj = base.FullScreenImage(MULTI_320)
        obj._load()
        obj._errors_action = "grafx2"
        obj._error_image_action([(0, 0)])
        self.assertTrue("grafx2" in self.os_system_params)
        os.unlink(error_img)


class TestMisc(TestCase):
    """
    Test helper functions
    """

    def test_best_color_match(self):
        """
        Test _best_color_match helper function.
        """
        # perfect match
        idx, delta = base._best_color_match((0, 0, 0),
                                            base.PALETTES['Pepto'])
        self.assertEqual(idx, 0)
        self.assertEqual(delta, 0)

        # almost there
        idx, delta = base._best_color_match((2, 0, 0),
                                            base.PALETTES['Pepto'])
        self.assertEqual(idx, 0)
        self.assertEqual(delta, 4)

        idx, delta = base._best_color_match((254, 254, 254),
                                            base.PALETTES['Pepto'])
        self.assertEqual(idx, 1)
        self.assertEqual(delta, 3)

        # quite distorted: after all we got gray - which have values
        # 68, 68, 68
        idx, delta = base._best_color_match((86, 86, 86),
                                            base.PALETTES['Pepto'])
        self.assertEqual(idx, 11)
        self.assertEqual(delta, 972)

        # one value lower and now we got dark gray - which have values
        # 68, 68, 68
        idx, delta = base._best_color_match((85, 85, 85),
                                            base.PALETTES['Pepto'])
        self.assertEqual(idx, 11)
        self.assertEqual(delta, 867)


if __name__ == "__main__":
    main()
