Image2c64
=========

Image2c64 is a program which can converts virtually any image supported by
`Pillow`_ to C64 hires or multicolor formats. Best results are achieved with
filetypes PNG or GIF.

Inspired on `PNG2HIRES_ v0.2 gfx format converter`_ /enthusi (onslaught)

As an input 320x200 (multicolor or hires) or 160x200 (mutlicolor) picture is
expected. Mutlicolor pictures will be scaled down to 160x200. Picture will be
converted to 16 colors. During that process some information can be lost, if
used more than 16 colors.

Requirements:
-------------

+ Python 2.7
+ `Pillow`_ module

Usage:
------

First of all, check up the switches program provides:

.. code:: shell-session

   $ ./image2c64 --help

Examples:

+ Convert PNG image to koala with detailed log:

  .. code:: shell-session

     $ ./image2c64 -vvv -f koala image.png

  Output will be written to ``image.prg``.

+ Convert GIF image to executable hires image, and write output to
  ``output.prg`` file:

  .. code:: shell-session

     $ ./image2c64 -f hires -x -o output.prg image.gif

+ Convert several images to raw data. Put the files in ``out`` directory:

  .. code:: shell-session

     $ ./image2c64 -f multi -r -o out image.png image1.gif image2.gif image3.gif


Changes
-------

+ 2014-11-11 Fixed issue with color clash check in multicolor
+ 2014-11-11 Added ``grafx2`` option into error param. In such case image will
  be opened in `grafx2`_ program alongside with the error pic on spare screen.
+ 2014-02-09 Rewrite the core of the converter (introduced *char* abstraction),
  added ability to convert sequence of images.
+ 2012-11-20 Added executable output format for multicolor
+ 2012-11-19 Added multicolor support, changes to the docstrings
+ 2012-11-18 First public release

Other info
----------

+ Last update: 2014-02-05
+ Version: 2.0
+ Author: Roman 'gryf' Dobosz <gryf73@gmail.com>
+ Licence: BSD

.. _PNG2HIRES_ v0.2 gfx format converter: http://www.atlantis-prophecy.org/onslaught/legal.html
.. _pillow: https://github.com/python-imaging/Pillow
.. _grafx2: http://pulkomandy.tk/projects/GrafX2
