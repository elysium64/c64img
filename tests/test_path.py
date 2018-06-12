#!/usr/bin/env python
"""
Tests for c64img.path module
This is part of the c64img project <https://bitbucket.org/gryf/image2c64>

Author: Roman 'gryf' Dobosz <gryf73@gmail.com>
Licence: BSD
"""
from unittest import TestCase, main

from c64img import path


class TestPath(TestCase):
    """
    Test helper functions
    """

    def test_get_modified_fname(self):
        """
        Test get_modified_fname function.
        """
        pic_path = "foo/hires.png"
        self.assertEqual(path.get_modified_fname(pic_path, "png", "_foo"),
                         "foo/hires_foo.png")
        self.assertEqual(path.get_modified_fname(pic_path, ".png", "_foo"),
                         "foo/hires_foo.png")
        self.assertEqual(path.get_modified_fname(pic_path, "png", "_foo."),
                         "foo/hires_foo.png")


if __name__ == "__main__":
    main()
