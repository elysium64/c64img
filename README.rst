======
C64img
======

C64img is a python module which provides several possible conversion between
various graphics formats and C64 formats or even raw data.

This project was inspired by `PNG2HIRES_ v0.2 gfx format converter`_ /enthusi
(onslaught), which was initially used as simple graphics converter between
PNG/GIF images to C64 hires (Art studio + executable). It evolved to bunch of
modules, which have own purposes - from simply converting graphics, to
generating data for C64 programs written in cross compilers, or even generating
data for memory optimised animations out of sequence of images.

Image2c64
=========

Image2c64 is a frontend program to ``c64img`` module, which can converts
virtually any image supported by `Pillow`_ to C64 hires or multicolor formats.
Best results are achieved with filetypes PNG or GIF.

As an input 320x200 (multicolor or hires) or 160x200 (mutlicolor) picture is
expected. Mutlicolor pictures will be scaled down to 160x200. Picture will be
converted to 16 colors. During that process some information can be lost, if
used more than 16 colors.

Requirements:
-------------

+ `Python 2.7`_
+ `Pillow`_ module


Installation
------------

There is no need for installing this script. For convenience it may be placed
somewhere in the ``PATH`` environment variable.

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


Script can make several things in case of color clashes. In C64 graphics modes
you cannot put pixels in as one like, since there was hardware limitations
(memory, processing power etc), which provided to restrictions in graphics
modes. For example, in standard hires mode (320x200) it is impossible to use
more than 2 colors in 8x8 pixel area.

Underneath, c64img provides several options for color clash situation:

- no parameter or ``none`` - raport it on the console
- ``show`` - will display it - every wrong area will be marked with red
  rectangle
- ``save`` - will produce file with suffix ``_error.png`` next to original file
- ``grafx2`` - will save the error file, and open `grafx2`_ image editor with
  original image in front screen and error image on the spare screen. This is
  useful for manual clash corrections. Executable ``grafx2`` must be reachable
  by the environment variable ``PATH``.
- ``fix`` - will **try** to fix the clashes. Note, that this method is not
  perfect - the approximation of the colors is coarse, and may produce strange
  results.

Example of output for ``save`` and ``fix`` arguments for ``--error`` parameter:

.. code:: shell-session

   $ ./image2c64 -f multi -x -e save test_images/clash.multi.png
   ERROR: Too many colors per block in char 10, 11 near x=76, y=84.
   ERROR: Too many colors per block in char 11, 13 near x=84, y=100.
   ERROR: Too many colors per block in char 12, 15 near x=92, y=116
   $ ./image2c64 -f multi -x -e fix test_images/clash.multi.png
   WARNING: Cannot remap color; using background - 'Light green'
   $

Changes
-------

+ 2015-09-10 Rearranged repository into separate modules for maintainability
+ 2014-11-16 Added mechanism for automatic clashes fix
+ 2014-11-11 Fixed issue with color clash check in multicolor
+ 2014-11-11 Added ``grafx2`` option into error param. In such case image will
  be opened in `grafx2`_ program alongside with the error pic on spare screen.
+ 2014-02-09 Rewrite the core of the converter (introduced *char* abstraction),
  added ability to convert sequence of images.
+ 2012-11-20 Added executable output format for multicolor
+ 2012-11-19 Added multicolor support, changes to the docstrings
+ 2012-11-18 First public release

Licence
-------

Copyright (c) 2012-2014, gryf/elysium
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

The views and conclusions contained in the software and documentation are those
of the authors and should not be interpreted as representing official policies,
either expressed or implied, of the FreeBSD Project.


.. _PNG2HIRES_ v0.2 gfx format converter: http://www.atlantis-prophecy.org/onslaught/legal.html
.. _pillow: https://github.com/python-imaging/Pillow
.. _grafx2: http://pulkomandy.tk/projects/GrafX2
.. _python 2.7: https://www.python.org/
