#!/usr/bin/env python
"""
Tests for Image2c64 <https://bitbucket.org/gryf/image2c64>

Author: Roman 'gryf' Dobosz <gryf73@gmail.com>
Date: 2012-11-20
Version: 1.3
Licence: BSD
"""
from unittest import TestCase, main
import logging

from c64img import logger


class TestLogger(TestCase):
    """
    Test Logger class
    """
    def test___init(self):
        """
        Test logger object creation
        """
        log = logger.Logger("foo")
        self.assertTrue(isinstance(log, logger.Logger))
        # since logger.Logging is mocked here we will have DummyLogger
        # instance
        self.assertTrue(isinstance(log(), logging.Logger))  # DummyLogger))
        self.assertEqual(log().handlers[0].name, 'console')

    def test__setup_logger(self):
        """
        Test setup logger method
        """
        log = logger.Logger("foo")
        self.assertEqual(len(log().handlers), 1)
        log.setup_logger()
        self.assertEqual(len(log().handlers), 1)
        self.assertEqual(log().handlers[0].name, 'console')
        self.assertEqual(log().getEffectiveLevel(), logging.WARNING)

    def test_set_verbose(self):
        """
        Test for changing verbosity level
        """
        log = logger.Logger("foo")()

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


if __name__ == "__main__":
    main()
