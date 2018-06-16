======
C64img
======

C64img is a python package which provides an abstraction layer for creating
images which Commodore 64 understands. This is especially useful in converting
images created on PC graphics tools, with C64 limitation in mind.

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

Like other standard Python pro programs, ``c64img`` provide a convenient way to
install using `setuptools`_, so the procedure will look like:

.. code:: shell-session

   $ python setup.py install

or, `pip`_ might be used as well:

.. code:: shell-session

   $ pip install -e /path/to/c64img_repository

or, you can grab latest stable version from `pypi`_:

.. code:: shell-session

   $ pip install c64img

finally, if you prefer to use virtualenv:

.. code:: shell-session

   $ virtualenv -p python2 venvname
   $ source venvname/bin/activate
   (venvname) $ pip install c64img

After that, you should be able to access ``image2c64`` script or import
``c64img`` module in Python interpreter.

Usage:
------

First of all, check up the switches program provides:

.. code:: shell-session

   $ image2c64 --help

Besides fine-tuning options like ``-b``/``--border`` for selecting border
color, ``-g``/``--background`` for selecting background color, it allows to
select aprorpiate output format:

- *multi* - for pure data located at ``$6000``
- *hires* - same, but for hires bitmap and colors (``$2000``)
- *koala* - multicolor bitmap in Koala format
- *art-studio-hires* - high resolution bitmap in Art Studio format (hires
  version)

Those formats should be passed using ``-f``/``--format`` parameter.

Furthemore two more switches can be used for output format:

- *raw* (``-r``, ``--raw``) - this will produce four files (*prefix* is
  obtained from the input image file name, or by using ``-o`` switch for
  output):

  - ``prefix_bg.raw`` 1-byte file with background color,
  - ``prefix_screen.raw`` - screen colors (usually placed at $0400),
  - ``prefix_color-ram.raw`` - additional 3rd color (supposed to be placed at
    ``$d800``)
  - and finally ``prefix_bitmap.raw`` - with bitmap matrix of the picture

- *executable* - produces *prg* which can be executed on emulator or real C64.
  Note, that this is just a image data and little displayer added to the image
  data.

For example:

+ Convert PNG image to koala with detailed log:

  .. code:: shell-session

     $ image2c64 -vv -f koala image.png

  Output will be written to ``image.prg``.

+ Convert GIF image to executable hires image, and write output to
  ``output.prg`` file:

  .. code:: shell-session

     $ image2c64 -f hires -x -o output.prg image.gif

+ Convert several images to raw data. Put the files in ``out`` directory:

  .. code:: shell-session

     $ image2c64 -f multi -r -o out image.png image1.gif image2.gif image3.gif

Parameter ``-v``/``-verbose`` can be use multiple times (effective, maximum
amount is double v) which increase verbosity of the output. Using
``-q``/``--quiet`` have opposite effect - it will suppress the output.

Color clashes
.............

Script can make several things in case of color clashes. In C64 graphics modes
you cannot put pixels in as one like, since there was hardware limitations
(memory, processing power etc), which provided to restrictions in graphics
modes. For example, in standard hires mode (320x200) it is impossible to use
more than 2 colors in 8x8 pixel area.

Underneath, c64img provides several options for color clash situation. By using
``-e``/``--errors`` switch with one of the following parameter, user can
influence conversion process in case of clashes/errors:

- no parameter or ``none`` - raport it on the console
- ``show`` - will display it - every wrong area will be marked with red
  rectangle
- ``save`` - will produce file with suffix ``_error.png`` next to original file
- ``grafx2`` - will save the error file, and open `grafx2`_ image editor with
  original image in front screen and error image on the spare screen. This is
  useful for manual clash corrections. Executable ``grafx2`` must be reachable
  by the environment variable ``PATH``.
- ``fix`` - will **try** to fix the clashes. Note, that this method is pretty
  naïve - the approximation of the colors is coarse, and may produce strange
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

+ 2018-06-12 Added information about possibility to convert picture to chars
  (no conversion! Just an info in log!)
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

This software is licensed under 3-clause BSD license. See LICENSE file for
details.


.. _PNG2HIRES_ v0.2 gfx format converter: http://www.atlantis-prophecy.org/onslaught/legal.html
.. _pillow: https://github.com/python-imaging/Pillow
.. _grafx2: http://grafx2.chez.com
.. _python 2.7: https://www.python.org
.. _setuptools: https://pypi.python.org/pypi/setuptools
.. _pip: https://github.com/pypa/pip
.. _pypi: https://pypi.org
