#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
image2c64 converts virtually any fullscreen image supported by Pillow to C64
hires or multicolor formats. Best results are achived with filetypes PNG or
GIF.
"""
import argparse
import os
import sys

from c64img import __version__ as ver
from c64img.hires import HiresConverter
from c64img.multi import MultiConverter
from c64img.path import get_modified_fname


def convert(arguments, converter_class):
    """
    Convert pictures
    """
    last = conv = None
    exit_code = 0
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
        if conv.save(filename, format_) != 0:
            exit_code += 1

    return exit_code


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

    if hasattr(arguments, "executable") and arguments.executable:

        format_ = "prg"
        _, ext = os.path.splitext(filename)
        if ext != ".prg":
            filename = get_modified_fname(filename, "prg")

    if hasattr(arguments, "raw") and arguments.raw:

        format_ = "raw"
        filename, ext = os.path.splitext(filename)

    return filename, format_


def image2c64():
    """
    Parse options, run the conversion
    """
    class_map = {"art-studio-hires": HiresConverter,
                 "hires": HiresConverter,
                 "koala": MultiConverter,
                 "multi": MultiConverter}

    formatter = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=formatter)
    parser.add_argument("-g", "--border", help="set color number for border, "
                        "default: most frequent color", type=int,
                        choices=range(16))
    parser.add_argument("-b", "--background", help="set color number for "
                        "background", type=int, choices=range(16))
    parser.add_argument("-e", "--errors", help="perform the action in case of "
                        "color clashes: save errormap under the same name "
                        "with '_error' suffix, show it, open in grafx2, fix "
                        "it, or don't do anything (the message appear)",
                        default="none", choices=("show", "save", "grafx2",
                                                 "fix", "none"))
    parser.add_argument("-f", "--format", help="format of output file, this "
                        "option is mandatory", choices=class_map.keys(),
                        required=True)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-x", "--executable", help="produce C64 executable as"
                       " 'prg' file", action="store_true")
    group.add_argument("-r", "--raw", help="produce raw files with only the "
                       "data. Useful for include in assemblers",
                       action="store_true")
    parser.add_argument("-o", "--output", help="output filename, default: "
                        "same filename as original with appropriate extension"
                        ". If multiple files provided as the input, output "
                        "will be treated as the directory")
    parser.add_argument('filename', nargs="+")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-q", "--quiet", help='please, be quiet. Adding more '
                       '"q" will decrease verbosity', action="count",
                       default=0)
    group.add_argument("-v", "--verbose", help='be verbose. Adding more "v" '
                       'will increase verbosity', action="count", default=0)
    parser.add_argument("-V", "--version", action='version',
                        version="%(prog)s v" + ver)

    arguments = parser.parse_args()
    return convert(arguments, class_map[arguments.format])


if __name__ == "__main__":
    sys.exit(image2c64())
