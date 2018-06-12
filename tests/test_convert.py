#!/usr/bin/env python
"""
Tests for Image2c64 <https://bitbucket.org/gryf/image2c64>

Author: Roman 'gryf' Dobosz <gryf73@gmail.com>
Date: 2012-11-20
Version: 1.3
Licence: BSD
"""
from tempfile import mkstemp, mkdtemp
from unittest import TestCase, main
import argparse
import os
import shutil

from c64img import cmd_convert
from c64img.base import FullScreenImage


HIRES = os.path.join(os.path.dirname(__file__), "test_images", "hires.png")


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


class TestResolvename(TestCase):
    """Test resolve name function"""

    def setUp(self):
        if not hasattr(self, "_path"):
            self._path = os.path.abspath(os.curdir)

        if not hasattr(self, "_args_mock_cls"):
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
            self._args_mock_cls = Obj

    def tearDown(self):
        os.chdir(self._path)

    def test_resolve_name(self):
        """
        Test resolve_name function
        """
        args = self._args_mock_cls()
        args.filename = ["foo"]
        args.format = "hires"
        args.output = None
        args.executable = False
        self.assertEqual(cmd_convert.resolve_name(args, args.filename[0]),
                         ("foo.prg", "hires"))

        args.output = "bar"
        self.assertEqual(cmd_convert.resolve_name(args, args.filename[0]),
                         ("bar", "hires"))

        args.executable = True
        self.assertEqual(cmd_convert.resolve_name(args, args.filename[0]),
                         ("bar.prg", "prg"))

        args.executable = False
        args.raw = True
        args.output = "bar.prg"
        self.assertEqual(cmd_convert.resolve_name(args, args.filename[0]),
                         ("bar", "raw"))

        args.output = "foo.hires"
        self.assertEqual(cmd_convert.resolve_name(args, args.filename[0]),
                         ("foo", "raw"))

        args.output = "foo.hires.png"
        self.assertEqual(cmd_convert.resolve_name(args, args.filename[0]),
                         ("foo.hires", "raw"))

        dname = mkdtemp()
        os.chdir(dname)

        args.output = "outdir"
        args.filename = ["foo.png", "bar,png"]
        self.assertEqual(cmd_convert.resolve_name(args, args.filename[0]),
                         ("outdir/foo", "raw"))

        fdesc, fname = mkstemp(suffix=".prg", dir=args.output)
        os.close(fdesc)

        args.output = fname
        self.assertRaises(IOError, cmd_convert.resolve_name, args,
                          args.filename[0])

        os.chdir(self._path)
        shutil.rmtree(dname)


class TestMisc(TestCase):
    """
    Test helper functions
    """

    def test_convert(self):
        """
        Test convert function
        """

        class Mock(object):
            def __init__(self):
                self.filename = []
                self.errors = ['show', 'save', 'none'][2]
                self.border = None
                self.background = None
                self.verbose = 0
                self.quiet = 0
                self.output = None
                self.format = None
                self.executable = False
                self.raw = False

        def mock_set_verbose(verbose, quiet):
            ConvClass.V = verbose
            ConvClass.Q = quiet

        class ConvClass(FullScreenImage):
            BG = None
            BORDER = None
            LOG = None
            V = 0
            Q = 0
            ERRORS = "none"
            SELF = []

            def __init__(self, fname, errors_action="none"):
                super(ConvClass, self).__init__(fname, errors_action)
                ConvClass.ERRORS = errors_action
                self.log = Mock()
                self.log.set_verbose = mock_set_verbose
                ConvClass.SELF.append(self)

            def save(self, fname, format_):
                return

            def set_border_color(self, color):
                ConvClass.BORDER = color

            def set_bg_color(self, color):
                ConvClass.BG = color

        arg_mock = Mock()
        cmd_convert.convert(arg_mock, ConvClass)
        self.assertEqual(ConvClass.BG, None)
        self.assertEqual(ConvClass.BORDER, None)
        self.assertEqual(ConvClass.V, 0)
        self.assertEqual(ConvClass.Q, 0)
        self.assertEqual(ConvClass.ERRORS, 'none')
        self.assertEqual(len(ConvClass.SELF), 0)

        arg_mock = Mock()
        arg_mock.filename = ["foo", "bar"]
        arg_mock.errors = "show"
        cmd_convert.convert(arg_mock, ConvClass)
        self.assertEqual(ConvClass.ERRORS, 'show')
        self.assertEqual(len(ConvClass.SELF), 2)
        self.assertEqual(ConvClass.SELF[0].prev_chars, {})
        self.assertEqual(ConvClass.SELF[1].prev_chars, ConvClass.SELF[0].chars)

        arg_mock = Mock()
        arg_mock.filename = ["foo", "bar", "baz"]
        arg_mock.border = 2  # red
        arg_mock.background = 8
        cmd_convert.convert(arg_mock, ConvClass)
        self.assertEqual(ConvClass.BORDER, 2)
        self.assertEqual(ConvClass.BG, 8)
        self.assertEqual(len(ConvClass.SELF), 5)
        self.assertEqual(ConvClass.SELF[2].prev_chars, {})
        self.assertEqual(ConvClass.SELF[3].prev_chars, ConvClass.SELF[2].chars)
        self.assertEqual(ConvClass.SELF[4].prev_chars, ConvClass.SELF[3].chars)

        arg_mock = Mock()
        arg_mock.filename = ["foo"]
        arg_mock.verbose = 2
        arg_mock.quiet = 2
        cmd_convert.convert(arg_mock, ConvClass)
        self.assertEqual(ConvClass.V, 2)
        self.assertEqual(ConvClass.Q, 2)
        self.assertEqual(ConvClass.ERRORS, 'none')
        self.assertEqual(len(ConvClass.SELF), 6)


class TestCmd(TestCase):
    """Test cmd_convert functions"""

    def setUp(self):
        """Setup"""
        class AnyObj(object):
            """General mock"""
            pass

        class ArgParseMock(object):
            """ArgumentParser mock"""

            def __init__(self, *args, **kwargs):
                pass

            def add_argument(self, *args, **kwargs):
                pass

            def add_mutually_exclusive_group(self, *args, **kwargs):
                return ArgParseMock()

            def parse_args(self):
                retobj = AnyObj()
                retobj.format = "hires"
                return retobj

        self._argparse = argparse.ArgumentParser
        argparse.ArgumentParser = ArgParseMock
        self._convert = cmd_convert.convert
        cmd_convert.convert = lambda x, y: 0

    def tearDown(self):
        """Teardown"""
        argparse.ArgumentParser = self._argparse
        cmd_convert.convert = self._convert

    def test_image2c64(self):
        """
        Test image2c64 cmd_convert
        """
        self.assertEqual(cmd_convert.image2c64(), 0)


if __name__ == "__main__":
    main()
