Image2c64
---------

Image2c64 is a program which can converts virtually any image supported by
`Pillow`_ to C64 hires or multicolor formats. Best results are achieved with
filetypes PNG or GIF.

Inspired on `PNG2HIRES_ v0.2 gfx format converter` /enthusi (onslaught)

As an input 320x200 (multicolor or hires) or 160x200 (mutlicolor) picture is
expected. Mutlicolor pictures will be scaled down to 160x200. Picture will be
converted to 16 colors. During that process some information can be lost, if
used more than 16 colors.

Requirements:
-------------

+ Python 2.7
+ `Pillow`_ module

Changes
-------

+ 2014-02-05 Rewrite the core of the converter (introduced *char* abstraction),
  added ability to convert sequent of images into multicolor pictures.
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
